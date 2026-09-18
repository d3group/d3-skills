#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Render every slide AND every step of a built deck, audit for overflow, export a PDF.

    uv run --with playwright --with pillow d3deck/shoot.py dist/my_talk.html                # every slide, every step -> shots/
    uv run --with playwright --with pillow d3deck/shoot.py dist/my_talk.html --from 3 --to 8
    uv run --with playwright --with pillow d3deck/shoot.py dist/my_talk.html --contact       # + contact sheets (needs Pillow)
    uv run --with playwright --with pillow d3deck/shoot.py dist/my_talk.html --pdf dist/my_talk.pdf
    uv run d3deck/shoot.py dist/my_talk.html --chrome        # headless Chrome instead of Playwright
    uv run --with playwright playwright install chromium   # once per machine

Exit status is 1 if anything overflowed, so this can gate a build.

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


def run_playwright(deck, out_dir, first, last, tol, scale, contact, pdf):
    from playwright.sync_api import sync_playwright

    os.makedirs(out_dir, exist_ok=True)
    problems, shots = [], []
    with sync_playwright() as p:
        try:
            browser = p.chromium.launch()
        except Exception as exc:   # Chromium not installed for Playwright
            sys.exit(f'Playwright could not launch Chromium ({exc.__class__.__name__}). '
                     'Run: uv run --with playwright playwright install chromium   or use --chrome')
        page = browser.new_page(viewport=VIEWPORT, device_scale_factor=scale)
        page.goto('file://' + os.path.abspath(deck))
        page.wait_for_timeout(1500)          # fonts, base64 figures
        page.wait_for_function('window.D3_MATH_READY !== false', timeout=30000)   # MathJax, when the deck embeds it
        n = page.evaluate('N')
        lo = max(0, (first - 1) if first else 0)
        hi = min(n, last if last else n)
        print(f'{deck}: {n} slides, shooting {lo + 1}..{hi}')
        for i in range(lo, hi):
            k = page.evaluate(f'(() => {{ show({i}, 0); return steps({i}); }})()')
            for s in range(k):
                page.evaluate(f'show({i}, {s})')
                page.wait_for_timeout(SETTLE_MS)
                page.evaluate("document.querySelectorAll('.sl').forEach(x => x.style.transform = 'translate(-50%,-50%) scale(1)')")
                path = os.path.join(out_dir, f'{i + 1:03d}_{s + 1}.png')
                page.locator('.sl.on').screenshot(path=path)
                shots.append(path)
                for hit in page.evaluate(AUDIT_JS, tol):
                    problems.append((i + 1, s + 1, hit))
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
    if contact:
        make_contact_sheets(shots, out_dir)
    return 1 if problems or math_errors else 0


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
    sys.exit(run_playwright(a.deck, out, a.first, a.last, a.tol, a.scale, a.contact, a.pdf))


if __name__ == '__main__':
    main()
