# Content design: what goes into an explainer for the authors themselves

## Contents
1. What the reader wants
2. The build-up principle
3. Section spine
4. Depth budgets
5. The research gap
6. Derivations
7. How the code realizes it
8. Evidence
9. The honest inventory
10. What to leave out
11. Wording

## 1. What the reader wants

The author and the co-authors already own the project. They open the explainer because one of these is true:

- They lost the overview: many decisions were made over months, some with co-authors or with an assistant, and the whole no longer sits in one head.
- A derivation is in the paper, and they could not reproduce it at a whiteboard.
- They know the math and not the code, or the reverse, and cannot say which function computes which equation.
- A co-author joins and needs the project's logic, not its sales pitch.
- They want to see the mechanism move: what happens to the result when an assumption or parameter changes.

So the explainer answers "how does this actually work, and why is it built this way?" It does not argue that the project is important. After reading, the author should be able to do concrete things; name them in the brief ("re-derive Eq. (7) and say which assumption each step uses", "say which term in the loss enforces the constraint and where it is computed").

## 2. The build-up principle

Each section adds one idea on top of the previous ones, and each idea is introduced in this order:

1. **A plain sentence.** "Every candidate you skip makes your benchmark better and the chance that the best one is already gone larger."
2. **Something to move.** The interactive figure that makes the sentence visible.
3. **The formal statement**, pulled from the paper.
4. **The derivation**, step by step, each step with its reason.
5. **Where it lives in the code.**

The sentence comes first because the reader should know what the algebra is about to say before reading it. A section that starts with notation has the order backwards.

## 2a. Three devices that make the build-up visible

- **The hero states the destination.** The central equation of the project (or, if there is none, the claim) sits in the hero, colour-coded. The reader sees at the start what the page will assemble, and the lede says in plain words what it will be able to do.
- **One colour code, kept everywhere.** Decide two to five roles before writing (what we choose, what we earn, what nature does; or one colour per competing method) and use them in the hero, in every formula (`\\role{...}`), in every figure, and in prose where it helps (`<span class="r-role">`). A reader who has learned that orange is the decision reads every later figure faster.
- **The assembling panel.** When the project culminates in one equation or one chain of statements, list its pieces as `[hud]` lines and mark each section with the level it reaches. Skip the panel when the project has no such spine; do not invent one.

Dated decisions belong in the text where they explain why the model looks as it does ("since 31 Aug the types form a continuum; this replaces the three archetypes"), in a `.note.basics` titled with the date. Authors reread explainers, and the history of a decision is part of understanding it.

Voice: a colleague explaining at a whiteboard. First person plural for the project's work; addressing the reader as "you" is fine where it puts them into the setting ("you must commit before demand is known").

## 3. Section spine

Adapt it; do not fill it mechanically. Merge or drop sections that have nothing to say for this project.

| # | Section | Content | Typical components |
|---|---|---|---|
| 01 | The project in one screen | The question, the claim in one sentence, status or headline numbers, how the explainer is organized | `.claim`, `.kpis`, short list |
| 02 | Setting and problem | Actors, decisions, information, objective; only the notation needed later | flow or schematic, short table |
| 03 | The research gap | What exists, where it stops, what this project adds | `table.gap`, one paragraph per strand |
| 04 to N | Core ideas, one per section | The build-up order of section 2 | widget, `.eq`, `.derivation`, chips |
| N+1 | How the code realizes it | Pipeline, paper-to-code map, one or two excerpts | `D3X.flow`, table, `pre.code` |
| N+2 | Evidence | What each experiment shows and does not show; real numbers | widget on embedded results, `figure.static` |
| N+3 | Honest inventory | Assumptions that carry the result, paper versus code, open questions, next steps | `.note.warn`, `.note.open` |
| N+4 | Notation and sources | Symbol, meaning, code name | `table.notation` with `id="notation"` |

For tier B (no code) drop N+1 or turn it into "what an implementation needs". For tier C (no paper) the core-idea sections cite code and notes, and formal statements are marked `[[reading]]` until the author confirms them.

