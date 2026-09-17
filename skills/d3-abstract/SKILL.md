---
name: d3-abstract
description: |
  Create D3 (Data Driven Decisions) branded abstracts as A4 PDFs: one page by default, two or more pages for extended abstracts. Use when:
  (1) Creating an abstract, extended abstract, one-pager, fact sheet, or summary sheet with D3 branding
  (2) Preparing an extended abstract or short submission (1, 2, or N pages) for a conference or workshop
  (3) Creating research updates, project overviews, weekly updates, status reports, or info sheets for D3
  (4) Working with two-column A4 LaTeX layouts for the Chair of Information Systems and Business Analytics, University of Würzburg
  (5) Enriching an abstract with vault knowledge (recall) or NotebookLM literature
  MANDATORY TRIGGERS: abstract, extended abstract, D3 abstract, one-pager, one-slider, two-pager, fact sheet, faktaark, handout, summary sheet, info sheet, research update, weekly update, recall one-pager, literature summary, research recall
---

# D3 Abstract

> **`<skill-dir>`** in this skill means the skill's own base directory, which Claude Code shows when the skill loads (installed as a plugin: `${CLAUDE_PLUGIN_ROOT}/skills/d3-abstract`; copied by hand: `~/.claude/skills/d3-abstract`). Substitute the real path in every command.

Create A4 abstracts with D3 (Data Driven Decisions) and University of Würzburg branding. The default is one page. The user can choose two pages or more, for example for an extended abstract submission. The layout is slot-based: a `.tex` file fills a handful of macros, and each call of the page template produces one page with header, lead paragraph, two columns, and footer. Font: Inter. **Requires XeLaTeX. All Python runs through `uv`.**

## Files

```
<skill-dir>/
├── SKILL.md
├── example-update.tex                # 1 page, internal weekly update
├── example-extended-abstract.tex     # 2 pages, submission with references
├── assets/                           # copied into every project
│   ├── d3-abstract.sty               # colors, macros, slots, footer
│   ├── d3-abstract-template.tex      # page layout, one \input per page
│   ├── logos/                        # logo-wue.pdf, logo-d3.pdf (header), seal and extras
│   └── fonts/                        # Inter .ttf files, OFL.txt
├── scripts/
│   └── check_abstract.py             # uv-run checker: pages, fill, wording, emphasis
└── references/
    ├── macros.md                     # macros, cards, tables, charts, colors, fonts
    ├── writing-style.md              # style and wording rules with examples
    ├── content-mapping.md            # input to LaTeX mapping, sections per document type
    ├── questions.md                  # question section guide (internal documents)
    └── troubleshooting.md            # compile errors and fixes
```

Read a reference file when the workflow step that needs it says so.

## Page Count

The page count is a contract between the user and the document. Ask for it in Phase 1, declare it in the preamble, and verify it after every compile.

| Choice | When | Declaration |
|--------|------|-------------|
| **1 page (default)** | Updates, fact sheets, short abstracts | `\renewcommand{\abstractpages}{1}` |
| **2 pages** | Extended abstracts, updates with a results page | `\renewcommand{\abstractpages}{2}` |
| **N pages** | Extended abstracts with a venue page limit | `\renewcommand{\abstractpages}{N}` |

Rules:

1. The `.tex` file contains exactly N calls of `\input{assets/d3-abstract-template}`.
2. The compiled PDF has exactly N pages. More pages mean overflow. Fewer pages mean a missing template call.
3. With N above 1 the footer shows `page / N` automatically.
4. A venue page limit is an upper bound that the user sets. Never exceed it. If the content does not fit, cut content and tell the user what was cut.
5. If no page count is stated and the user gives no answer, use 1 page.

### Page Roles for Two or More Pages

| Page | Role | Lead paragraph | Typical content |
|------|------|----------------|-----------------|
| 1 | Self-contained core | Required | Claim, problem, approach, headline result |
| 2 to N-1 | Continuation | Optional | Method details, extended results, full-width table or figure |
| N | Closing | Optional | Discussion, scope, conclusion, references |

- Page 1 passes the Scan Test on its own. A reader who stops after page 1 knows the claim and the main result.
- Every page sets its own `\undertittel`. Continuation pages name their theme, for example "Experiments and Discussion".
- An empty `\innledning` removes the lead paragraph and frees about 5 line units per column.
- Each section lives on one page in one column. Plan the allocation in the outline (Pass 0).
- Internal documents place the question section at the end of the right column on page 1. Submission abstracts place the references at the end of the right column on page N.
- The last page is at least 60% full. If it falls below that, propose N-1 pages or name the content that would fill it, and let the user decide.

## Document Types

