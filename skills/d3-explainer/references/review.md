# Two-agent review, on a token budget

Run it after `build.py` (no `--draft`) and `check.py --shots` are clean. The machines have already verified that pointers exist and that nothing crashes; the reviewers spend their tokens only on what needs judgment:

- **Fidelity reviewer:** is what the explainer says *true to the sources*, and does it explain?
- **Experience reviewer:** does every interactive figure *teach its sentence*, and does the page read well?

## Token rules (why this stays cheap)

1. **Paths, not content.** Give reviewers absolute paths. Never paste sections, reports, or sources into the prompt.
2. **Packets instead of raw files.** Every build writes `review/fidelity-packet.md` and `review/figures-packet.md`. The first is the explainer as plain text with line numbers (no scripts, no markup), the derivation steps with their stated reasons, the equations and code excerpts the build pulled verbatim (marked PULLED: they cannot deviate), and, for every chip, the evidence it points to: the cited equation's TeX, the cited code lines, the first lines of the vault note. The second holds caption and script per figure. A reviewer can settle most claims from its packet alone and opens a source file only when the evidence is not enough. The packets keep a reviewer's reading independent of the repository's size; without them a reviewer roams the paper and the code, and its cost grows with the project.
3. **Findings only.** No praise, no summary of the explainer, no restating of what is fine. At most 12 findings per reviewer, one line each plus the fix.
4. **One round by default.** A second look happens only when a blocker was raised, only by the reviewer who raised it, only on the changed files. If the harness lets you continue a finished agent (SendMessage), continue that reviewer instead of starting a fresh one: it still holds the sources in context.
5. **Screenshots of figures only.** `check.py --shots` writes one PNG per interactive figure. Section tiles (`--sections`) are for diagnosing a layout problem, not for routine review.
6. **Reviewers are read-only** (`subagent_type=Explore`). They cannot edit; you apply the fixes.
7. **Two rounds of reading, then the answer.** A reviewer's cost grows with every round of tool calls, because its whole context is processed again each round. The prompts therefore prescribe: round 1, read everything on the list in one message as parallel calls; round 2, optional, at most three targeted source reads; then answer. Arithmetic is done by hand, not with tools. Measured on the bundled example with four planted defects (a sign error in a derivation, a wrong headline number, a false claim about the code, a caption contradicting its figure): reviewers reading raw files 113k tokens, packets 108k, packets with the two-round budget 97k, and every protocol found every defect within its remit. Expect about 50k tokens per reviewer as a floor.
8. **Give context, once.** Both prompts have a `Context` slot. Fill it from section 0 of `brief.md`: the input tier, deliberate deviations from the paper's route, and the shared toy parameter set if figures use one. A reviewer who does not know that a figure is a declared toy with illustrative parameters will spend tokens looking for the calibration.
9. **A smaller model is fine for the experience reviewer** when the harness lets you choose one per subagent; keep the fidelity reviewer on the strongest model, because checking a derivation is where it earns its cost.

Dispatch both reviewers in one message (two Agent calls) so they run in parallel. Do not edit section files while they run (their line numbers would go stale); update `brief.md` or draft the delivery note meanwhile.

## Reviewer 1: fidelity

