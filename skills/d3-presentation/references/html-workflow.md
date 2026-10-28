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
     numbering='content', look='klar', reveal='ghost', feel='calm')

titleslide()
section(1, question='Which question does this part answer?')
onecol(K('Problem', 'Action title summarizing the key message'), middle(
       '<div class="grid2">' + tile('Point one', ['a keyword line'], kick='First', ico='target') +
       tile('Point two', ['revealed on the second step'], kick='Second', ico='bulb', color='teal', s=1) + '</div>'),
       steps=2, time='0:45', notes='0: point one. 1: point two.', src='One-line summary for the search palette')
thankyou()
build('my_talk')          # writes dist/my_talk.html
```

`uv run slides.py` builds and prints `N slides · M steps · X MB → dist/my_talk.html`.

- `meta()` must come first; it resets the deck. Without `chair=`, the chair line follows `lang`: English by default, "Lehrstuhl für Wirtschaftsinformatik und Business Analytics" with `lang='de'`. `sections` takes 1 to 7 names. `tracker=True` shows a section tracker in the footer band of content slides (it replaces the chair | presenter text there). `numbering='all'` counts every slide like Beamer; `'content'` matches the `contentnumbering` option: title, agenda, section, and thank-you slides carry no number and backup numbering restarts after `appendix()`.
- The title slide shows title and subtitle, like the LaTeX one. meta(date=...) is stored for the manifest only, like \date in LaTeX; put the date into the subtitle if it should appear.
- Every slide function accepts `steps=1, notes='', src='', cls='', group=None, num=True, time=None, provenance=''`. `src` is a one-line summary that is never rendered; it feeds the `/` search palette. `cls` adds classes to the `<section>` for scoped CSS. `num=False` hides and skips the number. `time='0:45'` is the slide's speaking budget: the presenter window paces against the sum, and `shoot.py --slot` compares it with the slot (give every presented slide one, or none). `provenance='Table 3 · N = 38'` prints a small source line on the footer line, right of the footer text, for numbers the audience may ask about; illustrative numbers say so there. It keeps its full width up to half the line (the footer text gives way and is cut first); a longer one is cut with an ellipsis and `shoot.py` warns `provenance cut`, so keep it to a few words and move detail to `notes=`.
- `feel` is the motion budget agreed in Step 1: `'calm'` (default) warns when more than about 40 percent of the content slides build; `'rich'` and `'interactive'` do not. The build warns about every content slide that is text only, whatever the feel.

## The look

Every look is built on the University of Würzburg PowerPoint master (`PPT-Master-Universitaet-Wuerzburg.potx`, 2026 corporate design; the geometry is the master's layout boxes, 1 px = 9525 EMU) and set in the house font Inclusive Sans UW:

- **Content slides.** The new university logo sits top left over a hairline. The title is semibold navy at 32 px, the body box is 1137 by 420 px (two columns of 548 px). The foot reads `presenter | chair | deck title`, the provenance note (`provenance=`) shares that line on the right, taking up to half of it, and the page number stands in a navy tab at the bottom right.
- **Covers.** `titleslide()` follows the master's Deckblatt: `cover='band'` (white with a navy band; the default of the D3 looks), `cover='navy'` (all navy; the default of the uni look) or `cover='photo'` (the Würzburg skyline, about 0.3 MB). Title, subtitle, presenter and date come from `meta()`.
- **Structure slides.** `section(n, question=...)` is a navy divider (Trennseite) with `Part n of N`, a large sky-blue numeral, the part name and its question. `agenda()` lists two-digit numbers and topics. `thankyou(text=..., contact=[...])` is the closing slide (Abschlussseite) with its navy contact box.
- **Seal.** Covers, dividers and the closing slide carry the rector's seal as a corner crop. The CD replaces it by a faculty ornament in faculty communication; until that package is released the seal stands in.
- **Language.** `lang='de'` switches the labels (Teil n von N, Quellenangaben, Kontakt, Vielen Dank) and the default chair line.
- **Fonts and logos.** Inclusive Sans UW (5 faces) and D3 Symbols (an Inter subset for the Greek letters, arrows and math operators Inclusive Sans UW lacks) are embedded, and the logos and seals as vector SVGs, once per file. The font has no tabular figures; numbers that must align go into a table or the mono labels.

`meta(look='klar')` is the default, the D3 look: the D3 logo stands in the master's co-branding slot (top right; on title and closing slides next to the university logo), the section tracker sits in the header between the logos, titles are an orange kicker plus one claim (`K()`), the body is black at 22 px with generous whitespace, and `takeaway=` is the sand bar with an orange rule on a fixed baseline. There is no agenda slide: the tracker and the question dividers carry the structure (`agenda()` still works if an audience expects one). Each divider also lists the part's slides with their numbers (clickable, at most six listed). Navy is the university navy `#02246C`; D3 orange `#F29100` is the only accent, and the seal is blue on navy.

