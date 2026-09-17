# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Scaffold (or refresh) an explainer project inside a research repository.

    uv run ~/.claude/skills/d3-explainer/scripts/init.py                     # creates ./explainer in the current repo
    uv run ~/.claude/skills/d3-explainer/scripts/init.py path/to/explainer --name my_project
    uv run ~/.claude/skills/d3-explainer/scripts/init.py path/to/explainer --refresh   # only replace d3x/ with the skill's current engine

Creates: explainer.toml (prefilled from the repository), brief.md (the content brief to get approved), sections/, figures/,
data/, review/, and d3x/ (the engine: build.py, check.py, stylesheet, runtime, KaTeX, fonts). The folder is self-contained:
a co-author can rebuild with `uv run d3x/build.py` without the skill installed.
"""
from __future__ import annotations

import argparse
import re
import shutil
import sys
from pathlib import Path

SKILL = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))

BRIEF = """# Content brief: {title}

Status: DRAFT, not yet approved by the author.

## 0. Run settings and decisions
- Scope: <whole project | the part the user named>
- Depth: {depth}.  Review: {review}.
- Input tier: <A to E>.  Paper used: <folder>.  Enrichment: <skipped | recall | notebooklm | both>.
- Save location: <path>
- Decided without asking the author (and why): <none | list; an autonomous or batch run records every such decision here>

## 1. The project in two sentences
<what question the project answers, and the answer>

## 2. Reader and purpose
The author and co-authors. After reading they should be able to: <2 to 4 concrete abilities, e.g. "re-derive Eq. (7) and say which assumption each step uses">

## 3. Sources read (and deliberately not read)
| Source | Read | Used for |
|---|---|---|
| paper/... | yes | ... |

## 4. The research gap
- What prior work established: ...
- Where it stops: ...
- What this project adds: ...
- Evidence for the gap statement: <paper section, bib entries, vault note; or "my reading">

## 5. Section plan
| # | Section (title states the message) | Core content | Interactive figure: knob -> insight | Sources |
|---|---|---|---|---|
| 01 | ... | ... | ... | ... |

## 6. Derivations to include
| Derivation | Steps | Why the reader needs it | Source |
|---|---|---|---|

## 7. Open points the explainer will state honestly
- Paper and code disagree on: ...
- Assumptions that carry the result: ...
- Open questions: ...

## 8. Left out on purpose
- ...
"""

TOML = """name        = "{name}"
title       = "{title}"
title_html  = ""                  # optional: the hero title with one accented word, e.g. "How long to look before you <em>leap</em>"
eyebrow     = "project explainer · for the authors"
subtitle    = ""                  # the lede: what the page builds up and what the reader can do afterwards
authors     = []
status      = ""                  # e.g. "Working draft, model v3" (shown in the header)
depth       = "{depth}"          # focus | overview | standard | deep: sets the word and figure budget the build reports against
repo        = "{repo}"            # repository root: relative to this folder, or an absolute path
paper       = {paper}             # folders with the paper's .tex / .aux, relative to repo
macros_from = {macros}            # .tex files whose \\newcommand definitions become KaTeX macros
{vault}
code_links  = "auto"              # auto (GitHub permalinks when origin is on GitHub) | github | vscode | none

# The project's colour code (two to five roles): a colour name in plots, a macro \\key{{...}} in formulas, a legend entry in the hero.
# [[role]]
# key = "choice"
# color = "#F29100"               # D3 palette: #153F87 navy, #F29100 orange, #4D9AAA teal, #808080 gray
# label = "what we choose"

# [hero]
# equation = "eq:main"            # the project's central equation, pulled from the paper; or tex = "..." with the role macros
# note = "Every symbol in that line is defined below."

# [hud]                           # optional assembling panel; sections then carry data-hud="1", "2", ...
# title = "the equation, assembling"
# lines = ["...", "..."]

