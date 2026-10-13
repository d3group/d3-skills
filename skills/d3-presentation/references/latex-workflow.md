# LaTeX Workflow (PDF via Beamer)

The PDF format of the D3 presentation skill. Read `SKILL.md` first for the shared rules (format choice, content and wording rules, brand colors, verification); this file covers only what is specific to LaTeX.

## CRITICAL: Project Structure

> **ALWAYS create a dedicated subfolder for each presentation!**
>
> LaTeX generates many auxiliary files (.aux, .log, .nav, .out, .snm, .toc).
> These MUST be contained in their own folder - NEVER create presentations in the project root.

```
my-presentation/          <-- Create this folder FIRST
├── my-presentation.tex   <-- Your presentation
├── my-presentation.pdf   <-- Compiled output
├── assets/               <-- assembled from the skill's assets/latex/, assets/fonts/ and assets/logos/
│   ├── d3-beamer.sty
│   ├── d3-template-library.tex
│   ├── fonts/            <-- Inclusive Sans UW font files
│   └── logos/            <-- vector logos and seal (PDF)
└── *.aux, *.log, etc.    <-- LaTeX auxiliary files (contained!)
```

## Workflow

1. **Create subfolder**: `mkdir <presentation-name>` - DO THIS FIRST!
2. **Assemble assets**: `mkdir -p <name>/assets/logos && cp -r <skill-dir>/assets/latex/* <skill-dir>/assets/fonts <name>/assets/ && cp <skill-dir>/assets/logos/{logo-d3,uw-logo-navy,uw-logo-white,uw-seal-blue,uw-seal-faint}.pdf <name>/assets/logos/` (the `.sty` expects `assets/d3-beamer.sty`, `assets/fonts/` and `assets/logos/` next to the `.tex` file)
3. **Invoke `d3-scientific-wording` and read the style guide**: [style-guide.md](style-guide.md), including the Wording section (SKILL.md, Workflow step 3)
4. **Create .tex file**: In the subfolder, use the template structure below
5. **Compile**: Run `xelatex <filename>.tex` twice (required for hyperlinks and TikZ positioning)
6. **Verify** at the review depth chosen in SKILL.md Step 0, after the wording lint (`uv run <wording-dir>/scripts/check_wording.py <name>.tex`) (light: compile log clean; standard: one reviewer pass over the .tex and the PDF pages; full: the two-agent loop)

## Template Structure

```latex
\documentclass[aspectratio=169]{beamer}

% Core D3 styling (required)
\usepackage{assets/d3-beamer}

% Advanced components (optional - only if you need code boxes, chevrons, timelines)
\input{assets/d3-template-library}

\title{ACTION TITLE HERE}
\subtitle{Optional Subtitle}
\date{Date and Location}

\chair{Chair of Information Systems and Business Analytics}
\presenter{Author Name}
\contact{name@uni-wuerzburg.de}   % optional lines in the thank-you box

% Define sections once for reuse
\defsectionsfour{Introduction}{Methodology}{Results}{Conclusion}

\begin{document}

% Title slide
\titleslide

% Agenda slide (clickable items)
\showagenda

% Section divider (highlights current section)
\showsection{1}

% Content slides here

% Thank you slide
\thankyouslide

\end{document}
```

**Note:** The `\input{assets/d3-template-library}` is optional. Only include it when you need:
- Code boxes (`codebox`, `errorbox`, `terminalbox`)
- TikZ diagram styles (`d3box`, `d3project`, `d3circle`, etc.)
- Chevron process flows (`\twochevron`, `\threechevron`, `\fourchevron`, `\fourcolchevron`)
- Project timelines (`projecttimeline`, `\workpackage`)

## Slide Numbering (optional)

By default the page tab counts every frame. Load the style with the `contentnumbering` option to count content slides only:

```latex
\usepackage[contentnumbering]{assets/d3-beamer}
```

- Title, agenda, section-divider and thank-you frames no longer advance the counter and show no number.
- The option loads `appendixnumberbeamer`. Put `\appendix` right after `\thankyouslide`: the total in the main part becomes the last content slide, and backup slides restart at 1 with their own total.
- The page tab shows the number only. Add the option `pagetotal` to show `n/N`.
- Compile three times so the totals settle. Custom frames you define yourself can join the scheme with `\d@uncount` after their `\end{frame}` (inside `\makeatletter ... \makeatother`).

## Slide Types

> **Copy code from `example-presentation.tex`** - it contains complete working examples of all slide types.

### Basic Slides (inline examples)

**One-Column Content:**
```latex
\onecol{Action title summarizing the key message}{
    Content here (bullets, text, graphics)
    \begin{itemize}
        \item Point one
        \item Point two with \highlight{highlighted text}
    \end{itemize}
}
```

**Two-Column Slide:**
```latex
\twocol{Action title}{
    \columnheader{Left Header}
    Left content
}{
    \columnheader{Right Header}
    Right content
}
```

**Two-Column with Takeaway:**
```latex
\twocoltakeaway{Analysis Title}{
    Left column
}{
    Right column
}{
    Key takeaway message in the sand bar with the orange rule.
}
```

### Advanced Slides (copy from d3-template-library.tex)

Search for these comments in `example-presentation.tex`:

| Search For | Description |
|------------|-------------|
| `% AGENDA SLIDE` | Agenda with numbered items (all clickable) |
| `% SECTION` | Section dividers with `\showsection{n}` |
| `% CODE BOXES` | Standard, error, and terminal code boxes |
| `% CHEVRONS` | Process flows with 2, 3, or 4 phases |
| `% TIMELINES` | Gantt-style timeline with work packages |
| `% TikZ box styles` | Process boxes, arrows, and flowcharts |

