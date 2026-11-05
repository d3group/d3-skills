#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""Check Slurm batch scripts against the KiRegio server rules. Stdlib only.

    uv run <skill-dir>/scripts/check_sbatch.py jobs/train.sbatch [more scripts]

Prints `file:line: ERROR|WARN: message` and exits 1 if any ERROR was found. Errors are things the
server rejects or that lose work (time above 24 h, wrong partition for the GPU request, #SBATCH lines
Slurm ignores, pip/conda, secrets); warnings are habits that slow the queue or hurt other users.
"""
from __future__ import annotations

import re
import shlex
import sys
from pathlib import Path

MAX_S = 24 * 3600
LONG_S = 20 * 3600


def parse_time(text: str) -> int | None:
    try:
        if "-" in text:
            d, rest = text.split("-", 1)
            p = [int(x) for x in rest.split(":")] + [0, 0]
            return ((int(d) * 24 + p[0]) * 60 + p[1]) * 60 + p[2]
        p = [int(x) for x in text.split(":")]
    except ValueError:
        return None
    if len(p) == 1:
        return p[0] * 60
    if len(p) == 2:
        return p[0] * 60 + p[1]
    return (p[0] * 60 + p[1]) * 60 + p[2]


def directives(lines: list[str]):
    """(line number, option, value) for each #SBATCH line Slurm reads, plus ignored ones."""
    read, ignored, in_header = [], [], True
    for n, line in enumerate(lines, 1):
        s = line.strip()
        if n == 1 and s.startswith("#!"):
            continue
        if s.startswith("#SBATCH"):
            body = s[len("#SBATCH"):]
            try:
                tokens = shlex.split(body, comments=True)
            except ValueError:
                tokens = body.split()
            opts = []
            i = 0
            while i < len(tokens):
                t = tokens[i]
                if t.startswith("--") and "=" in t:
                    k, v = t.split("=", 1)
                    opts.append((k, v))
                elif t.startswith("-") and i + 1 < len(tokens) and not tokens[i + 1].startswith("-"):
                    opts.append((t, tokens[i + 1]))
                    i += 1
                else:
                    opts.append((t, ""))
                i += 1
            (read if in_header else ignored).extend((n, k, v) for k, v in opts)
        elif s and not s.startswith("#"):
            in_header = False
    return read, ignored


ALIASES = {"-t": "--time", "-p": "--partition", "-c": "--cpus-per-task", "-G": "--gpus", "-o": "--output",
           "-e": "--error", "-J": "--job-name"}


