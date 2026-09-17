# Interactive figures that teach

An interactive figure is worth its cost when moving something lets the reader check a claim they would otherwise have to take on faith. Everything here follows from that.

## 1. The knob-to-insight test

Before building a figure, write one sentence of the form:

> Moving **X** shows that **Y**.

"Dragging the cutoff from left to right shows that the rule fails for two opposite reasons, and that the success probability peaks near 37 % for every n." "Setting the measurement noise to zero makes the three estimators coincide, so their disagreement is a small-sample effect." "Shrinking the training set makes the flexible model chase the noise while the rigid one stays stably biased."

- The sentence goes into the brief's section plan and becomes the figure's `Notice` line.
- No sentence, no figure. "Shows the architecture" or "visualizes the data" is not an insight; use a static figure or a table.
- One insight per figure. A second insight is a second figure, or a preset.
- If the insight is a single number or a fixed comparison, a KPI tile or a table is better than a figure.

## 2. Rules

**Run the real mechanism.** Implement the project's actual formula, estimator, or algorithm in JavaScript at toy scale: closed forms, a 1-D or 2-D version of the problem, a few hundred samples, a small grid, a handful of iterations. Do not fake a curve that merely looks right; the reviewer reads the script against the paper. When the real thing cannot run in a browser (a trained network, a large optimization model, a long simulation), show the repository's own result files and let the reader filter or hover, or build a toy that isolates the one mechanism and say it is a toy.

**Three sources of numbers, in order of preference.**
1. *Evidence*: result files that already exist in the repository, embedded as JSON, with a `[[result:…]]` chip in the caption.
2. *Computed by the repository's own code*: when no result file has what the figure needs (a sweep over the parameter the slider moves), copy the template `<skill>/assets/templates/make_data.py` to `explainer/data/make_data.py`; it imports the project's modules, evaluates them on a grid, and writes JSON next to itself, never into the repo's own folders (`uv run explainer/data/make_data.py` from the repository root; details in `components.md`, section 5). The sliders then snap to the precomputed grid, the figure shows the project's numbers and not a re-implementation, and the script stays in the folder so the data can be regenerated. Cite the functions it calls with `[[code:…]]` chips in the caption. Spot-check two or three values against numbers printed in the paper.
3. *Toy*: a JavaScript re-implementation at small scale, for mechanisms whose point is the shape and not the number. Declare it with `toy: true`.

Prefer 2 over 3 whenever the code runs in seconds and the numbers matter to the argument. Prefer 3 when continuous dragging carries the insight and a grid would feel coarse.

**Start at the paper's setting.** Default parameter values are the paper's or the config's values, so the first picture matches what the author knows. One exception: the decision variable of a draggable-optimum figure starts away from the optimum, so that there is something to find; say so in the Try line and offer the optimum as a preset. A reader takes every number in a figure for a project number: when a toy has to use a different constant than the code (an initial value, a clip, a step size scaled for the browser), name both values in the caption.

**No calibration in the repo** (a theory paper whose parameters are "illustrative"): define one shared toy parameter set, put it in one `<script>window.P = {…}</script>` before the first figure, state it once in section 01 or 02, and use it in every figure, so that the figures tell one consistent story. Replace the "Paper setting" preset by "Baseline". Add a preset named "Paper setting" when the figure has more than two controls. Presets are also the cheapest way to guide: "Try: press *Symmetric costs*".

**Keep noise still.** Random draws come from `ctx.rng()`. The sample stays the same while sliders move, and changes only through the "New sample" action. `check.py` warns when Reset does not restore the picture, which is the symptom of `Math.random()`.

**Few controls.** Two to four parameters per figure (presets and action buttons do not count; `check.py` warns above four). Every control must change the picture visibly across its range (`check.py` fails a dead control). Ranges cover the interesting regime including the degenerate cases (zero noise, symmetric costs, n = 1), because degenerate cases are where intuition is tested. Guard the formula at those extremes: no division by zero, no log of zero; `check.py` moves every slider to both ends and fails on NaN.

**Direct manipulation where the object is geometric.** A decision, a threshold, a point on a curve: make it a `plot.handle` and keep the slider as the accessible twin.

**Say what the state means.** `ctx.readout` for the two or three numbers the reader should watch; `ctx.note` for a sentence that interprets the current state ("This is the exact optimum for n = 20: skip 7, then take the first record"). A reader who drags without guidance learns little; a sentence that changes with the state is guidance.

**Chart discipline.**
- Colour means what the project's colour code says it means: use the `[[role]]` keys, so that the curve of "what we choose" has the colour it has in the formulas. At most three coloured series per panel (navy, orange, teal); gray for baselines, references, and the past; a further series gets a dash pattern or its own panel.
- Orange marks what the reader moves (the handle) and is light on white: label orange series directly or through the legend.
- Never two y-axes. Two quantities with different units get two panels (`cell: [0, 2]`, `cell: [1, 2]`) that share the x-axis or the control.
- Label axes with quantity and unit. Label series in the legend (automatic) and, for up to three lines, at the line end (`end: true`).
- Lines 2 px, areas as light washes, reference lines dashed gray. No 3-D, no gradients, no decorative animation.
- Fixed axis domains while a slider moves, so the reader sees the curve move and not the axis rescale. Choose the domain for the whole parameter range; if a curve leaves the panel at an extreme, that is fine and honest.
- Fixed does not mean wide. The effect named in the Notice line has to be visible at the default setting: `check.py` warns when the curves use under 6 % of the panel height. Remedies, in order: plot the difference or the ratio instead of the levels; start a *line* plot's axis above zero and say so in the panel title (bars and areas keep their zero baseline); offer two or three zoom levels through a select parameter. Never rescale continuously.

