"""Tests for d3run.py: `queue`, `size` across widths, `scale`, `submit --after-tag`, the job-count warning and the
GPU smoke guard.

Run on the laptop: python3 evals/tests/test_d3run.py [path to d3run.py]   (default: the skill's scripts/d3run.py)
Fake squeue/scontrol/sbatch on PATH replay a queue snapshot taken on the server on 2026-11-05; nothing connects to
the server. Needs git and Python 3.10+.
"""
import json
import os
import sqlite3
import subprocess
import sys
import tempfile
import textwrap
from pathlib import Path

D3RUN = (Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parents[2] / "scripts" / "d3run.py").resolve()
FAILS = []

SQUEUE = """\
1001|vaha|R|cpu|N/A|4|None|18:33:11|
1002|vaha|R|cpu|N/A|4|None|3:24:24|
1006|tila|R|main|gres/gpu:1|4|None|23:26:02|
1007|tila|R|main|gres/gpu:1|1|None|5:39:17|
1008|tila|R|main|gres/gpu:1|1|None|4:05:01|
1009|ving|R|main|gres/gpu:1|1|None|1:28:18|
1010|ving|PD|main|gres/gpu:1|1|Resources|1-00:00:00|
1011|ving|PD|main|gres/gpu:1|1|Priority|1-00:00:00|
1012|tila|PD|main|gres/gpu:1|4|Dependency|1-00:00:00|
1013|vaha|PD|cpu|N/A|4|JobArrayTaskLimit|1-00:00:00|
"""
SCONTROL_NODE = ("NodeName=compute Arch=x86_64 CoresPerSocket=42 CPUAlloc=27 CPUEfctv=166 CPUTot=170 "
                 "Gres=gpu:4 RealMemory=638976 AllocMem=270336 FreeMem=313752 State=MIXED "
                 "CfgTRES=cpu=166,mem=624G,billing=166,gres/gpu=4 AllocTRES=cpu=27,mem=264G,gres/gpu=4\n")


def check(name, cond, out=""):
    print(("ok   " if cond else "FAIL ") + name)
    if not cond:
        FAILS.append(name)
        print(textwrap.indent(out, "     | "))


def setup() -> tuple[Path, dict]:
    tmp = Path(tempfile.mkdtemp())
    bindir = tmp / "bin"
    bindir.mkdir()
    (tmp / "squeue.txt").write_text(SQUEUE)
    (tmp / "node.txt").write_text(SCONTROL_NODE)
    (bindir / "squeue").write_text(f"#!/bin/sh\ncat {tmp}/squeue.txt\n")
    (bindir / "scontrol").write_text(
        f"#!/bin/sh\nif [ \"$1 $2\" = \"show node\" ]; then cat {tmp}/node.txt; else echo \"$@\" >> {tmp}/scontrol.log; fi\n")
    (bindir / "sbatch").write_text(
        f"#!/bin/sh\necho \"$@\" >> {tmp}/sbatch.log\nn=$(wc -l < {tmp}/sbatch.log | tr -d ' ')\necho $((5000 + n))\n")
    for f in bindir.iterdir():
        f.chmod(0o755)
    proj = tmp / "proj"
    proj.mkdir()
    env = dict(os.environ, PATH=f"{bindir}:{os.environ['PATH']}", USER="abcd")
    env.pop("SLURM_JOB_ID", None)
    subprocess.run(["git", "init", "-q"], cwd=proj, check=True)
    subprocess.run(["git", "-c", "user.email=t@t", "-c", "user.name=t", "commit", "-q", "--allow-empty", "-m", "x"],
                   cwd=proj, check=True)
    (proj / "job.sbatch").write_text("#!/bin/bash\n#SBATCH --time=00:10:00\necho hi\n")
    run(proj, env, "init", "--user", "abcd", "--no-s3")
    return proj, env


def run(proj, env, *args) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(D3RUN), *args], cwd=proj, env=env, capture_output=True, text=True)


