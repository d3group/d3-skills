---
name: d3-scientific-wording
description: |
  Wording layer of the D3 (Data Driven Decisions) skills: how the sentences of a paper, abstract, poster, slide deck, explainer or rebuttal are phrased. Direct claims instead of "not X but Y", neutral related work, claims calibrated to the evidence, short sentences, concise scientific vocabulary, wording adapted to the outlet and the field, optional Simplified Technical English (ASD-STE100), and an optional clean-up of invisible AI marks. d3-abstract, d3-poster, d3-presentation and d3-explainer invoke it before they write text. Use when:
  (1) Writing or revising scientific prose: a paper section, an abstract, a related-work paragraph, a rebuttal, a proposal, a thesis chapter, slide or poster text
  (2) The text sounds generated, inflated, defensive or too complex, and should read as written by a researcher
  (3) Adapting the wording of a text to a venue (NeurIPS, ICIS, EJOR, Applied Energy, ...) or to a field
  (4) Writing or converting text in Simplified Technical English (STE, ASD-STE100)
  (5) Checking a draft against the D3 wording rules, or removing invisible characters and AI watermarks from finished text
  (6) Measuring how the user's own papers, a target venue or a topic's literature is written (literature folder, vault, NotebookLM) and adapting the wording to that profile
  MANDATORY TRIGGERS: wording, phrasing, writing style, scientific writing, academic writing, tone, sounds like AI, overclaiming, hedging, related work tone, concise, polish the text, rewrite this paragraph, rebuttal wording, Simplified Technical English, STE, ASD-STE100, plain English, watermark, invisible characters, wording profile, my writing style, style of the journal, how papers in this venue are written, Formulierung, Schreibstil, wissenschaftlich formulieren
---

# D3 Scientific Wording

> **`<skill-dir>`** in this skill means the skill's own base directory, which Claude Code shows when the skill loads (installed as a plugin: `${CLAUDE_PLUGIN_ROOT}/skills/d3-scientific-wording`; copied by hand: `~/.claude/skills/d3-scientific-wording`). Substitute the real path in every command.

This skill decides how the sentences of a research text are phrased. The calling skill or the user owns the content, the structure and the layout; this skill owns the wording. The goal is text that reads as written by a researcher of the group: it states what was done and found, describes other work by what it did, claims what the evidence carries, and keeps each sentence to one idea.

All Python runs through uv (`uv run`); never pip, never global installs.

## Files

| File | Load when |
|---|---|
| `references/rules.md` | Before writing or revising the first paragraph. The full rules with before/after pairs. |
| `references/outlets.md` | Step 1 and 3: detecting genre, outlet and field; the profile of each genre; the reader; the term sheet |
| `references/outlets/<family>.md` | Step 3: one file per outlet family (OR/MS, IS, ML, economics, energy, Nature, game theory and games, sports science, German); read only the one the brief names |
| `references/ste.md` | STE mode is on (default for d3-explainer, an option for d3-presentation and d3-poster, on request elsewhere) |
| `references/profiles.md` | Step 1b: the user agreed to measure a wording profile (author, outlet or topic) |
| `scripts/check_wording.py` | Step 4: the lint for `.tex`, `.html`, `.md`, `.txt` and `slides.py` |
| `scripts/wording_profile.py` | Step 1b and 4: `list`, `measure` and `compare` for a corpus of PDFs, `.tex`, `.md` or `.html` |

The table is complete; there is no need to list the folder. Work in few steps: every step re-reads the whole context, so a run with 30 steps costs several times one with 10. Read files that you need anyway in one step, side by side.

## Two ways in

**Standalone.** The user asks to write or revise a text (a paper section, a rebuttal, a paragraph). Run Steps 1 to 5. The review depth follows the words of the other D3 skills (Step 4): `light` for rewrites of up to about a page, STE conversions, slide and poster text; `standard` for abstracts, introductions and theory text; "quick" or "short on tokens" mean light, "thorough" or "submission-ready" mean full.

**Called by another D3 skill.** d3-abstract, d3-poster, d3-presentation and d3-explainer invoke this skill before they write text. The caller has its own question round, so this skill adds no second one: the caller puts the open wording questions of Step 1 into its round (the profile question into its knowledge-enrichment question, where it has one), passes the answers, writes with the rules, runs the lint in its verification step, gives the cold read of Step 4 to its own content reviewer instead of starting another agent, and asks the watermark question of Step 5 in its delivery message. Where the caller's genre conventions govern form (action titles, verb-first poster bullets, Try/Notice captions, emphasis limits), the caller decides the form and this skill decides the wording.