| Type | Purpose | Default pages | Left column starts with | Document closes with |
|------|---------|---------------|-------------------------|----------------------|
| **Research Update** | Paper-driven progress for supervisors and peers | 1 | Problem Formulation | Open Questions |
| **Weekly Update** | Internal status report | 1 | Background | Questions for the Team |
| **Project Overview** | What a project does, for stakeholders | 1 | Background | Questions for the Team |
| **Research Summary** | Methods and results for an external audience | 1 | Background | Questions for the Team |
| **Submission Abstract** | Abstract or extended abstract for a venue | 1, 2, or the page limit | Motivation | Conclusion and References |

Default to **Research Update** for paper-driven internal work, to **Weekly Update** for recurring internal documents, and to **Submission Abstract** when the user names a call for papers, a venue page limit, or an "extended abstract". Section structures per type are in `references/content-mapping.md`.

A Submission Abstract is a finished document: it has no question section, no "Figures Needed" placeholders, and no progress table. If the venue prescribes its own template (LNCS, ACM, IEEE and similar), tell the user that the D3 layout then serves as the circulation version for the group, and ask how to proceed. When the user states that no template is required, take that as given.

## Project Structure

Every abstract gets its own project folder under `writing_outputs/` in the current working directory. The skill's `assets/` directory is copied into it, so each project compiles on its own.

```
writing_outputs/YYYYMMDD_HHMMSS_<description>/
├── progress.md                  # progress log
├── SUMMARY.md                   # final summary and compile guide
├── drafts/
│   ├── assets/                  # cp -r <skill-dir>/assets drafts/assets
│   ├── figures/                 # optional, on the graphics path
│   ├── outline.md               # the approved outline from Pass 0
│   ├── v1_abstract.tex
│   ├── v1_abstract.pdf
│   ├── v2_abstract.tex          # revisions, never overwrite
│   └── revision_notes.md
└── final/
    ├── assets/                  # copy of drafts/assets, so final/ compiles on its own
    ├── YYYYMMDD_short_title.tex # approved version, e.g. 20260312_dfl_theory_direction.tex
    └── YYYYMMDD_short_title.pdf
```

If the user already works in a folder that contains `assets/d3-abstract.sty`, use that folder and skip the copy. Compile from the folder that contains `assets/` (here: `drafts/`).

## Document Skeleton

Every abstract starts from this structure. The example shows a one-page Research Update.

```latex
%! TEX program = xelatex
\documentclass[a4paper]{article}
\usepackage[english]{babel}   % or \usepackage[ngerman]{babel}
\usepackage{parskip}
\usepackage{geometry}
\usepackage{amsmath,amssymb}  % for math-heavy documents

\usepackage{assets/d3-abstract}

% Global title = paper or project name. One header line holds about 40 characters,
% longer titles wrap to two lines. Set the break yourself with \\ to avoid a single-word last line.
\newcommand{\tittel}{Your Paper Title Here}

% Footer. Research updates: target venue and deadline.
\renewcommand{\projektname}{\textbf{Target: VENUE YEAR}\enspace|\enspace\textbf{Deadline: Month Day, Year}}

% Page contract (1 is the default)
\renewcommand{\abstractpages}{1}

\begin{document}
\newgeometry{bottom=0.5cm, right=1.5cm, left=1.5cm, top=1.5cm}
\pagestyle{empty}

% === Page 1 ===
\renewcommand{\undertittel}{Research Update\enspace|\enspace March 6, 2026}

\renewcommand{\innledning}{%
Lead paragraph: main contribution, headline metric, target venue.}

\renewcommand{\venstre}{%
\sectionhead{Problem Formulation}
% Formal setup in the notation of the domain

\sectionhead{Main Results}
% Infoboxes with supporting metrics, then 2 to 4 numbered contributions or theorems

\sectionhead{Benchmark Comparison}
% booktabs table: comparison methods above \midrule, our methods below

\keypoint{One-sentence takeaway.}
}

\renewcommand{\hoyre}{%
\sectionhead{Paper Progress}
% booktabs status table: Section | Status

\sectionhead{Figures Needed}
% card gray placeholders for planned figures

\sectionhead{Open Questions}
\begin{enumerate}
\item Questions for supervisor and peers (see references/questions.md)
\end{enumerate}
}

\input{assets/d3-abstract-template}

\end{document}
```

Load the style as `\usepackage{assets/d3-abstract}` with the `assets/` prefix. The font and logo paths inside the style are relative to the folder that contains `assets/`.

For a Submission Abstract, start from `example-extended-abstract.tex`. For each further page, set the per-page slots again and add one more template call. Slots that stay unset are empty, so a continuation page without lead paragraph simply leaves `\innledning` out:

```latex
% === Page 2 ===
\renewcommand{\undertittel}{Experiments and Discussion}
\renewcommand{\helbredde}{...}        % optional full-width table or figure
\renewcommand{\venstre}{...}
\renewcommand{\hoyre}{...}
\input{assets/d3-abstract-template}
```

## Slot System

| Slot | Purpose | Scope |
|------|---------|-------|
| `\tittel` | Title in the header (define once with `\newcommand`) | Global |
| `\projektname` | Footer text. When set, it replaces the university line | Global |
| `\abstractpages` | Declared page count. Above 1, the footer adds `page / N` | Global |
| `\undertittel` | Subtitle below the title. Empty gives a single-line header | Per page |
| `\innledning` | Full-width lead paragraph. Empty removes the block | Per page |
| `\helbredde` | Optional full-width block between lead paragraph and columns | Per page |
| `\venstre` | Left column | Per page |
| `\hoyre` | Right column | Per page |
| `\bildebredde` | Image width for `\bilde` (default `1.0\linewidth`) | Per page |

Per-page slots reset automatically after each template call.

**Footer.** The default footer reads "Data Driven Decisions Group | University of Würzburg | www.uni-wuerzburg.de". Setting `\projektname` replaces that line completely:

```latex
\renewcommand{\projektname}{\textbf{Target: ICML 2026}\enspace|\enspace\textbf{Deadline: January 31, 2026}}
\renewcommand{\projektname}{AI for Healthcare\enspace|\enspace Weekly Update}
\renewcommand{\projektname}{\textbf{Extended abstract for OR 2026}\enspace|\enspace\textbf{Page limit: 2}}
```

**Lengths.** One title line holds about 40 characters and a title may use two lines. The footer holds about 100 characters on one line. An infobox label holds about 38 characters next to its number.

**Subtitle.** Separate parts with `\enspace|\enspace`, the same separator as in the footer. Dates are exact: "Research Update | March 6, 2026". Submission abstracts put authors and affiliation in the page 1 subtitle.

**Full-width block.** Use `\helbredde` for a wide table or a `\helfigur{file}{caption}`. Its height is lost in both columns, so subtract it from both budgets.

## Workflow Protocol

Every `Print:` line goes to the chat and gets appended to `progress.md`.

### Phase 1: Plan

1. **Analyze the request.**
   - New document or edit of an existing `.tex` file (then follow the Editing Workflow)
   - Document type, audience, purpose
   - Page count or page limit, if the request already states one
   - Print: `[HH:MM:SS] PLANNING: [type], [N] page(s), for [audience]`

2. **Ask the clarification questions (MANDATORY).** Ask only what the request leaves open: a question whose answer the request already contains is skipped, and the answer taken from the request is stated back to the user in one line. Use a structured question tool if one is available.
   1. **Page count:** *"How long should the abstract be: one page (default), two pages, or more? For an extended abstract, what is the page limit of the call?"* Skip this question when the request states the length. "One-pager" means 1. "Extended abstract" without a number means: ask for the limit.
   2. **Document type:** Research Update, Weekly Update, Project Overview, Research Summary, or Submission Abstract. Skip when the defaults under Document Types decide it, and name the chosen type.
   3. **Title:** *"Is '[inferred title]' the correct title?"* Skip when the user gives the title verbatim.
   4. **Emphasis:** *"What should the document emphasize most: the results, the problem formulation, a new direction, or specific figures?"*
   5. **Missing content:** *"Is there anything outside your notes that belongs in the document, such as new results, a decision, or a blocker?"* For research documents add: *"Can you give me the formal setup and notation, or point me to the section of the draft that has it?"*
   6. **Figures:** *"Which figures exist already, and which are planned?"* Internal documents may use placeholders. Submission abstracts need the final figures.
   7. **Submission Abstract only:** authors and affiliations, venue and deadline, whether references count toward the page limit, whether the venue requires its own template, and the comparison conditions of the experiments (same data, same features, same tuning budget). The deadline goes into `progress.md` and `SUMMARY.md`. The document itself carries venue and page limit in the footer.

