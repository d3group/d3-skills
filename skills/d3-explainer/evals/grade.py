# /// script
# requires-python = ">=3.11"
# dependencies = ["playwright>=1.49"]
# ///
"""Format-agnostic grader for explainer evals (works on d3-explainer output and on hand-rolled HTML alike).

    uv run evals/grade.py --html X.html --repo /path/to/repo --depth standard --review standard \
        --notes RUN_NOTES.md --out grading.json [--shots DIR]

The page is loaded with the network blocked, so anything that needs a CDN shows up as broken, exactly as it
would for a co-author opening the file on a train.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

PROBE = r"""
async () => {
  const raf = () => new Promise(r => requestAnimationFrame(() => requestAnimationFrame(r)));
  const hash = s => { let h = 0; for (let i = 0; i < s.length; i++) h = (h * 31 + s.charCodeAt(i)) | 0; return h; };
  const sig = () => [...document.querySelectorAll('svg')].map(s => hash(s.innerHTML)).join(',') + '|' +
    [...document.querySelectorAll('canvas')].map(c => { try { return hash(c.toDataURL()); } catch (e) { return 0; } }).join(',') + '|' + hash(document.body.innerText);
  const nan = () => { let n = 0; for (const el of document.querySelectorAll('svg *')) for (const a of el.attributes) if (/NaN|undefined/.test(a.value)) { n++; break; } return n; };
  const out = {};
  // open everything that is merely collapsed so that content checks see it, but count main-line words first
  // prose only: figures, formulas, code, navigation and collapsed detail are not main-line reading text
  const clone = document.body.cloneNode(true);
  clone.querySelectorAll('script, style, svg, canvas, .figbox, .katex, mjx-container, math, pre, nav, aside, #side, #drawer, .toc, .chip, details:not([open]) > *:not(summary), .dstep.hidden, [hidden]').forEach(e => e.remove());
  out.words = (clone.textContent.match(/[A-Za-zÀ-ÿ0-9][\w'’-]*/g) || []).length;
  out.ranges = document.querySelectorAll('input[type=range]').length;
  out.controls = document.querySelectorAll('input[type=range], select, input[type=checkbox], input[type=radio]').length;
  out.nanDefault = nan();
  let dead = [], nanMoved = 0, tested = 0;
  for (const inp of [...document.querySelectorAll('input[type=range]')].slice(0, 30)) {
    if (inp.offsetParent === null) continue;
    const def = inp.value, states = new Set();
    for (const v of [inp.min || 0, inp.max || 100]) { inp.value = v; inp.dispatchEvent(new Event('input', {bubbles: true})); inp.dispatchEvent(new Event('change', {bubbles: true})); await raf(); states.add(sig()); nanMoved += nan(); }
    inp.value = def; inp.dispatchEvent(new Event('input', {bubbles: true})); inp.dispatchEvent(new Event('change', {bubbles: true})); await raf();
    tested++; if (states.size < 2) dead.push(inp.id || inp.name || inp.getAttribute('data-param') || '(unnamed)');
  }
  out.tested = tested; out.dead = dead; out.nanMoved = nanMoved;
  out.mathEls = document.querySelectorAll('.katex, mjx-container, math').length;
  const text = document.body.innerText;
  out.rawTex = (text.match(/\\frac|\\mathbb|\\begin\{|\$\$|\\\(/g) || []).length;
  out.eqTags = document.querySelectorAll('.katex-tag, .katex .tag, mjx-mtd[id^="mjx-eqn"], mjx-labels mjx-mtd, .mjx-tag').length;
  out.headings = [...document.querySelectorAll('h1,h2,h3,h4,summary,.note .h,.callout-title')].map(h => h.innerText.trim()).filter(Boolean);
  out.tables = [...document.querySelectorAll('table')].map(t => (t.querySelector('tr') || t).innerText.trim().slice(0, 120));
  out.captions = [...document.querySelectorAll('figcaption, .caption, .figcap')].map(c => c.innerText.trim());
  out.buttons = [...document.querySelectorAll('button')].map(b => b.innerText.trim()).filter(Boolean);
  out.dashes = (text.match(/—|[A-Za-z,;:)]\s–\s[A-Za-z(]/g) || []).length;
  out.toy = /illustrative|\btoy\b|stylized|stylised|synthetic|not an experiment|simulated here/i.test(text);
  out.pointerText = text + ' ' + [...document.querySelectorAll('[title],[href]')].map(e => (e.getAttribute('title') || '') + ' ' + (e.getAttribute('href') || '')).join(' ');
  out.fonts = getComputedStyle(document.body).fontFamily;
  out.mono = /mono/i.test(getComputedStyle(document.querySelector('figcaption b, .step .lbl, th') || document.body).fontFamily); out.hero = !!document.querySelector('header.hero, .hero');
  return out;
}
"""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--html", required=True)
    ap.add_argument("--repo", required=True)
    ap.add_argument("--depth", default="standard", choices=["focus", "overview", "standard", "deep"])
    ap.add_argument("--review", default="standard", choices=["light", "single", "standard", "full"])
    ap.add_argument("--notes")
    ap.add_argument("--out", required=True)
    ap.add_argument("--shots")
    a = ap.parse_args()
    html_path, repo = Path(a.html).resolve(), Path(a.repo).resolve()
    exp: list[dict] = []

    def add(text: str, passed: bool, evidence: str) -> None:
        exp.append({"text": text, "passed": bool(passed), "evidence": evidence})

    if not html_path.exists():
        add("A final HTML explainer file exists", False, f"{html_path} not found")
        Path(a.out).write_text(json.dumps({"expectations": exp, "summary": {"passed": 0, "failed": 1, "total": 1, "pass_rate": 0.0}}, indent=2))
        return 0
    src = html_path.read_text(encoding="utf-8", errors="replace")
    ext = sorted(set(re.findall(r"""(?:src|href)\s*=\s*["'](https?://[^"']+)["']""", re.sub(r"<a\b[^>]*>", "", src)) + re.findall(r"url\(\s*['\"]?(https?://[^)'\"]+)", src) + re.findall(r"@import\s+['\"](https?://[^'\"]+)", src)))
    add("Single self-contained file: no scripts, styles, fonts or images loaded from the network", not ext,
        "no external resources" if not ext else f"{len(ext)} external resources, e.g. {', '.join(ext[:3])}")

    from playwright.sync_api import Error, sync_playwright
    with sync_playwright() as pw:
        browser = None
        for kw in ({}, {"channel": "chrome"}, {"channel": "msedge"}):
            try:
                browser = pw.chromium.launch(**kw)
                break
            except Error:
                pass
        if browser is None:
            sys.exit("no browser for playwright")
        ctx = browser.new_context(viewport={"width": 1280, "height": 900})
        ctx.route("**/*", lambda route: route.continue_() if route.request.url.startswith(("file:", "data:", "blob:", "about:")) else route.abort())
        page = ctx.new_page()
        errs: list[str] = []
        page.on("pageerror", lambda e: errs.append(str(e)[:200]))
        page.on("console", lambda m: errs.append(m.text[:200]) if m.type == "error" and "ERR_FAILED" not in m.text and "net::" not in m.text else None)
        page.goto(html_path.as_uri())
        page.wait_for_timeout(1500)
        r = page.evaluate(PROBE)
        page.set_viewport_size({"width": 390, "height": 800})
        page.wait_for_timeout(300)
        overflow = page.evaluate("document.documentElement.scrollWidth - document.documentElement.clientWidth")
        if a.shots:
            shots = Path(a.shots)
            shots.mkdir(parents=True, exist_ok=True)
            page.set_viewport_size({"width": 1280, "height": 1500})
            page.evaluate("window.scrollTo(0,0)")
            page.wait_for_timeout(300)
            page.screenshot(path=str(shots / "01-top-of-page.png"))
            figs = page.locator("figure:has(input[type=range]), .figbox, .widget, figure:has(svg), figure:has(canvas)").all()
            seen = 0
            for f in figs:
                try:
                    box = f.bounding_box()
                    if not box or box["height"] < 150 or box["width"] < 300:
                        continue
                    f.scroll_into_view_if_needed()
                    page.wait_for_timeout(150)
                    f.screenshot(path=str(shots / f"{seen + 2:02d}-figure.png"))
                    seen += 1
                except Error:
                    continue
                if seen >= 4:
                    break
        browser.close()

    add("Page loads offline without JavaScript errors", not errs, "no errors" if not errs else f"{len(errs)} errors, first: {errs[0]}")
    need = {"focus": 1, "overview": 2, "standard": 4, "deep": 5}[a.depth]
    add(f"Interactive: at least {need} sliders drive figures", r["ranges"] >= need, f"{r['ranges']} range inputs, {r['controls']} controls in total")
    add("Every slider visibly changes its figure, a readout, or the text (no dead controls)", r["tested"] > 0 and not r["dead"],
        f"{r['tested']} sliders moved to both ends; dead: {r['dead'] or 'none'}")
    add("No NaN or undefined in any SVG attribute, at default and at slider extremes", r["nanDefault"] + r["nanMoved"] == 0,
        f"default: {r['nanDefault']}, after moving sliders: {r['nanMoved']}")
    need_math = {"focus": 4, "overview": 6, "standard": 15, "deep": 25}[a.depth]
    add(f"Math is typeset offline (at least {need_math} rendered formulas, no raw TeX left in the text)", r["mathEls"] >= need_math and r["rawTex"] == 0,
        f"{r['mathEls']} typeset formulas, {r['rawTex']} raw TeX fragments visible")
    add("Equations carry the paper's own equation numbers", r["eqTags"] >= 1, f"{r['eqTags']} numbered display equations")

    cands = set(re.findall(r"(?<![\w/.-])((?:src|paper|scripts|configs|results|notebooks|tests|docs|data)/[\w./ -]*?[\w-]+\.(?:py|tex|json|ya?ml|csv|ipynb|toml|md|bib))", r["pointerText"]))
    missing = sorted(c for c in cands if not (repo / c).exists())
    avail = sum(1 for d in ("src", "paper", "scripts", "configs", "results") if (repo / d).is_dir() for f in (repo / d).rglob("*") if f.suffix in {".py", ".tex", ".json", ".csv", ".yaml", ".yml"})
    want = max(2, min(6, avail))          # a toy repository has few files to point at
    add(f"Points into the repository: at least {want} distinct file pointers, and every file mentioned exists", len(cands) >= want and not missing,
        f"{len(cands)} distinct paths; missing: {missing[:5] or 'none'}")
    lines = set(re.findall(r"((?:src|scripts)/[\w./-]+\.py):(\d+)", r["pointerText"]))
    bad = []
    for p, ln in lines:
        f = repo / p
        if f.exists() and int(ln) > f.read_text(errors="replace").count("\n") + 1:
            bad.append(f"{p}:{ln}")
    add("Line-level code pointers (path:line): at least 3, all within their file", len(lines) >= 3 and not bad, f"{len(lines)} path:line pointers; out of range: {bad[:5] or 'none'}")

    heads = " | ".join(r["headings"])
    add("Has a research-gap section (what exists, where it stops, what is new)", bool(re.search(r"\bgap\b|prior work|related work|existing (work|approach|literature)|literature|what is new|where .* stops", heads, re.I)),
        "matching heading: " + (next((h for h in r["headings"] if re.search(r"\bgap\b|prior work|related work|existing|literature|what is new|stops", h, re.I)), "none")))
    add("Has an honest inventory (assumptions, paper versus code, open questions) as its own section or callouts",
        bool(re.search(r"open (question|end|point)|limitation|assumption|paper (vs\.?|versus|and) code|disagree|discrepan|caveat|still open|honest|what is open", heads, re.I)),
        "matching heading: " + (next((h for h in r["headings"] if re.search(r"open (question|end|point)|limitation|assumption|versus code|vs\.? code|and code|disagree|discrepan|caveat|still open|honest", h, re.I)), "none")))
    add("Has a notation or glossary table", bool(re.search(r"notation|glossary|symbols", heads, re.I)) and any(re.search(r"symbol|notation|meaning|term", t, re.I) for t in r["tables"]),
        f"{len(r['tables'])} tables; headers: {[t[:40] for t in r['tables'][:4]]}")
    add("Has a step-through derivation (steps revealed one at a time)", any(re.search(r"next step|show all|reveal|next$|step \d", b, re.I) for b in r["buttons"]),
        f"buttons: {sorted(set(r['buttons']))[:8]}")
    guided = [c for c in r["captions"] if re.search(r"\btry\b|drag|move the|slide|press|notice|observe|watch", c, re.I)]
    add("Figure captions tell the reader what to do and what to notice", len(guided) >= max(1, need - 1), f"{len(guided)} of {len(r['captions'])} captions give guidance")
    add("Toy simulations are labelled as illustrative (not passed off as the repository's experiments)", r["toy"], "label found" if r["toy"] else "no 'illustrative/toy/stylized/synthetic' wording found")
    lo, hi = {"focus": (300, 1500), "overview": (600, 2900), "standard": (1800, 6900), "deep": (3500, 13800)}[a.depth]
    add(f"Main-line length fits the requested depth ({a.depth}: {lo:,} to {hi:,} words of prose; figures, formulas, code and collapsed detail are not counted)", lo <= r["words"] <= hi, f"{r['words']:,} words of prose")
    add("No horizontal overflow at phone width (390 px)", overflow <= 1, f"overflow: {overflow}px")
    add("House wording rule: no em-dashes or spaced en-dashes as punctuation (at most 2)", r["dashes"] <= 2, f"{r['dashes']} found")
    add("D3 look: Inter, mono labels, a hero band", "inter" in r["fonts"].lower() and r["mono"] and r["hero"], f"body font: {r['fonts'][:40]}; mono labels: {r['mono']}; hero: {r['hero']}")

    if a.notes and Path(a.notes).exists():
        notes = Path(a.notes).read_text(errors="replace")
        if a.review == "light":
            add("Review kept light as requested (automated checks, no reviewer agents)", not re.search(r"(fidelity|experience) review(er)?[^\n]{0,80}\b\d+\s*/\s*10", notes, re.I) and bool(re.search(r"light|automated", notes, re.I)),
                "notes mention light/automated review" if re.search(r"light|automated", notes, re.I) else "notes do not describe the review depth")
        else:
            two = bool(re.search(r"fidelity", notes, re.I)) and bool(re.search(r"experience|visual|interaction|figure", notes, re.I))
            scored = len(re.findall(r"\b\d{1,2}\s*/\s*10\b|\|\s*\d{1,2}\s*\|", notes)) >= 4
            add("Two-perspective review performed and documented (content fidelity, and figures/experience) with scores and findings", two and scored, f"two perspectives named: {two}; scores present: {scored}")
    passed = sum(e["passed"] for e in exp)
    Path(a.out).write_text(json.dumps({"expectations": exp, "summary": {"passed": passed, "failed": len(exp) - passed, "total": len(exp), "pass_rate": round(passed / len(exp), 4)}}, indent=2))
    print(f"{passed}/{len(exp)} passed -> {a.out}")
    for e in exp:
        print(("  PASS " if e["passed"] else "  FAIL ") + e["text"] + "  [" + e["evidence"][:110] + "]")
    return 0


if __name__ == "__main__":
    sys.exit(main())
