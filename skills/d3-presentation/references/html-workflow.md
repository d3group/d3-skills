# HTML Workflow (interactive deck)

One self-contained HTML file, written as Python. Read `SKILL.md` first for the shared rules; this file covers what is specific to HTML. The API mirrors the LaTeX macros, so an outline written for one format ports to the other.

## Project structure

```
my_talk/
├── slides.py           the deck; long talks may split into c_*.py modules imported by slides.py
├── figures/            png, jpg, jpeg, svg, or pdf files used by fig()
├── d3deck/             the engine (copied by init.py, never edited per talk), with fonts/, logos/ and mathjax/ inside
├── dist/my_talk.html   build output, one file
├── dist/my_talk.pdf    optional print export (shoot.py --pdf)
└── shots/              per-step screenshots and contact sheets from shoot.py
```

## 1. Scaffold

```bash
uv run <skill-dir>/assets/html/init.py my_talk        # creates ./my_talk with a starter slides.py
```

## 2. Anatomy of slides.py

```python
from d3deck import *

meta(title='Action title', subtitle='Optional', date='Date and Location',
     presenter='Author Name', chair='Chair of Information Systems and Business Analytics',
     sections=['Introduction', 'Methodology', 'Results', 'Conclusion'],
     numbering='content', look='klar', reveal='ghost')

titleslide()
section(1, question='Which question does this part answer?')
onecol(K('Problem', 'Action title summarizing the key message'), '''
<ul>
 <li>Point one</li>
 <li data-s="1">Point two, revealed on the second step</li>
</ul>''', steps=2, notes='What to say.', src='One-line summary for the search palette')
thankyou()
build('my_talk')          # writes dist/my_talk.html
```

`uv run slides.py` builds and prints `N slides · M steps · X MB → dist/my_talk.html`.

- `meta()` must come first; it resets the deck. `sections` takes 1 to 7 names. `tracker=True` shows a section tracker in the footer band of content slides (it replaces the chair | presenter text there). `numbering='all'` counts every slide like Beamer; `'content'` matches the `contentnumbering` option: title, agenda, section, and thank-you slides carry no number and backup numbering restarts after `appendix()`.
- The title slide shows title and subtitle, like the LaTeX one. meta(date=...) is stored for the manifest only, like \date in LaTeX; put the date into the subtitle if it should appear.
- Every slide function accepts `steps=1, notes='', src='', cls='', group=None, num=True`. `src` is a one-line summary that is never rendered; it feeds the `/` search palette. `cls` adds classes to the `<section>` for scoped CSS. `num=False` hides and skips the number.

## The look

`meta(look='klar')` is the default and follows the talk design used for D3 defenses: every content slide has the section tracker on top, a title made of an orange kicker and one claim in a light weight, a body in dark ink at 22 px with generous whitespace, the takeaway on a fixed baseline with an orange tick, and a quiet mono foot with the section name, `page / total` and the D3 logo. The university logo and the seal appear on the title and thank-you slides only. There is no agenda slide: the tracker and the question dividers carry the structure (`agenda()` still works if an audience expects one).

`meta(look='beamer')` draws the frame of the LaTeX template instead (university logo, navy bar, footer tab, bold title; `tracker=True` moves the tracker into the footer band). Choose it when the HTML deck must match a PDF deck slide for slide.

## 3. Slide functions

| HTML | LaTeX | Notes |
|---|---|---|
| `titleslide()` | `\titleslide` | title template with the seal watermark |
| `agenda()` | `\showagenda` | numbered circles, clickable to the section dividers that exist |
| `section(n, question='')` | `\showsection{n}` | 1-based; also sets the current section for tracker and jump tabs. In the klar look the divider shows `Part n of N` and the question this part answers |
| `statement(html)` | none | one sentence at 50 px, alone on the slide; mark the one word that carries it with `<b>` (orange). A few per talk, at the turns of the argument |
| `facts(title, items, takeaway='')` | none | one to four headline numbers side by side; `items` are `(value, label)` or `(value, label, True)` for the single accented number |
| `K(kick, claim, sub='')` | none | builds a title: orange kicker (the category, one or two words) plus the claim; pass it wherever a title goes |
| `onecol(title, html)` | `\onecol` | body box 1133 by 432 px |
| `twocol(title, left, right)` | `\twocol` | two boxes of 547 px |
| `twocoltakeaway(title, left, right, takeaway)` | `\twocoltakeaway` | shorter boxes, takeaway box below |
| `slide(title, html)` | none | frame and title only; position elements yourself (for example a full-width figure) |
| `thankyou()` | `\thankyouslide` | "Thank You!" and the presenter |
| `appendix()` | `\appendix` | everything after is backup |
| `backuphome(title='Backup')` | none | hub listing the backup slides by `group`; H jumps here |
| `build(name)` | | writes `dist/<name>.html` |

## 4. Fragments (compose inside bodies)

