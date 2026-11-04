#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""d3run: run IDs, a run registry and S3 transfers for Slurm jobs (D3 group, KiRegio server).

Copy this file into the project (e.g. tools/d3run.py), commit it, and call it on the login host:

    uv run tools/d3run.py init --user abcd --s3-uri s3://<bucket>/<project>
    uv run tools/d3run.py new --config configs/a.yaml configs/b.yaml --tag round-2026-11
    uv run tools/d3run.py submit <run_id> --script jobs/train.sbatch --time 06:00:00 --cpus 1 --mem 8G --gpus 1
    uv run tools/d3run.py reconcile
    uv run tools/d3run.py size --tag round-2026-11
    uv run tools/d3run.py archive --finished --clean --submit

Design:
- The run ID exists before sbatch: <YYYYMMDD>-<user>-<slug>-<4 hex>. It names the run folder
  runs/<run_id>/ (logs, checkpoints, results) and the S3 prefix <s3-uri>/runs/<run_id>/. A Slurm job
  ID is only an attribute of one attempt, stored with its submit time, so restarted job IDs cannot
  mix up runs, and one run can span several 24 h jobs.
- One writer per file: only this script, on the login host, writes runs/registry.db. Jobs write
  runs/<run_id>/status.json (d3job.py), transfer jobs write runs/<run_id>/archive.json, and
  `reconcile` reads both. SQLite over NFS from two hosts can corrupt the database.
- Light on the login host: each command touches a small SQLite file, a few small files and at most
  one sacct call per 200 jobs. Only archive, push and pull move data; above 1 GB or 2,000 files they
  refuse to run on the login host and ask for --submit, which runs the transfer as a Slurm job.
- S3 is the store, the server is scratch: nothing is deleted locally before every file is verified
  in S3 by size, never while a run is queued or running, never anything tracked by git.
  Without a bucket: copy to your own machine (rsync) or other storage, make a `manifest` of the copy
  there, and `clean --manifest` deletes on the server only what the copy holds with the same sizes.
- Fair use: all GPUs or CPUs only while nobody else waits. `submit` counts the user's running and
  startable jobs (one squeue call); while other users wait, jobs above the share (default 3 of 4 GPUs,
  112 of 150 CPUs in `cpu`) are submitted held. `feed` (also run by `reconcile`, or looping as a 1-CPU
  feeder job) releases them when nobody waits and holds back pending ones when others start waiting.
  Running jobs are never touched (the cluster does not preempt).
