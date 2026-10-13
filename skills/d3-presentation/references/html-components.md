# HTML Components: designed objects

Load this before designing the slides of an HTML deck, and again when reviewing the contact sheet. The frame (klar or beamer look, Inter, D3 tokens) is the same in every D3 deck; what makes a deck worth watching is what happens inside the body region: objects that are built rather than typed, motion that reports something, and details that answer a question when the presenter points at them. The kit and this guide were distilled from M. Möhle's D3 talk decks and ported to the `slides.py` API. Every helper returns an HTML string and is imported with `from d3deck import *`; `assets/html/example-slides.py` (section 5) uses each one.

## 1. The bar

**Every content slide**
- centres on a **designed object** that carries the claim; a slide whose main object is a bullet list is a draft, and the build warns "text only";
- carries **keywords on the slide, sentences in the notes** (about 40 words of visible prose on a typical slide);
- **fills its region or centres its object** with `middle()`; a block glued to the top above an empty half is a hole, and `shoot.py` reports it;
- moves only where the motion **reports something** (a relation drawn while it is said, a bar growing out of the previous one, a counted total), within the feel agreed at intake (`meta(feel=...)`).

**Every deck** (for `rich` and `interactive`; worth it for `calm` too)
- a **hook the room experiences** in the first two minutes: a replayed stimulus, a concrete case with a real number, a gap on a gauge; never an agenda slide;
- at least one **figure that builds**, one relation per step;
- at least one **moving number or shape**;
- an **interface or artefact rebuilt in HTML** whenever the talk involves one (a screenshot only when a rebuild is impossible);
- for `interactive`: **something that responds** to the presenter (hover-lit relations, click-for-detail badges, citations, preset chips on an instrument);
- `statement()` or a `callout()` band where the argument turns, on about one slide in three at most.

## 2. The draft says ... build instead

Ask "what is the object here?" before writing any text.

| The draft says | Build instead |
|---|---|
| "X looks right but is wrong" | the answer replayed in a `chat()` replica with the wrong detail `flag()`ged, and a `gauge()` with the wrong and the right value and the gap as a zone |
| "prior work assumes A leads to B" | a small `model()` of the assumed relation, then a `callout()` with what breaks |
| "three reasons" | three `tile()`s with icons in a `grid3`, the decisive one on its own step |
| "the model" | `model()` in lanes, one relation per step, tags on the edges, `k=` keys so hovering a hypothesis lights its path |
| "A moderates the effect of B on C" | `edge('a', ('b', 'c'), 'mod')`: the dashed arrow points at the middle of the relation |
| "construct A versus construct B" | `versus()` with a centre column of row labels, one column per step |
| "the sample / the design" | `facts()` for the headline numbers, a conditions grid of `tile()`s |
| "results" | a `k-table` with `effect()` bars and `badge()`s that open the hypothesis; the disappointing row on its own step, hatched (`'weak'`) |
| "the derivation / the identity" | `proof()` rows, the key step teal, a tempting wrong step red, then `brace()`d terms naming each part |
| "what X does to Y" | `bars()` on one scale, each new bar growing out of the previous one (`grow_from=`) |
| "N studies, participants, candidates" | `units()` one square per unit, or a grid of `bub()` circles that open their names on click |
| "our position among the options" | `selector()`: every option visible, the chosen one lit |
| "timeline / next steps" | `milestones()` to scale with a today dot, plus a `countdown()` chip |
| "a parameter matters" | a `lab()` instrument: the figure, a `slider()` with presets, a `readout()` |
| "the one sentence to remember" | `statement()` slide, or the `callout()` band under the object |

## 3. Catalogue

Common arguments: `s=` is the step (0-based, like `data-s`), `k=` a Q&A key (section 3.9), `color=` one of `navy` (default), `teal`, `orange`, `red`, `gray`.

### 3.1 Blocks

```python
tile('One model, one baseline', ['overrides logged with a reason', ('source, briefly', 'muted')],
     kick='After', ico='database', color='teal', s=1)      # kicker with icon, headline, keyword lines
icon('check')          # inline stroke icon; icon('alert', size=28). Names: kit.ICONS (arrows, chart, users, target, ...; for course roadmaps: linear, roulette, curve)
well('users', 'teal')  # round icon well
middle(html)           # centres a short object vertically in its region
callout('Adoption held where planners could <b>override with a reason</b>.')   # navy band, <b> in orange; quiet=True: pale
chip('supported', sign='ok'), chip('the paradox', solid=True)
sign_badge('pos')      # pos +, neg -, ind ?, ok (check), no (x), nil: signs carry icons, never ✓ or ✕
badge('H1', pop='H1: the full hypothesis')   # square identifier; with pop= a button with a popover
stamp('removed', 'red', s=2, style='left:360px;top:190px')   # lands with a bounce on its step
```

Put tiles side by side with `<div class="grid3">...</div>` (also `grid2`, `grid4`). Keep the same component for the same kind of content across the deck.

### 3.2 Numbers

