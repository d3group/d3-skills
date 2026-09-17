# Components and API

Working examples of everything below: `assets/example/explainer/sections/*.html`.

## Contents
1. Project layout and `explainer.toml`
2. Section files
3. Text components
4. Source chips
5. Build directives: equations, code, data, images
6. Math
7. Derivations
8. Interactive figures: `D3X.widget`
9. The plot helper
10. Flow diagrams: `D3X.flow`
11. Helpers
12. What the build and the check report

## 1. Project layout and `explainer.toml`

```
<repo>/explainer/
├── explainer.toml     title, paper folders, vault, macros, depth
├── brief.md           the approved content brief
├── sections/          NN-slug.html, one <section> each, sorted by file name
├── figures/  data/    images and small JSON files to embed (repo paths work too)
├── d3x/               the engine, copied by init.py; never edited per project
├── dist/<name>.html   the output: one offline file
└── review/            check.md and shots/ (git-ignored)
```

```toml
name        = "cutoff_rule"               # dist/<name>.html
title       = "How long to look before you leap"
title_html  = "How long to look before you <em>leap</em>"   # optional: the hero title with one accented word
eyebrow     = "sequential selection · a build-up for the authors"   # small line above the title
subtitle    = "The lede under the title: two or three sentences. HTML and $math$ allowed."
authors     = ["First Author", "Co-Author"]
status      = "Working draft, model v2"   # optional, shown in the header
depth       = "standard"                  # overview | standard | deep
repo        = ".."                        # repository root, relative to explainer/; an absolute path works too
paper       = ["paper"]                   # folders searched for .tex and .aux
macros_from = ["paper/macros.tex"]        # \newcommand, \DeclareMathOperator -> KaTeX macros
vault       = "Vault - Project"           # an Obsidian vault inside the repo, optional
code_links  = "auto"                      # auto | github | vscode | none
[[role]]                                  # the project's colour code, two to five roles
key   = "skip"                            # letters only: colour name in plots, \\skip{...} in formulas
color = "#F29100"
label = "what we choose: the cutoff"      # shown in the hero's legend
[[role]]
key = "win"; color = "#153F87"; label = "the rule picks the best"      # (one table per role; shown compactly here)

[hero]
equation = "eq:limit"                     # pull the central equation from the paper, or write it with the role macros:
# tex    = "\\win{P(x)} = -\\skip{x} \\ln \\skip{x}"
note     = "Every symbol in that line is defined below."

[hud]                                     # the assembling panel on wide screens (optional)
title = "the argument, assembling"
lines = ["skip r − 1, then take the first record", "Pₙ(r) = (r−1)/n · Σ 1/(k−1)", "n → ∞ :  P(x) = −x ln x"]   # plain text or Unicode, narrow

[macros]
"\\E" = "\\mathbb{E}"                     # extra or overriding macros
[css]
extra = ""                                # rarely needed
```

Role colours come from the D3 palette: navy `#153F87`, orange `#F29100`, teal `#4D9AAA`, and gray `#808080` for a fourth role. These three hues stay apart under colour-blindness simulation; a fourth hue from the palette does not, so keep to three plus gray. Orange is light on white: an orange series needs a label. Orange is also the colour of the draggable handle, so it suits the role "what we choose".

## 2. Section files

```html
<section id="core-idea" data-nav="Why 37 percent" data-kicker="Core idea" data-hud="4">
  <h2>Skipping candidates buys a benchmark, and the price is that the best may be among them</h2>
  ...
</section>
```

Everything belongs inside the one `<section>` element: text, figures, and every `<script>` (figure scripts, shared constants, JSON data blocks). A file that continues after `</section>` fails the build. A section file may also hold a `<script>` without a figure, for constants that several figures share (`<script>window.P = {kappa: 1.2, sigma: 0.3};</script>` before the first widget of the explainer); state such a parameter set once in the text. `id` is the anchor, `data-nav` the short label in the contents card, `data-hud="k"` lights lines 1 to k of the assembling panel while this section is on screen, `data-kicker` the mono label next to the step badge (Orientation, Setting, Gap, Core idea, Realization, Evidence, Honest inventory, Notation). The build adds the section number, the sidebar, the header, and the footer. Use `<h3>` inside sections. Link to other sections with `<a href="#id">`; unresolved links fail the build.