3. **Knowledge enrichment (optional).**

   Offer it when the request is high-level, lacks metrics or results, is research-oriented, or mentions "literature", "recall", or "past work". Skip it when the user provides a detailed brief, declines, or edits an existing file.

   ```
   Would you like me to pull in context from your vault or notebooks before drafting?

   1. Recall vault: search past sessions and notes for [topic]
   2. Ask NotebookLM: query your notebook for literature insights
   3. Both: vault context plus literature
   4. Skip: proceed with what you have provided

   For 1 to 3: which topic or question should I search for?
   ```

   **Recall path.** Invoke the `recall` skill with the topic through the Skill tool. Extract previous decisions, metrics, open threads, and the "One Thing" synthesis.

   **NotebookLM path.**
   1. Check authentication: `notebooklm status`
   2. Ask which notebook to use, or use the current one
   3. Formulate one targeted question from the document's purpose and confirm it with the user
   4. Run: `notebooklm ask --new --json "{question}" > "${TMPDIR:-/tmp}/d3-abstract-notebooklm.json"`
   5. Read the `answer` text and `references[].cited_text` from the JSON
   6. Stop there. The citation resolution pipeline of the NotebookLM skill is for vault notes and adds nothing here

   **Combined path.** Recall first (what we have done), then NotebookLM (what the literature says).

   **Knowledge brief.** Summarize the results in the conversation and ask before using them:

   ```
   From your vault and notebooks, I found:
   - [3 to 5 bullet points of relevant knowledge]
   - Previous status: [last decisions and progress]
   - Literature context: [findings from NotebookLM, with sources]
   - Gaps: [what you still need to provide]

   Should I incorporate this into the abstract?
   ```

   **Fallbacks.** QMD missing: offer NotebookLM or skip. NotebookLM authentication expired: suggest `notebooklm login` or skip. No results: offer different keywords or skip.

   Print: `[HH:MM:SS] ENRICHMENT: [skipped | recall | notebooklm | both]`

4. **Create the project folder** (see Project Structure) with `drafts/` and `final/`, and copy `assets/` into `drafts/`.
   Print: `[HH:MM:SS] CREATED: Project folder structure`

5. **Initialize `progress.md`:**

   ```markdown
   # Progress Log: [Title]

   **Started:** YYYY-MM-DD HH:MM:SS
   **Status:** In progress
   **Type:** [document type]
   **Pages:** [N] (chosen by user | default)

   ## Timeline

   ### [HH:MM:SS] Phase 1: Plan
   - [x] Clarification questions answered
   - [ ] Knowledge enrichment (skipped | recall | notebooklm | both)
   - [x] Project folder created, assets copied

   ### [HH:MM:SS] Phase 2: Build
   - [ ] Pass 0: content outline approved
   - [ ] Pass 1: skeleton compiles to [N] page(s)
   - [ ] Pass 2: all pages filled

   ### [HH:MM:SS] Phase 3: Validate
   - [ ] Checker passes (0 errors)
   - [ ] Visual validation passed
   - [ ] Dual review passed (both scores at least 9/10)

   ### [HH:MM:SS] Phase 4: Deliver
   - [ ] SUMMARY.md created
   - [ ] Final PDF delivered

   ## Files Created

   ## Notes
   ```

   Update it at each milestone with a timestamp.

### Phase 2: Multi-Pass Build

Build in three passes and complete each one.

#### Pass 0: Content Outline (MANDATORY)

Read `references/content-mapping.md` first: it holds the section structure for each document type and the allocation across pages. Internal documents also need `references/questions.md`. Then open the example that matches the type (`example-update.tex` or `example-extended-abstract.tex`).

1. Define the core message: audience, purpose, and the one sentence the reader should remember.
2. If a knowledge brief exists, map it: previous decisions, progress, and metrics go to the left column sections, literature findings go to supporting evidence, open threads go to the question section, and gaps go back to the user.
3. Draft a bullet outline, one block per page:

   ```
   Title: [paper or project name]
   Pages: [N]
   Page 1
     Subtitle: [...]
     Lead: [claim + headline metric + target]
     Left:  [section: content] ... (budget: NN units)
     Right: [section: content] ... (budget: NN units)
   Page 2 (continuation)
     Subtitle: [...]
     Full width: [table or figure, if any]
     Left:  ...
     Right: ...
   ```

4. Budget every column (see Line Budget) before presenting the outline. Internal documents: include the drafted questions in the outline, with a mark on every question that you derived yourself.
5. Run the **Scan Test**: title, lead paragraph, and section heads of page 1 convey the full message without the body text. If they do not, rewrite the lead or rename sections.
6. Present the outline and ask: *"Does this outline capture your message? Any sections to add, remove, or reorder?"*
7. Save the approved outline as `drafts/outline.md`.
8. Print: `[HH:MM:SS] OUTLINE: Approved by user`

Write LaTeX only after the user has approved the outline.

#### Pass 1: Skeleton

