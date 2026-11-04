# The run registry

`d3run.py` keeps `runs/registry.db` (SQLite, rollback journal, no WAL) in the project's checkout on the server. Only
`d3run.py` on the login host writes it. Jobs write their own run folder; `reconcile` reads it back.

## Run ID

`<YYYYMMDD>-<login>-<slug>-<4 hex>`, e.g. `20261104-abcd-lstm-s42-7c1e`.

| Part | Why |
|---|---|
| date first | sorts by time in `ls`, S3 listings, notes |
| login | IDs from two users never collide when runs meet (shared project prefix, merged tables, papers) |
| slug (config name or `--name`, at most 24 characters) | readable in logs and notes |
| 4 random hex | unique within a day; `new` checks the registry and draws again on a collision |

Only `a-z0-9-`, at most about 50 characters: safe as a folder name, an S3 key and part of a Slurm job name (the job
name is `<slug>-<hex>`, because queue views cut long names).

Two columns sit next to the ID, not inside it:

- `config_hash`: SHA-256 of the config file plus the `--param` values. `new` refuses a second run with the same hash
  and commit unless `--allow-duplicate` (replications) is given; an interrupted run is continued with `submit`, not
  recreated.
- `tag`: the round or study (`pilot-2026-11`, `lstm-sweep`). Post-processing selects runs by tag, never by lists of
  Slurm job IDs.

## Tables

`runs`: `run_id`, `user`, `project`, `name`, `tag`, `git_commit`, `git_dirty`, `config_path`, `config_hash`,
`params_json`, `status`, `progress`, `run_dir`, `s3_uri`, `note`, `created_at`, `updated_at`, `archived_at`,
`cleaned_at`.

`attempts` (one row per Slurm job of a run): `run_id`, `attempt`, `slurm_job_id`, `submitted_at`, `job_name`,
`depends_on`, `req_time_s`, `req_cpus`, `req_mem`, `req_gpus`, `state`, `exit_code`, `elapsed_s`, `total_cpu_s`,
`max_rss_mb`, `gpu_mem_mb`, `node`, `started_at`, `ended_at`, `out_path`, `err_path`.

`settings`: `user`, `project`, `s3_uri`, optional `s3_endpoint`, `aws_profile`, `aws_bin`.

Every job `d3run.py` submits carries the Slurm comment `d3run`; `feed` holds and releases only those (fair use,
cluster.md section 4). Times are server local time in the format `sacct` prints (checked against the server's
`sacct --parsable2` on 2026-11-04: `TotalCPU` as `MM:SS.mmm`, `MaxRSS` on the `.batch` line, e.g. `4192052K`). If Slurm job IDs repeat (after a rebuild), `reconcile`
picks the accounting record whose submit time is closest to the attempt's, and `find-job` lists every match.

## Run status

| Status | Meaning | Set by |
|---|---|---|
| `NEW` | ID created, nothing submitted | `new` |
| `SUBMITTED` / `RUNNING` | an attempt is queued / running | `submit`, `reconcile` |
| `INTERRUPTED` | attempts ended, work remains (checkpoint exists) | `reconcile` from `status.json` or `TIMEOUT` |
| `DONE` | the job called `ctx.finish()`, or a job without d3job exited 0 | `reconcile` |
| `FAILED` | `ctx.fail()`, or Slurm `FAILED`/`OUT_OF_MEMORY`/`NODE_FAIL` | `reconcile` |
| `CANCELLED` | cancelled | `reconcile`, `mark` |

Finished states stick; `submit --force` starts a run again.

## Files in a run folder

| File | Written by | Content |
|---|---|---|
| `run.json` | `new` | ID, commit, config hash, parameters, tag, S3 prefix (the S3 copy describes itself) |
| `config.<ext>` | `new` | the config as submitted |
| `status.json` | the job (`d3job`) | `state`, `progress`, `attempt`, `slurm_job_id`, `host`, error |
| `archive.json` | `archive` | verified file count and bytes, `verified_at`, `cleaned_at` |
| `logs/attempt-NN-<jobid>.out/.err` | Slurm | output of each attempt |
| `logs/gpu-<jobid>.csv` | job template | GPU memory per minute (read by `size`) |
| `checkpoints/` | `d3job` | `step-…`, `LATEST.json`, `uploaded.json` |
| `results/` | the job | metrics, predictions, figures |
| `mlflow/` | the job (`ctx.mlflow()`) | the run's own MLflow store `mlflow.db`, `run_id`, `artifacts/` ([tracking.md](tracking.md)) |

## Fitting an existing orchestrator

Projects with their own submit script and database (one row per experiment, a per-job result file) need not switch
to `d3run.py`. Check these points instead:

1. **An ID made before `sbatch`** names the logs and result files (a UUID works). Logs named after `%j` alone break
   when job IDs restart.
2. **Attempts:** store each Slurm job ID with its submit time; one experiment may need several jobs.
3. **One writer:** jobs do not write the central database. They write their own result file or a status file; the
   login host imports them. If jobs must write it, at least turn WAL off (`PRAGMA journal_mode=DELETE`), because
   WAL needs all writers on one host, and the login host is a different machine from the compute node.
4. **Selection by tag or experiment ID:** post-processing scripts that take lists of Slurm job IDs and translate them
   (`WHERE slurm_job_id IN …`) return wrong experiments once new IDs reach the old range. Give them experiment IDs or
   a round tag.
5. **Commit per experiment**, and refuse submissions from a dirty tree.
6. **Jobs that rewrite shared outputs from all runs** (summary tables, figures) do not belong in an automatic
   round: run them on purpose, on a chosen set of runs.
7. **Experiment tracking with the same rule:** MLflow or W&B logs into a store per run (or the W&B service), named
   by the experiment ID, and resumes that run in every segment; no store that all jobs write
   ([tracking.md](tracking.md)).
