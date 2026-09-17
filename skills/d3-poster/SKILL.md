---
name: d3-poster
description: |
  Create D3 (Data Driven Decisions) branded conference posters (A0 portrait, baposter grid). Use when:
  (1) Creating a research poster, conference poster, or academic poster with D3 branding
  (2) Generating an A0 poster from a paper, Overleaf submodule, or repo of results
  (3) Working with baposter / 3-column grid layouts for the Chair of Information Systems
  (4) Translating an existing paper or one-slider into a printable poster
  (5) Scanning a paper repo for abstract, sections, figures, tables, and bibliography to seed the poster
  (6) Enriching a poster with vault knowledge (recall) or NotebookLM literature
  MANDATORY TRIGGERS: poster, conference poster, research poster, A0 poster, baposter, D3 poster, paper poster, scientific poster, plakat, poster session
---

# D3 Poster (Conference / Research)

> **`<skill-dir>`** in this skill means the skill's own base directory, which Claude Code shows when the skill loads (installed as a plugin: `${CLAUDE_PLUGIN_ROOT}/skills/d3-poster`; copied by hand: `~/.claude/skills/d3-poster`). Substitute the real path in every command.

Create professional A0-portrait research posters with D3 (Data Driven Decisions) and University of Würzburg branding. Builds on the `baposter` class for a grid layout, with a thin D3 reskin (`d3-poster.sty`) that overrides the brand color, adds the D3 logo, and ports the `\highlight` / `\keypoint` / `infobox` / `card` macros from `d3-abstract`. **Compiles with XeLaTeX or LuaLaTeX for Inter font; falls back to pdfLaTeX with Helvetica clone.**

## Reference files (loaded on demand)

The skill body below is the workflow; long reference material lives in `references/`. Load a reference file when its topic comes up:

| File | Load when |
|---|---|
| `references/extraction.md` | About to extract content from a paper (any tier). Has the tier-by-tier extraction commands, PDF figure extraction (vector-first), low-res raster protocol, on-disk format priority, architecture-figure interview. |
| `references/tikz-recipes.md` | About to draw a figure from scratch in TikZ. Has 4 verified-compiling recipes (block diagram, pipeline, layered architecture, comparison) plus general TikZ rules. |
| `references/error-handling.md` | Compile errors or visible rendering bugs. Has the 6 known issues (missing class, missing fonts, siunitx `\d` conflict, headershade case bug, Calibri error, silent clipping). |
| `references/dual-agent-review.md` | Review depth is `standard` or `full` (see Review). Has the reviewer prompts, the iteration loop for `full` (capped at 4 rounds), score-to-README protocol. |
| `references/macros-and-styling.md` | Writing the poster body and need to confirm macro names, color values, font sizes, table conventions. |

## Template files and assets

```
<skill-dir>/
├── SKILL.md                    # this file
├── baposter.cls                # class file (copied to each project's drafts/)
├── example-poster.tex          # reference example -- DO NOT copy into user projects
├── references/                 # progressive-disclosure references (see table above)
└── assets/                     # this entire folder IS copied into user projects
    ├── d3-poster.sty
    ├── logos/                  # logo-wue.pdf, DataDrivenDecisions.png, seal-wue.png, logo-uni.pdf
    └── fonts/                  # Inter_18pt-{Regular,Bold,Italic,BoldItalic,SemiBold}.ttf, OFL.txt
```

**Two placement rules:**

1. `baposter.cls` sits at the SKILL ROOT, not under `assets/`. `\documentclass` does not reliably accept path prefixes, so the class file must be a sibling of the .tex file at compile time.
2. `example-poster.tex` sits at the SKILL ROOT, NOT inside `assets/`. **Never copy it into a user project.** It's a reference you read when you need to remember the patterns. If you copy `assets/` wholesale, you don't pick up `example-poster.tex` — exactly right, because shipping it alongside the user's `poster.tex` would confuse Overleaf's "Main document" selector and leave a stale `example-poster.pdf`. The user's project should contain ONE `.tex` whose stem matches its `.pdf`.

## Project setup (save location + folder structure)

### Save location priority

Posters are usually tied to a paper. Where you save determines whether collaborators can compile on Overleaf when local LaTeX isn't available. **Decide the save location BEFORE creating any files:**