"""
from __future__ import annotations

import argparse
import getpass
import hashlib
import json
import math
import os
import re
import secrets
import shlex
import shutil
import sqlite3
import subprocess
import sys
import tempfile
import time
from pathlib import Path

MAX_TIME_S = 24 * 3600          # partition limit; longer jobs are accepted but never start
LONG_TIME_S = 20 * 3600         # above this, split into segments
SEGMENT_S = 12 * 3600           # segment length suggested by `size`
LOGIN_MAX_BYTES = 1 << 30       # transfers above this run as a Slurm job
LOGIN_MAX_FILES = 2000
CONFIG_MAX_BYTES = 10 << 20     # hash configs, not data
KEEP_AFTER_CLEAN = {"run.json", "status.json", "archive.json"}
ACTIVE_JOB_STATES = ("PENDING", "RUNNING", "REQUEUED", "SUSPENDED", "CONFIGURING", "COMPLETING",
                     "RESIZING", "SIGNALING", "STAGE_OUT")
FAILED_JOB_STATES = {"FAILED", "OUT_OF_MEMORY", "NODE_FAIL", "BOOT_FAIL", "DEADLINE", "PREEMPTED"}
FINISHED_RUN_STATES = ("DONE", "FAILED", "CANCELLED")
RUN_STATES = ("NEW", "SUBMITTED", "RUNNING", "INTERRUPTED") + FINISHED_RUN_STATES
TS = "%Y-%m-%dT%H:%M:%S"        # server local time, the format sacct prints
GPUS_TOTAL, CPU_CAP = 4, 150    # the node's GPUs; CPUs the cpu partition may use (MaxCPUsPerNode)
SHARE_GPUS, SHARE_CPUS = 3, 112  # one user's share while others wait (settings share_gpus, share_cpus)
WAIT_REASONS = ("Resources", "Priority", "ReqNodeNotAvail", "Nodes required")
HOLD_REASONS = ("JobHeldUser", "JobHeldAdmin")

SCHEMA = """
CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT);
CREATE TABLE IF NOT EXISTS runs (
    run_id TEXT PRIMARY KEY,
    user TEXT NOT NULL,
    project TEXT NOT NULL,
    name TEXT NOT NULL,
    tag TEXT,
    git_commit TEXT,
    git_dirty INTEGER,
    config_path TEXT,
    config_hash TEXT,
    params_json TEXT,
    status TEXT NOT NULL DEFAULT 'NEW',
    progress REAL,
    run_dir TEXT NOT NULL,
    s3_uri TEXT,
    note TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    archived_at TEXT,
    cleaned_at TEXT,
    copied_to TEXT
);
CREATE TABLE IF NOT EXISTS attempts (
    run_id TEXT NOT NULL REFERENCES runs(run_id),
    attempt INTEGER NOT NULL,
    slurm_job_id TEXT,
    submitted_at TEXT NOT NULL,
    job_name TEXT,
    depends_on TEXT,
    req_time_s INTEGER,
    req_cpus INTEGER,
    req_mem TEXT,
    req_gpus INTEGER,
    state TEXT NOT NULL DEFAULT 'PENDING',
    exit_code TEXT,
    elapsed_s INTEGER,
    total_cpu_s REAL,
    max_rss_mb REAL,
    gpu_mem_mb REAL,
    node TEXT,
    started_at TEXT,
    ended_at TEXT,
    out_path TEXT,
    err_path TEXT,
    PRIMARY KEY (run_id, attempt)
);
CREATE INDEX IF NOT EXISTS attempts_job ON attempts(slurm_job_id);
CREATE INDEX IF NOT EXISTS runs_tag ON runs(tag);
CREATE INDEX IF NOT EXISTS runs_hash ON runs(config_hash);
"""


# ---------------------------------------------------------------- helpers

def now() -> str:
    return time.strftime(TS)


def info(msg: str) -> None:
    print(f"d3run: {msg}", file=sys.stderr)


def die(msg: str, code: int = 2):
    print(f"d3run: error: {msg}", file=sys.stderr)
    sys.exit(code)


def in_job() -> bool:
    return bool(os.environ.get("SLURM_JOB_ID"))


def job_env() -> dict:
    """The environment sbatch hands to jobs (--export=ALL), without d3run's own uv script environment.

    `uv run d3run.py` puts its script environment first on PATH and sets VIRTUAL_ENV; passed on, a job's bare
    `python` would be that environment's interpreter, and `uv run` in the job warns about VIRTUAL_ENV.
    """
    env = dict(os.environ)
    for key in ("VIRTUAL_ENV", "UV_RUN_RECURSION_DEPTH", "UV"):
        env.pop(key, None)
    if sys.prefix != sys.base_prefix:
        own = str(Path(sys.prefix))
        env["PATH"] = os.pathsep.join(x for x in env.get("PATH", "").split(os.pathsep) if not x.startswith(own))
    return env


def login_only(cmd: str) -> None:
    if in_job():
        die(f"`{cmd}` writes the registry and runs only on the login host, not inside a Slurm job "
            "(one writer per file: SQLite over NFS from two hosts can corrupt it)")


def slugify(text: str, maxlen: int) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", (text or "").lower()).strip("-")
    return s[:maxlen].strip("-") or "run"


def parse_slurm_time(text: str) -> int:
    """Slurm time formats: MM, MM:SS, HH:MM:SS, D-HH, D-HH:MM, D-HH:MM:SS."""
    text = text.strip()
    try:
        if "-" in text:
            d, rest = text.split("-", 1)
            parts = [int(p) for p in rest.split(":")]
            while len(parts) < 3:
                parts.append(0)
            h, m, s = parts
            return ((int(d) * 24 + h) * 60 + m) * 60 + s
        parts = [int(p) for p in text.split(":")]
    except ValueError:
        die(f"cannot read time '{text}' (use HH:MM:SS)")
    if len(parts) == 1:
        return parts[0] * 60
    if len(parts) == 2:
        return parts[0] * 60 + parts[1]
    h, m, s = parts[-3:]
    return (h * 60 + m) * 60 + s


def fmt_time(seconds: float) -> str:
    seconds = int(round(seconds))
    return f"{seconds // 3600:02d}:{seconds % 3600 // 60:02d}:{seconds % 60:02d}"


def parse_duration(text: str) -> float | None:
    """sacct durations such as TotalCPU: [D-][HH:]MM:SS[.mmm]."""
    text = (text or "").strip()
    if not text:
        return None
    days = 0
    if "-" in text:
        d, text = text.split("-", 1)
        days = int(d)
    try:
        nums = [float(p) for p in text.split(":")]
    except ValueError:
        return None
    while len(nums) < 3:
        nums.insert(0, 0.0)
    h, m, s = nums[-3:]
    return days * 86400 + h * 3600 + m * 60 + s


def parse_mem_mb(text: str) -> float | None:
    m = re.fullmatch(r"([\d.]+)([KMGT]?)", (text or "").strip())
    if not m:
        return None
    factor = {"": 1 / 1024 / 1024, "K": 1 / 1024, "M": 1, "G": 1024, "T": 1024 * 1024}[m.group(2)]
    return float(m.group(1)) * factor


def ceil_quarter_hour(seconds: float) -> int:
    return max(900, math.ceil(seconds / 900) * 900)


def write_json(path: Path, data) -> None:
    tmp = path.with_name(f".{path.name}.d3tmp")
    tmp.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n")
    os.replace(tmp, path)


def read_json(path: Path):
    try:
        return json.loads(path.read_text())
    except (OSError, ValueError):
        return None


def project_root(arg: str | None) -> Path:
    if arg:
        return Path(arg).expanduser().resolve()
    if os.environ.get("D3RUN_ROOT"):
        return Path(os.environ["D3RUN_ROOT"]).resolve()
    try:
        out = subprocess.run(["git", "rev-parse", "--show-toplevel"], capture_output=True, text=True,
                             check=True).stdout.strip()
        return Path(out)
    except (OSError, subprocess.CalledProcessError):
        return Path.cwd()


def open_registry(root: Path, create: bool = False) -> sqlite3.Connection:
    path = root / "runs" / "registry.db"
    if not path.exists() and not create:
        die(f"no registry at {path}; run `d3run.py init` in the project first")
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path, timeout=30)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=DELETE")   # no WAL: WAL needs shared memory on one host
    conn.executescript(SCHEMA)
    if "copied_to" not in {r[1] for r in conn.execute("PRAGMA table_info(runs)")}:
        conn.execute("ALTER TABLE runs ADD COLUMN copied_to TEXT")    # registries made before this column
    return conn


def get_settings(conn) -> dict:
    return {r["key"]: r["value"] for r in conn.execute("SELECT key, value FROM settings")}


def set_settings(conn, values: dict) -> None:
    conn.executemany("INSERT INTO settings(key, value) VALUES(?, ?) "
                     "ON CONFLICT(key) DO UPDATE SET value = excluded.value", list(values.items()))


def get_run(conn, run_id: str):
    row = conn.execute("SELECT * FROM runs WHERE run_id = ?", (run_id,)).fetchone()
    if row is None:
        die(f"unknown run ID {run_id}")
    return row


def attempts_of(conn, run_id: str):
    return conn.execute("SELECT * FROM attempts WHERE run_id = ? ORDER BY attempt", (run_id,)).fetchall()


def git_state(root: Path):
    try:
        commit = subprocess.run(["git", "-C", str(root), "rev-parse", "HEAD"], capture_output=True,
                                text=True, check=True).stdout.strip()
        dirty = subprocess.run(["git", "-C", str(root), "status", "--porcelain", "--untracked-files=no"],
                               capture_output=True, text=True, check=True).stdout.strip()
        return commit, bool(dirty)
    except (OSError, subprocess.CalledProcessError):
        return None, None


def read_ids(values: list[str]) -> list[str]:
    if values == ["-"]:
        return [line.strip() for line in sys.stdin if line.strip()]
    return values


def parse_params(items: list[str] | None) -> dict:
    params = {}
    for item in items or []:
        if "=" not in item:
            die(f"--param needs key=value, got '{item}'")
        k, v = item.split("=", 1)
        try:
            params[k] = json.loads(v)
        except ValueError:
            params[k] = v
    return params


# ---------------------------------------------------------------- S3 layer (AWS CLI)

def aws_cmd(st: dict) -> list[str]:
    aws = os.environ.get("D3RUN_AWS") or st.get("aws_bin") or shutil.which("aws") \
        or str(Path.home() / ".local" / "bin" / "aws")
    if not (Path(aws).exists() or shutil.which(aws)):
        die("AWS CLI not found: install it with `uv tool install awscli` (references/data-and-storage.md)")
    cmd = [aws]
    endpoint = os.environ.get("D3RUN_S3_ENDPOINT") or st.get("s3_endpoint")
    profile = os.environ.get("D3RUN_AWS_PROFILE") or st.get("aws_profile")
    if endpoint:
        cmd += ["--endpoint-url", endpoint]
    if profile:
        cmd += ["--profile", profile]
    return cmd


def walk(base: Path) -> dict[str, int]:
    """Relative path -> size for every file under base (temporary .d3tmp files left out)."""
    if base.is_file():
        return {base.name: base.stat().st_size}
    files = {}
    for dirpath, dirnames, filenames in os.walk(base):
        dirnames[:] = [d for d in dirnames if ".d3tmp" not in d]
        for fn in filenames:
            if ".d3tmp" in fn:
                continue
            p = Path(dirpath) / fn
            files[p.relative_to(base).as_posix()] = p.stat().st_size
    return files


def remote_sizes(aws: list[str], prefix_uri: str) -> dict[str, int] | None:
    """Relative key -> size for every object below prefix_uri (a 'folder')."""
    uri = prefix_uri.rstrip("/") + "/"
    res = subprocess.run(aws + ["s3", "ls", "--recursive", uri], capture_output=True, text=True)
    if res.returncode not in (0, 1):          # 1 = nothing found
        info(f"listing {uri} failed: {res.stderr.strip()}")
        return None
    bucket_key = uri[len("s3://"):].split("/", 1)
    prefix = bucket_key[1] if len(bucket_key) > 1 else ""
    out = {}
    for line in res.stdout.splitlines():
        parts = line.split(None, 3)
        if len(parts) == 4 and parts[2].isdigit() and parts[3].startswith(prefix):
            out[parts[3][len(prefix):]] = int(parts[2])
    return out


def sync_verify(aws: list[str], local: Path, uri: str, direction: str = "up") -> tuple[bool, dict]:
    """Copy local <-> uri, then compare every file's size. Returns (verified, details)."""
    is_file = local.is_file() if direction == "up" else False
    if direction == "up":
        if is_file:
            cmd = aws + ["s3", "cp", str(local), uri, "--only-show-errors"]
        else:
            cmd = aws + ["s3", "sync", str(local), uri.rstrip("/") + "/", "--only-show-errors",
                         "--exclude", "*.d3tmp*"]
    else:
        remote = remote_sizes(aws, uri)
        is_file = not remote
        local.parent.mkdir(parents=True, exist_ok=True)
        if is_file:
            cmd = aws + ["s3", "cp", uri, str(local), "--only-show-errors"]
        else:
            cmd = aws + ["s3", "sync", uri.rstrip("/") + "/", str(local), "--only-show-errors"]
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        return False, {"error": res.stderr.strip() or f"exit {res.returncode}", "files": 0, "bytes": 0,
                       "missing": []}
    if is_file:
        parent = uri.rsplit("/", 1)[0]
        remote = remote_sizes(aws, parent) or {}
        name = uri.rsplit("/", 1)[1]
        remote = {name: remote[name]} if name in remote else {}
        local_files = {name: local.stat().st_size} if local.exists() else {}
    else:
        remote = remote_sizes(aws, uri) or {}
        local_files = walk(local) if local.exists() else {}
    reference = local_files if direction == "up" else remote
    other = remote if direction == "up" else local_files
    missing = sorted(k for k, v in reference.items() if other.get(k) != v)
    return not missing and bool(reference), {"files": len(reference), "bytes": sum(reference.values()),
                                             "missing": missing}


def guard_login(n_files: int, n_bytes: int, here: bool, what: str) -> None:
    if in_job() or here:
        return
    if n_bytes > LOGIN_MAX_BYTES or n_files > LOGIN_MAX_FILES:
        die(f"{what}: {n_bytes / 2**30:.1f} GB in {n_files} files is too much for the login host. "
            "Add --submit to run it as a Slurm job (or --here if you are sure)")


def submit_self(root: Path, job_args: list[str], st: dict, hours: str, cpus: int = 2, mem: str = "4G",
                name: str = "d3run-transfer") -> None:
    script = Path(__file__).resolve()
    inner = "cd " + shlex.quote(str(root)) + " && " + shlex.join(["uv", "run", str(script), *job_args, "--here"])
    export = ["ALL", f"D3RUN_ROOT={root}"]
    for key, env in (("aws_bin", "D3RUN_AWS"), ("s3_endpoint", "D3RUN_S3_ENDPOINT"),
                     ("aws_profile", "D3RUN_AWS_PROFILE")):
        if st.get(key):
            export.append(f"{env}={st[key]}")
    if any("," in x for x in export[1:]):
        die("commas are not allowed in paths or settings passed to a job")
    log = root / "runs" / f"{name.removeprefix('d3run-')}-%j.out"
    cmd = ["sbatch", "--parsable", f"--job-name={name}", f"--time={hours}", f"--cpus-per-task={cpus}",
           f"--mem={mem}", f"--output={log}", f"--error={log}", f"--chdir={root}", f"--export={','.join(export)}",
           "--wrap", inner]
    res = subprocess.run(cmd, capture_output=True, text=True, cwd=root, env=job_env())
    if res.returncode != 0:
        die(f"sbatch failed: {res.stderr.strip()}")
    jid = res.stdout.strip().split(";")[0]
    hint = "; run `reconcile` when it has finished" if job_args[0] == "archive" else ""
    print(f"{name} job {jid}; log {str(log).replace('%j', jid)}{hint}")


