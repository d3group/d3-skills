---
name: d3-server-use
description: |
  Run compute jobs on the D3 group's KiRegio Slurm server the way the group agreed: Slurm for everything that
  computes, uv only, jobs of at most 24 h that checkpoint and resume, a smoke test and a pilot before every round,
  run IDs and a registry that tie code, config, logs, checkpoints and results together, and the S3 bucket as the
  store so the small server home stays clean. Use this skill when:
  (1) Running anything on the server: sbatch or srun jobs, GPU or CPU, JupyterHub, the first login and ssh setup
  (2) Preparing or submitting a round of experiments: smoke tests, sizing --time/--mem/--cpus/GPUs, many configs
  (3) Making long jobs survive the 24 h limit: checkpoints, resume, chained segments
  (4) Finding which code, config, logs and results belong to a run or to a Slurm job ID
  (5) Moving data, checkpoints, logs or results between server, S3 bucket and laptop; cleaning up the home
  (6) Diagnosing pending, failed or slow jobs, an unresponsive login host, or a full home
  (7) Understanding and fixing alerts from the admin's monitoring ("Server Police" in Slack, also in German:
      "Meldung"): home above 100 GB, an idle GPU, unused CPUs
  MANDATORY TRIGGERS: KiRegio, Slurm, sbatch, srun, squeue, sq, sacct, seff, sprio, job pending, GPU server,
  compute server, run on the server, submit jobs, cluster, checkpoint, 24 hours, time limit, JupyterHub, MinIO,
  S3 bucket, home quota, d3run, run registry, server alert, alerts channel, Server Police, HomeQuotaWarning,
  HomeQuotaReached, JobGpuIdle, JobCpuUnderused, NasUnreachable
---

# Jobs on the KiRegio server

The group shares one compute node (166 CPUs, 624 GB, 4 × RTX 4090) behind a login host. Everything that computes runs
through Slurm; the login host takes light commands only. A job runs at most 24 h. Fair share decides whose job starts
first: whoever used less recently. The server home is small (warning above 100 GB, hard limit 200 GB) and has no
backups, so the S3 bucket is where data, checkpoints, logs and results live.

> **`<skill-dir>`** is this skill's folder. **`<site>`** is the user's site file `~/.config/d3-server/site.toml`
> (template `assets/site.example.toml`): login name, ssh alias, server addresses, the S3 answer. It stays on the
> user's computer because this skill is public. **`<alias>`** is the ssh alias from `<site>`, **`<proj>`** the
> project's checkout on the server.

## 0. First use (once per user)

Read `<site>` first. Fill in only what is missing and never ask again for what is stored. Write `<site>` only with
what the user answered or confirmed, and show the entries before saving them the first time; in a session without
the user (a test, a plan for later) list the questions instead of writing a site file.

1. **Login name.** Ask once ("What is your login name on the KiRegio server, e.g. abcd?") and store it as `login`.
2. **ssh: detect before you guide.** Stop at the first check that works:
   - `<site>` has an `ssh_alias`, and `ssh -o BatchMode=yes -o ConnectTimeout=10 <alias> hostname` answers.
   - `~/.ssh/config` already has a Host block for the server: list the blocks (`grep -i '^Host ' ~/.ssh/config`),
     resolve each with `ssh -G <name> | grep -i '^hostname '`, and test the one that points to the server address.
   - Neither works: guide the user through [references/first-time-setup.md](references/first-time-setup.md), only
     the steps that are missing (key pair, public key to the admin, Host block, first login). The user runs the
     key commands; never create, read or copy a private key, and change `~/.ssh/config` only after a yes.

   Store `ssh_alias`, `host` and the date in `ssh_ok`. From then on every server command is `ssh <alias> '…'`.
