# Macros, Tables, Charts, Colors

Use the macros and styles listed here. The style file defines everything the layout needs, so documents do not define new commands, colors, or TikZ styles.

## Contents

1. Header, footer, and page blocks
2. Section headings and lead paragraph
3. Figures
4. Highlight macros
5. TikZ card styles and figure placeholders
6. Tables (booktabs + siunitx)
7. Charts and figure colors
8. Lists and references
9. Color palette
10. Font sizes

## 1. Header, Footer, and Page Blocks

All of these are called by the page template. Documents only fill the slots.

- `\setheader{title}{subtitle}`: university logo (left), title and subtitle (center), D3 logo (right), 2pt d3-navy rule below. With an empty subtitle only the title line renders.
- `\ingressblock`: renders `\innledning` as the lead paragraph. Skipped when the slot is empty.
- `\fullwidthblock`: renders `\helbredde` across the full text width, above the columns. Skipped when the slot is empty.
- `\bunntekst`: thin rule plus centered footer. Shows the university line by default, `\projektname` when set, and `page / N` when `\abstractpages` is above 1.

## 2. Section Headings and Lead Paragraph

- `\sectionhead{text}`: bold heading in d3-navy with automatic space above. Use inside `\venstre`, `\hoyre`, or `\helbredde`. No manual `\vspace` before headings.
- `\ingress{text}`: large lead text in d3-navy, used by `\ingressblock`.

## 3. Figures

Place image files in `drafts/figures/`. The folder is on the graphics path.

- `\figur{file}{caption}`: column-width figure with bold caption below.
- `\storfigur{file}{caption}`: alias of `\figur`.
- `\bilde{file}{caption}`: centered image with width `\bildebredde`.
- `\helfigur{file}{caption}`: centered figure at 75% of the text width, for the `\helbredde` slot.

```latex
\renewcommand{\helbredde}{\helfigur{architecture.pdf}{Fig.\,1: System architecture.}}
```

## 4. Highlight Macros

| Macro | Purpose | Limit |
|-------|---------|-------|
| `\highlight{}` | Inline d3-orange bold for a term or number | 3 per page, tables included |
| `\keypoint{}` | Navy-tinted callout box with left accent border, full column width | 1 per column |
| `infobox` | Headline metric with a large number | 3 per page |
| `card alert` | Blocker, deadline, or risk | 2 per page |

Outside tables, a number is emphasized in one place: the headline number by `\highlight{}` in the lead paragraph, other numbers by infoboxes. Best-value highlights in tables are exempt. A `\keypoint{}` may restate the headline number.

## 5. TikZ Card Styles and Figure Placeholders

Use inside `\begin{tikzpicture}...\end{tikzpicture}`:

- `card`: light blue fill
- `card gray`: light gray fill
- `card highlight`: navy-tinted fill
- `card alert`: orange-tinted fill with 3pt orange left border
- `infobox`: centered box with 3pt navy left border
- `tag`: small label

Infoboxes, cards, and callouts span the full column width and stack vertically with `\vspace{1ex}` between them. Infobox (the label holds about 38 characters on one line):

```latex
\begin{tikzpicture}
\node[infobox] {\textbf{\color{d3-navy}\Large 50+}\quad publications};
\end{tikzpicture}
```

Alert card:

```latex
\begin{tikzpicture}
\node[card alert, text width=\linewidth-14pt, align=center, inner sep=6pt, minimum height=0.8cm]
  {\textbf{\color{d3-orange} Blocked:}\enspace IRB approval pending};
\end{tikzpicture}
```

Figure placeholder for planned figures (internal documents only):

```latex
\begin{tikzpicture}
\node[card gray, text width=\linewidth-16pt, align=center, minimum height=2.0cm]
  {\color{d3-gray}\sffamily\small
   \textbf{Fig.\,1:} Regret vs.\ $n$ (log-log)\\[2pt]
   Convergence curves showing the $n^{-1/2}$ slope};
\end{tikzpicture}
```

