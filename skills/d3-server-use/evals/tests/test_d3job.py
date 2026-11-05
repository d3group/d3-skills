"""Tests for d3job.py: checkpoint names torch.save accepts, uploads before one was timed, resume from S3, MLflow on
the group server.

Run on the laptop: python3 evals/tests/test_d3job.py [path to d3job.py]   (default: the skill's scripts/d3job.py)
A fake `aws` maps s3:// to a local folder; nothing connects to a bucket. Needs bash and Python 3.10+; the MLflow
checks need uv (they fetch MLflow 3 into uv's cache) and are skipped without it.
"""
import getpass
import os
import shutil
import subprocess
import sys
import tempfile
import textwrap
import time
from pathlib import Path

D3JOB = (Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parents[2] / "scripts" / "d3job.py").resolve()
FAILS = []

FAKE_AWS = r'''#!/bin/bash
[ "$1" = "s3" ] || exit 1
op=$2; shift 2
args=(); skip=
for a in "$@"; do
  if [ -n "$skip" ]; then skip=; continue; fi
  case $a in --only-show-errors|--recursive) ;; --exclude|--endpoint-url|--profile) skip=1 ;; *) args+=("$a") ;; esac
done
map() { local p=${1#s3://}; echo "$FAKE_S3/${p%/}"; }
case $op in
  cp) src=${args[0]}; dst=${args[1]}
      if [[ $src == s3://* ]]; then s=$(map "$src"); [ -f "$s" ] || exit 1; mkdir -p "$(dirname "$dst")"; cp "$s" "$dst"
      else d=$(map "$dst"); mkdir -p "$(dirname "$d")"; cp "$src" "$d"; fi ;;
  sync) src=${args[0]}; dst=${args[1]}
      if [[ $src == s3://* ]]; then s=$(map "$src"); [ -d "$s" ] || exit 1; mkdir -p "$dst"; cp -R "$s"/. "$dst"/
      else d=$(map "$dst"); mkdir -p "$d"; cp -R "$src"/. "$d"/; fi ;;
  rm) for a in "${args[@]}"; do [[ $a == s3://* ]] && rm -rf "$(map "$a")"; done ;;
  *) exit 1 ;;
esac
'''

JOB = textwrap.dedent('''\
    import sys
    sys.path.insert(0, sys.argv[1])
    from d3job import RunContext
    kw = {"upload_mb_s": float(sys.argv[3])} if len(sys.argv) > 3 else {}
    ctx = RunContext.from_env(**kw)
    mode = sys.argv[2]
    if mode == "resume":
        ck = ctx.latest_checkpoint()
        print("RESUMED", ck.name if ck else None, ck.read_bytes()[:3] if ck else b"")
    elif mode == "server":
        import mlflow
        rid = ctx.mlflow(server=True)
        mlflow.log_metric("m", ctx.attempt, step=ctx.attempt)
        exp = mlflow.get_experiment(mlflow.active_run().info.experiment_id)
        print("RID", rid)
        print("URI", ctx.mlflow_uri())
        print("EXP", exp.name)
        print("ARTIFACTS", exp.artifact_location)
        ctx.mark("interrupted", progress=0.5)
    else:
        ctx.mark("running")
        print("STOP", ctx.should_stop())
        with ctx.checkpoint(5) as p:
            print("TMPNAME", p.name)
            p.write_bytes(b"abc" * 1000)
    ''')


def check(name, cond, out=""):
    print(("ok   " if cond else "FAIL ") + name)
    if not cond:
        FAILS.append(name)
        print(textwrap.indent(out, "     | "))


def case(elapsed_s: float, limit_s: int, mode: str, *extra, keep: Path | None = None):
    tmp = keep or Path(tempfile.mkdtemp())
    (tmp / "s3").mkdir(exist_ok=True)
    aws = tmp / "aws"
    aws.write_text(FAKE_AWS)
    aws.chmod(0o755)
    (tmp / "job.py").write_text(JOB)
    run_dir = tmp / "runs" / "r1"
    env = {k: v for k, v in os.environ.items() if not k.startswith(("SLURM_", "D3RUN_"))}
    env.update({"D3RUN_ID": "r1", "D3RUN_DIR": str(run_dir), "D3RUN_ATTEMPT": "1" if mode != "resume" else "2",
                "D3RUN_TIME_LIMIT_S": str(limit_s), "D3RUN_JOB_START": str(int(time.time() - elapsed_s)),
                "D3RUN_S3_URI": "s3://bkt/proj/runs/r1", "D3RUN_AWS": str(aws), "FAKE_S3": str(tmp / "s3")})
    r = subprocess.run([sys.executable, str(tmp / "job.py"), str(D3JOB.parent), mode, *extra], cwd=tmp, env=env,
                       capture_output=True, text=True)
    return tmp, r.stdout + r.stderr


