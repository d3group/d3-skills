# Experiment tracking: MLflow and Weights & Biases, where a project uses them

The registry (`d3run.py`) books what ran where: run ID, commit, config, Slurm attempts, status. A tracking tool
books what the training saw: parameters, metrics per step, small artifacts, and a UI to compare runs. The two fit
together through the run ID. Tracking is optional: the skill supports it where a project already uses it or the
user wants it, and never adds it on its own (section 1). For a new setup MLflow is the recommendation because it
keeps everything on university infrastructure (the server and the bucket); Weights & Biases suits users who already
work with it, for data without restrictions.

## Contents
1. Whether to track: detect, then ask
2. What goes wrong without care
3. MLflow: one store per run, one project store
3a. The group MLflow server (since 2026-11-05)
4. In the training code
5. On the login host: sync and view
6. Weights & Biases
7. What not to track
8. Tested

## 1. Whether to track: detect, then ask

Look in the project first (on the laptop, in the repository):

```bash
grep -n -i -E '\b(mlflow|wandb)\b' pyproject.toml uv.lock requirements*.txt setup.cfg 2>/dev/null | head
grep -rlE '^\s*(import|from) (mlflow|wandb)\b|MLflowLogger|WandbLogger|report_to|MLFLOW_|WANDB_' \
     --include='*.py' --include='*.sh' --include='*.sbatch' --include='*.yaml' --include='*.toml' \
     --exclude=d3job.py --exclude=d3track.py --exclude-dir=.venv . | head
ls -d mlruns mlflow.db wandb 2>/dev/null
```

`d3job.py` and `d3track.py` are excluded: the skill's own helpers mention both tools in every project.

- **Found:** the project tracks. Keep its tool and fit it: one store per run and one run per run ID across
  segments (sections 2 to 6). An existing `mlruns/` or `mlflow.db` that jobs wrote together is moved to the
  per-run layout only with the user's yes; until then nothing changes.
- **Training frameworks report on their own:** Lightning loggers (`MLFlowLogger`, `WandbLogger`) and Hugging Face's
  `report_to=` (older versions report to every installed tool by default). Set `report_to` explicitly, so a
  package that happens to be installed does not start logging, or asking for a W&B login, inside a job.
- **A `WANDB_API_KEY` in a file** is a secret in the repository: tell the user (the key belongs in `~/.netrc`
  through `wandb login`).
- **Not found, and the work trains or compares runs:** ask once, with the other open questions: "Do you want to
  track these experiments (metrics per step, runs side by side in a UI)? MLflow (recommended, stays on university
  storage), Weights & Biases (if you already use it; data without restrictions only), or none (the run registry
  still records every run)." None is the default; a one-off job, a data conversion or a sweep the user evaluates
  from `results/` needs no tracking.
- **Remember the answer** as `tracking = "mlflow" | "wandb" | "none"` under `[projects.<name>]` in the site file and
  do not ask again. Without a user to ask (a batch run), add nothing and list the question.

## 2. What goes wrong without care

- **One SQLite file, many writers.** MLflow's default store is an SQLite file (`mlflow.db`; the folder store
  `./mlruns` is in maintenance mode). Many jobs on different nodes writing one SQLite file in the NFS home can
  corrupt it, as with the registry. Each store therefore has exactly one writer.
- **Segments split a run.** A run that spans three 24 h jobs becomes three MLflow runs unless every segment
  reopens the same one. MLflow also ends any active run as FINISHED when the process exits, so a segment that
  stops to resume later must set the status itself.
- **The login host runs light commands only.** No `mlflow server` there. Since 2026-11-05 the admin runs a group
  MLflow server instead (section 3a).
- **MLflow is not installed system-wide** (checked 2026-11-04 on the login host and a compute node). It comes from
  the project: `uv add mlflow`, which jobs then use through `uv run --no-sync`.

## 3. MLflow: one store per run, one project store

```
 job (any node)                                    login host                        laptop
 runs/<id>/mlflow/mlflow.db   one writer: the      d3track.py sync                   MLflow UI
   one MLflow run, all        run's jobs, one ───▶  snapshot of each store ──▶       uvx --from mlflow==<v>
   segments; artifacts/       after another          runs/mlflow.db (one writer) ──▶    mlflow ui
   uploaded at finish/fail                           s3://<bucket>/<project>/mlflow/mlflow.db
```

- `RunContext.mlflow()` (d3job) creates the run's store in the run folder: experiment = the project, run name =
  the run ID, tags from `run.json` (`d3.run_id`, `d3.tag`, `mlflow.source.git.commit`, `d3.config_hash`, …),
  and the params `d3run.py new` recorded as MLflow params. Later segments reopen the same MLflow run (its ID sits
  in `runs/<id>/mlflow/run_id`) and update `d3.attempt` and `d3.slurm_job_id`.