Section titles state the message ("Skipping candidates buys a benchmark, and the price is that the best may be among them"), in varied lengths. The navigation label (`data-nav`) is short.

## 4. Depth budgets

The build reports main-line words and interactive figures against these budgets. Words inside `<details>` are counted separately as "folded". `D3X.flow` diagrams are structure, not knobs, and do not count as interactive figures.

| Depth | Sections | Main-line words | Interactive figures | Derivations | Reading time |
|---|---|---|---|---|---|
| focus | 1 to 3 | up to 1,200 | 1 to 2 | 1 | about 5 min |
| overview | 4 to 6 | up to 2,500 | 2 to 4 | 0 to 1 | 10 to 15 min |
| standard | 7 to 10 | up to 6,000 | 4 to 8 | 1 to 3 | 20 to 35 min |
| deep | 10 to 14 | up to 12,000 | up to 14 | as needed | 40 to 60 min |

`focus` is for "explain just this derivation" or "only the loss function": the build-up order of section 2 applied to one idea, a closing block on what it assumes and leaves open, and a notation table. No gap section, no pipeline, no evidence section unless the user asks. It is the right answer to a small question; do not inflate it to an overview.

"Deep on X" is a standard explainer in which X gets the room it needs and everything else stays brief. When X is a chain of derivations (a lemma, then the main result, then its corollaries), give each link its own short section with its own derivation block: "one idea per section" still holds, and the limit of one to three derivations applies to the parts that are *not* X. Set `depth = "deep"` only if the main line then exceeds the standard budget. When the user asks for every detail of something, give every detail of that thing and keep the rest at standard. The build counts the reasons of derivation steps (`data-why`) as main-line words.

When over budget, in this order: fold proofs of routine steps into `<details>`; merge sections that share a figure; cut background; cut the figure whose Notice line is weakest. Do not raise the depth to make the warning go away.

## 5. The research gap

The gap section is a map, not a literature review.

- Group prior work into two to five **strands**, each described by what it established and the assumption or scope where it stops. One short paragraph per strand, with the two or three citations the paper itself uses.
- State what this project adds as a fact about the combination: "No strand treats X and Y together; the model here does, at the cost of Z."
- Show it as a `table.gap`: strands in rows, capabilities or assumptions in columns, this project in the last row (`class="ours"`). Cells: `class="y"` with ✓, `class="p"` for partial with a word, `class="n"` with a dash.
- Sources: the paper's introduction and related work, a gap-audit note in the vault, NotebookLM answers. If the positioning is your inference, put it in a `.note.reading` and ask the author in the brief.
- When the repository contains no positioning at all (no related work, no notes), do not invent a literature. State the gap the sources do support, which is the distance between what the paper's title and abstract promise and what paper and code deliver, and hand the literature question to the authors as an open point.
- Tone: neutral. Describe scope, not shortcomings. No "fails to", "overlooks", "merely", "only".
- If the author's notes record how the gap statement changed over time, one sentence on that history helps co-authors understand why the framing is what it is.

## 6. Derivations

Use `.derivation` for the one to three derivations that carry the project. A derivation earns its place when the result is used later and the author could not write it down from memory.

- Pull the start and the end from the paper (`<div class="eq" data-label="...">`), so the explainer and the paper cannot disagree.
- Three to eight steps. Every step has a `data-why` that names the rule or assumption used ("the sum is a Riemann sum of 1/t, so it converges to the integral", "Assumption 1: candidates arrive in uniformly random order, so the best of the first k − 1 is equally likely at every position"). A step without a reason is a line of algebra, not an explanation.
- Group routine algebra into one step. Put long but routine parts into `<details class="deep">` inside the step.
- After the derivation, one `.note.key` with what to keep: the structural insight, not the formula again.
- Where an assumption enters, say what breaks without it. That is often where a figure helps ("let quality trend upward over time and skipping 37 % stops being optimal").
- If the paper's derivation has a gap or you cannot follow a step, say so in a `.note.warn`. Never paper over it with confident prose. This is a finding the author wants.
- If your derivation deviates from the paper's route (because it is more intuitive), say so and point to the paper's version.
- If the paper states a result without the steps in between ("differentiating yields"), the steps are your reconstruction: pull the start and the end from the paper, mark the block `[[reading]]`, and say in the brief that nobody but you has checked them unless a fidelity review runs.