## Step 1: The wording brief

Wording depends on who reads the text and where. Settle six fields before writing, and a seventh when a corpus is at hand. Read as many as possible from the sources and ask only for the rest.

| Field | Values | Where to read it |
|---|---|---|
| Genre | paper, extended abstract, abstract, poster, slides, explainer, rebuttal, proposal, thesis chapter, internal update | the request; the calling skill |
| Outlet | the venue or the occasion: NeurIPS, ICIS, EJOR, a group meeting, a defense | `\documentclass` and style files, the call for papers, `storyline.md`, the abstract's footer |
| Field | OR/MS, IS, ML, economics, energy, game theory and games, sports science, ... | the paper's keywords, the venues in the `.bib`, the code's libraries |
| Reader | experts of the field, adjacent researchers, practitioners, students, co-authors | outlet and genre; `storyline.md` or `brief.md` |
| Language | English (US or UK), German | the babel option, the existing text |
| Mode | standard scientific wording, or Simplified Technical English | the caller's default; the user |
| Profile (optional) | none (default); author, outlet or topic profile | a literature folder, a vault or a NotebookLM notebook that the request names or the caller's scan found |

`references/outlets.md` lists the detection signals and what each value changes (sentence caps, person, hedging, citation form, what the outlet's reviewers look for). Read only what the brief needs: section 1 while the outlet is unknown, the genre row of section 2, and the one family file in `references/outlets/` that section 3 names. Then:

1. State the detected brief in one line: "Wording: paper for EJOR, OR, experts, US English, standard mode."
2. Ask for the fields you could not detect, in one message, with a structured question tool if one is available. Skip what the request already says. Ask the profile question only when a corpus source was found or named; never search the user's home folder for one. In a batch run, take the defaults (unknown outlet: the field's journal norm; reader: experts of the field; US English; standard mode) and record that they are defaults.
3. Record the brief under a `## Wording` heading in the project's notes file (`storyline.md`, `brief.md` or `progress.md`); standalone, in `wording.md` next to the document. The same heading holds the term sheet (Step 3) and the corrections log (see Revising).

## Step 1b (optional): Measure a wording profile