def s3_settings(root: Path, a) -> tuple[dict, str]:
    """Settings and the project's S3 URI: from --s3-uri (inside jobs) or from the registry."""
    if getattr(a, "s3_uri", None):
        return {}, a.s3_uri.rstrip("/")
    if in_job():
        die("inside a job pass --s3-uri (the transfer job never opens the registry)")
    conn = open_registry(root)
    st = get_settings(conn)
    conn.close()
    if not st.get("s3_uri"):
        die("no S3 location set. If you have a bucket: `init --s3-uri s3://<bucket>/<project>`; "
            "otherwise ask the admin for one (references/data-and-storage.md has the interim route)")
    return st, st["s3_uri"]


# ---------------------------------------------------------------- fair use (queue)

def queue_snapshot() -> list[dict]:
    """All jobs in the queue: one squeue call."""
    try:
        res = subprocess.run(["squeue", "-h", "-o", "%i|%u|%t|%P|%b|%C|%r|%k"], capture_output=True, text=True,
                             timeout=60)
    except FileNotFoundError:
        die("squeue not found: run this on the login host (or pass --no-throttle)")
    if res.returncode != 0:
        die(f"squeue failed: {res.stderr.strip()}")
    jobs = []
    for line in res.stdout.splitlines():
        f = line.split("|")
        if len(f) < 8:
            continue
        m = re.search(r"gpu(?::[A-Za-z0-9_.-]+)?:(\d+)", f[4])
        try:
            cpus = int(f[5])
        except ValueError:
            cpus = 0
        jobs.append({"id": f[0], "user": f[1], "state": f[2], "partition": f[3], "gpus": int(m.group(1)) if m else 0,
                     "cpus": cpus, "reason": f[6], "comment": "|".join(f[7:])})
    return jobs


def _reasons(job: dict) -> list[str]:
    return [r.strip() for r in job["reason"].split(",")]


def is_waiting(job: dict) -> bool:
    """Pending for resources or priority, i.e. it would run if resources were free."""
    return job["state"] == "PD" and any(r.startswith(WAIT_REASONS) for r in _reasons(job))


def is_active(job: dict) -> bool:
    """Running, or pending and free to start (not held, not waiting on a dependency or a start time)."""
    if job["state"] in ("R", "CG", "CF"):
        return True
    return job["state"] == "PD" and not any(r.startswith(HOLD_REASONS + ("Dependency", "BeginTime"))
                                            for r in _reasons(job))


def share_budget(jobs: list[dict], me: str, st: dict) -> dict:
    others = [j for j in jobs if j["user"] != me and is_waiting(j)]
    others_gpu = any(j["partition"] == "main" for j in others)
    others_cpu = any(j["partition"] == "cpu" for j in others)
    mine = [j for j in jobs if j["user"] == me and is_active(j)]
    use_g = sum(j["gpus"] for j in mine if j["partition"] == "main")
    use_c = sum(j["cpus"] for j in mine if j["partition"] == "cpu")
    cap_g = int(st.get("share_gpus") or SHARE_GPUS) if others_gpu else int(st.get("gpus_total") or GPUS_TOTAL)
    cap_c = int(st.get("share_cpus") or SHARE_CPUS) if others_cpu else int(st.get("cpu_cap") or CPU_CAP)
    return {"others_gpu": others_gpu, "others_cpu": others_cpu, "use_gpus": use_g, "use_cpus": use_c,
            "cap_gpus": cap_g, "cap_cpus": cap_c, "free_gpus": cap_g - use_g, "free_cpus": cap_c - use_c}


def budget_line(b: dict) -> str:
    who = [x for x, flag in (("GPU", b["others_gpu"]), ("CPU", b["others_cpu"])) if flag]
    return (f"GPUs {b['use_gpus']}/{b['cap_gpus']}, CPUs {b['use_cpus']}/{b['cap_cpus']} "
            + (f"(others waiting for {' and '.join(who)}: share applies)" if who else "(nobody else waiting)"))


def _job_num(job: dict) -> int:
    m = re.match(r"\d+", job["id"])
    return int(m.group()) if m else 0


def feed_pass(st: dict, me: str) -> tuple[str, int]:
    """Release held d3run jobs within the budget; hold back pending ones while over it. Returns (line, held)."""
    jobs = queue_snapshot()
    b = share_budget(jobs, me, st)
    ours = [j for j in jobs if j["user"] == me and j["comment"].startswith("d3run")]
    held = sorted((j for j in ours if j["state"] == "PD" and any(r.startswith(HOLD_REASONS) for r in _reasons(j))),
                  key=_job_num)
    release = []
    for j in held:
        need_g, need_c = (j["gpus"], 0) if j["partition"] == "main" else (0, j["cpus"])
        if need_g <= b["free_gpus"] and need_c <= b["free_cpus"]:
            release.append(j["id"])
            b["free_gpus"] -= need_g
            b["free_cpus"] -= need_c
    hold_back = []
    for j in sorted((j for j in ours if j["state"] == "PD" and is_active(j)), key=_job_num, reverse=True):
        if j["partition"] == "main" and b["free_gpus"] < 0:
            hold_back.append(j["id"])
            b["free_gpus"] += j["gpus"]
        elif j["partition"] == "cpu" and b["free_cpus"] < 0:
            hold_back.append(j["id"])
            b["free_cpus"] += j["cpus"]
    for verb, ids in (("release", release), ("hold", hold_back)):
        if ids:
            res = subprocess.run(["scontrol", verb, ",".join(ids)], capture_output=True, text=True)
            if res.returncode != 0:
                info(f"scontrol {verb} failed: {res.stderr.strip()}")
    still = len(held) - len(release) + len(hold_back)
    line = (f"{time.strftime('%H:%M')} {budget_line(share_budget(jobs, me, st))}; released {len(release)}, "
            f"held back {len(hold_back)}, held {still}")
    return line, still


def read_settings_ro(root: Path) -> dict:
    path = root / "runs" / "registry.db"
    try:
        conn = sqlite3.connect(f"file:{path}?mode=ro", uri=True, timeout=30)
        return {k: v for k, v in conn.execute("SELECT key, value FROM settings")}
    except sqlite3.Error:
        return {}


# ---------------------------------------------------------------- commands

def cmd_init(a) -> None:
    login_only("init")
    root = project_root(a.root)
    conn = open_registry(root, create=True)
    cur = get_settings(conn)
    new = {
        "project": slugify(a.project or cur.get("project") or root.name, 24),
        "user": slugify(a.user or cur.get("user") or os.environ.get("USER", "user"), 12),
    }
    if a.no_s3:
        new["s3_uri"] = ""
    elif a.s3_uri:
        if not a.s3_uri.startswith("s3://") or "," in a.s3_uri:
            die("--s3-uri must look like s3://<bucket>/<project> (no commas)")
        new["s3_uri"] = a.s3_uri.rstrip("/")
    for key in ("s3_endpoint", "aws_profile", "aws_bin", "share_gpus", "share_cpus"):
        if getattr(a, key) is not None:
            new[key] = str(getattr(a, key))
    set_settings(conn, new)
    conn.commit()
    st = get_settings(conn)
    for k in sorted(st):
        print(f"{k:12} {st[k]}")
    if not st.get("s3_uri"):
        info("no S3 location: archive, push and pull are off until you set one")
    ignored = subprocess.run(["git", "-C", str(root), "check-ignore", "-q", "runs/registry.db"])
    if ignored.returncode == 1:
        info("add `runs/` to .gitignore: run folders, logs and the registry stay out of git")


def cmd_settings(a) -> None:
    root = project_root(a.root)
    path = root / "runs" / "registry.db"
    if not path.exists():
        print("no registry yet: run `d3run.py init`")
        return
    conn = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    for r in conn.execute("SELECT key, value FROM settings ORDER BY key"):
        print(f"{r['key']:12} {r['value']}")