3. **Bucket: detect, then ask only what is missing.** If `<site>` has `has_bucket = "no"`, or `"yes"` together
   with `bucket` and `endpoint_url`, use that. Otherwise:
   - Ask once: "Do you have an S3 bucket on the KiRegio storage?" Store `has_bucket` and `asked_on`.
   - **yes:** look before asking. On the laptop: `aws --version`, `aws configure list`,
     `grep -n -E '^\[|endpoint_url' ~/.aws/config`. On the server: `ssh <alias> '~/.local/bin/aws --version;
     grep -n -E "^\[|endpoint_url" ~/.aws/config'`. Never open `~/.aws/credentials`. Then ask only for what is
     still unknown: the bucket name, the S3 API endpoint (from the admin's mail; not the web console address), a
     profile name if it is not `default`. Store `bucket`, `endpoint_url`, `aws_profile` in `<site>`. A missing CLI
     or config: set it up with [references/data-and-storage.md](references/data-and-storage.md); the user writes
     the keys themselves. Check access with `aws s3 ls s3://<bucket>/` on the laptop and on the login host and
     store the date in `access_ok`. Once per bucket, check that it keeps objects:
     `aws s3api get-bucket-lifecycle-configuration --bucket <bucket>` (no rules is good); a rule that expires or
     deletes objects makes it unfit as the only copy, so tell the user and ask the admin.
   - **Per project:** the folder inside the bucket (`s3_prefix`, default the project name) goes into
     `<site>` under `[projects.<name>]` and into the project's registry with `d3run.py init --s3-uri
     s3://<bucket>/<prefix>` (add `--s3-endpoint`/`--aws-profile` if the server's `~/.aws/config` does not set
     them). `d3run.py settings` shows what a registry already has.
   - From then on S3 holds data (raw, pre- and postprocessed), checkpoints, logs and results by default; the
     server keeps only what running jobs need.
   - **no:** suggest asking the admin for one. Until then the user's own computer is the store: rsync copies
     runs and data there, and `d3run.py clean --manifest` deletes on the server only what the copy holds with the
     same sizes. Small text results that belong in the repository can go by git (commit on the server, push, pull).
     Other storage the user has (a university share, their own cloud) works the same way through a manifest of the
     copy, within the data rules ([references/data-and-storage.md](references/data-and-storage.md), section 7).
     Ask again only when the user says they got a bucket.
4. **New account:** change the JupyterHub default password at once and import the CA certificate once per
   computer ([references/first-time-setup.md](references/first-time-setup.md)).

## 1. Rules, and why

- **Everything that computes is a Slurm job.** No ssh to the compute node; on the login host only `ls`, `du` of a
  small folder, `git`, `uv sync`, `sq`, `sacct`, `d3run.py`. Each user has 4 CPUs and 8 GB there: heavy work crawls,
  is killed above 8 GB, and its file reads still load the shared NFS server. On the old server, where login and
  compute were one machine, a polars scan once made everything unresponsive for everyone.
- **No scans of the whole home, not even in a job.** `du` or `find` over `~` sends the shared NFS server a request
  for every file and slows everyone. The total is in Grafana, run folders in `d3run.py usage`, a single folder in
  `du -sh <folder>`.
- **uv only:** `uv add`, `uv sync`, `uv run`, `uv tool install`. No pip, conda, venv or global installs. Sync once on
  the login host (`uv sync --managed-python`, so the Python sits in the home where the compute node sees it), then
  jobs call `uv run --no-sync`, so a hundred jobs do not sync the shared `.venv` at the same time.
- **At most 24 h per job; every long job is interruptible.** A job above 24 h is accepted but never starts. Jobs
  save checkpoints on a timer, use their time up to a margin measured from their own step and checkpoint times
  (seconds to a few minutes, not a fixed quarter hour), resume from the newest checkpoint, and run as a chain of
  segments ([references/interruptible-jobs.md](references/interruptible-jobs.md)).
- **Realistic requests.** Shorter `--time` and smaller `--mem` start earlier (backfill) and leave room for others.
  The 4 GPUs serve the whole group and cannot be split: one GPU per job unless the code uses more. Measure, then
  request (smoke test, pilot, `size`).
- **All GPUs or CPUs only while nobody else waits.** The cluster never preempts, so a running job keeps its GPU until
  it ends. `d3run.py submit` checks the queue: while other users wait, your running and startable jobs stay within a
  share (3 of 4 GPUs, 112 of 150 CPUs in `cpu`; `init --share-gpus/--share-cpus`), and the rest is submitted held.
  `d3run.py feed` releases held jobs when nobody waits and holds back pending ones when others start waiting.
- **A run ID before every submission.** `<YYYYMMDD>-<login>-<slug>-<4 hex>` names the run folder, the logs and the
  S3 prefix. Slurm job IDs restart when the server is rebuilt and one run spans several 24 h jobs, so a job ID is
  only an attribute of one attempt.
- **Committed code, recorded per run.** The code reaches the server by `git pull` in `<proj>`. A job runs the code
  that is on the server when it *starts*, so never pull while jobs of a round are queued; `d3run.py new` refuses
  uncommitted changes and records the commit.
- **S3 is the store, the server is scratch.** Upload as you go, verify, then delete the local copy. The bucket sits
  on the group's NAS, in a RAID but without backups: whoever needs a result safe for certain downloads it and backs
  it up themselves. Without a bucket the user's own computer is the store (rsync, then `clean --manifest`). Clean up
  after every round and whenever `d3run.py usage` passes about 50 GB. Nothing on the server is deleted before a copy
  is verified by checksum (MD5 against the bucket's ETag, SHA-256 for other copies; `--size-only` only on the user's
  request).