- `mark()`, `finish()` and `fail()` close the MLflow run: SCHEDULED when a segment stops to resume later,
  FINISHED when done, FAILED when failed. A run given up after hard deaths (d3job's `max_hard_failures`) is set
  FAILED by the segment that gives it up. `finish()` and `fail()` upload the store with the status.
- `d3track.py sync` on the login host copies every run's store into the project's store `runs/mlflow.db`, which
  only it writes, and uploads that to the bucket. It reads each store from a snapshot (the file and its journal
  copied while neither changed), so it never touches a store a job is writing; a store that keeps changing is
  skipped until the next sync. Metrics are appended (only new points), params copied once, tags and status
  updated; artifacts stay in the run folder (tag `d3.artifact_uri`).

## 3a. The group MLflow server (since 2026-11-05)

Facts as set up by the admin on 2026-11-05 (repository `d3group/ki-regio-server`, role `mlflow`):

- **Where:** `http://10.99.0.50:5000/mlflow` from the login host, the compute node and notebooks; in a browser
  `https://p086wiwi177011.wiwi.uni-wuerzburg.de/mlflow/` (import the server's CA first, as for the hub).
  `MLFLOW_TRACKING_URI` is preset in login shells (`/etc/profile.d`), in jobs (sbatch passes the environment on)
  and in hub notebooks.
- **Login:** every server account has an MLflow account. Its start password is the hub's start password from the
  admin's mail with `ml` appended (MLflow needs 12 characters). `mlflow-passwd` on the login host changes it and
  updates `~/.mlflow/credentials`, from which jobs and notebooks log in without setup. Forgot it: the admin resets
  it.
- **Artifacts** go through the server to the NAS (bucket `mlflow-artifacts`): no S3 keys needed. Final model
  weights and small files yes; running checkpoints stay in the run folder (the NAS has two disks for everyone).
- **Rights:** everyone reads every experiment; whoever creates one may change it and share it.
- **Client:** `uv add "mlflow>=3,<4"` (the server runs MLflow 3).
- **Which store:** with tracking = "mlflow", ask once which store the user wants: the group server (one UI for
  everyone's runs, no sync, artifacts on the NAS; needs the server up) or the run's own store (section 3; works
  without the server, travels with the run folder). Remember it as `mlflow_store = "server" | "run"` under
  `[projects.<name>]` in the site file.
- **On the server:** the code calls `ctx.mlflow(server=True)` instead of `ctx.mlflow()`. The first segment creates
  the run on the server in the experiment `<login>/<project>` (experiment names are shared by everyone on the
  server and another user's experiment is read-only; `experiment=` names one its owner shared) and keeps its ID in
  `runs/<id>/mlflow/run_id`, the server's URI in `runs/<id>/mlflow/tracking_uri`. Later segments continue the same
  run; `ctx.mlflow_uri()` returns the server's URI for framework loggers. A run keeps the store its first segment
  chose. Without `MLFLOW_TRACKING_URI` (the laptop) it logs into the run's own store and the job log says so.
- **Preset variable:** `ctx.mlflow()` without `server=True`, `d3track.py` and `mlflow ui --backend-store-uri` set
  their own URI and are not affected by it. Code that logs without setting a URI (plain `mlflow.log_metric`, a
  Lightning `MLFlowLogger()` without `tracking_uri`) logs to the group server, no longer to an `mlflow.db` in the
  working directory.

## 4. In the training code

```python
import mlflow
from d3job import RunContext

ctx = RunContext.from_env()
if ctx.finished():
    raise SystemExit(0)
ctx.mlflow()                                   # start, or resume in a later segment
ckpt = ctx.latest_checkpoint()
start = load(ckpt) if ckpt else 0
if start == 0:
    mlflow.log_params(hyperparameters)         # once: params cannot change within a run
ctx.mark("running")
try:
    for epoch in range(start, n_epochs):
        loss = train_one_epoch()
        mlflow.log_metric("train_loss", loss, step=epoch)
        if ctx.should_checkpoint():
            with ctx.checkpoint(epoch + 1) as path:
                save(path)
            if ctx.should_stop():
                ctx.mark("interrupted", progress=(epoch + 1) / n_epochs)   # MLflow: SCHEDULED
                raise SystemExit(0)
    save_results(ctx.results_dir)
    ctx.finish()                               # MLflow: FINISHED
except Exception as exc:
    ctx.fail(exc)                              # MLflow: FAILED
    raise
```

- **Steps continue across segments:** log with the global step (epoch or optimizer step from the checkpoint), so
  the curve of a resumed run has no gaps or overlaps.
- **Frameworks:** call `ctx.mlflow()` first. Hugging Face's `MLflowCallback` logs into the active run.
  Lightning: `MLFlowLogger(tracking_uri=ctx.mlflow_uri(), run_id=ctx.mlflow())` (call `ctx.mlflow()` once and keep
  the ID). `MLFLOW_TRACKING_URI` and `MLFLOW_EXPERIMENT_NAME` are set for libraries that read them.
- **Group server** (`mlflow_store = "server"`): `ctx.mlflow(server=True)` in place of `ctx.mlflow()`; the rest of
  the code stays the same (section 3a).
- **Frequent logging:** every metric call is a write to SQLite on NFS. Log per epoch or every N steps, or turn on
  `mlflow.config.enable_async_logging()`; d3job's end of a segment flushes the queue (end_run waits for it).
  A store written several times a second rarely holds still for a snapshot, so the project view catches up when
  the job pauses or ends.
- **Local runs** (no `D3RUN_*` variables) log into `runs/local/mlflow/`; the same code runs on the laptop.

## 5. On the login host: sync and view

```bash
uv run tools/d3track.py sync          # all run folders with a store; or: sync <run_id> …
uv run tools/d3track.py where         # the commands to open the project's store on the laptop
```

- Sync with every `reconcile` while a round runs (it is light: small file copies) and always before
  `d3run.py archive --clean`, which leaves no store on the server (the copy is in the bucket;
  `d3run.py pull runs/<id>` brings it back, then sync again).
- `d3track.py` has no inline script metadata on purpose: `uv run` uses the project's environment, so it reads the
  stores with the MLflow version that wrote them. The laptop opens the project's store with the same version
  (`where` prints it): `uvx --from 'mlflow==<v>' mlflow ui --backend-store-uri sqlite:///mlflow.db`.
- With a bucket, `sync` uploads the store to `s3://<bucket>/<project>/mlflow/mlflow.db`; the laptop takes it from
  there (`aws s3 cp … --profile <laptop profile>`). Without one: `rsync -a <alias>:<proj>/runs/mlflow.db .`
- Runs on the group server need no sync (`sync` skips them): their UI is the server's (section 3a).
- Never run `mlflow ui` or `mlflow server` as a lasting process on the login host.

## 6. Weights & Biases

```python
run = ctx.wandb()                              # id and name = run ID, group = round tag, resume="allow"
run.log({"train_loss": loss}, step=epoch)
```

- Compute nodes reach W&B directly (tested 2026-11-04, no proxy), so the default online mode works and every
  segment continues the same W&B run through `resume="allow"`. `mark("interrupted")` calls `mark_preempting()` and
  ends the segment; `finish()` and `fail()` finish the run with exit code 0 or 1.
- Login: `wandb login` once on the server (the key lands in `~/.netrc`; never in the repository or a job script).
- Offline (`WANDB_MODE=offline`): each segment writes `runs/<id>/wandb/offline-run-*`; upload them in order with
  `wandb sync` on the login host.
- W&B's service is outside university infrastructure: only data without restrictions, never artifacts from data
  under an agreement (references/data-and-storage.md, section 9).

## 7. What not to track

- Checkpoints stay with d3job (server and bucket, pruned); logging them as MLflow or W&B artifacts doubles the
  storage and the quota.
- Large outputs go to `results/` (uploaded at `finish()`); log their location or a small summary instead.
- No personal or agreement data in params, tags or artifacts: the stores travel to the bucket and the laptop.

## 8. Tested

On 2026-11-04 with MLflow 3.18 and wandb 0.31 on a laptop, with the skill's own scripts: a run interrupted and
resumed in a second segment (one MLflow run, steps 0 to 9 without gaps, SCHEDULED, then FINISHED), a failed run, a
run given up after a hard death (RUNNING, then FAILED), repeated syncs (only new points), syncs while a job wrote
15,000 points (skipped while busy, then complete, no crash), async logging (all points stored), and `ctx.wandb()`
over two offline segments. On the server: a compute node reached pypi.org, github.com, api.wandb.ai, the bucket
and the login host; MLflow was not installed. Not tested: W&B against its service.

On 2026-11-05 against the group server (MLflow 3.17.2, client 3.17.2, as a service account on the login host):
`ctx.mlflow(server=True)` over two segments kept one MLflow run (metric points from both segments), named the
experiment `<login>/<project>`, stored an artifact through the server (`mlflow-artifacts:/…`) and left the run
SCHEDULED after the interruption. `evals/tests/test_d3job.py` covers the same on the laptop with a stand-in store,
plus the fallback without `MLFLOW_TRACKING_URI`.