## The Frame (University of Würzburg design, 2025)

`d3-beamer.sty` draws every frame with TikZ on the 1280 × 720 px grid of the university PowerPoint master (1 px = 0.125 mm on the 16:9 Beamer page). It needs `aspectratio=169`.

- **Content slides**: the university logo top left, the D3 logo in the co-branding slot top right, a grey hairline below the logo row, the title in navy Inclusive Sans SemiBold below the hairline, body text in black, square bullets in cornflower blue (`d3-blue`). The footer line reads `presenter | chair | short title` (`\title[short]{long}` sets the short title); the page number sits in a navy tab at the bottom right.
- **Title slide**: white, the university logo with the D3 logo next to it, the title in navy Bold, then a navy band with a short orange rule, the subtitle, the presenter and the date. The seal sits in the band's bottom-right corner.
- **Section dividers** (`\showsection{n}`, `\showsection[question]{n}`): navy full bleed, white logo, orange "PART n OF N", the two-digit number in sky blue, the part name in white, an optional question below it, the seal in the bottom-right corner. `\sectionslide[question]{title}` makes the same slide without a number. The package option `agendadividers` replaces the navy divider with the agenda, the current part highlighted (the pre-2025 behaviour).
- **Agenda** (`\showagenda`): two-digit numbers in sky blue, topics in black; every row links to its divider.
- **Thank-you slide** (`\thankyouslide`, `\thankyouslide[text]`): "Thank you" in navy, a navy box with the presenter, the chair and the optional `\contact{line\\line}` lines, light grey right half with a faint seal.
- **Takeaway** (`\twocoltakeaway`): a sand bar above the footer with a 4 px orange rule on the left; the text is Medium black and bold words turn orange-ink. `\takeawaylabel{Key takeaway:}` in the preamble puts a bold label in front of every takeaway (none by default, as in the HTML deck). `\takeawayshift{<length>}` moves the bar on one slide (positive = lower).
- **Kicker**: `\kicker{Word}` before a slide puts an orange word in front of its title (one slide only).
- **Seal**: the rector's seal stands in for the faculty ornament that the university's brand architecture will put on faculty and chair slides; the faculty package is not released yet, so the seal is an interim choice.
- **German labels**: the package option `german` gives "Teil n von N", "Vielen Dank" and the German chair line.

**Font.** Inclusive Sans UW (the university's house font, SIL OFL 1.1) in Regular, Italic, Medium, SemiBold and Bold, loaded from `assets/fonts/`. There is no Bold Italic: `\textbf{\textit{...}}` slants the Bold. `\textsemibold{}` and `\textmedium{}` reach the two middle weights. The font has no Greek letters and no math symbols: the `.sty` maps text-mode α–ω, the Greek capitals, ≤ ≥ ≈ ≠ ∞ √ ∈ ∑ ∫ ∂ ⇒ ′ ″ ✓, ² ³ and µ to math mode, so they print in the math font instead of vanishing. Arrows (→ ← ↔) come from the font itself. Any other missing glyph shows up as `Missing character` in the `.log`; check it after each build.

## Code Boxes

For programming presentations, use these code environments (requires `\input{assets/d3-template-library}`):

```latex
% Standard code (navy border)
\begin{codebox}
def hello():
    print("Hello World")
\end{codebox}

% Error code (red border)
\begin{errorbox}
TypeError: unsupported operand type
\end{errorbox}

% Terminal output (dark background)
\begin{terminalbox}
$ python main.py
Processing complete
\end{terminalbox}
```

Use `\pyind` for Python-style indentation in code boxes.

## Critical Rules

Brand colors, content rules and wording rules are shared by both formats and live in [SKILL.md](../SKILL.md). In LaTeX, use only the named colors from `d3-beamer.sty` (`d3-navy`, `d3-darkblue`, `d3-orange`, `d3-orange-ink`, `d3-gray`, `d3-lightblue`, `d3-blue`, `d3-sky`, `d3-sand`, `d3-hairline`, and the chart colors `d3-teal`, `d3-teal-ink`, `d3-yellow`, `d3-berry`, `d3-peach`, `d3-lavender`) with `\color{d3-navy}`, `\textcolor{d3-orange}{text}` or `\fill[d3-teal]`; tints follow the xcolor syntax (`d3-navy!15`). Chart series run navy, orange, blue, teal, yellow, berry, gray. Key messages use `\textbf{\textcolor{d3-orange}{...}}`, never `\orangebox{}`.

## Assets Included

These live in the skill's `assets/latex/`, `assets/fonts/` and `assets/logos/`; the copy step above places them at `assets/` inside the talk folder:

- `d3-beamer.sty` - Core style (frame, title, agenda, dividers, thank you, takeaway; draws everything with TikZ)
- `d3-template-library.tex` - Optional components (code boxes, TikZ styles, chevrons, timelines)
- `fonts/` - Inclusive Sans UW (`InclusiveSansUW-*.ttf`)
- `logos/` - vector PDFs: `uw-logo-navy.pdf`, `uw-logo-white.pdf` (university logo), `uw-seal-blue.pdf`, `uw-seal-faint.pdf` (seal, corner crops) and `logo-d3.pdf`

See `example-presentation.tex` for a complete working example of all components.