## 3. Text components

| Markup | Use |
|---|---|
| `<p class="claim">…</p>` | The project's claim, once, in section 01 |
| `<div class="kpis"><div class="kpi [accent]"><div class="v">3.92 €</div><div class="l">label [[result:…]]</div></div>…</div>` | Headline numbers, three or four |
| `<div class="note"><span class="h">Title</span>…</div>` | Aside or definition |
| `<div class="note key">` | What to keep from a section; at most one per section |
| `<div class="note warn">` | Paper and code disagree; a fragile assumption; a step you could not verify |
| `<div class="note open">` | Open question, next step |
| `<div class="note reading">` | Your interpretation, not stated in the sources; end it with `[[reading]]` |
| `<div class="tblwrap"><table>…</table></div>` | Tables; `td.num` right-aligns numbers; `tr.ours` highlights the project's row |
| `<table class="gap">` | Gap matrix: cells `class="y"` ✓, `class="p"` partial (a word), `class="n"` – |
| `<table class="notation" id="notation">` | Symbol, meaning, code name. The id feeds the Notation drawer (key `n`) |
| `<details class="deep"><summary>Title <span class="tag">optional depth</span></summary><div class="in">…</div></details>` | Folded depth; not counted in the main-line budget |
| `<details class="predict"><summary>Question before a figure</summary><div class="in">Answer</div></details>` | Guess first, then look |
| `<figure class="static"><img src="paper/figures/x.pdf" alt="…"><figcaption>…</figcaption></figure>` | A figure from the repo (PNG, JPG, SVG, PDF) |
| `<div class="cols2">…</div>` | Two columns, collapsing on phones |
| `class="wide"` on a `figure` or `.tblwrap` | Breaks out of the text column to 1000 px |
| `<span class="hl">…</span>` | The one highlighted phrase of a paragraph; rare |
| `<p class="kicker">…</p>` | Small mono label above a table or list |
| `<div class="varlist"><div>$\omega$: realized demand (MWh)</div>…</div>` | The variables of a setting, introduced where they are first needed |
| `<span class="pill [open|done]">open</span>` | Status tags in tables and inventories |
| `<div class="key"><span style="color:var(--r-skip)"><i></i>what we choose</span>…</div>` | A colour legend under an equation; the hero's is generated |

## 4. Source chips

Written inline in text, in captions, in the `data-why` of derivation steps, in `detail` strings of flows. Under a hand-written display formula put the chip into `<div class="eqsrc">[[paper:eq:x]]</div>`, which aligns it like the chip of a pulled equation. Prefer a chip over a hand-typed "Eq. (7)": the chip prints the number from the paper's `.aux` and the build warns about hand-typed ones. The build validates them; the page renders them as small pills, linked where a link exists.

| Chip | Validated against | Shown as |
|---|---|---|
| `[[code:src/model.py:88]]` | file exists, line within file | `code model.py:88`, GitHub permalink at the built commit |
| `[[code:src/model.py:88 def solve]]` | also: the symbol text occurs in the file. The symbol is the anchor and the number a hint: if the code moved, chip and link use the real line and the build warns so that you update the number and reread the sentence | `code model.py:88 solve`. Prefer this form: the function name is what a reader who has not seen the code needs |
| `[[code:src/model.py]]` | file exists | `code src/model.py` |
| `[[paper:eq:prob]]`, `[[paper:sec:model]]`, `fig:`, `tab:`, `thm:`, `lem:`, `prop:`, `def:`, `alg:`, `app:` … | a `\label{…}` with that name in the paper folders | `paper Eq. (12)`, `paper §3.2` when an `.aux` is present, else the label |
| `[[paper:§Optimal cutoff]]` | a `\section` or `\subsection` title containing that text (for headings without a `\label`; the scan marks them with °) | `paper § Optimal cutoff` |
| `[[paper:Section 4, second paragraph]]` | nothing (free text) | as written |
| `[[vault:Why the rule needs a random arrival order]]` | a note with that name in the configured vault | `vault …`, `obsidian://` link |
| `[[result:results/success.json]]` | file exists | `result results/success.json` |
| `[[file:CLAUDE.md]]`, `[[file:Vault - X/old_explainer.html]]` | any file in the repo exists | `file …`; for sources that are neither code, paper, note, nor result |
| `[[src:NotebookLM, <notebook name>]]` | nothing | `source …` |
| `[[reading]]` | nothing | `my reading`, dashed |