1. **Paper submodule detected → `<submodule>/poster/`**. If `.gitmodules` lists a submodule that contains a paper (path like `paper/`, `manuscript/`, `overleaf/`, or any submodule whose contents include a `\title{}` + `\begin{abstract}` .tex), save inside that submodule. Lab convention: paper submodules live on GitHub and the corresponding Overleaf project syncs via Overleaf's GitHub Sync — the remote will be `github.com/...`, not `git.overleaf.com`.
2. **No submodule but a paper folder exists → `<paper-folder>/poster/`**. Still place under the paper folder.
3. **Fallback → `./poster/`** at the current working directory root.

Detect with:

```bash
test -f .gitmodules && git submodule status
for sm in $(git config --file .gitmodules --get-regexp path 2>/dev/null | awk '{print $2}'); do
  find "$sm" -maxdepth 3 -name "*.tex" -exec grep -l "\\\\begin{abstract}" {} \; 2>/dev/null
done
```

Print and confirm with the user before creating files:

```
[HH:MM:SS] SAVE LOCATION: <chosen-path>/poster/
  Reason: [paper submodule at paper/ (GitHub-hosted, Overleaf-synced) | paper/ folder exists | repo root fallback]
  Reachable on Overleaf? [yes -- push submodule to GitHub, Overleaf will sync | no -- local compile only]
```

### Folder structure

```
<save-target>/poster/
├── progress.md
├── SUMMARY.md
├── drafts/
│   ├── baposter.cls            # copied from skill (sibling of poster.tex)
│   ├── assets/                 # copied from skill (d3-poster.sty, logos, fonts)
│   ├── figures/                # optional: poster-specific figures
│   ├── poster.tex              # the one working file (revisioned via git)
│   ├── poster.pdf              # always has the matching stem
│   └── revision_notes.md
└── final/
    ├── baposter.cls            # duplicated for Overleaf-standalone upload
    ├── assets/                 # duplicated for Overleaf-standalone upload
    ├── poster.tex              # same filename as in drafts/ -- stem invariant
    ├── poster.pdf
    └── README.md               # date, title, venue, review scores
```

Setup commands:

```bash
POSTER_DIR=<resolved-path>/poster
mkdir -p "$POSTER_DIR/drafts" "$POSTER_DIR/final"
cp    <skill-dir>/baposter.cls "$POSTER_DIR/drafts/baposter.cls"
cp -r <skill-dir>/assets       "$POSTER_DIR/drafts/assets"
# Do NOT copy example-poster.tex -- it stays at the skill root.
```

**Naming rule (critical for Overleaf):** the working file is always `poster.tex`, producing `poster.pdf`. Stem matches. Versioning uses git, not filename prefixes — no `v1_poster.tex`, no `YYYYMMDD_title.tex`. A previous version of this skill used such prefixes; in practice it confused Overleaf uploads (the user would set `v2_poster.tex` as main doc, but the cached `v1_poster.pdf` next to it made it unclear which was the real output).

**Why duplicate `baposter.cls` + `assets/` in both `drafts/` and `final/`?** ~1.5 MB per copy, but it guarantees each folder is **independently uploadable to Overleaf** — a collaborator opening `final/` doesn't need anything from `drafts/`.

## Document skeleton

Every poster MUST start with this structure:

