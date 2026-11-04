"""d3job: the job side of d3run.py. Stdlib only; copy it next to d3run.py (e.g. tools/d3job.py).

Inside a Slurm job started by `d3run.py submit`:

    from d3job import RunContext

    ctx = RunContext.from_env()            # reads the D3RUN_* and SLURM_* variables
    if ctx.finished():                     # an earlier segment finished (or failed): nothing to do
        raise SystemExit(0)
    ckpt = ctx.latest_checkpoint()         # newest checkpoint, local or fetched from S3, or None
    start = load(ckpt) if ckpt else 0
    ctx.mark("running")
    try:
        for step in range(start, n_steps):
            train_one_step()
            if ctx.should_checkpoint():    # the timer is due, or the end is near
                with ctx.checkpoint(step) as path:   # write the checkpoint into `path` (file or folder)
                    save(path)
                if ctx.should_stop():
                    ctx.mark("interrupted", progress=(step + 1) / n_steps)
                    raise SystemExit(0)    # the next segment resumes from here
        save_results(ctx.results_dir)
        ctx.finish()                       # uploads results/, marks the run done
    except Exception as exc:
        ctx.fail(exc)                      # marks failed: later segments exit at once
        raise

When to stop: as late as possible. The job knows when it ends (SLURM_JOB_END_TIME, or the start the job
template records plus the limit d3run passes, or one `squeue` call) and measures how long a step and a
checkpoint save take. should_stop() turns true when the time left drops below

    1.5 x (longest recent step + longest recent save) + safety_s        (safety_s = 30 s)

so with 2 s steps and a 10 s save the job stops about 48 s before the limit. Until both are measured it
uses guesses (step 60 s, save 120 s), capped at a quarter of the limit, and it takes the first checkpoint
after 5 minutes so the save time is known early. margin_s=... fixes the margin instead.

Hard deaths: a segment killed without a clean status (out of memory, a segfault, an exit without ctx.fail)
leaves status.json at "running". The next segment counts that; after `max_hard_failures` (2) such ends in a
row it marks the run failed, so the remaining segments exit instead of failing the same way. A clean
"interrupted" or "done" resets the count.

Signals: the USR1 that Slurm sends before the limit (job template, --signal=B:USR1@600) only confirms the
end time; the trap writes it into runs/<id>/STOP. SIGTERM (Slurm's kill) stops at once. Checkpoints every
`every_s` seconds (default 30 min) bound the loss when a job dies without any warning.

Uploads: a checkpoint saved so close to the end that its upload might be cut off stays local; the next
segment uploads it before it continues. S3 always holds a complete checkpoint, because LATEST.json is
uploaded only after the checkpoint itself.

Without the D3RUN_* variables (a local test run) the context works in runs/local/ without S3 and without
a time limit, so the same code runs on the laptop.
"""
from __future__ import annotations

import collections
import contextlib
import json
import os
import shutil
import signal
import socket
import subprocess
import sys
import time
from pathlib import Path

STATUS = "status.json"


def _log(msg: str) -> None:
    print(f"[d3job] {msg}", file=sys.stderr, flush=True)


def _write_json(path: Path, data) -> None:
    tmp = path.with_name(f".{path.name}.d3tmp")
    tmp.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n")
    os.replace(tmp, path)


def _read_json(path: Path, default):
    try:
        return json.loads(path.read_text())
    except (OSError, ValueError):
        return default


def _parse_left(text: str) -> float | None:
    """squeue %L: [days-]hours:minutes:seconds or minutes:seconds."""
    text = text.strip()
    if not text or text in ("UNLIMITED", "NOT_SET", "INVALID"):
        return None
    days = 0
    if "-" in text:
        d, text = text.split("-", 1)
        days = int(d)
    try:
        nums = [int(x) for x in text.split(":")]
    except ValueError:
        return None
    while len(nums) < 3:
        nums.insert(0, 0)
    h, m, s = nums[-3:]
    return float(((days * 24 + h) * 60 + m) * 60 + s)