def check(path: Path) -> int:
    lines = path.read_text().splitlines()
    read, ignored = directives(lines)
    opts: dict[str, tuple[int, str]] = {}
    for n, k, v in read:
        opts[ALIASES.get(k, k)] = (n, v)
    errors = 0

    def report(n: int, level: str, msg: str) -> None:
        nonlocal errors
        errors += level == "ERROR"
        print(f"{path}:{n}: {level}: {msg}")

    for n, k, _ in ignored:
        report(n, "ERROR", f"#SBATCH {k} comes after the first command; Slurm ignores it. Move it up")

    gpus = 0
    for key in ("--gres", "--gpus", "--gpus-per-node", "--gpus-per-task"):
        if key in opts:
            m = re.search(r"(\d+)\s*$", opts[key][1])
            gpus = max(gpus, int(m.group(1)) if m else 1)

    if "--time" not in opts:
        report(1, "ERROR", "no --time: the default is the 24 h maximum, which keeps the job out of backfill. "
                           "Set a realistic limit (d3run.py size suggests one)")
    else:
        n, v = opts["--time"]
        t = parse_time(v)
        if t is None:
            report(n, "ERROR", f"cannot read --time={v}")
        elif t > MAX_S:
            report(n, "ERROR", f"--time={v} is above 24:00:00: the job is accepted but never starts. "
                               "Checkpoint and split it into segments")
        elif t > LONG_S:
            report(n, "WARN", f"--time={v}: above 20 h; shorter segments start earlier and lose less on a crash")

    if "--partition" in opts:
        n, v = opts["--partition"]
        if v == "main" and not gpus:
            report(n, "ERROR", "--partition=main without a GPU is rejected by the submit filter")
        elif v == "cpu" and gpus:
            report(n, "ERROR", "--partition=cpu with a GPU is rejected by the submit filter")
        else:
            report(n, "WARN", "--partition is not needed: GPU jobs go to main and CPU-only jobs to cpu by themselves")
    if gpus > 1:
        report(opts.get("--gres", opts.get("--gpus", (1, "")))[0], "WARN",
               f"{gpus} GPUs: the group shares 4. Ask for more than one only if the code uses them all")
    if "--mem" not in opts and "--mem-per-cpu" not in opts:
        report(1, "WARN", "no --mem: CPU jobs get 2 GB per CPU, GPU jobs without --cpus-per-task 64 GB per GPU. "
                          "Set what the job needs")
    for key in ("--output", "--error"):
        if key not in opts:
            report(1, "WARN", f"no {key}: logs land in slurm-<jobid>.out in the submit folder")
        else:
            n, v = opts[key]
            folder = Path(v).parent
            if "%" not in str(folder) and not folder.exists():
                report(n, "WARN", f"{key} folder '{folder}' does not exist (relative to where you run sbatch); "
                                  "Slurm does not create it and the job fails without a log. Create it, or submit "
                                  "with d3run, which writes logs into the run folder")
    if "--signal" not in opts:
        report(1, "WARN", "no --signal: the job gets no warning before the limit. Checkpoint on a timer, or add "
                          "--signal=B:USR1@600 with a trap (assets/job_template.sbatch)")

    text = "\n".join(lines)
    body = [(n, l) for n, l in enumerate(lines, 1) if l.strip() and not l.strip().startswith("#")]
    no_sync = "UV_NO_SYNC=1" in text
    for n, line in body:
        s = line.strip()
        if re.search(r"(^|[\s;&|])(pip3?|python3? -m pip)\s+install\b", s) or re.search(r"\buv pip install\b", s):
            report(n, "ERROR", "pip install in a job: add dependencies with `uv add` on the login host, "
                               "`uv sync` once, then `uv run` in the job")
        if re.search(r"(^|[\s;&|])(conda|mamba|micromamba)\s", s) or re.search(r"python3? -m venv|virtualenv\b", s):
            report(n, "ERROR", "conda/venv in a job: the group uses uv (`uv sync`, then `uv run`)")
        if re.search(r"source\s+\S*\.venv/bin/activate", s):
            report(n, "WARN", "activating .venv by hand: use `uv run --no-sync python ...` instead")
        if re.match(r"(srun\s+)?(python3?|ipython)\s", s) and "uv run" not in s:
            report(n, "WARN", "bare python: use `uv run --no-sync python ...` so the project's environment is used")
        if "uv run" in s and "--no-sync" not in s and not no_sync and "--script" not in s:
            report(n, "WARN", "`uv run` without --no-sync: every job syncs the shared .venv at the same time. "
                              "Run `uv sync` once on the login host, then `uv run --no-sync` in jobs")
        if re.match(r"ssh\s", s) or " ssh " in s:
            report(n, "WARN", "ssh inside a job: the compute node is reached only through Slurm")
        if re.search(r"(AWS_SECRET_ACCESS_KEY|AWS_ACCESS_KEY_ID|PASSWORD|TOKEN)\s*=\s*['\"]?[A-Za-z0-9/+]{8,}", s,
                     re.IGNORECASE):
            report(n, "ERROR", "a secret is written into the script: keep keys in ~/.aws/credentials (chmod 600) "
                               "or the environment, never in files in the repo")
    return errors


def main() -> None:
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(2)
    if sys.argv[1] in ("-h", "--help"):
        print(__doc__)
        sys.exit(0)
    total = 0
    for arg in sys.argv[1:]:
        total += check(Path(arg))
    sys.exit(1 if total else 0)


if __name__ == "__main__":
    main()