```latex
%! TEX program = xelatex
\documentclass[a0paper]{baposter}

\usepackage{relsize}
\usepackage{url}
\usepackage{multicol}
\usepackage{amsmath,amssymb}
\usepackage{natbib}
\usepackage{graphicx}

\usepackage{assets/d3-poster}   % D3 reskin: colors, fonts, macros

\DeclareMathOperator*{\argmin}{arg\,min}
\renewcommand{\vec}[1]{\boldsymbol{#1}}   % Optional: bold math vectors

\begin{document}

\begin{poster}{
  columns=2,                     % DEFAULT 2. Use 3 ONLY when content truly justifies it.
  grid=false,
  borderColor=uniblue,           % uniblue is remapped to d3-navy by d3-poster.sty
  headerColorOne=uniblue,
  headerColorTwo=uniblue,
  headerFontColor=white,
  headerheight=11em,
  boxColorOne=white,
  boxpadding=1em,
  headershape=rectangle,
  headershade=plain,             % REQUIRED: baposter's default `shadeLR` is case-incorrect and leaves
                                 % header backgrounds unfilled. See references/error-handling.md #4.
  headerfont=\Large\sffamily\bfseries,
  textborder=none,
  background=plain,
  bgColorOne=white,
  bgColorTwo=white,
  headerborder=open,
  boxshade=plain,
  eyecatcher=false
}
%%% Eye Catcher (empty) %%%
{}
%%% Title -- single line, large, ragged-right.  No subtitle by default.
{\sffamily\bfseries\Huge\raggedright Your Poster Title}
%%% Authors -- one line; logo cell sits next to this line.
{\vspace{0.6em}
  Author Name, Data Driven Decisions Group\enspace|\enspace author@uni-wuerzburg.de}
%%% Logos (bottom-right, aligned with author line)
{\dthreelogos}

%%% Motivation (column 0, row 0)
\headerbox{Motivation}{name=Motivation,column=0,row=0}{
  Lead paragraph: why this work matters, what's new, headline metric.
  Use \highlight{} sparingly on key terms.
}

%%% Problem (column 0, fills to bottom)
\headerbox{Problem}{name=Problem,column=0,below=Motivation,above=bottom}{
  Formal problem setup. Domain-appropriate math.
  \keypoint{One-sentence headline takeaway.}
}

%%% Approach (column 1, top)
\headerbox{Approach}{name=Approach,column=1,row=0}{
  Methodology. End with the method-overview figure (no caption needed -- describe in body text).
}

%%% Results + inline Literature (column 1, fills to bottom)
\headerbox{Empirical Results}{name=Results,column=1,below=Approach,above=bottom}{
  Infoboxes with metrics + a booktabs comparison table.
  End with an inline Literature paragraph (3 references, no separate box).
}

\end{poster}
\end{document}
```

**CRITICAL:** Use `\usepackage{assets/d3-poster}` (with `assets/` prefix) — the wrapper expects to be loaded from a project root that has `assets/d3-poster.sty` and a sibling `baposter.cls`.

## Box positioning, columns, title

### Column count — default 2, 3 only if needed

Use `columns=2` by default. Use `columns=3` ONLY when:

- The paper has 5+ truly distinct content sections that can't be combined (rare)
- The user explicitly requests it for a venue that expects it

In 2-column layout, **fold the Literature into the bottom of the Results box** (as a short paragraph, e.g., "**Literature.** Author1 (Year, *Venue*); Author2 (Year, *Venue*); ..."). Avoids the cramped boxes that 3-column tends to produce at A0 portrait.

### Default 2-column grid

```
+-----------------------+-----------------------+
| Motivation            | Approach              |
| (col 0, top)          | (col 1, top)          |
+-----------------------+-----------------------+
| Problem               | Empirical Results     |
| (col 0, fills to      | + inline Literature   |
|  bottom)              | (col 1, fills to      |
|                       |  bottom)              |
+-----------------------+-----------------------+
```

### 3-column variant (rare)

```
+---------------+---------------+---------------+
| Motivation    | Approach      | Empirical     |
| (col 0)       | (col 1,       | Results       |
+---------------+  full height) | (col 2)       |
| Problem       |               +---------------+
| (col 0)       |               | Literature    |
|               |               | (col 2)       |
+---------------+---------------+---------------+
```

### `\headerbox` keys

| Key | Purpose | Example |
|---|---|---|
| `name=X` | Unique identifier for cross-refs | `name=Motivation` |
| `column=N` | 0-based column index | `column=0` |
| `row=N` | 0-based row from top | `row=0` |
| `below=Y` | Position directly below box Y | `below=Motivation` |
| `above=bottom` | Stretch to page bottom | `above=bottom` |
| `height=1` | Fill full column height | rarely needed in 2-col |
| `span=N` | Span N columns | `span=2` (full-width banner) |

### Title — large, single-line, no subtitle by default

Title uses `\sffamily\bfseries\Huge\raggedright` (see `example-poster.tex`). Larger than upstream baposter because the D3 brand prioritises a readable hook. Keep titles short enough to fit on 1-2 visual lines at A0 width.

**Subtitle: do NOT add one by default.** Single-line punchy title is the default. Add a subtitle only if the user asks; see `references/macros-and-styling.md` for the syntax.

## Paper / repo scanning workflow

**Posters almost always derive from an existing paper, but the input setup varies a lot.** Some users have a full repo with paper submodule + figures; others have only a PDF a coauthor sent them; some have just notes. Detect the tier before deciding how to extract.

### Step 1: Detect the input tier

Probe the working directory and **stop at the first match**:

| Tier | What you find | How to detect |
|---|---|---|
| **A. Full repo + paper submodule** | Outer repo with `.gitmodules` pointing at a paper repo on GitHub, alongside `figures/`, `results/`, `code/`, etc. The canonical case. | submodule contains an abstract-bearing .tex AND sibling `figures/` / `results/` / `code/` exist |
| **B. Paper repo only** | A single repo or submodule containing .tex, figures, references — nothing outside. Common for Overleaf-only projects. | submodule (or cwd) has abstract-bearing .tex + paper-relative `figures/`, but no sibling code/results dirs |
| **C. Single paper file** | Just a `*.pdf` or `*.docx` in cwd, no source. Common when a coauthor emails the compiled paper. | a paper file but no .tex, no submodule |
| **D. Notes / topic only** | No file. User describes the work inline. | none of the above |

Print `[HH:MM:SS] INPUT TIER: <X> -- <one-line description>` so the user can confirm or override.

### Step 2: Extract content

Load `references/extraction.md` for the tier-specific commands. Summary:

- **Tier A/B:** parse the .tex source — the extraction-mapping table maps `\section{...}` → poster boxes, `\begin{table}` → booktabs tables, `\includegraphics{...}` → figure inventory, `references.bib` → Literature paragraph.
- **Tier C:** dump PDF text via `uv run --with pymupdf`; for figures, prefer the **PDF-page-crop approach** (vector-preserving) before falling back to raster embedding extraction or full-page high-DPI render.
- **Tier D (.docx):** dump text and images via `uv run --with python-docx`.
- **Tier D' (no file):** skip extraction; interview the user with the structured prompt template in `references/extraction.md`.

### Step 3: Scan for figures, results, code

| Asset type | Default search paths | Format priority |
|---|---|---|
| Figures | `figures/`, `figs/`, `plots/`, `images/`, paper-folder/figures/ | **PDF > EPS > SVG > PNG > JPG** — prefer vector. Dedup by stem (see `references/extraction.md`). |
| Generated results | `results/`, `output/`, `experiments/`, `runs/` | Same: PDF preferred |
| Code / methodology | `code/`, `src/`, `notebooks/`, `scripts/` | n/a |
| Paper-relative | Anything inside the paper subfolder | Same as Figures |

Quick survey:

```bash
for d in figures figs plots images results output experiments code src notebooks; do
  [ -d "$d" ] && echo "Found: $d/ ($(ls $d | wc -l | tr -d ' ') items)" && ls "$d" | head -5
done
```

If none exist, broaden the scan (`find . -type f \( -name "*.pdf" -o -name "*.png" \) -not -path "./.git/*"`) and ask the user which assets are poster-relevant.

**Why vector first:** A0 prints at ~84 cm wide; even a small figure on a poster is 25+ cm. Raster at paper-column resolution (~800 px) becomes 30 px/cm at A0 — visibly pixelated. Vector renders at print resolution regardless of physical size.

### Step 4: Print a content brief

After Steps 1-3, synthesize a brief that stays in conversation context:

```
Paper found: paper/manuscript.tex
- Title: <extracted title>
- Abstract -> Motivation lead: <2-3 sentence condensation>
- Sections: Intro -> Motivation; Setup -> Problem; Method -> Approach; Results -> Empirical Results
- Figures inventoried: 6 in figures/ (top candidates: regret-vs-n.pdf, method-overview.pdf)
- Tables inventoried: 2 in paper/ (main_comparison.tex looks like the headline)
- Bib hits: 47 references; will narrow to 3-5 for the Literature paragraph

Want to use this as the seed, or override anything?
```

Get user approval before mapping content into boxes.

## Creating figures: decision tree

When you need a figure in a box, choose:

1. **A vector figure already exists on disk** (PDF/EPS/SVG, same stem dedup): use it directly. `\includegraphics[width=\linewidth]{...}`.
2. **A raster figure exists but at sufficient resolution** (≥2200 px at column width): use it; warn if marginal.
3. **A raster figure exists but at low resolution** (<1500 px at column width): offer to redraw. See `references/extraction.md` for the threshold derivation.
4. **An architecture-style figure was detected** (filename or caption contains "architecture", "pipeline", "overview", "framework", ...): **interview the user before placing it** (use-as-is / simplify / replace / skip). See `references/extraction.md` §8.
5. **No usable source figure**: draw in TikZ. Load `references/tikz-recipes.md` for 4 verified recipes (block diagram, pipeline, layered architecture, comparison schematic) + general TikZ rules.