def job_deadline(env=os.environ) -> tuple[float | None, str]:
    """Epoch second at which Slurm ends this job, and where that came from."""
    limit = float(env["D3RUN_TIME_LIMIT_S"]) if env.get("D3RUN_TIME_LIMIT_S") else None
    if env.get("SLURM_JOB_END_TIME"):
        return float(env["SLURM_JOB_END_TIME"]), "SLURM_JOB_END_TIME"
    if limit and env.get("D3RUN_JOB_START"):
        return float(env["D3RUN_JOB_START"]) + limit, "job start + limit"
    if limit and env.get("SLURM_JOB_START_TIME"):
        return float(env["SLURM_JOB_START_TIME"]) + limit, "SLURM_JOB_START_TIME + limit"
    if env.get("SLURM_JOB_ID"):
        try:
            res = subprocess.run(["squeue", "-h", "-j", env["SLURM_JOB_ID"], "-o", "%L"], capture_output=True,
                                 text=True, timeout=15)
            left = _parse_left(res.stdout) if res.returncode == 0 else None
            if left is not None:
                return time.time() + left, "squeue"
        except (OSError, subprocess.SubprocessError):
            pass
    if limit and not env.get("SLURM_JOB_ID"):
        return time.time() + limit, "local run: process start + limit"
    if limit:   # in a job without a start time: allow for the job's startup before Python, at most 1 min
        return time.time() + limit - min(60.0, 0.1 * limit), "process start + limit - startup allowance"
    return None, "none"