def cmd_new(a) -> None:
    login_only("new")
    root = project_root(a.root)
    conn = open_registry(root)
    st = get_settings(conn)
    params = parse_params(a.param)
    configs = a.config or [None]
    if not a.name and configs == [None]:
        die("give --name or --config")
    commit, dirty = git_state(root)
    if commit is None:
        info("warning: not a git checkout; the runs record no commit")
    if dirty and not a.allow_dirty:
        die("tracked files have uncommitted changes: commit (and deploy) first so each run records the "
            "code it ran; --allow-dirty only for smoke tests")
    for cfg in configs:
        stem = Path(cfg).stem if cfg else ""
        name = a.name if (a.name and len(configs) == 1) else "-".join(x for x in (a.name, stem) if x)
        slug = slugify(name, 24)
        cfg_file = cfg_rel = cfg_hash = None
        if cfg:
            cfg_file = Path(cfg).expanduser().resolve()
            if not cfg_file.is_file():
                die(f"config not found: {cfg}")
            if cfg_file.stat().st_size > CONFIG_MAX_BYTES:
                die(f"{cfg} is larger than 10 MB: hash configs, not data")
            try:
                cfg_rel = cfg_file.relative_to(root).as_posix()
            except ValueError:
                cfg_rel = str(cfg_file)
        if cfg_file or params:
            h = hashlib.sha256(cfg_file.read_bytes() if cfg_file else b"")
            h.update(json.dumps(params, sort_keys=True).encode())
            cfg_hash = h.hexdigest()
        if cfg_hash and not a.allow_duplicate:
            dup = conn.execute(
                "SELECT run_id, status FROM runs WHERE config_hash = ? AND git_commit IS ? AND status IN "
                "('NEW','SUBMITTED','RUNNING','INTERRUPTED','DONE')", (cfg_hash, commit)).fetchone()
            if dup:
                die(f"{cfg or name}: same config, parameters and commit as {dup['run_id']} ({dup['status']}). "
                    "Continue that run with `submit`, or pass --allow-duplicate for a replication")
        run_id = make_run_id(conn, root, st["user"], slug)
        run_dir = root / "runs" / run_id
        for sub in ("logs", "checkpoints", "results"):
            (run_dir / sub).mkdir(parents=True, exist_ok=True)
        if cfg_file:
            shutil.copy2(cfg_file, run_dir / f"config{cfg_file.suffix}")
        s3 = st.get("s3_uri") or ""
        ts = now()
        meta = {"run_id": run_id, "user": st["user"], "project": st["project"], "name": slug, "tag": a.tag,
                "git_commit": commit, "git_dirty": dirty, "config_path": cfg_rel, "config_hash": cfg_hash,
                "params": params, "created_at": ts, "s3_uri": f"{s3}/runs/{run_id}" if s3 else None}
        write_json(run_dir / "run.json", meta)
        conn.execute(
            "INSERT INTO runs (run_id, user, project, name, tag, git_commit, git_dirty, config_path, "
            "config_hash, params_json, status, run_dir, s3_uri, note, created_at, updated_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'NEW', ?, ?, ?, ?, ?)",
            (run_id, st["user"], st["project"], slug, a.tag, commit, None if dirty is None else int(dirty),
             cfg_rel, cfg_hash, json.dumps(params, sort_keys=True), str(run_dir), meta["s3_uri"], a.note,
             ts, ts))
        conn.commit()
        print(run_id)


def make_run_id(conn, root: Path, user: str, slug: str) -> str:
    day = time.strftime("%Y%m%d")
    for _ in range(100):
        rid = f"{day}-{user}-{slug}-{secrets.token_hex(2)}"
        taken = conn.execute("SELECT 1 FROM runs WHERE run_id = ?", (rid,)).fetchone()
        if taken is None and not (root / "runs" / rid).exists():
            return rid
    die("no free run ID found; use a more specific --name")


def check_extra_sbatch(extra: list[str], gpus: int) -> None:
    for x in extra:
        if x.startswith(("--time", "--output", "--error", "--job-name", "--export", "--chdir", "--signal")):
            die(f"{x}: d3run sets this flag itself")
        if x.startswith(("--partition", "-p")):
            part = x.split("=", 1)[1] if "=" in x else ""
            if part == "main" and not gpus:
                die("--partition=main without a GPU is rejected by the submit filter; leave --partition out")
            if part == "cpu" and gpus:
                die("--partition=cpu with a GPU is rejected by the submit filter; leave --partition out")
            info("note: --partition is not needed; GPU jobs go to main and CPU-only jobs to cpu by themselves")


def cmd_submit(a) -> None:
    login_only("submit")
    root = project_root(a.root)
    conn = open_registry(root)
    st = get_settings(conn)
    script = Path(a.script).expanduser().resolve()
    if not script.is_file():
        die(f"job script not found: {a.script}")
    limit = parse_slurm_time(a.time)
    if limit > MAX_TIME_S:
        die("at most 24:00:00 per job: longer jobs are accepted but never start. "
            "Checkpoint and use --segments (references/interruptible-jobs.md)")
    if limit > LONG_TIME_S and a.segments == 1:
        info("warning: a limit above 20 h leaves no room; jobs with shorter limits also start earlier "
             "(backfill). Consider 12 h --segments")
    extra = a.sbatch_arg or []
    check_extra_sbatch(extra, a.gpus)
    if a.gpus > 1:
        info("note: 4 GPUs serve the whole group; ask for more than one only if the code uses them")
    export_extra = {"D3RUN_AWS": st.get("aws_bin", ""), "D3RUN_S3_ENDPOINT": st.get("s3_endpoint", ""),
                    "D3RUN_AWS_PROFILE": st.get("aws_profile", "")}
    budget = None if a.no_throttle else share_budget(queue_snapshot(), getpass.getuser(), st)
    if budget:
        info("fair use: " + budget_line(budget))
    held = 0
    for rid in read_ids(a.run_ids):
        run = get_run(conn, rid)
        if run["status"] == "DONE" and not a.force:
            info(f"{rid}: DONE, skipped (--force runs it again)")
            continue
        active = [r["slurm_job_id"] for r in attempts_of(conn, rid) if r["state"] in ACTIVE_JOB_STATES]
        if active and not a.after and not a.force:
            info(f"{rid}: job {active[-1]} is still queued or running (run `reconcile` if that is stale); "
                 f"skipped. Chain behind it with --after {active[-1]}")
            continue
        run_dir = Path(run["run_dir"])
        (run_dir / "logs").mkdir(parents=True, exist_ok=True)
        job_name = f"{run['name']}-{rid[-4:]}"
        last = conn.execute("SELECT MAX(attempt) FROM attempts WHERE run_id = ?", (rid,)).fetchone()[0] or 0
        prev = a.after
        for i in range(a.segments):
            attempt = last + 1 + i
            out = run_dir / "logs" / f"attempt-{attempt:02d}-%j.out"
            err = run_dir / "logs" / f"attempt-{attempt:02d}-%j.err"
            env = {"D3RUN_ID": rid, "D3RUN_DIR": str(run_dir), "D3RUN_ATTEMPT": str(attempt),
                   "D3RUN_TIME_LIMIT_S": str(limit), "D3RUN_SIGNAL_LEAD_S": str(a.signal_lead),
                   "D3RUN_S3_URI": run["s3_uri"] or "", **export_extra}
            if any("," in v for v in env.values()):
                die("commas are not allowed in paths or settings passed to a job")
            cmd = ["sbatch", "--parsable", f"--job-name={job_name}", f"--time={fmt_time(limit)}",
                   f"--cpus-per-task={a.cpus}", f"--mem={a.mem}", f"--output={out}", f"--error={err}",
                   f"--signal=B:USR1@{a.signal_lead}", f"--chdir={root}",
                   "--export=" + ",".join(["ALL"] + [f"{k}={v}" for k, v in env.items()])]
            if a.gpus:
                cmd.append(f"--gres=gpu:{a.gpus}")
            if prev:
                cmd.append(f"--dependency=afterany:{prev}")
            hold = False
            if budget and not prev:          # later segments wait on the first one and are not counted
                need, key = (a.gpus, "free_gpus") if a.gpus else (a.cpus, "free_cpus")
                hold = budget[key] < need
                if not hold:
                    budget[key] -= need
            cmd.append("--comment=d3run")
            if hold:
                cmd.append("--hold")
                held += 1
            cmd += extra + [str(script)] + a.script_args
            if a.dry_run:
                print(shlex.join(cmd))
                prev = f"<job of attempt {attempt}>"
                continue
            res = subprocess.run(cmd, capture_output=True, text=True, cwd=root, env=job_env())
            if res.returncode != 0:
                die(f"{rid}: sbatch failed: {res.stderr.strip()}")
            jid = res.stdout.strip().split(";")[0]
            conn.execute(
                "INSERT INTO attempts (run_id, attempt, slurm_job_id, submitted_at, job_name, depends_on, "
                "req_time_s, req_cpus, req_mem, req_gpus, state, out_path, err_path) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'PENDING', ?, ?)",
                (rid, attempt, jid, now(), job_name, prev, limit, a.cpus, a.mem, a.gpus,
                 str(out).replace("%j", jid), str(err).replace("%j", jid)))
            conn.execute("UPDATE runs SET status = 'SUBMITTED', updated_at = ? WHERE run_id = ?", (now(), rid))
            conn.commit()
            print(f"{rid} attempt {attempt}: job {jid}" + (" (held: fair use)" if hold else ""))
            prev = jid
    if held:
        print(f"{held} job(s) held because other users are waiting. `d3run.py feed` releases them when nobody waits: "
              "it runs with every `reconcile`, or start a feeder job with `d3run.py feed --submit`")