| Helper | Returns |
|---|---|
| `columnheader('Left')` | bold column heading |
| `highlight('text')` | bold orange text, the one orange element |
| `codebox(code)`, `errorbox(code)`, `terminalbox(code)` | monospace boxes; code is HTML-escaped for you |
| `chevrons(active, phases)` | process flow with 2 to 5 phases, each `(label, title)` or a title; `active` is 1-based |
| `timeline(2025, 2028, [(label, 'teal!60', 0, 0.5, row, 'M1'), ...])` | Gantt timeline; start and end in 0..1, row 1 at the bottom |
| `takeaway('sentence')` | the orange-ruled box, usable in `onecol` |
| `stat('1.6M', 'team matches')`, `stat(..., accent=True)` | card with a color edge |
| `bignum('38 %', 'caption')` | one large number |
| `fig('name', width='100%')` | embedded image with its aspect ratio pinned; see section 6 |
| `step(n, html, soft=False, until=None)` | wraps html so it is ghosted until step n |
| `scrim(off, left, top, right, bottom)` | white cover over a region, lifted at step `off` |
| `mark('name')`, `jump('name')`, `link('name', 'text')` | click-to-jump navigation |
| `crumb(('Ch. 5', 'ch5'), ('Descriptives', None))` | breadcrumb strip for backup slides |
| `mix('teal!60')` | a tint as hex, for inline styles; brand tokens plus white and black |
| `css('.mine{...}')` | append a stylesheet fragment; scope it with `cls=` |

Layout helpers in the stylesheet: `.grid2`, `.grid3`, `.grid4`.

## 5. Step builds

A step reveals something that is already laid out. Elements of later steps stand as pale grey ghosts (15 percent opacity) in their final place, so nothing is ever removed, nothing moves between steps, and the audience sees how much is still to come. `meta(..., reveal='hide')` makes them fully invisible instead, for decks where a ghost would give away the point; `data-soft="1"` dims a single element to 42 percent in either mode.

```python
onecol('Three mechanisms explain the effect', '''
<div class="grid3">
 <div>''' + stat('A', 'first') + '''</div>
 <div data-s="1">''' + stat('B', 'second') + '''</div>
 <div data-s="2" data-soft="1">''' + stat('C', 'third, soft-ghosted to 42 percent') + '''</div>
</div>''' + scrim(3, 0, '60%', 0, 0), steps=4)
```

- `data-s="k"`: sharp from step k (0-based). `data-soft="1"`: ghost to 42 percent instead of 15. `data-until="k"`: ghosted again after step k.
- `scrim(off, l, t, r, b)`: covers a rectangle of the slide (px numbers or `%` strings) and lifts at step `off`. Use it to reveal a grid cell by cell.
- `steps=` on the slide is the number of steps and draws the step dots under the top-right bar.
- Never `display:none`; the build warns. Rules for good builds are in the style guide, section Step builds.

## 6. Figures

Put files into `figures/`. `fig('plot')` finds `plot.png`, `.jpg`, `.jpeg`, `.svg`, or `.pdf` (in that order), embeds it as base64, and sets `aspect-ratio` from the image, so the container never distorts it. PDFs are rasterized once with `pdftoppm` (poppler) into `figures/.cache/`.

Annotated figure: wrap the image and an SVG in a relative box and draw in percentages, so the callout stays anchored when the figure scales.

```python
twocol('The gap is largest for lower-rated players',
       '<div style="position:relative">' + fig('gap', width='100%') + '''
<svg viewBox="0 0 100 100" preserveAspectRatio="none" style="position:absolute;inset:0;width:100%;height:100%">
 <circle cx="72" cy="38" r="9" fill="none" stroke="var(--orange)" stroke-width="1" vector-effect="non-scaling-stroke"/>
</svg></div>''',
       '<ul><li>...</li></ul>')
```

## Math

Formulas are typeset by MathJax (3.2.2, SVG output). Write LaTeX inside any body, title, takeaway or fragment: inline `$…$` or `\(…\)`, display `$$…$$` or `\[…\]`. Use raw strings so the backslashes survive: `r'<p>We choose $\hat\beta$ such that</p>\[ \hat\beta = \arg\min_\beta \E\big[\norm{y - X\beta}^2\big] \]'`. Formulas copied from the paper or the Beamer deck work as they are (AMS environments such as `aligned` and `cases`, `\operatorname*`, `\boldsymbol`, `\textcolor{#F39200}{…}`).

- The build embeds MathJax only when a slide contains math (the build line then says `MathJax embedded`; the file grows by about 2.2 MB and still works offline). `meta(math=True)` or `meta(math=False)` overrides the detection.
- The paper's macros go into `meta(macros={'E': r'\mathbb{E}', 'norm': r'\lVert #1 \rVert'})`; the number of arguments is read from the `#n` in the body.
- Math takes the colour and size of its surroundings, so it ghosts with `data-s` like text and turns orange inside `highlight()`. A display formula is one visual element: give it air and no more than one or two per slide.
- Dollar signs: `codebox()` and `terminalbox()` are never scanned, and a single `$` on a slide is left alone. Two literal dollars in one paragraph would pair up as math: write them as `<span class="nomath">$</span>`.
- The build's word budget counts a formula as one word.
- Speaker notes are plain text; formulas in `notes=` are not typeset.
- `assets/html/example-slides.py` has a working math slide (section 4): display and inline formulas, macros, one build.
- `shoot.py` lists every formula MathJax cannot render (unknown command, missing brace) under `MATH:` and exits with 1, like an overflow.

