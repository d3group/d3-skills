#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Render every slide AND every step of a built deck, audit for overflow, export a PDF.

    uv run --with playwright --with pillow d3deck/shoot.py dist/my_talk.html                # every slide, every step -> shots/
    uv run --with playwright --with pillow d3deck/shoot.py dist/my_talk.html --from 3 --to 8
    uv run --with playwright --with pillow d3deck/shoot.py dist/my_talk.html --contact       # + contact sheets (needs Pillow)
    uv run --with playwright --with pillow d3deck/shoot.py dist/my_talk.html --pdf dist/my_talk.pdf
    uv run --with playwright --with pillow d3deck/shoot.py dist/my_talk.html --slot 15      # time budget against a 15-minute slot
    uv run --with playwright --with pillow d3deck/shoot.py dist/my_talk.html --from 4 --to 4 --live --wait 1500   # a replay mid-flight
    uv run d3deck/shoot.py dist/my_talk.html --chrome        # headless Chrome instead of Playwright
    uv run --with playwright playwright install chromium   # once per machine

Exit status is 1 on overflow, on a formula MathJax cannot render, on an emoji or
dingbat in visible text, and on console errors or failed requests, so this can
gate a build. The other LINT findings (holes, wordy slides, Greek letters in
uppercase labels) are warnings. Every finding also lands in <shots>/report.json.

Every shot shows the end state: after the settle wait, the running CSS animations
of the slide are finished (infinite ones cancelled, so the base style shows),
because the base style of every animated element is its end state. --live
shoots what is on screen instead; add --wait to catch a replay mid-flight.

The last lines are the deck's signature: how many content slides build, move,
carry a designed object, and respond to the presenter, plus the text-only slides.

