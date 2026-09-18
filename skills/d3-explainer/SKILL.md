---
name: d3-explainer
description: |
  Create a D3 (Data Driven Decisions) interactive HTML explainer of a research project: one offline file that builds up the concepts, the key derivations, the research gap, and how the code realizes it, with interactive figures (sliders, draggable points, step-through derivations). Written for the repo's own author and co-authors to understand their project better, not for outsiders. Use when:
  (1) The user wants an explainer, walkthrough, or build-up of a research repo, paper, model, or derivation ("help me understand my own project")
  (2) Scanning code, paper sub-directories, vault, and results to explain what a project does and why
  (3) Onboarding a co-author; visualizing a model or derivation interactively
  (4) Updating an existing explainer after paper or code changed
  MANDATORY TRIGGERS: explainer, Erklärseite, D3 explainer, HTML explainer, interactive explainer, explain my project, explain my repo, explain the paper, explain the derivation, project walkthrough, co-author onboarding
---

# D3 Explainer (interactive HTML, for the authors themselves)

> **`<skill-dir>`** in this skill means the skill's own base directory, which Claude Code shows when the skill loads (installed as a plugin: `${CLAUDE_PLUGIN_ROOT}/skills/d3-explainer`; copied by hand: `~/.claude/skills/d3-explainer`). Substitute the real path in every command.

One offline HTML file that explains a research project to the people who are writing it: what the question is, which gap it closes, how the core idea works, how each derivation goes and why, where it all lives in the code, what the evidence shows, and what is still open. Interactive figures carry the intuition; the text stays close to the sources and says so.

**The reader is the author and their co-authors.** That decides almost everything below:

- They know the field. Skip textbook background unless their notes show it is a sore spot.
- They want to understand, so honesty beats polish: assumptions, paper-versus-code disagreements, and open questions get their own section, and interpretations are marked as such.
- They will check claims against their own files, so every substantive claim points to its source, and the build verifies that the pointer exists.
- Elaborate is fine, exhaustive is not. Depth that only some readers want goes into collapsed blocks. "Every detail" happens only when the user asks for it, and then only for the part they name.

All Python runs through uv (`uv run`, `uv run --with <pkg>`); never pip, never global installs.

## Reference files (load on demand)

| File | Load when |
|---|---|
| `references/scanning.md` | Phase 1: reading a repo on a token budget, input tiers, vault / recall / NotebookLM, prior explainers |
| `references/content-design.md` | Phase 2 and 3: section spine, depth budgets, how to present the gap and derivations, honest inventory, wording rules |
| `references/components.md` | Phase 3: the HTML vocabulary, source chips, build directives, `explainer.toml`, the `D3X` JavaScript API |
| `references/visualization.md` | Phase 2 and 3: designing interactive figures that teach; pattern catalog; pitfalls |
| `references/review.md` | Phase 4: the two reviewer prompts, token rules, the loop |
| `assets/example/` | A tiny repo with a finished explainer. Read `assets/example/explainer/sections/*.html` once for working patterns of every component. Never copy it into a user project. |

## Step 0: ask once

Unless the user already said it, ask these in one message, then do not ask again:

> **Scope.** The whole project, or one part (a model, a derivation, a pipeline)?
> **Depth.** `focus` (one idea or one derivation: 1 to 3 sections, one or two figures, about 5 min), `overview` (4 to 6 sections, about 10 to 15 min to read), `standard` (default: 7 to 10 sections, 4 to 8 interactive figures, 1 to 3 derivations, 20 to 35 min), or `deep` (up to 14 sections). "Deep on X" means standard plus one deep-dive section on X.
> **Review.** `light`: automated checks plus my own numbers pass, almost no extra tokens. `single`: one reviewer agent covers both fidelity and figures, one round, about 50 to 70k tokens. `standard`: two reviewer agents in parallel (fidelity to your sources; figures and interaction), one round, about 100 to 150k tokens together. A reviewer's cost is mostly a fixed floor and hardly depends on the project's size, so my recommendation follows the depth: `focus` light, `overview` single, `standard` and `deep` the two-agent review. `full`: the two agents loop until every score is 9 of 10, capped at three rounds, two to three times the cost of standard.

