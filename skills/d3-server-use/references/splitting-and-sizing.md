# Splitting a round into jobs, and how wide each job is

Checkpoints let a job survive the 24 h limit. They do not make it a good job for a shared server: one job that does
everything in a loop holds its CPUs or its GPU for all of it. Before every round, two decisions: where the work is
cut into jobs, and how many CPUs and GPUs each job gets. Both depend on the code, and the second also on the queue
at that moment.

## Contents
1. Why it matters on this server
2. Where to cut
3. How wide each job is
4. Fitting the round to the queue
5. Linking phases
6. The first server smoke while the queue is full
7. Examples

## 1. Why it matters on this server

- **No preemption.** A running job keeps what it holds until it ends. Each job end is a moment at which fair share
  decides who gets the CPUs or the GPU next. Many separate jobs give the queue many such moments; one long job gives
  none, and a chain of 24 h segments one a day.
- **Billing** ([cluster.md](cluster.md), section 3): per second `max(CPUs × 1.0, memory GB × 0.266, GPUs × 41.5)`.
  A GPU held through one hour of EDA, plotting or a CPU solver bills 149,400; the same hour as a 1-CPU job bills
  3,600.
- **The admin's monitoring** ([alerts.md](alerts.md)): a GPU job that spends over an hour in a CPU phase draws
  `JobGpuIdle`; a pool job whose last workers run alone while the other CPUs idle draws `JobCpuUnderused`.
- **Backfill** places small jobs into gaps. A job that needs 64 CPUs or 2 GPUs at once waits for that gap, and while
  it is the top pending job it holds the node for every job below it.
- **Failures** cost one unit instead of the round, and a rerun repeats only the failed units.

## 2. Where to cut

Split by default. Cut first where the hardware changes, then between independent units.

| Seam | Examples | Each piece |
|---|---|---|
| Hardware phase | data preparation, EDA (CPUs) → training, prediction (GPU) → optimization (CPUs) → evaluation, figures (CPUs) | its own job with only what that phase uses; a GPU only for the phase that computes on it |
| Independent units of a phase | configs, seeds, folds, markets, scenarios, time windows, model classes | one run each (`d3run.py new --config …`) |
| One long unit | a training of 30 h | segments ([interruptible-jobs.md](interruptible-jobs.md), section 7) |

What stays together, and what is bundled:

- A step of a few minutes that works on the previous step's state in memory stays in that step's job: prediction
  right after training with the same model, a metric right after a solve.
- Units shorter than about 10 minutes are bundled into chunks of 30 minutes to a few hours and run as a work list
  inside one job ([interruptible-jobs.md](interruptible-jobs.md), section 5). Each job pays for its start: Slurm,
  `uv run`, imports, CUDA, loading data. `d3run.py size` flags runs that short.
- More than about 500 of your jobs in the queue (every segment counts): bundle into chunks or submit in parts. The
  cluster holds at most 10,000 jobs for all users together (`MaxJobCount`), and backfill tests 100 of yours per
  cycle. `d3run.py submit` warns above 500.

The loop over units moves out of the code into the round: the entry point runs one unit given its config
(`--config`, or `--chunk i/n` for a slice of a list), never "the rest of the loop", and `d3run.py new --config …`
creates one run per unit. Each phase writes its outputs as files into its run folder (`ctx.results_dir`); the next
phase reads them from there by the upstream run ID. Nothing passes between jobs in memory.

## 3. How wide each job is

Request as many CPUs and GPUs as the job keeps busy, not the minimum.

- **Parallel inside the job:** threads (XGBoost and scikit-learn `n_jobs`, BLAS, `torch.set_num_threads`), a process
  pool over the units of a chunk, data loader workers that feed a GPU, several GPUs only for code that uses them
  (DDP and similar). The code reads the count from `SLURM_CPUS_PER_TASK`; a job that asks for 16 CPUs and starts
  one thread leaves 15 idle.
- **Why wider is cheap:** usage is CPU-seconds. A job that scales costs the same fair share at 16 CPUs for 1 h as at
  1 CPU for 16 h, and its result is there 15 h sooner. CPUs that the job's memory already pays for cost nothing
  extra: `--mem 128G` bills like 34 CPUs, so a 4-CPU job with 128 GB pays for 34. One GPU bills like 41.5 CPUs, so
  CPUs for its data loading cost no fair share; they are still missing for others' CPU jobs, so request what the
  input pipeline uses (first jobs: GPU busy %, `size` note), typically 4 to 8.