1. Create `drafts/v1_abstract.tex` from the Document Skeleton (Submission Abstracts: from `example-extended-abstract.tex`) with `\abstractpages` set to N and N template calls.
2. Add every `\sectionhead{}` from the approved outline, each with a `% TODO: [description]` placeholder.
3. Compile. The PDF must have exactly N pages.
4. Print: `[HH:MM:SS] SKELETON: [N] pages, [M] sections, compiles clean`

#### Pass 2: Fill and Compile

Read `references/writing-style.md` and `references/macros.md` before filling. On compile errors, read `references/troubleshooting.md`.

Work page by page:

1. Fill the left column section by section, then compile and confirm the page count is still N.
2. Internal documents, page 1: confirm the question section with the user before filling the right column (see Decision Making).
3. Fill the right column section by section, then compile and confirm the page count is still N.
4. After the last page: replace every `% TODO:` placeholder with content and compile once more. `% TODO verify` markers on unverified reference fields stay until the user has confirmed the data.
5. Print: `[HH:MM:SS] FILLED: All sections complete, [N] pages`

### Phase 3: Validate

1. **Compile** from the folder that contains `assets/`:

   ```bash
   xelatex -interaction=nonstopmode v1_abstract.tex
   ```

   One pass is enough. There are no cross-references and no bibliography run. Two log warnings are expected and harmless: the package name notice for `assets/d3-abstract` and a hyperref rerun notice on the first compile.

2. **Run the checker** and render the page images:

   ```bash
   uv run <skill-dir>/scripts/check_abstract.py v1_abstract.tex --render review
   ```

   Add `--submission` for a Submission Abstract.

   | Section | What it verifies |
   |---------|------------------|
   | PAGES | `\abstractpages`, number of template calls, and PDF page count agree |
   | COLUMN FILL | Fill per column, column balance, fill of the last page |
   | WORDING | Dashes, contrast constructions, tone toward related work, stock phrases |
   | EMPHASIS | `\highlight`, infobox, and `card alert` counts per page, `\keypoint` per column, a number emphasized in two places, lead paragraph length |
   | COLORS | Only named D3 colors, no `\definecolor`, no color values |
   | SUBMISSION ABSTRACT (with `--submission`) | No placeholders, no internal sections, reference list present |
   | TODO MARKERS | Leftover `% TODO:` placeholders and `% TODO verify` items |
   | LOG | Every TeX error, overfull boxes |

   Fix every error (`E`). Read every warning (`W`) and either fix it or confirm that it is legitimate, for example an established technical term. Rerun until the result is `PASS`. The fill value measures the lowest element of each column. Gaps inside a column show only in the page image.

3. **Inspect every page image** in `review/` with the Read tool:
   - Page count equals N, and the footer shows `page / N` for N above 1
   - Header: both logos, title, subtitle if set, navy rule
   - Lead paragraph: full width, at most 3 lines
   - Body: two top-aligned columns with a 20pt gap, nothing below the footer rule
   - Tables and TikZ boxes stay inside their column
   - Colors: d3-navy for headings and rules, d3-orange for highlights only
   - Font: Inter for all text and for numbers in tables. Formulas use the default math font
   - Title and subtitle break at sensible places, with no single-word last line

4. **If the PDF has more than N pages**, find and fix the overflow:
   1. Compile with only `\venstre` filled for the affected page, then add `\hoyre`, to find the overfull column
   2. Cut the lowest-priority section of that column
   3. If it still overflows: shorten lists to 4 items, remove table rows, compress prose
   4. If a `\keypoint{}` causes the overflow, shorten it or move it up
   5. Font sizes stay fixed. Cut content
   6. Recompile and rerun the checker

5. **Dual review** (see below). Both scores must reach 9/10.

6. **Clean up** after the dual review has passed: `rm -rf review/`

7. Print: `[HH:MM:SS] VALIDATED: [N] pages, checker PASS, content [X]/10, visual [Y]/10`

### Dual Review

Dispatch two review subagents in parallel through the Agent or Task tool. Give each one the paths of the page images, the path of the `.tex` file, and its rubric. Each returns a score from 0 to 10 and a list of concrete fixes. Without a subagent tool, run the two reviews yourself one after the other, each with its own rubric only.

Scoring: 10 means no findings. 9 means cosmetic findings only. Every violated rubric item costs at least 2 points, so a review with one violated item scores 8 or lower. Record both scores and both fix lists in `progress.md` for every round.

**Reviewer 1: Content**
- Lead paragraph states a claim with a number
- Scan Test passes for page 1
- Most important information comes first in each column
- One message per section, parallel lists, active voice
- Notation fits the research domain
- Wording rules hold: dashes, contrast constructions, neutral tone toward related work
- Every number and every reference is traceable to the user's material, and every added statement is on the list for the user (see Content Integrity)
- Multi-page documents: page 1 is self-contained, and every later page adds information

