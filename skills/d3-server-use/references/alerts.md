# Alerts from the admin's monitoring

The admin's monitoring posts alerts to a Slack channel of the group (its name goes into `<site>` as
`alerts_channel`); the bot is called "Server Police". Categories: storage, ops, updates, jobs. An alert names the
user's login, the job and the numbers, sometimes mentions the whole channel, and is followed by a "Resolved" message
once the condition is gone. The messages are in English since 2026-10-27 ("Alert", "Resolved", "Next step:"); older
ones in the channel say "Meldung", "Entwarnung" and "Behoben". The admin adds users to the channel when their jobs
first trigger an alert, or earlier when they ask to be added. The alerts are notices, not blame: they point to
jobs that hold resources they do not use, often because something hangs. Thresholds below are as observed in October
and November 2026 and have changed before (the CPU window was one hour at first); the admin may change them again.

## The alerts

| Alert | Fires when | What it means |
|---|---|---|
| `HomeQuotaWarning` | the user's `/home` is above 100 GB (the hard limit is 200 GB); resolved below about 90 GB | at the hard limit jobs can no longer write: logs, checkpoints and results fail |
| `HomeQuotaReached` | less than 1 GB is left below the hard limit | every write fails from the limit on, in jobs and notebooks: act at once |
| `JobGpuIdle` | a job has held a GPU for over 1 h and used less than about 10 % of it in the last hour | nobody else can use that GPU meanwhile (no GPU sharing on this cluster) |
| `JobCpuUnderused` | CPU-only jobs (partition `cpu`, not notebooks) with more than one CPU that have run for over 30 min and use less than 60 % of their CPUs leave, summed per user, 2.5 or more requested CPUs idle over the last half hour; resolved below 1.5 | the requested CPUs sit idle and are missing for other jobs |
| `NasUnreachable` | the storage (NAS) has not answered a single monitoring query for 30 min | an admin matter: disk and volume alerts are blind meanwhile. The home is not on the NAS, so jobs keep running; if the NAS itself is down, S3 is too, so retry failed transfers after "Resolved" |
| ops, updates | maintenance, updates, outages | follow the message; do not start long rounds right before announced maintenance |

## What to do

**`HomeQuotaWarning`, `HomeQuotaReached`**
1. `d3run.py usage` (run folders, `data/`, `results/`, `logs/`); the whole-home figure is in Grafana. Never scan the
   whole home with `du` or `find`. At `HomeQuotaReached` first free a few GB at once (`uv cache prune`, a run folder
   with a verified copy), because at the limit even the logs of an archive job fail.
2. Archive and clean: `d3run.py archive --finished --clean --submit`, `d3run.py push data/<folder> --clean
   --submit`; without a bucket the rsync route (data-and-storage.md, section 7).
3. `uv cache prune`; old `.venv`s and old checkouts of finished projects.
4. The warning resolves itself once the home is below about 90 GB.

**`JobGpuIdle`**
1. Is the job alive? `sq -u $USER`, the job's `.out`/`.err` (`d3run.py show <run_id>` lists the log paths), and the
   GPU load in `/home/.cluster-status/nvidia-smi.txt`.
2. It hangs (no new output, waiting on input, a deadlock in data loading, a solver stuck on a bad case):
   `scancel <jobid>`, fix, resubmit; the run resumes from its checkpoint. Give every unit of work a timeout (the
   solver's own time limit, or a watchdog around each unit) so a bad case fails fast and is recorded, instead of
   holding the job's resources until the time limit.
3. It works but keeps the GPU mostly idle: the GPU waits for data. Typical causes are too few data-loader workers
   (`num_workers`, prefetching, pinned memory), preprocessing on the CPU inside the loop, a batch too small for the
   GPU, or a model too small to need one. Fix the input pipeline, raise the batch size, or run it on CPUs.
4. An open JupyterHub notebook holding a GPU counts too: stop the server when you are not computing.

**`JobCpuUnderused`**
1. `seff <jobid>` shows how many of the requested CPUs the job used. A job that suddenly drops to a fraction of its
   CPUs often hangs (see `JobGpuIdle`, step 2): look at its output first.
2. Request what the job uses: `d3run.py size` suggests `--cpus` from the measured use.
3. Or make the code use the CPUs it asked for: set the thread count from `SLURM_CPUS_PER_TASK` (e.g.
   `n_jobs=int(os.environ["SLURM_CPUS_PER_TASK"])` for XGBoost and scikit-learn, `torch.set_num_threads(...)`).
   Libraries that ignore it either leave CPUs idle or start more threads than the job owns, which slows it down.
4. A job that needs more memory asks for it with `--mem`, not with more CPUs.

## Catching it before the alert

- The pilot of a round runs with the job template, which logs GPU memory and utilization once a minute.
- `d3run.py reconcile` and `d3run.py size` flag attempts that come close to these alerts: more than one CPU below
  60 % after 30 minutes, or a GPU below 15 % on average after an hour. Both are stricter than the alerts (which count
  only CPU-only jobs and need 2.5 idle CPUs per user, or a GPU below 10 %), so a flag is a warning, not a sure
  alert. Fix the requests before the full round.
- `d3run.py usage` after every round keeps the home well below 100 GB.

## Reading the alerts

If the user asks about an alert and Claude has a Slack connector, search the alerts channel for the user's login to
get the exact message and job IDs (read only). Never post in the channel or reply to the alerts.