**Captions.** Bold title, `Try` (an action in the imperative), `Notice` (the insight as a checkable fact). The Notice line should be falsifiable by the figure: if the reader could not tell from the picture whether it is true, rewrite one of them.

## 3. Pattern catalog

Pick by the kind of idea, not by what looks impressive.

| The idea is about | Pattern | Sketch |
|---|---|---|
| An optimum or trade-off | **Objective with a draggable decision** | Panel 1: what the objective is made of at the current decision (the pieces of the trade-off). Panel 2: the objective against the decision, handle on the curve, the optimum marked, readout "gap to the optimum". Example: `fig-cutoff` |
| A first-order condition | **Tangent at the draggable point** | The objective with a handle, plus a short tangent line at the handle (`plot.line` through two points) and a readout of the slope; the reader sees the derivative change sign at the optimum, which ties the figure to the derivation step below it |
| A rule or estimator on one data set | **One sample, one outcome** | Dots for the sample, marks for what the rule or each estimator does with it and for the truth, "New sample" action, slider for n. Example: `fig-queue` |
| Bias, variance, error rates, convergence | **Replication summary** | Run 200 seeded replications in `draw` (cache by parameter key if slow); bars or a band plot of the metric by method; slider for n or noise |
| A process that unfolds over time | **Sample paths with a time scrubber** | `type: 'time'` param with play; paths from `ctx.rng()`; toggles for the components of the process (trend, seasonality, shocks); a mean or band for reference |
| An update rule or algorithm | **Step-through iteration** | `time` param as the iteration counter; panel 1 the iterate in its space (contours via a coarse grid of `ctx.el('rect')` cells or a few level lines), panel 2 the objective per iteration |
| A loss function or penalty | **Loss landscape with a sliding prediction** | Loss against prediction error for the competing losses; handle on the prediction; readouts for each loss; shows asymmetry and kinks |
| A constraint or feasible region | **2-D feasible set with a moving constraint** | `ctx.el('polygon')` for the region in plot coordinates (`plot.sx`, `plot.sy`), slider for the constraint level, the optimum moving along the boundary |
| A policy with a threshold or regions | **State space partition** | Grid of cells colored by action (two tints), handle for the current state, slider for the parameter that moves the boundary |
| Sensitivity of a result | **Tornado or response curve** | The headline metric against one parameter with the others at the paper's setting; vline at the paper's value; select for which parameter |
| A pipeline or architecture | **Clickable flow** | `D3X.flow` with kinds and `detail` plus chips. Example: `fig-pipeline` |
| Evidence from the repository | **Results explorer** | Embedded JSON, lines or bars with hover, a select or toggle for metric, scale, or subset. Example: `fig-results` |
| A decomposition (A = B + C) | **Stacked or side-by-side parts** | Area for each term under the total; toggle each term; readout showing the identity holds numerically |
| Two formulations that agree in a limit | **Overlay with a limit slider** | Both curves, slider for the limit parameter, readout for the sup-norm gap |

Small numerics that come up often, all fine in plain JavaScript: numerical integration on a fixed grid (precompute outside `draw`), empirical quantiles (`D3X.quantile`), simulated paths of a recursion, gradient steps on a 2-D function, a small recursion on a grid of 100 points, a bisection root finder. Keep `draw` under about 30 ms so dragging stays smooth: precompute grids, cache replication results in a closure keyed by the parameters that matter.

## 4. Schematics

For actors, flows of goods or information, and timelines that `D3X.flow` does not fit, draw with `ctx.el` inside a widget (no plot needed): rectangles, circles, lines, `text`, arrows via `'marker-end': 'url(#' + ctx.arrow('ink2') + ')'`. Let one or two params change the schematic (which actors take part, which stage is active) so it still passes the knob-to-insight test; otherwise use a static SVG or the paper's own figure.

## 5. Pitfalls that `check.py` cannot see

- **A figure that is correct and teaches nothing.** The curve moves and the reader shrugs. Fix the framing: add the reference that makes the change meaningful (the optimum, the baseline, the paper's value) and a readout of the gap to it.
- **The toy contradicts the paper.** A different convention (cutoff index versus number skipped), a sign flipped, a sum that starts one term late. Compute one known value (the closed-form optimum at the paper's setting) and compare it with the toy's output before moving on.
- **Too much in one panel.** If the legend has more than four entries, split the figure.
- **Axis domains that hide the effect.** If the effect is 2 % of the axis range, change the quantity (plot the gap, not the levels) or the domain.
- **Animation as decoration.** A play button belongs only to time, iterations, or sample size.
- **Hand-typed numbers in an evidence figure.** Embed the file.