class RunContext:
    def __init__(self, run_id: str, run_dir: Path, attempt: int = 0, deadline: float | None = None,
                 limit_s: float | None = None, s3_uri: str = "", aws: list[str] | None = None,
                 every_s: float = 1800, first_ckpt_s: float = 300, keep_local: int = 1, keep_remote: int = 2,
                 margin_s: float | None = None, safety_s: float = 30, step_guess_s: float = 60,
                 save_guess_s: float = 120, signal_lead_s: float = 600, stop_check_s: float = 30,
                 max_hard_failures: int = 2):
        self.run_id = run_id
        self.run_dir = Path(run_dir)
        self.attempt = attempt
        self.deadline = deadline
        self.limit_s = limit_s
        self.s3_uri = s3_uri.rstrip("/")
        self.aws = aws or []
        self.every_s = every_s
        self.first_ckpt_s = first_ckpt_s
        self.keep_local = keep_local
        self.keep_remote = keep_remote
        self.margin_s = margin_s
        self.safety_s = safety_s
        self.step_guess_s = step_guess_s
        self.save_guess_s = save_guess_s
        self.signal_lead_s = signal_lead_s
        self.stop_check_s = stop_check_s
        self.max_hard_failures = max_hard_failures
        self.checkpoints_dir = self.run_dir / "checkpoints"
        self.results_dir = self.run_dir / "results"
        for d in (self.checkpoints_dir, self.results_dir, self.run_dir / "logs"):
            d.mkdir(parents=True, exist_ok=True)
        self._t0 = time.monotonic()
        self._last_ckpt: float | None = None
        self._last_tick: float | None = None
        self._ckpt_since_tick = 0.0
        self._steps: collections.deque = collections.deque(maxlen=20)
        self._saves: collections.deque = collections.deque(maxlen=5)
        self._uploads: collections.deque = collections.deque(maxlen=5)
        self._stop_now = False
        self._stop_logged = False
        self._stop_checked = 0.0
        self._stop_file = self.run_dir / "STOP"
        with contextlib.suppress(FileNotFoundError):
            self._stop_file.unlink()          # a STOP left by the previous segment
        for sig in (signal.SIGTERM, signal.SIGUSR1):
            with contextlib.suppress(ValueError):   # not in the main thread
                signal.signal(sig, self._on_signal)
        self._count_hard_failure()

    def _count_hard_failure(self) -> None:
        """An earlier attempt that left status 'running' died without a clean end (killed, out of memory, crash)."""
        st = self.status()
        if st.get("state") != "running" or int(st.get("attempt") or 0) >= self.attempt:
            return
        n = int(st.get("hard_failures") or 0) + 1
        if n >= self.max_hard_failures:
            self.mark("failed", hard_failures=n, error=f"{n} attempts in a row ended without a clean status "
                      "(killed, out of memory or crashed); see the logs of the last attempts")
            _log(f"{n} attempts in a row died without a clean end: run marked failed, later segments exit")
        else:
            st.update({"hard_failures": n, "attempt": self.attempt})
            _write_json(self.run_dir / STATUS, st)
            _log(f"attempt {self.attempt - 1} ended without a clean status ({n} in a row); trying once more")

    # ------------------------------------------------------------ construction
    @classmethod
    def from_env(cls, **kwargs) -> "RunContext":
        env = os.environ
        deadline, source = job_deadline(env)
        limit = float(env["D3RUN_TIME_LIMIT_S"]) if env.get("D3RUN_TIME_LIMIT_S") else None
        lead = float(env.get("D3RUN_SIGNAL_LEAD_S") or 600)
        if not env.get("D3RUN_ID"):
            _log("no D3RUN_ID: local mode in runs/local (no S3)")
            return cls("local", Path("runs/local"), deadline=deadline, limit_s=limit, signal_lead_s=lead, **kwargs)
        aws = []
        if env.get("D3RUN_S3_URI"):
            aws = [env.get("D3RUN_AWS") or shutil.which("aws") or str(Path.home() / ".local/bin/aws")]
            if env.get("D3RUN_S3_ENDPOINT"):
                aws += ["--endpoint-url", env["D3RUN_S3_ENDPOINT"]]
            if env.get("D3RUN_AWS_PROFILE"):
                aws += ["--profile", env["D3RUN_AWS_PROFILE"]]
        if deadline:
            _log(f"job ends at {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(deadline))} ({source})")
        return cls(env["D3RUN_ID"], Path(env["D3RUN_DIR"]), attempt=int(env.get("D3RUN_ATTEMPT", "0")),
                   deadline=deadline, limit_s=limit, s3_uri=env.get("D3RUN_S3_URI", ""), aws=aws,
                   signal_lead_s=lead, **kwargs)

    # ------------------------------------------------------------ status
    def status(self) -> dict:
        return _read_json(self.run_dir / STATUS, {})

    def mark(self, state: str, **info) -> None:
        """Write status.json (merged with what is there). States: running, interrupted, done, failed."""
        data = self.status()
        if state in ("interrupted", "done"):
            data["hard_failures"] = 0         # a clean end resets the count
        data.update(info)
        data.update({"run_id": self.run_id, "attempt": self.attempt, "state": state,
                     "updated_at": time.strftime("%Y-%m-%dT%H:%M:%S"), "host": socket.gethostname(),
                     "slurm_job_id": os.environ.get("SLURM_JOB_ID")})
        _write_json(self.run_dir / STATUS, data)

    def finished(self) -> bool:
        state = self.status().get("state")
        if state == "done":
            _log("run already done: this segment exits")
            return True
        if state == "failed" and not os.environ.get("D3RUN_RETRY"):
            _log("run marked failed: this segment exits (fix the cause, then resubmit; D3RUN_RETRY=1 overrides)")
            return True
        return False

    def finish(self, **info) -> None:
        self.push(self.results_dir)
        self.mark("done", progress=1.0, **info)
        self.push(self.run_dir / STATUS)

    def fail(self, exc: BaseException | str) -> None:
        self.mark("failed", error=repr(exc) if not isinstance(exc, str) else exc)
        self.push(self.run_dir / STATUS)

    # ------------------------------------------------------------ time and stop
    def _on_signal(self, signum, frame) -> None:
        if signum == signal.SIGTERM:
            self._stop_now = True             # Slurm's kill: stop at the next check
            _log("SIGTERM: stop at the next check")
        else:
            self._tighten(time.time() + self.signal_lead_s, "USR1")

    def _tighten(self, end: float, source: str) -> None:
        if self.deadline is None or end < self.deadline:
            self.deadline = end
            _log(f"end confirmed by {source}: {time.strftime('%H:%M:%S', time.localtime(end))}")

    def _read_stop_file(self) -> None:
        now = time.monotonic()
        if now - self._stop_checked < self.stop_check_s:
            return
        self._stop_checked = now
        if not self._stop_file.exists():
            return
        try:
            self._tighten(float(self._stop_file.read_text().strip()), "STOP file")
        except (OSError, ValueError):
            self._stop_now = True             # a STOP without an end time: stop now
        with contextlib.suppress(FileNotFoundError):
            self._stop_file.unlink()

    def time_left(self) -> float | None:
        return None if self.deadline is None else self.deadline - time.time()

    def margin(self) -> float:
        """Seconds to keep free: 1.5 x (step + save) + safety, from measurements once they exist."""
        if self.margin_s is not None:
            return self.margin_s
        step = max(self._steps) if self._steps else None
        save = max(self._saves) if self._saves else None
        m = 1.5 * ((self.step_guess_s if step is None else step) + (self.save_guess_s if save is None else save))
        m += self.safety_s
        if (step is None or save is None) and self.limit_s:
            m = min(m, 0.25 * self.limit_s)   # guesses must not eat short smoke-test jobs
        return m

    def should_stop(self) -> bool:
        if not self._stop_now:
            self._read_stop_file()
        left = self.time_left()
        stop = self._stop_now or (left is not None and left < self.margin())
        if stop and not self._stop_logged:
            self._stop_logged = True
            step = f"{max(self._steps):.1f} s" if self._steps else "guess"
            save = f"{max(self._saves):.1f} s" if self._saves else "guess"
            _log(f"stop: {left:.0f} s left, margin {self.margin():.0f} s (step {step}, save {save})"
                 if left is not None else "stop requested")
        return stop

    def checkpoint_due(self) -> bool:
        if self._last_ckpt is None:
            return time.monotonic() - self._t0 >= min(self.every_s, self.first_ckpt_s)
        return time.monotonic() - self._last_ckpt >= self.every_s

    def should_checkpoint(self) -> bool:
        """Call once per step: measures the step time, then says whether to checkpoint now."""
        now = time.monotonic()
        if self._last_tick is not None:
            self._steps.append(max(0.0, now - self._last_tick - self._ckpt_since_tick))
        self._last_tick = now
        self._ckpt_since_tick = 0.0
        return self.checkpoint_due() or self.should_stop()

    # ------------------------------------------------------------ checkpoints
    def _ckpt_names(self) -> list[str]:
        return sorted(p.name for p in self.checkpoints_dir.iterdir()
                      if p.name.startswith("step-") and ".d3tmp" not in p.name)

    @contextlib.contextmanager
    def checkpoint(self, step: int):
        """Yield a temporary path; on success publish it as checkpoints/step-<n>, upload, prune."""
        t_start = time.monotonic()
        name = f"step-{step:09d}"
        tmp = self.checkpoints_dir / f".d3tmp-{name}"
        if tmp.exists():
            shutil.rmtree(tmp) if tmp.is_dir() else tmp.unlink()
        try:
            yield tmp
        except BaseException:
            if tmp.exists():
                shutil.rmtree(tmp) if tmp.is_dir() else tmp.unlink()
            raise
        final = self.checkpoints_dir / name
        if final.exists():
            shutil.rmtree(final) if final.is_dir() else final.unlink()
        os.replace(tmp, final)
        _write_json(self.checkpoints_dir / "LATEST.json", {"name": name, "step": step})
        self._saves.append(time.monotonic() - t_start)
        self._last_ckpt = time.monotonic()
        uploaded = False
        if self.s3_uri:
            if self._upload_fits():
                uploaded = self._upload_checkpoint(name, final)
            else:
                _log(f"checkpoint {name} stays local (too close to the end); the next upload or segment takes it")
        self._prune_local(uploaded)
        self._ckpt_since_tick += time.monotonic() - t_start
        _log(f"checkpoint {name} in {self._saves[-1]:.1f} s" + (", uploaded" if uploaded else ""))

    def _upload_fits(self) -> bool:
        """Upload now only if the upload cannot run into the end of the job."""
        left = self.time_left()
        if left is None:
            return True
        up = max(self._uploads) if self._uploads else None
        if self.should_stop():                # the last checkpoint of this segment
            return up is not None and left - self.safety_s > 2 * up
        if up is None:
            return True                       # first upload: measure it (the first checkpoint comes early)
        return left - 1.5 * up > self.margin()   # must not run into the stop window

    def _upload_checkpoint(self, name: str, path: Path) -> bool:
        t = time.monotonic()
        ok = self.push(path) and self.push(self.checkpoints_dir / "LATEST.json")
        if ok:
            self._uploads.append(time.monotonic() - t)
            self._prune_remote(name, path.is_dir())
        return ok

    def _prune_local(self, uploaded: bool) -> None:
        # Uploaded: S3 holds a second copy, keep_local (1) is enough. Otherwise keep two locally.
        keep = self.keep_local if uploaded else max(self.keep_local, 2)
        for old in self._ckpt_names()[:-keep]:
            p = self.checkpoints_dir / old
            shutil.rmtree(p) if p.is_dir() else p.unlink()

    def _uploaded(self) -> list[dict]:
        return _read_json(self.checkpoints_dir / "uploaded.json", [])

    def _prune_remote(self, name: str, is_dir: bool) -> None:
        # The local list is pruned already, so the uploaded checkpoints are tracked in their own file.
        items = [x for x in self._uploaded() if x["name"] != name] + [{"name": name, "dir": is_dir}]
        if self.keep_remote:
            for old in items[:-self.keep_remote]:
                target = f"{self.s3_uri}/checkpoints/{old['name']}"
                ok = self._aws(["s3", "rm", "--recursive", target + "/", "--only-show-errors"] if old["dir"]
                               else ["s3", "rm", target, "--only-show-errors"])
                if ok:
                    items.remove(old)
        _write_json(self.checkpoints_dir / "uploaded.json", items)

    def latest_checkpoint(self) -> Path | None:
        latest = self.checkpoints_dir / "LATEST.json"
        info = _read_json(latest, None)
        if info and (self.checkpoints_dir / info["name"]).exists():
            path = self.checkpoints_dir / info["name"]
            if self.s3_uri and info["name"] not in {x["name"] for x in self._uploaded()}:
                if self._upload_checkpoint(info["name"], path):     # left local by the previous segment
                    _log(f"checkpoint {info['name']} uploaded on resume")
            return path
        if not self.s3_uri:
            return None
        if not self._aws(["s3", "cp", f"{self.s3_uri}/checkpoints/LATEST.json", str(latest), "--only-show-errors"]):
            return None                             # no checkpoint in S3 either: fresh start
        info = _read_json(latest, None)
        if not info:
            return None
        dest = self.checkpoints_dir / info["name"]
        ok = self._aws(["s3", "sync", f"{self.s3_uri}/checkpoints/{info['name']}/", str(dest), "--only-show-errors"])
        if not (ok and dest.exists() and any(dest.iterdir())):
            ok = self._aws(["s3", "cp", f"{self.s3_uri}/checkpoints/{info['name']}", str(dest), "--only-show-errors"])
        if ok and dest.exists():
            _log(f"checkpoint {info['name']} fetched from S3")
            return dest
        _log(f"checkpoint {info['name']} listed in S3 but not fetched")
        return None

    # ------------------------------------------------------------ S3
    def _aws(self, args: list[str]) -> bool:
        if not self.aws:
            return False
        res = subprocess.run(self.aws + args, capture_output=True, text=True)
        if res.returncode != 0:
            _log(f"aws {' '.join(args[:2])} failed: {res.stderr.strip()[:300]}")
        return res.returncode == 0

    def push(self, path: Path) -> bool:
        """Upload a file or folder below the run folder to the same place under the run's S3 prefix."""
        if not self.s3_uri:
            return False
        path = Path(path)
        rel = path.resolve().relative_to(self.run_dir.resolve()).as_posix()
        if path.is_dir():
            return self._aws(["s3", "sync", str(path), f"{self.s3_uri}/{rel}/", "--only-show-errors",
                              "--exclude", "*.d3tmp*"])
        return self._aws(["s3", "cp", str(path), f"{self.s3_uri}/{rel}", "--only-show-errors"])
