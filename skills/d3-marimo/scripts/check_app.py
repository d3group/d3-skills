#!/usr/bin/env python3
"""Check a marimo teaching app the way students will use it.

    uv run --with playwright check_app.py apps/my-app.py --expect "The best plan"
    uv run --with playwright check_app.py apps/my-app.py --expect "Model 1" --click "tab:Whole items" --expect-after "16.00"
    uv run --with playwright check_app.py --live https://chrisflath.github.io/apps/my-app.html --expect "Model 1"

Steps (local mode):
  1. native run: `marimo export html` executes every cell; any failing cell fails the check
  2. WASM export: `marimo export html-wasm --mode run --no-show-code` into a temporary folder
  3. serve it on localhost and open it in headless Chromium
  4. wait until --expect text is visible; perform --click actions; check --expect-after texts
  5. report console errors and the computed heading font (to catch a missing style cell)
The first run on a machine needs `uv run --with playwright playwright install chromium`.
Dependencies for step 1 are read from the app's inline script metadata (# /// script).
"""
import argparse
import functools
import http.server
import re
import shutil
import subprocess
import sys
import tempfile
import threading
import time
from pathlib import Path


def deps(app: Path):
    m = re.search(r"# /// script\n(.*?)# ///", app.read_text(), re.S)
    return re.findall(r'#\s+"([^"]+)"', m.group(1)) if m else ["marimo"]


def native(app: Path):
    withs = [x for d in deps(app) if not d.startswith("marimo") for x in ("--with", d.split("=")[0].split(">")[0])]
    out = Path(tempfile.mkdtemp()) / "native.html"
    r = subprocess.run(["uvx", *withs, "marimo", "export", "html", str(app), "-o", str(out)], capture_output=True, text=True)
    failed = "some cells failed" in (r.stdout + r.stderr) or r.returncode != 0
    print("native run:", "FAILED" if failed else "ok")
    if failed:
        print((r.stdout + r.stderr)[-2000:])
    return not failed


def wasm(app: Path):
    site = Path(tempfile.mkdtemp())
    (site / app.parent.name).mkdir()
    out = site / app.parent.name / app.with_suffix(".html").name
    subprocess.run(["uvx", "marimo", "export", "html-wasm", "--mode", "run", "--no-show-code", str(app), "-o", str(out)],
                   capture_output=True, text=True, check=True)
    if (app.parent / "public").exists() and not (out.parent / "public").exists():
        shutil.copytree(app.parent / "public", out.parent / "public")
    handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(site))
    srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return f"http://127.0.0.1:{srv.server_port}/{app.parent.name}/{out.name}", srv


def browse(url, expect, clicks, expect_after, timeout):
    from playwright.sync_api import sync_playwright
    ok = True
    with sync_playwright() as p:
        b = p.chromium.launch()
        pg = b.new_page(viewport={"width": 1300, "height": 1400})
        errors = []
        pg.on("console", lambda m: errors.append(m.text[:200]) if m.type == "error" else None)
        t0 = time.time()
        pg.goto(url)
        for text in expect:
            try:
                pg.locator(f"text={text}").locator("visible=true").first.wait_for(timeout=timeout * 1000)
                print(f"visible after {time.time() - t0:.0f} s: {text!r}")
            except Exception:
                print(f"NOT visible within {timeout} s: {text!r}")
                ok = False
        for c in clicks:
            kind, _, label = c.partition(":")
            loc = pg.get_by_role(kind, name=label) if kind in ("tab", "button", "switch", "checkbox", "radio") else pg.get_by_text(c)
            loc.first.click()
            time.sleep(3)
            print("clicked", c)
        for text in expect_after:
            n = pg.locator(f"text={text}").locator("visible=true").count()
            print(("found " if n else "MISSING ") + repr(text))
            ok = ok and n > 0
        font = pg.evaluate("(() => { const h = document.querySelector('.markdown h1, h1'); return h ? getComputedStyle(h).fontFamily : 'no h1'; })()")
        print("heading font:", font)
        if "Inclusive Sans UW" not in font:
            print("  (no university font: run scripts/inline_uw_css.py in the website repo)")
        print("console errors:", errors[:5] or "none")
        ok = ok and not errors
        b.close()
    return ok


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("app", nargs="?", help="path to the marimo app (.py); omit with --live")
    ap.add_argument("--live", help="check a deployed URL instead of a local file")
    ap.add_argument("--expect", action="append", default=[], help="text that must become visible (repeatable)")
    ap.add_argument("--click", action="append", default=[], help="role:name (tab:, button:, switch:) or plain text to click")
    ap.add_argument("--expect-after", action="append", default=[], help="text that must be visible after the clicks")
    ap.add_argument("--timeout", type=int, default=180, help="seconds to wait for each --expect text")
    a = ap.parse_args()
    if not a.live and not a.app:
        ap.error("give an app path or --live URL")
    ok = True
    srv = None
    if a.live:
        url = a.live
    else:
        app = Path(a.app).resolve()
        ok = native(app)
        url, srv = wasm(app)
    ok = browse(url, a.expect, a.click, a.expect_after, a.timeout) and ok
    if srv:
        srv.shutdown()
    print("CHECK", "PASSED" if ok else "FAILED")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
