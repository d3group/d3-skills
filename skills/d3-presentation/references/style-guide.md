# Presentation Guide

## 1. Visual Styles

### Viewport Rules
- **Header**: Title area at top (assume 2-line titles for consistent spacing)
- **Footer**: Page number and chair/presenter info - reserved for footnotes only
- **Viewport**: All content must fit between header and footer, never overlap
- Content is **top-aligned** within the viewport (handled automatically by template)

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
1. Understand the audience and purpose
2. Create outline with action titles first
3. Ask clarifying questions before generating

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

Prose must read as written by the presenter.

- No "not X, but Y" and no "it's not about X, it's about Y" constructions. State Y.
- No em-dashes. Use a comma, a colon, or a new sentence.
- Related work: say what it contributed and state the gap as a fact. No "merely", "simply", "fail to", "only", "overlook".
- No marker vocabulary: leverage, robust framework, comprehensive, transformative, synergies, delve, seamless.
- Titles vary in length, from two words to a full sentence. No forced groups of three.
- First person plural for own work: we analysed, we observe, our approach.
- Concrete numbers instead of "large-scale"; one condition clause instead of an adjective stack.

## 5. Step builds (HTML)

- One step is one idea. Step k+1 answers a question step k raised.
- No bullet-by-bullet reveals. Reveal a cluster, a column, or a region.
- Use a scrim to reveal a grid cell by cell; the whole grid is laid out from the start.
- Nothing moves between steps: elements are ghosted, never removed.
- At most one orange element per slide; the step that reveals it is the point of the slide.
- A beat with no new content is allowed once per section, as the transition into the own contribution.