def add_run(proj, tag, cfg_hash, status, attempts, progress=None):
    """attempts: list of dicts with req_cpus, req_mem, req_gpus, elapsed_s, total_cpu_s, max_rss_mb, gpu_util, state."""
    conn = sqlite3.connect(proj / "runs" / "registry.db")
    rid = f"20261105-abcd-{tag}-{os.urandom(2).hex()}"
    conn.execute("INSERT INTO runs (run_id, user, project, name, tag, config_hash, status, progress, run_dir, "
                 "created_at, updated_at) VALUES (?, 'abcd', 'proj', 'x', ?, ?, ?, ?, ?, 't', 't')",
                 (rid, tag, cfg_hash, status, progress, str(proj / "runs" / rid)))
    for i, a in enumerate(attempts, 1):
        conn.execute("INSERT INTO attempts (run_id, attempt, slurm_job_id, submitted_at, req_time_s, req_cpus, req_mem, "
                     "req_gpus, state, elapsed_s, total_cpu_s, max_rss_mb, gpu_mem_mb, gpu_util) "
                     "VALUES (?, ?, ?, 't', 86400, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                     (rid, i, a.get("jid", str(4000 + i)), a["req_cpus"], a.get("req_mem", "8G"), a.get("req_gpus", 0),
                      a.get("state", "COMPLETED"), a.get("elapsed_s"), a.get("total_cpu_s"), a.get("max_rss_mb"),
                      a.get("gpu_mem_mb"), a.get("gpu_util")))
    conn.commit()
    return rid


