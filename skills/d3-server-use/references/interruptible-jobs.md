# Interruptible jobs

A job ends after at most 24 h, and it can also die earlier (out of memory, node problem, admin maintenance). Code
that runs longer than a few hours must therefore save its state regularly, pick it up again, and run as a chain of
segments. `d3job.py` (stdlib, copied into the project next to `d3run.py`) does the bookkeeping.

## Contents
1. The four mechanisms
2. RunContext in a training loop
3. PyTorch
4. JAX / Flax with Orbax
5. Work lists (configs, seeds, chunks)
6. Segments and chains
7. Testing the resume
8. What not to rely on

## 1. The mechanisms

1. **The exact end.** The job knows when Slurm will stop it: `SLURM_JOB_END_TIME` if Slurm sets it, otherwise
   the start the job template records (`D3RUN_JOB_START`, before `uv` and imports) plus the limit `d3run.py
   submit` passes (`D3RUN_TIME_LIMIT_S`), otherwise one `squeue -j <id> -o %L` call at start. The log says which.
2. **A measured margin, not a fixed one.** `ctx.should_checkpoint()`, called once per step, measures the step
   time; `ctx.checkpoint()` measures the save time. `ctx.should_stop()` turns true when the time left drops below
   `1.5 × (longest recent step + longest recent save) + 30 s`. With 2 s steps and a 10 s save the job stops about
   48 s before the limit; with 20 min epochs it stops in time for one more epoch and its save. Until both are
   measured, guesses apply (step 60 s, save 120 s, so 5 minutes), capped at a quarter of the limit for short smoke
   jobs, and the first checkpoint comes after 5 minutes so the save time is known early. `margin_s=` fixes the
   margin; `safety_s=` changes the 30 s.
3. **USR1 confirms the end.** `--signal=B:USR1@600` makes Slurm signal the job shell ten minutes before the limit;
   the template's trap writes that end time into `runs/<id>/STOP`, and the context takes it if it is earlier than
   its own estimate (for example after an admin shortened the limit). It does not stop the job early. SIGTERM, which
   Slurm sends at the limit, stops at the next check. No signal has to pass through `uv run` to Python.
4. **Checkpoints on a timer** (`every_s`, default 30 minutes) bound the loss when a job dies without warning.
5. **Atomic, consistent state.** A checkpoint is written to a temporary path, renamed when complete, listed in
   `checkpoints/LATEST.json`, then uploaded (checkpoint first, `LATEST.json` after, so S3 always points to a
   complete one), and only then are older ones pruned (1 kept locally, 2 in S3; 2 locally while the newest is not
   uploaded). An upload that could run into the end of the job is skipped: the checkpoint stays local and the next
   upload, or the next segment at its start, takes it. `status.json` records `running`, `interrupted` (with
   `progress`), `done` or `failed`.

## 2. RunContext in a training loop

```python
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))   # where d3job.py lives
from d3job import RunContext

ctx = RunContext.from_env()                 # every_s=1800, keep_local=1, keep_remote=2, safety_s=30
if ctx.finished():                          # done, or failed (needs a human): later segments exit at once
    raise SystemExit(0)
ckpt = ctx.latest_checkpoint()              # local (uploaded first if it is not in S3 yet), else from S3, else None
state, start = (load(ckpt), load_step(ckpt) + 1) if ckpt else (init(), 0)
ctx.mark("running")
try:
    for step in range(start, n_steps):
        train_one_step(state)
        if ctx.should_checkpoint():                     # once per step: measures it; timer due or end near
            with ctx.checkpoint(step) as path:          # write into `path`: a file or a folder
                save(state, step, path)
            if ctx.should_stop():
                ctx.mark("interrupted", progress=(step + 1) / n_steps)
                raise SystemExit(0)                     # exit 0: the next segment resumes
    write_results(ctx.results_dir)                      # metrics, predictions, small files
    ctx.finish()                                        # uploads results/, marks done
except Exception as exc:
    ctx.fail(exc)
    raise
```

- Without `D3RUN_*` variables (on the laptop) the same code runs in `runs/local/` without S3 and without a budget.
- Report `progress` (0 to 1) with `interrupted`: `d3run.py size` extrapolates a pilot's total time from it.
- Call `should_checkpoint()` exactly once per step (an epoch, a batch, a work unit): it measures the step time
  from one call to the next, without the time spent in checkpoints.
- Steps of very different length (a validation epoch every tenth epoch): the margin uses the longest of the last 20
  steps, so it adapts after the first long one. To be safe from the first step on, pass `step_guess_s=`.
- Results go to `ctx.results_dir`; everything under the run folder reaches S3 with `finish()` or `archive`.

## 3. PyTorch

Save everything that changes during training, not only the weights:

