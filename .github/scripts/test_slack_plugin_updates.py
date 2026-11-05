"""Tests for slack_plugin_updates.py: which plugins changed between two commits and the Slack text for them.

Builds a throwaway git repository with a marketplace.json; nothing is posted (--dry-run prints the message).
Run: python3 .github/scripts/test_slack_plugin_updates.py
"""
import json
import os
import subprocess
import sys
import tempfile
import textwrap
from pathlib import Path

SCRIPT = Path(__file__).resolve().parent / "slack_plugin_updates.py"
FAILS = []


def check(name, cond, out=""):
    print(("ok   " if cond else "FAIL ") + name)
    if not cond:
        FAILS.append(name)
        print(textwrap.indent(out, "     | "))


def git(repo, *args):
    return subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True, check=True).stdout.strip()


def commit(repo, subject, plugins, touch=None):
    """Write marketplace.json with {name: version}, optionally change a file in a skill folder, commit."""
    market = {"name": "d3-skills", "version": "1.0.0", "plugins": [
        {"name": n, "version": v, "description": f"{n} does things", "source": "./", "skills": [f"./skills/{n}"]}
        for n, v in plugins.items()]}
    (repo / ".claude-plugin").mkdir(exist_ok=True)
    (repo / ".claude-plugin" / "marketplace.json").write_text(json.dumps(market, indent=2) + "\n")
    if touch:
        f = repo / "skills" / touch / "SKILL.md"
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text(f.read_text() + subject + "\n" if f.exists() else subject + "\n")
    readme = repo / "README.md"
    readme.write_text((readme.read_text() if readme.exists() else "") + subject + "\n")
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", subject)
    return git(repo, "rev-parse", "HEAD")


def run(repo, *args, webhook=None):
    env = {k: v for k, v in os.environ.items() if k != "SLACK_WEBHOOK_URL"}
    if webhook is not None:
        env["SLACK_WEBHOOK_URL"] = webhook
    r = subprocess.run([sys.executable, str(SCRIPT), *args], capture_output=True, text=True, cwd=repo, env=env)
    return r.returncode, r.stdout + r.stderr


def main():
    repo = Path(tempfile.mkdtemp())
    git(repo, "init", "-q", "-b", "main")
    git(repo, "config", "user.email", "t@example.org")
    git(repo, "config", "user.name", "Test")
    c1 = commit(repo, "start", {"a": "1.0.0", "b": "0.1.0"}, touch="a")
    commit(repo, "a 1.0.1: fix the thing", {"a": "1.0.1", "b": "0.1.0"}, touch="a")
    commit(repo, "a 1.1.0: a new step", {"a": "1.1.0", "b": "0.1.0"}, touch="a")
    c4 = commit(repo, "c 0.1.0: first version", {"a": "1.1.0", "b": "0.1.0", "c": "0.1.0"}, touch="c")

    code, out = run(repo, c1, c4, "--dry-run")
    check("dry run exits 0", code == 0, out)
    check("tags the channel", out.startswith("<!channel>"), out)
    check("names the changed plugin with old and new version", "*a* 1.0.0 → 1.1.0" in out, out)
    check("lists each commit of that plugin, version prefix removed",
          "fix the thing" in out and "a new step" in out and "a 1.0.1:" not in out, out)
    check("links the commits", "/commit/" in out, out)
    check("tells how to update", "claude plugin update a@d3-skills" in out, out)
    check("announces a new plugin with its install line",
          "*c* 0.1.0 (new)" in out and "/plugin install c --marketplace d3group/d3-skills" in out, out)
    check("leaves an unchanged plugin out", "*b*" not in out, out)

    c5 = commit(repo, "readme only", {"a": "1.1.0", "b": "0.1.0", "c": "0.1.0"})
    code, out = run(repo, c4, c5, "--dry-run")
    check("no version change: nothing to post, exit 0", code == 0 and "<!channel>" not in out, out)

    c6 = commit(repo, "b 0.2.0: more", {"a": "1.1.0", "b": "0.2.0", "c": "0.1.0"}, touch="b")
    code, out = run(repo, "0" * 40, c6, "--dry-run")
    check("first push (before = zeros): compares with the parent", code == 0 and "*b* 0.1.0 → 0.2.0" in out
          and "*a*" not in out, out)
    code, out = run(repo, "deadbeef" * 5, c6, "--dry-run")
    check("unknown before (force push): compares with the parent", code == 0 and "*b* 0.1.0 → 0.2.0" in out, out)

    code, out = run(repo, c5, c6)
    check("no webhook set: warns, posts nothing, exit 0", code == 0 and "SLACK_WEBHOOK_URL" in out, out)
    code, out = run(repo, c5, c6, webhook="http://127.0.0.1:9/never")
    check("webhook unreachable: exit 1", code == 1, out)

    print(f"\n{len(FAILS)} failed")
    sys.exit(1 if FAILS else 0)


if __name__ == "__main__":
    main()
