# The cluster: limits, partitions, priority, monitoring

State after the rebuild of October 2026 (checked with `scontrol show partition`, `sprio -w` and `sbatch --test-only`
on 2026-10-27, and `scontrol show config` on 2026-11-04: Slurm 23.11.4, `PreemptMode=OFF`, `KillWait=30 sec`,
`OverTimeLimit=0`, `JobRequeue=1`, `bf_window=1440,bf_max_job_test=2000,bf_max_job_user=100`; login limits and
JupyterHub against the admin's configuration on 2026-11-04). Settings can change: re-check with the same commands
before relying on a number.

## Contents
1. Hosts and hardware
2. Partitions, submit filter, limits
3. Priority, backfill, and why jobs wait
4. Fair use: sharing GPUs and CPUs
5. Monitoring commands
6. JupyterHub
7. What changed with the rebuild

## 1. Hosts and hardware

- **Login host** `login`: ssh, git, uv, Slurm commands. No GPU, no `nvidia-smi`. Light commands only: each user's
  processes there share 4 CPUs and 8 GB (slowed from 6 GB, killed above 8 GB).
- **Compute node** `compute`: 166 CPUs for jobs (170, 4 reserved), 624 GB memory, 4 × RTX 4090 (24 GB each, no
  vGPU, one job per GPU), driver 580 / CUDA 13. Not reachable by ssh; only through `sbatch`/`srun`.
- **Home** `/home/<login>` on NFS, shared by both hosts. Quota: warning above 100 GB, hard limit 200 GB. No backups.
  Creating many small files from a job is slow (about 30 files per second).
- **Tools:** `uv` system-wide, `sq` (queue sorted by priority), `seff` (what a finished job used), `gpu-status`
  (needs `ssh -t`), `rsync`. Missing: `sqlite3` (read databases with Python), `nvidia-smi` on the login host,
  git-lfs, MLflow (a project adds it: `uv add mlflow`). The AWS CLI is installed per user (`uv tool install awscli`).
- **Network** (tested 2026-11-04 from a compute node): the internet without a proxy (pypi.org, github.com,
  api.wandb.ai), the bucket, and the login host's ssh port. No tracking server runs on either host.

## 2. Partitions, submit filter, limits

| | `main` | `cpu` |
|---|---|---|
| For | GPU jobs only | CPU-only jobs |
| Cap on the node | all | 150 CPUs, 368 GB |
| Default memory | 4 CPUs and 64 GB per GPU if neither `--cpus-per-task` nor `--mem` is set | 2 GB per CPU |
| Time | at most 24 h, default 24 h | at most 24 h, default 24 h |

- **Leave `--partition` out.** The submit filter routes a job with a GPU request to `main` and one without to `cpu`.
  It rejects `--partition=main` without a GPU and `--partition=cpu` with one.
- **24 h cap:** a longer job is accepted (`EnforcePartLimits=NO`) but stays pending forever with reason
  `PartitionTimeLimit`. Old scripts that ask for `48:00:00` fail this way.
- **The default time is the maximum** (24 h), so a job without `--time` blocks backfill. Always set it.
- Both partitions share one node and the same priority tier.

## 3. Priority, backfill, and why jobs wait

- **Priority** = fair share (weight 100,000; usage half-life 7 days) + age (weight 10,000, full after 7 days). No
  job-size, partition or GPU weight, no per-user limits. Among one user's jobs only the age differs (about one point
  per minute, counted from the moment a job becomes eligible).
- **One priority list for both partitions.** If the top job cannot start (e.g. it needs a GPU and all four are busy),
  it holds the node, and the main scheduler starts no lower job there, not even a CPU-only one.
- **Only backfill starts jobs out of order, and it tests at most 100 jobs per user and cycle**
  (`bf_max_job_user=100`). With more than 100 of your own pending jobs that cannot start, your lower jobs wait even
  when they would fit. Other users' jobs are not blocked: backfill reaches them.
- Jobs that wait on a dependency start ageing only when it is met, so they rank below GPU jobs that waited longer.
- After a large round your fair share drops for about a week: other users' jobs start first. That is intended.

**How usage is counted** (checked 2026-11-04 with `scontrol show config`, `scontrol show partition`, `sshare`)

```
 billing per second = max( CPUs × 1.0 , memory GB × 0.266 , GPUs × 41.5 )   (PriorityFlags = MAX_TRES)
 usage              = billing-seconds, halved every 7 days
 fair share         = your rank among all users by usage (Fair Tree: steps of 1 / number of users)
```

- One GPU bills 41.5 per second, a quarter of the node, the same as 41.5 CPUs or about 156 GB of memory.
- The rank matters, not the amount: with 18 users one rank is worth 100,000 / 18 = 5,556 priority points, more
  than half of what age can add in a week. `sshare -U -l` shows your usage and fair share.
- Examples: a 10-minute smoke test on one GPU 24,900; one GPU-hour 149,400; a 1-CPU job for 24 h 86,400; 40 runs
  of 3 h on one GPU each 17.9 million. Work on the laptop and commands on the login host cost nothing.
- So: CPU work on CPUs, measure before a round, no idle JupyterHub server holding a GPU (it bills like a job).

**What helps**