def mlflow_case(tmp: Path, attempt: int, server_uri: str | None):
    """A job with ctx.mlflow(server=True) under uv with MLflow 3; a SQLite store outside the run folder stands in
    for the group server (MLFLOW_TRACKING_URI as preset on the cluster)."""
    run_dir = tmp / "runs" / "r1"
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "run.json").write_text('{"project": "proj"}')
    (tmp / "job.py").write_text(JOB)
    env = {k: v for k, v in os.environ.items() if not k.startswith(("SLURM_", "D3RUN_", "MLFLOW_"))}
    env.update({"D3RUN_ID": "r1", "D3RUN_DIR": str(run_dir), "D3RUN_ATTEMPT": str(attempt)})
    if server_uri:
        env["MLFLOW_TRACKING_URI"] = server_uri
    r = subprocess.run(["uv", "run", "--quiet", "--no-project", "--with", "mlflow>=3,<4", "python",
                        str(tmp / "job.py"), str(D3JOB.parent), "server"], cwd=tmp, env=env,
                       capture_output=True, text=True)
    out = r.stdout + r.stderr
    got = {l.split()[0]: l.split(None, 1)[1] for l in r.stdout.splitlines() if l.split()[:1] and l.split()[0] in
           ("RID", "URI", "EXP", "ARTIFACTS")}
    return got, out


def test_mlflow_server():
    if not shutil.which("uv"):
        print("skip ctx.mlflow(server=True): no uv on PATH")
        return
    # 5. on the server: the run lives in the server's store, keeps one MLflow run across segments
    tmp = Path(tempfile.mkdtemp())
    (tmp / "server").mkdir()
    server = f"sqlite:///{tmp / 'server' / 'mlflow.db'}"
    a1, out1 = mlflow_case(tmp, 1, server)
    check("server: the run is created in the server's store", a1.get("URI") == server and
          (tmp / "server" / "mlflow.db").is_file() and not (tmp / "runs/r1/mlflow/mlflow.db").exists(), out1)
    check("server: experiment named <login>/<project> (names are shared on the server)",
          a1.get("EXP") == f"{getpass.getuser()}/proj", out1)
    check("server: artifacts not in the run folder (the server stores them)",
          "runs/r1" not in (a1.get("ARTIFACTS") or "runs/r1"), out1)
    a2, out2 = mlflow_case(tmp, 2, server)
    check("server: attempt 2 resumes the same MLflow run", a1.get("RID") and a2.get("RID") == a1.get("RID"), out2)
    a3, out3 = mlflow_case(tmp, 3, None)
    check("server: a later segment stays on the server even without the variable",
          a3.get("RID") == a1.get("RID") and a3.get("URI") == server, out3)
    # 6. no MLFLOW_TRACKING_URI (the laptop): the run's own store, said in the log
    tmp = Path(tempfile.mkdtemp())
    b1, out = mlflow_case(tmp, 1, None)
    check("no tracking URI: falls back to the run's own store", (b1.get("URI") or "").endswith("runs/r1/mlflow/mlflow.db")
          and "own store" in out, out)


def main():
    s3ck = Path("s3/bkt/proj/runs/r1/checkpoints")
    # 1. smoke: 5 min limit, 230 s gone, the stop checkpoint is the first one -> uploaded (small file)
    tmp, out = case(230, 300, "stop")
    check("smoke stop checkpoint: in the stop window", "STOP True" in out, out)
    tmpname = next((l.split()[1] for l in out.splitlines() if l.startswith("TMPNAME")), ".")
    check("temporary checkpoint name does not start with a dot (torch.save rejects it)", not tmpname.startswith("."), out)
    check("smoke stop checkpoint: uploaded although no upload was measured",
          (tmp / s3ck / "step-000000005").is_file() and (tmp / s3ck / "LATEST.json").is_file(), out)
    # 4. attempt 2 without local checkpoints fetches it from S3
    shutil.rmtree(tmp / "runs" / "r1" / "checkpoints")
    _, out2 = case(5, 300, "resume", keep=tmp)
    check("attempt 2 fetches the checkpoint from S3", "RESUMED step-000000005 b'abc'" in out2 and "fetched from S3" in out2,
          out2)
    # 2. a checkpoint too large for the time left stays local (estimate from size at a slow assumed rate)
    tmp, out = case(230, 300, "stop", "0.00001")
    check("large stop checkpoint stays local", not (tmp / s3ck / "step-000000005").exists() and "stays local" in out, out)
    # 3. early first checkpoint (far from the end): uploaded, as before
    tmp, out = case(10, 3600, "stop")
    check("early checkpoint: not in the stop window", "STOP False" in out, out)
    check("early checkpoint: uploaded", (tmp / s3ck / "step-000000005").is_file(), out)
    test_mlflow_server()
    print(f"\n{len(FAILS)} failed")
    sys.exit(1 if FAILS else 0)


if __name__ == "__main__":
    main()
