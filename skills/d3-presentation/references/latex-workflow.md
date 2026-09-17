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
├── assets/               <-- assembled from the skill's assets/latex/ and assets/fonts/
│   ├── d3-beamer.sty
│   ├── d3-template-library.tex
│   ├── Title_template.pdf
│   ├── Slide_template.pdf
│   └── fonts/            <-- Inter font files
└── *.aux, *.log, etc.    <-- LaTeX auxiliary files (contained!)
```

## Workflow

1. **Create subfolder**: `mkdir <presentation-name>` - DO THIS FIRST!
2. **Assemble assets**: `mkdir <name>/assets && cp -r <skill-dir>/assets/latex/* <skill-dir>/assets/fonts <name>/assets/` (the `.sty` expects `assets/d3-beamer.sty`, `assets/Slide_template.pdf`, `assets/fonts/` next to the `.tex` file)
3. **Read the style guide**: [style-guide.md](style-guide.md), including the Wording section
4. **Create .tex file**: In the subfolder, use the template structure below
5. **Compile**: Run `xelatex <filename>.tex` twice (required for hyperlinks and TikZ positioning)
6. **Verify** at the review depth chosen in SKILL.md Step 0 (light: compile log clean; standard: one reviewer pass over the .tex and the PDF pages; full: the two-agent loop)

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

By default the footer counts every frame. Load the style with the `contentnumbering` option to count content slides only:

```latex
\usepackage[contentnumbering]{assets/d3-beamer}
```

- Title, agenda, section-divider and thank-you frames no longer advance the counter and show no number.
- The option loads `appendixnumberbeamer`. Put `\appendix` right after `\thankyouslide`: the total in the main part becomes the last content slide, and backup slides restart at 1 with their own total.
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
    Key takeaway message in orange-bordered box.
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

Brand colors, content rules and wording rules are shared by both formats and live in [SKILL.md](../SKILL.md). In LaTeX, use only the named colors from `d3-beamer.sty` (`d3-navy`, `d3-orange`, `d3-gray`, `d3-lightblue`, `d3-darkblue`, and the chart colors `d3-teal`, `d3-yellow`, `d3-peach`, `d3-lavender`) with `\color{d3-navy}`, `\textcolor{d3-orange}{text}` or `\fill[d3-teal]`; tints follow the xcolor syntax (`d3-navy!15`). Key messages use `\textbf{\textcolor{d3-orange}{...}}`, never `\orangebox{}`.

## Assets Included

All of these live in the skill's `assets/latex/` (fonts in `assets/fonts/`); the copy step above places them at `assets/` inside the talk folder:

- `d3-beamer.sty` - Core style (slide layouts, title, agenda, sections, thank you)
- `d3-template-library.tex` - Optional components (code boxes, TikZ styles, chevrons, timelines)
- `Title_template.pdf` - Background for title/section/thank you slides
- `Slide_template.pdf` - Background for content and agenda slides
- `fonts/` - Inter font files for consistent rendering

See `example-presentation.tex` for a complete working example of all components.

