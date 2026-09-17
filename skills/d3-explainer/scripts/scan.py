# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Map a research repository for the d3-explainer skill: paper, code, results, vault, in one compact report.

    uv run <skill-dir>/scripts/scan.py                 # scans the current directory
    uv run <skill-dir>/scripts/scan.py path/to/repo --out explainer/scan.md

The report replaces a few dozen ls/grep/find calls. It names what exists, how big it is (in tokens, chars / 4),
and what to read first. It never prints file contents beyond titles, abstracts, headings and symbol names.
"""
from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path

PRUNE = {".git", "node_modules", ".venv", "venv", "env", "__pycache__", ".mypy_cache", ".ruff_cache", ".pytest_cache", "lightning_logs", "wandb",
         "mlruns", ".cache", "dist", "build", "site-packages", ".ipynb_checkpoints", ".idea", ".vscode", ".obsidian", ".trash", "archive", "d3x"}
CODE_EXT = {".py": "Python", ".jl": "Julia", ".r": "R", ".R": "R", ".m": "MATLAB", ".cpp": "C++", ".c": "C", ".h": "C/C++", ".js": "JavaScript",
            ".ts": "TypeScript", ".rs": "Rust", ".go": "Go", ".lean": "Lean", ".sh": "Shell"}
FIG_EXT = {".pdf", ".png", ".jpg", ".jpeg", ".svg", ".eps"}
KEY_NOTE = re.compile(r"overview|idea|gap|contribution|open.?question|outline|spec|decision|roadmap|summary|concept|model", re.I)
ORIENT = re.compile(r"^(readme|claude|agents|architecture|overview|notes?|todo|roadmap|spec|design).*\.(md|txt)$|_(analysis|spec|notes|overview)\.md$|spec.*\.md$", re.I)


def tokens(n_chars: int) -> str:
    t = n_chars / 4
    return f"{t / 1000:.1f}k tok" if t >= 1000 else f"{int(t)} tok"


def read(p: Path, limit: int = 2_000_000) -> str:
    try:
        return p.read_text(encoding="utf-8", errors="replace")[:limit]
    except OSError:
        return ""


def walk(root: Path, max_files: int = 60000):
    n = 0
    for d, dirs, files in os.walk(root):
        dirs[:] = [x for x in dirs if x not in PRUNE and not x.endswith(".egg-info") and not re.search(r"template|guideline", x, re.I)]
        for f in files:
            if f.startswith("."):
                continue
            n += 1
            if n > max_files:
                return
            yield Path(d) / f


def git(root: Path, *a: str) -> str:
    try:
        return subprocess.run(["git", "--no-optional-locks", "-C", str(root), *a], capture_output=True, text=True, timeout=10).stdout.strip()
    except (OSError, subprocess.SubprocessError):
        return ""


def first_heading(text: str) -> str:
    m = re.search(r"^#\s+(.+)$", text, flags=re.M)
    return m.group(1).strip()[:90] if m else ""


def tex_clean(s: str) -> str:
    s = re.sub(r"(?<!\\)%.*", "", s)
    if s.count("$") >= 2:                    # leave inline math as written: stripping commands inside it garbles the sentence
        parts = s.split("$")
        return re.sub(r"\s+", " ", "".join("$" + p + "$" if i % 2 else tex_clean(p) + " " for i, p in enumerate(parts))).strip()
    s = re.sub(r"\\(cite[tp]?|ref|eqref|cref|label)\*?(\[[^\]]*\])*\{[^}]*\}", "", s)
    s = re.sub(r"\\[a-zA-Z]+\*?(\[[^\]]*\])?", " ", s)
    return re.sub(r"\s+", " ", s.replace("{", "").replace("}", "")).strip()


# ------------------------------------------------------------------ paper
def scan_papers(root: Path, files: list[Path]) -> list[str]:
    tex = [f for f in files if f.suffix == ".tex"]
    mains = []
    for f in tex:
        t = read(f, 400_000)
        if "\\documentclass" in t and ("\\begin{abstract}" in t or "\\title" in t) and "beamer" not in t[:600] and "baposter" not in t[:600]:
            if not re.search(r"(template|guideline|sample|example)", f.name, re.I) and not re.search(r"(template|guideline)", str(f.parent), re.I):
                mains.append((f, t))
    out: list[str] = []
    if not mains:
        pdfs = [f for f in files if f.suffix == ".pdf" and f.stat().st_size > 150_000 and re.search(r"paper|manuscript|draft|preprint|arxiv|submission", str(f), re.I)]
        if pdfs:
            out.append("No LaTeX paper source. Candidate paper PDFs (read with `uv run --with pymupdf`):")
            out += [f"- {p.relative_to(root)} ({p.stat().st_size // 1000} kB)" for p in pdfs[:6]]
        else:
            out.append("No paper found (no .tex with \\documentclass, no paper-like PDF).")
        return out
    for f, t in sorted(mains, key=lambda x: len(str(x[0])))[:6]:
        pdir = f.parent
        parts, total = [f], len(t)
        for m in re.finditer(r"\\(?:input|include|subfile)\{([^}]+)\}", re.sub(r"(?<!\\)%.*", "", t)):
            q = pdir / (m.group(1) if m.group(1).endswith(".tex") else m.group(1) + ".tex")
            if q.exists():
                parts.append(q)
        body = "\n".join(read(p, 400_000) for p in parts)
        total = len(body)
        title = re.search(r"\\title(?:\[[^\]]*\])?\{((?:[^{}]|\{[^{}]*\})*)\}", t)
        abstract = re.search(r"\\begin\{abstract\}(.*?)\\end\{abstract\}", body, flags=re.S)
        out.append(f"### {f.relative_to(root)}  ({tokens(total)} incl. {len(parts) - 1} input files)")
        if title:
            out.append(f"- Title: {tex_clean(title.group(1))[:160]}")
        if abstract:
            out.append(f"- Abstract: {tex_clean(abstract.group(1))[:700]}")
        clean = re.sub(r"(?<!\\)%.*", "", body)
        heads = [(m.group(1), m.group(2), "\\label" in clean[m.end():m.end() + 160].split("\\section")[0].split("\\subsection")[0])
                 for m in re.finditer(r"\\(section|subsection)\*?\{((?:[^{}]|\{[^{}]*\})*)\}", clean)]
        if heads:
            out.append("- Outline (° = no \\label; cite it as [[paper:§Title]]): " + " · ".join(("" if k == "section" else "› ") + tex_clean(h)[:50] + ("" if lab else "°") for k, h, lab in heads[:40]))
        if len(parts) > 1:
            out.append("- Section files: " + ", ".join(f"{p.relative_to(pdir)} ({tokens(len(read(p)))})" for p in parts[1:16]))
        labels = re.findall(r"\\label\{([^}]+)\}", body)
        by = defaultdict(list)
        for lab in labels:
            by[lab.split(":")[0] if ":" in lab else "other"].append(lab)
        n_eq = len(re.findall(r"\\begin\{(equation|align|gather|multline|eqnarray)\*?\}", body))
        n_thm = len(re.findall(r"\\begin\{(theorem|lemma|proposition|corollary|definition|assumption)\}", body))
        out.append(f"- Math: {n_eq} display equations, {n_thm} theorem-like environments; labels: " +
                   "; ".join(f"{k} ({len(v)}): {', '.join(v[:10])}{' …' if len(v) > 10 else ''}" for k, v in sorted(by.items(), key=lambda kv: -len(kv[1]))[:5]))
        figs = re.findall(r"\\includegraphics(?:\[[^\]]*\])?\{([^}]+)\}", body)
        if figs:
            out.append(f"- Figures used ({len(figs)}): " + ", ".join(figs[:12]) + (" …" if len(figs) > 12 else ""))
        macro_files = [p for p in tex if p.parent == pdir or pdir in p.parents if len(re.findall(r"\\(?:re)?newcommand|\\DeclareMathOperator", read(p, 200_000))) >= 3]
        if macro_files:
            out.append("- Macro definitions (for `macros_from`): " + ", ".join(str(p.relative_to(root)) for p in macro_files[:4]))
        aux = list(pdir.glob("*.aux"))
        out.append(f"- .aux present: {'yes, equation and section numbers will match the paper' if aux else 'no; compile the paper once if chips should show equation numbers'}")
        bibs = list(pdir.glob("*.bib"))
        for b in bibs[:2]:
            out.append(f"- Bibliography: {b.relative_to(root)} ({len(re.findall(r'^@', read(b), flags=re.M))} entries)")
    return out


# ------------------------------------------------------------------ code
def scan_code(root: Path, files: list[Path]) -> list[str]:
    vaults = [d for d in root.iterdir() if d.is_dir() and ((d / ".obsidian").exists() or re.search(r"vault", d.name, re.I))]
    code = [f for f in files if f.suffix in CODE_EXT and "paper" not in f.parts[len(root.parts):len(root.parts) + 1]
            and not any(v in f.parents for v in vaults)]   # import scripts inside an Obsidian vault are not project code
    if not code:
        return ["No source code found."]
    loc, by_lang, by_dir = {}, Counter(), Counter()
    for f in code:
        n = read(f, 600_000).count("\n")
        loc[f] = n
        by_lang[CODE_EXT[f.suffix]] += n
        rel = f.relative_to(root)
        by_dir["/".join(rel.parts[:2]) if len(rel.parts) > 2 else (rel.parts[0] if len(rel.parts) > 1 else ".")] += n
    out = [f"- {len(code)} source files, {sum(loc.values()):,} lines: " + ", ".join(f"{k} {v:,}" for k, v in by_lang.most_common(4)),
           "- By folder: " + ", ".join(f"{k}/ {v:,}" for k, v in by_dir.most_common(10))]
    nbs = [f for f in files if f.suffix == ".ipynb"]
    if nbs:
        out.append(f"- Notebooks ({len(nbs)}): " + ", ".join(str(f.relative_to(root)) for f in sorted(nbs, key=lambda p: -p.stat().st_mtime)[:6]))
    entry = [f for f in code if f.suffix == ".py" and not re.search(r"(^|/)tests?/|test_", str(f.relative_to(root))) and "__main__" in read(f, 300_000)]
    if entry:
        out.append("- Entry points (`__main__`): " + ", ".join(str(f.relative_to(root)) for f in entry[:10]))
    cfgs = [f for f in files if f.suffix in {".yaml", ".yml", ".toml"} and re.search(r"conf", str(f.parent), re.I)]
    if cfgs:
        out.append(f"- Configs ({len(cfgs)}): " + ", ".join(str(f.relative_to(root)) for f in cfgs[:8]))
    out.append("- Largest modules, with their top-level symbols (name:line):")
    src_first = sorted(loc, key=lambda f: (-(("src" in f.parts) or ("package" in f.parts)), -loc[f]))
    core = [f for f in src_first if not re.search(r"(^|/)tests?/|test_|/scripts?/|plot|viz|visual", str(f.relative_to(root)))][:14]
    for f in core:
        t = read(f, 600_000)
        syms = [(m.group(2), t.count("\n", 0, m.start()) + 1) for m in re.finditer(r"^(class|def|function|struct)\s+([A-Za-z_]\w*)", t, flags=re.M)]
        shown = ", ".join(f"{n}:{ln}" for n, ln in syms[:9]) + (f" … +{len(syms) - 9}" if len(syms) > 9 else "")
        out.append(f"  - {f.relative_to(root)} ({loc[f]} lines, {tokens(len(t))}): {shown}")
    return out


# ------------------------------------------------------------------ results, figures, knowledge
def scan_results(root: Path, files: list[Path]) -> list[str]:
    out = []
    res_dirs = [d for d in root.iterdir() if d.is_dir() and re.match(r"(results?|outputs?|experiments?|runs|artifacts|reports?)$", d.name, re.I)]
    for d in res_dirs[:5]:
        fs = [f for f in files if d in f.parents]
        if not fs:
            continue
        ext = Counter(f.suffix.lower() or "(none)" for f in fs)
        newest = sorted(fs, key=lambda p: -p.stat().st_mtime)[:5]
        out.append(f"- {d.name}/: {len(fs)} files ({', '.join(f'{k} {v}' for k, v in ext.most_common(5))}); newest: " +
                   ", ".join(f"{f.relative_to(root)} ({time.strftime('%Y-%m-%d', time.localtime(f.stat().st_mtime))})" for f in newest))
    small = [f for f in files if f.suffix.lower() in {".json", ".csv"} and 200 < f.stat().st_size < 250_000 and any(d in f.parents for d in res_dirs)]
    if small:
        out.append("- Small result tables that can be embedded for a real-data figure: " + ", ".join(f"{f.relative_to(root)} ({f.stat().st_size // 1000 or 1} kB)" for f in sorted(small, key=lambda p: -p.stat().st_mtime)[:8]))
    binary = [f for f in files if f.suffix.lower() in {".parquet", ".feather", ".pkl", ".npz", ".h5"} and "data" not in f.relative_to(root).parts[:1]]
    if binary:
        by = Counter(str(f.parent.relative_to(root)) for f in binary)
        out.append(f"- Binary result tables ({len(binary)}; convert the one you need to JSON, see components.md section 5): " + ", ".join(f"{k}/ ({v})" for k, v in by.most_common(5)) +
                   "; newest: " + ", ".join(f"{f.relative_to(root)} ({f.stat().st_size // 1000 or 1} kB)" for f in sorted(binary, key=lambda p: -p.stat().st_mtime)[:5]))
    fig_dirs = Counter()
    for f in files:
        if f.suffix.lower() in FIG_EXT and re.search(r"fig|plot|image|img", str(f.parent.relative_to(root)), re.I):
            fig_dirs[str(f.parent.relative_to(root))] += 1
    if fig_dirs:
        out.append("- Figure folders: " + ", ".join(f"{k}/ ({v})" for k, v in fig_dirs.most_common(6)))
    return out or ["No results or figure folders found."]


def scan_knowledge(root: Path, files: list[Path]) -> list[str]:
    out = []
    vaults = [d for d in root.iterdir() if d.is_dir() and ((d / ".obsidian").exists() or re.search(r"vault", d.name, re.I))]
    for v in vaults[:3]:
        notes = [f for f in files if v in f.parents and f.suffix == ".md"]
        folders = Counter(f.relative_to(v).parts[0] for f in notes if len(f.relative_to(v).parts) > 1)
        out.append(f"### Vault: {v.name}/  ({len(notes)} notes)")
        top = [f for f in notes if f.parent == v]
        if top:
            out.append("- Top-level notes: " + ", ".join(f"{f.stem} ({tokens(f.stat().st_size)})" for f in sorted(top)[:14]))
        if folders:
            out.append("- Folders: " + ", ".join(f"{k}/ ({n})" for k, n in folders.most_common(8)))
        own = re.compile(r"^(concepts?|reviews?|decisions?|specs?|ideas?|topics?|paper|model|meetings?|dashboards?)$", re.I)
        imported = re.compile(r"notebooklm|sources?|literature|clippings|readwise|zotero", re.I)
        for folder in sorted({f.parent for f in notes if own.match(f.parent.name) and not any(imported.search(x) for x in f.relative_to(v).parts[:-1])}):
            inside = sorted((f for f in notes if f.parent == folder), key=lambda p: -p.stat().st_mtime)
            out.append(f"- {folder.relative_to(v)}/ (the author's own notes, {len(inside)}): " + ", ".join(f"{f.stem} ({tokens(f.stat().st_size)})" for f in inside[:18]) + (" …" if len(inside) > 18 else ""))
        key = [f for f in notes if KEY_NOTE.search(f.stem) and f.parent != v and not own.match(f.parent.name) and not any(imported.search(x) for x in f.relative_to(v).parts[:-1])]
        if key:
            out.append("- Notes whose names suggest concepts, gaps, decisions: " + ", ".join(str(f.relative_to(v).with_suffix("")) for f in sorted(key, key=lambda p: -p.stat().st_mtime)[:12]))
        recent = sorted(notes, key=lambda p: -p.stat().st_mtime)[:8]
        out.append("- Most recently edited: " + ", ".join(f"{f.stem} ({time.strftime('%Y-%m-%d', time.localtime(f.stat().st_mtime))})" for f in recent))
    def looks_like_explainer(f: Path) -> bool:
        if f.suffix != ".html" or "dist" in f.parts or "htmlcov" in f.parts:
            return False
        if re.search(r"explain|walk.?through|tutorial|build.?up|erkl", f.name, re.I):
            return True
        if f.stat().st_size < 60_000:
            return False
        head = read(f, 1_500_000)
        return 'type="range"' in head and "<h2" in head      # a hand-made interactive page, whatever it is called

    prior = [f for f in files if looks_like_explainer(f)]
    if prior:
        out.append("- **Existing explainers** (read the headings first: they show what the author already understands and the tone they like): " +
                   ", ".join(f"{f.relative_to(root)} ({f.stat().st_size // 1000} kB)" for f in prior[:5]))
    orient = [f for f in files if ORIENT.search(f.name) and len(f.relative_to(root).parts) <= 2 and not any(v in f.parents for v in vaults)]
    if orient:
        out.append("- Orientation documents: " + ", ".join(f"{f.relative_to(root)} ({tokens(f.stat().st_size)}" + (f", “{h}”" if (h := first_heading(read(f, 4000))) else "") + ")" for f in sorted(orient, key=lambda p: (len(p.parts), p.name))[:12]))
    for name, what in (("Claude-Sessions", "session logs"), ("literature", "literature files"), ("Literature", "literature files"), ("discussions", "discussion notes"), ("docs", "docs")):
        d = root / name
        if d.is_dir():
            n = sum(1 for f in files if d in f.parents)
            out.append(f"- {name}/: {n} {what}")
    return out or ["No vault, notes or orientation documents found."]


def scan_freshness(root: Path, files: list[Path]) -> list[str]:
    """Last change of orientation documents, papers and code folders: stale documentation and abandoned approaches show up here."""
    def last(path: Path) -> str:
        d = git(root, "log", "-1", "--format=%cs", "--", str(path.relative_to(root)))
        if d:
            return d
        inside = [f for f in files if f == path or path in f.parents]
        return time.strftime("%Y-%m-%d", time.localtime(max((f.stat().st_mtime for f in inside), default=0))) if inside else "?"

    items = [f for f in files if ORIENT.search(f.name) and len(f.relative_to(root).parts) == 1][:4]
    items += [f for f in files if f.suffix == ".tex" and f.name in ("main.tex",) and len(f.relative_to(root).parts) <= 3][:3]
    for base in ("src", "scripts", "code", "package"):
        d = root / base
        if d.is_dir():
            subs = [x for x in sorted(d.iterdir()) if x.is_dir() and x.name not in PRUNE and any(f.suffix in CODE_EXT for f in files if x in f.parents)]
            items += subs[:6] if subs else [d]
    if not items:
        return []
    dated = sorted(((last(i), str(i.relative_to(root)) + ("/" if i.is_dir() else "")) for i in items), reverse=True)
    out = ["- Last changed: " + " · ".join(f"{name} {d}" for d, name in dated)]
    newest = dated[0][0]
    stale = [name for d, name in dated if d != "?" and newest != "?" and d < newest and name.lower().startswith(("claude", "readme", "agents"))]
    if stale:
        out.append(f"- NOTE {', '.join(stale)} is older than the newest code or paper change ({newest}). It may describe an earlier approach: check which code folder the paper actually covers before trusting it.")
    return out


def tier(has_paper: bool, has_code: bool, has_pdf: bool) -> str:
    if has_paper and has_code:
        return "A: code and paper source. The explainer can link every idea to both."
    if has_paper:
        return "B: paper source only. Derivations and gap come from the paper; the realization section describes the planned or external code."
    if has_code:
        return "C: code only. The explainer reconstructs the idea from code, README and notes; mark reconstructions as [[reading]]."
    if has_pdf:
        return "D: compiled paper only. Extract text with pymupdf; equations must be retyped and cannot be validated."
    return "E: notes or conversation only. Interview the author before writing anything."


def read_explainer(path: Path, section: str | None) -> int:
    """Outline of a self-contained HTML explainer with word counts, or one section as plain text (scripts and styles dropped)."""
    import html as _html
    t = re.sub(r"<(script|style)\b.*?</\1>", " ", read(path, 8_000_000), flags=re.S | re.I)
    parts = re.split(r"(?=<h[12]\b)", t)
    heads = []
    for i, part in enumerate(parts):
        m = re.match(r"<h([12])\b[^>]*>(.*?)</h\1>", part, flags=re.S)
        text = re.sub(r"\s+", " ", _html.unescape(re.sub(r"<[^>]+>", " ", part))).strip()
        heads.append((i, m.group(1) if m else "-", re.sub(r"\s+", " ", _html.unescape(re.sub(r"<[^>]+>", " ", m.group(2)))).strip() if m else "(before the first heading)", text))
    if section is None:
        print(f"# Outline of {path.name}  (read one section with --section N)")
        for i, level, title, text in heads:
            print(f"{i:>3}  h{level}  {title[:90]}  ({len(text.split())} words, {text.count('Figure')} figure mentions)")
        return 0
    hit = [h for h in heads if str(h[0]) == section or section.lower() in h[2].lower()]
    if not hit:
        sys.exit(f"no section matches '{section}'")
    print(f"# {hit[0][2]}\n\n{hit[0][3]}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("repo", nargs="?", default=".")
    ap.add_argument("--out", help="also write the report to this file")
    ap.add_argument("--explainer", help="instead of scanning: print the outline of this HTML explainer (with --section: one section as text)")
    ap.add_argument("--section", help="with --explainer: section number from the outline, or part of its title")
    a = ap.parse_args()
    if a.explainer:
        return read_explainer(Path(a.explainer).resolve(), a.section)
    root = Path(a.repo).resolve()
    if not root.is_dir():
        sys.exit(f"error: {root} is not a directory")
    files = list(walk(root))
    papers = scan_papers(root, files)
    code = scan_code(root, files)
    has_paper = any(line.startswith("### ") for line in papers)
    has_code = not code[0].startswith("No source")
    has_pdf = any("Candidate paper PDFs" in line for line in papers)
    sub = git(root, "config", "--file", ".gitmodules", "--get-regexp", "path")
    lines = [f"# Repository scan: {root.name}", "",
             f"- Path: {root}",
             f"- Git: {git(root, 'rev-parse', '--abbrev-ref', 'HEAD') or 'not a repository'} @ {git(root, 'rev-parse', '--short', 'HEAD')}  remote: {git(root, 'remote', 'get-url', 'origin') or 'none'}",
             f"- Submodules: {', '.join(x.split()[-1] for x in sub.splitlines()) if sub else 'none'}",
             f"- **Input tier {tier(has_paper, has_code, has_pdf)}**", *scan_freshness(root, files), "",
             "## Paper", *papers, "", "## Code", *code, "", "## Results and figures", *scan_results(root, files), "",
             "## Notes, vault, prior explainers", *scan_knowledge(root, files), ""]
    text = "\n".join(lines)
    print(text)
    if a.out:
        out = Path(a.out)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(text, encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