def main():
    # ---------------------------------------------------------------- queue
    proj, env = setup()
    r = run(proj, env, "queue")
    out = r.stdout + r.stderr
    check("queue runs", r.returncode == 0, out)
    check("queue: GPUs in use 4 of 4", "4 of 4" in out, out)
    check("queue: CPUs 27 of 166", "27 of 166" in out, out)
    check("queue: GPU release times sorted, upper bounds", "1.5 h, 4.1 h, 5.7 h, 23.4 h" in out, out)
    check("queue: two other users' GPU jobs waiting (dependency/held not counted)",
          "2 GPU" in out and "0 CPU" in out, out)
    check("queue: share applies while others wait", "share applies" in out, out)
    check("queue: GPUs contested -> no separate GPU smoke, the first real job checks the GPU",
          "no separate GPU smoke" in out and "no GPU free" in out and "first minutes" in out, out)
    (proj.parent / "squeue.txt").write_text("1001|vaha|R|cpu|N/A|4|None|18:33:11|\n")
    (proj.parent / "node.txt").write_text(SCONTROL_NODE.replace("gres/gpu=4\n", "gres/gpu=0\n"))
    r2 = run(proj, env, "queue")
    check("queue: no GPU job running -> all free now", "GPUs free up   4 free now" in r2.stdout, r2.stdout + r2.stderr)
    check("queue: a GPU free, nobody waiting -> a separate GPU smoke is fine",
          "GPU smoke" in r2.stdout and "starts now" in r2.stdout, r2.stdout + r2.stderr)
    (proj.parent / "squeue.txt").write_text("1001|vaha|R|cpu|N/A|4|None|18:33:11|\n"
                                            "1010|ving|PD|main|gres/gpu:1|1|Priority|1-00:00:00|\n")
    r3 = run(proj, env, "queue")
    check("queue: a GPU free but another user waits for one -> still no separate GPU smoke",
          "no separate GPU smoke" in r3.stdout and "1 GPU job of other users waiting" in r3.stdout, r3.stdout + r3.stderr)
    check("queue changes nothing", not (proj.parent / "scontrol.log").exists() and not (proj.parent / "sbatch.log").exists(),
          out)

    # ------------------------------------------------- size: scaling from two widths of the same config
    proj, env = setup()
    add_run(proj, "pilot", "h1", "DONE", [dict(req_cpus=4, elapsed_s=4 * 3600, total_cpu_s=3.9 * 4 * 3600,
                                               max_rss_mb=6000)])
    add_run(proj, "pilot", "h1", "DONE", [dict(req_cpus=16, elapsed_s=int(1.2 * 3600), total_cpu_s=14 * 1.2 * 3600,
                                               max_rss_mb=9000)])
    r = run(proj, env, "size", "--tag", "pilot")
    out = r.stdout + r.stderr
    check("size scaling runs", r.returncode == 0, out)
    check("size scaling: speed-up and efficiency printed", "3.3" in out and "83 %" in out, out)
    check("size scaling: picks the efficient wider width", "--cpus 16" in out.split("flags:")[-1], out)
    check("size scaling: time from the chosen width (1.2 h x 1.3 -> 01:45:00)",
          "--time 01:45:00" in out.split("flags:")[-1], out)

    # ---------------------------------------- size: poor scaling keeps the narrow width
    proj, env = setup()
    add_run(proj, "pilot", "h1", "DONE", [dict(req_cpus=4, elapsed_s=4 * 3600, total_cpu_s=3.9 * 4 * 3600,
                                               max_rss_mb=6000)])
    add_run(proj, "pilot", "h1", "DONE", [dict(req_cpus=16, elapsed_s=3 * 3600, total_cpu_s=6 * 3 * 3600,
                                               max_rss_mb=6000)])
    r = run(proj, env, "size", "--tag", "pilot")
    out = r.stdout + r.stderr
    check("size poor scaling: stays at --cpus 4", "--cpus 4" in out.split("flags:")[-1], out)

    # ---------------------------------------- size: GPU job, 2 -> 8 CPUs 20 % faster: wider wins (GPU pays for CPUs)
    proj, env = setup()
    add_run(proj, "pilot", "h1", "DONE", [dict(req_cpus=2, req_gpus=1, elapsed_s=6000, total_cpu_s=1.9 * 6000,
                                               max_rss_mb=8000, gpu_mem_mb=3000, gpu_util=40.0)])
    add_run(proj, "pilot", "h1", "DONE", [dict(req_cpus=8, req_gpus=1, elapsed_s=5000, total_cpu_s=6.0 * 5000,
                                               max_rss_mb=9000, gpu_mem_mb=3000, gpu_util=55.0)])
    r = run(proj, env, "size", "--tag", "pilot")
    out = r.stdout + r.stderr
    check("size gpu scaling: 20 % faster at 8 CPUs -> --cpus 8", "--cpus 8" in out.split("flags:")[-1], out)
    proj, env = setup()
    add_run(proj, "pilot", "h1", "DONE", [dict(req_cpus=2, req_gpus=1, elapsed_s=6000, total_cpu_s=1.9 * 6000,
                                               max_rss_mb=8000, gpu_mem_mb=3000, gpu_util=60.0)])
    add_run(proj, "pilot", "h1", "DONE", [dict(req_cpus=8, req_gpus=1, elapsed_s=5800, total_cpu_s=2.5 * 5800,
                                               max_rss_mb=8000, gpu_mem_mb=3000, gpu_util=62.0)])
    r = run(proj, env, "size", "--tag", "pilot")
    out = r.stdout + r.stderr
    check("size gpu scaling: 3 % faster at 8 CPUs -> stays at --cpus 2", "--cpus 2" in out.split("flags:")[-1], out)

    # ---------------------------------------- size: saturated single pilot -> measure a wider one
    proj, env = setup()
    add_run(proj, "pilot", "h1", "DONE", [dict(req_cpus=2, elapsed_s=3 * 3600, total_cpu_s=1.97 * 3 * 3600,
                                               max_rss_mb=4000)])
    r = run(proj, env, "size", "--tag", "pilot")
    out = r.stdout + r.stderr
    check("size saturated: suggests a wider pilot", "all 2 CPUs" in out and "allow-duplicate" in out, out)

    # ---------------------------------------- size: memory bills like many CPUs
    proj, env = setup()
    add_run(proj, "pilot", "h1", "DONE", [dict(req_cpus=4, elapsed_s=3 * 3600, total_cpu_s=3.9 * 3 * 3600,
                                               max_rss_mb=100 * 1024)])
    r = run(proj, env, "size", "--tag", "pilot")
    out = r.stdout + r.stderr
    check("size memory: --mem 130G bills like 34 CPUs", "--mem 130G" in out and "34 CPUs" in out, out)

    # ---------------------------------------- size: GPU job starved by its CPUs
    proj, env = setup()
    add_run(proj, "pilot", "h1", "DONE", [dict(req_cpus=1, req_gpus=1, elapsed_s=2 * 3600,
                                               total_cpu_s=0.99 * 2 * 3600, max_rss_mb=8000,
                                               gpu_mem_mb=3000, gpu_util=22.0)])
    r = run(proj, env, "size", "--tag", "pilot")
    out = r.stdout + r.stderr
    check("size gpu: data loading note when CPUs are saturated and the GPU is underused",
          "41 CPUs" in out and "workers" in out, out)

    # ---------------------------------------- size: very short runs -> bundle
    proj, env = setup()
    add_run(proj, "pilot", "h1", "DONE", [dict(req_cpus=1, elapsed_s=180, total_cpu_s=170, max_rss_mb=500)])
    r = run(proj, env, "size", "--tag", "pilot")
    out = r.stdout + r.stderr
    check("size short: suggests bundling units", "bundle" in out and "3 min" in out, out)

    # ---------------------------------------- submit --after-tag
    proj, env = setup()
    up1 = add_run(proj, "predict", None, "SUBMITTED", [dict(req_cpus=4, state="RUNNING", jid="701"),
                                                       dict(req_cpus=4, state="PENDING", jid="702")])
    up2 = add_run(proj, "predict", None, "SUBMITTED", [dict(req_cpus=4, state="PENDING", jid="703")])
    add_run(proj, "predict", None, "DONE", [dict(req_cpus=4, state="COMPLETED", jid="690", elapsed_s=100)])
    down = add_run(proj, "optimize", None, "NEW", [])
    r = run(proj, env, "submit", down, "--script", "job.sbatch", "--time", "01:00:00", "--after-tag", "predict")
    out = r.stdout + r.stderr
    log = (proj.parent / "sbatch.log").read_text() if (proj.parent / "sbatch.log").exists() else ""
    check("submit --after-tag runs", r.returncode == 0, out)
    check("submit --after-tag: waits on the last queued job of every run of the tag",
          "--dependency=afterany:702:703" in log or "--dependency=afterany:703:702" in log, log + out)

    # ---------------------------------------- submit: many jobs -> warning
    proj, env = setup()
    ids = []
    conn = sqlite3.connect(proj / "runs" / "registry.db")
    for i in range(260):
        rid = f"20261105-abcd-many-{i:04x}"
        conn.execute("INSERT INTO runs (run_id, user, project, name, tag, status, run_dir, created_at, updated_at) "
                     "VALUES (?, 'abcd', 'proj', 'many', 'many', 'NEW', ?, 't', 't')", (rid, str(proj / 'runs' / rid)))
        ids.append(rid)
    conn.commit()
    r = subprocess.run([sys.executable, str(D3RUN), "submit", "-", "--script", "job.sbatch", "--time", "01:00:00",
                        "--segments", "2", "--dry-run"], cwd=proj, env=env, capture_output=True, text=True,
                       input="\n".join(ids))
    out = r.stdout + r.stderr
    check("submit: 520 jobs -> job-count warning", "520" in out and "bundle" in out, out[-1500:])

    # ---------------------------------------- submit: no separate GPU smoke job while the GPUs are contested
    proj, env = setup()                                      # the snapshot: 4 of 4 GPUs busy, ving waits for one
    log = proj.parent / "sbatch.log"
    smoke = add_run(proj, "smoke", None, "NEW", [])
    real = add_run(proj, "r1-train", None, "NEW", [])
    r = run(proj, env, "submit", smoke, "--script", "job.sbatch", "--time", "00:10:00", "--gpus", "1")
    check("submit: GPU smoke refused while no GPU is free and others wait",
          r.returncode != 0 and "first minutes" in r.stderr and "--allow-gpu-smoke" in r.stderr and not log.exists(),
          r.stdout + r.stderr)
    r = run(proj, env, "submit", smoke, "--script", "job.sbatch", "--time", "00:10:00")
    check("submit: the CPU smoke goes through", r.returncode == 0 and log.exists(), r.stdout + r.stderr)
    r = run(proj, env, "submit", real, "--script", "job.sbatch", "--time", "04:00:00", "--gpus", "1")
    check("submit: the first real GPU job goes through", r.returncode == 0 and "--gres=gpu:1" in log.read_text(),
          r.stdout + r.stderr)
    smoke2 = add_run(proj, "smoke", None, "NEW", [])
    r = run(proj, env, "submit", smoke2, "--script", "job.sbatch", "--time", "00:10:00", "--gpus", "1",
            "--allow-gpu-smoke")
    check("submit: --allow-gpu-smoke submits it anyway", r.returncode == 0, r.stdout + r.stderr)
    (proj.parent / "squeue.txt").write_text("1001|vaha|R|cpu|N/A|4|None|18:33:11|\n")
    (proj.parent / "node.txt").write_text(SCONTROL_NODE.replace("gres/gpu=4\n", "gres/gpu=0\n"))
    smoke3 = add_run(proj, "smoke", None, "NEW", [])
    r = run(proj, env, "submit", smoke3, "--script", "job.sbatch", "--time", "00:10:00", "--gpus", "1")
    check("submit: GPU smoke allowed when a GPU is free and nobody waits", r.returncode == 0, r.stdout + r.stderr)

    # ---------------------------------------- scale: local width measurement when the server has no room
    work = Path(tempfile.mkdtemp())
    (work / "pool.py").write_text(textwrap.dedent('''\
        import os, sys, time
        from concurrent.futures import ProcessPoolExecutor
        from pathlib import Path
        d = Path(os.environ.get("D3RUN_LOCAL_DIR", "runs/local"))
        if (d / "done").exists():          # a resumed run that is already done exits at once
            sys.exit(0)
        def unit(_):
            t = time.process_time()
            while time.process_time() - t < 0.4:
                pass
        if __name__ == "__main__":
            with ProcessPoolExecutor(int(os.environ["SLURM_CPUS_PER_TASK"])) as ex:
                list(ex.map(unit, range(8)))
            d.mkdir(parents=True, exist_ok=True)
            (d / "done").write_text("1")
        '''))
    env_local = {k: v for k, v in os.environ.items() if not k.startswith(("SLURM_", "D3RUN_"))}
    r = subprocess.run([sys.executable, str(D3RUN), "scale", "--widths", "1", "2", "4", "--", sys.executable, "pool.py"],
                       cwd=work, env=env_local, capture_output=True, text=True)
    out = r.stdout + r.stderr
    check("scale runs", r.returncode == 0, out)
    rows = [l for l in out.splitlines() if l.split()[:1] in (["1"], ["2"], ["4"])]
    check("scale: one row per width", len(rows) == 3, out)
    t2 = float(rows[1].split()[1]) if len(rows) == 3 else 0
    check("scale: every width starts fresh (width 2 did the work, ~1.6 s)", t2 > 1.0, out)
    check("scale: suggests the widest efficient width", "--cpus 4" in out, out)
    check("scale: peak memory reported", "GB" in out, out)
    check("scale: warns that a 3 s slice is short", "short" in out, out)
    check("scale: the project's runs/local is untouched", not (work / "runs" / "local" / "done").exists(), out)
    proj, env = setup()                       # PATH has a fake sbatch: this is the cluster
    r = run(proj, env, "scale", "--", sys.executable, "-c", "pass")
    check("scale: refuses on the cluster", r.returncode != 0 and "own computer" in r.stderr, r.stdout + r.stderr)

    print(f"\n{len(FAILS)} failed")
    sys.exit(1 if FAILS else 0)


if __name__ == "__main__":
    main()