- **Measure the scaling, locally first.**
  1. On your own computer, `d3run.py scale -- <command on a slice of 1 to 5 minutes>` runs the slice at 1, 2, 4, …
     CPUs, each time in a fresh local run folder, and prints time, speed-up, efficiency and peak memory. The width
     is the widest at which each CPU still delivers 70 % of the narrow run's speed; below that the extra CPUs
     mostly wait, and below 60 % CPU use the monitoring flags the job.
  2. Submit a few first units of the round (the largest among them) at that width, up to what the share lets run
     at once, with about twice
     the local time for a full unit (the server's CPUs are slower or faster). They are the pilot, and their results
     count. Long units get a first segment of about an hour: `size` extrapolates from the `progress` they report,
     and they resume later.
  3. `size` on those first jobs sets the flags for the rest. When they kept all their CPUs busy, `size` says so:
     the code may scale further.

  A pilot at two widths on the server only when `scale` was still scaling at all of the laptop's CPUs and `queue`
  shows room for the wider one: the same config at the laptop's width and twice that, the second with
  `d3run.py new --config <same> --allow-duplicate --tag <same tag>`; `size` compares them by the same rule.
- **GPU jobs:** a laptop cannot measure the GPU side, but `scale` on the code's CPU path still gives the peak
  memory (`--mem`) and the CPUs the data loading keeps busy. Start with 1 GPU and 4 CPUs (the partition's default
  per GPU); `size` on the first jobs decides. Their GPU pays for up to 41 CPUs, so `size` takes a wider width when it is
  at least 10 % faster. While the queue is full, these first jobs also carry the GPU checks (section 6).
- **A unit that fills only part of a GPU** (GPU busy below about 50 % in the first jobs, little GPU memory): a GPU cannot be
  shared between jobs, so several units share one 1-GPU job (processes, or one model vectorized over seeds), or the
  unit runs on CPUs.
- **Memory:** what one unit needs (`size`). Units with very different memory needs go into separate jobs, each with
  its own `--mem`, instead of one job sized for the largest.

## 4. Fitting the round to the queue

`d3run.py queue` (read-only: one `squeue`, one `scontrol show node`) prints the free CPUs and GPUs, who waits, and
when the running GPU jobs end at the latest. Run it before choosing widths and job counts.

| `queue` shows | Choose |
|---|---|
| Nobody waits, much is free | each job at its efficient width, as many in parallel as there are units, up to the whole machine; when others start waiting, `submit` and `feed` keep you within the share |
| Others wait | the share (3 of 4 GPUs, 112 of 150 CPUs; `submit` holds the rest); narrower jobs start sooner and leave room |
| What you need is busy for hours | what is free now: a 2-GPU job waits until 2 GPUs are free at once, while 1-GPU jobs start on the first free GPU and spread as more free up. Compare "wait for k + time on k" with "time on 1 from now" |
| Units differ in duration or memory | separate jobs, each sized for its unit, instead of one wide pool whose CPUs idle while its longest unit runs |

A round of separate 1-GPU (or few-CPU) jobs adapts by itself: with one GPU free its jobs run one after another,
with four free side by side, and other users get a GPU between two of them. Times from `queue` are time limits,
so they are upper bounds.

## 5. Linking phases

- One tag per phase: `<round>-prep`, `<round>-train`, `<round>-opt`, `<round>-eval`.
- The downstream run knows its inputs: `d3run.py new --config … --param upstream_tag=<round>-train` (or the
  upstream run ID in its config). It reads `runs/<upstream id>/results/`.
- Submit the next phase when `reconcile` shows the previous one done, or right away with
  `submit … --after-tag <round>-train`: it waits for the last segment of every queued or running run of that tag
  (`--after 101:102` takes job IDs). The dependency is `afterany`, so the job also starts when an upstream run
  failed; it checks first:

  ```python
  import json
  ctx = RunContext.from_env()
  tag = json.loads((ctx.run_dir / "run.json").read_text())["params"]["upstream_tag"]
  ups = [p.parent for p in sorted(ctx.run_dir.parent.glob("*/run.json"))
         if json.loads(p.read_text()).get("tag") == tag]
  bad = [u.name for u in ups if json.loads((u / "status.json").read_text()).get("state") != "done"]
  if not ups or bad:
      ctx.fail(RuntimeError(f"upstream {tag} not done: {bad or 'no runs'}"))
      raise SystemExit(1)
  ```

- `archive --clean` only after the last phase that reads a run's results has finished.

## 6. The first server smoke while the queue is full

A smoke job on the server is for the first time a project runs there; the local smoke test has passed before it
(SKILL.md, step 5). Each job waits for its own turn: when a GPU frees up, it goes to the highest-priority job
pending at that moment, and a job submitted later waits for the next one. While `queue` shows no GPU free or other
users waiting for one (its `GPU smoke` line), a separate 10-minute GPU smoke therefore spends your turn, and the
first real job waits for the GPU after it, often hours. Backfill does not help: it fills free GPUs, and there are none. `submit` refuses a
GPU job tagged or named smoke then (`--allow-gpu-smoke` only when the user wants one anyway). One turn does both:

1. **The server smoke on CPUs.** The tiny config end to end on the code's CPU path (`--gpus 0`; PyTorch on device `cpu`,
   `JAX_PLATFORMS=cpu`), and the resume test ([interruptible-jobs.md](interruptible-jobs.md), section 8), on the
   `cpu` partition. Code without a CPU path: what runs without the GPU (imports, configs, data paths, one batch).
