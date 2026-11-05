"""Post new plugin versions of this marketplace to Slack (#d3_skills), tagging the channel.

Compares the plugin versions in .claude-plugin/marketplace.json between two commits and sends one message for all
plugins whose version changed or that are new, with the commits that touched each plugin's skill folder.
Run by .github/workflows/slack-plugin-updates.yml; the webhook comes from the secret SLACK_WEBHOOK_URL.

    python3 .github/scripts/slack_plugin_updates.py <before> <after> [--dry-run]

--dry-run prints the message instead of posting it. Without SLACK_WEBHOOK_URL it warns and posts nothing.
Standard library only.
"""
import json
import os
import re
import subprocess
import sys
import urllib.request

MARKET = ".claude-plugin/marketplace.json"
MAX_COMMITS = 10


def git(*args, check=True):
    r = subprocess.run(["git", *args], capture_output=True, text=True)
    if check and r.returncode != 0:
        sys.exit(f"git {' '.join(args)} failed: {r.stderr.strip()}")
    return r


def plugins_at(rev):
    r = git("show", f"{rev}:{MARKET}", check=False)
    if r.returncode != 0:
        return {}
    return {p["name"]: p for p in json.loads(r.stdout).get("plugins", [])}


def base_commit(before, after):
    """`before` from the push event; a first push (zeros) or a force push (commit not here) uses after's parent."""
    if before and set(before) != {"0"} and git("cat-file", "-e", f"{before}^{{commit}}", check=False).returncode == 0:
        return before
    r = git("rev-parse", "--verify", "--quiet", f"{after}^", check=False)
    return r.stdout.strip() if r.returncode == 0 else None


def commit_lines(base, after, plugin):
    paths = [p.removeprefix("./") for p in plugin.get("skills", [])] or ["."]
    rng = f"{base}..{after}" if base else after
    log = git("log", "--no-merges", "--format=%H%x09%s", rng, "--", *paths).stdout.splitlines()
    repo = f"{os.environ.get('GITHUB_SERVER_URL', 'https://github.com')}/" \
           f"{os.environ.get('GITHUB_REPOSITORY', 'd3group/d3-skills')}"
    prefix = re.compile(rf"^{re.escape(plugin['name'])} [0-9][0-9A-Za-z.+-]*: ")
    lines = []
    for entry in log[:MAX_COMMITS]:
        sha, subject = entry.split("\t", 1)
        lines.append(f"• {prefix.sub('', subject)} (<{repo}/commit/{sha}|{sha[:7]}>)")
    if len(log) > MAX_COMMITS:
        lines.append(f"• ... and {len(log) - MAX_COMMITS} more")
    return lines


def message(before, after):
    base = base_commit(before, after)
    old, new = plugins_at(base) if base else {}, plugins_at(after)
    blocks = []
    for name, p in new.items():
        was = old.get(name, {}).get("version")
        if was == p.get("version"):
            continue
        if was is None:
            head = f"*{name}* {p.get('version')} (new)"
            how = f"Install: `/plugin install {name} --marketplace d3group/d3-skills`"
        else:
            head = f"*{name}* {was} → {p.get('version')}"
            how = (f"Update: `claude plugin marketplace update d3-skills && claude plugin update {name}@d3-skills`, "
                   "then restart Claude Code")
        blocks.append("\n".join([head, *commit_lines(base, after, p), how]))
    if not blocks:
        return None
    return "<!channel> New in the d3-skills marketplace:\n\n" + "\n\n".join(blocks)


def main():
    args = [a for a in sys.argv[1:] if a != "--dry-run"]
    if len(args) != 2:
        sys.exit(__doc__)
    text = message(*args)
    if text is None:
        print("No plugin version changed; nothing to post.")
        return
    if "--dry-run" in sys.argv:
        print(text)
        return
    url = os.environ.get("SLACK_WEBHOOK_URL", "")
    if not url:
        print("::warning::SLACK_WEBHOOK_URL is not set; nothing posted. Message:\n" + text)
        return
    req = urllib.request.Request(url, data=json.dumps({"text": text, "unfurl_links": False}).encode(),
                                 headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            print(f"Posted to Slack: HTTP {r.status}")
    except OSError as e:
        sys.exit(f"Posting to Slack failed: {e}")


if __name__ == "__main__":
    main()
