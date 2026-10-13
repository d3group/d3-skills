# Macros & Styling Reference

Full inventory of macros exported by `d3-poster.sty`, the university frame it draws, the D3 color palette (2026 University of Würzburg corporate design), font sizing conventions, and table/figure formatting rules. Load this file once when you start writing the poster body and want to confirm a macro name or value. SKILL.md has a short pointer with the most-used macros.

## Macros exported by d3-poster.sty

### University frame (drawn automatically)

`d3-poster.sty` wraps baposter's `poster` environment (same five arguments) and draws the frame of the university's A0 poster template. All sizes are in template millimetres: `\dthreeunit` is 1 mm on A0 portrait and scales with the shorter paper side, so A1 and other sizes keep the proportions.

| Element | A0 geometry | Notes |
|---|---|---|
| Margins | 25 mm | set by the .sty (overrides the class `margin` option) |
| Header box | full width, 119 mm high, `d3-navy` | `headerheight=\dthreeheaderheight` (139 mm: box + 20 mm gap) |
| University logo | white, 135 mm wide, 15 mm from the box's top-left corner | `uw-logo-white.pdf` |
| Title + authors | text field from x = 294 mm (269 mm into the box), 425 mm wide, top-aligned with the logo | white; title Bold (`\dthreetitlefont`, 50 pt), authors Regular (`\dthreeauthorfont`, 34 pt) |
| Seal | blue, 93 × 93 mm, flush with the box's right and bottom edges | `uw-seal-blue.pdf` (a corner crop). Interim: the CD booklet replaces it with a faculty ornament once the faculty package is released |
| Section bars | box width, 2em (~24 mm) high | `#ECECEC` (`d3-headergray`), navy SemiBold text (`\dthreesectionfont`); key `emphasis` = `d3-blue` bar, white text |
| Column gap | 14.2 mm | `colspacing=\dthreecolspacing` |
| Footer rule | navy, 0.7 mm, 12.5 mm below the columns | content ends at y = 1095 mm (94 mm bottom margin) |
| Logo row | cells 72 × 39 mm, 7.1 mm apart, from the left margin | 5th argument of `\begin{poster}`; five cells, the D3 logo takes the first two |
| References | right half (x = 428 mm), heading `\dthreereferencesname` in navy | `\dthreereferences{...}`; 24 pt text |

If the title block or the references block does not fit its slot, the .sty sets it smaller (font size in steps down to 60 %, then scaling) and writes `d3-poster Warning: ... was set at <factor> of its normal size`. Shorten the text instead of accepting a small title.

### Header and footer macros

- `\begin{poster}{options}{eyecatcher}{title}{authors}{logos}` — title and authors are plain text; the .sty sets them in the header box. The eye-catcher argument is ignored (the university logo takes its place). The logos argument fills the footer logo row.
- `\dthreelogos` — the D3 logo across the first two cells of the footer logo row (about 30 mm high on A0). Before the 2026 design it placed the old university logo and the D3 logo in the header; the university logo now always sits in the header box.
- `\dthreelogowue` — "university logo only": leaves the footer logo row empty (kept for older posters).
- `\dthreelogocell[<includegraphics options>]{file}` — one more logo cell (partner, funder), placed after `\dthreelogos`: `{\dthreelogos\dthreelogocell{partner-logo.pdf}}`.
- `\dthreereferences{...}` — the footer References slot; use in the preamble or anywhere inside the poster environment. Plain text, 3-5 short references. Rename the heading with `\renewcommand{\dthreereferencesname}{Literatur}`.
- `\dthreesubtitle{text}` — optional subtitle line inside the title argument (only when the user asks).
- Lengths: `\dthreeunit`, `\dthreeheaderheight`, `\dthreecolspacing`. Fonts: `\titlefont` (SemiBold), `\mediumfont` (Medium), `\dthreesectionfont`, `\dthreetitlefont`, `\dthreeauthorfont`.

### Highlight macros