Add `|label` to override the text: `[[code:src/train.py:362 _train_step_jitted|the jitted train step]]`. Inside KPI tiles and table cells give long chips a short `|label`; chips truncate with an ellipsis rather than overflow, and the full pointer stays in the tooltip.

A failed chip means the claim next to it is unverified. Find the right pointer or change the claim; do not remove the chip to make the build pass.

## 5. Build directives

**Equation from the paper.** Empty `div`, the build fills it:

```html
<div class="eq" data-label="eq:prob"></div>
```

Works anywhere, including inside a `.dstep`, which is the natural way to end a derivation on the paper's own equation. Finds `\label{eq:prob}`, takes the enclosing `equation` / `align` / `gather` / `multline` / `eqnarray`, strips labels, converts to `aligned` / `gathered`, adds `\tag{12}` when the `.aux` knows the number, and appends the `[[paper:eq:prob]]` chip. If KaTeX cannot render what the paper uses (`check.py` reports it), define the macro in `[macros]` or write the formula by hand as `$$…$$` with a `[[paper:…]]` chip.

**Code from the repo.**

```html
<pre class="code" data-src="src/secretary.py" data-symbol="def run_once" data-note="the cutoff rule"></pre>
```

`data-symbol` anchors the excerpt at the first line containing that text and takes the block that follows (up to the next line at the same indentation, at most `data-max="40"` lines), so the excerpt follows the function when the file changes. `data-lines="20-26"` selects by line numbers instead; use it only for a fragment inside a function, and expect the build to warn that it will drift. Real lines, dedented, line-numbered, lightly highlighted (`data-lang`: py, js, jl, r; default from the extension), captioned with a permalink. Keep excerpts under about 25 lines; over 60 the build warns.

**Data from the repo.**

```html
<script type="application/json" id="data-success" data-src="results/success.json"></script>
<script>var R = D3X.data('data-success');</script>
```

JSON only; `data-src` resolves against `explainer/` first, then the repo root (the same rule as images). Convert other formats once, into `explainer/data/`, keeping only the columns and rows the figure needs:

```bash
uv run --with pandas python -c "import pandas as pd; pd.read_csv('results/x.csv').to_json('explainer/data/x.json', orient='list')"
uv run --with pandas --with pyarrow python -c "import pandas as pd; pd.read_parquet('results/sweep.parquet')[['n','method','error']].to_json('explainer/data/results.json', orient='list')"
```

The caption's `[[result:…]]` chip points at the original file in the repo, not at the converted copy. Aggregate before embedding; over 400 kB the build warns.

When the numbers have to be computed (a sweep the repo never stored), copy `<skill>/assets/templates/make_data.py` to `explainer/data/make_data.py` and adapt it: a uv script header with its dependencies, the project's modules imported from the repo root, `sys.dont_write_bytecode = True` so that importing them leaves no `__pycache__` behind, JSON written next to the script. One command regenerates the data, from the repository root: `uv run explainer/data/make_data.py` (or `uv run --project . python explainer/data/make_data.py` when the project needs its own pinned environment).

**Images.** `<img src="…">` paths resolve against `explainer/` first, then the repo root, and are embedded. PDFs are rasterized with `pdftoppm`.

## 6. Math

KaTeX, offline. Inline `$…$` or `\(…\)`, display `$$…$$` or `\[…\]`. Paste LaTeX from the paper as it is: the paper's macros come in through `macros_from`, and the build escapes `<`, `>`, `&` inside math, so `$a<b$` and `aligned` with `&` are safe. Math also works in captions, `data-why`, control labels, readout labels, legend labels, `ctx.note`, and flow `detail` strings. Text drawn *inside* the SVG (axis labels, panel titles, `hline` / `vline` / `point` / `text` / `region` / end labels, flow node labels) cannot hold KaTeX: simple TeX there is converted to Unicode (`$c_{\max}$` becomes cₘₐₓ, `$x^\star$` becomes x*), so keep those labels to symbols, sub- and superscripts; fractions and operators belong in the caption or a readout. In JavaScript strings, double the backslashes: `'optimum $x^\\star$'`. Literal dollar: `<span class="usd">$</span>`.

