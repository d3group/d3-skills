# Scanning a repository on a token budget

The explainer is only as good as your understanding of the project, and understanding is where tokens go. Read in the order of information per token, stop when the brief can be written, and record in `brief.md` what you read and what you skipped, so the author can say "you missed the important note".

## 1. Run the scan first

```bash
uv run ~/.claude/skills/d3-explainer/scripts/scan.py [repo] [--out explainer/scan.md]
```

One call, a few seconds, about 1 to 3k tokens of output. It lists: git state and submodules, input tier, when the orientation documents, the paper and each code folder last changed, each paper with title, abstract, outline, section files with token sizes, equation and section labels, macro files, whether an `.aux` exists; code volume by folder, entry points, the largest modules with `symbol:line`; result folders and small tables that can be embedded; vaults with their folders, key notes, and recent notes; prior explainers; orientation documents. Do not re-derive any of this with `ls` and `grep`.

## 2. Input tiers

| Tier | What exists | Consequence |
|---|---|---|
| **A** | code and paper source | The full explainer. Every idea links to paper and code. The honest inventory can compare the two. |
| **B** | paper source only | Derivations and gap from the paper. The "realization" section describes the planned or external implementation, or is dropped. |
| **C** | code only | Reconstruct the idea from code, README, notes. Reconstructions are `[[reading]]`. Ask the author to confirm the problem statement and the claimed contribution before the brief. |
| **D** | compiled PDF only | Extract text: `uv run --with pymupdf python -c "import fitz,sys; [print(p.get_text()) for p in fitz.open(sys.argv[1])]" paper.pdf`. Equations must be typed by hand and cannot be validated; say so in the brief. |
| **E** | notes or conversation only | Interview first: question, setting, contribution, the two or three ideas that are hard, what exists so far. |

Several papers in one repo: ask which one, or whether the explainer covers the project across papers. Never merge papers silently.

## 3. Reading order and budget

Rough budgets for a `standard` explainer. They are guidance, not limits; a 25-page theory paper deserves more paper tokens and fewer code tokens.

| Step | Read | Typical budget |
|---|---|---|
| 1 | `CLAUDE.md`, `README`, root-level spec or analysis notes | 3 to 8k |
| 2 | Paper: abstract, introduction, contributions, model and method sections in full; results skimmed for headline numbers and the experimental setup; related work for the gap | 15 to 35k |
| 3 | Prior explainers: `scan.py --explainer file.html` prints the outline with word counts; `--section N` prints one section as plain text (read one for tone, and the ones that overlap with the new scope) | 1 to 4k |
| 4 | Vault: choose by title, at most 6 to 10 notes: project overview, concept notes, gap audits, decisions, open questions, the latest spec delta | 8 to 20k |
| 5 | Code: the modules that realize the core idea, by symbol from the scan; read functions, not files | 8 to 25k |
| 6 | Results: one or two small tables to embed; the paper's own figures to reuse | 1 to 4k |

Reading tactics that save the most:

- **Check which approach is current before building a mental model.** A repo may hold two parallel approaches (`src/v1`, `src/v2`) while the paper covers one, and `CLAUDE.md` may describe the older one. The scan's "Last changed" line and its NOTE flag this. When in doubt, grep the paper for the module and function names.
- **Read `.tex` section files whole, in paper order.** They are the densest source, and you need exact labels for `[[paper:...]]` chips and `data-label` equations.
- **Read code by symbol.** The scan gives `name:line`. Read `offset`/`limit` windows around the symbols that implement the model, the loss, the solver, the estimator, the evaluation metric. Skip data loading, logging, CLI parsing, plotting.
- **Large code base (over about 40 files or 8,000 lines): delegate the map.** One `Explore` subagent, with the paper's method section path and this task: "Produce a paper-to-code map: for each of these concepts [list from the paper], the file, function, and line range that implements it; the main pipeline from entry point to result file as a list of steps; anything the code does that the method section does not mention, and the reverse. At most 60 lines, with `path:line` for every item." Keep its answer; do not open the files again except to pull excerpts.
- **Vault notes: titles first.** A vault with hundreds of notes is mostly literature imports (`Notes/NotebookLM/...`, `Sources/`). The notes that matter for an explainer are the author's own, which the scan lists by folder with their sizes: overviews, `Concepts/`, `Reviews/` (gap audits, referee audits), decisions, open questions, spec deltas. Dated notes tell the history of model decisions; the explainer can mention a decision and its date where it explains why the model looks the way it does.
- **Session logs (`Claude-Sessions/`)**: skip unless the author asks for project history; use the `recall` skill for that.

## 4. What to extract while reading

Keep a running list; it becomes `brief.md`.

- The question and the claim, in the author's words, with the label or line where they say it.
- The gap: which strands of prior work the paper positions against, what each established, where each stops. Source: introduction, related work, a gap-audit note. If the repo does not contain a positioning, say so and offer NotebookLM or a short interview instead of inventing one.
- The two to five ideas that are genuinely hard. Signals: long derivations, notes titled "why ...", repeated spec revisions, review comments, places where paper and code differ.
- For each hard idea: the formal object (equation labels), the intuition, what could be moved in a figure, where the code implements it.
- Notation, with code names.
- Headline results and the files they come from.
- Disagreements between paper and code, unstated assumptions, open questions, planned extensions.

## 5. Optional enrichment

Offer it only when the repo leaves the gap or the project history thin. Same protocol as `d3-abstract`:

- **Recall** (`recall` skill through the Skill tool): what was decided, when, and what is open.
- **NotebookLM**: `notebooklm status`, agree on the notebook and one targeted question with the user, `notebooklm ask --new --json "{question}" > "${TMPDIR:-/tmp}/d3-explainer-notebooklm.json"`, read `answer` and `references[].cited_text`. Literature claims that come from there are marked `[[src:NotebookLM, <notebook>]]`.

Summarize what came back in three to five bullets and ask before using it. Fallbacks: QMD missing, offer NotebookLM or skip; authentication expired, suggest `notebooklm login` or skip.

## 6. The paper-to-code map

Tier A explainers should contain this table (in the realization section), because it is the thing authors most often cannot reproduce from memory:

| Concept | Paper | Code | Note |
|---|---|---|---|
| Success probability | `[[paper:eq:prob]]` | `[[code:src/secretary.py:8 def success_probability]]` | the code evaluates the exact finite-n value; the paper analyses the limit |

Build it while reading; every row needs both pointers or an explicit "not in the paper" or "not implemented".