```
You review an interactive explainer of a research project for FIDELITY to its sources. The readers are the
project's own authors, so an error in a derivation or a wrong claim about their code is the worst defect.

Context: <input tier; deliberate deviations from the paper; shared toy parameters, if any>

WORKING BUDGET (your cost grows with every round of tool calls, because your whole context is re-read each round):
- Round 1: read these two files, both in ONE message as parallel tool calls:
  <abs>/explainer/brief.md                          (intended content and scope)
  <abs>/explainer/review/fidelity-packet.md
- Round 2 (only if needed): at most 3 targeted reads of source files listed at the end of the packet, again in ONE
  message, and only for claims the packet's evidence cannot settle. Read the function or the paragraph, not the file.
- Then answer. No further rounds. Do arithmetic by hand. Do not read the section .html files: they are the packet plus scripts.

The packet contains the explainer's text with line numbers (L12 = line 12 of the section file named in the heading), every
derivation step with its stated reason, the text of flow-diagram boxes, and under "Evidence for the chips" the equation or
the code lines each pointer cites. Lines marked PULLED were copied from the source by the build; do not re-verify them.

The build already verified that every pointer exists. You verify MEANING. Work in this order:
1. Derivations: check every hand-written STEP. Is it valid, is the stated reason the actual reason, do start and end
   match the PULLED equations? Redo the algebra of a step only when it looks wrong or the reason does not explain it.
2. Numbers: every number in text, KPI tiles and figure defaults against the paper or the result file it cites.
3. Code claims: for each [[code:...]] chip, does the cited code do what the sentence says? Read the function, not the file.
4. Gap: is prior work described by what it did and where it stops, consistent with the paper's related work?
   Anything inferred must be marked [[reading]].
5. Honest inventory: is a paper-versus-code difference or an assumption missing that you noticed during 1 to 4?
6. Scope: name sections or paragraphs an author would not miss (background they know, paper restated, plumbing),
   and the one important idea of the project that is missing, if any.

Output exactly this, nothing else:

## Fidelity review
| Category | Score /10 |
|---|---|
| Derivations correct and justified | N |
| Numbers and code claims match sources | N |
| Gap stated fairly and sourced | N |
| Honest inventory complete | N |
| Scope: nothing missing, nothing superfluous | N |

### Findings (max 12, most severe first)
- [blocker|major|minor] sections/NN-file.html:LINE : what is wrong, the source that shows it (path:line or \label) -> the fix

Severity: blocker = the explainer states something false about the paper, the math, or the code. major = misleading,
unsupported, or a derivation step without a valid reason. minor = wording, emphasis, a missing pointer.
Score 9 = ship as is. Be strict; an inflated score costs the authors more than a harsh one.
```

## Reviewer 2: experience

```
You review an interactive explainer of a research project for how well its FIGURES AND PAGE TEACH. The readers are
the project's own authors and co-authors.

Context: <input tier; whether figures are toys with a shared illustrative parameter set, and which; the model formulas
a reader needs to check a figure value by hand, if they are not in the brief>

WORKING BUDGET (your cost grows with every round of tool calls, because your whole context is re-read each round):
- Round 1: read ALL of the following in ONE message as parallel tool calls:
  <abs>/explainer/brief.md                          (section plan with one knob-to-insight sentence per figure)
  <abs>/explainer/review/figures-packet.md          (caption and script of every figure)
  <abs>/explainer/review/check.md                   (automated check report)
  <abs>/explainer/review/shots/<figure-id>.png      (list every screenshot by name; default state of each figure)
- Round 2 (optional): one read of the text part of <abs>/explainer/review/fidelity-packet.md (stop at "Evidence for
  the chips") for the page-level questions.
- Then answer. No further rounds. Check values by hand, not with tools. Do not read the section .html files or the paper.

For each interactive figure (each <figure class="widget">):
1. Read its <script>. Does the draw function compute the mechanism the caption claims (the real formula at toy scale),
   or does it fake a plausible curve? Check one value by hand at the default parameters.
2. Is the "Notice" statement TRUE according to the script, in the state it talks about? A Notice about another state
   ("at n = 100 ...", "with costs equal ...") has to be checked by hand in that state; the screenshot shows only the default.
   Would moving the named control make it checkable, and is it falsifiable from the picture?
3. Controls: two to four, ranges include the degenerate cases, defaults at the paper's setting, a preset where useful.
4. Chart discipline: axis labels with units, colours used with the meaning the project's colour code gives them (the
   [[role]] entries, listed in the hero), at most three coloured series (navy, orange, teal) plus gray, no dual axes, legend or end labels
   present, nothing cut off or overlapping in the screenshot.
   Is the effect visible at the default setting, or do the curves sit in a sliver of the panel?
   Do the toy's constants match the code's or the paper's, and where they differ, does the caption name both?
5. toy: true present on everything that is not the repository's own result; evidence figures read embedded files.
Then for the page: does each section lead with a plain sentence before notation; are there walls of text without a
figure, table or callout; do captions have Try and Notice; is any house wording rule broken (dashes as punctuation,
"not X but Y", leverage/delve/comprehensive/seamless)?

Output exactly this, nothing else:

## Experience review
| Category | Score /10 |
|---|---|
| Figures implement the real mechanism | N |
| Each figure delivers its insight | N |
| Controls, defaults, readouts | N |
| Chart discipline and legibility | N |
| Page flow and wording | N |

### Findings (max 12, most severe first)
- [blocker|major|minor] sections/NN-file.html:LINE (figure id) : what is wrong -> the fix

Severity: blocker = a figure shows something false or contradicts the paper. major = a figure does not deliver its
insight, a control is pointless, the picture is illegible. minor = polish.
Score 9 = ship as is. Be strict.
```