TikZ output is vector by default — the cleanest path when redrawing.

## Workflow protocol

### Phase 1: Plan

1. **Analyze the request.** New poster or editing an existing one? Identify the paper source (run Step 1 of paper scanning). Print: `[HH:MM:SS] PLANNING: [new|editing]`.
2. **Optional knowledge enrichment.** Offer only when the user's request is high-level, no paper is linked, or the user mentions "literature", "recall", "past work". Skip if a paper was scanned or the user provides a detailed brief. Options to offer: (1) recall vault, (2) NotebookLM, (3) both, (4) skip. Print: `[HH:MM:SS] ENRICHMENT: [skipped|recall|notebooklm|both]`.
3. **Resolve save location and create folder** (see Project setup section above).
4. **Initialize progress.md** with phase-by-phase timestamps.

### Phase 2: Multi-pass build

Three passes. Never skip a pass.

**Pass 0: Content outline (MANDATORY)**

1. If a paper was scanned, use the extracted content as primary input.
2. If a knowledge brief exists, layer it in.
3. Draft a bullet-point outline (Title, Authors, Motivation, Problem, Approach, Results+Literature). For each: what goes in it.
4. Run the **glance test** — title + box headers + headline number must telegraph the contribution at 2m.
5. Present to user and get approval.
6. Print: `[HH:MM:SS] OUTLINE: Approved by user`.

**Do NOT write any LaTeX until the outline is approved.**

**Pass 1: Skeleton**

1. Create `poster.tex` using the Document Skeleton above.
2. Fill in all `\headerbox{Title}{...}` entries matching the approved outline.
3. Add `% TODO: [description]` placeholders inside each box.
4. Compile — must produce a 1-page A0 PDF.
5. Print: `[HH:MM:SS] SKELETON: 1 page A0, [N] boxes, compiles clean`.

**Pass 2: Fill + compile**

1. Fill each box content one at a time, in order: Motivation → Problem → Approach → Empirical Results.
2. **Compile after each box is filled** — verify the box height hasn't pushed neighbours into clipping.
3. Remove all `% TODO:` comments.
4. Final compile + visual validation (see Compilation and Validation section below).
5. Print: `[HH:MM:SS] FILLED: All boxes complete, 1-page A0`.

## Content development

### Define the core message

- **Audience:** conference attendees walking by (30-60s for overview, 2-5 min if they stop)
- **Purpose:** should a passing reader recognise the contribution and consider asking about it?
- **One-sentence summary:** if the reader remembers one thing, what is it?

### Plan the layout

Use the **inverted pyramid + glance test**: a viewer 2m away should grasp the topic from the title + box headers alone.

### Content outline (MANDATORY before LaTeX)

Draft a bullet outline and get user approval. Example:

```
Title: [Paper title, shortened if needed]
Authors: [1-2 names + affiliation + email]
Motivation:
  - 2-3 sentences: problem framing + headline contribution
  - 1 \highlight{} on the key claim
Problem:
  - Formal setup (1-2 equations max)
  - keypoint: one-sentence takeaway
Approach:
  - 2-3 method paragraphs (bold lead-ins: Prescriptive analytics, Global training, Rolling horizon)
  - 1 figure (method overview, no caption)
Empirical Results:
  - 2-3 infoboxes (headline metrics)
  - 1 comparison table (booktabs, NeurIPS style)
  - 1-2 sentence conclusion with \highlight{} on the win margin
  - inline Literature paragraph (3 references)
```

### Budget content space (concise by default)

**Posters are not papers and not one-pagers.** A passer-by reads the title and headline number, stops if interested, and grasps the contribution from 3-5 sentences plus a figure. Anything more is wasted.

Default budgets for the 2-column layout:

| Box | Default capacity |
|---|---|
| Motivation (col 0, top) | 60-100 words, 1 `\highlight{}`, NO figure |
| Problem (col 0, bottom) | 80-150 words + 1-2 equations + 1 `\keypoint{}` |
| Approach (col 1, top) | 100-180 words (2-3 bold-lead paragraphs) + 1 figure |
| Empirical Results (col 1, bottom) | 30-60 words + 2-3 infoboxes + 1 comparison table + 3-citation Literature paragraph |

If you exceed these by more than ~20%, you are overpacking. Cut sentences before adding line-spacing tweaks.

**Concise writing rules (apply during Pass 2):**