- `minimum height=2.0cm` controls the placeholder size (2.0cm fits well in a column)
- `text width=\linewidth-16pt` fills the column width (text width plus twice the 8pt inner sep)
- First line: figure number. Second line: what the figure will show

## 6. Tables (booktabs + siunitx)

Use `booktabs` rules and `siunitx` `S` columns for numeric data. The style file loads both and sets numbers in Inter with tabular figures, so decimals align exactly.

```latex
\begin{tabular*}{\linewidth}{@{\extracolsep{\fill}} l S[table-format=3.0] @{}}
\toprule
\textbf{Item} & {\textbf{Value}} \\
\midrule
Row 1 & 100 \\
Row 2 & 200 \\
\bottomrule
\end{tabular*}
```

`tabular*` with `\extracolsep{\fill}` stretches the table to the column width, so its rules line up with infoboxes and text. Text cells that wrap use a ragged-right `p` column, which avoids stretched word spacing:

```latex
\begin{tabular*}{\linewidth}{@{\extracolsep{\fill}} l >{\raggedright\arraybackslash}p{3.6cm} @{}}
```

siunitx rules:

- `S[table-format=X.Y]` reserves X integer digits and Y decimals (for 35.1 use `2.1`)
- Wrap header text in braces: `{\textbf{Header}}`
- For text suffixes such as `35.1k`, add `table-space-text-post=k`
- `\highlight{}` and `\textbf{}` work inside `S` columns

### Benchmark Comparison Tables

Separate the comparison methods from our methods with a `\midrule`, so readers see at once which rows are ours.

```latex
\begin{tabular*}{\linewidth}{@{\extracolsep{\fill}} l S[table-format=1.2] S[table-format=1.2] @{}}
\toprule
\textbf{Method} & {\textbf{Metric 1}} & {\textbf{Metric 2}} \\
\midrule
% --- Comparison methods ---
Method A & 3.10 & 0.82 \\
Method B & 2.95 & 0.85 \\
Method C & 2.70 & 0.87 \\
\midrule
% --- Ours ---
\textbf{Ours (variant 1)} & \highlight{1.80} & \highlight{0.94} \\
\textbf{Ours (variant 2)} & 1.95 & 0.92 \\
\bottomrule
\end{tabular*}
```

- Comparison methods above the `\midrule`, our methods below, our method names in `\textbf{}`
- `\highlight{}` marks the best value per column, whichever method achieves it
- Tables with more than three numeric columns highlight only the summary column, which keeps the page within the limit of 3 highlights
- Name comparison methods by their published names, and cite them when bibliographic data is available (see Content Integrity in `SKILL.md`). The table note states the shared conditions as far as the user has confirmed them (same data, same features, same tuning budget)
- If space allows, group the comparison methods by category

Recommended column widths:

| Context | First column | Second column | Notes |
|---------|--------------|---------------|-------|
| Either column, two text columns | `p{2.2cm}` | `>{\raggedright\arraybackslash}p{4.0cm}` | a column is about 8.6cm wide |
| Either column, text plus numbers | `l` | `S` columns | use `tabular*` to `\linewidth` |
| Full width (`\helbredde`) | `tabular*` to `\linewidth` with `@{\extracolsep{\fill}}` | | see `example-extended-abstract.tex` |

## 7. Charts and Figure Colors

One color scheme separates our methods from the comparison methods in every chart:

- **Our methods:** `d3-navy`
- **Comparison methods:** `d3-gray` or lighter gray
- **One variant of ours to single out:** `d3-orange` for that variant, `d3-navy` for the others
- Line plots: solid thick lines for ours, dashed thin lines for comparison methods
- Scatter plots: filled markers for ours, open markers for comparison methods
- Every chart has a legend or direct labels
- Palette: `d3-navy`, `d3-orange`, `d3-gray` and their tints only

### matplotlib (through uv)