SACCT_FIELDS = ["JobIDRaw", "State", "ExitCode", "ElapsedRaw", "TotalCPU", "MaxRSS", "NodeList",
                "Submit", "Start", "End"]


def sacct(ids: list[str]) -> dict[str, list[dict]]:
    cmd = ["sacct", "--noheader", "--parsable2", "--format=" + ",".join(SACCT_FIELDS), "--jobs=" + ",".join(ids)]
    try:
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    except FileNotFoundError:
        die("sacct not found: run reconcile on the login host")
    if res.returncode != 0:
        die(f"sacct failed: {res.stderr.strip()}")
    out: dict[str, list[dict]] = {}
    current = None
    for line in res.stdout.splitlines():
        f = line.split("|")
        if len(f) < len(SACCT_FIELDS):
            continue
        rec = dict(zip(SACCT_FIELDS, f))
        jid = rec["JobIDRaw"]
        if "." not in jid:
            current = {"jid": jid, "state": (rec["State"].split() or [""])[0], "exit": rec["ExitCode"],
                       "elapsed": int(rec["ElapsedRaw"] or 0), "cpu": parse_duration(rec["TotalCPU"]),
                       "rss": parse_mem_mb(rec["MaxRSS"]), "node": rec["NodeList"], "submit": rec["Submit"],
                       "start": None if rec["Start"] in ("Unknown", "None", "") else rec["Start"],
                       "end": None if rec["End"] in ("Unknown", "None", "") else rec["End"]}
            out.setdefault(jid, []).append(current)
        elif current is not None and jid.split(".")[0] == current["jid"]:
            rss = parse_mem_mb(rec["MaxRSS"])
            if rss is not None and (current["rss"] is None or rss > current["rss"]):
                current["rss"] = rss
    return out


def pick_record(recs: list[dict], submitted_at: str) -> dict:
    """Same Slurm ID twice (IDs restarted): take the record whose submit time is closest to ours."""
    if len(recs) == 1:
        return recs[0]

    def ts(x):
        try:
            return time.mktime(time.strptime(x, TS))
        except (TypeError, ValueError):
            return None

    ref = ts(submitted_at)
    if ref is None:
        return recs[-1]
    return min(recs, key=lambda r: abs((ts(r["submit"]) or 0) - ref))


def gpu_peak(csv_path: Path) -> float | None:
    try:
        lines = csv_path.read_text().splitlines()
    except OSError:
        return None
    peaks = []
    for line in lines:
        parts = [p.strip() for p in line.split(",")]
        if len(parts) >= 2:
            try:
                peaks.append(float(parts[1]))
            except ValueError:
                pass
    return max(peaks) if peaks else None


def derive_status(prev: str, attempts, sj: dict | None) -> str:
    if prev in FINISHED_RUN_STATES:
        return prev
    state = (sj or {}).get("state")
    if state == "done":
        return "DONE"
    if state == "failed":
        return "FAILED"
    if not attempts:
        return prev
    states = [x["state"] for x in attempts]
    if any(s in ACTIVE_JOB_STATES for s in states):
        return "RUNNING" if "RUNNING" in states else "SUBMITTED"
    if state == "interrupted":
        return "INTERRUPTED"
    last = states[-1]
    if last.startswith("CANCELLED"):
        return "CANCELLED"
    if last in FAILED_JOB_STATES:
        return "FAILED"
    if last == "COMPLETED" and sj is None:
        return "DONE"           # a job without d3job: exit code 0 counts as done
    return "INTERRUPTED"        # TIMEOUT, or exit 0 while the job still reported "running"


def import_run_files(conn, run) -> str:
    run_dir = Path(run["run_dir"])
    sj = read_json(run_dir / "status.json")
    new_status = derive_status(run["status"], attempts_of(conn, run["run_id"]), sj)
    progress = (sj or {}).get("progress")
    progress = progress if isinstance(progress, (int, float)) else run["progress"]
    arch = read_json(run_dir / "archive.json") or {}
    conn.execute("UPDATE runs SET status = ?, progress = ?, archived_at = COALESCE(?, archived_at), "
                 "cleaned_at = COALESCE(?, cleaned_at), copied_to = COALESCE(?, copied_to), updated_at = ? "
                 "WHERE run_id = ?",
                 (new_status, progress, arch.get("verified_at"), arch.get("cleaned_at"), arch.get("copied_to"),
                  now(), run["run_id"]))
    return new_status


def cmd_reconcile(a) -> None:
    login_only("reconcile")
    root = project_root(a.root)
    conn = open_registry(root)
    if a.all:
        rows = conn.execute("SELECT * FROM attempts").fetchall()
    else:
        marks = ",".join("?" * len(ACTIVE_JOB_STATES))
        rows = conn.execute(f"SELECT * FROM attempts WHERE state IN ({marks})", ACTIVE_JOB_STATES).fetchall()
    ids = sorted({r["slurm_job_id"] for r in rows if r["slurm_job_id"]})
    acct: dict[str, list[dict]] = {}
    for i in range(0, len(ids), 200):
        acct.update(sacct(ids[i:i + 200]))
    for r in rows:
        recs = acct.get(r["slurm_job_id"])
        if not recs:
            continue
        rec = pick_record(recs, r["submitted_at"])
        conn.execute("UPDATE attempts SET state = ?, exit_code = ?, elapsed_s = ?, total_cpu_s = ?, max_rss_mb = ?, "
                     "node = ?, started_at = ?, ended_at = ? WHERE run_id = ? AND attempt = ?",
                     (rec["state"], rec["exit"], rec["elapsed"], rec["cpu"], rec["rss"], rec["node"],
                      rec["start"], rec["end"], r["run_id"], r["attempt"]))
    for r in conn.execute("SELECT a.run_id, a.attempt, a.slurm_job_id, r.run_dir FROM attempts a "
                          "JOIN runs r USING (run_id) WHERE a.gpu_mem_mb IS NULL AND a.slurm_job_id IS NOT NULL "
                          "AND a.elapsed_s IS NOT NULL").fetchall():
        peak = gpu_peak(Path(r["run_dir"]) / "logs" / f"gpu-{r['slurm_job_id']}.csv")
        if peak is not None:
            conn.execute("UPDATE attempts SET gpu_mem_mb = ? WHERE run_id = ? AND attempt = ?",
                         (peak, r["run_id"], r["attempt"]))
    query = "SELECT * FROM runs" if a.all else (
        "SELECT * FROM runs WHERE status NOT IN ('DONE','FAILED','CANCELLED') OR archived_at IS NULL "
        "OR cleaned_at IS NULL")
    counts: dict[str, int] = {}
    pending_after_done = []
    for run in conn.execute(query).fetchall():
        status = import_run_files(conn, run)
        counts[status] = counts.get(status, 0) + 1
        if status == "DONE":
            pending_after_done += [x["slurm_job_id"] for x in attempts_of(conn, run["run_id"])
                                   if x["state"] == "PENDING"]
    conn.commit()
    print(f"updated {len(rows)} attempts; runs checked: " +
          (", ".join(f"{k} {v}" for k, v in sorted(counts.items())) or "none"))
    if pending_after_done:
        print("finished runs still have queued segments (they exit at once, or cancel them): scancel "
              + " ".join(pending_after_done))
    if not a.no_feed:
        print("fair use: " + feed_pass(get_settings(conn), getpass.getuser())[0])


def cmd_show(a) -> None:
    root = project_root(a.root)
    conn = open_registry(root)
    run = get_run(conn, a.run_id)
    for k in run.keys():
        if run[k] not in (None, ""):
            print(f"{k:12} {run[k]}")
    rows = attempts_of(conn, a.run_id)
    if rows:
        print("\nattempt job        state         elapsed  cpu-used  max-rss  gpu-mem  requested")
        for r in rows:
            el = f"{r['elapsed_s'] / 3600:.2f} h" if r["elapsed_s"] else "-"
            cpu = f"{r['total_cpu_s'] / r['elapsed_s']:.1f}" if r["total_cpu_s"] and r["elapsed_s"] else "-"
            rss = f"{r['max_rss_mb'] / 1024:.1f} G" if r["max_rss_mb"] else "-"
            gpu = f"{r['gpu_mem_mb'] / 1024:.1f} G" if r["gpu_mem_mb"] else "-"
            req = f"{fmt_time(r['req_time_s'] or 0)} {r['req_cpus']}c {r['req_mem']} {r['req_gpus'] or 0}g"
            print(f"{r['attempt']:>7} {r['slurm_job_id'] or '-':10} {r['state']:13} {el:>8} {cpu:>9} {rss:>8} "
                  f"{gpu:>8}  {req}")
            print(f"        log {r['out_path']}")