- **No secrets in files you write.** Passwords, access keys and the Grafana login stay in the user's own files
  (`~/.aws/credentials`, password manager) and the admin's mails, never in a repo, a note, a job script or `<site>`.
- **One writer per file.** Only `d3run.py` on the login host writes the registry; jobs write their own run folder.
  SQLite over NFS written from two hosts can corrupt the database.

## 2. A round, step by step

Claude runs on the user's computer and sends commands as `ssh <alias> 'cd <proj> && …'`. For many short commands
(watching a queue) the ControlMaster settings in [references/first-time-setup.md](references/first-time-setup.md)
reuse one connection.

1. **Read the project first, then set it up.** The skill is generic; the repository it is used in decides the
   details. Look before changing anything: project rules (`CLAUDE.md`, `AGENTS.md`, `.agent/`, `README`; where they
   are stricter, they win), the environment (`pyproject.toml`, `uv.lock`), existing job and submit scripts
   (`grep -rl '^#SBATCH'`), an existing run database or orchestrator, existing checkpoint code, and where configs,
   data, logs and results live. Then adapt: a project with its own orchestrator keeps it and is checked against
   "Fitting an existing orchestrator" in [references/registry.md](references/registry.md); a project without one
   gets `d3run.py` and `d3job.py`. Keep the project's folder names and conventions instead of inventing new ones.
   Setup (once per project): `git clone` into `<proj>`, `uv sync --managed-python`, `uv cache prune`. Copy
   `<skill-dir>/scripts/d3run.py` and `d3job.py` into the project (e.g. `tools/`) and the job template
   `<skill-dir>/assets/job_template.sbatch` (e.g. `jobs/train.sbatch`) yourself, as part of the change you prepare:
   the delivered project must run as it is, without the user copying files out of the skill folder. Add `runs/` and
   `__pycache__/` to `.gitignore`, commit. Then `uv run tools/d3run.py init --user <login> --s3-uri s3://<bucket>/<prefix>` with the
   values from `<site>` (or `--no-s3`).
2. **Plan.** Split the work into units that can resume (epochs, configs, seeds, chunks). Decide CPU or GPU per part:
   only code that uses the GPU goes to a GPU; tree models, linear models, evaluation or post-processing run on CPUs
   (`JAX_PLATFORMS=cpu` for JAX code on CPUs). Estimate the runtime; above about 20 h plan segments.
3. **Make the code interruptible** with `RunContext` from `d3job.py`
   ([references/interruptible-jobs.md](references/interruptible-jobs.md)). Lint every job script:
   `uv run <skill-dir>/scripts/check_sbatch.py jobs/*.sbatch`.
4. **Deploy.** Commit and push on the laptop, `git pull` in `<proj>` (nothing of the project queued), `uv sync`
   if `pyproject.toml` or `uv.lock` changed.
5. **Smoke test.** Parse every config of the round once locally and check the types (YAML reads `seed: 08` as
   text). Run the local resume test (references/interruptible-jobs.md, section 7). Then one tiny config per resource class, `--time 00:10:00`, with `--allow-dirty` only if needed:
   imports, GPU visible from inside the job (print `jax.devices()` or `torch.cuda.is_available()`), data paths,
   output written. Test the resume too: `--segments 2 --time 00:05:00` on a config that needs about 8 minutes;
   the second attempt must log that it started from a checkpoint. The login host has no GPU, so GPU checks only
   count inside a job.
6. **Pilot and size.** One run at full size per resource class, generous limits, tagged `pilot-<round>`; the code
   reports `progress` so a partial pilot extrapolates. After it ends: `d3run.py reconcile`, then
   `d3run.py size --tag pilot-<round>` prints `--time`, `--cpus`, `--mem`, segments and the GPU memory peak.
7. **Submit the round.** `d3run.py new --config configs/round/*.yaml --tag <round>` creates one run per config;
   `d3run.py submit <ids…> --script jobs/train.sbatch <flags from size>`. Submit the CPU-only part before the GPU
   part (age is the only priority difference between your own jobs). Never use `--partition`: GPU jobs go to `main`
   and CPU jobs to `cpu` by themselves. If `submit` reports held jobs (others are waiting), `reconcile` every 15 minutes
   releases them for free while the computer is on; a feeder job (`d3run.py feed --submit`, one CPU) costs fair
   share (about 35 GPU-minutes a day) and is for rounds that run while it is off. Write the round (tag, commit,
   flags) into the project notes.