When the user wants a profile, read `references/profiles.md`. In short: `wording_profile.py list` shows what a folder holds; `measure` (with `--match` on a journal name for an outlet profile, or on the user's name for an author profile) writes `wording-profile-<name>.md` and `.json` next to the project's notes file. It reads PDFs, `.tex`, `.md` and `.html`, and stores counts, term lists and short excerpts, never full texts. Read the `.md` once and write its consequences under `## Wording`: the sentence-length target, the person, the outlet's conventional phrases, and the dominant terms for the term sheet. A profile adjusts targets and vocabulary. It never overrides an error-level rule, and its exemplars show structure; their wording is never copied into the user's text. NotebookLM sources are measured after the `notebooklm-import` skill has put them into the vault; without that, three targeted questions give quoted evidence instead of counts.

## Step 2: Write with the rules

Read `references/rules.md` before the first paragraph, in the same step as the input (and `references/ste.md` in STE mode). Rules applied while drafting cost nothing; rules applied in an audit afterwards leave patched sentences. The core, each with its reason:

1. **State the claim directly.** No "not X but Y" and none of its family ("not only X but also Y", "X, not Y", "it is not about X, it is about Y", "more than just X"). The reader processes X only to discard it, and the construction is the most recognizable mark of generated text. If the contrast carries information, give both facts in two sentences.
2. **Report related work neutrally.** For each cited work: what it does, under which assumptions, with which result. Then state the own setting as a fact. The difference between the two sentences is the positioning. It needs no grades: neither dismissal ("fails to", "merely", "overlooks") nor courtesy praise before a dismissal ("seminal", "a valuable first step").
3. **Claim what the evidence carries.** "Show" for what the data show under stated conditions, "suggest" for indirect evidence, "prove" only for a proof. Numbers replace intensifiers: "cuts regret by 31 %", not "dramatically improves". "Significant" only with a test; "novel" and "first" only when the user confirms them, and then name what is new. One hedge per claim. Firm on definitions and derivations, careful on data.
4. **Keep sentences short.** One idea per sentence, one comparison or condition per sentence, the condition first. The lint warns above 35 words in a paper, 30 in an abstract or explainer, 25 on a poster and 20 on a slide; STE caps descriptions at 25 words and instructions at 20. A sentence the reader must parse twice is too long at any length.
5. **Be concise and scientific.** No filler ("it is important to note", "in order to"), no metadiscourse, no nominal style ("perform an analysis of" becomes "analyze"). An ordinary thing takes the common word, a theoretical thing takes the field's term: "use", not "leverage"; "estimator", not "tool".
6. **Sound like the researcher.** No em-dashes or en-dashes as punctuation (ranges keep theirs). No marker vocabulary (delve, pivotal, seamless, comprehensive, transformative, showcase, underscore). No forced groups of three, no rhetorical-question hooks, no "Moreover, ... Furthermore, ..." chains, never three sentences in a row with the same opener. "We" for the group's own work. No emoji, no contractions.
7. **One term per concept.** Pick the term, define it at first use in words the reader already has, and keep it. A synonym makes the reader wonder whether two words mean two things. A definition is written once and repeated verbatim.
8. **Say what does what.** Literal verbs for systems (a model estimates; it does not understand), each action attributed to the component that performs it, a pronoun only where exactly one antecedent fits, and every "therefore" with its premises on the page.

## Step 3: Adapt to outlet and topic

The rules hold everywhere; outlet and topic set the register around them. `references/outlets.md` has the genre profiles and `references/outlets/` one file per outlet family. In short:

- **Genre** sets the form: complete sentences in a paper, action titles and labels on a slide, verb-first bullets on a poster, Try/Notice captions in an explainer, the quoted-comment format in a rebuttal.
- **A measured profile** (Step 1b) replaces the general description of the family file with numbers from real texts, and a topic profile seeds the term sheet.
- **Outlet** sets what the reviewers expect: an enumerated contribution list (ML venues), a contribution to theory and a research model (IS), a formal model with managerial insights (OR/MS), identification before estimates (economics), system boundaries and units (energy), the broad reader and "Here we show" (Nature). It also sets citation form, person, length limits and anonymity: anonymous submissions refer to the group's earlier work in the third person.
- **Topic** sets the vocabulary. Take terms, notation and abbreviations from the user's sources (the paper, its `.bib`, the notation table), never synonyms from an adjacent field and never from memory alone. For documents longer than a page, keep a term sheet under `## Wording` (format in `references/outlets.md`). When the sources use two terms for one thing, ask which one stays.

## Step 4: Check

1. Run the lint on the text sources, not on compiled output:

   ```bash
   uv run <skill-dir>/scripts/check_wording.py <files> [--genre paper|abstract|poster|slides|explainer|rebuttal] [--ste] [--lang en|de]
   uv run <skill-dir>/scripts/check_wording.py revised.md --source draft.md      # a revision: every number and citation kept, none added
   uv run <skill-dir>/scripts/check_wording.py abstract.md --notes notes.md      # drafted from notes: no number or citation that is not in the notes
   ```

   Run it twice: once on the first full draft, once on the final text. With `--source` or `--notes` the same run compares numbers and citations with the original, so no comparison script of your own is needed.

   It strips markup, math and code and reports dashes, contrast framing, related-work grades, overclaiming, stacked hedges, filler, marker vocabulary, sentence length against the genre cap, repeated openers, emoji and invisible characters. With `--ste` it also reports semicolons, contractions, Latin abbreviations, phrasal verbs, passive constructions and paragraphs over six sentences. Without `--genre` it detects the genre from the file. Fix every error. Each warning is a decision: fix it, or keep it for a stated reason (a technical term, a statistical test, a theorem).
2. Read your own output once against what the lint cannot see: does each claim match its evidence (rule 3), is each concept named by one term with its definition verbatim (rule 7), are the premises on the page (rule 8), and when revising, the scope rules below. A violation named in a comment and left in the text is not fixed.
3. **Profile** (when one was measured): `uv run <skill-dir>/scripts/wording_profile.py compare <profile>.json <files>` puts the draft's sentence length, stance and punctuation next to the corpus bands and lists terms where the draft uses a form the corpus does not prefer. Move a metric toward its band from whichever side it is on; below the band on passives, nominalizations, dashes and boosters is fine.
4. **Cold read.** The writer cannot run this test: whoever knows the material fills in missing steps without noticing. So a reader who has only the text lists every sentence whose claim does not follow from what precedes it, and every term used before it is explained. The cold read is a task for a reviewer, never an extra agent:
   - **Called by another D3 skill:** the caller's content reviewer does it at review depth `standard` or `full`, with the instruction below in its prompt. It reads the text before any source, brief or storyline; that order is what keeps the read cold. At `light` nobody does it, and your own pass (item 2) stands.
   - **Standalone:** `light` runs items 1 to 3 and no agent. `standard` starts one read-only agent (`subagent_type=Explore`) that gets only the text and the instruction. `full` repeats the cold read on the revised text until its list holds only choices for the author or polish, never a missing premise; it never rewrites text the user approved.
   - Answer each point in the text, or hand it to the user as a choice.

   > **Cold read.** Before you open any source, brief or storyline, read the text as a reader of <outlet> who has only this text. List every sentence whose claim does not follow from what comes before it, and every term used before it is explained (terms the field uses without definition excepted). Mark these findings [cold read].

## Revising a text the user wrote

- **A style edit changes how something is said, never what.** No new claim, example, hedge or closing sentence; no content dropped to satisfy a rule. If the text seems to need something, say so outside the text and let the author decide.
- **Text the user wrote or approved verbatim is canonical.** Change only what they asked to change. Where a rule of this skill contradicts wording they chose deliberately, flag it instead of changing it.
- **Revise in passes:** structure, then sentences, then words. Say which pass you are on.
- **Corrections are rules for this document.** Log each comment of the user verbatim under `## Wording` → Corrections in the same turn. A fix the user stated applies everywhere the same defect recurs in the document. A pattern you only infer from a comment is a question, not a sweep.
- **After two rejected versions of one sentence, stop producing variants.** Say what the sentence has to do, offer one option, and ask which direction the author wants.
- A correction that recurs across projects belongs in this skill: propose it as a change to `references/rules.md` in the d3-skills repository.

## Step 5 (optional): Remove invisible AI marks

Ask once, in the delivery message, never as a separate round: *"Should I also remove invisible characters and metadata that AI tools can leave in the text (watermarks-remover, deterministic cleaning only)?"* The lint's `invisible` findings show whether there is anything to remove. On a yes:

1. **Find the tool.** It is the third-party plugin [watermarks-remover](https://github.com/guillaumemeyer/watermarks-remover) (MIT). When its skills are listed (`watermarks-remover:clean-user-facing-text`, `watermarks-remover:remove-ai-marks`), use them. When they are not, give the user the install commands and wait; never install a third-party plugin on your own:
   ```
   /plugin marketplace add guillaumemeyer/watermarks-remover
   /plugin install watermarks-remover@watermarks-remover
   ```
2. **Clean the sources, then rebuild.** Run `clean-user-facing-text` (stdlib scripts, no service) on the text sources: the `.tex`, `slides.py`, the explainer's section files, the `.md`. Inspect first (report only), then clean, then rebuild and rerun the lint and the caller's checks. Its `--no-normalize-spaces` option keeps intentional non-breaking and thin spaces.
3. **Only the deterministic layer.** The tool's statistical layer paraphrases the text with a language model (`rewrite_text.py`, and the default of its service's `/clean` endpoint for text). It rewrites the wording this skill set and costs quality. Run it only when the user asks for it by name, and then rerun the lint and the review.
4. **Metadata of delivered files** (C2PA, XMP and document properties of a PDF or DOCX) needs `remove-ai-marks` and its local service. Offer it only when the user wants the delivered file itself cleaned.
5. Report what was removed (character classes and counts) and that the text is otherwise unchanged. Cleaning changes nothing about disclosure: when a venue asks authors to declare AI assistance, the declaration still applies.

## Checklist

- [ ] Wording brief settled and recorded under `## Wording` (genre, outlet, field, reader, language, mode)
- [ ] Profile, if any: measured, its consequences written under `## Wording`, the draft compared; nothing copied from the corpus
- [ ] `references/rules.md` read before writing; `references/ste.md` when STE is on
- [ ] Term sheet kept for documents longer than a page
- [ ] Lint, at most twice: 0 errors, every warning decided; `--source` for a revision, `--notes` for a text drafted from notes
- [ ] Own pass: claims against evidence, one term per concept, premises on the page
- [ ] Revisions: nothing added, nothing dropped, user-approved wording untouched, corrections logged
- [ ] Watermark question asked once at delivery; cleaning only on a yes, on sources, deterministic layer only