**Reviewer 2: Visual Design**
- Page count equals the declared count, and the last page is at least 60% full
- Columns balanced and top-aligned, no overflow below the footer rule
- Header and footer complete and correct
- Only D3 colors, Inter for all text and table numbers
- Infoboxes, cards, placeholders, and tables fit their column
- Whitespace: no large gaps and no cramped sections

**Iteration loop:** if either score is below 9, implement the listed fixes in the current version, recompile, rerun the checker with `--render review`, and send both reviewers the new images. Repeat until both scores are at least 9.

### Phase 4: Deliver

1. Show the validated PDF to the user with a short summary (pages, checker result, review scores) and the list of added statements (see Content Integrity). Then ask:
   - **Completeness:** *"Is anything missing that you would like added?"*
   - **Accuracy:** *"Are all numbers and claims accurate, or does anything need correction?"*
   - **Approval:** *"Do you approve this version as final?"*

   Corrections lead to a new version (see Version Management) and a new validation.
2. After approval, copy the version to `final/` as `YYYYMMDD_short_title.tex` and `.pdf`, together with a copy of `assets/`. Compile once in `final/` to confirm that it builds there, then delete `.aux`, `.log`, and `.out` files in `drafts/` and `final/`.
3. Create `SUMMARY.md`:

   ````markdown
   # Abstract: [Title]

   ## Files
   - **Final PDF:** `final/YYYYMMDD_short_title.pdf`
   - **Final TeX:** `final/YYYYMMDD_short_title.tex`
   - **Assets:** `final/assets/`

   ## Compilation
   ```bash
   cd final/ && xelatex -interaction=nonstopmode YYYYMMDD_short_title.tex
   ```

   ## Document Details
   - **Type:** [document type]
   - **Pages:** [N] (page limit: [limit or none], deadline: [date or none])
   - **Audience:** [target audience]
   - **Content score:** [X]/10
   - **Visual score:** [Y]/10

   ## Notes
   - [Open items, unverified references, added statements, content that was cut to fit]
   ````

4. Update `progress.md` with completion status and final timestamps.
5. Print the final summary with the paths of the final files.

## Line Budget and Overflow Prevention

Extra pages are the most common failure. The article class moves overflowing content to a new page, which breaks the page contract. Budget before writing.

A column physically holds about 55 lines at `\small`. Budget **45 line units per column** on pages with a lead paragraph and **50** on continuation pages without one. The margin absorbs wrapped lines. A full-width block reduces both column budgets by its own height. Infoboxes, cards, and callouts span the full column width and stack vertically.

| Element | Line units |
|---------|-----------|
| `\sectionhead{}` | 3 (includes spacing) |
| Paragraph (3 sentences) | 5 |
| Bullet list (5 items) | 7 |
| `\keypoint{}` | 5 |
| `\figur{}{}` | 10 |
| `infobox` | 4 |
| `card gray` placeholder (2.0cm) | 6 |
| `card alert` | 4 |
| `booktabs` table (5 rows) | 8 |
| Display equation | 3 |
| Question list (4 questions) | 12 |
| `reflist` entry | 3 |

The budget is a planning estimate, and the checker's COLUMN FILL line is the measurement. After the first full compile, add content from the outline or cut content until every column of a full page is between 75% and 95%. Full pages are all pages except the last page of a multi-page document, which needs at least 60%. Above 95%, one more wrapped line can push content to a new page.

Rules:

1. Total every column in the outline before writing LaTeX
2. Compile after each column to catch overflow early
3. When content does not fit, cut content. Font sizes stay fixed
4. Lead paragraph: at most 3 sentences and 50 words
5. Lists: at most 5 to 6 items
6. Tables: at most 6 rows at `\small` in a column. Wide tables go into `\helbredde`
7. At most one `\keypoint{}` per column
8. Balance the columns. If one holds 40 units and the other 25, redistribute
9. When required content does not fit into N pages, the choice between cutting and adding a page belongs to the user. A venue page limit always wins

## Emphasis

| Element | Limit | Carries |
|---------|-------|---------|
| `\highlight{}` | 3 per page, tables included | The headline number, once, in the lead paragraph |
| `infobox` | 3 per page | Supporting numbers that differ from the highlighted headline number |
| `\keypoint{}` | 1 per column | The takeaway sentence. It may restate the headline number |
| `card alert` | 2 per page | A blocker, risk, or a deadline that the footer does not already show |
| Table highlight | Best value per column, summary column only in wide tables | Exempt from the one-place rule below |

**One place per number:** outside tables, a number is emphasized either by `\highlight{}` or by an infobox. The headline number belongs to the lead paragraph, so the infoboxes show other numbers.

