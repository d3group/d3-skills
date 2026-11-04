#!/usr/bin/env python3
"""d3track: the experiment-tracking side of d3run (MLflow). Login host only, in the project's environment.

Every run logs into its own MLflow store, runs/<id>/mlflow/mlflow.db, which only its jobs write
(RunContext.mlflow() in d3job). `sync` copies the runs of these stores into the project's store runs/mlflow.db,
which only this script writes, and uploads that store to the bucket (s3://<bucket>/<project>/mlflow/mlflow.db):

    uv run tools/d3track.py sync                  # every run folder that has a store
    uv run tools/d3track.py sync <run_id> ...     # only these runs
    uv run tools/d3track.py where                 # how to open the project's store in the MLflow UI

Copy it next to d3run.py (it reads the registry settings through it). It has no inline script metadata on purpose:
`uv run` then uses the project's environment, so it reads the stores with the same MLflow version the jobs wrote
them with (`uv add mlflow`). Each store is read from a snapshot (the file and its journal copied while it did not
change), never opened in place, so a job that writes it at the same time is not disturbed. Metrics are appended
(only points the project's store does not have yet), params copied once, tags and status updated; artifacts stay
in the run folder (tag d3.artifact_uri). Sync before `d3run.py archive --clean`: a cleaned run folder keeps no store
on the server (its copy is in the bucket; `d3run.py pull runs/<id>` brings it back).
"""
from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import d3run  # noqa: E402  registry settings and the aws command

TERMINAL = ("FINISHED", "FAILED", "KILLED")


def die(msg: str) -> None:
    print(f"d3track: {msg}", file=sys.stderr)
    sys.exit(2)


def _stat(f: Path) -> tuple[int, int] | None:
    try:
        st = f.stat()
    except FileNotFoundError:
        return None
    return st.st_mtime_ns, st.st_size


def snapshot(db: Path, into: Path) -> Path | None:
    """Copy a store and its rollback journal while neither changes; None if it kept changing. The writing job
    may create or delete the journal at any moment: a file that vanishes during the copy means try again."""
    journal = db.with_name(db.name + "-journal")
    for _ in range(5):
        before = (_stat(db), _stat(journal))
        try:
            shutil.copy2(db, into / "mlflow.db")
            (into / "mlflow.db-journal").unlink(missing_ok=True)
            if before[1] is not None:
                shutil.copy2(journal, into / "mlflow.db-journal")   # SQLite rolls an unfinished write back
        except FileNotFoundError:
            time.sleep(1)
            continue
        if (_stat(db), _stat(journal)) == before:
            return into / "mlflow.db"
        time.sleep(1)
    return None


def settings(root: Path) -> dict | None:
    """The registry settings (bucket, endpoint, profile), or None in a project without `d3run.py init`."""
    if not (root / "runs" / "registry.db").exists():
        return None
    conn = d3run.open_registry(root)
    try:
        return d3run.get_settings(conn)
    finally:
        conn.close()


def project_store(dst, root: Path, name: str, cache: dict) -> str:
    if name not in cache:
        exp = dst.get_experiment_by_name(name)
        cache[name] = exp.experiment_id if exp else dst.create_experiment(
            name, artifact_location=(root / "runs" / "mlflow-artifacts").resolve().as_uri())
    return cache[name]


def copy_run(src, run, dst, exp_id: str) -> tuple[str, int, str]:
    """Bring one run of a run's store up to date in the project's store; returns (run ID, new points, status)."""
    from mlflow.entities import Metric, Param, RunTag
    d3_id = run.data.tags.get("d3.run_id") or run.info.run_name
    found = dst.search_runs([exp_id], filter_string=f"tags.`d3.run_id` = '{d3_id}'", max_results=1)
    if found:
        drid = found[0].info.run_id
    else:
        drid = dst.create_run(exp_id, start_time=run.info.start_time, run_name=run.info.run_name,
                              tags={"d3.run_id": d3_id}).info.run_id
    have = dst.get_run(drid).data.params
    params = [Param(k, v) for k, v in sorted(run.data.params.items()) if k not in have]
    tags = [RunTag(k, v) for k, v in sorted(run.data.tags.items()) if k != "mlflow.runName"]
    tags += [RunTag("d3.artifact_uri", run.info.artifact_uri or ""), RunTag("d3.source_run_id", run.info.run_id)]
    for i in range(0, len(params), 100):
        dst.log_batch(drid, params=params[i:i + 100])
    for i in range(0, len(tags), 100):
        dst.log_batch(drid, tags=tags[i:i + 100])
    new = 0
    for key in sorted(run.data.metrics):
        hist = sorted(src.get_metric_history(run.info.run_id, key), key=lambda m: (m.timestamp, m.step))
        add = [Metric(m.key, m.value, m.timestamp, m.step) for m in hist[len(dst.get_metric_history(drid, key)):]]
        for i in range(0, len(add), 1000):
            dst.log_batch(drid, metrics=add[i:i + 1000])
        new += len(add)
    status = run.info.status
    if status in TERMINAL:
        dst.set_terminated(drid, status, end_time=run.info.end_time)
    else:
        dst.update_run(drid, status=status)
    return d3_id, new, status


