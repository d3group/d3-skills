# Presentation Guide

## 1. Visual Styles

### Viewport Rules
- **Header**: Title area at top (assume 2-line titles for consistent spacing)
- **Footer**: Page number and chair/presenter info - reserved for footnotes only
- **Viewport**: All content must fit between header and footer, never overlap
- Content is **top-aligned** within the viewport (handled automatically by template). In HTML, a short object is centred in its region with `middle()` rather than leaving the lower half empty

### Alignment
- Text boxes and figures must be properly aligned
- Watch for vertical alignment issues (e.g., boxes with "g" vs without)
- Make box heights consistent based on largest character
- Apply the **squint test**: key messages visible from distance

### Font Sizes (from template)
- Title: 14pt
- Subtitle: 7pt
- Body text: 8pt
- Column header: 10pt bold
- Use only these sizes - if text doesn't fit, shorten it

### TikZ and Graphics
- Graphics often become too large - verify they fit viewport
- Remove chart junk (unnecessary lines, decorations)
- Use color only to highlight

---

## 2. Content Styles

### Storylining (Pyramid Principle)
1. Start with the answer/recommendation, then support it
2. Group arguments into logical clusters (max 3-4 per level)
3. Each level answers "why?" or "how?" of the level above
4. Executive summary captures the entire story

### Top-Down Communication
- **Main message in title** → slide shows supporting details
- **Presentation flow**: Overview first, details later
- One message per slide
- Reserve details for the appendix

### Action Titles
- Complete thought summarizing the slide's key message
- Reader understands narrative by reading titles alone
- One line preferred, two lines acceptable
- No information in title that isn't on the slide

### List Consistency
Lists must be grammatically parallel.

**Good:** Created code / Reviewed code / Shipped code
**Good:** Code creation / Code review / Code shipping
**Bad:** Created code / Code review / Have shipped code

### Slide Purpose
Every slide must serve a specific function:
- **Data**: charts for trends, tables for comparisons
- **Concepts**: brief text (not paragraphs)
- **Processes**: graphics, timelines, flowcharts

Remove slides that don't strengthen the narrative.

### Format Selection
| Content Type | Best Format |
|--------------|-------------|
| Trends over time | Line chart |
| Part-to-whole | Pie/stacked bar |
| Comparison | Bar chart / Table |
| Process flow | Diagram / Timeline |
| Relationships | Matrix / Flowchart |

### Slide Type Selection

| Use Case | Slide Type |
|----------|------------|
| Opening/closing | Title slide / Thank you slide |
| Structure overview | Agenda slide |
| Section transitions | Section divider (highlights current section) |
| General content | One-column slide (`\onecol` / `onecol()`) |
| Comparing two things | Two-column slide (`\twocol` / `twocol()`) |
| Highlighting a key insight | Two-column with takeaway (`\twocoltakeaway` / `twocoltakeaway()`) |
| Sequential process (2-5 steps) | Chevron/Process slide |
| Project phases over time | Timeline slide |
| Code examples | Use `codebox`, `errorbox`, or `terminalbox` (same names in HTML) |

**Chevron slides**: Use `\twochevron`, `\threechevron`, or `\fourchevron` depending on the number of phases. First argument (N) highlights that phase. Each phase has a label and title (e.g., `{Phase 1:}{Planning}`). The legacy `\fourcolchevron{N}{...}` uses single labels. Highlighted phases use `d3-navy`, others use `d3-navy!15`.

**Agenda slides**: Use `\showagenda` once, then `\showsection{n}` throughout presentation to highlight the current section. All items are clickable.

---

## 3. Execution

### File Organization
Create a new folder for each presentation:
- Name: 1-3 words, lowercase, separated by `_` (e.g., `ai_healthcare`, `q4_results`)
- All presentation files live in that folder

### Planning
1. Settle the storyline with the user first (SKILL.md, Step 1): their narrative if they have one, otherwise a choice between two proposals. Save it as `storyline.md`
2. Understand the audience, the time slot, and the one takeaway
3. The approved action titles are the outline; slides are written to them

### Storyline skeletons by talk type
Budgets are speaking time. One content slide takes 45 to 60 seconds, a slide with a built figure up to 1:30; title, dividers and closing about 10 seconds each. Keep about 10 percent of the slot as slack. A skeleton gives the slots; the two proposals of Step 1 order them differently.

| Talk type | Skeleton |
|---|---|
| Conference paper (7 to 15 min) | hook (a concrete case or surprising number, felt rather than described) · gap (what prior work assumes and why it breaks here) · research question and contribution · model, one relation per step · method at a glance · what participants saw or the data · results with the honest row on its own step · implication · closing with the takeaway · backup (limitations, full model, robustness). For 7 minutes merge gap into the hook and method with the data |
| Progress report or group meeting (15 to 45 min) | parts with dividers: where we were · what changed (each change with its reason) · the hardest new idea, derived step by step · where it goes (venue, timeline) · the ask: concrete questions for the room, never "thoughts?" |
| Defense or proposal (20 to 30 min) | motivation · research questions · compact background · per study: question, method, result, contribution · synthesis · limitations · contributions to theory and practice · closing; backup holds every method detail a committee may ask for |
| Lecture (45 to 90 min) | learning goals · activation (a question to the room) · concept blocks, each intuition, formal, example, check question · live demos · summary · exercises; more slides, fewer words each |
| Invited talk (30 to 45 min) | a puzzle · why it matters · two or three studies as chapters that resolve it · the bigger picture · what comes next; fewer numbers, more figures, a memorable last sentence |

### Checklist

**Title Slide**
- Add title (use `\title{}`)
- Add subtitle if relevant, otherwise remove
- Update date (add location if relevant)
- Set `\presenter{}` and `\chair{}`

