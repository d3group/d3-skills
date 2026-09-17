# Macros & Styling Reference

Full inventory of macros exported by `d3-poster.sty`, the D3 color palette, font sizing conventions, and table/figure formatting rules. Load this file once when you start writing the poster body and want to confirm a macro name or value. SKILL.md has a short pointer with the most-used macros.

## Macros exported by d3-poster.sty

### Header

- `\dthreelogos` — WUE logo + DataDrivenDecisions logo, side-by-side at 3em each, bottom-aligned with the author line. Use as the `{Logo}` argument of `\begin{poster}{...}{eyecatcher}{title}{authors}{logo}`. The `minipage[b]` baseline-anchor inside the macro is what makes the logos sit next to the author text rather than ballooning the header.
- `\dthreelogowue` — WUE-only single logo variant (3.5em tall), also bottom-aligned.

### Highlight macros

- `\highlight{text}` — inline d3-orange bold text. Use sparingly (2-3 per box max).
- `\keypoint{text}` — d3-navy tinted callout box with 3pt navy left accent border. Use 1 per box max.

### TikZ card / infobox styles

Use inside `\begin{tikzpicture}...\end{tikzpicture}`:

- `card` — light blue fill
- `card gray` — light gray fill (use for figure placeholders)
- `card highlight` — navy-tinted fill
- `card alert` — orange-tinted fill with 4pt orange left accent border
- `infobox` — centered info box with 4pt navy left accent border (good for headline metrics)
- `tag` — small label/tag

Example infobox (poster-scaled):

```latex
\begin{tikzpicture}
\node[infobox] {\textbf{\color{d3-navy}\Large 460}\quad heterogeneous SKUs};
\end{tikzpicture}
```

### baposter built-ins (re-exported context)

- `\headerbox{Title}{key=value,...}{content}` — primary content box
- `\hhrule` — horizontal rule in `uniblue` (mapped to d3-navy), useful as a separator inside a box
- `\labelitemi` — bullet style (a d3-navy square)

## Figures — usage rules

### No captions by default

Posters are NOT papers. A poster figure is meant to be parsed in 5 seconds, not studied — the figure itself should be self-explanatory, and the surrounding box body provides the verbal context. **Do not add `\textbf{Fig.~N:}` captions by default.** Just `\includegraphics{...}` inside the box.

Per box, plan for **1-2 figures maximum**. If you find yourself wanting a 3rd, you're overloading the box — cut content instead.

Add a caption ONLY when the user explicitly asks for one (e.g., "the venue requires numbered figures"). Single short line under the figure:

```latex
\includegraphics[width=\linewidth]{method-overview.pdf}
% Caption only if user asked:
\\[2pt]{\footnotesize\color{d3-gray} \textbf{Fig.~1.} Method overview.}
```

### Figure placeholders (also no captions)

When a figure isn't ready yet, drop a `card gray` placeholder:

```latex
\begin{tikzpicture}
\node[card gray, minimum width=0.95\linewidth, minimum height=6cm,
      align=center, font=\sffamily\small]
  {\color{d3-gray}Drop \texttt{method-overview.pdf} into \texttt{figures/}};
\end{tikzpicture}
```

## Tables (booktabs + siunitx)

Same conventions as `d3-abstract`: baselines above `\midrule`, our methods below, `\highlight{}` the best value per column. Use siunitx `S` columns for decimal alignment, with header text wrapped in `{}` braces.

```latex
\begin{tabular}{@{}l S[table-format=2.1] S[table-format=2.1] @{}}
\toprule
\textbf{Method} & {\textbf{Metric 1}} & {\textbf{Metric 2}} \\
\midrule
% --- Baselines ---
Baseline A & 18.4 & 22.1 \\
\midrule
% --- Ours ---
\textbf{Ours}  & \highlight{12.7} & \highlight{15.3} \\
\bottomrule
\end{tabular}
```

## Chart / figure color convention

Same rules as `d3-abstract`:

- **Our methods:** `d3-navy` (primary, visually dominant)
- **Baselines:** `d3-gray` or light gray (recedes)
- **Highlighted variant of ours:** `d3-orange`

Never use rainbow palettes. Our methods must be identifiable at 2m.

## Color palette

Use ONLY these colors:

| Color | Value | Usage |
|---|---|---|
| `d3-navy` | RGB(21, 63, 135) | Primary: box headers, rules, headings (also remaps `uniblue`) |
| `d3-orange` | #f29100 | Accent: highlights, emphasis |
| `d3-gray` | RGB(128, 128, 128) | Subtle text, figure placeholder text |
| `d3-lightblue` | RGB(200, 220, 240) | Card and infobox backgrounds |
| `d3-darkblue` | RGB(10, 40, 100) | Darker variant |

**NEVER** use `red`, `blue`, `green`, or arbitrary hex codes. **NEVER** redefine `uniblue` (d3-poster.sty already remaps it to d3-navy).

## Font sizes

baposter scales fonts automatically based on `a0paper`. The header font is set via the poster options (`headerfont=\Large\sffamily\bfseries`). Within boxes:

| Element | Recommended size |
|---|---|
| Section / box headers | Set by `headerfont` (default `\Large\sffamily\bfseries`) |
| Body text | Default (~24pt at poster scale, set by baposter) |
| Author / affiliation | `\smaller` |
| Figure captions (if used) | `\footnotesize` |
| Math display | Match body text size; don't manually shrink |

If text doesn't fit, **shorten the text** — don't decrease font sizes.

## Title / subtitle

**Title:** always `\sffamily\bfseries\Huge\raggedright` in the title cell. Larger than the upstream baposter default because the D3 brand prioritises a readable hook over packing more text in the header. Keep titles short enough to fit on one or two visual lines at A0 width — if a title needs three lines, shorten it.

**Subtitle: do NOT add one by default.** Single-line punchy title is the default. If the user explicitly asks for a subtitle, render it as a second `\\`-separated line in `\Large` (not `\Huge`), italicised:

```latex
{\sffamily\bfseries\Huge\raggedright Your Poster Title \\[0.3em]
 \Large\itshape Optional subtitle only when user asks}
```

baposter's title cell will full-justify lines that wrap automatically; the `\raggedright` we set helps but does not fully override baposter's internal layout. If the title wraps awkwardly, the first fix is to shorten it, not to manually break with `\\`.