```python
count(72, frm=82)                 # an integer that counts 82 -> 72 on stage; previews and print show 72
bars(bar('+20 % lift', 7456),
     bar('+10 % lift', 29826, grow_from=7456),
     bar('+5 % lift', 119303, 'orange', sub='our case', s=1),
     unit=' per arm', scale=None, label_w=180, value_w=200)   # ONE scale; grow_from: grows out of that value
effect(.41), effect(-.28, 'neg'), effect(.09, 'weak')          # effect-size bar for a table cell; width = |r|
gauge(30, 90, [(54, '54 · forecast', 'navy'), (80, '80 · demand', 'orange')], zone=(54, 80, 'orange'))
units([(38, 'teal', 'kept the model'), (9, 'gray', 'returned'), (3, 'orange', 'deciding')], size=24)
bub(12, 'red', pop='the 12 names ...')                          # a circle sized by a count
```

Tables: `<table class="k-table">` with `<tr data-s="1">` for a row that builds in; its rules fade with it. Existing numbers helpers stay: `facts()`, `stat()`, `bignum()`.

### 3.3 Model figures

```python
model([node('form', 'Explanation form', col=0, y=150, w=220, h=72, sub='what the designer controls'),
       node('verify', 'Lower cost of verifying', col=1, y=62, color='teal', sub=cite('Author 2024', '...')),
       node('rely', 'Appropriate reliance', col=2, y=150),
       node('m', 'Task familiarity', col=1, y=300, color='gray')],
      [edge('form', 'verify', 'pos', s=1, k='H1'),
       edge('verify', 'rely', 'pos', tag='H1', s=1, k='H1'),
       edge('m', ('verify', 'rely'), 'mod')],
      lanes=[('Design', 'explanation'), ('Mechanism', 'finding'), ('Behaviour', 'reliance')])
```

- The figure has exactly the size of its region (`box='body'`, `'col'`, `'short'` or `(w, h)`); positions are px inside it. `col=` centres a node in a lane; lane labels take the top 46 px, so start nodes at `y >= 50`.
- The geometry is computed: an edge leaves and enters on the sides facing each other, several edges on one side spread out in the order of their far ends, the curve leaves each border at a right angle, and the arrowhead's tip touches the target border. Never hand-draw arrows beside a `model()`.
- Signs: `pos` teal, `neg` orange, `ind` navy, `mod` dashed grey, `plain` grey-blue (unsigned flows). A legend of the signs used is added bottom left (`legend_=False` to drop it).
- An edge with `s=` draws in on its step; nodes take `s=` too. Build one relation per step and say the mechanism while it draws.
- A redrawn published model keeps every node and edge of the source; tight geometry is a reason to reroute (`bend=`), never to drop an arrow.

### 3.4 Derivations

```python
proof(line(r'$n = 2\,(z_{1-\alpha/2} + z_{1-\beta})^2\;\sigma^2/\delta^2$', 'per arm, two-sided'),
      line(r'$\delta \to \delta/2 \Rightarrow n \to 2n$', 'tempting, wrong', 'wrong', s=1),
      line(r'$n \approx 16\;\sigma^2/\delta^2$', 'the rule of 16', 'key', s=2))
'<div style="display:flex;gap:40px">' + brace(r'$\sigma^2$', 'noise', 'teal') + brace(r'$1/\delta^2$', 'lift', 'orange') + '</div>'
```

Formulas are MathJax as everywhere in the deck. Braces draw left to right when they arrive.

### 3.5 Comparisons

```python
versus('Point forecast', 'Interval forecast', [('54 salads', 'Output', '40 to 80 salads'), ...],
       left_ico='target', right_ico='sliders', left_color='gray', right_color='teal', rstep=1)
selector(['I · Analysis', 'II · Explanation', 'III · Prediction', 'IV · Both', 'V · Design'], 3)
```

### 3.6 Stimuli and interfaces

```python
chat('How many salads should we stock for Saturday?',
     '<p>Stock <b>' + flag('54 salads') + '</b>.</p>', title='Study stimulus · control', user_color=None)
```

With `replay=True` (default) the question pops, typing dots run and the answer streams in on arrival (about 3 s, only at step 0; coming back mid-build shows the finished window). Rebuild an interface from the study's own text and colours (`user_color=` for the stimulus' bubble colour); stimulus colours are allowed inside a mock. Code: `codebox()`, `errorbox()`, `terminalbox()`.

### 3.7 Time

```python
milestones('2026-09-01', '2027-03-31', [('2026-09-24', 'This talk', 'feedback', 'done'),
           ('2026-11-30', 'Field study', 'three stores', 'key')], today='2026-09-24')
countdown('2026-11-30', 'to the field study')
```

Positions are to scale; the today dot and the countdown move to the real date when the deck opens. Keep milestone labels about a tenth of the width apart. `timeline()` (Gantt, twin of the LaTeX macro) and `chevrons()` remain for work packages and phases.

### 3.8 Instruments