## Wording Rules

These rules apply to every sentence in the document, including captions, table notes, and questions. The checker reports clear violations as errors and patterns with legitimate uses as warnings. Both need a decision. `references/writing-style.md` has the full guide with examples.

1. **Dashes only in number ranges.** Write ranges as `2024--2026` or `9--26`. Sentences use commas, colons, parentheses, or a full stop. Titles, subtitles, and footers separate parts with `\enspace|\enspace`. Bold run-in labels end with a period: `\textbf{Sepsis model v2.} Retrained on ...`
2. **State the claim directly.** Write what the method is and does. Constructions of the "not X but Y" family (also "not only X", "X, not Y", "rather than X") get replaced by the positive statement. If a contrast carries information, give both facts in separate sentences.

   | Before | After |
   |--------|-------|
   | "Our method is not a heuristic but an exact algorithm." | "Our method is an exact algorithm." |
   | "We optimize decisions rather than predictions." | "We train the forecast on the dispatch cost." |

3. **Report related work neutrally.** For each cited work, state what it does, under which assumptions, and with which result. Then state your setting as a fact. No grades in either direction: neither dismissal ("fails to", "suffers from", "merely", "overlooks") nor courtesy praise ("seminal", "a valuable first step", "significant strides").

   | Before | After |
   |--------|-------|
   | "While prior work has made significant strides, existing methods fail to handle state constraints." | "SPO+ [1] covers linear objectives. Storage scheduling adds inter-temporal state constraints." |
   | "Unlike previous approaches, we ..." | "Method A [2] assumes i.i.d. prices. We study autocorrelated prices." |

4. **Plain vocabulary.** "Use" for "leverage", "utilize", "harness". "To" for "in order to". "Main" or "central" for "key". Delete "it is worth noting", "comprehensive", "crucial", "pivotal", "seamless". State findings directly in place of "delve into", "shed light on", "pave the way".

## Content Integrity

1. **Numbers come from the user's material.** Derived numbers (differences, percentages, days until a deadline) are allowed when the arithmetic is shown to the user.
2. **References are verifiable.** Cite only sources that come from the user, from the project's `.bib` file, or from the enrichment step with full bibliographic data. Copy the data as given, including abbreviated author lists. Mark any incomplete or unverified field with `% TODO verify`. Never write a reference from memory alone.
3. **Methods without source data stay uncited.** Name a comparison method by its published name. Cite it when bibliographic data is available, and otherwise ask the user for the source.
4. **Descriptions of cited work come from the user's material or the enrichment step.** When the user supplies only the bare citation, keep the description at the level of the title.
5. **Interpretations follow from the numbers.** Check every interpretive sentence ("X explains most of the difference") against the supplied numbers before writing it.
6. **Keep a list of added statements**: notation you reconstructed, mechanism descriptions, derived numbers, interpretations, and `% TODO verify` items. Show this list with the accuracy question in Phase 4 and record it in `SUMMARY.md`.

## Editing Workflow

1. **Detect editing mode:** the user provides an existing `.tex` file or asks to modify a document.
   Print: `[HH:MM:SS] EDITING MODE: Found existing abstract [filename]`
2. **Read the existing file**: structure, content, style, declared page count.
3. **Create a new version**, never overwrite: `cp v1_abstract.tex v2_abstract.tex`
   Print: `[HH:MM:SS] VERSION: Creating v2_abstract.tex from v1`
4. **Apply the edits to the new version only.**
5. **A changed page count** updates three places together: `\abstractpages`, the number of template calls, and the page roles. Going from 1 to 2 pages: move detail sections to page 2 and keep page 1 self-contained. Going from 2 to 1: keep the claim, the headline result, and one table or figure, and tell the user what was cut.
6. **Document the changes** in `revision_notes.md`:

   ```markdown
   ## Version 2 Changes (YYYY-MM-DD HH:MM:SS)
   - Updated headline numbers on page 1
   - Added page 2 with experiment details (page count 1 to 2)
   - Fixed table alignment in the right column
   ```

7. **Compile and validate** the new version (Phase 3).

Files that load `assets/d3-oneslider` were made with the former one-slider version of this skill. They still compile with their own `assets/` copy. To migrate one, copy the new `assets/`, change the `\usepackage` line and the template `\input` to the `d3-abstract` names, and compile.

### Version Management

- Initial draft: `v1_abstract.tex`. Revisions: `v2_abstract.tex`, `v3_abstract.tex`, and so on
- A new version starts whenever the user has seen the current one and asks for changes. Fixes during build, validation, and dual review happen in the current version
- Never overwrite a version the user has seen, and never skip a number
- Copy to `final/` only after user approval, named `YYYYMMDD_short_title.{tex,pdf}`