1. No throat-clearing. Cut "It is important to note that", "Our results suggest that", "We propose a novel approach that..."
2. Verb-first bullets. "Achieves 30% cost reduction" not "We achieve a 30% cost reduction".
3. Numbers before prose. Put 30% in an `infobox` and skip the prose version.
4. One sentence per idea. No compound sentences with subordinate clauses.
5. No background the venue audience already knows. A NeurIPS poster doesn't need to explain what regret is.
6. No "future work" section. Posters describe finished work.

## Compilation and validation

### Step 1: Compile locally (XeLaTeX preferred)

From `poster/drafts/`:

```bash
xelatex -interaction=nonstopmode poster.tex
```

With `\cite{}` + `references.bib`:

```bash
xelatex -interaction=nonstopmode poster.tex
bibtex  poster
xelatex -interaction=nonstopmode poster.tex
xelatex -interaction=nonstopmode poster.tex
```

**Engine notes:** XeLaTeX is default (loads Inter via fontspec). LuaLaTeX works the same. pdfLaTeX falls back to TeX Gyre Heros — use only if both Xe and Lua fail.

### Step 1b: Overleaf fallback (only if local fails AND submodule path is available)

When local fails with a missing-package / missing-font / environment error you can't resolve, fall back to Overleaf. Only applies when the save location is inside a paper submodule.

Lab convention: paper submodules are on GitHub, Overleaf is connected via GitHub Sync. Flow: push to GitHub → Overleaf pulls → compile in browser.

```bash
cd <submodule-path>
git remote -v   # expect github.com/<org>/<paper-repo>.git, NOT git.overleaf.com
git add poster/
git commit -m "Add D3 poster"
git push
```

Then tell the user:

- Open the connected Overleaf project
- **Menu → GitHub → Pull GitHub changes** (or wait for auto-sync)
- **Menu → Settings → Main document:** `poster/drafts/poster.tex`
- **Menu → Settings → Compiler:** XeLaTeX
- Click **Recompile**

Once it compiles, download the PDF and place at `poster/drafts/poster.pdf` so the rest of validation still applies. **Don't forget** to update the outer repo's submodule pointer:

```bash
cd <outer-repo-root>
git add <submodule-path>
git commit -m "Bump paper submodule with poster"
```

When local compile succeeds, **do not** mention the Overleaf path — it adds noise.

### Step 2: Visual validation (MANDATORY)

A0 PDFs are huge. Render with `uv run --with pymupdf` to keep dependencies isolated:

```bash
mkdir -p review/
uv run --with pymupdf python -c "
import fitz
doc = fitz.open('poster.pdf')
for i, page in enumerate(doc):
    pix = page.get_pixmap(dpi=150)
    pix.save(f'review/page-{i+1:03d}.png')
    print(f'Page {i+1}: {pix.width}x{pix.height}')
doc.close()
"
```

**Note on uv:** this skill uses `uv run --with <pkg>` for all Python — never install packages globally.

Inspect each PNG with the Read tool. Check for: content clipping, header rendering, box headers (white on d3-navy), font (Inter not fallback), colors (d3-navy / d3-orange / d3-gray only), TikZ and figures fit inside parent boxes.

### Step 3: Check compilation warnings

```bash
grep -c "Overfull\|Warning" poster.log
```

A handful of underfull-hbox warnings is expected. Investigate `Overfull \hbox` exceeding 50pt (content too wide), `Font ... not found` (use XeLaTeX), or `File ... not found` (missing logo / figure / baposter.cls).

## Overflow & clipping

baposter does NOT push overflow to a new page like the article class — **it silently clips**. This is the #1 cause of broken posters. There's no LaTeX error; you only see it in the rendered PNG.

### Prevention

1. **Budget box content BEFORE writing LaTeX** (see Content development → Budget content space).
2. **Compile after each box is filled** — catch clipping early.
3. **Shorten text, don't shrink fonts** — baposter sets its own scale per `a0paper`; manually scaling text breaks consistency.
4. **One equation per box (max two)** — equations consume a lot of vertical space at poster scale.
5. **Lists: max 5-6 items per box.**
6. **Tables: max 6 rows** at default scale.
7. **One `\keypoint{}` per box max.**

### Detection checklist

- [ ] Output is exactly 1 page (extra pages = layout collapse)
- [ ] No box body content clipped at its bottom edge
- [ ] No infobox/card/figure overflows its parent box
- [ ] All `\keypoint{}` callouts fully render
- [ ] Author line fully visible (not truncated by logo cell)
- [ ] No "Overfull \hbox" warnings > 50pt in the .log