**Content Slides**
- Each slide needs an action title
- Use appropriate layout (`\onecol`, `\twocol`, `\twocoltakeaway`)
- Use `\columnheader{}` for two-column subheadings
- Use code boxes for any code examples

### Visual precision
Checked at full size, on every build step, not only on the contact sheet:
- **Arrowheads**: the shaft enters the head from behind, on the arrow's axis; the tip touches the target's border, neither overlapping it nor stopping short (`model()` computes this; hand-drawn TikZ or SVG arrows need the same care).
- **Labels never sit on lines**: an edge label cuts the line with a white ground (a `tag=`), or keeps a consistent gap from it.
- **Same-kind boxes align**: nodes of one stage share a row, a height and the column grid; gutters are constant within a slide.
- **No overlap at any build step**: a node that is fine at the last step may collide with something at step 2.
- **Reproduced figures stay complete**: a redrawn published model, table or equation keeps every edge, label and term of the source (list them first). Dropping an arrow or a residual term states a different claim; if the slide compresses the source on purpose, say so on the slide or in the notes.

### Verification
1. View the compiled PDF
2. Check for overlaps:
   - Content into header/title area
   - Content into footer (page number area)
3. Check alignment of all elements
4. Apply the squint test
5. Iterate until no visual issues remain

---

## 4. Wording (both formats)

Prose must read as written by the presenter. The wording rules of all D3 documents live in the `d3-scientific-wording` skill: `<wording-dir>/references/rules.md` (`<wording-dir>` is `<skill-dir>/../d3-scientific-wording`), and in STE mode also `references/ste.md`. Its lint reads `slides.py` and `.tex` decks. In short:

- No "not X, but Y" and no "it's not about X, it's about Y" constructions. State Y.
- No em-dashes. Use a comma, a colon, or a new sentence.
- Related work: say what it contributed and state the gap as a fact. No "merely", "simply", "fail to", "overlook".
- Claims within the evidence: numbers instead of "dramatically" or "large-scale", "significant" only with a test.
- First person plural for own work: we analysed, we observe, our approach.

What is specific to slides:

- Titles vary in length, from two words to a full sentence. No forced groups of three.
- One condition clause instead of an adjective stack; labels on objects, full sentences in the notes.

### Voice and rigour
- **Present, do not defend.** The slide states what the research does and finds. No pre-emptive defences ("the theory makes no claim that ...", "the weakest joint is ..."); objections belong on backup slides titled as the answer.
- **No debt framing.** Not "what I owe" or "what I still have to show". Research does things; a venue expects things.
- **No coined terms.** Do not invent word combinations for things the literature already names. Every technical term carries its source (a citation on the slide) and its plain meaning where it first appears.
- **Every number is explained where it stands.** A total shows its sum (40 + 38 + 4 = 82), a percentage its base, a scale its range. A number the room cannot reconstruct raises a hand in the Q&A.
- **Illustrative is labelled illustrative**, on the slide (`provenance='Illustrative numbers'`), and never borrows a real study's number that happens to match.
- **Attribution is exact.** A number attributed to a paper is that paper's number in that paper's sense; check it at the source.
- **Title style follows the deck.** Action titles are the default; if the presenter's existing deck uses short labels, keep that convention throughout instead of mixing.
- **One spelling variant per deck** (American or British), notes included; quotes and stimulus replicas keep their original spelling.
- **Honest rows get their own step**: null results and limitations are said, not skimmed.

## 5. Step builds and designed objects (HTML)

**An object on every slide, motion where it reports.** Every content slide centres on a designed object that carries its claim (html-components.md has the bar, the objects and the "draft says ... build instead" table); the words are labels on it and the sentences go into the notes. Motion is part of the argument, never decoration: a relation drawn while it is said, a bar growing out of the previous one, a total that counts, a stimulus replayed as participants saw it.

**The feel sets the budget** (`meta(feel=...)`, agreed in Step 1):
- `calm` (default): at most about one slide in three builds; the kit's arrival motion stays, since it only finishes what is already laid out.
- `rich`: builds wherever a step adds one idea; replays, counted numbers, figures that build.
- `interactive`: rich plus Q&A interactions or a live instrument the presenter drives.

Rules for every feel:
- One step is one idea. Step k+1 answers a question step k raised; say it while it appears, and write what each step does in the notes (`0: ... 1: ...`).
- No bullet-by-bullet reveals. Reveal a cluster, a column, a region, a relation.
- Two to four steps per slide; a model built one relation per step may take up to six. The build warns above four.
- Nothing moves between steps: later elements wait as pale ghosts in their final place (`meta(reveal='ghost')`, the default), never removed. Use `reveal='hide'` only when a ghost would give away the point.
- One visual idea per slide: do not combine a figure with stat cards with a process flow. Tiles, a callout and a legend support an object; they do not compete with it.
- About 40 visible words on a typical slide, 60 at most outside a dense backup slide; 3 to 5 lines per tile.
- HTML titles are a kicker plus a claim, `K('Method', 'A cutoff rule needs one number')`. The kicker names the category; the claim is a sentence of at most 15 words. "Results", "Method" or "Agenda" alone are not titles.
- Orange covers only a few percent of the surface: blue is what is known, orange is what is new. At most one orange element per slide; the step that reveals it is the point of the slide.
- Use `statement()` at the turns of the argument, `facts()` for the numbers the audience should take home, and the `callout()` band for the one sentence that must land, on about one slide in three at most.
- Use a scrim to reveal a grid cell by cell; the whole grid is laid out from the start.
- A beat with no new content is allowed once per section, as the transition into the own contribution.
- Anything interactive is a bonus: the slide reads completely without a hover or a click, in the PDF and the overview too.