- `\highlight{text}` — inline d3-orange bold text. Use sparingly (2-3 per box max).
- `\keypoint{text}` — light-blue callout box (`d3-lightblue`) with navy text and a 3pt navy left accent border. Use 1 per box max.
- `\subheading{text}` — navy SemiBold subheading inside a box (the template's subheadings).

### TikZ card / infobox styles

Use inside `\begin{tikzpicture}...\end{tikzpicture}`:

- `card` — light blue fill (`d3-lightblue`, #CBD9EE)
- `card gray` — light gray fill (use for figure placeholders)
- `card sand` — sand fill (`d3-sand`, #F1EBDF) for quiet boxes
- `card highlight` — navy-tinted fill
- `card alert` — orange-tinted fill with 4pt orange left accent border
- `takeaway` — sand fill with 4pt orange left accent border (the D3 takeaway rule)
- `infobox` — centered light-blue info box with 4pt navy left accent border (good for headline metrics)
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
- `\labelitemi` — bullet style (a cornflower `d3-blue` square)
- Box key `emphasis` (added by the .sty) — cornflower bar with white text for one box: `\headerbox{Results}{name=Results,column=1,emphasis}{...}`; `emphasis=false` returns to the grey bar

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
- **More series:** in the order navy, orange, blue, teal, yellow, berry, gray

Never use rainbow palettes. Our methods must be identifiable at 2m.

## Color palette

The 2026 University of Würzburg corporate design with the D3 orange as accent (the university's coral is not used next to it). Use ONLY these colors:

| Color | Value | Usage |
|---|---|---|
| `d3-navy` | #02246C | Primary: header box, bar text, rules, headings (also remaps `uniblue`) |
| `d3-darkblue` | #011646 | Darkest variant |
| `d3-orange` | #F29100 | D3 accent: `\highlight`, alert card, takeaway rule |
| `d3-orange-ink` | #B86E00 | Orange as small text on white (contrast) |
| `d3-gray` | #808080 | Subtle text, figure placeholder text, baselines |
| `d3-lightblue` | #CBD9EE | Card, keypoint and infobox backgrounds |
| `d3-blue` | #5E8AC7 | Cornflower: bullets, `emphasis` bar, secondary series |
| `d3-sky` | #5AA1D8 | Large numerals |
| `d3-sand` | #F1EBDF | Quiet boxes, takeaway background |
| `d3-teal` | #009485 | Chart series (as text: `d3-teal-ink` #007A6E) |
| `d3-yellow` | #F8C300 | Chart series |
| `d3-berry` | #821044 | Chart series |
| `d3-peach` | #FCE4BF | Light orange fill |
| `d3-lavender` | #D9CCE6 | Light fill |
| `d3-hairline` | #D3D6DC | Thin rules on white |
| `d3-headergray` | #ECECEC | Section bars |

Body text is black. **NEVER** use `red`, `blue`, `green`, or arbitrary hex codes. **NEVER** redefine `uniblue` (d3-poster.sty already remaps it to d3-navy).

## Font sizes

The font is Inclusive Sans UW (the university's house font, SIL OFL): Regular, Italic, Medium, SemiBold, Bold; Bold Italic is faked with a slant. It has no Greek letters, no ≤ ≥ ≈ ≠ ∞ √ ∈ ∑ ∫ ∂ ⇒ ′ ″ ✓ and no tabular figures; the .sty maps those characters to math mode (math stays in Latin Modern) and sets siunitx numbers in the text font.

baposter scales fonts automatically based on `a0paper`. The section bar font is set via the poster options (`headerfont=\dthreesectionfont`: SemiBold `\Large`, navy). Within boxes:

| Element | Recommended size |
|---|---|
| Section bars | Set by `headerfont` (`\dthreesectionfont`) |
| Subheadings | `\subheading{}` (SemiBold `\large`, navy) |
| Body text | Default (~24pt at poster scale, set by baposter) |
| Author / affiliation | `\smaller` |
| Figure captions (if used) | `\footnotesize` |
| Math display | Match body text size; don't manually shrink |

If text doesn't fit, **shorten the text** — don't decrease font sizes.

## Title / subtitle

**Title:** plain text in the title argument. The .sty sets it white, Bold, ragged-right in the navy header box (50 pt on A0 as in the template, 425 mm text field). Keep titles short enough to fit on one or two lines — if a title needs three lines, shorten it. Size commands such as `\Huge` from older posters still work; the block is then scaled to fit the header box.

**Subtitle: do NOT add one by default.** Single-line punchy title is the default. If the user explicitly asks for a subtitle, add it with `\dthreesubtitle{}` inside the title argument (white, italic, author size):

```latex
{Your Poster Title\dthreesubtitle{Optional subtitle only when user asks}}
```
