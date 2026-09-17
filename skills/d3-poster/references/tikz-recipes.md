# TikZ Recipe Reference — 4 figure patterns + general rules

Copy-paste-ready TikZ figures when no usable source figure exists — Tier C with low-res extraction, Tier D with nothing at all, or any tier where the user wants to redraw. Each recipe has been verified compiling under XeLaTeX with the d3-poster.sty palette and styles loaded.

**Prerequisites:** the .sty exports `card`, `card highlight`, `infobox` styles + the d3-navy / d3-orange / d3-gray palette. Add `\usetikzlibrary{positioning,arrows.meta,shapes.geometric,fit}` to the preamble if not already there.

**TikZ output is vector by default.** XeLaTeX renders TikZ as native PDF vector commands — the cleanest path to vector figures, no source-PDF or external-export round-trip needed.

Adapt the recipes freely — they're patterns, not contracts. **The user can also ask for any other figure type; treat these as starting points, not the menu.**

## Recipe 1: Block diagram (Input → Method → Output)

Workhorse for method overviews. 3 boxes in a row, the middle one tinted to mark "our method":

```latex
\begin{center}
\begin{tikzpicture}[
  every node/.style={font=\sffamily\small},
  block/.style={draw=d3-navy, fill=d3-lightblue, line width=1pt,
                minimum width=3.2cm, minimum height=1.5cm, align=center, rounded corners=2pt},
  arr/.style={-{Stealth[length=4mm]}, line width=1.2pt, d3-navy},
  node distance=1.2cm
]
\node[block]              (in)  {Features\\$\vec{x}$};
\node[block, right=of in, fill=d3-navy!15] (m) {Weighted SAA\\estimator};
\node[block, right=of m]  (out) {Decision\\$\hat{q}_t$};
\draw[arr] (in) -- (m);
\draw[arr] (m)  -- (out);
\end{tikzpicture}
\end{center}
```

## Recipe 2: Pipeline (N stages)

Sequential stages with directional arrows. Fits 4-5 stages comfortably in a 2-column poster's column width; if you need 6+, span both columns with `span=2` on the parent `\headerbox`.

```latex
\begin{center}
\begin{tikzpicture}[
  every node/.style={font=\sffamily\footnotesize},
  stage/.style={draw=d3-navy, fill=white, line width=1pt,
                minimum width=2.4cm, minimum height=1.2cm, align=center},
  arr/.style={-{Stealth[length=3.5mm]}, line width=1pt, d3-navy},
  node distance=0.55cm
]
\node[stage]                       (s1) {Raw\\demand};
\node[stage, right=of s1]          (s2) {Feature\\eng.};
\node[stage, right=of s2, fill=d3-navy!10] (s3) {Global\\model};
\node[stage, right=of s3, fill=d3-navy!15] (s4) {Local\\weights};
\node[stage, right=of s4]          (s5) {Rolling\\opt.};
\draw[arr] (s1) -- (s2);  \draw[arr] (s2) -- (s3);
\draw[arr] (s3) -- (s4);  \draw[arr] (s4) -- (s5);
\end{tikzpicture}
\end{center}
```

Use `fill=d3-navy!10` and `fill=d3-navy!15` shading on the stages where the contribution sits, so a viewer's eye lands there first.

## Recipe 3: Layered architecture (5-7 components)

ML-style architecture with stacked layers and an optional side branch. The side branch uses `d3-orange` + dashed to mark an auxiliary component (regulariser, attention mechanism, etc.).

