# /// script
# requires-python = ">=3.11"
# dependencies = ["playwright>=1.49"]
# ///
"""Exercise a built explainer in headless Chromium and report what is broken.

    uv run d3x/check.py                       # checks dist/*.html, writes review/check.md
    uv run d3x/check.py --shots               # + one screenshot per interactive figure  -> review/shots/
    uv run d3x/check.py --shots --sections    # + tiled screenshots of every section     (costly to read; use on demand)
    uv run --with playwright playwright install chromium    # once per machine

Interactive figures fail silently: a NaN in a path, a slider that changes nothing, a formula KaTeX cannot
parse. This script moves every control to its extremes, clicks every preset and action, drags every handle,
steps through every derivation, and checks for page overflow at desktop and phone width.
Exit status 1 = at least one error.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ENGINE = Path(__file__).resolve().parent

HOOK = """
window.__errs = [];
window.addEventListener('error', e => window.__errs.push(String(e.message || e)));
window.addEventListener('unhandledrejection', e => window.__errs.push('unhandled rejection: ' + String(e.reason)));
(() => { const ce = console.error; console.error = function () { window.__errs.push([].map.call(arguments, String).join(' ')); ce.apply(console, arguments); }; })();
"""

AUDIT = r"""
async () => {
  const raf = () => new Promise(r => requestAnimationFrame(() => requestAnimationFrame(r)));
  const out = {widgets: [], katex: [], badChips: [], derivations: [], flows: []};
  const sig = fig => { const s = fig.querySelector('.stage svg'); return (s ? s.innerHTML.length + ':' + s.innerHTML.slice(0, 20000) : '') + '|' +
      [...fig.querySelectorAll('.ro, .dyn')].map(e => e.textContent).join('|'); };
  const problems = fig => {
    const bad = [], svg = fig.querySelector('.stage svg'); if (!svg) return ['no svg was created'];
    const marks = svg.querySelectorAll('path,line,circle,rect,text,polygon,polyline,ellipse').length;
    if (marks < 3) bad.push('stage is (nearly) empty: ' + marks + ' marks');
    for (const el of svg.querySelectorAll('*')) for (const a of el.attributes)
      if (/NaN|undefined|Infinity/.test(a.value)) { bad.push(`<${el.tagName} ${a.name}="${a.value.slice(0, 50)}"> contains NaN/undefined/Infinity`); break; }
    for (const t of svg.querySelectorAll('text')) if (/\$|\\[a-zA-Z]/.test(t.textContent)) { bad.push(`label "${t.textContent.slice(0, 40)}" shows raw TeX: SVG text cannot render math, write Unicode (κ, λ, q*)`); break; }
    for (const host of fig.querySelectorAll('.ctrls, .acts, .legend, .readouts, .dyn, figcaption, .flowdetail')) {
      const c = host.cloneNode(true); c.querySelectorAll('.katex, .katex-display').forEach(k => k.remove());
      const m = /\$[^$]{1,60}\$|\\[a-zA-Z]{2,}/.exec(c.textContent); if (m) { bad.push(`raw TeX "${m[0].slice(0, 40)}" is visible in the ${host.className.split(' ')[0] || host.tagName.toLowerCase()}: it was not rendered`); break; } }
    const vb = svg.viewBox.baseVal;
    for (const t of svg.querySelectorAll('text')) { if (t.getAttribute('transform')) continue; let b; try { b = t.getBBox(); } catch (e) { continue; }
      if (!b.width) continue;
      if (b.x < -1 || b.x + b.width > vb.width + 1 || b.y < -1 || b.y + b.height > vb.height + 1) bad.push(`label "${t.textContent.slice(0, 30)}" is cut off at the edge of the figure`); }
    return [...new Set(bad)].slice(0, 6);
  };
  const collisions = fig => { const out = [], svg = fig.querySelector('.stage svg'); if (!svg) return out;
    const boxes = [...svg.querySelectorAll('text')].filter(t => !t.getAttribute('transform') && t.textContent.trim()).map(t => { try { const b = t.getBBox(); return {t: t.textContent.trim(), x: b.x, y: b.y, w: b.width, h: b.height}; } catch (e) { return null; } }).filter(Boolean);
    for (let i = 0; i < boxes.length; i++) for (let j = i + 1; j < boxes.length; j++) { const a = boxes[i], b = boxes[j];
      const ox = Math.min(a.x + a.w, b.x + b.w) - Math.max(a.x, b.x), oy = Math.min(a.y + a.h, b.y + b.h) - Math.max(a.y, b.y);
      if (ox > 0 && oy > 0 && ox * oy > 0.35 * Math.min(a.w * a.h, b.w * b.h)) out.push(`labels "${a.t.slice(0, 24)}" and "${b.t.slice(0, 24)}" overlap`); }
    return out.slice(0, 4); };
  for (const fig of document.querySelectorAll('figure.widget')) {
    const id = fig.id, rec = {id, errors: [], warnings: [], controls: 0};
    const W = (window.D3X.widgets || []).find(w => w.id === id);
    if (!W) { rec.errors.push('never registered with D3X.widget / D3X.flow'); out.widgets.push(rec); continue; }
    if (W.kind === 'flow') {
      let clicked = 0; const detail = fig.querySelector('.flowdetail');
      for (const g of fig.querySelectorAll('g[data-node]')) { if (!g.style.cursor) continue; const before = detail.textContent;
        g.dispatchEvent(new MouseEvent('click', {bubbles: true})); await raf(); clicked++;
        if (detail.textContent === before && clicked > 1) rec.warnings.push(`node ${g.getAttribute('data-node')}: detail panel did not change`); }
      if (W.reset) { W.reset(); await raf(); }   // back to the default state for the screenshot
      const rects = [...fig.querySelectorAll('g[data-node]')].map(g => { const r = g.querySelector('rect'); return {id: g.getAttribute('data-node'), x0: +r.getAttribute('x') + 1, y0: +r.getAttribute('y') + 1, x1: +r.getAttribute('x') + +r.getAttribute('width') - 1, y1: +r.getAttribute('y') + +r.getAttribute('height') - 1}; });
      for (const e of fig.querySelectorAll('path[data-from]')) { let x = 0, y = 0; const segs = [];
        for (const t of e.getAttribute('d').match(/[MHV][^MHV]*/g) || []) { const v = t.slice(1).trim().split(/[ ,]+/).map(Number);
          if (t[0] === 'M') { x = v[0]; y = v[1]; } else if (t[0] === 'H') { segs.push([x, y, v[0], y]); x = v[0]; } else { segs.push([x, y, x, v[0]]); y = v[0]; } }
        for (const n of rects) { if (n.id === e.getAttribute('data-from') || n.id === e.getAttribute('data-to')) continue;
          if (segs.some(q => Math.max(q[0], q[2]) > n.x0 && Math.min(q[0], q[2]) < n.x1 && Math.max(q[1], q[3]) > n.y0 && Math.min(q[1], q[3]) < n.y1))
            rec.warnings.push(`edge ${e.getAttribute('data-from')} -> ${e.getAttribute('data-to')} runs through box "${n.id}"; move a node to another row or column`); } }
      rec.controls = clicked; rec.flow = true; if (!clicked) rec.warnings.push('no node has a detail text; a flow without details is a static picture');
      out.flows.push(id); out.widgets.push(rec); continue;
    }
    for (const pl of fig.querySelectorAll('.stage svg g.plot')) {
      const clip = pl.querySelector('clipPath rect'), series = [...pl.querySelectorAll('path[data-series]')]; if (!clip || !series.length) continue;
      const Hh = +clip.getAttribute('height'); let ext = 0; for (const q of series) { try { ext = Math.max(ext, q.getBBox().height); } catch (e) {} }
      if (ext > 0 && ext < 0.06 * Hh) rec.warnings.push(`the curves use only ${Math.round(100 * ext / Hh)} % of the panel height: the effect the caption describes may be invisible. Plot the difference instead of the levels, or narrow the axis (line plots may start above zero; say so in the panel title)`); }
    collisions(fig).forEach(m => rec.warnings.push(m + ' in the default state: move one with dx / dy / anchor, or name it in the legend'));
    const off = fig.querySelectorAll('.stage svg [data-offscale]').length; if (off) rec.warnings.push(`${off} point(s) lie off the scale in the default state and are drawn hollow at the edge: widen the axis or say so in the caption`);
    const e0 = window.__errs.length, seen = new Map();
    const note = (state, p) => { if (!seen.has(p)) seen.set(p, []); seen.get(p).push(state); };
    problems(fig).forEach(p => note('default', p));
    const cap = fig.querySelector('figcaption');
    if (!cap) rec.warnings.push('no figcaption');
    const base = sig(fig);
    for (const inp of fig.querySelectorAll('[data-param]')) {
      const k = inp.getAttribute('data-param'); rec.controls++;
      const states = [];
      const tryValue = async (label, apply) => { apply(); await raf(); states.push(sig(fig));
        problems(fig).forEach(p => note(`${k}=${label}`, p)); };
      if (inp.type === 'range') { const lo = +inp.min, hi = +inp.max, def = inp.value;
        for (const v of [lo, (lo + hi) / 2, hi]) await tryValue(v, () => { inp.value = v; inp.dispatchEvent(new Event('input', {bubbles: true})); });
        inp.value = def; inp.dispatchEvent(new Event('input', {bubbles: true})); await raf();
      } else if (inp.type === 'checkbox') { const def = inp.checked;
        for (const v of [!def, def]) await tryValue(v, () => { inp.checked = v; inp.dispatchEvent(new Event('change', {bubbles: true})); });
      } else if (inp.tagName === 'SELECT') { const def = inp.value;
        for (const o of inp.options) await tryValue(o.value, () => { inp.value = o.value; inp.dispatchEvent(new Event('change', {bubbles: true})); });
        inp.value = def; inp.dispatchEvent(new Event('change', {bubbles: true})); await raf(); }
      if (new Set(states).size < 2) rec.errors.push(`control "${k}" has no visible effect on the figure, the readouts, or the note`);
    }
    for (const b of fig.querySelectorAll('button[data-preset], button[data-action]')) {
      if (b.getAttribute('data-action') === 'reset') continue; rec.controls++;
      const before = sig(fig); b.click(); await raf();
      problems(fig).forEach(p => note(`after "${b.textContent}"`, p));
      if (sig(fig) === before && b.hasAttribute('data-action')) rec.warnings.push(`button "${b.textContent}" changed nothing`);
    }
    const reset = fig.querySelector('button[data-action="reset"]'); if (reset) { reset.click(); await raf(); }
    if (reset && sig(fig) !== base) rec.warnings.push('Reset does not restore the initial picture (is the draw function using Math.random or outside state?)');
    for (const [p, states] of seen) rec.errors.push(p + '  [' + (states.length > 4 ? states.slice(0, 4).join(', ') + ', +' + (states.length - 4) + ' more states' : states.join(', ')) + ']');
    window.__errs.slice(e0).forEach(m => rec.errors.push('console: ' + m.split('\n')[0].slice(0, 240)));
    rec.errors = [...new Set(rec.errors)].slice(0, 12);
    rec.handles = fig.querySelectorAll('.stage svg g.handle').length;
    rec.params = fig.querySelectorAll('[data-param]').length; rec.presets = fig.querySelectorAll('button[data-preset]').length;
    rec.actions = fig.querySelectorAll('button[data-action]:not([data-action="reset"])').length;
    if (rec.params > 4) rec.warnings.push(`${rec.params} parameters: more than four controls on one figure usually means two insights; split it or turn a parameter into a preset`);
    if (!rec.controls && !rec.handles) rec.warnings.push('no controls and no handles: this is a static figure; is interactivity earning its place here?');
    out.widgets.push(rec);
  }
  for (const e of document.querySelectorAll('.katex-error')) out.katex.push({src: e.textContent.slice(0, 120), msg: (e.getAttribute('title') || '').slice(0, 200),
    section: (e.closest('section') || {}).id || ''});
  // an unknown macro does not fail the formula: KaTeX prints the command name in the error colour
  for (const e of document.querySelectorAll('.katex [style*="color"]')) { const c = getComputedStyle(e).color;
    if (c === 'rgb(180, 87, 42)' && !out.katex.some(k => k.src === e.textContent.slice(0, 60))) out.katex.push({src: e.textContent.slice(0, 60), msg: 'unknown command; add it to [macros] in explainer.toml or rewrite it', section: (e.closest('section') || {}).id || ''}); }
  for (const c of document.querySelectorAll('.chip.bad')) out.badChips.push(c.textContent);
  for (const D of document.querySelectorAll('.derivation')) {
    const n = D.querySelectorAll('.dstep').length; let guard = 0; const next = D.querySelector('[data-next]');
    while (next && next.style.display !== 'none' && guard++ < 60) { next.click(); }
    const hidden = D.querySelectorAll('.dstep.hidden').length;
    out.derivations.push({title: D.getAttribute('data-title') || '', steps: n, ok: hidden === 0,
      nowhy: [...D.querySelectorAll('.dstep')].filter(s => !s.getAttribute('data-why')).length});
    const all = D.querySelector('[data-all]'); if (all && D.getAttribute('data-mode') !== 'open') all.click();
  }
  return out;
}
"""

OVERFLOW = r"""
() => {
  const vw = document.documentElement.clientWidth, out = [];
  const side = document.getElementById('side'), sr = side ? side.getBoundingClientRect() : null;
  const leftLimit = sr && sr.right > 0 && sr.left >= 0 ? sr.right : 0;          // the sidebar covers this strip on desktop
  for (const el of document.querySelectorAll('main *')) {
    const r = el.getBoundingClientRect(); if (r.width === 0 || r.height === 0) continue;
    if (r.left < leftLimit - 1 && !el.closest('svg') && getComputedStyle(el).position !== 'fixed') {
      out.push(`<${el.tagName.toLowerCase()} class="${String(el.className.baseVal ?? el.className).slice(0, 40)}"> in #${(el.closest('section') || {}).id || '?'} starts ${Math.round(leftLimit - r.left)}px left of the content area (hidden under the sidebar or off-screen)`);
      if (out.length >= 8) break; continue; }
    if (r.right <= vw + 1) continue;
    let p = el.parentElement, scrolls = false;
    for (; p && p !== document.body; p = p.parentElement) { const o = getComputedStyle(p).overflowX; if (o === 'auto' || o === 'scroll' || o === 'hidden') { scrolls = true; break; } }
    if (scrolls) continue;
    out.push(`<${el.tagName.toLowerCase()} class="${String(el.className.baseVal ?? el.className).slice(0, 40)}"> in #${(el.closest('section') || {}).id || '?'} extends ${Math.round(r.right - vw)}px past the viewport`);
    if (out.length >= 8) break;
  }
  return out;
}
"""


def drag_handles(page, report: dict) -> None:
    """Drag every handle by 40 px with the real mouse: handles depend on pointer capture, which synthetic events cannot test."""
    for rec in report["widgets"]:
        if not rec.get("handles"):
            continue
        fig = page.locator(f"figure#{rec['id']}")
        fig.scroll_into_view_if_needed()
        n = fig.locator(".stage svg g.handle").count()
        for i in range(n):
            h = fig.locator(".stage svg g.handle").nth(i)
            box = h.bounding_box()
            if not box:
                continue
            cx, cy = box["x"] + box["width"] / 2, box["y"] + box["height"] / 2
            before = fig.locator(".stage svg").inner_html()
            page.mouse.move(cx, cy)
            page.mouse.down()
            page.mouse.move(cx + 40, cy - 30, steps=4)
            page.mouse.up()
            page.wait_for_timeout(80)
            if fig.locator(".stage svg").inner_html() == before:
                rec["errors"].append(f"handle {i + 1} does not respond to dragging")
        reset = fig.locator('button[data-action="reset"]')
        if reset.count():
            reset.first.click()


def shoot(page, outdir: Path, sections: bool) -> list[str]:
    outdir.mkdir(parents=True, exist_ok=True)
    for old in outdir.glob("*.png"):
        if sections or not old.name.startswith("sec-"):
            old.unlink()
    made = []
    for fig in page.locator("figure.widget").all():
        fid = fig.get_attribute("id")
        fig.scroll_into_view_if_needed()
        path = outdir / f"{fid}.png"
        fig.screenshot(path=str(path))
        made.append(path.name)
    if sections:
        page.add_style_tag(content="#progress,#menu{display:none!important}")     # fixed elements smear across full-page clips
        for sec in page.locator("main > section").all():
            sid = sec.get_attribute("id")
            box = sec.bounding_box()
            if not box:
                continue
            main = page.locator("main").bounding_box()          # wide figures and tables extend beyond the text column
            box["x"], box["width"] = main["x"], main["width"]
            top, k = box["y"] + page.evaluate("window.scrollY"), 0
            while k * 1400 < box["height"]:
                h = min(1400, box["height"] - k * 1400)
                path = outdir / f"sec-{sid}-{k + 1}.png"
                page.screenshot(path=str(path), full_page=True, clip={"x": box["x"], "y": top + k * 1400, "width": box["width"], "height": h})
                made.append(path.name)
                k += 1
    return made


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("html", nargs="?", help="built file (default: the newest dist/*.html next to d3x/)")
    ap.add_argument("--shots", action="store_true", help="screenshot every interactive figure into review/shots/")
    ap.add_argument("--sections", action="store_true", help="with --shots: also tile every section (many images)")
    ap.add_argument("--out", default=None, help="review folder (default: <project>/review)")
    a = ap.parse_args()

    if a.html:
        target = Path(a.html).resolve()
    else:
        built = sorted((ENGINE.parent / "dist").glob("*.html"), key=lambda p: p.stat().st_mtime)
        if not built:
            sys.exit("error: no dist/*.html; run build.py first")
        target = built[-1]
    review = Path(a.out).resolve() if a.out else target.parent.parent / "review"
    review.mkdir(parents=True, exist_ok=True)

    from playwright.sync_api import Error, sync_playwright

    with sync_playwright() as pw:
        browser, first = None, ""
        for kw in ({}, {"channel": "chrome"}, {"channel": "msedge"}):      # bundled Chromium, else an installed Chrome / Edge
            try:
                browser = pw.chromium.launch(**kw)
                break
            except Error as e:
                first = first or str(e).splitlines()[0]
        if browser is None:
            sys.exit(f"error: no browser available to Playwright ({first}).\n"
                     "Install one once per machine:  uv run --with playwright playwright install chromium")
        ctx = browser.new_context(viewport={"width": 1280, "height": 900}, device_scale_factor=1)
        page = ctx.new_page()
        page.add_init_script(HOOK)
        page.goto(target.as_uri())
        try:
            page.wait_for_function("window.D3X_READY === true", timeout=15000)
        except Error:
            print("ERROR  the page never finished booting (window.D3X_READY is not set); a script error stops everything after it")
            for m in page.evaluate("window.__errs || []")[:10]:
                print("       console:", m[:300])
            return 1
        page.wait_for_timeout(150)
        boot_errs = page.evaluate("window.__errs.slice()")
        report = page.evaluate(AUDIT)
        drag_handles(page, report)
        overflow = {"1280": page.evaluate(OVERFLOW)}
        page.set_viewport_size({"width": 390, "height": 800})
        page.wait_for_timeout(450)          # the figures redraw in their narrow layout after a resize
        overflow["390"] = page.evaluate(OVERFLOW)
        tiny = page.evaluate("""() => { const out = [];
          for (const fig of document.querySelectorAll('figure.widget')) { const svg = fig.querySelector('.stage svg'); if (!svg || !svg.viewBox.baseVal.width) continue;
            const k = svg.clientWidth / svg.viewBox.baseVal.width; let min = 99;
            for (const t of svg.querySelectorAll('text')) min = Math.min(min, (parseFloat(t.getAttribute('font-size')) || 12) * k);
            if (min < 7) out.push(`${fig.id}: text renders at ${min.toFixed(1)} px on a phone`); } return out; }""")
        page.set_viewport_size({"width": 1280, "height": 900})
        page.wait_for_timeout(120)
        shots = shoot(page, review / "shots", a.sections) if a.shots else []
        browser.close()

    errors, warnings, lines = 0, 0, [f"# Check report: {target.name}", ""]
    if boot_errs:
        lines.append("## Script errors while loading")
        for m in dict.fromkeys(boot_errs):
            lines.append(f"- ERROR {m[:400]}")
            errors += 1
        lines.append("")
    lines.append("## Interactive figures")
    if not report["widgets"]:
        lines.append("- (none)")
    for rec in report["widgets"]:
        status = "ERROR" if rec["errors"] else ("warn" if rec["warnings"] else "ok")
        what = f"{rec['controls']} boxes with detail" if rec.get("flow") else ", ".join(f"{rec.get(k, 0)} {k}" for k in ("params", "presets", "actions", "handles") if rec.get(k))
        lines.append(f"- **{rec['id']}**: {status} ({what or 'no controls'})")
        for m in rec["errors"]:
            lines.append(f"  - ERROR {m}")
            errors += 1
        for m in rec["warnings"]:
            lines.append(f"  - warning {m}")
            warnings += 1
    lines += ["", "## Math"]
    if report["katex"]:
        for k in report["katex"]:
            lines.append(f"- ERROR KaTeX cannot render `{k['src']}` in #{k['section']}: {k['msg']}")
            errors += 1
    else:
        lines.append("- all formulas render")
    lines += ["", "## Derivations"]
    for d in report["derivations"]:
        ok = "ok" if d["ok"] else "ERROR steps remain hidden after clicking through"
        errors += 0 if d["ok"] else 1
        lines.append(f"- {d['title'] or '(untitled)'}: {d['steps']} steps, {ok}")
        if d["nowhy"]:
            lines.append(f"  - warning {d['nowhy']} step(s) have no data-why; a step without a reason is a line of algebra, not an explanation")
            warnings += 1
        if d["steps"] > 9:
            lines.append(f"  - warning {d['steps']} steps is long; group routine algebra into one step or fold the tail into <details>")
            warnings += 1
    if not report["derivations"]:
        lines.append("- (none)")
    lines += ["", "## Source chips"]
    if report["badChips"]:
        for c in report["badChips"]:
            lines.append(f"- ERROR unresolved chip: {c}")
            errors += 1
    else:
        lines.append("- all chips resolved at build time")
    lines += ["", "## Page overflow"]
    for width, items in overflow.items():
        if items:
            for m in items:
                lines.append(f"- ERROR at {width}px: {m}")
                errors += 1
        else:
            lines.append(f"- {width}px: clean")
    if tiny:
        lines += ["", "## Phone legibility"] + [f"- warning {m}: unreadable. Figures with plots adapt on their own; a fixed or hand-drawn figure this wide needs a simpler phone version (ctx.narrow) or fewer labels" for m in tiny]
        warnings += len(tiny)
    if shots:
        lines += ["", "## Screenshots", f"- {len(shots)} files in {review / 'shots'}"]
    lines += ["", f"**{errors} error(s), {warnings} warning(s)**"]
    text = "\n".join(lines) + "\n"
    (review / "check.md").write_text(text, encoding="utf-8")
    print(text, end="")          # the verdict must be the last line, so that `| tail -1` shows it
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