```python
def save(path):
    torch.save({"model": model.state_dict(), "optim": optim.state_dict(), "sched": sched.state_dict(),
                "scaler": scaler.state_dict() if scaler else None, "epoch": epoch, "step": step,
                "rng": {"torch": torch.get_rng_state(), "cuda": torch.cuda.get_rng_state_all(),
                        "numpy": np.random.get_state(), "python": random.getstate()},
                "best_val": best_val}, path)          # `path` is a file here

ck = torch.load(ctx.latest_checkpoint(), map_location="cpu", weights_only=False)
```

Resume mid-epoch only if the data order is reproducible (seeded sampler plus the step); otherwise checkpoint at epoch
ends and size the margin to one epoch.

## 4. JAX / Flax with Orbax

- Orbax needs an **absolute** path: `ocp.StandardCheckpointer().save(path.resolve(), state)` inside
  `with ctx.checkpoint(step) as path:`, then `checkpointer.wait_until_finished()` before the block ends, so the
  rename happens only after the asynchronous write is complete.
- Save optimizer state, step, RNG keys and any state the model keeps outside its parameters (grids, buffers or
  statistics stored as plain attributes): a restore without it loads the parameters onto a different function.
- CPU-only JAX jobs: `JAX_PLATFORMS=cpu` (the CUDA plugin traceback in the log is harmless). Large models on one GPU:
  `XLA_PYTHON_CLIENT_MEM_FRACTION=0.95`, or `XLA_PYTHON_CLIENT_PREALLOCATE=false` while measuring the real peak
  in a pilot (the default preallocation shows 75 % of the GPU in `nvidia-smi` whatever the model needs).

## 5. Work lists (configs, seeds, chunks)

Many short units inside one job (evaluation metrics, post-processing, a seed sweep in one process):

- One result file per unit, written atomically (temp name, then `os.replace`). On start, skip the units whose result
  exists: the result files are the checkpoint.
- Check `ctx.should_stop()` between units; mark `interrupted` with `progress = done / total`.
- Give every unit a timeout (a solver's time limit, or a watchdog per unit) and record a unit that runs out as
  failed, then go on. One bad case should not hold the job's CPUs or GPU until the time limit; the admin's
  monitoring flags such jobs (references/alerts.md).
- Prefer one job per unit through `d3run.py new --config …` when a unit takes minutes or more: Slurm then packs the
  jobs, and a failure costs one unit.
- Many tiny result files are slow on NFS and in S3; collect them in one SQLite or Parquet file per job.

## 6. Segments and chains

`d3run.py submit <id> --segments 3 --time 12:00:00` submits three attempts, each depending on the previous one with
`afterany` (it starts whatever the previous one's end state). Each attempt resumes from the newest checkpoint. When
the run is done (or failed), the remaining segments start, see it in `status.json`, and exit within seconds. A
segment that dies without a clean status (out of memory, a segfault, an exit without `ctx.fail`) leaves `running`
in `status.json`; the next segment counts that, and after two such ends in a row (`max_hard_failures=2`) it marks the
run failed, so a chain does not repeat the same crash on every GPU slot. A clean `interrupted` resets the count;
`reconcile` lists them so you can `scancel` them instead. Choose segments from the pilot: `d3run.py size` prints
`--time` and `--segments`. A segment that runs out of work early just ends: nothing is wasted but its queue slot.

Twelve-hour segments are a good default for long runs: they find gaps in the schedule more easily than 24 h ones and
lose at most one checkpoint interval when something fails.

## 7. Testing the resume (part of the smoke test)

Locally first, without Slurm (local mode works in `runs/local/`): give the run less time than it needs and start it
twice, e.g. `rm -rf runs/local; D3RUN_TIME_LIMIT_S=120 uv run python src/train.py --small` two times. The first run
must end `interrupted` with a checkpoint, the second must log that it resumed from it.

```bash
RID=$(uv run tools/d3run.py new --name resume-smoke --config configs/smoke.yaml --tag smoke)
uv run tools/d3run.py submit "$RID" --script jobs/train.sbatch --time 00:05:00 --segments 2 -- --config configs/smoke.yaml
# later
uv run tools/d3run.py reconcile && uv run tools/d3run.py show "$RID"
grep -h "start\|checkpoint" runs/$RID/logs/attempt-0*
```

Pass: attempt 1 ends `interrupted` with a checkpoint, attempt 2 logs that it started from it and ends `done`. With
S3, also delete `runs/$RID/checkpoints/` between the attempts once: attempt 2 must fetch the checkpoint from S3.

## 8. What not to rely on

- `--requeue` and `scontrol requeue`: allowed (`JobRequeue=1`) but not tested here; the chain needs neither.
- `sbatch` from inside a job (self-resubmission): not tested; the chain above needs none.
- Signals reaching Python through `uv run`: the template avoids the question with the STOP file.
- `KillWait` after the limit: Slurm sends SIGTERM, then kills about 30 s later. Too short for a large checkpoint,
  which is why the context stops before the limit by its measured margin instead of waiting for SIGTERM.
- An upload finishing in the last seconds: the context skips uploads that could run into the end; the checkpoint
  is safe locally and reaches S3 with the next segment or with `archive`.