def upload(root: Path, store: Path) -> None:
    st = settings(root)
    if st is None:
        print("no registry here: the project's store stays on the server (d3run.py init sets the bucket)")
        return
    if not st.get("s3_uri"):
        print("no bucket set: the project's store stays on the server; copy it to the laptop with rsync")
        return
    uri = f"{st['s3_uri']}/mlflow/mlflow.db"
    try:
        aws = d3run.aws_cmd(st)
    except SystemExit:
        print(f"not uploaded to {uri}: no AWS CLI on this host")
        return
    res = subprocess.run(aws + ["s3", "cp", str(store), uri, "--only-show-errors"], capture_output=True, text=True)
    print(f"uploaded to {uri}" if res.returncode == 0 else f"upload to {uri} failed: {res.stderr.strip()}")


def cmd_sync(a) -> None:
    if os.environ.get("SLURM_JOB_ID"):
        die("sync writes the project's store and runs only on the login host, not inside a job (one writer)")
    from mlflow import MlflowClient
    root = d3run.project_root(a.root)
    runs = root / "runs"
    folders = [runs / r for r in a.run_ids] if a.run_ids else sorted(p for p in runs.glob("*") if p.is_dir())
    stores = [(f, f / "mlflow" / "mlflow.db") for f in folders if (f / "mlflow" / "mlflow.db").exists()]
    if not stores:
        print("no run folder with an MLflow store (RunContext.mlflow() creates runs/<id>/mlflow/mlflow.db)")
        return
    store = runs / "mlflow.db"
    dst = MlflowClient(f"sqlite:///{store.resolve()}")
    cache: dict = {}
    total = 0
    for folder, db in stores:
        with tempfile.TemporaryDirectory(prefix="d3track-") as tmp:
            try:
                snap = snapshot(db, Path(tmp))
                if snap is None:
                    print(f"{folder.name}: store kept changing, skipped (next sync)")
                    continue
                src = MlflowClient(f"sqlite:///{snap}")
                for exp in src.search_experiments():
                    exp_id = project_store(dst, root, exp.name, cache)
                    for run in src.search_runs([exp.experiment_id], max_results=1000):
                        d3_id, new, status = copy_run(src, run, dst, exp_id)
                        total += new
                        print(f"{d3_id}: {status.lower()}, {new} new metric points")
            except Exception as exc:          # noqa: BLE001  one store's trouble never stops the others
                print(f"{folder.name}: not read ({type(exc).__name__}: {exc}); skipped (next sync)")
    print(f"project store {store.relative_to(root)}: {total} new metric points")
    if not a.no_upload:
        upload(root, store)


def cmd_where(a) -> None:
    import mlflow
    root = d3run.project_root(a.root)
    st = settings(root) or {}
    v = mlflow.__version__
    print(f"project store: {root / 'runs' / 'mlflow.db'} (written by `d3track.py sync`; MLflow {v})")
    print("open it on the laptop, with the same MLflow version:")
    if st.get("s3_uri"):
        print(f"  aws s3 cp {st['s3_uri']}/mlflow/mlflow.db mlflow.db --profile <laptop profile>")
    else:
        print(f"  rsync -a <alias>:{root}/runs/mlflow.db mlflow.db")
    print(f"  uvx --from 'mlflow=={v}' mlflow ui --backend-store-uri sqlite:///mlflow.db")


def main() -> None:
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--root", help="project folder (default: git top level, or $D3RUN_ROOT)")
    p = argparse.ArgumentParser(prog="d3track.py", description=__doc__.split("\n\n")[0])
    sub = p.add_subparsers(dest="command", required=True)
    s = sub.add_parser("sync", parents=[common],
                       help="copy the runs' MLflow stores into the project's store, upload it")
    s.add_argument("run_ids", nargs="*", help="run IDs (default: every run folder with a store)")
    s.add_argument("--no-upload", action="store_true", help="do not upload the project's store to the bucket")
    s.set_defaults(func=cmd_sync)
    s = sub.add_parser("where", parents=[common], help="how to open the project's store in the MLflow UI")
    s.set_defaults(func=cmd_where)
    a = p.parse_args()
    a.func(a)


if __name__ == "__main__":
    main()
