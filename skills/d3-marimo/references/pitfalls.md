# Pitfalls: marimo in the browser, and porting old notebooks

Each entry happened in a real port (DSS apps, October 2026). Symptom, cause, fix.

## WASM runtime

**Custom CSS has no effect after export.** `marimo export html-wasm` copies `css_file` but never loads it.
Fix: the generated style cell (`inline_uw_css.py`) that renders `<style>` through `mo.Html`.

**Some elements ignore the stylesheet.** Tabs, tables and other UI elements render in a shadow DOM; page selectors do
not reach in. CSS *variables* do: theme marimo through `--primary`, `--blue-1…12`, `--color-blue-500`, `--action`,
`--marimo-text-font`, `--tw-prose-headings`. A heading inside `mo.ui.tabs` needs an inline style
(`mo.Html('<h3 style="color:#02246C">…')`).

**The app hangs after the static cells when it reads a data file.** `pd.read_csv(url)` inside Pyodide failed on
GitHub Pages (compressed responses) though it worked on a local server. Fix: `pyodide.http.open_url(url)` in the
browser, plain `read_csv(path)` locally (template, `load_csv`).

**Solver missing.** PuLP needs the CBC binary; Pyodide cannot run it. Use SciPy: `linprog(..., method="highs")`,
`milp(c, constraints=LinearConstraint(A, lb, ub), integrality=..., bounds=Bounds(0, 1))`. Results matched PuLP in
every port.

**Local test passes, live fails.** Different server behaviour (compression, caching). Always run `check_app.py --live`
after the deploy finishes.

**Headless checks find nothing.** marimo checkboxes are not `<input>`s and many outputs sit in shadow roots: locate
with `get_by_role("checkbox")` and `locator("text=…")`, which pierce shadow DOM; `inner_text("body")` does not.
`document.fonts.check()` also returns true when no such font is declared; check the computed `font-family` instead.

## Python in marimo cells

**Read-only arrays.** `np.fill_diagonal(df.values, 1)` raises "underlying array is read-only" under pandas
copy-on-write. Work on `df.to_numpy().copy()`.

**f-strings with LaTeX.** `mo.md(f"... $e_{pd}$ ...")` formats `{pd}` as Python (here: the pandas module). Keep LaTeX in
a plain string piece: `mo.md(f"## {icon} Title\n" "$e_{pd}$ ...")` (implicit concatenation; only the first piece is an
f-string).

**A cell's name collides.** marimo forbids redefining a global in two cells; prefix cell-local names with `_`.

## Porting the model

**LP relaxation reported as the answer.** A PuLP model without `cat="Integer"`/`LpBinary` returns fractions
("6.5 passports"). Make the integrality explicit, and consider showing both as the lesson.

**Matrix rows and columns are not in the same order.** Country-by-country data (passport index) lists passports and
destinations in different orders; a positional diagonal marks the wrong cells. Index by label (`df.loc[p, p]`), or
use the data's own self-code (`-1`).

**Category semantics.** "Everything except *visa required* counts as access" also counted *no admission*. List the
categories explicitly and, if it matters, let students choose them (`mo.ui.multiselect`).

**Mixed units in one objective.** Summing sodium (mg) and fat (g) lets one nutrient dominate. Offer a normalised
objective (each term divided by its limit) next to the original.

**Labels that lie.** The original printed the objective under "Total cost". Re-derive every printed quantity.

## Classroom

**Competition apps.** Do not put a "reveal optimum" button in a student app. Do not depend on a Google Apps Script
leaderboard: submissions failed and the board filled with duplicates. Ask the room for the best score instead.