"quick", "no review", "cheap" or "short on tokens" means light. "thorough" means full. "just this derivation", "only explain X", "keep it short" mean focus. Nothing said means depth standard, and the review recommended for the depth.

**When nobody can answer** (a batch or agent run): take the defaults, decide every point this skill would ask about, record each decision in section 0 of `brief.md`, and continue. The brief is then the place where the author can see what was decided for them.

## Workflow

Print a one-line timestamped status at each phase boundary, as the other D3 skills do: `[HH:MM:SS] PHASE: ...`.

### Phase 1: Map the project (read cheaply, in the right order)

```bash
uv run <skill-dir>/scripts/scan.py            # from the repo root; add --out explainer/scan.md to keep it
```

The scan reports the input tier (A: code and paper, B: paper only, C: code only, D: PDF only, E: notes only), when the orientation documents, the paper and each code folder last changed (a stale `CLAUDE.md` or an abandoned approach shows up here), the paper outline with its equation labels, the largest code modules with symbol names and line numbers, embeddable result files, the vault with the author's own notes by folder, prior explainers, and a token estimate for everything. Print `INPUT TIER: X` and let the user override.

Then read, in this order, and stop when the brief can be written. Details and budgets are in `references/scanning.md`.

1. Orientation documents (`CLAUDE.md`, `README`, spec or analysis notes at the root).
2. The paper: abstract, introduction, contribution statement, then the model and method sections. Skim results for the headline numbers.
3. Prior explainers found by the scan: the outline (`scan.py --explainer <file>`), then one section in full for tone (`--section N`). They show what the author already understands and the voice they like. Build on them; do not repeat them.
4. Vault: overview, concept, gap, decision and open-question notes, chosen by title. Not the literature dump.
5. Code: only the modules that realize the core idea, found through the symbol map. For a large code base (over about 40 files or 8,000 lines) send one `Explore` subagent to produce the paper-to-code map and keep its conclusion, not the files.

Optional enrichment, offered only when the gap or the project history is thin in the repo: the `recall` skill (what was decided, and when) or NotebookLM (what the literature says). Same protocol as in `d3-abstract`. Print `ENRICHMENT: skipped | recall | notebooklm | both`.

### Phase 2: Content brief, approved before any HTML

```bash
uv run <skill-dir>/scripts/init.py --depth standard --review standard   # creates ./explainer: explainer.toml, brief.md, sections/, d3x/
#   several papers in the repo: add --paper <folder>         explainer elsewhere: init.py <dir> --repo <repo root>
```

Save location: `<repo>/explainer/`, at the root of the outer repository (not inside the paper submodule: Overleaf has no use for it). Confirm the location in the same message as the brief.

Fill `explainer/brief.md`: the project in two sentences, what the reader should be able to do afterwards, sources read and deliberately not read, the gap, the section plan, the derivations, the honest inventory, and what is left out on purpose. The section plan has one line per section and, for every interactive figure, its **knob-to-insight sentence**: "moving X shows that Y". A figure without such a sentence is decoration and gets cut here, not after it is built.

Show the brief in chat in compact form and get approval. This is the one mandatory checkpoint: it costs a few hundred tokens and prevents writing the wrong 6,000 words. Do not write sections before it.

### Phase 3: Write, one section at a time

Load `references/components.md` and `references/visualization.md`, and skim the example sections once.

- One file per section: `explainer/sections/NN-slug.html`, exactly one `<section id=... data-nav=... data-kicker=...>` each. The build numbers them and creates the navigation.
- Build after every section, so errors stay local: `uv run explainer/d3x/build.py --draft` (TODO markers and links to sections not yet written only warn)
- Order inside a core-idea section: plain sentence, interactive figure, formal statement, derivation, where it lives in the code. Intuition first, algebra second.
- **Let the repository speak instead of retyping it.** `<div class="eq" data-label="eq:prob"></div>` pulls the equation from the paper's `.tex` (with its number, if an `.aux` exists). `<pre class="code" data-src="src/model.py" data-lines="88-104"></pre>` pulls the real lines. Both are cheaper than typing and cannot drift from the source.
- **Point to sources with chips**: `[[paper:eq:prob]]`, `[[code:src/model.py:88 def solve]]`, `[[vault:Note name]]`, `[[result:results/table.csv]]`, and `[[reading]]` for your own interpretation. The build fails on a file, line, symbol, label, or note that does not exist. A failed chip is a finding about your understanding: fix the claim, do not delete the chip.
- Interactive figures show, in order of preference: the repository's result files; numbers computed by the repository's own code on a grid (a small `explainer/data/make_data.py`, see `visualization.md`); or the real formula re-implemented at toy scale in the browser, declared `toy: true`, which puts a visible "illustrative toy" badge on it. Defaults sit at the paper's setting. Numbers are embedded from files, never typed from memory.
- Every figure caption starts with `{fig}` (the build numbers figures; refer to one as `{fig:figure-id}`) and says what to try and what to notice.