Four things this script exists to get right (from the colleague's deck):
  * it shoots every STEP, since end states hide build bugs;
  * it waits out the 420 ms ghost transition before each shot;
  * it selects slides with '.sl' and audits against the slide box AND against
    the .body/.col boxes, whose overflow is cropped and therefore invisible;
  * it uses checkVisibility({opacityProperty, visibilityProperty}) so hidden
    ancestors do not produce false overflows.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys

SETTLE_MS = 480          # ghost transition is 420 ms; never go below ~450
VIEWPORT = {'width': 1320, 'height': 830}

AUDIT_JS = """(tol) => {
  const s = document.querySelector('.sl.on'); if (!s) return [];
  const box = s.getBoundingClientRect(); const out = [];
  const label = el => ({tag: el.tagName.toLowerCase(),
    cls: (el.className && el.className.baseVal !== undefined ? el.className.baseVal : String(el.className || '')).slice(0, 60),
    text: (el.textContent || '').trim().replace(/\\s+/g, ' ').slice(0, 60)});
  for (const el of s.querySelectorAll('*')) {
    if (!el.checkVisibility({opacityProperty: true, visibilityProperty: true})) continue;
    const r = el.getBoundingClientRect(); if (r.width === 0 && r.height === 0) continue;
    const host = el.closest('.body,.col');
    if (host && !el.matches('.body,.col')) {
      const b = host.getBoundingClientRect();
      const neg = {left: b.left - r.left, top: b.top - r.top};
      const worstNeg = Object.entries(neg).filter(([, v]) => v > tol).sort((x, y) => y[1] - x[1])[0];
      if (worstNeg) out.push(Object.assign({side: worstNeg[0], px: Math.round(worstNeg[1])}, label(el), {text: 'content above or left of its box (cropped)'}));
      continue;
    }
    const over = {left: box.left - r.left, right: r.right - box.right, top: box.top - r.top, bottom: r.bottom - box.bottom};
    const worst = Object.entries(over).filter(([, v]) => v > tol).sort((a, b) => b[1] - a[1])[0];
    if (worst) out.push(Object.assign({side: worst[0], px: Math.round(worst[1])}, label(el)));
  }
  for (const b of s.querySelectorAll('.body,.col')) {
    const dh = b.scrollHeight - b.clientHeight, dw = b.scrollWidth - b.clientWidth;
    if (dh > tol) out.push(Object.assign({side: 'bottom', px: Math.round(dh)}, label(b), {text: 'content taller than its box (cropped)'}));
    if (dw > tol) out.push(Object.assign({side: 'right', px: Math.round(dw)}, label(b), {text: 'content wider than its box (cropped)'}));
  }
  return out;
}"""


# Lint of one slide at its final step. Content = visible elements that have own text, are replaced elements,
# or draw a box (background or border); containers that only lay out do not count, so a centred block is
# measured by what is in it, not by its full-height wrapper.
LINT_JS = r"""(o) => {
  const s = document.querySelector('.sl.on'); if (!s) return [];
  const out = [];
  const vis = el => el.checkVisibility({opacityProperty: true, visibilityProperty: true});
  const cls = el => (el.className && el.className.baseVal !== undefined ? el.className.baseVal : String(el.className || ''));
  const label = el => ({tag: el.tagName.toLowerCase(), cls: cls(el).slice(0, 60),
    text: (el.textContent || '').trim().replace(/\s+/g, ' ').slice(0, 60)});
  const CHROME = '.kf-foot,.trk,.stepdots,.fr-foot,.fr-num,.prov,.fr-uni,.fr-d3,.fr-d3t,.fr-bar,.fr-tab';
  const texts = [];
  const w = document.createTreeWalker(s, NodeFilter.SHOW_TEXT);
  for (let n = w.nextNode(); n; n = w.nextNode()) {
    const p = n.parentElement;
    if (!p || !n.nodeValue.trim() || p.closest('mjx-container,script,style') || !vis(p)) continue;
    texts.push([n, p]);
  }
  const seen = new Set();
  const add = (el, level, kind, msg) => { const key = kind + '|' + msg; if (seen.has(key)) return; seen.add(key);
    out.push(Object.assign(label(el), {level, kind, msg})); };
  /* emoji and dingbats standing in for icons; typographic arrows are fine */
  const EMO = /[☀-➿⭐⭕]|[\u{1F300}-\u{1FAFF}]/u;
  const ICON = {'✓': 'check', '✔': 'check', '✅': 'check', '✕': 'x', '✖': 'x', '✗': 'x',
    '✘': 'x', '❌': 'x', '⚠': 'alert', '❗': 'alert', '⛔': 'xcircle', '➔': 'arrowr', '➜': 'arrowr'};
  for (const [n, p] of texts) {
    const m = n.nodeValue.match(EMO);
    if (m) add(p, 'error', 'emoji', `emoji/dingbat "${m[0]}" in visible text; use an inline icon: icon('${ICON[m[0]] || '...'}')`);
  }
  /* lowercase Greek inside an uppercase label prints as a capital: alpha becomes A */
  const GR = /[α-ωϑϕϖϵ]/;
  for (const [n, p] of texts) {
    const m = n.nodeValue.match(GR);
    if (m && getComputedStyle(p).textTransform === 'uppercase')
      add(p, 'warn', 'greek-caps', `${m[0]} prints as ${m[0].toUpperCase()}; wrap the symbol in <span class="nocaps">`);
  }
  /* wordy: visible words outside the chrome, a formula counts as one */
  let words = 0;
  for (const [n, p] of texts) if (!p.closest(CHROME)) words += n.nodeValue.trim().split(/\s+/).filter(Boolean).length;
  words += [...s.querySelectorAll('mjx-container')].filter(m => !m.closest(CHROME) && vis(m)).length;
  if (words > o.maxWords) add(s, 'warn', 'wordy', `wordy: ${words} words on the slide; keep about 40 and move sentences to notes=`);
  /* hole: content glued to the top of its region with empty space below */
  if (o.hole && !s.querySelector('.stmt')) {
    const boxes = [...s.querySelectorAll('.body,.col')].filter(b => { const r = b.getBoundingClientRect(); return r.width > 60 && r.height > 60; });
    if (boxes.length) {
      const rtop = Math.min(...boxes.map(b => b.getBoundingClientRect().top));
      const rbot = Math.max(...boxes.map(b => b.getBoundingClientRect().bottom));
      const REPLACED = new Set(['img', 'svg', 'canvas', 'video', 'input', 'button', 'select', 'textarea', 'hr', 'mjx-container']);
      const isContent = el => {
        const t = el.tagName.toLowerCase();
        if (REPLACED.has(t)) return true;
        for (const c of el.childNodes) if (c.nodeType === 3 && c.nodeValue.trim()) return true;
        const cs = getComputedStyle(el);
        if (cs.backgroundImage !== 'none' || (cs.backgroundColor !== 'rgba(0, 0, 0, 0)' && cs.backgroundColor !== 'transparent')) return true;
        return ['Top', 'Right', 'Bottom', 'Left'].some(k => parseFloat(cs['border' + k + 'Width']) > 0 && cs['border' + k + 'Style'] !== 'none');
      };
      const cands = [];
      for (const b of boxes) cands.push(...b.querySelectorAll('*'));
      cands.push(...s.querySelectorAll('.take'));
      let top = Infinity, bottom = -Infinity, low = null;
      for (const el of cands) {
        const m = el.closest('mjx-container'); if (m && m !== el) continue;
        const sv = el.closest('svg'); if (sv && sv !== el) continue;
        if (!vis(el) || !isContent(el)) continue;
        const r = el.getBoundingClientRect(); if (r.width === 0 || r.height === 0) continue;
        top = Math.min(top, r.top);
        if (r.bottom > bottom) { bottom = r.bottom; low = el; }
      }
      if (low) {
        const H = rbot - rtop, gapB = rbot - bottom, gapT = top - rtop;
        if (gapB > o.holeFrac * H && gapT < 0.5 * gapB)
          add(low, 'warn', 'hole', `hole: content ends ${Math.round(gapB)} px above the bottom of its region; fill the region or centre it`);
      }
    }
  }
  return out;
}"""

# What the signature counts on one slide at its final step. Chrome (logos, tracker, foot) and formulas are not objects;
# a statement() slide is a deliberate one-sentence design and counts as one.
SIGNATURE_JS = r"""() => {
  const s = document.querySelector('.sl.on');
  const CHROME = '.kf-foot,.trk,.stepdots,.fr-foot,.fr-num,.prov,.fr-uni,.fr-d3,.fr-d3t,.fr-bar,.fr-tab';
  const OBJ = 'img, svg:not(.ico), table, pre, .chev, .tl, .stat, .facts, .bignum, .stmt, [class^="k-"], [class*=" k-"]';
  const own = el => !el.closest(CHROME) && !el.closest('mjx-container');
  return {obj: [...s.querySelectorAll(OBJ)].some(own),
          inter: [...s.querySelectorAll('[data-k],[data-pop],.cite,button,input,select')].filter(own).length};
}"""

# show(i, s) and count the CSS animations that start on the slide (transitions of the ghosting do not count)
SHOW_JS = """([i, s]) => { show(i, s); const sl = document.querySelector('.sl.on');
  return document.getAnimations().filter(a => typeof CSSAnimation !== 'undefined' && a instanceof CSSAnimation &&
    a.effect && a.effect.target && sl.contains(a.effect.target) && a.playState !== 'finished').length; }"""

# jump every animation and transition of the slide to its end; infinite loops are cancelled, so the base style shows
FINISH_JS = """() => { const sl = document.querySelector('.sl.on'); let n = 0;
  for (const a of document.getAnimations()) { const t = a.effect && a.effect.target; if (!t || !sl.contains(t)) continue;
    try { a.finish(); } catch (e) { a.cancel(); } n++; } return n; }"""

MAX_WORDS = 100      # wordy above this many visible words (the build already warns above 75 body words)
HOLE_FRAC = 0.30     # hole when the content ends more than this share of the region above its bottom


def fmt_time(sec):
    sec = int(round(sec))
    return f'{sec // 60}:{sec % 60:02d}'


def budget(meta, slot=None):
    """-> dict with the summed time budget, the slot and the presented content slides that carry no time."""
    total = sum(int(m.get('tm') or 0) for m in meta)
    main = [m for m in meta if m.get('k') == 'content' and not str(m.get('f', '')).startswith('backup')]
    timed = [m for m in main if m.get('tm')]
    untimed = [m['i'] + 1 for m in main if not m.get('tm')] if timed else []
    b = {'total_s': total, 'slot_s': int(slot * 60) if slot else None, 'untimed': untimed}
    b['over_s'] = total - b['slot_s'] if slot and total > b['slot_s'] else 0
    return b


def run_playwright(deck, out_dir, first, last, tol, scale, contact, pdf, live=False, wait=0, slot=None):
    from playwright.sync_api import sync_playwright

    os.makedirs(out_dir, exist_ok=True)
    problems, shots, lint, console = [], [], [], []
    moving, sig = set(), {}
    with sync_playwright() as p:
        try:
            browser = p.chromium.launch()
        except Exception as exc:   # Chromium not installed for Playwright
            sys.exit(f'Playwright could not launch Chromium ({exc.__class__.__name__}). '
                     'Run: uv run --with playwright playwright install chromium   or use --chrome')
        page = browser.new_page(viewport=VIEWPORT, device_scale_factor=scale)
        page.on('console', lambda m: m.type == 'error' and console.append(f'console error: {m.text}'))
        page.on('pageerror', lambda e: console.append(f'uncaught: {e}'))
        page.on('requestfailed', lambda r: console.append(f'request failed: {r.url} ({r.failure})'))
        page.goto('file://' + os.path.abspath(deck))
        page.wait_for_timeout(1500)          # fonts, base64 figures
        page.wait_for_function('window.D3_MATH_READY !== false', timeout=30000)   # MathJax, when the deck embeds it
        n = page.evaluate('N')
        meta = page.evaluate('META')
        lo = max(0, (first - 1) if first else 0)
        hi = min(n, last if last else n)
        print(f'{deck}: {n} slides, shooting {lo + 1}..{hi}')
        for i in range(lo, hi):
            k = page.evaluate(f'(() => {{ show({i}, 0); return steps({i}); }})()')
            m = meta[i]
            content = m.get('k') == 'content'
            backup = str(m.get('f', '')).startswith('backup')
            for s in range(k):
                if page.evaluate(SHOW_JS, [i, s]):
                    moving.add(i)
                page.wait_for_timeout(SETTLE_MS + wait)
                if not live:
                    page.evaluate(FINISH_JS)
                page.evaluate("document.querySelectorAll('.sl').forEach(x => x.style.transform = 'translate(-50%,-50%) scale(1)')")
                path = os.path.join(out_dir, f'{i + 1:03d}_{s + 1}.png')
                page.locator('.sl.on').screenshot(path=path)
                shots.append(path)
                for hit in page.evaluate(AUDIT_JS, tol):
                    problems.append((i + 1, s + 1, hit))
                if content and s == k - 1:
                    for hit in page.evaluate(LINT_JS, {'hole': not backup, 'maxWords': MAX_WORDS, 'holeFrac': HOLE_FRAC}):
                        lint.append((i + 1, s + 1, hit))
                    if not backup:
                        sig[i] = page.evaluate(SIGNATURE_JS)
            print(f'  slide {i + 1:3d}  {k} step(s)', end='\r', flush=True)
        math_errors = page.evaluate("""() => [...document.querySelectorAll('.sl')].flatMap((s, i) =>
            [...s.querySelectorAll('mjx-container svg [data-mjx-error]')].filter(e => !e.parentElement.closest('[data-mjx-error]'))
              .map(e => [i + 1, e.getAttribute('data-mjx-error'), e.textContent.replace(e.getAttribute('data-mjx-error'), '').trim().slice(0, 60)]))""")
        if pdf:
            page.emulate_media(media='print')
            page.pdf(path=pdf, width='1280px', height='720px', print_background=True, prefer_css_page_size=True)
            print(f'\nPDF -> {pdf}')
        browser.close()
    print(f'\n{len(shots)} shots -> {out_dir}')
    if problems:
        print(f'\nOVERFLOW: {len(problems)} element(s) outside their box\n')
        for slide, step, h in problems:
            print(f'  {slide:3d}.{step}  {h["px"]:4d}px {h["side"]:<6s} {h["tag"]}.{h["cls"]}  "{h["text"]}"')
    else:
        print('overflow audit: clean')
    if math_errors:
        print(f'\nMATH: {len(math_errors)} formula(s) MathJax cannot render\n')
        for slide, msg, src in math_errors:
            print(f'  {slide:3d}    {msg}  "{src}"')
    errors = [x for x in lint if x[2]['level'] == 'error']
    if lint:
        print(f'\nLINT: {len(lint)} finding(s), {len(errors)} error(s)\n')
        for slide, step, h in lint:
            print(f'  {slide:3d}.{step}  {h["level"]:<5s} {h["msg"]}  {h["tag"]}.{h["cls"]}  "{h["text"]}"')
    if console:
        print(f'\nCONSOLE: {len(console)} error(s)\n')
        for line in console:
            print(f'  {line}')
    b = budget(meta, slot)
    if b['total_s'] or slot:
        print('\nbudget ' + fmt_time(b['total_s']) + (f' of {fmt_time(b["slot_s"])} slot' if slot else ''))
        if b['over_s']:
            print(f'  over the slot by {fmt_time(b["over_s"])}: cut slides or move them to the backup')
        if b['untimed']:
            print('  no time= on content slides ' + ', '.join(map(str, b['untimed'])) + ' while others carry one')
    signature = {'content': len(sig), 'builds': sum(1 for i in sig if meta[i].get('st', 1) > 1),
                 'motion': sum(1 for i in sig if i in moving), 'objects': sum(1 for v in sig.values() if v['obj']),
                 'interactive': sum(v['inter'] for v in sig.values()), 'interactive_slides': sum(1 for v in sig.values() if v['inter']),
                 'text_only': [i + 1 for i in sorted(sig) if not sig[i]['obj']]}
    if sig:
        part = '' if (lo == 0 and hi == n) else f'  (slides {lo + 1}..{hi})'
        print(f'\nsignature  {signature["content"]} content slides · {signature["builds"]} with builds · '
              f'{signature["motion"]} with motion · {signature["objects"]} with a designed object · '
              f'{signature["interactive"]} interactive elements on {signature["interactive_slides"]} slides{part}')
        if signature['text_only']:
            print('text only: ' + ', '.join(map(str, signature['text_only'])) + '  (give each a designed object)')
    report = {'deck': os.path.abspath(deck), 'slides': n, 'shots': len(shots),
              'overflow': [dict(slide=a, step=b_, **h) for a, b_, h in problems],
              'math': [dict(slide=a, error=e, source=src) for a, e, src in math_errors],
              'lint': [dict(slide=a, step=b_, **h) for a, b_, h in lint],
              'console': console, 'signature': signature, 'budget': b}
    with open(os.path.join(out_dir, 'report.json'), 'w', encoding='utf-8') as fh:
        json.dump(report, fh, ensure_ascii=False, indent=1)
    if contact:
        make_contact_sheets(shots, out_dir)
    return 1 if problems or math_errors or errors or console else 0


def chrome_binary():
    cands = [os.environ.get('CHROME'),
             '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
             '/Applications/Chromium.app/Contents/MacOS/Chromium',
             shutil.which('google-chrome'), shutil.which('chromium'), shutil.which('chromium-browser')]
    return next((c for c in cands if c and os.path.exists(c)), None)


def run_chrome(deck, out_dir, first, last, contact):
    """Fallback without Playwright: one headless-Chrome run per step via ?shot#slide.step. No audit."""
    chrome = chrome_binary()
    if not chrome:
        sys.exit('no Chrome found; set $CHROME, or run without --chrome: uv run --with playwright --with pillow d3deck/shoot.py ... '
                 '(first time: uv run --with playwright playwright install chromium)')
    os.makedirs(out_dir, exist_ok=True)
    with open(deck, encoding='utf-8') as fh:
        html = fh.read()
    steps = [int(x) for x in re.findall(r'<section class="sl[^"]*" data-steps="(\d+)"', html)]
    n = len(steps)
    lo = max(0, (first - 1) if first else 0)
    hi = min(n, last if last else n)
    print(f'{deck}: {n} slides, shooting {lo + 1}..{hi} with headless Chrome')
    shots = []
    for i in range(lo, hi):
        for s in range(steps[i]):
            path = os.path.abspath(os.path.join(out_dir, f'{i + 1:03d}_{s + 1}.png'))
            url = f'file://{os.path.abspath(deck)}?shot#{i + 1}.{s + 1}'
            subprocess.run([chrome, '--headless=new', '--disable-gpu', '--hide-scrollbars', '--window-size=1280,720',
                            '--virtual-time-budget=2000', f'--screenshot={path}', url],
                           check=True, capture_output=True)
            shots.append(path)
        print(f'  slide {i + 1:3d}  {steps[i]} step(s)', end='\r', flush=True)
    print(f'\n{len(shots)} shots -> {out_dir}\nno overflow audit in --chrome mode; look at the shots')
    if contact:
        make_contact_sheets(shots, out_dir)
    return 0


def make_contact_sheets(shots, out_dir, cols=4, rows=3, thumb_w=480):
    """Tile the shots into browsable sheets. Look at these: the eye catches what the audit does not."""
    try:
        from PIL import Image
    except ImportError:
        print('\n(contact sheets skipped: rerun with uv run --with playwright --with pillow d3deck/shoot.py ...)')
        return
    per = cols * rows
    th = int(thumb_w * 720 / 1280)
    for page, start in enumerate(range(0, len(shots), per), 1):
        sheet = Image.new('RGB', (cols * thumb_w, rows * th), 'white')
        for j, path in enumerate(shots[start:start + per]):
            im = Image.open(path).convert('RGB').resize((thumb_w, th), Image.LANCZOS)
            sheet.paste(im, ((j % cols) * thumb_w, (j // cols) * th))
        dest = os.path.join(out_dir, f'contact_{page:02d}.png')
        sheet.save(dest)
        print(f'  contact sheet -> {dest}')


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('deck', help='the built deck, e.g. dist/my_talk.html')
    ap.add_argument('-o', '--out', default=None, help='shots folder (default: <talk>/shots)')
    ap.add_argument('--from', dest='first', type=int, help='first slide (1-based)')
    ap.add_argument('--to', dest='last', type=int, help='last slide (1-based, inclusive)')
    ap.add_argument('--tol', type=float, default=2.0, help='overflow tolerance in px')
    ap.add_argument('--scale', type=int, default=1, help='device scale factor for the shots (2 = retina)')
    ap.add_argument('--contact', action='store_true', help='also write contact sheets')
    ap.add_argument('--pdf', default=None, help='also export the print view to this PDF path')
    ap.add_argument('--chrome', action='store_true', help='use headless Chrome instead of Playwright (no audit)')
    ap.add_argument('--live', action='store_true', help='do not finish running animations; shoot what is on screen')
    ap.add_argument('--wait', type=int, default=0, help='extra ms to wait before each shot (time-lapse with --live)')
    ap.add_argument('--slot', type=float, default=None, help='talk slot in minutes; compares the summed time= budgets')
    a = ap.parse_args()
    if not os.path.exists(a.deck):
        sys.exit(f'no such deck: {a.deck} (run uv run slides.py first)')
    out = a.out or os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(a.deck))), 'shots')
    if a.chrome:
        sys.exit(run_chrome(a.deck, out, a.first, a.last, a.contact))
    try:
        import playwright  # noqa: F401
    except ImportError:
        print('playwright not installed (run: uv run --with playwright --with pillow d3deck/shoot.py ...); falling back to --chrome')
        sys.exit(run_chrome(a.deck, out, a.first, a.last, a.contact))
    sys.exit(run_playwright(a.deck, out, a.first, a.last, a.tol, a.scale, a.contact, a.pdf, a.live, a.wait, a.slot))


if __name__ == '__main__':
    main()