## 7. How the code realizes it

- One `D3X.flow` of the pipeline from input to result file, five to nine boxes, each with a `detail` sentence and a `[[code:...]]` chip. Box kinds: `data`, `code`, `model`, `result`, `external`.
- The paper-to-code map table (see `scanning.md`, section 6).
- One or two `pre.code` excerpts of at most about 25 lines, for the lines that *are* the idea (the loss, the update, the constraint), not for plumbing. Say in one sentence before the excerpt what to look at.
- Name the code names of the paper's symbols in the notation table.

## 8. Evidence

- For each headline result: what was compared, on what, the number, and the file it comes from (`[[result:...]]`).
- Embed a small result table (`<script type="application/json" data-src=...>`) and plot it with a widget, so hover gives exact values. Reuse the paper's own figures with `figure.static` when re-plotting adds nothing.
- Say what the experiments do not show (no out-of-sample test, one data set, baselines without tuning). The author knows; the co-author needs to.
- Keep toys and evidence apart. A toy figure illustrates a mechanism; an evidence figure shows the repository's numbers. The `toy: true` badge makes the difference visible.

## 9. The honest inventory

This section is the reason an explainer for authors differs from one for outsiders. Look for:

- **Paper versus result files.** Recompute every headline number you quote from the committed result files instead of copying the paper's table. A headline number that differs between the paper's table and the committed result file is exactly what the authors need to hear before submission. `.note.warn`, with the `[[result:…]]` and `[[paper:…]]` chips.
- **Paper versus code.** Different hyperparameters or loss weights, an exact finite-sample computation where the paper states a limit, a rounding or tie-breaking rule the paper does not mention, features the paper lists that the code never loads, defaults in configs that differ from the reported setup. `.note.warn`, with both chips.
- **Assumptions that carry the result.** Which ones the main result needs, where each enters, and whether the experiments respect them.
- **Open questions and next steps.** From vault notes, TODO comments, review notes, the paper's limitations. `.note.open`.
- **Things you could not verify.** A number whose source file you did not find, a derivation step you could not reproduce. Say it plainly.

If the inventory is empty, state what was compared ("objective terms and weights, sample sizes, data splits, the reported hyperparameters against `configs/`") so the author can judge the coverage.

## 10. What to leave out

- Textbook background the author demonstrably knows. If the vault shows a concept was hard (a note titled "why does the cross term vanish"), that concept is not background; it is content.
- A literature survey. The gap section has strands, not a bibliography.
- Code plumbing: data loading, logging, experiment orchestration, plotting.
- Paragraph-by-paragraph restatement of the paper.
- Figures without a knob-to-insight sentence.
- Praise for the project.

## 11. Wording

Text should read as written by a researcher of the group explaining the project to a colleague.

- First person plural for the project's own work: "we model membership as a flow".
- No em-dashes or en-dashes as punctuation: comma, colon, parentheses, or a new sentence. Ranges keep their dash (`2024–2026`).
- No "not X, but Y" and no "it is not about X, it is about Y". State Y.
- No marker vocabulary: leverage, delve, seamless, comprehensive, robust framework, transformative, holistic, synergies, cutting-edge.
- Related work as facts: what it established, where it stops. No grading ("seminal", "fails to", "merely").
- Concrete numbers and conditions instead of adjectives: "the success rate rises from 0.31 to 0.38 between 15 % and 37 % skipped", not "the success rate increases substantially".
- Short paragraphs, two to five sentences. Definitions inline where first used; the notation table is for looking up, not for learning.
- Captions of interactive figures: a bold title, then `Try` (an action) and `Notice` (the insight, stated as a fact that the figure makes checkable).
- Questions to the reader (`<details class="predict">`) before a figure, where guessing first makes the figure land: "Before you drag: does skipping half of the candidates beat skipping a quarter?"
- A literal dollar sign is written `<span class="usd">$</span>`, because `$` starts inline math.
