# Troubleshooting

## 1. Font Not Found (Inclusive Sans UW)

```
! Package fontspec Error: The font "InclusiveSansUW-Regular" cannot be found.
```

Compile with `xelatex` from the folder that contains `assets/`. The style loads the fonts from `assets/fonts/` relative to the working directory. `pdflatex` cannot load them.

```bash
ls assets/fonts/InclusiveSansUW-*.ttf
```

## 2. Logo Not Found

```
! LaTeX Error: File `uw-logo-navy.pdf' not found.
```

The header uses `uw-logo-navy.pdf` (left) and `logo-d3.pdf` (right) from `assets/logos/`. An `assets/` copy from before the 2026 corporate design lacks the new university logo: copy the current `assets/` from the skill.

```bash
ls assets/logos/uw-logo-navy.pdf assets/logos/logo-d3.pdf
```

## 3. Style Not Found

```
! LaTeX Error: File `assets/d3-abstract.sty' not found.
```

Load the style with the path prefix, `\usepackage{assets/d3-abstract}`, and copy the assets if they are missing:

```bash
cp -r <skill-dir>/assets ./assets
```

The warning "You have requested package `assets/d3-abstract', but the package provides `d3-abstract'" is expected and harmless. The same holds for the hyperref rerun notice on the first compile.

## 4. More Pages Than Declared

The checker reports `PDF = N+1`. Content overflows. Follow the overflow steps in `SKILL.md` (Phase 3, step 4): find the overfull column, cut its lowest-priority section, recompile, rerun the checker.

## 5. Fewer Pages Than Declared

The checker reports fewer template calls than `\abstractpages`. Add the missing page block (slots plus `\input{assets/d3-abstract-template}`) or lower `\abstractpages` after asking the user.

## 6. Footer Shows No Page Indicator

`page / N` appears only when `\abstractpages` is above 1. Set it in the preamble, before `\begin{document}`.

## 7. Overfull and Underfull Boxes

```
Overfull \hbox (12.5pt too wide)
```

An element is wider than its column. Typical causes: a table with fixed `p{}` widths that sum to more than the column, a long unbreakable word or URL, a TikZ node with a fixed width. Narrow the table, rephrase, or set `text width=\linewidth-20pt` on the node. Underfull warnings are cosmetic.

Inside tables the style tolerates overhangs up to 1.5pt: siunitx reserves the width of an "8" per digit, and a "0" or "4" in Inclusive Sans UW is slightly wider. Any overfull box the log still reports is a real overflow.

## 8. Characters Missing From the PDF

```
Missing character: There is no ½ (U+00BD) in font [assets/fonts/InclusiveSansUW-Regular.ttf]...
```

Inclusive Sans UW has no Greek letters and few math symbols, and XeLaTeX drops a character that the font lacks without an error. The style maps Greek letters and ≤ ≥ ≈ ≠ ∞ √ ∈ ∑ ∫ ∂ ⇒ ′ ″ ✓ µ ² ³ to math mode. The checker reports every other missing character as an error. Write it in math mode (`$\tfrac{1}{2}$`) or as a LaTeX command.

## 9. siunitx Parses a Header as a Number

```
! Package siunitx Error: Invalid number 'Value'.
```

Wrap header cells of `S` columns in braces: `{\textbf{Value}}`.

## 10. pgfplots Commands Undefined

Add `\usepackage{pgfplots}\pgfplotsset{compat=1.18}` to the preamble. The style file loads TikZ only.

## 11. Checker Problems

- `uv: command not found`: install uv (`brew install uv`) and rerun
- First run downloads PyMuPDF into the uv cache. Later runs start at once
- "PDF is older than the .tex file": recompile, then rerun the checker
- "no layout rules" or "header hairline or footer rule missing": the page lacks the gray hairline under the logo row or the footer rule, which means the page was not produced by the template or holds overflow. Check the template call
- A flagged word that is an established technical term ("doubly robust", "Naive Bayes") stays. Warnings need a decision, errors need a fix

## 12. Documents From Before the 2026 Corporate Design

Abstracts made with the Inter and old-logo version of the style compile unchanged with their own `assets/` copy. To restyle one, replace its `assets/` with the current copy and compile: the slot macros, color names and TikZ styles are the same. Check the page count afterwards, because the new header with the logo row is taller.

## 13. Documents From the Former One-Slider Skill

Files that load `assets/d3-oneslider` compile with their own `assets/` copy. To migrate: copy the new `assets/`, change `\usepackage{assets/d3-oneslider}` to `\usepackage{assets/d3-abstract}` and `\input{assets/d3-oneslider-template}` to `\input{assets/d3-abstract-template}`, then compile and run the checker. Two visible changes follow from fixes in the style: the default university footer now renders when `\projektname` is empty, and an empty subtitle no longer leaves a blank line in the header.

## Error Log Format

```
[HH:MM:SS] ERROR: Description
           Context: What was attempted
           Action: How it was resolved
```
