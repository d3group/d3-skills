"""Tests for check_sbatch.py: help, a clean template, a job above 24 h.

Run on the laptop: python3 evals/tests/test_check_sbatch.py [path to check_sbatch.py]
"""
import subprocess
import sys
import tempfile
import textwrap
from pathlib import Path

SKILL = Path(__file__).resolve().parents[2]
LINT = (Path(sys.argv[1]) if len(sys.argv) > 1 else SKILL / "scripts" / "check_sbatch.py").resolve()
FAILS = []


def check(name, cond, out=""):
    print(("ok   " if cond else "FAIL ") + name)
    if not cond:
        FAILS.append(name)
        print(textwrap.indent(out, "     | "))


def lint(*args):
    r = subprocess.run([sys.executable, str(LINT), *args], capture_output=True, text=True)
    return r.returncode, r.stdout + r.stderr


def main():
    for flag in ("--help", "-h"):
        code, out = lint(flag)
        check(f"{flag}: usage, exit 0, no traceback", code == 0 and "Traceback" not in out and "check_sbatch" in out, out)
    code, out = lint(str(SKILL / "assets" / "job_template.sbatch"))
    check("the job template passes", code == 0, out)
    bad = Path(tempfile.mkdtemp()) / "long.sbatch"
    bad.write_text("#!/bin/bash\n#SBATCH --time=48:00:00\nuv run --no-sync python src/train.py\n")
    code, out = lint(str(bad))
    check("a 48 h job fails", code == 1, out)
    print(f"\n{len(FAILS)} failed")
    sys.exit(1 if FAILS else 0)


if __name__ == "__main__":
    main()