```latex
\begin{center}
\begin{tikzpicture}[
  every node/.style={font=\sffamily\footnotesize},
  layer/.style={draw=d3-navy, fill=d3-lightblue, line width=0.8pt,
                minimum width=5.5cm, minimum height=0.9cm, align=center},
  arr/.style={-{Stealth[length=3mm]}, line width=0.8pt, d3-navy},
  side/.style={draw=d3-orange, dashed, line width=0.7pt,
               fill=d3-orange!8, minimum width=2.5cm, minimum height=0.8cm, align=center},
  node distance=0.35cm
]
\node[layer]                              (input) {Input: demand $\xi$, features $\vec{x}$};
\node[layer, below=of input, fill=d3-navy!10] (enc)   {Encoder (LightGBM ensemble)};
\node[layer, below=of enc,   fill=d3-navy!18] (head)  {Weighting head $w^i(\vec{x})$};
\node[layer, below=of head]               (out)   {Output: optimal order $\hat{q}_t$};
\node[side, right=of enc] (reg) {RO regulariser};
\draw[arr] (input) -- (enc);
\draw[arr] (enc)   -- (head);
\draw[arr] (head)  -- (out);
\draw[arr, d3-orange, dashed] (reg) -- (enc);
\end{tikzpicture}
\end{center}
```

Tint depth (`d3-navy!10`, `!18`) signals importance: deeper = more central. Cap at 3 tint levels per diagram or it gets noisy.

## Recipe 4: Comparison schematic (prior vs. ours)

Two stacked panels with badges. Use when the contribution is best explained as "they did X, we do Y" and a numeric table alone doesn't show the conceptual difference:

```latex
\begin{center}
\begin{tikzpicture}[
  every node/.style={font=\sffamily\footnotesize},
  panel/.style={draw=d3-navy, line width=0.8pt, minimum width=6cm, minimum height=2.5cm, align=center},
  badge/.style={fill=d3-navy, text=white, font=\sffamily\bfseries\small,
                inner sep=4pt, rounded corners=2pt},
  badgeours/.style={fill=d3-orange, text=white, font=\sffamily\bfseries\small,
                    inner sep=4pt, rounded corners=2pt}
]
\node[panel, fill=black!4]   (prior) at (0,0)   {Conditional expectation\\via parametric model};
\node[badge, above=-2pt of prior.north west, anchor=west] {Prior work};
\node[panel, fill=d3-navy!8] (ours)  at (0,-3)  {Weighted SAA over\\historical samples};
\node[badgeours, above=-2pt of ours.north west, anchor=west] {Ours};
\end{tikzpicture}
\end{center}
```

The `above=-2pt of ... .north west, anchor=west` is what tucks the badges into the upper-left corner of each panel.

## General TikZ-figure rules

1. **One figure per box maximum.** If you find yourself needing two TikZ figures in one `\headerbox`, the box is overloaded.
2. **Use only d3-navy, d3-orange, d3-gray (and their tints).** No rainbow palettes. Tints via `!N` syntax (e.g., `d3-navy!10`).
3. **Sans-serif inside figures.** Add `every node/.style={font=\sffamily\small}` (or `\footnotesize`) at the top of every `tikzpicture`.
4. **Arrows: `-{Stealth[length=3mm or 4mm]}`** — arrows.meta gives consistent arrowheads. Avoid `->` (default is too thin).
5. **Borders: `line width=0.8pt` for nested, `1pt` for outer.** Thicker looks heavy at A0; thinner disappears at print.
6. **Center figures with `\begin{center}...\end{center}` inside `\headerbox`.** baposter doesn't auto-center floats.
7. **Compile, render to PNG, eyeball.** TikZ silently mis-positions things when node distances clash with `minimum width` — always run the visual validation pass after adding a TikZ figure.

## When to use which recipe

| Situation | Recipe |
|---|---|
| Method overview — single-pass: data → method → output | 1 (Block diagram) |
| Sequential pipeline — 4-5 distinct stages | 2 (Pipeline) |
| ML architecture — stacked layers, optional side-branch | 3 (Layered architecture) |
| Highlighting "they did X, we do Y" conceptual contrast | 4 (Comparison) |
| Anything else (Sankey, hierarchy, decision tree, ...) | Ask the user; adapt the closest recipe or write fresh TikZ |