```python
onecol(K('Instrument', 'The interval narrows with the square root of the sample'),
       lab('<svg id="curve" viewBox="0 0 700 300">...</svg>',
           slider('n', 'Visitors per arm', 500, 20000, 2000, step=500, presets=(500, 2000, 8000)) +
           readout(('Half-width', 'hw', ''), ('Detectable lift', 'mde', ''))))
js('''D3Deck.live('#curve', {
  setup(el) { this.draw(el); document.getElementById('n').addEventListener('input', () => this.draw(el)); },
  draw(el)  { /* read n, repaint the svg, D3Deck.set('hw', '±1.35 pp') */ }
});''')
```

`D3Deck.live(el, {setup, enter, leave, step, frame})`: `setup(el)` once at boot (paint a still: print and previews show it), `enter`/`leave` when its slide comes on or goes off screen (stop timers, reset to the still), `step(el, n)` on every step change (0-based, also right after enter), `frame(el, dt)` every animation frame while on screen. Helpers: `D3Deck.rng(seed)` (deterministic: the run on stage is the run you rehearsed), `D3Deck.canvas(cv, w, h)` (a crisp canvas), `D3Deck.set(id, text)` (a readout that flashes once when it changes), `D3Deck.calm` (reduced motion: jump to end states). A guided walk on a build step makes an instrument usable without touching it.

### 3.9 Q&A interactions

| Interaction | How | Use |
|---|---|---|
| Hover-lit relations | the same `k=` on edges, tags, nodes, badges | "Which arrow is H2?": point, it lights, the rest dims |
| Click for detail | `badge('H1', pop=...)`, `pop('label', 'detail html')`, `bub(n, pop=...)` | the full hypothesis, the names behind a count, a definition |
| Citations | `cite('Author 2024', 'Author, A. (2024). Title. Venue.', 'p. 7')` | "Where is that from?" |
| Preset chips | `slider(..., presets=(40, 160))` | rehearsed values, one click each |

Clickable things are `<button>`s (every helper above makes one): the presenter window relays button clicks and slider input to the projected slide, so the presenter drives the demo from the laptop. The resting state must be complete: print and previews never show `.lit` or a popover.

## 4. Motion

The kit's own motion needs nothing from the author. For slide-specific motion through `css()`:

1. **Animate only the slide on screen:** selectors start with `.sl.is-current`. The presenter's next pane, the overview and print never carry `.is-current`.
2. **The base style is the end state.** Animate *from* the start state with a `both` fill: `@keyframes x { from { opacity: 0 } }`. Every preview and the PDF then show the finished picture.
3. **Step state through `.is-shown`:** the engine adds it to every `data-s` element whose step is reached, so `.sl.is-current .fig:has(.m3.is-shown) .node-a { ... }` restyles on step 3.
4. **Replays only on arrival:** gate with `.sl.is-current[data-step="0"]`, so returning mid-build shows the end state.
5. Print and reduced motion switch every animation off; `shoot.py` finishes animations before each shot (`--live --wait 3000` to time-lapse a replay).

Vocabulary (keyframes in the kit): `k-pop`, `k-appear`, `k-grow-x`, `k-draw`, `k-count`, `k-ring`, `k-stream`, `k-stamp`, and micro-motion for mocks `k-press`, `k-nudge`, `k-slide-l`, `k-slide-r`, `k-fade-back`. Timing: entrances .3 to .55 s with `var(--ease)`, movements .6 to .8 s, stagger 80 to 120 ms, a mock's whole sequence under 3 s (setup, action, consequence), nothing loops unless the loop is the message.

## 5. Colour with intent

- **Tints as grounds, saturated colour as ink.** Nodes and tiles sit on `--navy-10`, `--teal-10`, `--orange-10`, `--red-10`; the saturated colour appears in the top rule, the icon, the key word, the edge.
- **One colour story per deck, kept.** Decide on the first model slide what teal and red mean (two constructs, two conditions, works and fails) and never reuse them for anything else. Signed edges: teal positive, orange negative, navy indeterminate, grey dashed moderation.
- **Orange is the single accent:** the point of the slide, the key milestone, the negative sign. Orange text on white uses `--orange-ink`.
- **Grey is information:** secondary labels; hatched grey or `'weak'` means underpowered or uncertain.

## 6. What looks generic (avoid)

- An agenda slide as slide 2; the klar dividers list their part's slides.
- Topic titles ("Results") where a finding fits; bullet lists as the main object; five equal tiles without hierarchy.
- Emoji, and dingbats standing in for icons (✓ ✕ ⚠ ★ ➜); `shoot.py` fails on them.
- Screenshots of interfaces, tables or charts that could be rebuilt.
- Motion without meaning: everything fading up, bouncing icons, loops that never stop.
- A deck where nothing responds when the presenter points at it (for `interactive`).
- Backup slides that fall back to a paragraph: give each its object, titled as the answer.
- A PDF page or overview thumbnail that shows a half-built figure: keep the base style the end state.
