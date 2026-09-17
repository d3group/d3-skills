# Extraction Reference — paper text, tables, figures

Detailed extraction commands for each input tier. Load this file when you've identified the user's input tier and are about to pull content from their paper source. See the main SKILL.md ("Paper / Repo Scanning Workflow") for the tier-detection workflow.

## Table of contents

1. Tier A/B (LaTeX source) — extraction mapping table
2. Tier C (PDF only) — text extraction
3. Tier C — figure extraction (vector-first, with raster fallbacks)
4. Tier C — low-resolution raster warning protocol
5. Tier D (Word .docx) — text and image extraction
6. Tier D' (notes / topic only) — interactive prompt template
7. On-disk figure format priority (PDF > EPS > SVG > PNG > JPG)
8. Architecture-figure interview (when to use as-is, simplify, replace, skip)

## 1. Tier A/B (LaTeX source available)

Extract from the .tex source — this is the highest-fidelity path:

| Paper element | Poster element | Extraction heuristic |
|---|---|---|
| `\title{...}` | Poster title | Use verbatim; shorten ruthlessly if it wraps past 2 lines |
| `\author{...}` | Author block | Take first 1-2 authors + their affiliation |
| `\begin{abstract}...\end{abstract}` | Motivation lead text | Condense to 2-3 sentences; surface the headline metric |
| `\section{Introduction}` first paragraph | Motivation body | Extract problem statement and "why now" |
| `\section{Problem|Model|Setup|Formulation}` | Problem box | Pull formal equations and definitions |
| `\section{Method|Approach|Algorithm}` | Approach box | Bullet the core idea + key equation |
| `\section{Results|Experiments|Evaluation}` | Empirical Results | Headline numbers + main comparison table |
| `\begin{table}...\end{table}` | Results table | Convert to `booktabs` (NeurIPS style) |
| `\includegraphics{...}` | Figure list | Inventory; resolve to actual PDF/PNG/SVG files on disk |
| `references.bib` | Literature paragraph | Filter to citations actually `\cite{}`d; pick 3 key ones |

## 2. Tier C — PDF text extraction

Extract page text with `uv run --with pymupdf`:

```bash
uv run --with pymupdf python -c "
import fitz, sys
doc = fitz.open('paper.pdf')
for i, page in enumerate(doc):
    print(f'=== Page {i+1} ===')
    print(page.get_text())
doc.close()
" > /tmp/paper-text.txt
```

**Heads-up on PDF text extraction:** PyMuPDF preserves reading order well for single-column papers but struggles with two-column layouts (text from both columns interleaves). For two-column papers, also extract per-block via `page.get_text("blocks")` and sort by `y` then `x` to recover reading order.

Then parse the text dump to identify the title (first big text on page 1), abstract (paragraph after the word "Abstract"), section headers (capitalised lines followed by paragraphs), and references (entries starting with `[N]` or `Author, Year`). The mapping table from §1 still applies; you're just sourcing from extracted text instead of .tex commands.

## 3. Tier C — figure extraction (prefer vector, fall back to raster)

Paper PDFs typically contain a mix of:

- **Vector figures** (TikZ-drawn schematics, matplotlib PDFs, vector logos) — drawn as page commands, not embedded as images
- **Raster figures** (photos, screenshots, low-res charts) — embedded as image objects

The naive `page.get_images()` extractor **only catches the raster ones and silently misses the vector figures** — often the most important ones on the paper. Use the right approach for each kind:

### Approach 1 (preferred, vector-preserving): crop the PDF page to the figure region

Produces a small standalone PDF that stays vector and prints sharp at any size. Requires knowing the figure's bounding box; the heuristic is to search for the caption ("Figure N:") and take the rectangle above it.

```bash
mkdir -p extracted-figures/
uv run --with pymupdf python -c "
import fitz
doc = fitz.open('paper.pdf')
for page_idx, page in enumerate(doc):
    for cap_match in page.search_for('Figure', quads=False) + page.search_for('Fig.', quads=False):
        bbox = fitz.Rect(page.rect.x0, page.rect.y0, page.rect.x1, cap_match.y0 - 6)
        if bbox.height < 80:
            continue
        out = fitz.open()
        out_page = out.new_page(width=bbox.width, height=bbox.height)
        out_page.show_pdf_page(out_page.rect, doc, page_idx, clip=bbox)
        name = f'extracted-figures/p{page_idx+1}-y{int(cap_match.y0)}.pdf'
        out.save(name); out.close()
        print(name)
doc.close()
"
```

Verify the output is vector by re-rendering one at multiple DPIs (pixel dimensions should scale linearly with DPI):