Not supported by KaTeX: `\ensuremath` (stripped from macros), `\mbox` with math inside, TikZ, `\textcolor` with xcolor mixes, custom environments. `check.py` lists every formula that fails and every unknown command.

## 7. Derivations

```html
<div class="derivation" id="deriv-cutoff" data-title="From the success probability to 1/e">
  <div class="dstep" data-why="Let $n \to \infty$ with $x = r/n$ fixed; the sum is a Riemann sum of $1/t$ over $[x, 1]$.">
    $$P_n(r) \longrightarrow x \int_x^1 \frac{dt}{t} = -x \ln x$$
  </div>
  <div class="dstep" data-why="Set the derivative to zero; $P''(x) < 0$, so this is the maximum.">
    …
  </div>
</div>
```

Rendered as numbered steps with the reason above each formula, revealed with "Next step" (or "Show all"). `data-mode="open"` shows everything at once; use it for two- or three-step arguments. A step body may hold text, several formulas, a `.note`, or a `<details class="deep">`.

## 8. Interactive figures: `D3X.widget`

```html
<figure class="widget [wide]" id="fig-cutoff">
  <figcaption><b>{fig}. Success probability as a function of the cutoff.</b>
    <span class="try">Drag the orange handle from left to right, then raise $n$.</span>
    <span class="notice">The peak sits near 37 % for every $n$.</span>
  </figcaption>
</figure>
<script>
D3X.widget('fig-cutoff', {
  toy: true,                      // badge "illustrative toy": anything that is not the repo's own experiment
  height: 320,                    // drawing height in px of a 720 (or 960 when wide) px wide canvas
  seed: 1,
  params: {
    x:    {label: 'share skipped $x$', min: 0, max: 0.95, step: 0.01, value: 0.15, unit: ''},
    ties: {label: 'allow ties', value: false},                         // boolean -> checkbox
    rule: {label: 'rule', options: ['cutoff', 'take the first'], value: 'cutoff'},   // options -> select
    t:    {label: 'time', type: 'time', min: 0, max: 100, step: 1, value: 0, fps: 20, loop: false},  // slider + play button
    k:    {type: 'hidden', min: 0, max: 1, value: 0.5}                 // state without a control (set by a handle)
  },
  presets: {'Paper setting': {x: 0.37, ties: false}, 'Take the first': {x: 0}},
  actions: {resample: 'New sample',                                    // built in: new random seed
            solve: {label: 'Jump to optimum', run: function (state) { state.x = 0.37; }}},
  draw: function (p, ctx) { … }   // called on every change; p holds the current values plus p.seed
});
</script>
```

`{fig}` becomes "Figure N" (the build numbers all figures in document order, static ones too); elsewhere write `{fig:fig-cutoff}` for a linked "Figure N". Hard-coded figure numbers draw a warning, because they break as soon as a figure is inserted.

On screens narrower than 560 px a figure redraws on a 440 px canvas and side-by-side panels (`cell`) stack, so labels stay legible; `ctx.narrow` tells `draw` when that is the case, and `ctx.W` changes with it. A figure drawn with absolute coordinates through `ctx.el` should either use `ctx.W` and `ctx.H` or opt out with `fixed: true`. `check.py` warns when text would render under 7 px on a phone.

A control whose range depends on another control (a cutoff $r$ between 1 and $n$): make it a share between 0 and 1 and convert inside `draw`, as `fig-cutoff` in the example does. A figure that mixes the repository's numbers with a browser-side computation keeps `toy: true`, and its caption says which series is which.

Parameter details: `fmt: function (v) { return Math.round(v * 100) + ' %'; }` formats the value shown next to a slider, `unit: '€'` appends a unit; select `options` are strings or `{value, label}` objects; `seed` fixes the first random sample, and the "New sample" action increments it, so the default picture is reproducible and can be chosen (try a few seeds until the default shows the typical case, not a rare one).

Wrap per-figure constants and helper functions in an IIFE `(function () { … })();` so figures do not share globals. Precompute anything expensive outside `draw`.