```python
# /// script
# requires-python = ">=3.10"
# dependencies = ["matplotlib"]
# ///
import matplotlib.pyplot as plt

D3_NAVY, D3_ORANGE, D3_GRAY = "#153F87", "#F29100", "#808080"

methods = ["Method A", "Method B", "Ours"]
regret = [3.10, 2.95, 1.80]
colors = [D3_GRAY, D3_GRAY, D3_NAVY]

fig, ax = plt.subplots(figsize=(3.4, 2.2))          # column width in inches
ax.bar(methods, regret, color=colors)
ax.set_ylabel("Regret")
ax.spines[["top", "right"]].set_visible(False)
fig.savefig("figures/regret.pdf", bbox_inches="tight")
```

Run it from `drafts/` with `uv run make_figure.py`, then include it with `\figur{regret.pdf}{Fig.\,1: Regret by method.}`. The hex values are for plotting scripts only. LaTeX sources use the named D3 colors.

### pgfplots

Add `\usepackage{pgfplots}\pgfplotsset{compat=1.18}` to the preamble.

```latex
\begin{tikzpicture}
\begin{axis}[
    ybar, width=\linewidth, height=4cm,
    symbolic x coords={Method A, Method B, Ours},
    xtick=data, nodes near coords,
    ylabel={Regret}, enlarge x limits=0.3,
    every node near coord/.append style={font=\tiny},
]
\addplot[fill=d3-gray!40, draw=d3-gray] coordinates {(Method A, 3.10) (Method B, 2.95)};
\addplot[fill=d3-navy, draw=d3-navy] coordinates {(Ours, 1.80)};
\end{axis}
\end{tikzpicture}
```

### Inline TikZ bars (no extra package)

```latex
\begin{tikzpicture}[baseline=-0.5ex]
\fill[d3-gray!30] (0,0) rectangle (2.0,0.35);
\node[right, font=\tiny] at (0.05,0.175) {Method A: 3.10};
\fill[d3-gray!30] (0,-0.5) rectangle (1.9,-.15);
\node[right, font=\tiny] at (0.05,-0.325) {Method B: 2.95};
\fill[d3-navy] (0,-1.0) rectangle (1.2,-0.65);
\node[right, font=\tiny, white] at (0.05,-0.825) {\textbf{Ours: 1.80}};
\end{tikzpicture}
```

## 8. Lists and References

Lists are tight by default (`nosep`). Override per list if needed:

```latex
\begin{itemize}[itemsep=2pt]
\item Item with extra space
\end{itemize}
```

Reference list for submission abstracts. Cite in the text as `[1]`, `[2]`:

```latex
\sectionhead{References}
\begin{reflist}
\item Elmachtoub, A. N., Grigas, P. (2022). Smart ``Predict, then Optimize''.
  \textit{Management Science} 68(1), 9--26.
\end{reflist}
```

Format: authors, year in parentheses, title, venue in italics, volume(issue), pages as a number range. One entry costs about 2 line units.

## 9. Color Palette

| Color | Value | Usage |
|-------|-------|-------|
| `d3-navy` | RGB(21, 63, 135) | Primary: titles, rules, headings |
| `d3-orange` | #f29100 | Accent: highlights, alerts |
| `d3-gray` | RGB(128, 128, 128) | Footer text, comparison methods in charts |
| `d3-lightblue` | RGB(200, 220, 240) | Card backgrounds |
| `d3-darkblue` | RGB(10, 40, 100) | Darker variant |

Documents use these named colors only: no `\definecolor`, no `red`, `blue`, or `green`, no hex codes in LaTeX.

## 10. Font Sizes

Inter for all text and for numbers in tables. Formulas use the default math font (Computer Modern), and numbers inside formulas follow the formula.

| Element | Size |
|---------|------|
| Page title | `\LARGE` |
| Subtitle | `\normalsize` |
| Lead paragraph | `\large` |
| Body text | `\small` (set by the template) |
| Section headings | `\large` (set by `\sectionhead`) |
| Figure captions, references | `\footnotesize` |
| Footer | `\footnotesize` |

Body text stays at `\small`. When text does not fit, shorten the text. Large tables may use `\footnotesize`.
