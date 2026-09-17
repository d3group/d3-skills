# Troubleshooting

## 1. Font Not Found (Inter)

```
! Package fontspec Error: The font "Inter" cannot be found.
```

Compile with `xelatex` from the folder that contains `assets/`. The style loads the fonts from `assets/fonts/` relative to the working directory. `pdflatex` cannot load them.

```bash
ls assets/fonts/Inter_18pt-Regular.ttf
```

## 2. Logo Not Found

```
! LaTeX Error: File `logo-wue.pdf' not found.
```

The header uses `logo-wue.pdf` (left) and `logo-d3.pdf` (right) from `assets/logos/`.

```bash
ls assets/logos/logo-wue.pdf assets/logos/logo-d3.pdf
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

## 8. siunitx Parses a Header as a Number

```
! Package siunitx Error: Invalid number 'Value'.
```

Wrap header cells of `S` columns in braces: `{\textbf{Value}}`.

## 9. pgfplots Commands Undefined

Add `\usepackage{pgfplots}\pgfplotsset{compat=1.18}` to the preamble. The style file loads TikZ only.

## 10. Checker Problems

- `uv: command not found`: install uv (`brew install uv`) and rerun
- First run downloads PyMuPDF into the uv cache. Later runs start at once
- "PDF is older than the .tex file": recompile, then rerun the checker
- "layout rules not detected": the page has no header or footer rule, which means the page was not produced by the template. Check the template call
- A flagged word that is an established technical term ("doubly robust", "Naive Bayes") stays. Warnings need a decision, errors need a fix

## 11. Documents From the Former One-Slider Skill

Files that load `assets/d3-oneslider` compile with their own `assets/` copy. To migrate: copy the new `assets/`, change `\usepackage{assets/d3-oneslider}` to `\usepackage{assets/d3-abstract}` and `\input{assets/d3-oneslider-template}` to `\input{assets/d3-abstract-template}`, then compile and run the checker. Two visible changes follow from fixes in the style: the default university footer now renders when `\projektname` is empty, and an empty subtitle no longer leaves a blank line in the header.

## Error Log Format

```
[HH:MM:SS] ERROR: Description
           Context: What was attempted
           Action: How it was resolved
```
