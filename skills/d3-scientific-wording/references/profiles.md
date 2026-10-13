# Measured wording profiles (optional)

The rules in `rules.md` are the group's floor, and `outlets.md` with its family files in `outlets/` describes outlets from general knowledge. A measured profile replaces the general description with numbers from real texts: how long the sentences of EJOR papers are, which term the decision-focused learning literature prefers, how the user's own papers state a contribution. Read this file when the user agreed to Step 1b of SKILL.md.

## Contents

1. Three kinds of profile
2. Sources
3. The question
4. Selecting and measuring the corpus
5. From profile to decisions
6. Precedence
7. Integrity
8. Cautions
9. Reuse

## 1. Three kinds of profile

| Kind | Corpus | What it gives | Typical use |
|---|---|---|---|
| **Author** | the user's own papers | the user's voice: sentence length, stance (hedges, boosters, "we"), punctuation habits, recurring formulations, how they state contributions | a paper or rebuttal that should sound like the user's earlier work |
| **Outlet** | papers published in the target venue | the venue's conventions: register, person, sentence length, how papers state gaps and contributions, typical section moves | a submission to a venue the user has not written for, or a venue with a strong house style (Nature, IEEE Transactions, econ journals) |
| **Topic** | papers on the topic, any venue | the field's terminology: the dominant term and spelling for each concept, the standard abbreviations, collocations | the term sheet of any document; an explainer or deck on a topic with competing names |

A document can use more than one: an outlet profile for register and a topic profile for terms is the common pair.

## 2. Sources

| Source | How to find it | What it can give |
|---|---|---|
| Literature folder (PDFs, `.tex`) | folders named `literature`, `papers`, `refs`, `bib`; the d3-explainer scan lists them | outlet and topic profiles; an author profile from the user's own papers in it |
| The user's own papers | paper submodules and folders in the repositories, the user's publication folder | author profile. Prefer single-author papers and papers the user wrote most of |
| A draft and its final version | two versions of the same paper | the user's revision moves (what they cut, merge, add); measure both and compare |
| Obsidian vault | a folder with `.obsidian/`, or a name containing "vault" | the user's own notes: their vocabulary (topic), not their prose style. Imported sources (`NotebookLM/`, `Sources/`, `Literature/`, `Clippings/`): topic and outlet profiles like PDFs. Drafts kept in the vault: author profile |
| NotebookLM notebook | `notebooklm status` | with the `notebooklm-import` skill, its sources become files in the vault and are measured like PDFs. Without it, targeted questions only (below) |

**NotebookLM without import.** Counts need the texts, and the `notebooklm` CLI answers questions; it does not hand out full sources. Ask at most three targeted questions with `notebooklm ask --new --json "<question>" > "${TMPDIR:-/tmp}/d3-wording-notebooklm.json"` and read `answer` and `references[].cited_text`, as d3-abstract does:

- "Which terms do the sources use for <concept>? Name each term with the sources that use it."
- "Quote one sentence from each of three sources in which the source states its contribution."
- "Which abbreviations do the sources define for <topic>?"

Mark what comes back as quoted evidence (`[NotebookLM, <notebook>]`), not as counts, and say so in the profile.

## 3. The question

Ask only when a source was detected or the user mentioned one; never search the user's home folder for literature. Put it into the Step 1 question round, or into the caller's enrichment question where the caller has one:

> **Wording profile (optional).** I found [42 PDFs in `literature/` | your vault | a NotebookLM notebook]. I can measure how [your own papers | papers in <outlet> | papers on <topic>] are written and adapt the wording to it: sentence length, stance, standard terms and phrases. A script does the counting in about a minute; reading the profile costs about 3k tokens. Which profile, if any?

Default: no profile. In a batch run, skip it and record "no profile".

## 4. Selecting and measuring the corpus

```bash
uv run <skill-dir>/scripts/wording_profile.py list <folder>                                   # words, year, venue hint per file
uv run <skill-dir>/scripts/wording_profile.py list <folder> --match "Operational Research"    # preview a selection
uv run <skill-dir>/scripts/wording_profile.py measure <folder or files> --kind outlet --name EJOR \
    --match "European Journal of Operational Research" --out <project>/wording-profile-ejor
```

