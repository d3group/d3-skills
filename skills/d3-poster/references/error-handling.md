# Error Handling Reference

Lookup this file when you hit a LaTeX error or a visible-but-silent rendering issue. The eight entries below cover everything observed across the skill's development. SKILL.md has a one-line index near the end pointing to this file.

## 1. Class file not found

```
! LaTeX Error: File `baposter.cls' not found.
```

**Fix:** `baposter.cls` must sit at the project root (next to `poster.tex`, not under `assets/`). Re-copy:

```bash
cp <skill-dir>/baposter.cls ./baposter.cls
```

## 2. Font not found (Inclusive Sans UW)

```
! Package fontspec Error: The font "InclusiveSansUW-Regular" cannot be found.
```

**Fix:** Use XeLaTeX (not pdfLaTeX) and verify `assets/fonts/` exists with the .ttf files (Regular, Italic, Medium, SemiBold, Bold):

```bash
ls assets/fonts/InclusiveSansUW-*.ttf
```

An older `assets/` folder that still holds `Inter_18pt-*.ttf` is outdated: recopy `assets/` from the skill.

## 3. `\d` already defined (siunitx conflict)

```
! LaTeX Error: Command \d already defined.
```

**Cause:** siunitx wants to define `\d` (differential) but the LaTeX kernel defines `\d` (dot-below accent).

**Fix:** `d3-poster.sty` already does `\let\d\relax` before loading siunitx. If you see this, your `d3-poster.sty` is outdated — recopy from the skill.

## 4. Box headers with a gradient instead of the solid fill

**Symptom:** Box headers show a colour gradient instead of the solid `#ECECEC` fill of `headerColorOne=d3-headergray`.

**Cause:** baposter's own default (baposter.cls, around line 524) is `headershade=shadeLR`, a left-to-right gradient from `headerColorOne` to `headerColorTwo` (baposter's default: brown). `d3-poster.sty` sets `headershade=plain` and both header colours to `d3-headergray`, so the gradient appears when an options block sets another `headershade` or `headerColorTwo`, or when an outdated `d3-poster.sty` is loaded. The choice key is case-insensitive (`\define@choicekey*`), so `shadeLR` and `shadelr` name the same gradient.

**Fix:** Keep `headershade=plain` in the `\begin{poster}{...}` options, as the Document Skeleton and `example-poster.tex` do, and leave the header colours at the template values. Recopy `d3-poster.sty` from the skill if it is outdated.

```latex
\begin{poster}{
  ...
  headershade=plain,             % <-- this line
  ...
}
```

We patch this in the user's poster, not in baposter.cls, because the .cls is vendored upstream code we want to keep clean for future syncs.

## 5. Calibri font error

```
! Package fontspec Error: The font "calibri" cannot be found.
```

**Cause:** Using an unpatched `baposter.cls` from the upstream repo. Upstream ships hardcoded `\setmainfont[Path=fonts/]{calibri.ttf}` which is both proprietary and missing.

**Fix:** Use the vendored copy at `<skill-dir>/baposter.cls` — its Calibri block has been removed in favor of `d3-poster.sty`'s Inclusive Sans UW setup.

## 6. Box content clipped (no LaTeX error, but visible in PNG)

baposter does NOT raise an error when box content overflows; it silently clips.

**Symptom:** When you render the PDF to PNG and inspect, content at the bottom of a `\headerbox` is cut off, or a figure's bottom edge sits on top of the next box's header.

**Fix:** Cut content in the overfull box. See SKILL.md "Overflow & Clipping" section for the full protocol — cut the lowest-priority content first, shorten lists to max 4 items, reduce table rows, and never shrink fonts (baposter sets its own scale per `a0paper`).

## 7. Greek letters or symbols vanish

```
Missing character: There is no ≤ (U+2264) in font InclusiveSansUW-Regular...
```

**Cause:** Inclusive Sans UW has no Greek letters and lacks ≤ ≥ ≈ ≠ ∞ √ ∈ ∑ ∫ ∂ ⇒ ′ ″ ✓. XeLaTeX drops such characters silently; only the log shows them.

**Fix:** `d3-poster.sty` maps these characters to math mode with `newunicodechar` (α → `\ensuremath{\alpha}`, ≤ → `\ensuremath{\leq}`, ...). For any other missing character, write it in math mode or add a mapping in the poster preamble: `\newunicodechar{ℓ}{\ensuremath{\ell}}`. Check with `grep "Missing character" poster.log | grep -v nullfont`; the `;` lines in `nullfont` come from `baposter.cls` and are harmless.

## 8. Title or references set smaller

```
Package d3-poster Warning: The title block was set at 0.85 of its normal size to fit its slot.
```

**Cause:** the title and authors do not fit the navy header box (or the references do not fit the footer slot). The .sty steps the font size down to 60 % and then scales the block.

**Fix:** Shorten the title, the author line or the references. Do not accept a title below normal size on a poster.