2. **The first real GPU jobs at the same time**, without waiting for the CPU smoke, so they catch the next free
   GPU: the first units of the round, up to the share (`queue`, share line), 1 GPU and 4 CPUs unless `size` knows
   better. They are smoke and pilot at once, and their results count.
3. **The GPU checks in their first minutes**, so a failure ends the job early and frees the GPU. In the loop of
   [interruptible-jobs.md](interruptible-jobs.md), section 2:

   ```python
   assert torch.cuda.is_available(), "no GPU visible in the job"   # JAX: jax.devices()[0].platform == "gpu"
   print(f"[check] GPU {torch.cuda.get_device_name(0)}", flush=True)
   checked = ckpt is not None                  # a resumed segment has loaded a checkpoint already
   for step in range(start, n_steps):
       train_one_step(state)                   # at full batch size: out of memory shows in the first steps
       if ctx.should_checkpoint():             # the first one after 5 minutes
           with ctx.checkpoint(step) as path:
               save(state, step, path)
           if not checked:                     # once: the resume path, on the GPU
               load(ctx.latest_checkpoint())
               checked = True
               print("[check] checkpoint written and loaded on the GPU", flush=True)
           ...
   ```

   The job template logs the GPU's use every minute (`logs/gpu-<job>.csv`). Keep the checks in the code: in later
   rounds, which have no smoke job, they make a broken first job fail within minutes.
4. **Look** when the CPU smoke has ended and about 10 minutes after the first GPU job started: `reconcile`, then
   `grep -h "\[check\]" runs/<id>/logs/attempt-01-*.out`. A failure in either: `scancel` the GPU jobs, fix,
   `git pull` (nothing of the project queued) and submit again. Cancelled jobs lose only their age, a small part
   of the priority.
5. **The rest of the round** after `size` on the first jobs (section 3). While others wait, `submit` would hold it
   anyway.

With a GPU free and nobody else waiting for one, a separate GPU smoke costs no turn: run it first. The same
reasoning holds for CPU jobs when the `cpu` partition is full and others wait for it.

## 7. Examples

**Predict then optimize** (3 markets; an LSTM per market, about 2 h on a GPU; 365 day-ahead forecasts per market;
1,095 battery MILPs of 2 to 10 minutes, single-threaded; an evaluation):

| Phase | Runs | Each job |
|---|---|---|
| train + predict | 3, one per market | 1 GPU, the CPUs its data loader uses, about 2.5 h; prediction stays in this job (minutes, same model in memory) |
| optimize | 36, one per market and month (about 30 solves, a work list) | CPU only; a pool of the measured width, or 1 CPU for about 3 h; `--after-tag <round>-train` |
| evaluate | 1 | 1 to 4 CPUs, summary and figures; `--after-tag <round>-opt` |

As one script the study held a GPU for four days while it spent most of them in a CPU solver. Split, the GPU is
held for about 7.5 GPU-hours, and the solves run side by side on free CPUs.

**Grid sweep** (48 trainings of 1.5 h on a GPU): 48 runs, one GPU each, with the CPUs the data loader keeps busy.
With one GPU free they run one after another, with four free side by side.

**Scenario pool** (1,200 single-threaded scenarios of 10 to 20 minutes, written as one joblib pool of 64): 1,200
jobs would be too many and one 64-CPU job waits for 64 free CPUs, then idles while its last scenarios run. Chunks
of 40 scenarios give 30 runs; each runs a pool at the width `scale` measured on a few scenarios, longest scenarios
first so the pool's tail stays short, and writes one result file per scenario so it can resume.