8. **Watch.** `d3run.py reconcile` (it also runs one fair-use pass, and flags finished jobs that would trigger the
   admin's alerts) and `list --tag <round>` every 15 minutes or more, not in a tight loop. Queue views: `sq`, `squeue -u $USER -t PD -o "%i %P %Q %r %S"`. Pending although
   resources look free: see [references/cluster.md](references/cluster.md) (one priority list, backfill tests at
   most 100 jobs per user, the `nice` fix).
9. **Archive and clean.** With a bucket: `d3run.py archive --finished --clean --submit` uploads each finished
   run folder, checks every file's size in S3, then deletes the server copy (three small JSON files stay). Data:
   `d3run.py push data/processed --clean --submit`, back with `pull`. Without a bucket: the rsync route in
   [references/data-and-storage.md](references/data-and-storage.md), section 7. The first time a store is used,
   run a restore drill: bring one cleaned run back (`d3run.py pull runs/<id> --checksum`, or rsync it back) and
   check it, before the server keeps nothing else. Then `d3run.py usage`.

## When an alert arrives

The admin's monitoring ("Server Police") posts alerts to a Slack channel (`alerts_channel` in `<site>`), in English:
`HomeQuotaWarning` (home above 100 GB), `HomeQuotaReached` (less than 1 GB left below the 200 GB limit),
`JobGpuIdle` (a GPU held over an hour at under about 10 % use), `JobCpuUnderused` (CPU jobs below 60 % of their
CPUs that together leave 2.5 or more CPUs idle), `NasUnreachable` (storage monitoring blind, an admin matter), plus
maintenance notices. They are notices, not blame. Find the job, say
what the alert means, and fix the cause with [references/alerts.md](references/alerts.md); with a Slack connector,
read the alert itself (search the channel for the user's login), but never post there.

## 3. The registry: `d3run.py`

| Command | Does |
|---|---|
| `init --user <login> --s3-uri s3://<bucket>/<prefix>`, `settings` | create `runs/registry.db` and store login and S3 location; show them (read-only) |
| `new --config a.yaml b.yaml --tag <round>` | one run ID per config; records commit, config hash, parameters; refuses duplicates |
| `submit <ids…> --script <sbatch> --time --cpus --mem [--gpus 1] [--segments k] [-- args]` | one attempt per segment, chained with `afterany`; logs in `runs/<id>/logs/` |
| `reconcile` | job states and usage from one `sacct` call; run status from `status.json`; one fair-use pass |
| `feed [--loop \| --submit]` | fair use: release held jobs when nobody else waits, hold back pending ones when others wait |
| `show <id>`, `list [--tag] [--status]`, `find-job <slurm id>` | what ran where, with which code and logs |
| `size --tag <pilot>` | `--time`, `--cpus`, `--mem`, segments from measured usage (margin 1.3) |
| `archive`, `push`, `pull` (`--clean`, `--submit`) | S3 transfers; sizes, and before deleting MD5 against the ETag; large ones run as a Slurm job |
| `manifest`, `clean --manifest` | without a bucket: files, sizes and SHA-256 of a copy; delete on the server only what it holds |
| `usage`, `mark <id> <STATUS>` | disk use of run folders; set a status by hand |

Use the scripts through their help, not their source: `uv run <skill-dir>/scripts/d3run.py --help` and
`d3run.py <command> --help` list every option, and the docstring at the top of `d3job.py` shows the job side; reading
the full source is not needed. Every command is light: a small SQLite file and one `sacct` call per 200 jobs (an ID
costs microseconds). Transfers
above 1 GB or 2,000 files refuse to run on the login host and ask for `--submit`. Schema, statuses and how to fit an
existing orchestrator: [references/registry.md](references/registry.md).

## 4. Files

| File | Purpose |
|---|---|
| `scripts/d3run.py` | run IDs, registry, submit, reconcile, sizing, S3 archive/push/pull (stdlib, `uv run`) |
| `scripts/d3job.py` | job side: exact end time, measured stop margin, checkpoints with S3 upload, resume, `status.json` |
| `scripts/check_sbatch.py` | lint job scripts: 24 h, partition and GPU, ignored `#SBATCH` lines, pip/conda, secrets |
| `assets/job_template.sbatch` | job script with run-ID logs, USR1 trap, GPU memory log, `uv run --no-sync` |
| `assets/site.example.toml` | template of the user's site file (no secrets) |
| `references/first-time-setup.md` | account, ssh key and Host block, JupyterHub password, certificate |
| `references/cluster.md` | partitions, submit filter, limits, priority and backfill, monitoring, JupyterHub |
| `references/interruptible-jobs.md` | checkpoint and resume patterns (PyTorch, JAX/Orbax, work lists), segments |
| `references/data-and-storage.md` | quota and NFS, S3 with the AWS CLI, layout, cleanup, the interim route |
| `references/registry.md` | schema, statuses, run files, fitting an existing orchestrator |
| `references/alerts.md` | the admin's monitoring alerts: what each means, what to do, how to avoid it |
| `references/pitfalls.md` | symptoms, causes and fixes seen on this server |