def cmd_list(a) -> None:
    root = project_root(a.root)
    conn = open_registry(root)
    q, args = "SELECT * FROM runs WHERE 1=1", []
    if a.tag:
        q += " AND tag = ?"
        args.append(a.tag)
    if a.status:
        q += " AND status = ?"
        args.append(a.status.upper())
    if a.since:
        q += " AND created_at >= ?"
        args.append(a.since)
    for run in conn.execute(q + " ORDER BY created_at", args).fetchall():
        att = attempts_of(conn, run["run_id"])
        last = att[-1] if att else None
        hours = sum(x["elapsed_s"] or 0 for x in att) / 3600
        copy = run["copied_to"] or "s3"
        where = copy if run["cleaned_at"] else (f"{copy}+server" if run["archived_at"] else "server")
        print(f"{run['run_id']:44} {run['status']:11} {len(att):>2} att  "
              f"{(last['slurm_job_id'] + ' ' + last['state']) if last else '-':22} {hours:6.2f} h  {where:8} "
              f"{run['tag'] or ''}")


def cmd_find_job(a) -> None:
    root = project_root(a.root)
    conn = open_registry(root)
    rows = conn.execute("SELECT * FROM attempts WHERE slurm_job_id = ? ORDER BY submitted_at DESC",
                        (a.slurm_job_id,)).fetchall()
    if not rows:
        die(f"no attempt with Slurm job {a.slurm_job_id}")
    if len(rows) > 1:
        info(f"Slurm job ID {a.slurm_job_id} was used {len(rows)} times (IDs restarted); newest first")
    for r in rows:
        print(f"{r['run_id']}  attempt {r['attempt']}  submitted {r['submitted_at']}  {r['state']}")


def cmd_size(a) -> None:
    root = project_root(a.root)
    conn = open_registry(root)
    runs = conn.execute("SELECT * FROM runs WHERE tag = ?", (a.tag,)).fetchall() if a.tag \
        else [get_run(conn, rid) for rid in a.run_ids]
    if not runs:
        die("no runs selected (give --tag or run IDs)")
    totals, rss, cores, gpu, notes, req_cpus = [], [], [], [], [], []
    for run in runs:
        att = [x for x in attempts_of(conn, run["run_id"]) if x["elapsed_s"]]
        if not att:
            continue
        if run["status"] in ("FAILED", "CANCELLED"):
            if any(x["state"] == "OUT_OF_MEMORY" for x in att):
                notes.append(f"{run['run_id']}: ran out of memory at {att[-1]['req_mem']}; raise --mem")
            else:
                notes.append(f"{run['run_id']}: {run['status'].lower()}, left out")
            continue
        elapsed = sum(x["elapsed_s"] for x in att)
        if run["status"] == "DONE":
            totals.append(elapsed)
        elif run["progress"] and 0 < run["progress"] < 1:
            totals.append(elapsed / run["progress"])
            notes.append(f"{run['run_id']}: total time extrapolated from progress {run['progress']:.0%}")
        else:
            totals.append(elapsed)
            notes.append(f"{run['run_id']}: not finished and no progress reported, its time is a lower bound")
        rss += [x["max_rss_mb"] for x in att if x["max_rss_mb"]]
        cores += [x["total_cpu_s"] / x["elapsed_s"] for x in att if x["total_cpu_s"] and x["elapsed_s"] >= 60]
        gpu += [x["gpu_mem_mb"] for x in att if x["gpu_mem_mb"]]
        req_cpus += [x["req_cpus"] for x in att if x["req_cpus"]]
    if not totals:
        die("no attempts with accounting data yet: run `reconcile` after the pilot jobs have ended")
    m = a.margin
    need = max(totals) * m
    if need <= LONG_TIME_S:
        seg_time, segments = ceil_quarter_hour(need), 1
    else:
        seg_time = SEGMENT_S
        segments = math.ceil(need / (SEGMENT_S - 900))
    flags = [f"--time {fmt_time(seg_time)}"]
    print(f"runs measured      {len(totals)} ({sum(1 for r in runs if r['status'] == 'DONE')} done)")
    print(f"longest run        {max(totals) / 3600:.2f} h  -> --time {fmt_time(seg_time)}"
          + (f" x {segments} segments" if segments > 1 else "") + f"  (margin {m})")
    if segments > 1:
        flags.append(f"--segments {segments}")
    if cores:
        c = max(1, math.ceil(max(cores) - 0.05))
        print(f"CPU cores used     {max(cores):.2f} (requested {max(req_cpus) if req_cpus else '?'})  -> --cpus {c}")
        flags.append(f"--cpus {c}")
    if rss:
        g = max(1, math.ceil(max(rss) * m / 1024))
        print(f"peak memory        {max(rss) / 1024:.2f} GB  -> --mem {g}G")
        flags.append(f"--mem {g}G")
    if gpu:
        print(f"peak GPU memory    {max(gpu) / 1024:.2f} GB of 24 GB (RTX 4090)")
        flags.append("--gpus 1")
    for n in notes:
        print(f"note: {n}")
    print("flags: " + " ".join(flags))


def cmd_archive(a) -> None:
    root = project_root(a.root)
    if a.no_registry:                                  # inside the transfer job
        st, s3 = s3_settings(root, a)
        targets = [(rid, root / "runs" / rid, f"{s3}/runs/{rid}", False) for rid in a.run_ids]
    else:
        login_only("archive")
        conn = open_registry(root)
        st = get_settings(conn)
        s3 = st.get("s3_uri") or ""
        if not s3:
            s3_settings(root, a)                       # dies with the setup hint
        if a.run_ids:
            runs = [get_run(conn, rid) for rid in a.run_ids]
        elif a.tag:
            runs = conn.execute("SELECT * FROM runs WHERE tag = ?", (a.tag,)).fetchall()
        elif a.finished:
            runs = conn.execute("SELECT * FROM runs WHERE status IN ('DONE','FAILED','CANCELLED') "
                                "AND cleaned_at IS NULL").fetchall()
        else:
            die("give run IDs, --tag or --finished")
        targets = []
        for run in runs:
            sj = read_json(Path(run["run_dir"]) / "status.json") or {}
            active = run["status"] in ("SUBMITTED", "RUNNING") or sj.get("state") == "running" or any(
                x["state"] in ACTIVE_JOB_STATES for x in attempts_of(conn, run["run_id"]))
            if active and a.clean:
                info(f"{run['run_id']}: queued or running, uploaded but not cleaned")
            targets.append((run["run_id"], Path(run["run_dir"]), run["s3_uri"] or f"{s3}/runs/{run['run_id']}",
                            active))
        snapshot_registry(conn, aws_cmd(st), s3)
    if not targets:
        print("nothing to archive")
        return
    if a.submit:
        job_args = ["archive", "--no-registry", "--s3-uri", s3] + (["--clean"] if a.clean else []) + \
                   [rid for rid, _, _, active in targets if not (active and a.clean)]
        submit_self(root, job_args, st, a.job_time)
        return
    sizes = [walk(d) for _, d, _, _ in targets if d.is_dir()]
    guard_login(sum(len(s) for s in sizes), sum(sum(s.values()) for s in sizes), a.here, "archive")
    aws = aws_cmd(st)
    freed_total = 0
    for rid, run_dir, uri, active in targets:
        msg, freed = archive_one(aws, rid, run_dir, uri, a.clean and not active)
        freed_total += freed
        print(msg)
    if not a.no_registry:
        for rid, *_ in targets:
            import_run_files(conn, get_run(conn, rid))
        conn.commit()
    if a.clean:
        print(f"freed {freed_total / 2**30:.2f} GB on the server")


def archive_one(aws: list[str], rid: str, run_dir: Path, uri: str, clean: bool) -> tuple[str, int]:
    if not run_dir.is_dir():
        return f"{rid}: no local folder", 0
    ok, d = sync_verify(aws, run_dir, uri)
    rec = read_json(run_dir / "archive.json") or {}
    rec.update({"run_id": rid, "s3_uri": uri, "files": d["files"], "bytes": d["bytes"]})
    if not ok:
        rec["missing"] = d["missing"][:20]
        write_json(run_dir / "archive.json", rec)
        return f"{rid}: NOT verified ({d.get('error') or str(len(d['missing'])) + ' files differ'}); kept", 0
    rec["verified_at"] = now()
    rec.pop("missing", None)
    freed = 0
    if clean:
        for child in run_dir.iterdir():
            if child.name in KEEP_AFTER_CLEAN:
                continue
            freed += sum(walk(child).values()) if child.is_dir() else child.stat().st_size
            shutil.rmtree(child) if child.is_dir() else child.unlink()
        rec["cleaned_at"] = now()
        rec["freed_bytes"] = freed
    write_json(run_dir / "archive.json", rec)
    subprocess.run(aws + ["s3", "cp", str(run_dir / "archive.json"), f"{uri}/archive.json", "--only-show-errors"],
                   capture_output=True)
    return f"{rid}: {d['files']} files, {d['bytes'] / 2**20:.1f} MB verified in {uri}" + \
        (f"; local copy removed" if clean else ""), freed