- **Select by evidence, not by guess.** `--match` searches the PDF metadata, the first page and the file name: a journal name for an outlet profile, the user's surname for an author profile, nothing for a topic profile of a curated folder. Check the selection with `list` first, and drop files that are not papers (slides, theses, supplementary material) by naming files explicitly.
- **Size.** At least 3 documents and 10,000 words for bands; 5 documents and 20,000 words for solid evidence. The profile states its own evidence level. With fewer documents, read it as anecdotes.
- **What the script does.** It extracts the body text (running headers removed, captions, tables and the reference list dropped), splits sentences the same way as the lint, and writes `<out>.md` to read and `<out>.json` for `compare`. PDF extraction is heuristic: a two-column paper with heavy math loses some sentences, which is harmless for rates and medians.
- **Read `<out>.md` once** and write the decisions it implies under `## Wording` (section 5). Keep the profile files next to the project's notes file; they hold counts, term lists and short excerpts only.

During the check (SKILL.md, Step 4), put the draft next to the profile:

```bash
uv run <skill-dir>/scripts/wording_profile.py compare <project>/wording-profile-ejor.json paper/sections/*.tex
```

It prints each metric of the draft against the corpus band, and every term for which the draft uses a form the corpus does not prefer.

## 5. From profile to decisions

| Profile section | Decision under `## Wording` |
|---|---|
| Sentence length band | The target for the document's mean and 90th percentile. The lint caps stay as the outer limit. |
| Hedges, boosters | Where in the band the claims sit. A corpus with many boosters does not license overclaiming (section 6). |
| We / I / passive | The person: follow the outlet or the author. |
| Colons, semicolons, parentheses, dashes | Punctuation habits within the D3 rules: no dashes as punctuation whatever the corpus does. |
| Openers, connectives | Which connectives the outlet uses; a reference for varying openers. |
| What the corpus does that the D3 rules flag | Errors stay errors. A warning that is an outlet habit (for example "the remainder of this paper is organized as follows" in OR journals) may be kept with the reason "outlet convention (profile)". |
| Recurring formulations | Conventional phrases of up to about six words that many authors use ("to the best of our knowledge", "we contribute to") may be used. Longer phrases are evidence of structure, not text to reuse. |
| Terms, variants, abbreviations | They seed the term sheet: the dominant form and the standard abbreviation win, unless the user decides otherwise or the paper defines its own term on purpose. |
| Rhetorical moves | How and how often the corpus states contributions, gaps, limitations and implications: for example, whether an explicit limitations paragraph is the norm, or whether contributions come as an enumerated list. |

## 6. Precedence

1. The user's stated corrections and the text they wrote or approved.
2. The D3 rules at error level: direct claims, no dashes as punctuation, neutral related work, claims within the evidence, the genre's sentence caps.
3. The measured profile: targets, vocabulary, conventions; it can turn a warning into an accepted convention.
4. The general descriptions in `outlets.md` and `outlets/`, and the defaults.

An author profile describes how the user wrote, which can include habits the group rules exclude. Where they conflict, follow the rules and tell the user once which habit you did not reproduce and why.

## 7. Integrity

- **Never copy sentences from the corpus into the user's text.** Other authors' wording is theirs. Even the user's own published wording is not recycled verbatim into a new paper. Exemplars in a profile show structure: where the contribution sentence sits, how long it is, what it names.
- A profile stores counts, term lists and excerpts of at most 25 words with their source file. It never stores full texts, and the PDFs stay where they are.
- Text quoted by NotebookLM is marked as such in the profile.

## 8. Cautions

These come from the colleague's academic-voice skill, which was built on exactly this kind of measurement.

- **Absent is not evidence against.** A phrase the corpus never uses may still be fine; a small corpus, or one from length-limited venues, has no room for many legitimate devices. Only the user's explicit statement makes something a prohibition.
- **Co-authored text blends voices.** An author profile from co-authored papers measures the team. Single-author papers and the user's own draft-to-final edits are the clean evidence.
- **Measure what you think you measure.** A rate can be right while the distribution is wrong: a colon rate says nothing about whether colons cluster. Read the exemplars before trusting a number.
- **Bands are document-level.** Do not force every paragraph into the band; definitional passages and lists are legitimately different.
- **Converge, do not push.** Measure the draft, then move each metric toward the band from whichever side it is on. "Always tighten" is not a rule.

## 9. Reuse

- Before measuring, look for an existing profile: in the project, under the vault's writing notes, and in this skill's `references/profiles/` folder if the group has contributed one.
- **Author profiles** describe the user, not the project. Offer once to copy the profile into the vault (for example `<vault>/Writing/wording-profile-<name>.md`) so later projects start from it.
- **Outlet profiles** of the venues the group targets repeatedly (OR, IS, ML, economics, energy, game theory and games, sports science) are worth keeping. One that proved useful can be added to `references/profiles/<outlet>.md` in the d3-skills repository, with counts and short phrases only.
