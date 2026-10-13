---
name: d3-marimo
description: |
  Build or convert interactive teaching apps as marimo notebooks that run in the browser (WASM) on the chair's
  academic website (chrisflath.github.io), in the University of Würzburg look. Use this skill when:
  (1) Converting a Colab, Jupyter or molab notebook into a marimo app for students
  (2) Building a new interactive course app (optimization model, data explorer, game, quiz)
  (3) Replacing PuLP/CBC models with solvers that run in the browser (SciPy HiGHS: linprog, milp)
  (4) Restyling marimo apps with the university font and colours
  (5) Deploying an app to the website's apps/ folder and listing it on the teaching page
  MANDATORY TRIGGERS: marimo, WASM, molab, Colab to marimo, notebook app, teaching app, course app, html-wasm,
  academic website app, interactive notebook, PuLP in the browser
---

# Teaching apps in marimo (WASM)

Students open a link and the app runs in their browser: no install, no account, no server. marimo exports a
notebook with `marimo export html-wasm`; the website's `scripts/build.py` does this for every `.py` in `apps/`
(run mode, code hidden) and `notebooks/` (edit mode) on every push to `main`.

> **`<skill-dir>`** is this skill's base directory. **`<site>`** is the website repository
> (`academic-website`, remote `chrisflath/chrisflath.github.io`). Ask for its path if it is not obvious.

## Workflow

1. **Get the source.** Colab: `https://drive.google.com/uc?export=download&id=<file id>` returns the `.ipynb`
   (works for files shared by link). molab: append `.py` to the notebook URL. Read every cell and its outputs:
   the outputs are the reference numbers your port must reproduce.
2. **Port the model first, natively.** Reproduce the original results in plain Python with the solver you will
   use in the browser (step 3) before writing any UI. Note every bug you find in the original
   ([references/pitfalls.md](references/pitfalls.md) lists the usual ones) and decide with the user whether the app
   fixes it silently, fixes it visibly (often the better lesson), or keeps the original behaviour as a default.
3. **Choose browser-safe dependencies.** Pyodide runs pure-Python packages plus its own builds of numpy, scipy,
   pandas, altair. Not available: PuLP's CBC binary, Gurobi, OR-Tools. Use `scipy.optimize.linprog(method="highs")`
   for LPs and `scipy.optimize.milp` for integer programs. `requests` works for simple GETs.
4. **Start from the template.** `cp <skill-dir>/assets/app_template.py <site>/apps/<course>-<topic>.py`. It already has
   the kicker line, the style cell, section icons, a solver cell and the footer. Keep cells small: one idea per cell,
   UI elements in their own cell, results in the next.
5. **Data.** Put files in `<site>/apps/public/data/`. Load them with `mo.notebook_location() / "public" / "data" / name`
   and, in the browser, through `pyodide.http.open_url` (see the template). Record source, date and licence in the app.
6. **Look.** The app declares `css_file="uw.css"` (used by local `marimo edit`) and carries a generated style cell
   (used by the WASM export, which ignores `css_file`). After any change to `<site>/apps/uw.css` run
   `python scripts/inline_uw_css.py` in `<site>`. Keep it light: university font and colours through marimo's theme
   variables, one coral `mo.icon("lucide:…")` per section heading, no further reskinning.
7. **Check.** `uv run --with playwright <skill-dir>/scripts/check_app.py <site>/apps/<app>.py --expect "<text>"`
   runs the app natively (every cell must execute), exports it to WASM, serves it locally and waits in headless
   Chromium until the expected text renders, then reports console errors. Add `--click` steps for buttons or
   switches that must work. Compare the numbers with step 2.
8. **List it.** Add the app to the course in `<site>/teaching_config.json` (`"notebooks": [{"file": "apps/…py",
   "title": …, "topics": […]}]`). Edit the JSON as text so the diff stays small; never re-serialise the file.
9. **Deploy.** Commit in `<site>`; pushing `main` deploys through GitHub Actions (about 2 minutes). Pushing publishes:
   ask before the first push of a new app, and mention any unrelated local commits that would go out with it.
   Then run the check against the live URL: `check_app.py … --live https://chrisflath.github.io/apps/<app>.html`.
10. **Link from slides.** In a d3-presentation deck, generate the QR code from the URL at build time (`qrcode` package)
    and verify it decodes from the rendered slide.

## Rules for course apps

- **Competitions do not ship their solution.** If students compete for the best answer, the app shows their own
  result only; the optimum goes on a slide or into class. No leaderboards that write to third-party services.
- **Every number is reproducible.** State data source and date in the app; put solver checks (brute force where the
  instance is small) in a comment next to hard-coded results.
- **Illustrative data is labelled illustrative.** Fictional names (players, countries) avoid made-up facts about
  real ones.
- **Teach through the model.** Offer the switch that shows the instructive failure (LP relaxation vs integer, greedy vs
  optimal, raw vs weighted objective) instead of hiding it.

## Files

| File | Purpose |
|---|---|
| `assets/app_template.py` | marimo app skeleton with the university look, a data loader that works in WASM, a solver cell |
| `assets/uw.css` | the look: Inclusive Sans UW, navy/coral, marimo theme variables (copy to `<site>/apps/uw.css`) |
| `assets/inline_uw_css.py` | copies `uw.css` into the style cell of every app that uses it (copy to `<site>/scripts/`) |
| `scripts/check_app.py` | native run, WASM export, headless browser check, optional live check |
| `references/pitfalls.md` | what breaks in WASM and in notebook ports, with the fix for each |

Fonts: `Inclusive Sans UW` (OFL) lives in `<site>/apps/public/fonts/`; the d3-presentation skill ships the same files
in `assets/fonts/`.