```bash
uv run --with pymupdf python -c "
import fitz
for dpi in (75, 300, 600):
    d = fitz.open('extracted-figures/p3-y412.pdf')
    pix = d[0].get_pixmap(dpi=dpi)
    print(f'{dpi}dpi: {pix.width}x{pix.height}')
    d.close()
"
```

The caption-search heuristic is rough — expect false positives ("Fig. 1 (a)" inline references) and false negatives (captions PyMuPDF can't locate). **Show the user the candidate PDFs and ask which to use** rather than placing automatically.

### Approach 2 (catches embedded raster)

Use this in addition to Approach 1 — it catches photos, screenshots, and low-res charts that aren't in vector form:

```bash
uv run --with pymupdf python -c "
import fitz
doc = fitz.open('paper.pdf')
for page_idx, page in enumerate(doc):
    for img_idx, img in enumerate(page.get_images(full=True)):
        xref = img[0]
        pix = fitz.Pixmap(doc, xref)
        if pix.n - pix.alpha >= 4:
            pix = fitz.Pixmap(fitz.csRGB, pix)
        out = f'extracted-figures/p{page_idx+1}-img{img_idx+1}.png'
        pix.save(out); pix = None
        print(out)
doc.close()
"
```

Then run the resolution check (§4) and warn about any PNG that won't survive A0 scaling.

### Approach 3 (last resort): render the full page at high DPI

Use only when Approach 1 fails to capture a vector figure and the user can't redraw:

```bash
uv run --with pymupdf python -c "
import fitz
doc = fitz.open('paper.pdf')
for i, page in enumerate(doc):
    pix = page.get_pixmap(dpi=600)
    pix.save(f'extracted-figures/page-{i+1}-600dpi.png')
    print(f'page-{i+1}-600dpi.png: {pix.width}x{pix.height}')
doc.close()
"
```

Stays sharp for A0 print at 600 dpi but the file is large (~20-30 MB per A4 page). Don't use as default.

## 4. Tier C — low-resolution raster warning protocol

A figure rendered at column-width (~38 cm in a 2-column A0) needs **at least 2200 px wide for 150 dpi crispness**. Below ~1500 px visibly pixelates at A0 print.

Threshold derivation: A0 portrait is 84 cm wide; 2 columns means ~38 cm/column = 14.96 in × 150 dpi ≈ 2244 px. Below that, pixel density on the printed sheet drops below ~60 dpi, which is the eye's threshold for "visibly pixelated" at viewing distances of 30-50 cm.

Run this after extraction (Approach 2 or 3):

```bash
uv run --with pymupdf python -c "
import fitz, os
for f in sorted(os.listdir('extracted-figures')):
    if not f.endswith(('.png', '.jpg', '.jpeg')):
        continue
    pix = fitz.Pixmap(os.path.join('extracted-figures', f))
    flag = 'OK' if pix.width >= 2200 else ('LOW' if pix.width >= 1500 else 'TOO LOW')
    print(f'{f}: {pix.width}x{pix.height} -- {flag}')
"
```

If any figure is flagged `LOW` or `TOO LOW`, surface this to the user:

```
Extracted figures and their poster-scale legibility:
  p3-img1.png: 1840x1200 -- LOW    (will look soft at column width)
  p5-img2.png: 720x540   -- TOO LOW (will visibly pixelate)
  p7-img3.png: 2640x1980 -- OK

For p5-img2.png (the architecture diagram), I recommend redrawing in TikZ.
Want me to sketch a clean 3-block version based on the figure description in the paper text?
```

If the user agrees to redraw, go to `references/tikz-recipes.md`. If they decline, place the extracted PNG anyway — their call.

## 5. Tier D — Word .docx extraction

Text extraction (preserves style tags so headings can be detected):

```bash
uv run --with python-docx python -c "
from docx import Document
doc = Document('paper.docx')
for i, p in enumerate(doc.paragraphs):
    style = p.style.name if p.style else 'Normal'
    print(f'[{style}] {p.text}')
" > /tmp/paper-text.txt
```

Image extraction (.docx is a zip; images live in `word/media/`):

```bash
mkdir -p extracted-figures/
uv run --with python-docx python -c "
import zipfile, os, shutil
with zipfile.ZipFile('paper.docx') as z:
    for name in z.namelist():
        if name.startswith('word/media/'):
            with z.open(name) as src, open(os.path.join('extracted-figures', os.path.basename(name)), 'wb') as dst:
                shutil.copyfileobj(src, dst)
                print(f'extracted-figures/{os.path.basename(name)}')
"
```

Section headers in Word are usually `Heading 1` / `Heading 2`; map to poster sections the same way as Tier A/B (§1).

## 6. Tier D' — no file, topic only

Skip extraction and interview the user directly. Use this prompt template:

```
I don't see a paper source. To draft a poster I need:
1. Title (one line):
2. Authors + affiliation + email (one line):
3. Motivation -- why this matters (60-100 words):
4. Problem -- formal setup, key equation if any (80-150 words):
5. Approach -- the method in 2-3 sentences:
6. Headline result -- the single number a viewer should remember:
7. Comparison table (if any) -- rows are methods, columns are metrics:
8. References -- 3 key cites (Author Year, Venue):

Paste your answers in any format; I'll structure them.
```

## 7. On-disk figure format priority

When the same figure exists in multiple formats on disk, **always prefer vector**. Falling-back order:

1. `figure.pdf` (vector, preferred)
2. `figure.eps` (vector, legacy; XeLaTeX handles via `\includegraphics`)
3. `figure.svg` (vector, but requires conversion — use `uv run --with cairosvg python -c "..."` to convert to PDF first; do not link SVG directly in LaTeX)
4. `figure.png` (raster, accept only if no vector version exists)
5. `figure.jpg` (raster, last resort)

The scanner should **deduplicate by stem**: if `figures/method-overview.pdf` and `figures/method-overview.png` both exist, list only the PDF and silently skip the PNG:

```bash
find figures/ figs/ plots/ images/ -maxdepth 2 -type f \( -name "*.pdf" -o -name "*.eps" -o -name "*.svg" -o -name "*.png" -o -name "*.jpg" \) 2>/dev/null \
  | awk -F/ '{
      stem=$NF; sub(/\.[^.]+$/, "", stem);
      ext=$NF; sub(/^.*\./, "", ext);
      rank = (ext=="pdf"?1:ext=="eps"?2:ext=="svg"?3:ext=="png"?4:5);
      if (!(stem in best) || rank < best_rank[stem]) {
        best[stem]=$0; best_rank[stem]=rank;
      }
    }
    END { for (s in best) print best[s] }'
```

When presenting the inventory, note the format ranking so the user understands why a PNG was dropped in favor of its PDF sibling. If only a PNG is available and the figure is critical, **ask the user to re-export from the original source as PDF** (matplotlib `savefig('foo.pdf')`, TikZ standalone, etc.). For poster-scale legibility, regenerating as PDF is almost always worth the 30 seconds.

**Why vector first:** A0 prints at ~84 cm wide; even a small figure on a poster is 25+ cm. Raster at paper-column resolution (~800 px wide) becomes 30 px/cm at A0 — visibly pixelated. Vector formats render at print resolution regardless of physical size.

## 8. Architecture-figure interview

Paper architecture figures (ML pipelines, system diagrams, method-overview schematics) are usually the single most important figure on a poster — but they are also usually too dense for poster-scale legibility. A figure designed to be studied at 12pt in a paper column becomes illegible at a 30 cm panel.

When the scanner detects what looks like an architecture figure (filename or surrounding caption contains "architecture", "pipeline", "overview", "framework", "system", "model", "schema", "diagram"), **interview the user** before placing it. AskUserQuestion options:

- **Use as-is** — paper's figure transfers directly; quick path.
- **Simplify (recommended)** — redraw a stripped-down version showing only the 3-5 essential blocks, drop sub-components, drop tiny labels. Best for poster scale.
- **Replace with a 3-block diagram** — build a fresh TikZ schematic with just Input → Method → Output (see `references/tikz-recipes.md` Recipe 1).
- **Skip the figure entirely** — if a tight equation or table tells the story better.

Follow-up questions when "Simplify" is chosen:

1. *"Which 3-5 components are the must-keep blocks?"* (drop everything else)
2. *"Are the inter-block arrows labelled? If yes, which labels matter at poster scale?"*
3. *"Do you want me to redraw in TikZ from scratch, or strip elements from the existing PDF?"*
4. *"Color scheme: keep paper colors, or remap to d3-navy / d3-orange / d3-gray for visual consistency?"*

If the user picks "Use as-is" but the figure clearly won't be legible (paper figure has 8pt labels), push back once: *"This figure has very small labels (e.g., 'attn_head_proj') — at A0 scale they'll still be small. Want me to enlarge or simplify before placing it?"*

If the figure is from a TikZ source in the paper repo (`*.tex` containing `\begin{tikzpicture}`), prefer **simplification at the TikZ source level** (drop nodes, increase font sizes, recompile to PDF) over post-hoc cropping of the rendered PDF.