def snapshot_registry(conn, aws: list[str], s3: str) -> None:
    with tempfile.TemporaryDirectory() as td:
        snap = Path(td) / "registry.db"
        dst = sqlite3.connect(snap)
        conn.backup(dst)
        dst.close()
        uri = f"{s3}/registry/registry-{time.strftime('%Y%m%d')}.db"
        res = subprocess.run(aws + ["s3", "cp", str(snap), uri, "--only-show-errors"], capture_output=True, text=True)
        if res.returncode != 0:
            info(f"registry snapshot not uploaded: {res.stderr.strip()}")


def inside_root(root: Path, p: str) -> Path:
    path = (root / p).resolve() if not Path(p).is_absolute() else Path(p).resolve()
    if path == root or root not in path.parents:
        die(f"{p}: give a folder or file inside the project, not the project itself")
    return path


def refuse_tracked(root: Path, path: Path) -> None:
    tracked = subprocess.run(["git", "-C", str(root), "ls-files", "--", str(path)], capture_output=True, text=True)
    if tracked.stdout.strip():
        die(f"{path}: contains files tracked by git; --clean never deletes code or tracked files")
    if path == root / "runs" or path.name == "registry.db" or root / "runs" / "registry.db" in path.parents:
        die("the registry and the runs/ folder as a whole are never cleaned; clean single runs (runs/<run_id>)")


def cmd_push(a) -> None:
    root = project_root(a.root)
    st, s3 = s3_settings(root, a)
    paths = [inside_root(root, p) for p in a.paths]
    for p in paths:
        if not p.exists():
            die(f"{p} does not exist")
        if a.clean:
            refuse_tracked(root, p)
    if a.submit:
        submit_self(root, ["push", "--s3-uri", s3] + (["--clean"] if a.clean else []) +
                    [p.relative_to(root).as_posix() for p in paths], st, a.job_time)
        return
    sizes = [walk(p) for p in paths]
    guard_login(sum(len(s) for s in sizes), sum(sum(s.values()) for s in sizes), a.here, "push")
    aws = aws_cmd(st)
    for p in paths:
        rel = p.relative_to(root).as_posix()
        ok, d = sync_verify(aws, p, f"{s3}/{rel}")
        if not ok:
            print(f"{rel}: NOT verified ({d.get('error') or str(len(d['missing'])) + ' files differ'}); kept")
            continue
        print(f"{rel}: {d['files']} files, {d['bytes'] / 2**20:.1f} MB verified in {s3}/{rel}")
        if a.clean:
            shutil.rmtree(p) if p.is_dir() else p.unlink()
            print(f"{rel}: local copy removed")


def cmd_pull(a) -> None:
    root = project_root(a.root)
    st, s3 = s3_settings(root, a)
    aws = aws_cmd(st)
    paths = [inside_root(root, p) for p in a.paths]
    if a.submit:
        submit_self(root, ["pull", "--s3-uri", s3] + [p.relative_to(root).as_posix() for p in paths], st,
                    a.job_time)
        return
    for p in paths:
        rel = p.relative_to(root).as_posix()
        remote = remote_sizes(aws, f"{s3}/{rel}") or {}
        guard_login(len(remote), sum(remote.values()), a.here, f"pull {rel}")
        ok, d = sync_verify(aws, p, f"{s3}/{rel}", direction="down")
        print(f"{rel}: " + (f"{d['files']} files, {d['bytes'] / 2**20:.1f} MB verified" if ok else
                            f"NOT verified ({d.get('error') or str(len(d['missing'])) + ' files differ'})"))


def cmd_manifest(a) -> None:
    """Files and sizes below project paths: of the server checkout, or of a copy (--root <copy>)."""
    root = Path(a.root).expanduser().resolve() if a.root else project_root(None)
    paths = list(a.paths)
    if a.finished:
        path = root / "runs" / "registry.db"
        conn = sqlite3.connect(f"file:{path}?mode=ro", uri=True, timeout=30)
        paths += [f"runs/{r[0]}" for r in conn.execute(
            "SELECT run_id FROM runs WHERE status IN ('DONE','FAILED','CANCELLED') AND cleaned_at IS NULL "
            "ORDER BY created_at")]
    if a.list:
        print("\n".join(paths))
        return
    out = {"root": str(root), "made_at": now(), "paths": {}}
    for rel in paths:
        target = root / rel
        if target.exists():
            out["paths"][rel] = walk(target)
        else:
            info(f"{rel}: not found below {root}")
    print(json.dumps(out, indent=1, sort_keys=True))


def cmd_clean(a) -> None:
    """Delete on the server what a verified copy holds: every file present in the manifest with the same size."""
    root = project_root(a.root)
    text = sys.stdin.read() if a.manifest == "-" else Path(a.manifest).read_text()
    try:
        copy = json.loads(text)["paths"]
    except (ValueError, KeyError):
        die("the manifest must be the JSON that `d3run.py manifest` prints")
    conn = None
    if not in_job():
        conn = open_registry(root)
    targets = []
    for rel in copy:
        p = inside_root(root, rel)
        if not p.exists():
            print(f"{rel}: not on the server (cleaned already?)")
            continue
        is_run = p.parent == root / "runs"
        if not is_run:
            refuse_tracked(root, p)
        if is_run and conn is not None:
            run = conn.execute("SELECT * FROM runs WHERE run_id = ?", (p.name,)).fetchone()
            sj = read_json(p / "status.json") or {}
            if run is not None and (run["status"] in ("SUBMITTED", "RUNNING") or sj.get("state") == "running" or any(
                    x["state"] in ACTIVE_JOB_STATES for x in attempts_of(conn, p.name))):
                print(f"{rel}: queued or running, not cleaned")
                continue
        targets.append((rel, p, is_run))
    if a.submit:
        saved = root / "runs" / f"manifest-{time.strftime('%Y%m%d-%H%M%S')}.json"
        saved.write_text(text)
        submit_self(root, ["clean", "--manifest", str(saved), "--copied-to", a.copied_to], {}, a.job_time,
                    name="d3run-clean")
        return
    sizes = [walk(p) for _, p, _ in targets]
    guard_login(sum(len(x) for x in sizes), 0, a.here, "clean")
    freed_total = 0
    for (rel, p, is_run), local in zip(targets, sizes):
        theirs = copy[rel]
        missing = sorted(k for k, v in local.items() if theirs.get(k) != v)
        if missing:
            print(f"{rel}: NOT cleaned, {len(missing)} files missing or different in the copy (e.g. {missing[0]})")
            continue
        freed = 0
        if is_run:
            for child in p.iterdir():
                if child.name in KEEP_AFTER_CLEAN:
                    continue
                freed += sum(walk(child).values()) if child.is_dir() else child.stat().st_size
                shutil.rmtree(child) if child.is_dir() else child.unlink()
            rec = read_json(p / "archive.json") or {}
            rec.update({"run_id": p.name, "copied_to": a.copied_to, "files": len(local), "bytes": sum(local.values()),
                        "verified_at": now(), "cleaned_at": now(), "freed_bytes": freed})
            write_json(p / "archive.json", rec)
            if conn is not None and conn.execute("SELECT 1 FROM runs WHERE run_id = ?", (p.name,)).fetchone():
                import_run_files(conn, get_run(conn, p.name))
        else:
            freed = sum(local.values())
            shutil.rmtree(p) if p.is_dir() else p.unlink()
        freed_total += freed
        print(f"{rel}: {len(local)} files verified in the copy ({a.copied_to}); removed from the server")
    if conn is not None:
        conn.commit()
    print(f"freed {freed_total / 2**30:.2f} GB on the server")


def cmd_usage(a) -> None:
    root = project_root(a.root)
    rows, total = [], 0
    base = root / "runs"
    if base.is_dir():
        for d in base.iterdir():
            if d.is_dir():
                files = walk(d)
                b = sum(files.values())
                rows.append((b, len(files), d.name))
                total += b
    rows.sort(reverse=True)
    print(f"runs/ total {total / 2**30:.2f} GB in {len(rows)} run folders")
    for b, n, name in rows[:a.top]:
        print(f"  {b / 2**30:8.2f} GB {n:7} files  {name}")
    for name in a.also:
        p = root / name
        if p.exists():
            files = walk(p)
            print(f"{name}/ {sum(files.values()) / 2**30:.2f} GB in {len(files)} files")
    print("home quota: warning above 100 GB, hard limit 200 GB. The whole-home figure is in Grafana; "
          "`du -sh ~` over NFS with many files is slow")


def cmd_feed(a) -> None:
    root = project_root(a.root)
    st = read_settings_ro(root)
    me = getpass.getuser()
    if a.submit:
        submit_self(root, ["feed", "--loop", "--hours", str(a.hours), "--interval", str(a.interval)], st,
                    fmt_time(min(MAX_TIME_S, a.hours * 3600 + 600)), cpus=1, mem="1G", name="d3run-feed")
        return
    end = time.time() + a.hours * 3600
    while True:
        line, still = feed_pass(st, me)
        print(line, flush=True)
        if not a.loop or still == 0 or time.time() + a.interval > end:
            break
        time.sleep(a.interval)
    if a.loop and still:
        print(f"{still} job(s) still held; start another feeder (`feed --submit`) or run `reconcile` regularly")