`ctx` inside `draw`:

| Member | Purpose |
|---|---|
| `ctx.plot(opts)` | a plot panel with axes; see section 9 |
| `ctx.readout(label, valueString, {accent: true})` | number tiles under the figure; label and value are plain text, the label may hold `$math$` (no HTML tags) |
| `ctx.note(html)` | one sentence under the figure that changes with the state: "The order is too low: move right by about 78 units." Often the most instructive element |
| `ctx.rng(stream?)` | seeded generator: `r()`, `r.normal(mu, sd)`, `r.range(a, b)`, `r.int(n)`. Same seed, same noise, so moving a slider does not reshuffle the sample; "New sample" changes the seed. Never `Math.random()` |
| `ctx.legend(label, color, 'line' | 'dash' | 'box' | 'dot')` | manual legend entry (plots add theirs automatically) |
| `ctx.el(tag, attrs, text, parent?)` | raw SVG element, for schematics and custom marks; `ctx.svg` is the root group, `ctx.W`, `ctx.H` the canvas size. To draw inside a plot pass `plot.marks` (clipped to the plot area, under the labels) or `plot.over` (unclipped, on top) as `parent`, and position with `plot.sx`, `plot.sy` |
| `ctx.color('win!30')` | a role or theme colour, or a tint of it, as hex; `ctx.arrow(color)` returns a marker id for `marker-end` |
| `ctx.fmt(v)` | compact number format |

Every widget gets a Reset button, keyboard-accessible controls, an automatic legend, and a hover crosshair whose tooltip lists every labelled series at that position (lines by interpolation, labelled scatter series by their nearest point).

## 9. The plot helper

```js
var plot = ctx.plot({
  x: {domain: [0, 1], label: 'share of candidates skipped', ticks: 5, log: false, fmt: function (v) { return Math.round(v * 100) + ' %'; }},   // or x: [0, 1]
  y: {domain: [0, 0.5], label: 'probability of picking the best'},
  // x: {bands: ['method A', 'method B', 'baseline']}   -> categorical axis for bars
  title: 'Success probability',      // small panel title
  cell: [1, 2],                      // panel 2 of 2, side by side: use two panels, never two y-axes
  margin: {r: 110},                  // room for end labels
  grid: true
});
```

| Method | Draws |
|---|---|
| `plot.line(xs, ys, {color, label, dash, width, end})` | polyline; `end: true` puts the label at the line's end (needs `margin.r`); non-finite values break the line |
| `plot.fn(f, {from, to, n, …line opts})` | `y = f(x)` over the domain |
| `plot.area(xs, ys, base, {color, opacity, label})` | filled area down to `base` (number or array); `NaN` in `ys` leaves a gap, so "not defined in this regime" is `NaN`, never 0 |
| `plot.band(xs, lo, hi, {color, opacity, label})` | uncertainty band |
| `plot.scatter(xs, ys, {color, r, opacity, label, titles})` | dots with hover titles; a point outside the axes is drawn hollow at the edge (and `check.py` warns), never dropped |
| `plot.bars(values, {color, colors, label, series: [k, n], values: true, fmt})` | bars on a `bands` axis; `series` for grouped bars |
| `plot.hline(y, {label, color, dash, anchor, dy})`, `plot.vline(x, {…})` | reference lines, gray and dashed by default; skipped when outside the axis. Two lines close together: give one `anchor: 'end'` (label on the other side) or a `dy` offset, or name them in the legend with `ctx.legend` instead |
| `plot.region(x0, x1, {label, color, opacity})` | shaded vertical region |
| `plot.point(x, y, {label, color, dx, dy})` | marked point with label |
| `plot.text(x, y, str, {anchor, dx, dy, bold, size, color})` | annotation; flips side near the edges |
| `plot.arrow(x0, y0, x1, y1, {label, color})` | annotation arrow |
| `plot.handle(x, y, {setX: 'x', setY: null, label: 'drag'})` | draggable point; dragging writes the named params (clamped to their min, max, step). Give the param a slider too, so it stays keyboard-accessible |
| `plot.sx(x)`, `plot.sy(y)`, `plot.ix(px)`, `plot.iy(py)`, `plot.bx(i)`, `plot.bw()` | scales, inverses, band centre and width, for custom marks via `ctx.el` |