`meta(look='beamer')` is the same D3 frame with the conventions of the LaTeX theme: no tracker unless `tracker=True` (then it takes the footer band), dividers without the slide list, body text at Beamer sizes. Choose it when the HTML deck must match a PDF deck slide for slide.

`meta(look='uni')` drops the D3 branding, for teaching and other university decks (for example a dean's office talk). Coral `#ED6A5B` is the accent for graphic marks (accented numbers, the seal on navy). Berry `#821044` takes the role of D3 orange for text accents (kickers, `<b>` in takeaways and statements), because coral is too light for small text on white. Light blue `#5E8AC7` marks bullets and rules, and `takeaway=` is the sand bar with the master's arrow. The kit colours map onto the palette: `orange` becomes berry. The kit objects are toned down to the master's plain style (no cards, no icons, sans-serif labels).

## 3. Slide functions

| HTML | LaTeX | Notes |
|---|---|---|
| `titleslide(cover=None)` | `\titleslide` | the master's cover: `'band'` (D3 default, both logos), `'navy'` (uni default) or `'photo'` |
| `agenda()` | `\showagenda` | two-digit numbers in sky blue, clickable to the section dividers that exist |
| `section(n, question='')` | `\showsection{n}` | 1-based; also sets the current section for tracker and jump tabs. The navy divider shows `Part n of N`, the part name and the question this part answers; in the klar look also the part's slides |
| `statement(html)` | none | one sentence at 48 px in navy, alone on the slide; mark the one word that carries it with `<b>` (orange). A few per talk, at the turns of the argument |
| `facts(title, items, takeaway='')` | none | one to four headline numbers side by side; `items` are `(value, label)` or `(value, label, True)` for the single accented number |
| `K(kick, claim, sub='')` | none | builds a title: orange kicker (the category, one or two words) plus the claim; pass it wherever a title goes |
| `onecol(title, html)` | `\onecol` | body box 1137 by 420 px |
| `twocol(title, left, right)` | `\twocol` | two boxes of 548 px |
| `twocoltakeaway(title, left, right, takeaway)` | `\twocoltakeaway` | shorter boxes, takeaway box below |
| `slide(title, html)` | none | frame and title only; position elements yourself (for example a full-width figure) |
| `thankyou(text='', contact=None)` | `\thankyouslide` | closing slide: "Thank you" (or `text`) and a navy contact box (`contact`: list of lines; default presenter and chair) |
| `references(items, title='')` | none | reference list (Quellenangaben), small, two columns; exempt from the busy-slide warnings and the text-only lint |
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

Layout helpers in the stylesheet: `.grid2`, `.grid3`, `.grid4`, and `middle(html)` to centre a short object vertically.

The component kit adds the designed objects (tiles with icons, `model()` figures with computed arrows, `bars()`, `gauge()`, `effect()` bars in a `k-table`, `proof()` and `brace()`, `versus()`, `selector()`, `chat()` replicas, `milestones()`, `units()`, instruments) and the Q&A interactions (`k=` keys, `pop()`, `badge(pop=)`, `cite()`, preset chips). Catalogue, examples and the bar every slide should meet: [html-components.md](html-components.md).

## 5. Step builds

A step reveals something that is already laid out. Elements of later steps stand as pale grey ghosts (15 percent opacity) in their final place, so nothing is ever removed, nothing moves between steps, and the audience sees how much is still to come. `meta(..., reveal='hide')` makes them fully invisible instead, for decks where a ghost would give away the point; `data-soft="1"` dims a single element to 42 percent in either mode, and `data-hide="1"` keeps a single element fully invisible on stage until its step (a vote's answer, a quiz solution), while previews and print still show it.

```python
onecol('Three mechanisms explain the effect', '''
<div class="grid3">
 <div>''' + stat('A', 'first') + '''</div>
 <div data-s="1">''' + stat('B', 'second') + '''</div>
 <div data-s="2" data-soft="1">''' + stat('C', 'third, soft-ghosted to 42 percent') + '''</div>
</div>''' + scrim(3, 0, '60%', 0, 0), steps=4)
```

- `data-s="k"`: sharp from step k (0-based). `data-soft="1"`: ghost to 42 percent instead of 15. `data-hide="1"`: no ghost on stage, for a reveal the ghost would give away. `data-until="k"`: ghosted again after step k.
- `scrim(off, l, t, r, b)`: covers a rectangle of the slide (px numbers or `%` strings) and lifts at step `off`. Use it to reveal a grid cell by cell.
- `steps=` on the slide is the number of steps and draws the step dots under the top-right bar.
- The kit helpers take `s=` for the same purpose (`tile(..., s=1)`, `edge(..., s=2)`, `bar(..., s=1)`).
- The engine marks the slide on screen with `.is-current` and every `data-s` element whose step is reached with `.is-shown`; motion written with `css()` keys on these (html-components.md, section Motion). Previews, the overview and print never carry `.is-current`, so they show end states.
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

Type sizes are tokens: `--fs-LARGE 49px`, `--fs-Large 41px` (titles), `--fs-large 34px`, `--fs-normal 31px` (column headers), `--fs-small 28px` (body), `--fs-footnote 25px`, `--fs-script 23px` (code), `--fs-tiny 17px` (footer); the kit's components use `--k-lg 26px`, `--k-md 21px`, `--k-sm 19px`, `--k-xs 16px`, `--k-mi 11.5px`. Use tokens for every size.

`js()` appends deck-local JavaScript after the engine and the kit, for live modules (`D3Deck.live(...)`, html-components.md section 3.8).

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

`notes='...'` on any slide. Start with what each step does (`0: ... 1: ...`) and end with the transition sentence when useful. N or S opens the presenter window: the current slide, the next step, the notes, a clock and the elapsed time; when slides carry `time=`, a pace line says "on pace", "ahead by m:ss" or "behind by m:ss" against the budgets up to this slide. Chrome and Edge ask once for permission to place the window on the second screen. T resets the timer, P pauses it (in the presenter window only; in the main window P prints). Keys work in either window, and clicks on buttons and slider input on the presenter's current slide are relayed to the projected slide, so demos and popovers are driven from the laptop. If the popup is blocked, N toggles a notes drawer in the main window. Notes are embedded in the file and one keypress away for anyone who opens it; build with build('my_talk', notes=False) before sharing a deck whose notes are private.

## 10. Build

`uv run slides.py`. The build fails loudly on: a slide before `meta()`, `section(n)` outside the section list, an unresolved or duplicate mark, a missing figure, a PDF figure without `pdftoppm`, `chevrons` with fewer than 2 or more than 5 phases, a timeline range outside 0..1. It warns on `display:none`, on more than 7 sections, and on what makes a deck look cluttered: more than 4 steps on a slide, one step per bullet, more than about 75 body words or 6 bullets, more than two kinds of visual component on one slide, and builds on more than 40 percent of the content slides. Resolve these warnings; they are the difference between a calm and a busy deck.

## 11. Verify

```bash
uv run --with playwright --with pillow d3deck/shoot.py dist/my_talk.html --contact --slot 15    # every slide, every step -> shots/
uv run --with playwright --with pillow d3deck/shoot.py dist/my_talk.html --from 3 --to 8         # a range
uv run --with playwright --with pillow d3deck/shoot.py dist/my_talk.html --from 5 --to 5 --live --wait 1500   # a replay mid-way
uv run --with playwright --with pillow d3deck/shoot.py dist/my_talk.html --pdf dist/my_talk.pdf  # print view as PDF
uv run d3deck/shoot.py dist/my_talk.html --chrome                                              # headless Chrome, no packages, no audit
```
First time on a machine: `uv run --with playwright playwright install chromium` (installs the browser Playwright drives).

The script waits 480 ms per step so the 420 ms transition has settled, then finishes every animation on the slide, so each shot is the end state (`--live` shoots what is on screen instead, `--wait MS` waits longer; together they time-lapse a replay). It prints, in order:

- `OVERFLOW`: every visible element outside the slide box or cropped by its body box (exit 1).
- `MATH`: formulas MathJax cannot render (exit 1).
- `LINT`: emoji or dingbats used as icons (error, exit 1); holes, where content ends more than 30 percent of the region above its bottom without being centred (fill the region or use `middle()`); wordy slides over 100 visible words; lowercase Greek inside an uppercase label, which prints α as Α (wrap it in `nocaps()`).
- `CONSOLE`: script errors and failed requests (exit 1).
- `budget m:ss of MM:00 slot` with `--slot`, or whenever slides carry `time=`; it warns when the budget exceeds the slot or when some presented slides have a time and others not.
- `signature`: how many content slides build, move, carry a designed object and hold interactive elements, and `text only:` the slides without an object. Every slide named there gets an object (html-components.md, section 2).
- `shots/report.json` holds all of it.

Contact sheets need Pillow (the --with pillow above); without it, read the per-step shots in shots/ directly. Then continue at the review depth chosen in Step 0 of `SKILL.md`: light stops here, standard adds one reviewer pass over `slides.py` and `shots/contact_*.png`, full runs the two-agent loop.

## 12. Presenting

| Key | Action |
|---|---|
| Right, PageDown, Space | next step, then next slide |
| Left, PageUp | previous step |
| Down, Up | next or previous slide |
| Home, End | first or last slide |
| number, Enter | jump to that slide (the numbers of the `#12.3` deep links) |
| F | fullscreen present mode; Esc leaves |
| N, S | presenter window (notes, next step, timer, pace); T resets, P pauses the timer there |
| O | overview of every slide at its final step; click or arrows and Enter to jump |
| B, W | black or white screen for a discussion; the same key or Esc returns |
| L | laser pointer |
| / | search palette over titles, summaries and speaker notes; Enter jumps |
| H | backup hub |
| P | print (one slide per page, final state) |
| ? | all keys |

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
- Anything the presenter should click is a `<button>` (all kit helpers make one); the presenter window relays only buttons and inputs.
- Motion written with `css()` keeps the end state as the base style and animates from the start under `.sl.is-current`; otherwise the PDF and the previews show a half-built slide.
- Kit labels are uppercase: a Greek letter or `s_i` in them turns into a capital. Wrap symbols in `nocaps()` or write them as `$...$`.
- `model()` draws in its region's px; a figure in a column needs `box='col'` (`'short'` in `twocoltakeaway`).

## 14. Checklist before delivery

- [ ] Titles read as the argument on their own
- [ ] Every content slide centres on a designed object; the signature line lists no text-only slide
- [ ] Every number traceable to the fact sheet in `storyline.md`; illustrative numbers labelled
- [ ] Time budget within the slot (`--slot`)
- [ ] One orange element per slide at most
- [ ] Every step reveals something; nothing moves between steps
- [ ] `shoot.py` audit clean, LINT and CONSOLE without errors, holes fixed; contact sheets inspected
- [ ] Wording rules applied (`d3-scientific-wording`); `check_wording.py slides.py` reports 0 errors
- [ ] Review done at the chosen depth (light: audit clean; standard: one pass applied; full: 9 or better in every category)