### Phase 4: Verify

```bash
uv run explainer/d3x/build.py                  # no --draft: TODO markers now fail; prints words per section against the depth budget
uv run explainer/d3x/check.py --shots          # headless browser: moves every control, drags every handle, steps every derivation
```

`check.py` must end with `0 error(s)`. It catches what reading the source cannot: NaN in a path, a control that changes nothing, a formula MathJax cannot render, a label cut off at a slider extreme, page overflow at phone width. Its first run on a machine may ask for a browser once: `uv run --with playwright playwright install chromium` (it falls back to an installed Chrome or Edge).

Look at two or three of the screenshots in `explainer/review/shots/` yourself. Then review at the chosen depth; prompts and token rules are in `references/review.md`:

- **single**: one read-only reviewer with the merged prompt from `references/review.md`, reading both packets, `check.md` and the screenshots in one round. Then verify and apply as below.
- **light**: no reviewer agents. Do one numbers pass yourself: every number in the text, the KPI tiles, and the figure defaults against the paper or the result file it cites. Then stop.
- **standard**: two read-only reviewers in parallel, one round. Each build writes two packets into `explainer/review/`: `fidelity-packet.md` (the explainer's text with line numbers, the derivation steps with their reasons, and for every chip the cited equation or code lines as evidence) and `figures-packet.md` (caption and script of every figure). The *fidelity reviewer* checks derivations, numbers, and gap claims from the first; the *experience reviewer* checks that every figure teaches its knob-to-insight sentence from the second, plus `check.md` and the screenshots. Neither needs to roam the repository, which is what keeps the review affordable. Do not edit section files while they run. Then verify each blocker and major yourself, apply them, rebuild, rerun `check.py`. A second look happens only for a blocker, only by the reviewer who raised it, only on the changed files.
- **full**: the same two reviewers, looped until every category is 9 or better, capped at three rounds; then hand the remaining points to the user.

### Phase 5: Deliver

Give the path `explainer/dist/<name>.html` (one file, works offline, safe to email), the review depth used, and the merged findings table with what was fixed. Mention: `n` opens the notation drawer, derivations step with "Next step", chips link to GitHub permalinks at the built commit when the remote is on GitHub. If the repo has a vault, offer to drop a copy of the HTML into it, where the author's earlier explainers live. Offer to commit `explainer/` (without `review/`); commit only on a yes.

## Rules that carry the quality

**Sources and honesty**
- Every derivation, number, and claim about prior work carries a chip, or is marked `[[reading]]`. Nothing is invented: no results, no citations, no file names.
- The explainer states where paper and code disagree, which assumptions carry the result, and what is open. For the author this section is often the most valuable one. If you found nothing to put there, you have not looked closely enough; say what you checked.
- Related work is described by what it established and where it stops, as facts. The gap is a statement about the literature, not a verdict on other authors.

- Embedded data travels with the file. Before embedding, drop or relabel personal and pseudonymous identifiers (household or customer IDs, names, addresses, meter numbers) unless the author confirms they may ship; aggregate where the figure allows it. Say in the delivery message what data the file contains.

**Scope**
- One idea per section, one interactive figure per idea at most. The build prints main-line words and figure count against the budget of the chosen depth; treat an over-budget warning as a request to fold or cut, not to raise the budget.
- Optional depth goes into `<details class="deep">`. It does not count toward the main-line budget, which is the point.
- Leave out: literature surveys, code plumbing (I/O, logging, CLI parsing), paragraph-by-paragraph restatement of the paper, background the author demonstrably knows.

**Wording** (the house rules of the other D3 skills; the build warns on the mechanical ones)
- No em-dashes or en-dashes as punctuation. No "not X, but Y". No leverage, delve, seamless, comprehensive, robust framework. First person plural for the project's own work. Concrete numbers instead of adjectives. Section titles state the message and vary in length.

**Look and presentation** (the engine provides the look in the D3 corporate design; the content has to use the devices)
- A long-read in the D3 colours (navy, orange, teal, gray, as in d3-presentation) and Inter, with mono for labels, controls and readouts: dark-blue hero, one narrow column with wider figures. The design is not the point; what is presented and how is.
- The hero carries the project's signature: its central equation (pulled from the paper with `[hero] equation`, or written with `[hero] tex`) or, failing that, the claim in one sentence. One word of the title may be accented (`title_html` with `<em>`).
- A colour code is defined once and kept everywhere. Two to five `[[role]]` entries in `explainer.toml` name what the colours mean in this project (what is chosen, what is earned, what is exogenous; or one colour per competing method). Each role is a colour name in plots (`color: 'choice'`), a macro in formulas (`\choice{b}`), and an entry of the hero's legend. Give the roles D3 colours: navy, orange, teal, in that order, and gray for a fourth; with more roles than that, reduce the roles. Never use a colour that has no stated meaning; gray is also for baselines and references.
- The build-up is visible: numbered step badges per section, and on wide screens the assembling panel (`[hud]` lines plus `data-hud="k"` on sections) that lights up the pieces of the central equation or argument as the reader scrolls.
- In figures: at most three coloured series plus gray, two panels instead of two y-axes, fixed axes while a slider moves. Orange marks what the reader moves.

## Updating an existing explainer

The header of the page shows the commit it was built from. When paper or code moved on:

1. Refresh the engine first; it is always safe and brings the newest diagnostics: `uv run <skill-dir>/scripts/init.py explainer --refresh`.
2. Run `uv run explainer/d3x/build.py`. It re-validates every pointer against the current repo and lists every place that needs attention: renamed labels and missing files as errors, functions that moved as warnings (the chip already follows the function name; update the number), code excerpts selected by line range with the line they now begin with. Switch such excerpts to `data-symbol`.
3. Find what changed in substance. With git: `git log --oneline <built-commit>..HEAD -- <paper and src paths>`. Without git: the diagnostics plus `grep -n "\[\[" explainer/sections/*.html`. Moved code has often changed: reread each sentence next to a pointer the build flagged, and recheck quoted numbers against the result files.
4. Edit the affected section files in place, rebuild, run `check.py`. Version with git, not with file names.

Pointer-only updates need no new brief and no reviewers: automated checks plus your own numbers pass (review depth light). When claims, derivations or figures change, tell the user which sections are affected before editing, and review those sections at the depth they chose.

## Decision points

**Ask the user:** scope, depth, review depth (Step 0); the input tier if the scan is ambiguous; which paper, when several exist; approval of the brief; whether a gap statement you could only infer is right; commit and vault copy at the end.

**Decide yourself:** section order and titles; which component fits which content; which figure pattern fits which idea; what goes into `<details>`; parameter ranges and presets of figures (defaults at the paper's setting); which minor review findings to skip.

## Checklist before delivery

- [ ] Brief approved; `brief.md` reflects what was actually built
- [ ] `build.py` without `--draft`: 0 errors, no over-budget warning left unanswered
- [ ] `check.py --shots`: 0 errors; screenshots looked at
- [ ] Every figure has a knob-to-insight sentence in the brief and a Try / Notice caption; toys are marked `toy: true`
- [ ] Every derivation step has a reason (`data-why`), and the derivation matches the paper or says where it deviates
- [ ] Whole-project explainers (overview and up): gap section with what exists, where it stops, what this project adds, each with a source or `[[reading]]`; paper-to-code map for tier A. A `focus` explainer skips both unless asked
- [ ] Honest inventory present: assumptions, paper-versus-code, open questions (in a `focus` explainer: a short closing block on what the explained part assumes and leaves open)
- [ ] Notation table present (`id="notation"`), with the code names of the symbols where they exist
- [ ] Review done at the chosen depth; findings and fixes reported to the user