Colours: the project's role keys first (`'skip'`, `'win'`), then the D3 names `'navy'`, `'orange'`, `'teal'`, `'gray'`, `'lightblue'`, `'darkblue'`, plus `'ink'`, `'ink2'`, `'ink3'`; tints as `'navy!30'`. Unspecified line colours cycle navy, orange, teal.

## 10. Flow diagrams: `D3X.flow`

```html
<figure class="widget" id="fig-pipeline"><figcaption>…<span class="try">Select each box.</span><span class="notice">…</span></figcaption></figure>
<script>
D3X.flow('fig-pipeline', {
  cols: 4, rowHeight: 92,
  rowLabels: ['simulation route', 'formula route'],   // optional small labels at the left of each row
  select: 'rule',                                     // optional: the box whose detail is open at the start
  nodes: [
    {id: 'order', label: 'Random arrival order', sub: 'rng.random(n)', col: 0, row: 0, kind: 'data',
     detail: 'What the box does, in a sentence, with math and chips. [[code:src/x.py:10 def load]]'},
    …
  ],
  edges: [['order', 'rule'], ['rule', 'share', 'optional label'], {from: 'a', to: 'b', dash: true}]
});
</script>
```

Kinds: `data` (light blue), `code` (outlined), `model` (navy, the project's contribution), `result` (orange tint), `external` (dashed); a key of the kinds in use appears under the diagram. On a phone a flow keeps its size and scrolls sideways. Place nodes on a grid with `col` and `row`. Edges to the next column run straight or with one bend; every other edge (skipping a box, going back, wrapping a long chain onto a second row) travels in the gap below the row in its own lane, so a chain of eight links can simply continue on `row: 1`. `check.py` warns if an edge still crosses a box. A second click on a box closes its detail. Labels up to about 22 characters wrap to two lines; `sub` is a monospace subtitle (a function or file name). Five to nine nodes read well; beyond twelve, split the diagram.

## 11. Helpers

`D3X.linspace(a, b, n)`, `D3X.mean(arr)`, `D3X.quantile(arr, q)`, `D3X.normPdf(x, mu, sd)`, `D3X.normCdf(x, mu, sd)`, `D3X.rng(seed)`, `D3X.data(id)`, `D3X.color(spec)`, `D3X.fmt(v)`, `D3X.enrich(el)` (renders chips and math in HTML you inserted yourself).

## 12. What the build and the check report

`uv run explainer/d3x/build.py [--draft]`

- `--draft` while writing: TODO markers are allowed, and links to sections that do not exist yet only warn.
- Errors (nothing is written): unresolved chips, unknown `data-label`, code lines out of range, missing images or data, duplicate ids, broken `#links`, a `figure.widget` without a script or a script without a figure, leftover TODO (unless `--draft`).
- Warnings: house wording rules, `Math.random()`, captions without Try / Notice, over-budget words or interactive figures for the chosen depth (flow diagrams are not counted), large embeds, missing notation table.
- A table of words per section (main line and folded) and the totals.
- `review/fidelity-packet.md` and `review/figures-packet.md` for the reviewers (see `review.md`).

`uv run explainer/d3x/check.py [--shots] [--sections]`

- Moves every slider to min, mid, max; toggles every checkbox; selects every option; clicks presets and actions; drags every handle; steps every derivation; clicks every flow node.
- Errors: exceptions in `draw`, NaN / undefined / Infinity in any SVG attribute, a control with no visible effect, a label cut off at the figure's edge in any state, raw TeX left visible in a label, control, legend or caption, KaTeX failures and unknown commands, steps that stay hidden, content hidden under the sidebar, page overflow at 1280 and 390 px.
- Warnings: labels that overlap in the default state, points off the scale, curves that use under 6 % of their panel's height (the effect is invisible), more than four parameters on one figure, a flow edge crossing a box, a figure without controls, Reset not restoring the picture, derivation steps without a reason, very long derivations.
- `--shots` writes one PNG per interactive figure to `review/shots/<id>.png`; `--sections` adds tiled section screenshots (many images; use it for a layout problem, not by default).
- The report is also saved as `review/check.md` for the reviewers.