def cmd_mark(a) -> None:
    login_only("mark")
    root = project_root(a.root)
    conn = open_registry(root)
    get_run(conn, a.run_id)
    status = a.status.upper()
    if status not in RUN_STATES:
        die(f"status must be one of {', '.join(RUN_STATES)}")
    conn.execute("UPDATE runs SET status = ?, note = COALESCE(?, note), updated_at = ? WHERE run_id = ?",
                 (status, a.note, now(), a.run_id))
    conn.commit()
    print(f"{a.run_id}: {status}")


# ---------------------------------------------------------------- CLI

def build_parser() -> argparse.ArgumentParser:
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--root", help="project folder (default: git top level, or $D3RUN_ROOT)")
    p = argparse.ArgumentParser(prog="d3run.py", description=__doc__.split("\n\n")[0],
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="command", required=True)

    s = sub.add_parser("init", parents=[common], help="create or update the registry settings")
    s.add_argument("--user", help="server login name, part of every run ID (e.g. abcd)")
    s.add_argument("--project", help="project name (default: folder name)")
    s.add_argument("--s3-uri", help="s3://<bucket>/<project>: where runs and data live")
    s.add_argument("--no-s3", action="store_true", help="no bucket yet")
    s.add_argument("--s3-endpoint", help="S3 endpoint URL, if not in ~/.aws/config")
    s.add_argument("--aws-profile", help="AWS CLI profile, if not the default")
    s.add_argument("--aws-bin", help="path of the aws binary (default: aws on PATH, then ~/.local/bin/aws)")
    s.add_argument("--share-gpus", type=int, help=f"GPUs your jobs may hold while others wait (default {SHARE_GPUS})")
    s.add_argument("--share-cpus", type=int, help=f"CPUs in `cpu` your jobs may hold while others wait (default {SHARE_CPUS})")
    s.set_defaults(func=cmd_init)

    s = sub.add_parser("settings", parents=[common], help="show the registry settings (read-only)")
    s.set_defaults(func=cmd_settings)

    s = sub.add_parser("new", parents=[common], help="create run IDs before submitting")
    s.add_argument("--config", nargs="+", help="one run per config file")
    s.add_argument("--name", help="readable name (slug) for the run ID")
    s.add_argument("--tag", help="round or study the runs belong to")
    s.add_argument("--param", action="append", help="key=value stored with the run (repeatable)")
    s.add_argument("--note")
    s.add_argument("--allow-dirty", action="store_true", help="smoke tests only: uncommitted tracked changes")
    s.add_argument("--allow-duplicate", action="store_true", help="replication of an existing config")
    s.set_defaults(func=cmd_new)

    s = sub.add_parser("submit", parents=[common], help="submit runs (one attempt per segment)",
                       description="Arguments after -- go to the job script.")
    s.add_argument("run_ids", nargs="+", help="run IDs, or - to read them from stdin")
    s.add_argument("--script", required=True, help="sbatch script (assets/job_template.sbatch)")
    s.add_argument("--time", required=True, help="limit per segment, HH:MM:SS, at most 24:00:00")
    s.add_argument("--cpus", type=int, default=1)
    s.add_argument("--mem", default="4G")
    s.add_argument("--gpus", type=int, default=0)
    s.add_argument("--segments", type=int, default=1, help="chain of attempts linked by afterany")
    s.add_argument("--after", help="start the first segment after this Slurm job")
    s.add_argument("--signal-lead", type=int, default=600, help="seconds of warning before the limit")
    s.add_argument("--sbatch-arg", action="append", help="extra sbatch flag, e.g. --sbatch-arg=--nice=100")
    s.add_argument("--force", action="store_true", help="submit even if DONE or still queued")
    s.add_argument("--no-throttle", action="store_true", help="skip the fair-use check (nobody else uses the server)")
    s.add_argument("--dry-run", action="store_true", help="print the sbatch commands only")
    s.set_defaults(func=cmd_submit)

    s = sub.add_parser("reconcile", parents=[common], help="update states and usage from sacct and run files")
    s.add_argument("--all", action="store_true", help="recheck every attempt and run")
    s.add_argument("--no-feed", action="store_true", help="skip the fair-use pass (release/hold)")
    s.set_defaults(func=cmd_reconcile)

    s = sub.add_parser("show", parents=[common], help="one run with its attempts and logs")
    s.add_argument("run_id")
    s.set_defaults(func=cmd_show)

    s = sub.add_parser("list", parents=[common], help="list runs")
    s.add_argument("--tag")
    s.add_argument("--status")
    s.add_argument("--since", help="YYYY-MM-DD")
    s.set_defaults(func=cmd_list)

    s = sub.add_parser("find-job", parents=[common], help="which run a Slurm job ID belongs to")
    s.add_argument("slurm_job_id")
    s.set_defaults(func=cmd_find_job)

    s = sub.add_parser("size", parents=[common], help="suggest --time/--cpus/--mem from measured attempts")
    s.add_argument("run_ids", nargs="*")
    s.add_argument("--tag")
    s.add_argument("--margin", type=float, default=1.3)
    s.set_defaults(func=cmd_size)

    for name, func, hlp in (("archive", cmd_archive, "upload run folders to S3, verify, optionally clean"),
                            ("push", cmd_push, "upload project paths (e.g. data/raw) to S3, verify, optionally clean"),
                            ("pull", cmd_pull, "download project paths from S3 and verify")):
        s = sub.add_parser(name, parents=[common], help=hlp)
        if name == "archive":
            s.add_argument("run_ids", nargs="*")
            s.add_argument("--tag")
            s.add_argument("--finished", action="store_true", help="all DONE/FAILED/CANCELLED runs not yet cleaned")
            s.add_argument("--no-registry", action="store_true", help=argparse.SUPPRESS)
        else:
            s.add_argument("paths", nargs="+", help="paths inside the project; S3 mirrors the layout")
        if name != "pull":
            s.add_argument("--clean", action="store_true", help="delete the local copy once verified")
        s.add_argument("--submit", action="store_true", help="run the transfer as a Slurm job")
        s.add_argument("--here", action="store_true", help="run on the login host despite the size")
        s.add_argument("--job-time", default="04:00:00", help="time limit of the transfer job")
        s.add_argument("--s3-uri", help=argparse.SUPPRESS)
        s.set_defaults(func=func)

    s = sub.add_parser("manifest", parents=[common], help="files and sizes of project paths (server or a copy)")
    s.add_argument("paths", nargs="*", help="project paths, e.g. runs/<id> data/raw")
    s.add_argument("--finished", action="store_true", help="add all finished runs not yet cleaned (server)")
    s.add_argument("--list", action="store_true", help="print the paths only (for rsync --files-from)")
    s.set_defaults(func=cmd_manifest)

    s = sub.add_parser("clean", parents=[common], help="delete on the server what a verified copy holds")
    s.add_argument("--manifest", required=True, help="manifest JSON of the copy (`manifest --root <copy>`), or -")
    s.add_argument("--copied-to", required=True, help="where the copy lives, e.g. laptop:~/d3-archive/<project>")
    s.add_argument("--submit", action="store_true", help="run the deletion as a Slurm job (many files)")
    s.add_argument("--here", action="store_true", help="run on the login host despite the file count")
    s.add_argument("--job-time", default="02:00:00")
    s.set_defaults(func=cmd_clean)

    s = sub.add_parser("usage", parents=[common], help="disk use of run folders (and other folders)")
    s.add_argument("--top", type=int, default=15)
    s.add_argument("--also", nargs="*", default=["data", "results", "logs"])
    s.set_defaults(func=cmd_usage)

    s = sub.add_parser("feed", parents=[common], help="fair use: release held jobs when nobody else waits")
    s.add_argument("--loop", action="store_true", help="repeat until no job is held (or --hours pass)")
    s.add_argument("--interval", type=int, default=300, help="seconds between checks (default 300)")
    s.add_argument("--hours", type=float, default=23.5, help="how long a loop or feeder job runs at most")
    s.add_argument("--submit", action="store_true", help="run the loop as a 1-CPU Slurm job (feeder)")
    s.add_argument("--here", action="store_true", help=argparse.SUPPRESS)
    s.set_defaults(func=cmd_feed)

    s = sub.add_parser("mark", parents=[common], help="set a run's status by hand")
    s.add_argument("run_id")
    s.add_argument("status")
    s.add_argument("--note")
    s.set_defaults(func=cmd_mark)
    return p


def main(argv: list[str] | None = None) -> None:
    argv = list(sys.argv[1:] if argv is None else argv)
    script_args: list[str] = []
    if "--" in argv:
        i = argv.index("--")
        argv, script_args = argv[:i], argv[i + 1:]
    a = build_parser().parse_args(argv)
    a.script_args = script_args
    a.func(a)


if __name__ == "__main__":
    main()
