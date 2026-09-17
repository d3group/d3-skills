# Error Handling Reference

Lookup this file when you hit a LaTeX error or a visible-but-silent rendering issue. The six entries below cover everything observed across the skill's development. SKILL.md has a one-line index near the end pointing to this file.

## 1. Class file not found

```
! LaTeX Error: File `baposter.cls' not found.
```

**Fix:** `baposter.cls` must sit at the project root (next to `poster.tex`, not under `assets/`). Re-copy:

```bash
cp ~/.claude/skills/d3-poster/baposter.cls ./baposter.cls
```

## 2. Font not found (Inter)

```
! Package fontspec Error: The font "Inter" cannot be found.
```

**Fix:** Use XeLaTeX (not pdfLaTeX) and verify `assets/fonts/` exists with the .ttf files:

```bash
ls assets/fonts/Inter_18pt-Regular.ttf
```

## 3. `\d` already defined (siunitx conflict)

```
! LaTeX Error: Command \d already defined.
```

**Cause:** siunitx wants to define `\d` (differential) but the LaTeX kernel defines `\d` (dot-below accent).

**Fix:** `d3-poster.sty` already does `\let\d\relax` before loading siunitx. If you see this, your `d3-poster.sty` is outdated — recopy from the skill.

## 4. Header backgrounds rendered without fill (baposter `headershade` case bug)

**Symptom:** Box headers appear as plain white (or transparent) bars instead of the d3-navy fill we set via `headerColorOne=uniblue`. The log may contain `Package baposter Warning: Unknown headershade style 'shadeLR'`.

**Cause:** baposter.cls defines `headershade` as a `\define@choicekey` with the lowercase choice list `{shadelr, shadetb, shadetbinverse, plain}`. But the .cls's built-in default for the `poster` style (around line 524) is `headershade=shadeLR` — mixed case. Choice keys do exact string matching, so `shadeLR` doesn't match `shadelr`, the unknown branch fires, and the headershade handler is reset to "none" — which is why the fill disappears.

**Fix:** Always set `headershade=plain` explicitly in the `\begin{poster}{...}` options. The Document Skeleton and `example-poster.tex` include it; copy them rather than rolling your own option block.

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

**Fix:** Use the vendored copy at `~/.claude/skills/d3-poster/baposter.cls` — its Calibri block has been removed in favor of `d3-poster.sty`'s Inter setup.

## 6. Box content clipped (no LaTeX error, but visible in PNG)

baposter does NOT raise an error when box content overflows; it silently clips.

**Symptom:** When you render the PDF to PNG and inspect, content at the bottom of a `\headerbox` is cut off, or a figure's bottom edge sits on top of the next box's header.

**Fix:** Cut content in the overfull box. See SKILL.md "Overflow & Clipping" section for the full protocol — cut the lowest-priority content first, shorten lists to max 4 items, reduce table rows, and never shrink fonts (baposter sets its own scale per `a0paper`).