- Submit the CPU-only part of a round **before** the GPU part.
- Realistic `--time`: backfill only places jobs whose limit fits into the gaps.
- When your CPU jobs are blocked behind your own pending GPU jobs, raise `nice` on the GPU jobs above the priority
  gap, and set it back to 0 afterwards:

  ```bash
  gpu=$(squeue -h -u $USER -t PD -p main -o %Q | sort -n | tail -1)
  cpu=$(squeue -h -u $USER -t PD -p cpu -o "%Q %r" | grep -v Dependency | sort -n | head -1 | cut -d' ' -f1)
  echo $((gpu - cpu))                                                      # the gap
  scontrol update jobid=$(squeue -h -u $USER -t PD -p main -o %i | paste -sd, -) nice=<gap + margin>
  ```

  Side effect: nice also lowers your GPU jobs against other users' jobs.
- `bf_max_job_user` and the partition layout are the admin's decision.
- `sbatch --test-only` start estimates were unreliable on the old server; use it to check the filter, not to plan.

## 4. Fair use: sharing GPUs and CPUs

The rule of the group: one user's jobs take all GPUs or all CPUs only while nobody else is waiting.

- **No preemption** (`PreemptMode=OFF`): a running job keeps its GPU until it ends. The longest you can make
  someone wait is the remaining time of your running jobs, so when the group is busy prefer GPU segments of a
  few hours (`--segments`) to one long job.
- **`d3run.py submit`** reads the queue once (`squeue`). "Waiting" means another user's job is pending with reason
  `Resources` or `Priority` (held jobs, array throttles and dependencies do not count). While someone waits for a
  GPU (`main`), your running and startable GPU jobs stay within `share_gpus` (default 3 of 4); while someone waits
  in `cpu`, your CPU jobs stay within `share_cpus` (default 112 of 150). Jobs above the share are submitted with
  `--hold` and the comment `d3run`. Later segments of a run wait on the first one and are not counted.
- **`d3run.py feed`** (one `squeue`, at most two `scontrol` calls): releases held `d3run` jobs, oldest first, as
  far as the share or, with nobody waiting, the whole machine allows; when others start waiting and your startable
  jobs exceed the share, it holds back the newest pending ones. It never touches running jobs or jobs without the
  `d3run` comment. It runs with every `reconcile`, which costs nothing: while your computer is on, a `reconcile`
  every 15 minutes does the feeding. A feeder job (`feed --submit`: 1 CPU, 1 GB, checks every 5 minutes, ends when
  nothing is held or after 23.5 h) bills one CPU while it runs, about 86,400 billing-seconds a day (some 35
  GPU-minutes); use it for rounds that run while your computer is off.
- Change the share per project with `d3run.py init --share-gpus N --share-cpus N`; skip the check with
  `submit --no-throttle` only when you know nobody else uses the server.
- Without d3run, Slurm's own array throttle does the static part: `sbatch --array=0-79%3` runs at most 3 tasks at
  a time, and `scontrol update JobId=<array id> ArrayTaskThrottle=N` changes it later. Other users of the server
  already work this way.

## 5. Monitoring commands

| Command | Shows |
|---|---|
| `sq`, `sq -u $USER` | queue sorted by priority: what runs, what starts next |
| `squeue -u $USER -t PD -o "%i %.30j %P %Q %r %S"` | your pending jobs: name, partition, priority, reason, planned start |
| `sprio -u $USER`, `sprio -w` | priority components per job, and the weights |
| `sacct -u $USER -S <date> --format=JobID,JobName%30,State,Elapsed,MaxRSS` | states after a round (jobs since the rebuild only) |
| `seff <jobid>` | time, CPU and memory a finished job used against what it requested |
| `scontrol show job <id>` | `Scheduler=Main` or `Scheduler=Backfill` for a started job |
| `sdiag` | backfill statistics ("Last depth cycle (try sched)") |
| `cat /home/.cluster-status/nvidia-smi.txt` | GPU usage of the compute node, readable from the login host |
| Grafana (URL in `<site>`) | utilization, storage, home quota |

Whether a framework sees a GPU can only be checked inside a job. Watch the queue every 15 minutes or more; a watcher
that opens a new ssh session every few seconds loads the login host (use ControlMaster, first-time-setup.md).

## 6. JupyterHub

https only, at most one GPU per notebook server. More GPUs, or anything longer than the session, goes through
`sbatch` (a terminal in JupyterHub can submit too). Stop the server when done (File, Hub Control Panel, Stop My
Server): an idle notebook holding a GPU blocks a quarter of the group's GPUs. A notebook server ends when the
runtime chosen at the start (1 to 24 h) is over, or after 30 minutes without activity. Profiles: CPU with 1, 8 or
16 cores (4, 16, 32 GB) and one GPU profile (2 cores, 16 GB, 1 GPU).

## 7. What changed with the rebuild

| | Before | Since October 2026 |
|---|---|---|
| Login | shell on the compute machine | separate login host, no ssh to the compute node |
| Max time | 14 days | 24 h per job |
| Default time | 4 h (GPU), 2 h (CPU) | 24 h (the maximum) |
| Priority | age, fair share, job size, GPU count | fair share and age only; no preemption |
| Home | kept | new and empty; quota 100 GB warning, 200 GB hard |
| JupyterHub | http | https only, CA certificate needed |
| Job IDs | up to about 400,000 | restarted at about 3,000 |