[macros]                          # extra KaTeX macros, e.g. "\\\\E" = "\\\\mathbb{{E}}"
"""


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("target", nargs="?", default="explainer")
    ap.add_argument("--name", help="output file stem (default: repository folder name)")
    ap.add_argument("--repo", default=None, help="repository root (default: parent of the target folder)")
    ap.add_argument("--refresh", action="store_true", help="only replace d3x/ with the skill's current engine")
    ap.add_argument("--depth", default="standard", choices=["focus", "overview", "standard", "deep"], help="from Step 0; sets the budget the build reports against")
    ap.add_argument("--review", default="standard", choices=["light", "single", "standard", "full"], help="from Step 0; recorded in brief.md")
    ap.add_argument("--paper", default=None, help="paper folder relative to the repo, when the repo holds several papers")
    a = ap.parse_args()
    target = Path(a.target).resolve()
    repo = Path(a.repo).resolve() if a.repo else target.parent
    engine = target / "d3x"
    if engine.exists():
        shutil.rmtree(engine)
    shutil.copytree(SKILL / "assets" / "d3x", engine, ignore=shutil.ignore_patterns("__pycache__", ".DS_Store"))
    if a.refresh:
        print(f"refreshed {engine}")
        return 0
    if (target / "explainer.toml").exists():
        print(f"{target / 'explainer.toml'} exists: engine refreshed, content left untouched")
        return 0
    for d in ("sections", "figures", "data", "review"):
        (target / d).mkdir(parents=True, exist_ok=True)

    import scan  # noqa: E402  (sibling script)
    files = list(scan.walk(repo))
    title, paper_dirs, macro_files = repo.name, [], []
    for f in sorted((p for p in files if p.suffix == ".tex"), key=lambda p: len(str(p))):
        t = scan.read(f, 300_000)
        if "\\documentclass" in t and "\\begin{abstract}" in t and "beamer" not in t[:600]:
            m = re.search(r"\\title(?:\[[^\]]*\])?\{((?:[^{}]|\{[^{}]*\})*)\}", t)
            if m and title == repo.name:
                title = scan.tex_clean(m.group(1))[:140]
            rel = str(f.parent.relative_to(repo))
            if rel not in paper_dirs and not re.search(r"template|guideline|poster|talk|slides|presentation", rel, re.I):
                paper_dirs.append(rel)
    candidates = list(paper_dirs)
    if a.paper:
        paper_dirs = [a.paper]
        title = repo.name
        for f in sorted((repo / a.paper).glob("*.tex")):
            m = re.search(r"\\title(?:\[[^\]]*\])?\{((?:[^{}]|\{[^{}]*\})*)\}", scan.read(f, 300_000))
            if m:
                title = scan.tex_clean(m.group(1))[:140]
                break
    else:
        paper_dirs = paper_dirs[:1]
    for d in paper_dirs[:2]:
        for f in sorted((repo / d).rglob("*.tex")):
            if len(re.findall(r"\\(?:re)?newcommand|\\DeclareMathOperator", scan.read(f, 200_000))) >= 3 and not re.search(r"template|guideline", str(f), re.I):
                macro_files.append(str(f.relative_to(repo)))
    vaults = [d.name for d in repo.iterdir() if d.is_dir() and ((d / ".obsidian").exists() or re.search(r"vault", d.name, re.I))]
    name = a.name or re.sub(r"[^a-z0-9]+", "_", repo.name.lower()).strip("_")
    fmt = lambda xs: "[" + ", ".join('"%s"' % x for x in xs) + "]"
    rel_repo = Path(*[".."] * len(target.relative_to(repo).parts)) if repo in target.parents else repo
    short = title.replace('"', "'")
    if len(short) > 48:                       # a title's first clause is a better short form than its first 48 characters
        short = re.split(r"\s*[:\u2013\u2014]\s+|\.\s", short)[0]
    if len(short) > 48:
        short = short[:48].rsplit(" ", 1)[0]
    (target / "explainer.toml").write_text(TOML.format(
        name=name, title=title.replace('"', "'"), depth=a.depth, repo=str(rel_repo), paper=fmt(paper_dirs[:3]), macros=fmt(macro_files[:3]),
        vault=('vault       = "%s"' % vaults[0]) if vaults else '# vault     = "Vault - Project"   # Obsidian vault inside the repo, enables [[vault:Note]] chips'), encoding="utf-8")
    (target / "brief.md").write_text(BRIEF.format(title=title, depth=a.depth, review=a.review), encoding="utf-8")
    (target / ".gitignore").write_text("review/\nfigures/.cache/\nscan.md\n", encoding="utf-8")
    if len(candidates) > 1:
        print(f"NOTE several papers found: {candidates}. Using {paper_dirs}. Ask the author which one the explainer is about; rerun with --paper <folder> to switch.")
    print(f"created {target}\n  explainer.toml  paper={paper_dirs[:3]} vault={vaults[:1]} macros_from={macro_files[:3]}\n  brief.md        fill it, get it approved, then write sections/NN-slug.html\n"
          f"  build:  uv run {target.name}/d3x/build.py --draft      check:  uv run {target.name}/d3x/check.py --shots")
    return 0


if __name__ == "__main__":
    sys.exit(main())