### If clipping detected

1. Identify the overfull box (visually scan the rendered PNG).
2. Cut the lowest-priority content in that box.
3. If still clipping: shorten lists (max 4 items), reduce table rows, compress prose.
4. If a `\keypoint{}` causes clipping: move it earlier or shorten its text.
5. **Never shrink fonts.** Cut content.
6. Recompile and re-render.

## Review

**Review depth.** Three levels; the user picks one in words, otherwise use `standard` and say so in one line ("Review: standard. Say 'light' to skip the reviewer agents.").

| Depth | What runs | Token cost |
|---|---|---|
| `light` | The automated checks (compile log, page count, clipping checklist) and your own look at the rendered pages. No reviewer agents. | almost none |
| `standard` (default) | The two reviewer agents below, in parallel, one round. Apply their fixes, recompile, rerun the automated checks. No second review. | about 100k tokens, largely independent of document length |
| `full` | The two reviewers in a loop until both scores are at least 9, at most 4 rounds; then hand the remaining findings to the user. | two to four times `standard` |

"quick", "no review", "light", "short on tokens", "cheap" mean `light`. "thorough", "full review", "submission-ready" mean `full`. In `light`, replace the reviewers by one pass of your own over both rubrics and list what you checked.

For `standard` and `full`, load `references/dual-agent-review.md`: it has the two reviewer prompts (Content, Visual Design), the orchestrator summary template, and the score-to-README protocol. Dispatch both agents in parallel (single message, two `Agent` tool calls with `subagent_type=Explore`); both inspect the rendered PNG. **Surface their scores and feedback to the user in chat**: what was checked, what passed, what failed, what was changed. `standard` stops after one round of fixes; `full` iterates until both Overall scores are at least 9, or 4 rounds elapse.

## Editing & versioning

When editing an EXISTING poster, **use git, not filename prefixes**. The working file is always `poster.tex` and produces `poster.pdf` — stem-match invariant.

1. **Detect editing mode.** Print `[HH:MM:SS] EDITING MODE: Found existing poster -- [filename]`.
2. **Snapshot via git BEFORE editing:**
   ```bash
   cd <repo-with-the-poster>
   git add poster/drafts/poster.tex && git commit -m "Pre-edit snapshot"
   ```
   If git isn't available (rare): `cp poster.tex .poster.tex.pre-$(date +%s)`. Git is strongly preferred.
3. **Read the existing file** — understand box structure, content, style.
4. **Apply edits in place** to `poster.tex`. Single working file; do not create `v2_poster.tex`.
5. **Document changes in `revision_notes.md`:**
   ```markdown
   ## Revision YYYY-MM-DD HH:MM:SS
   - Replaced placeholder figure with method-overview.pdf
   - Updated Empirical Results table with final numbers
   - Resulting content score: 9/10, visual score: 9/10
   ```
6. **Compile and validate** — see Compilation and validation above.

**Promotion to `final/`:** when the user approves, copy `poster/drafts/{poster.tex, poster.pdf, baposter.cls, assets/}` into `poster/final/` with the SAME filenames. Write `final/README.md` capturing the date, short title, venue, and final review scores.

## Macros & styling — at a glance

The most-used macros for a typical poster. See `references/macros-and-styling.md` for the full inventory (more cards, font-size table, full color palette, table conventions, title/subtitle syntax).

| Macro | Use |
|---|---|
| `\dthreelogos` | WUE + DataDrivenDecisions logos, bottom-aligned in the header logo cell |
| `\highlight{text}` | Inline d3-orange bold; 2-3 per box max |
| `\keypoint{text}` | d3-navy tinted callout box with left accent; 1 per box max |
| `\headerbox{Title}{keys}{content}` | Primary content box (baposter built-in) |
| `\hhrule` | Horizontal d3-navy rule (separator inside a box) |

TikZ styles available inside `tikzpicture`: `card`, `card gray`, `card highlight`, `card alert`, `infobox`, `tag`.

D3 colors (use ONLY these): `d3-navy`, `d3-orange`, `d3-gray`, `d3-lightblue`, `d3-darkblue`. Never `red`/`blue`/`green` or arbitrary hex codes.

## Error handling

Load `references/error-handling.md` when a compile error or rendering issue appears. Known issues:

1. **Class file not found** — `baposter.cls` must sit next to `poster.tex`, not under `assets/`.
2. **Font not found (Inter)** — use XeLaTeX, verify `assets/fonts/` exists.
3. **`\d` already defined (siunitx conflict)** — d3-poster.sty does `\let\d\relax` before loading siunitx; outdated .sty means recopy.
4. **Header backgrounds rendered without fill** — the baposter `headershade` case bug. Set `headershade=plain` explicitly (already in Document Skeleton).
5. **Calibri font error** — using unpatched upstream baposter.cls. Use the vendored copy at the skill root.
6. **Box content clipped (no LaTeX error)** — baposter silently clips overflow. See Overflow & clipping above.

## Quality checklist

Before marking a poster complete:

**Files & structure**
- [ ] `baposter.cls` at `poster/drafts/` root, next to `poster.tex`
- [ ] `assets/d3-poster.sty`, `assets/fonts/`, `assets/logos/` present
- [ ] No leftover `example-poster.tex` / `example-poster.pdf` in the project
- [ ] PDF compiles without errors using XeLaTeX
- [ ] PDF is exactly 1 A0 page
- [ ] `poster.pdf` stem matches `poster.tex`

**Versioning (if editing)**
- [ ] Pre-edit snapshot committed via git
- [ ] Single `poster.tex` edited in place — no v2_/v3_ filenames
- [ ] `revision_notes.md` updated with a dated entry

**Content**
- [ ] Column count confirmed with user (default 2)
- [ ] Title is `\Huge\raggedright`, single line, no subtitle (unless user asked)
- [ ] Author block is one short line; logos bottom-aligned next to it
- [ ] Motivation: 60-100 words with 1 `\highlight{}`, NO figure
- [ ] Problem: 1-2 equations + 1 `\keypoint{}`
- [ ] Approach: 100-180 words + 1 figure (no caption)
- [ ] Empirical Results: 2-3 infoboxes + comparison table + inline Literature
- [ ] No standalone Literature box (folded into Results bottom)
- [ ] Figures have NO captions unless user explicitly asked
- [ ] Each box has at most 1-2 figures
- [ ] `\highlight{}` ≤ 3 per box; `\keypoint{}` ≤ 1 per box
- [ ] Only D3 colors used
- [ ] Tables use `booktabs` and NeurIPS style (baselines above `\midrule`)
- [ ] Conciseness rules applied (no throat-clearing, verb-first bullets, one idea per sentence)

**Visual validation**
- [ ] PDF rendered to PNG and inspected
- [ ] No box content clipped at any edge
- [ ] Header: both logos render, title fully visible
- [ ] Inter font renders correctly (not fallback serif)
- [ ] Colors: d3-navy for box headers, d3-orange for highlights only
- [ ] All figures and tables fit within parent boxes
- [ ] No "Overfull \hbox" warnings > 50pt

**Review**
- [ ] Review done at the chosen depth: `light` checks and own pass listed; `standard` one reviewer round applied; `full` Content and Visual scores ≥ 9/10
- [ ] `final/README.md` written with date, title, venue, scores

## Decision points

### Ask the user when

- **Input tier** (A/B/C/D) — first question, before everything else
- **Paper source** — if multiple paper candidates exist
- **Column count** — default 2; confirm before assuming 3
- **Title & subtitle** — title confirmation; subtitle off by default, ask only if mentioned
- **Author block** — 1-2 names + affiliation + email on one line
- **Headline metric** — the single number a viewer should remember (goes in an `infobox`)
- **Figure preference** — which 1-2 figures from the paper to feature
- **Architecture figure** — if detected: use-as-is / simplify / replace / skip (see `references/extraction.md` §8)
- **Captions on figures** — off by default; ask only if mentioned (e.g., venue requirement)
- **Bibliography filtering** — which 3-5 references to feature in the Literature paragraph
- **Knowledge enrichment** — vault recall / NotebookLM / both / skip (only when the request is high-level)
- **Review depth** — do not ask; use `standard` unless the user's words pick `light` or `full`, and say which one runs

### Decide independently

- Which `\headerbox` keys to use for positioning (within the chosen column count)
- Which TikZ macro fits each piece of content (`infobox` vs. `card` vs. `card alert`)
- Spacing adjustments within a box (`\vspace`)
- Default 2-column layout (Motivation+Problem | Approach+Results) unless user requests otherwise
