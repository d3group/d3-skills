# /// script
# requires-python = ">=3.10"
# dependencies = ["pymupdf>=1.24"]
# ///
"""Check a D3 abstract: page contract, column fill, wording, emphasis, colors, TeX log.

Run with uv (dependencies resolve from the inline metadata above):

    uv run ~/.claude/skills/d3-abstract/scripts/check_abstract.py v1_abstract.tex
    uv run ~/.claude/skills/d3-abstract/scripts/check_abstract.py v1_abstract.tex --render review

Exit code 0 means no errors (warnings may remain), 1 means at least one error.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

TEMPLATE_CALL = re.compile(r"\\input\{assets/d3-abstract-template(\.tex)?\}")
DECLARED_PAGES = re.compile(r"\\renewcommand\{\\abstractpages\}\{(\d+)\}")
COMMENT = re.compile(r"(?<!\\)%.*$", re.MULTILINE)
TIKZ_PATH_LINE = re.compile(r"\\(draw|path|fill|filldraw|clip|addplot)\b")

# (level, label, pattern, advice). Patterns run on comment-stripped source, case-insensitive.
WORDING_RULES: list[tuple[str, str, str, str]] = [
    # Dashes as punctuation
    ("E", "dash", r"---", "rewrite with a comma, colon, parentheses, or two sentences"),
    ("E", "dash", "(?<!\\d)[\u2012\u2013\u2014\u2015]|[\u2012\u2013\u2014\u2015](?!\\d)",
     "rewrite with a comma, colon, parentheses, or two sentences"),
    # Contrast framing
    ("E", "contrast", r"\bnot\s+(only|just|merely|simply|solely)\b", "state the positive claim directly"),
    ("E", "contrast", r"\bnot\b[^.;:!?]{0,80}?\bbut\b", "state the positive claim directly"),
    ("E", "contrast", r",\s+not\s+", "state the positive claim directly"),
    ("E", "contrast", r"\b(is|are|was|were)n't\b[^.;:!?]{0,60}?\b(it's|it\s+is|they're|they\s+are)\b",
     "state the positive claim directly"),
    ("W", "contrast", r"\brather\s+than\b", "check whether the positive claim alone is enough"),
    ("W", "contrast", r"\binstead\s+of\b", "check whether the positive claim alone is enough"),
    ("W", "contrast", r"\bmore\s+than\s+(just|merely)\b|\bgo(es)?\s+beyond\b",
     "check whether the positive claim alone is enough"),
    # Tone toward related work
    ("E", "related-work", r"\bfail(s|ed|ing)?\s+to\b", "report what the cited work does and under which assumptions"),
    ("E", "related-work", r"\bsuffer(s|ed|ing)?\s+from\b", "report the property as a neutral fact"),
    ("E", "related-work", r"\bstruggl(e|es|ed|ing)\s+(to|with)\b", "report the property as a neutral fact"),
    ("E", "related-work", r"\b(overlook|neglect)(s|ed|ing)?\b", "state the scope of the cited work"),
    ("E", "related-work", r"\b(fall|falls|fell)\s+short\b", "give the measured difference"),
    ("E", "related-work", r"\bmerely\b", "delete the qualifier"),
    ("E", "related-work", r"\bunlike\s+(previous|prior|existing|earlier|traditional|conventional|other)\b",
     "describe both settings as facts in separate sentences"),
    ("E", "related-work",
     r"\b(existing|prior|previous|current|traditional|conventional)\s+(methods?|approaches|work|models?|studies)\s+"
     r"(cannot|can\s*not|are\s+unable|is\s+unable|do\s+not|does\s+not)\b",
     "report what the cited work does and under which assumptions"),
    ("E", "related-work", r"\b(seminal|pioneering|groundbreaking|ground-breaking|landmark)\b",
     "cite the work without grading it"),
    ("E", "related-work", r"\b(valuable|important|promising|useful|good)\s+first\s+step\b",
     "cite the work without grading it"),
    ("E", "related-work", r"\b(significant|great|considerable|remarkable)\s+(strides|progress)\b",
     "cite the work without grading it"),
    ("E", "related-work", r"\blaid\s+the\s+(groundwork|foundations?)\b", "cite the work without grading it"),
    ("W", "related-work", r"\bwhile\s+(prior|previous|existing|earlier|recent)\b",
     "check the sentence for a concession followed by a dismissal"),
    ("W", "related-work", r"\b(shortcoming|drawback|deficienc(y|ies)|weakness(es)?)\b",
     "prefer a factual scope statement"),
    ("W", "related-work", r"\b(naive(ly)?|simplistic|outdated|inferior|superior)\b",
     "keep only as an established technical term"),
    ("W", "related-work", r"\blimited\s+to\b|\bignor(e|es|ed|ing)\b", "prefer a factual scope statement"),
    # Stock phrases
    ("E", "phrase", r"\bit('s|\s+is)\s+(important|worth)\s+(to\s+note|noting)\b|\bworth\s+noting\b",
     "delete and state the point"),
    ("E", "phrase", r"\bleverag(e|es|ed|ing)\b", 'write "use"'),
    ("E", "phrase", r"\butili[sz](e|es|ed|ing)\b", 'write "use"'),
    ("E", "phrase", r"\bharness(es|ed|ing)?\b", 'write "use"'),
    ("E", "phrase", r"\bdelv(e|es|ed|ing)\b", 'write "examine" or state the finding'),
    ("E", "phrase", r"\bin\s+order\s+to\b", 'write "to"'),
    ("E", "phrase", r"\bplay(s|ed)?\s+an?\s+(crucial|key|vital|pivotal|critical|central)\s+role\b",
     "name the specific role"),
    ("E", "phrase", r"\bcomprehensive(ly)?\b", "delete or name what is covered"),
    ("E", "phrase", r"\bshed(s|ding)?\s+light\s+on\b", 'write "clarify" or state the finding'),
    ("E", "phrase", r"\bpav(e|es|ed|ing)\s+the\s+way\b", "state what it enables"),
    ("E", "phrase", r"\b(crucial(ly)?|pivotal|seamless(ly)?|cutting-edge|game-chang\w*)\b",
     "use a specific, measurable description"),
    ("E", "phrase", r"\b(showcas|underscor)(e|es|ed|ing)\b", 'write "show"'),
    ("E", "phrase", r"\b(testament|tapestry|realm|ever-evolving|rapidly\s+evolving)\b", "delete or be specific"),
    ("W", "phrase", r"\bkey\b", 'write "main" or "central", or drop it (fine as a technical term)'),
    ("W", "phrase", r"\brobust(ly|ness)?\b", "fine as a technical term, otherwise name the property"),
]

EMPHASIS_LIMITS = [
    (r"\\highlight\{", "\\highlight", 3),
    (r"\\node\[[^\]]*\binfobox\b", "infobox", 3),
    (r"\\node\[[^\]]*\bcard alert\b", "card alert", 2),
]

# Established technical terms that contain a flagged word. Matches inside these are skipped.
TECHNICAL_TERMS = re.compile(
    r"doubly[\s-]+robust|distributionally[\s-]+robust|robust\s+(optimi[sz]ation|regression|statistics|control)"
    r"|na[i\u00ef]ve\s+bayes|(public|private|primary|foreign|secret|api)[\s-]+key|key[\s-]+value",
    re.IGNORECASE,
)
ALLOWED_COLOR = re.compile(r"^(d3-[a-z]+|black|white)(![\d.]+(!(d3-[a-z]+|black|white))?)*$")
NUMBER = re.compile(r"\d+(?:[.,]\d+)*")


class Report:
    def __init__(self) -> None:
        self.errors = 0
        self.warnings = 0
        self.lines: list[str] = []

    def add(self, level: str, text: str) -> None:
        if level == "E":
            self.errors += 1
        elif level == "W":
            self.warnings += 1
        self.lines.append(f"  {level} {text}")

    def section(self, title: str) -> None:
        self.lines.append(title)


def strip_comments(src: str) -> str:
    """Blank out TeX comments but keep line numbering intact."""
    return COMMENT.sub("", src)


def line_of(text: str, pos: int) -> int:
    return text.count("\n", 0, pos) + 1


def excerpt(text: str, start: int, end: int, pad: int = 28) -> str:
    snippet = text[max(0, start - pad): min(len(text), end + pad)]
    return " ".join(snippet.split())


def brace_group(text: str, open_pos: int) -> str:
    """Return the content of the brace group that opens at open_pos."""
    depth = 0
    for i in range(open_pos, len(text)):
        ch = text[i]
        if ch == "{" and (i == 0 or text[i - 1] != "\\"):
            depth += 1
        elif ch == "}" and text[i - 1] != "\\":
            depth -= 1
            if depth == 0:
                return text[open_pos + 1: i]
    return text[open_pos + 1:]


def plain_words(tex: str) -> list[str]:
    tex = re.sub(r"\$[^$]*\$", " x ", tex)
    tex = re.sub(r"\\[a-zA-Z]+\*?(\[[^\]]*\])?", " ", tex)
    tex = re.sub(r"[{}\\~]", " ", tex)
    return [w for w in tex.split() if re.search(r"\w", w)]


def check_double_hyphen(text: str, findings: list) -> None:
    """`--` is reserved for number ranges. TikZ path operators are skipped."""
    lines = text.split("\n")
    for m in re.finditer(r"(?<!-)--(?!-)", text):
        ln = line_of(text, m.start())
        if TIKZ_PATH_LINE.search(lines[ln - 1]):
            continue
        before = text[: m.start()].rstrip()[-1:]
        after_text = text[m.end():].lstrip()
        after = after_text[:1]
        if before.isdigit() and after.isdigit():
            continue
        if before in ")]" or after in "([+" or re.match(r"(cycle|node|plot)\b", after_text):
            continue
        findings.append((ln, "E", "dash", excerpt(text, m.start(), m.end()),
                         "rewrite with a comma, colon, parentheses, or two sentences"))


def check_wording(text: str, rep: Report) -> None:
    rep.section("WORDING")
    findings: list[tuple[int, str, str, str, str]] = []
    check_double_hyphen(text, findings)
    spans: list[tuple[int, int, str]] = []
    protected = [t.span() for t in TECHNICAL_TERMS.finditer(text)]
    for level, label, pattern, advice in WORDING_RULES:
        for m in re.finditer(pattern, text, flags=re.IGNORECASE):
            if any(a <= m.start() and m.end() <= b for a, b in protected):
                continue
            if any(lab == label and a < m.end() and m.start() < b for a, b, lab in spans):
                continue
            spans.append((m.start(), m.end(), label))
            ln = line_of(text, m.start())
            findings.append((ln, level, label, excerpt(text, m.start(), m.end()), advice))
    for ln, level, label, snippet, advice in sorted(findings):
        rep.add(level, f"L{ln:<4} {label:<13} \"{snippet}\"  -> {advice}")
    if not findings:
        rep.lines.append("  ok")


def slot_content(chunk: str, slot: str) -> str:
    m = re.search(r"\\renewcommand\{\\" + slot + r"\}\s*\{", chunk)
    return brace_group(chunk, m.end() - 1) if m else ""


def repeated_emphasis(chunk: str) -> dict[str, list[str]]:
    """Numbers that are emphasized in more than one place. Table cells are exempt."""
    prose = re.sub(r"\\begin\{tabular\*?\}.*?\\end\{tabular\*?\}", " ", chunk, flags=re.DOTALL)
    places: dict[str, list[str]] = {}

    def note(group_text: str, place: str) -> None:
        for number in NUMBER.findall(re.sub(r"\\[a-zA-Z]+", " ", group_text)):
            if place not in places.setdefault(number, []):
                places[number].append(place)

    for m in re.finditer(r"\\highlight\{", prose):
        note(brace_group(prose, m.end() - 1), "\\highlight")
    for m in re.finditer(r"\\node\[[^\]]*\binfobox\b[^\]]*\]\s*\{", prose):
        big = re.search(r"\\(?:Large|LARGE|huge|Huge|large)\b([^}]*)\}", brace_group(prose, m.end() - 1))
        if big:
            note(big.group(1), "an infobox")
    return {n: p for n, p in places.items() if len(p) > 1}


def check_emphasis(text: str, rep: Report) -> None:
    rep.section("EMPHASIS (per page)")
    clean = True
    body = text.split("\\begin{document}", 1)[-1]
    chunks = TEMPLATE_CALL.split(body)
    # re.split with one capture group yields [chunk, group, chunk, group, ..., tail]
    pages = chunks[0:-1:2]
    for idx, chunk in enumerate(pages, start=1):
        for pattern, name, limit in EMPHASIS_LIMITS:
            n = len(re.findall(pattern, chunk))
            if n > limit:
                clean = False
                rep.add("W", f"page {idx}: {n} x {name} (limit {limit})")
        for slot, side in (("venstre", "left"), ("hoyre", "right")):
            content = slot_content(chunk, slot)
            n = len(re.findall(r"\\keypoint\{", content))
            if n > 1:
                clean = False
                rep.add("W", f"page {idx}: {n} x \\keypoint in the {side} column (limit 1 per column)")
        lead = slot_content(chunk, "innledning")
        if lead:
            words = plain_words(lead)
            if len(words) > 50:
                clean = False
                rep.add("W", f"page {idx}: lead paragraph has {len(words)} words (limit 50)")
            sentences = [x for x in re.split(r"(?<=[.!?])\s+", " ".join(words)) if x]
            if len(sentences) > 3:
                clean = False
                rep.add("W", f"page {idx}: lead paragraph has {len(sentences)} sentences (limit 3)")
        for number, places in repeated_emphasis(chunk).items():
            clean = False
            rep.add("W", f"page {idx}: {number} is emphasized in {' and '.join(places)}, keep one place")
    if clean:
        rep.lines.append("  ok")


def check_colors(text: str, rep: Report) -> None:
    rep.section("COLORS")
    clean = True
    for m in re.finditer(r"\\definecolor\b", text):
        clean = False
        rep.add("E", f"L{line_of(text, m.start()):<4} \\definecolor in the document, use the D3 palette")
    for m in re.finditer(r"\\(?:text|page)?color\[[^\]]*\]\{[^}]*\}", text):
        clean = False
        rep.add("E", f"L{line_of(text, m.start()):<4} color given by value, use the named D3 colors")
    for m in re.finditer(r"\\(?:text)?color\{([^}]*)\}", text):
        if not ALLOWED_COLOR.match(m.group(1).strip()):
            clean = False
            rep.add("E", f"L{line_of(text, m.start()):<4} color \"{m.group(1)}\" is outside the D3 palette")
    if clean:
        rep.lines.append("  ok")


def check_submission(text: str, rep: Report) -> None:
    rep.section("SUBMISSION ABSTRACT")
    clean = True
    for m in re.finditer(r"\bcard gray\b", text):
        clean = False
        rep.add("E", f"L{line_of(text, m.start()):<4} figure placeholder, a submission needs the final figure")
    for m in re.finditer(r"\\sectionhead\{\s*(Open Questions|Questions for the Team|Paper Progress|Figures Needed)", text):
        clean = False
        rep.add("E", f"L{line_of(text, m.start()):<4} section \"{m.group(1)}\" belongs to internal documents")
    if "\\begin{reflist}" not in text:
        clean = False
        rep.add("W", "no reflist found, a submission abstract cites its sources")
    if clean:
        rep.lines.append("  ok")


def check_todos(raw: str, rep: Report) -> None:
    hits = [(line_of(raw, m.start()), m.group(0).strip()) for m in re.finditer(r"%\s*TODO\b.*$", raw, flags=re.MULTILINE)]
    if not hits:
        return
    rep.section("TODO MARKERS")
    for ln, line in hits:
        rep.add("W", f"L{ln:<4} {line[:90]}")
    rep.lines.append("  resolve before delivery, and report every \"TODO verify\" item to the user")


def check_log(tex_path: Path, rep: Report) -> None:
    log_path = tex_path.with_suffix(".log")
    if not log_path.exists():
        return
    rep.section("LOG")
    log = log_path.read_text(errors="replace")
    clean = True
    overfull = len(re.findall(r"Overfull \\hbox", log))
    if overfull:
        clean = False
        rep.add("W", f"{overfull} x Overfull \\hbox (content wider than its column)")
    for message in dict.fromkeys(m.group(1).strip() for m in re.finditer(r"^! (.+)$", log, flags=re.MULTILINE)):
        clean = False
        rep.add("E", f"TeX error: {message}")
    if clean:
        rep.lines.append("  ok")


def column_fill(page) -> tuple[float, float] | int:
    """Fill ratio of the left and right column between header rule and footer rule."""
    width = page.rect.width
    rules = [d["rect"] for d in page.get_drawings() if d["rect"].width > 0.8 * width and d["rect"].height < 4]
    if len(rules) < 2:
        return len(rules)
    top = min(r.y1 for r in rules)
    bottom = max(r.y0 for r in rules)
    boxes = [b[:4] for b in page.get_text("blocks")]
    boxes += [tuple(d["rect"]) for d in page.get_drawings()]
    boxes += [tuple(page.get_image_bbox(img)) for img in page.get_images(full=True)]
    fills = [0.0, 0.0]
    for x0, y0, x1, y1 in boxes:
        if y0 <= top or y1 >= bottom or (x1 - x0) > 0.6 * width:
            continue
        side = 0 if (x0 + x1) / 2 < width / 2 else 1
        fills[side] = max(fills[side], (y1 - top) / (bottom - top))
    return fills[0], fills[1]


def check_pages(tex_path: Path, text: str, render_dir: Path | None, dpi: int, rep: Report) -> None:
    rep.section("PAGES")
    m = DECLARED_PAGES.search(text)
    declared = int(m.group(1)) if m else 1
    calls = len(TEMPLATE_CALL.findall(text))
    summary = f"declared \\abstractpages = {declared} | template calls = {calls}"
    if calls != declared:
        rep.add("E", f"{summary}  -> one template call per declared page")

    pdf_path = tex_path.with_suffix(".pdf")
    if not pdf_path.exists():
        rep.add("W", f"{summary} | no PDF found, compile with xelatex first")
        return
    if pdf_path.stat().st_mtime < tex_path.stat().st_mtime:
        rep.add("W", "PDF is older than the .tex file, recompile before trusting the page checks")

    import pymupdf  # provided by the inline script metadata

    doc = pymupdf.open(pdf_path)
    n = doc.page_count
    if n != declared:
        hint = "content overflows, cut or move content" if n > declared else "a page is missing"
        rep.add("E", f"{summary} | PDF = {n}  -> {hint}")
    else:
        rep.lines.append(f"  ok  {summary} | PDF = {n}")

    rep.section("COLUMN FILL (share of the space between header rule and footer rule)")
    for i, page in enumerate(doc, start=1):
        fill = column_fill(page)
        if fill == 1:
            rep.add("W", f"page {i}: header rule or footer rule missing, the content of this page or of the page "
                         "before it overflows")
            continue
        if fill == 0:
            rep.add("W", f"page {i}: no layout rules, this page holds overflow or was not made by the template")
            continue
        left, right = fill
        rep.lines.append(f"  page {i}: left {left:4.0%} | right {right:4.0%}")
        if max(left, right) > 0.95:
            rep.add("W", f"page {i}: a column is above 95% full, one more line can push content to a new page")
        if abs(left - right) > 0.25:
            rep.add("W", f"page {i}: columns differ by {abs(left - right):.0%}, redistribute content")
        if i == n and n > 1:
            if max(left, right) < 0.6:
                rep.add("W", f"page {i}: last page under 60% full, cut to {n - 1} page(s) or add content")
        elif max(left, right) < 0.75:
            rep.add("W", f"page {i}: under 75% full, add content from the outline or ask the user")

    if render_dir is not None:
        render_dir.mkdir(parents=True, exist_ok=True)
        for i, page in enumerate(doc, start=1):
            out = render_dir / f"page-{i:03d}.png"
            page.get_pixmap(dpi=dpi).save(out)
        rep.lines.append(f"  rendered {n} page image(s) to {render_dir}/")
    doc.close()


def main() -> int:
    parser = argparse.ArgumentParser(description="Check a D3 abstract (.tex and compiled PDF).")
    parser.add_argument("tex", type=Path, help="path to the abstract .tex file")
    parser.add_argument("--render", type=Path, metavar="DIR", help="write one PNG per page into DIR")
    parser.add_argument("--submission", action="store_true",
                        help="Submission Abstract: no placeholders, no internal sections, references present")
    parser.add_argument("--dpi", type=int, default=150, help="resolution of rendered pages (default 150)")
    args = parser.parse_args()

    if not args.tex.exists():
        print(f"File not found: {args.tex}", file=sys.stderr)
        return 2

    raw = args.tex.read_text(encoding="utf-8")
    text = strip_comments(raw)
    rep = Report()
    check_pages(args.tex, text, args.render, args.dpi, rep)
    check_wording(text, rep)
    check_emphasis(text, rep)
    check_colors(text, rep)
    if args.submission:
        check_submission(text, rep)
    check_todos(raw, rep)
    check_log(args.tex, rep)

    print(f"d3-abstract check: {args.tex}")
    print("\n".join(rep.lines))
    verdict = "FAIL" if rep.errors else "PASS"
    print(f"RESULT: {verdict} ({rep.errors} error(s), {rep.warnings} warning(s))")
    return 1 if rep.errors else 0


if __name__ == "__main__":
    sys.exit(main())