## Python and uv

All Python in this skill runs through `uv`. Never call `pip install` or a bare `python3`.

- Skill scripts carry inline metadata (PEP 723): `uv run <skill-dir>/scripts/check_abstract.py ...`
- One-off snippets: `uv run --with <package> python -c "..."`
- Figure scripts: `uv run --with matplotlib python make_figure.py`, saved as PDF into `drafts/figures/` (see `references/macros.md` for the D3 colors in matplotlib)

## Decision Making

### Ask the user
- Page count when the request leaves it open, and any change of the page count later
- Document type and content framing
- Audience or purpose when unclear
- What to cut when required content does not fit
- Major structural changes during editing

### Confirm generated questions (MANDATORY, internal documents)

Before writing "Open Questions" or "Questions for the Team" into the `.tex` file, present the draft:

*"I have drafted these questions for the [Open Questions / Questions for the Team] section. Do they capture what you want to ask, or should I change any?"*

List 2 to 5 questions and write them into LaTeX after the user approves or edits them. They drive real conversations with supervisors and peers, so they must reflect the user's actual uncertainties. Questions taken from the user's notes come first. Mark every question that you derived yourself, so the user can delete it.

### Decide independently
- Layout pattern and section order within the document type
- Which macros to use (`\keypoint`, `\highlight`, `infobox`, cards)
- Column content distribution and spacing adjustments
- Table formats and figure sizes within the font hierarchy

## Quality Checklist

**Files and structure**
- [ ] `assets/` present in the compilation directory
- [ ] PDF compiles without errors using XeLaTeX
- [ ] Files in the correct folders (`drafts/`, `final/` with its own `assets/`), `outline.md` saved, `progress.md` current, `SUMMARY.md` created
- [ ] Editing: version incremented, previous versions preserved, `revision_notes.md` updated

**Page contract**
- [ ] Page count chosen by the user or defaulted to 1
- [ ] `\abstractpages`, template calls, and PDF pages agree
- [ ] Multi-page: page 1 self-contained, every page has a subtitle, last page at least 60% full
- [ ] Venue page limit respected

**Content**
- [ ] Outline approved before any LaTeX was written
- [ ] Lead paragraph states a claim, at most 50 words
- [ ] Scan Test passes
- [ ] One message per section, parallel lists
- [ ] Emphasis within limits, one place per number
- [ ] Added statements listed for the user (Content Integrity)
- [ ] Internal documents: question section approved by the user
- [ ] Submission abstracts: no placeholders, no question section, references verified

**Wording**
- [ ] Checker reports 0 errors, and every warning was read
- [ ] No dashes outside number ranges
- [ ] No "not X but Y" constructions
- [ ] Related work reported neutrally

**Visual**
- [ ] Every page image inspected
- [ ] Columns balanced and top-aligned, fill between 75% and 95% on full pages
- [ ] Header, footer, fonts, and colors correct (formulas use the default math font)
- [ ] Dual review passed with both scores at least 9/10

## Quick Reference

1. **Ask the page count**: 1 page by default, 2 or N on request. Declare it with `\abstractpages`
2. **One template call per page**, and the PDF page count equals the declared count
3. **XeLaTeX** compiles the document. **uv** runs all Python
4. **`\usepackage{assets/d3-abstract}`** with the path prefix, in a dedicated project folder with its own `assets/` copy
5. **Outline first**: read `content-mapping.md`, draft, budget, Scan Test, user approval (Pass 0), then skeleton (Pass 1), then fill (Pass 2)
6. **Budget 45 line units per column** (50 without lead paragraph), compile after each column, and tune to 75% to 95% measured fill
7. **Overflow means cutting content.** Font sizes stay fixed
8. **Lead paragraph = claim** with a number, at most 50 words
9. **Page 1 is self-contained** in multi-page documents
10. **Emphasis limits**: 3 `\highlight{}` and 3 infoboxes per page, 1 `\keypoint{}` per column, headline number in the lead, other numbers in infoboxes
11. **Wording**: dashes only in number ranges, direct claims, neutral related work, plain vocabulary
12. **Content integrity**: numbers and references from the user's material, added statements listed for the user
13. **Only D3 colors**: no new `\definecolor`, no hex codes
14. **Run the checker** after every full compile (`--submission` for submissions), then inspect every page image
15. **Dual review**: content and visual reviewers, both at least 9/10
16. **Versions**: v1, v2, v3, never overwrite
17. **Examples**: `example-update.tex` (1 page) and `example-extended-abstract.tex` (2 pages)