## The merged reviewer (review depth `single`)

For `focus` and `overview` explainers one reviewer covers both remits at about half the cost. Use the fidelity prompt with these changes: round 1 reads `brief.md`, `fidelity-packet.md`, `figures-packet.md`, `check.md` and every screenshot, all in one message; the work list is the fidelity list 1 to 5 followed by the figure checks 1 to 5 of the experience prompt; the output has one score table with six rows (derivations; numbers and code claims; gap and inventory; figures implement the real mechanism; each figure delivers its insight; page flow and wording) and at most 14 findings. Scope item 6 of the fidelity list is dropped: a small explainer has little to cut.

## After the reviewers return

1. Show the user one merged table, not the raw reports:

   ```markdown
   ## Review, round N
   | | Derivations | Numbers and code | Gap | Inventory | Scope | Mechanism | Insight | Controls | Charts | Flow |
   |---|---|---|---|---|---|---|---|---|---|---|
   | Score | 9 | 8 | 9 | 7 | 9 | 9 | 8 | 9 | 9 | 9 |

   | # | Severity | Where | Finding | Action |
   |---|---|---|---|---|
   | 1 | blocker | 02-core-idea.html:58 | step 3 differentiates x ln x without the product rule | fix |
   | 2 | minor | 02-setting.html:12 | "comprehensive" | fix |
   | 3 | minor | fig-queue | add a slider for the noise level | skip: would be a fifth control |
   ```

2. Verify before you fix. A reviewer can be wrong about the paper. For every blocker and major, open the cited source line yourself; if the finding does not hold, mark it "rejected" with the reason. Do not apply findings on trust.
3. Apply blockers and majors. Apply minors when they are cheap. State which ones you skip and why.
4. Rebuild and rerun `check.py`. Both must be clean again.

## Loop by review depth

- **standard:** one round. If round 1 had a blocker, send the changed section files back to the reviewer who raised it with: "Round 2. Only these files changed: <paths>. Were these findings resolved: <the blockers, verbatim>? Answer per finding: resolved or not, one line. Report a new finding only if it is a blocker." Then stop, whatever the answer, and report unresolved points to the user.
- **full:** repeat both reviewers until every category is 9 or better, at most three rounds. From round 2 on, tell each reviewer which files changed and to re-score only the affected categories. After round 3, hand the remaining findings to the user as questions. Explainers can get stuck in polish loops; the cap forces escalation.
- **light:** no reviewers.

Record the outcome at the end of `brief.md`:

```markdown
## Review record
- 2026-09-17, standard, 1 round. Fidelity 9/8/9/7/9, experience 9/8/9/9/9. 1 blocker fixed (02-core-idea.html step 3), 2 minors skipped.
```