## 7. Custom CSS

`css()` appends a fragment after the shared stylesheets. Scope it with a class you also pass as `cls=`:

```python
css('.compare .body{display:grid;grid-template-columns:1fr 1fr;gap:24px}')
slide('Two models side by side', '<div class="body">...</div>', cls='compare')
```

Type sizes are tokens: `--fs-LARGE 49px`, `--fs-Large 41px` (titles), `--fs-large 34px`, `--fs-normal 31px` (column headers), `--fs-small 28px` (body), `--fs-footnote 25px`, `--fs-script 23px` (code), `--fs-tiny 17px` (footer). Use tokens for every size.

## 8. Backup app

```python
thankyou()
appendix()
backuphome()                                   # hub, reachable with H and the Backup jump tab
mark('ch5')
onecol('Backup: ...', crumb(('Ch. 5', None)) + '...', group='Ch. 5')
onecol('Backup: ...', crumb(('Ch. 5', 'ch5'), ('Descriptives', None)) + link('ch5', 'back') , group='Ch. 5')
```

`group=` labels the entries on the hub. `mark()` names the next slide; `jump()`/`link()`/`crumb()` target marks and are resolved at build time (an unresolved name fails the build). `crumb()` needs `backuphome()`.

## 9. Speaker notes

`notes='...'` on any slide. N opens a presenter window (current slide, next step, notes, clock, timer; T resets the timer). Keys work in either window. If the popup is blocked, N toggles a notes drawer in the main window. Notes are embedded in the file and one keypress away for anyone who opens it; build with build('my_talk', notes=False) before sharing a deck whose notes are private. In the notes window only the navigation keys and T act; F and P belong to the main window.

## 10. Build

`uv run slides.py`. The build fails loudly on: a slide before `meta()`, `section(n)` outside the section list, an unresolved or duplicate mark, a missing figure, a PDF figure without `pdftoppm`, `chevrons` with fewer than 2 or more than 5 phases, a timeline range outside 0..1. It warns on `display:none`, on more than 7 sections, and on what makes a deck look cluttered: more than 4 steps on a slide, one step per bullet, more than about 75 body words or 6 bullets, more than two kinds of visual component on one slide, and builds on more than 40 percent of the content slides. Resolve these warnings; they are the difference between a calm and a busy deck.

## 11. Verify

```bash
uv run --with playwright --with pillow d3deck/shoot.py dist/my_talk.html --contact              # every slide, every step -> shots/
uv run --with playwright --with pillow d3deck/shoot.py dist/my_talk.html --from 3 --to 8         # a range
uv run --with playwright --with pillow d3deck/shoot.py dist/my_talk.html --pdf dist/my_talk.pdf  # print view as PDF
uv run d3deck/shoot.py dist/my_talk.html --chrome                                              # headless Chrome, no packages, no audit
```
First time on a machine: `uv run --with playwright playwright install chromium` (installs the browser Playwright drives).

The script waits 480 ms per step so the 420 ms transition has settled, audits every visible element against the slide box and the body boxes, prints an overflow report, and exits 1 on overflow. Contact sheets need Pillow (the --with pillow above); without it, read the per-step shots in shots/ directly. Then continue at the review depth chosen in Step 0 of `SKILL.md`: light stops here, standard adds one reviewer pass over `slides.py` and `shots/contact_*.png`, full runs the two-agent loop.

## 12. Presenting

| Key | Action |
|---|---|
| Right, PageDown, Space | next step, then next slide |
| Left, PageUp | previous step |
| Down, Up | next or previous slide |
| Home, End | first or last slide |
| F | fullscreen present mode; Esc leaves |
| P | print (one slide per page, final state) |
| / | search palette; Enter jumps |
| H | backup hub |
| N | speaker notes |

`#12.3` in the URL opens slide 12 at step 3. The jump tabs at the top go to the section dividers and the backup.

## 13. Pitfalls

- Overflow is cropped by the body box and invisible in the browser; only the audit and the shots show it.
- A figure container must keep the figure's ratio; `fig()` does this, hand-written `<img>` tags do not.
- Never `display:none` in a build; ghost with `data-s`.
- Look at every step's shot. Wrong order and steps that reveal nothing hide in the intermediate states.
- The engine selector is `.sl`; an audit written against `.slide` checks nothing.
- The deck is one file. Send `dist/my_talk.html`, nothing else is needed.
- Notes ship inside the file unless you build with notes=False.
- A formula written in a normal Python string loses its backslashes (`'\beta'` starts with a backspace character). Use `r'…'` for every string that holds math.

## 14. Checklist before delivery

- [ ] Titles read as the argument on their own
- [ ] One orange element per slide at most
- [ ] Every step reveals something; nothing moves between steps
- [ ] `shoot.py` audit clean; contact sheets inspected
- [ ] Wording rules from the style guide applied
- [ ] Review done at the chosen depth (light: audit clean; standard: one pass applied; full: 9 or better in every category)
