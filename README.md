# D3 Skills

Claude Code skills of the Data Driven Decisions (D3) group for research communication in the D3 corporate design, teaching apps, and running jobs on the group's compute server.

> Chair of Information Systems and Business Analytics, University of Würzburg.

## Installation

In Claude Code 2.1.275 or later, one line installs a skill together with the marketplace:

```
/plugin install d3-abstract --marketplace d3group/d3-skills
/plugin install d3-poster --marketplace d3group/d3-skills
/plugin install d3-presentation --marketplace d3group/d3-skills
/plugin install d3-explainer --marketplace d3group/d3-skills
/plugin install d3-scientific-wording --marketplace d3group/d3-skills
/plugin install d3-marimo --marketplace d3group/d3-skills
/plugin install d3-server-use --marketplace d3group/d3-skills
```

In older versions, or to browse the skills first:

1. Add the marketplace (run in Claude Code):
   ```
   /plugin marketplace add d3group/d3-skills
   ```
2. Run `/plugin` in Claude Code
3. Go to **Discover** tab, find the skill
4. Select **Install for you (user scope)**, or install it by name: `/plugin install d3-explainer@d3-skills`
5. Restart Claude Code

Skills are then invoked as `/d3-explainer:d3-explainer`, or simply by asking. Update later with `/plugin marketplace update d3-skills`.

New versions are announced in #d3_skills on the D3 Slack: when a plugin's version in `.claude-plugin/marketplace.json`
changes on `main`, `.github/workflows/slack-plugin-updates.yml` posts it there (secret `SLACK_WEBHOOK_URL`).

## Available Skills

| Skill | Version | Description | Resources |
|-------|---------|-------------|-----------|
| [d3-abstract](#abstracts-and-one-pagers-on-a4-d3-abstract) | 1.3.1 | Abstracts, extended abstracts, one-pagers and research updates as A4 PDFs | LaTeX template, checker for page count, column fill, emphasis, colours and the TeX log |
| [d3-poster](#conference-posters-from-a-paper-d3-poster) | 1.3.1 | A0 conference posters from a paper, a paper submodule synced to Overleaf or a repo of results | baposter class, TikZ recipes, two-agent review |
| [d3-presentation](#talks-as-beamer-pdfs-or-html-decks-d3-presentation) | 1.8.4 | Presentations as LaTeX Beamer PDFs or interactive HTML decks (also in the University of Würzburg design for teaching, `look='uni'`; exportable to an editable PowerPoint on the university master) where every slide centres on a designed object: model figures that build, bars, gauges, replayed stimuli, live instruments; presenter window with pace, overview and Q&A interactions | Beamer theme, HTML deck engine and component kit, layout and signature lint |
| [d3-explainer](#explaining-a-project-to-its-own-authors-d3-explainer) | 0.12.1 | Interactive HTML explainer of a research repo (code, paper, vault) for its own authors and co-authors: concepts, derivations, research gap, paper-to-code map, open points | Build and check engine, worked example |
| [d3-scientific-wording](#wording-of-research-texts-d3-scientific-wording) | 0.1.1 | The wording layer of all D3 skills, also for papers, rebuttals and proposals: direct claims, neutral related work, claims within the evidence, short sentences, wording adapted to outlet and field, optional Simplified Technical English (ASD-STE100), optional removal of invisible AI marks | Rules with examples, outlet guides, STE guide, wording lint, corpus profiler |
| [d3-marimo](#teaching-apps-in-the-browser-d3-marimo) | 0.1.2 | Teaching apps as marimo notebooks that run in the browser (WASM) on the chair website: port Colab, Jupyter or molab notebooks, SciPy HiGHS instead of PuLP, university look, deploy and check | App template, look stylesheet and style-cell generator, headless browser check, pitfalls |
| [d3-server-use](#running-jobs-on-the-group-server-d3-server-use) | 0.9.2 | Compute jobs on the group's KiRegio Slurm server: first login and ssh, uv only, a quick submit for projects that are set up, run IDs and a registry that tie code, config, logs, checkpoints and results together, rounds split at their phases and units with each job as wide as it keeps busy and fitted to the queue, jobs that checkpoint and resume within the 24 h limit, a local smoke test and sizing for a new setup, a server smoke only the first time and never one that spends a GPU turn while the queue is full, fair use of the GPUs, the S3 bucket (or the user's own computer) as the store with verified cleanup, inputs and results through the bucket or, until there is one, by rsync, help with the admin's monitoring alerts, experiment tracking with MLflow or W&B where a project uses or wants it | Registry and S3 transfer CLI, job-side checkpoint and tracking helper, MLflow sync, job template, laptop input script, sbatch lint |

Each skill has a section below: what its folder contains, how a run goes from the first question to the delivery, and
what it checks. The folders are under [`skills/`](skills/). Design and review depth apply to several skills and come
first.

## Design

All D3 outputs follow the 2026 corporate design of the University of Würzburg with D3 co-branding: the new round university logo top left, the D3 logo in the co-branding slot (top right, or next to the university logo on title pages), the university navy `#02246C`, D3 orange `#F29100` as the only accent, the house font Inclusive Sans UW (SIL OFL), and the seal on title and divider pages. Slides follow the university PowerPoint master, posters the university poster template, one-pagers the letterhead. On posters the seal sits top right in the header, and the D3 logo opens the logo row in the footer. The explainer uses the D3 colours and the house font without logos. The university's coral is not used next to D3 orange. Inclusive Sans UW has no Greek letters or math operators. d3-presentation and d3-explainer embed a small fallback font for them (D3 Symbols, an Inter subset), the LaTeX skills set them in math mode, and d3-marimo apps fall back to the system font. The CD will replace the seal by a faculty ornament in faculty communication; until that package is released the seal stands in. For teaching decks without D3 branding, d3-presentation offers `look='uni'`; d3-marimo uses the university look throughout (coral and berry as accents, no D3 logo).

## Review depth: how many tokens a run spends

The four document skills (d3-abstract, d3-poster, d3-presentation, d3-explainer) check their output automatically
(compile log, overflow and layout audits, source-pointer validation) and can then have reviewer agents look at it. The
reviewers are where the tokens go, so the depth is your choice. Say it in your request ("light review", "I'm short on
tokens", "full review"); otherwise the default runs.

| Depth | What runs | Use when |
|---|---|---|
| `light` | Automated checks plus Claude's own pass over the review rubric. No reviewer agents. | You are short on tokens, or the document is a quick internal draft |
| `standard` (default) | Reviewer agents, one round, fixes applied. d3-abstract and d3-poster: two reviewers (content, visual). d3-presentation: one reviewer. d3-explainer: two reviewers (one merged reviewer with `single`) | Normal use |
| `full` | Reviewers loop until every score is 9 of 10. d3-presentation runs two reviewers (content, visual) here. d3-abstract and d3-poster stop after four rounds, d3-explainer after three; d3-presentation repeats until the scores are reached | Submission-ready output |

A reviewer costs roughly 50k tokens regardless of document size, so `standard` adds about 50 to 150k tokens and `full` a
multiple of that; `light` adds almost nothing. d3-explainer recommends a depth that follows the size of the explainer:
`light` for `focus`, `single` for `overview`, `standard` for `standard` and `deep`.

`d3-scientific-wording` adds no reviewer agent when another skill calls it: its cold read is a task of that skill's
content reviewer. Used on its own, `light` runs the lint and its own pass, `standard` one read-only agent for the cold
read, and `full` repeats the cold read on the revised text until it finds no missing premise.

`d3-server-use` and `d3-marimo` run no reviewer agents and have no review depth. Their checks are deterministic and cost
no extra tokens. In d3-server-use these are the refusals and verification in `d3run.py`, the stop logic in `d3job.py`
and the `check_sbatch.py` lint. In d3-marimo it is `check_app.py`, which runs the app natively, exports it to WASM and
opens it in a headless browser.

## Abstracts and one-pagers on A4 (d3-abstract)

`d3-abstract` writes abstracts, extended abstracts, one-pagers and internal updates as A4 PDFs, set in LaTeX with
XeLaTeX. The default is one page. Two or more pages are for extended abstracts and for updates with a results page; a
venue page limit is the upper bound. Five document types share one layout: Research Update, Weekly Update, Project
Overview, Research Summary and Submission Abstract. A `.tex` file fills a few slot macros, and each call of the page
template produces one page. Four rules hold throughout. The page count is declared and verified after every compile.
The outline is approved before any LaTeX is written. Content that does not fit is cut, and font sizes stay fixed. Every
number and reference comes from the user's material. Each abstract gets its own project folder with a copy of
`assets/`, so it compiles on its own.

<details>
<summary><b>In detail:</b> What the skill contains · From your material to the PDF · The question round · An abstract, step by step · The page · One page or N pages · What goes where · How much fits · What is checked, and how</summary>

### What the skill contains

```
skills/d3-abstract/
├── SKILL.md                         page count · document types · slots · plan, build, validate, deliver
├── example-update.tex               1 page, internal weekly update
├── example-extended-abstract.tex    2 pages, submission abstract with references
├── assets/                          copied into every project folder
│   ├── d3-abstract.sty              palette, fonts, header, footer, slots, highlight macros, card styles
│   ├── d3-abstract-template.tex     one page: header · lead · full-width block · two columns · footer
│   ├── logos/                       uw-logo-navy.pdf (left), logo-d3.pdf (right), DataDrivenDecisions.png
│   └── fonts/                       Inclusive Sans UW in five faces (.ttf) and its licence (SIL OFL 1.1)
├── scripts/
│   └── check_abstract.py            checker: pages, column fill, wording, emphasis, colors, TODOs, TeX log
└── references/                      content mapping · macros · writing style
                                     question section · troubleshooting
```

### From your material to the PDF

```
  your material                                 offered in the question round (optional)
 ┌───────────────────────────────┐             ┌─────────────────────────────────────────────────────────┐
 │ topic, notes, results, data   │             │ recall skill: past sessions and notes                   │
 │ paper draft, the project .bib │             │ NotebookLM: one confirmed question, answer + cited text │
 │ venue, page limit, deadline   │             │ wording profile: your papers, the venue, the topic      │
 │ an existing .tex (edit mode)  │             └────────────────────────────┬────────────────────────────┘
 └───────────────┬───────────────┘                                          │ knowledge brief, used after a yes
                 └────────────────────────────┬─────────────────────────────┘
                                              ▼
           outline.md ─▶ v1_abstract.tex (slots, one template call per page) ─▶ xelatex ─▶ checks · review
                                              ▼
           final/YYYYMMDD_short_title.pdf · .tex · assets/      the approved version, A4, 1 or N pages
```

### The question round: taken from the request, or asked

There is no setup step. The skill needs XeLaTeX and uv (see [Requirements](#requirements)); the optional enrichment uses the `recall`
skill and the `notebooklm` CLI when they are installed. Each abstract starts with a question round that asks only what
the request leaves open. An answer found in the request is stated back in one line.

```
 does the request answer it? ──yes──▶ take it, state it back in one line
            │ no
            ▼
 pages       one page (default), two, or more? · "one-pager" = 1 · "extended abstract" alone ─▶ ask the limit
             no answer ─▶ 1 page
 type        call for papers, page limit or "extended abstract" ─▶ Submission Abstract
             paper-driven internal work ─▶ Research Update · recurring internal ─▶ Weekly Update · else ask
 title       "Is '<inferred title>' the correct title?"
 emphasis    results · problem formulation · a new direction · specific figures
 missing     new results, a decision, a blocker · research documents: formal setup and notation
 figures     which exist, which are planned (placeholders only in internal documents)
 submission  authors and affiliations · venue and deadline · do references count toward the limit?
             · own venue template? · comparison conditions (same data, same features, same tuning budget)
 wording     reader, outlet, field if still open · Simplified Technical English only on request
 enrichment  recall · NotebookLM · both · wording profile · skip
             offered when the request is high-level, lacks results, is research-oriented, or mentions
             literature, recall or past work; skipped for a detailed brief or an edit
```

If the venue prescribes its own template (LNCS, ACM, IEEE and similar), the skill says that the D3 layout then serves as
the group's circulation version, and asks how to proceed. The review depth is chosen in words; without a choice
`standard` runs and is named in one line (see [Review depth](#review-depth-how-many-tokens-a-run-spends)).

### An abstract, step by step

The steps print timestamped lines, such as `[HH:MM:SS] OUTLINE: Approved by user`, to the chat and to `progress.md`.
Changes the user asks for after seeing a version go into a new version (`v2_abstract.tex`); a version the user has
seen is never overwritten.

```
 ①ask ─▶ ②enrich ─▶ ③folder ─▶ ④outline ─▶ ⑤skeleton ─▶ ⑥fill ─▶ ⑦check ─▶ ⑧review ─▶ ⑨deliver
  │       │          │          │           │            │        │         │          │
 pages,  optional:  project    per page,   N template   compile  xelatex,  light ·    completeness,
 type,   recall,    folder,    budget,     calls,       after    checker,  standard · accuracy, approval,
 title,  NotebookLM assets/    Scan Test,  headings,    each     wording   full       final/ + assets/,
 focus   or skip    copied     your yes    N pages      column   lint,                SUMMARY.md
                                                                 page PNGs
                                                         ▲        │
                                                         └── fix ◀┘  until PASS and N pages
```

Step ⑦ runs in the folder that contains `assets/`:

```
xelatex -interaction=nonstopmode v1_abstract.tex                                 # one pass is enough
uv run <skill-dir>/scripts/check_abstract.py v1_abstract.tex --render review     # --submission for a submission
uv run <wording-dir>/scripts/check_wording.py v1_abstract.tex --genre abstract   # add --ste for STE
```

Then every page image in `review/` is read. At delivery the skill shows the list of added statements (reconstructed
notation, derived numbers, interpretations, `% TODO verify` items) with the accuracy question, and offers the removal
of invisible marks once (see [Wording](#wording-of-research-texts-d3-scientific-wording)). A folder that already contains `assets/d3-abstract.sty` is used as it is;
otherwise the project folder looks like this:

```
writing_outputs/YYYYMMDD_HHMMSS_<description>/
├── progress.md    timestamped log, review scores, wording brief and the user's corrections
├── SUMMARY.md     final files, compile command, type, pages, scores, open items, what was cut
├── drafts/        assets/ · figures/ · outline.md · v1_abstract.tex/.pdf · v2_… · revision_notes.md
└── final/         assets/ · YYYYMMDD_short_title.tex/.pdf (the approved version, compiles on its own)
```

### The page: header, co-branding, lead, two columns, footer

```
 ┌───────────────────────────────── A4 · margins 1.5 cm, bottom 0.5 cm ─────────────────────────────────┐
 │ university logo (46 mm)                                                           D3 logo (38 mm)    │ logo row
 │ ──────────────────────────────────────────────────────────────────────────────────────────────────── │ hairline
 │ \tittel        navy, SemiBold, \LARGE · about 55 characters per line, at most two lines              │
 │ \undertittel   italic · parts separated by \enspace|\enspace · empty ─▶ single-line header           │
 │ \innledning    lead paragraph, navy, \large, full width · empty ─▶ block removed                     │
 │ \helbredde     optional full-width table or figure · its height is lost in both columns              │
 │ ┌──────────────── \venstre ─────────────────┐  20 pt  ┌───────────────── \hoyre ──────────────────┐  │
 │ │ primary: problem, approach, evidence      │         │ supporting: numbers, status, questions or │  │
 │ │ \small · about 8.6 cm wide                │         │ references · \small · about 8.6 cm wide   │  │
 │ └───────────────────────────────────────────┘         └───────────────────────────────────────────┘  │
 │ ──────────────────────────────────────────────────────────────────────────────────────────────────── │ footer rule
 │ Data Driven Decisions Group | Chair … | University of Würzburg, or \projektname          page / N    │ gray
 └──────────────────────────────────────────────────────────────────────────────────────────────────────┘
  global slots:    \tittel · \projektname · \abstractpages
  per-page slots:  \undertittel · \innledning · \helbredde · \venstre · \hoyre · \bildebredde
                   (reset after every template call)
```

The D3 logo sits in the co-branding slot, vertically centred on the university logo. With `ngerman` babel the footer
line is German. `page / N` appears only when `\abstractpages` is above 1.

### One page or N pages: the page contract

```
 \renewcommand{\abstractpages}{N}  =  N × \input{assets/d3-abstract-template}  =  N pages in the PDF
                                      verified after every compile; check_abstract.py (PAGES) fails on a mismatch

 N = 1 (default)   page 1        lead · left │ right · ends with the questions (internal) or references (submission)

 N ≥ 2             page 1        self-contained core: claim, problem, approach, headline result
                                 lead required · passes the Scan Test alone · internal: the question section is here
                   pages 2…N-1   continuation: method details, extended results, a \helbredde table or figure
                                 lead optional (an empty \innledning frees about 5 line units per column)
                   page N        closing: discussion, scope, conclusion, references · at least 60 % full
                   every page    own \undertittel · footer shows page / N · each section on one page, in one column

 too little for N pages ─▶ propose N-1          too much ─▶ cut from the last page upward, ask before adding a page
 a venue page limit is never exceeded: content is cut, and the user is told what was cut
```

### What goes where

```
 your material                      in the .tex                                             rule
 headline number ─────────────────▶ \highlight{} in the lead paragraph, once                3 \highlight per page
 supporting numbers ──────────────▶ infobox, numbers other than the headline                3 per page
 takeaway sentence ───────────────▶ \keypoint{}, may restate the headline number            1 per column
 blocker, risk, deadline ─────────▶ card alert (deadline only if the footer lacks it)       2 per page
 comparison data ─────────────────▶ booktabs table: comparison methods · \midrule · ours    best value highlighted
 wide table or figure ────────────▶ \helbredde (\helfigur: 75 % of the text width)          height off both columns
 planned figure ──────────────────▶ card gray placeholder                                   internal documents only
 open questions ──────────────────▶ enumerate under the question section                    2 to 5, confirmed by you
 cited source ────────────────────▶ [n] in the text + reflist entry                         verifiable sources only
```

| Type | Pages | Left column | Right column | Footer |
|---|---|---|---|---|
| Research Update | 1 | Problem Formulation, Main Results, Benchmark Comparison, keypoint | Paper Progress, Figures Needed, Open Questions | venue and deadline |
| Weekly Update | 1 | Background, Details This Week | Status, Next Week, Questions for the Team | project name |
| Project Overview | 1 | Background, Our Approach | Headline Figures, Partners, Questions for the Team | university or project |
| Research Summary | 1 | Background, Methods, Results | Main Findings, Publications, Questions for the Team | university or project |
| Submission Abstract | 1, 2 or the page limit | Motivation, Problem and Approach | Results, Contributions, Conclusion, References | venue and page limit |

A Submission Abstract has final figures only, no question section and no progress table. Authors and affiliation go
into the page 1 subtitle; the deadline goes into `progress.md` and `SUMMARY.md`.

### How much fits: budget in the outline, fill in the PDF

```
 plan, in the outline (a column holds about 55 lines at \small)
   budget per column   45 line units with a lead paragraph · 50 without · minus the height of a \helbredde block
   \sectionhead 3 · paragraph (3 sentences) 5 · list (5 items) 7 · \keypoint 5 · \figur 10 · infobox 4
   card alert 4 · card gray (2.0 cm) 6 · table (5 rows) 8 · display equation 3 · question list (4) 12
   reflist entry 3

 measure, after every full compile: COLUMN FILL = the lowest element of each column, as a share of the height
 between the header hairline and the footer rule (axis not to scale)
   0 %                                 60 %                75 %                      95 %              100 %
   ├─────────────────────────────────────┼───────────────────┼─────────────────────────┼─────────────────┤
            warning on every page         ok on the last page   target on every page    warning: one more
                                             of N ≥ 2 only                                line can push
                                                                                          to a new page
   columns more than 25 points apart ─▶ warning, redistribute

 overflow ─▶ find the overfull column ─▶ cut its lowest-priority section ─▶ lists to 4 items, fewer table rows,
             shorter prose ─▶ recompile, rerun the checker                                    font sizes stay fixed
```

### What is checked, and how

`check_abstract.py` prints one section per check and ends with `RESULT: PASS` or `FAIL`. Errors (`E`) set exit code 1
and need a fix; warnings (`W`) need a decision, for example to keep an established technical term.

| | Rule | Where |
|---|---|---|
| ⛔ **fails** | `\abstractpages`, the number of template calls and the PDF page count differ | `check_abstract.py` (PAGES) |
| ⛔ | dashes outside number ranges: `---`, Unicode dashes, `--` between words (TikZ paths are skipped) | `check_abstract.py` (WORDING) |
| ⛔ | the "not X but Y" family: "not only", "not just", "not … but", ", not", "isn't … it's" | `check_abstract.py` (WORDING) |
| ⛔ | grading related work: "fails to", "suffers from", "overlooks", "falls short", "merely", "unlike previous", "existing methods cannot", "seminal", "a valuable first step", "laid the groundwork" | `check_abstract.py` (WORDING) |
| ⛔ | stock phrases: "leverage", "utilize", "harness", "delve", "in order to", "plays a crucial role", "comprehensive", "shed light on", "pave the way", "showcase", "underscore", "worth noting" | `check_abstract.py` (WORDING) |
| ⛔ | sentences above 40 words (above 25 with `--ste`); overclaims such as "unprecedented" or "it is evident that" | `check_wording.py --genre abstract` |
| ⛔ | `\definecolor` in the document, a color given by value, a color name outside `d3-*`, `black`, `white` in `\color`, `\textcolor`, `\pagecolor` or a TikZ key (`fill=`, `draw=`, `color=`, `text=`; `none` passes) | `check_abstract.py` (COLORS) |
| ⛔ | TeX errors, and characters the font lacks (they vanish from the PDF) | `check_abstract.py` (LOG, reads the `.log`) |
| ⛔ | `card gray` placeholders and the sections Open Questions, Questions for the Team, Paper Progress, Figures Needed in a submission | `check_abstract.py --submission` |
| ⚙️ **automatic** | footer `page / N` when `\abstractpages` is above 1; the chair line in German with `ngerman` babel; `\projektname` replaces it | `d3-abstract.sty` |
| ⚙️ | empty `\undertittel` gives a one-line header; empty `\innledning` and `\helbredde` remove their block; per-page slots reset after each page | `d3-abstract.sty`, template |
| ⚙️ | Greek letters and ≤ ≥ ≈ ≠ ∞ √ ∈ ∑ ∫ ∂ ⇒ ′ ″ ✓ µ ² ³ typed in text are set in math mode | `d3-abstract.sty` |
| ⚙️ | numbers in tables in the text font, aligned on the decimal marker; overhangs up to 1.5 pt inside tables are tolerated | `d3-abstract.sty` |
| ⚙️ | warns: a column above 95 % full, columns more than 25 points apart, a full page under 75 %, the last page of N ≥ 2 under 60 %, a missing header hairline or footer rule (overflow) | `check_abstract.py` (COLUMN FILL) |
| ⚙️ | warns: more than 3 `\highlight`, 3 infoboxes or 2 `card alert` per page, more than 1 `\keypoint` per column, a lead above 50 words or 3 sentences, a number emphasized by `\highlight` and in an infobox | `check_abstract.py` (EMPHASIS) |
| ⚙️ | warns: wording with legitimate uses ("rather than", "instead of", "while prior", "naive", "limited to", "key", "robust"); terms such as "doubly robust" or "Naive Bayes" are skipped | `check_abstract.py` (WORDING) |
| ⚙️ | warns: leftover `% TODO` and `% TODO verify` markers, overfull boxes, no PDF yet or a PDF older than the `.tex`, no `reflist` in a submission | `check_abstract.py` |
| ⚙️ | one PNG per page for the visual check | `check_abstract.py --render review` (`--dpi`, default 150) |
| 📖 **guides** | ask the page count (default 1); never exceed a venue page limit; cut content, font sizes stay fixed | `SKILL.md` |
| 📖 | outline with a line budget per column and the Scan Test, approved before any LaTeX | `SKILL.md`, `references/content-mapping.md` |
| 📖 | the lead paragraph states a claim with its number, in 2 to 3 sentences | `references/writing-style.md` |
| 📖 | numbers and references from the user's material, the project `.bib` or the enrichment; unverified fields marked `% TODO verify`; added statements listed for the user | `SKILL.md` (Content Integrity) |
| 📖 | 2 to 5 questions in internal documents, confirmed by the user, self-derived ones marked | `SKILL.md`, `references/questions.md` |
| 📖 | comparison methods above the `\midrule`, ours below; in charts ours in navy, comparison methods in gray | `references/macros.md` |
| 📖 | every page image read: logos, hairlines, colors, font, title breaks, nothing below the footer rule | `SKILL.md` (Phase 3) |
| 📖 | content and visual reviewer, each with its own rubric and a score out of 10 (see [Review depth](#review-depth-how-many-tokens-a-run-spends)) | `SKILL.md` (Dual Review) |
| 📖 | a new version for each round of changes, never overwritten; `final/` only after the user's approval | `SKILL.md` (Version Management) |
| 📖 | all Python through `uv`, never `pip install` or a bare `python3` | `SKILL.md` (Python and uv) |

Abstracts made before the 2026 corporate design, or with the former one-slider skill (`assets/d3-oneslider`), compile
unchanged with their own `assets/` copy. `references/troubleshooting.md` describes how to move them to the current
style.

</details>

## Conference posters from a paper (d3-poster)

`d3-poster` turns a paper into a printable A0 portrait poster in the university's poster template with D3
co-branding. It starts from what exists: the LaTeX source in a paper submodule (on GitHub, synced to Overleaf) or a
paper folder, a repository with figures and results, a single PDF or `.docx`, or notes. It writes one `poster.tex`
and its `poster.pdf` next to the paper, so that co-authors can compile the poster on Overleaf. The layout is the
vendored `baposter` grid class with a thin reskin, `d3-poster.sty`, which draws the frame of the university
template. No LaTeX is written before you approve a content outline. Two columns are the default, three only when
the content needs them. When a box overflows, the skill cuts text and keeps the font sizes. Figures are vector
wherever possible. Versions live in git: there is one `poster.tex`, edited in place.

<details>
<summary><b>In detail:</b> What the skill contains · Before any file · From the paper to the boxes · A poster, step by step · The A0 page · Figures · When content does not fit · Two reviewers · What is checked, and how</summary>

### What the skill contains

```
skills/d3-poster/
├── SKILL.md                   workflow · project setup · skeleton · box budgets · review · checklists
├── baposter.cls               grid class (v2.0, GPL) without its Calibri block; copied next to poster.tex
├── example-poster.tex         reference poster to read; never copied into a project
├── assets/                    copied whole into drafts/ and final/
│   ├── d3-poster.sty          university frame · palette · Inclusive Sans UW · macros · card styles
│   ├── logos/                 white university logo, blue seal (header) · D3 logo (footer) · navy logo · D3 png
│   └── fonts/                 Inclusive Sans UW: regular, italic, medium, semibold, bold · OFL licence
└── references/                loaded when the topic comes up
    ├── extraction.md          per input tier: .tex mapping · PDF text and figures · .docx · interview
    ├── tikz-recipes.md        four figure recipes, each compiled · TikZ rules
    ├── macros-and-styling.md  frame geometry · macros · palette · fonts · tables · title
    ├── error-handling.md      eight known compile and rendering issues
    └── dual-agent-review.md   the two reviewer prompts · loop for `full` · scores into final/README.md
```

The skill has no script of its own. Its Python steps (PDF and `.docx` extraction, the PNG render of the poster) are
inline commands run with `uv run --with pymupdf` or `--with python-docx`. The wording lint is `check_wording.py`
from `d3-scientific-wording` (see [Wording](#wording-of-research-texts-d3-scientific-wording)).

### Before any file: detect, then ask

```
 SAVE      paper submodule in .gitmodules? ──yes──▶ <submodule>/poster/     (on GitHub; Overleaf syncs it)
             │ no
             ▼ paper folder? ──yes──▶ <paper-folder>/poster/
             │ no
             ▼ ./poster/                       printed with the reason; you confirm before a file is created
 TIER      A · B · C · D, first match ──▶ printed; you confirm or override
 BRIEF     title · section-to-box mapping · figures · tables · bib hits ──▶ "use this as the seed?"
 OUTLINE   bullets per box · glance test · wording mode (standard or STE) ──▶ approved before any LaTeX
 IF NEEDED paper source (several candidates) · 3 columns · subtitle · captions · architecture figure
           · vault recall or NotebookLM (for a high-level request, or one without a paper)
```

You are also asked for the title and the author line, the headline metric (it goes in an `infobox`), the one or two
figures to feature and the 3 to 5 references for the footer. The skill decides box positions, card styles and
spacing inside a box. Review depth is not asked: `standard` runs unless your words pick `light` or `full` (see
[Review depth](#review-depth-how-many-tokens-a-run-spends)).

### From the paper to the boxes

```
 INPUT TIER (first match)               EXTRACTION                                    ON THE POSTER
 A  repo with a paper submodule ──┐     .tex source
    + figures/ results/ code/     ├─▶   \title · \author ───────────────────────────▶ header: title, author line
 B  paper repo only (Overleaf) ───┘     abstract · first intro paragraph ───────────▶ Motivation
                                        \section{Problem|Model|Setup|Formulation} ──▶ Problem
                                        \section{Method|Approach|Algorithm} ────────▶ Approach
                                        \section{Results|Experiments|Evaluation} ───▶ Empirical Results
                                        \begin{table} ──────────────────────────────▶ booktabs table
                                        \includegraphics ───────────────────────────▶ figure inventory
                                        references.bib, cited entries only ─────────▶ footer: 3 references
 C  one paper file ──────────────────▶  .pdf: pymupdf text, figures ────────────────▶ same mapping
                                        .docx: python-docx text and images ─────────▶ same mapping
 D  notes or a topic ────────────────▶  interview: 8 questions ─────────────────────▶ the same boxes

 figure scan  figures/ figs/ plots/ images/ · results/ output/ experiments/ runs/ · code/ src/ notebooks/ scripts/
              one file per stem: PDF > EPS > SVG > PNG > JPG
```

A PDF in two columns is read block by block, sorted by y and then x. The result is a content brief: the title, the
abstract condensed for Motivation, the section-to-box mapping, the top figure candidates, the headline table and the
number of bib entries. Nothing goes into a box before you approve the brief.

### A poster, step by step

Editing an existing poster starts with a git commit (`Pre-edit snapshot`), changes `poster.tex` in place and adds a
dated entry to `revision_notes.md`. A new poster runs these steps:

```
 ①scan ───▶ ②outline ──▶ ③skeleton ───▶ ④fill ────▶ ⑤validate ─▶ ⑥lint ─▶ ⑦review ─▶ ⑧final
   │          │            │              │           │            │        │          │
 save       bullets      poster.tex     box by      xelatex,     check_   light,     watermark
 location,  per box,     from the       box,        PNG at       wording  standard   question,
 tier,      glance       skeleton,      compile     150 dpi,     --genre  or full    copy to
 extract,   test, STE?   TODO per box,  after each  log grep,    poster              final/,
 brief      you approve  1 A0 page                  checklist                        README.md
                                                                                     with scores
```

`progress.md` logs each phase with a timestamp, the wording brief and your wording corrections. XeLaTeX is the
default engine (LuaLaTeX works the same); pdfLaTeX falls back to a Helvetica clone and is the last resort. With
`\cite{}` the run is `xelatex`, `bibtex`, `xelatex`, `xelatex`. `drafts/` and `final/` each hold `baposter.cls` and
`assets/`, so either folder can be uploaded to Overleaf on its own. When the local compile fails and the poster sits
in a paper submodule, the skill pushes it to GitHub and tells you the Overleaf settings (main document
`poster/drafts/poster.tex`, compiler XeLaTeX). The PDF from Overleaf goes to `poster/drafts/poster.pdf` for the
checks, and the outer repository gets the new submodule pointer.

### The A0 page

`d3-poster.sty` draws the university frame around baposter's grid. Sizes are template millimetres on A0
(841 × 1189 mm, 25 mm margins); they scale with the shorter paper side, so A1 keeps the proportions.

```
 ┌─────────────────────────────────────────────────────────────────────────────────────────────┐
 │ ┌──────────────┐   title · white Bold · 50 pt · one or two lines                            │  header box
 │ │ university   │   authors · white · 34 pt · one line                                       │  navy, 119 mm
 │ │ logo, white  │   ◀──────────────── text field 425 mm ────────────────▶          ┌─────────┤
 │ └──────────────┘                                                                  │ seal,   │
 │                                                                                   │ blue,   │
 │                                                                                   │ 93 mm   │
 └───────────────────────────────────────────────────────────────────────────────────┴─────────┘
                                            20 mm
 ┌─ Motivation ──────────────────────────────┐      ┌─ Approach ───────────────────────────────┐  section bars
 │ 60–100 words · 1 \highlight · no figure   │ 14.2 │ 100–180 words in 2–3 bold-lead           │  ~24 mm, #ECECEC,
 └───────────────────────────────────────────┘  mm  │ paragraphs · 1 figure, no caption        │  navy SemiBold;
 ┌─ Problem ─────────────────────────────────┐      └──────────────────────────────────────────┘  key `emphasis`:
 │ 80–150 words                              │      ┌─ Empirical Results ──────────────────────┐  cornflower bar,
 │ 1–2 equations · 1 \keypoint               │      │ 30–60 words · 2–3 infoboxes              │  white text
 │                                           │      │ 1 booktabs table                         │
 │ above=bottom: fills the column            │      │ above=bottom: fills the column           │
 └───────────────────────────────────────────┘      └──────────────────────────────────────────┘
 ──────────────────────── navy rule, 0.7 mm, 12.5 mm below the columns ─────────────────────────
 ┌──────────────────┐ ┌────────┐ ┌────────┐ ┌────────┐   References (right half, 24 pt)
 │ D3 logo, 2 cells │ │ cell 3 │ │ cell 4 │ │ cell 5 │   3 short references, 5 at most
 └──────────────────┘ └────────┘ └────────┘ └────────┘   \dthreereferences{...}
   logo row: cells 72 × 39 mm · \dthreelogos, then \dthreelogocell{partner.pdf} for up to three more
```

The footer slot holds the literature; there is no Literature box. Three columns are for papers with five or more
distinct sections or for a venue that expects them: Motivation and Problem share column 0, Approach and Empirical
Results take a full column each. Posters made before the 2026 design still compile with the new header and footer.
The seal is an interim choice until the faculty package of the corporate design is released (see [Design](#design)).

### Figures: what is used, what is redrawn

```
 figure for a box ─▶ architecture-style name or caption? ──yes──▶ you choose: use as-is · simplify (recommended)
        │ no          (architecture, pipeline, overview, framework,         · replace by a 3-block diagram · skip
        ▼              system, model, schema, diagram)
 vector file on disk? (PDF > EPS > SVG) ──yes──▶ \includegraphics[width=\linewidth]{...}, SVG converted to PDF first
        │ no
        ▼
 raster width:  ≥ 2200 px ─▶ OK, used  ·  1500–2199 px ─▶ LOW, you are told  ·  < 1500 px ─▶ TOO LOW, redraw offered
        │ no usable figure, or redraw accepted
        ▼
 TikZ recipe (vector): 1 block diagram · 2 pipeline, 4–5 stages · 3 layered architecture · 4 prior vs. ours
```

From a PDF, figures are cropped from the page above their caption, which keeps them vector; you pick from the
candidates. Embedded images are extracted as PNG, and a full page at 600 dpi is the last resort. 2200 px is a column
of about 38 cm at 150 dpi. If a central figure exists only as PNG, you are asked to export it again as PDF. A poster
figure carries no caption unless you ask for one, and a box holds one or two figures at most.

### When content does not fit

```
 box content too tall ──▶ baposter clips it: no error, no warning, only the rendered PNG shows it
                          │ found by compiling after each box and looking at the 150 dpi render
                          ▼
                          cut the lowest-priority content ──▶ lists to 4 items · fewer table rows · shorter prose
                          │                                   \keypoint earlier or shorter · fonts keep their size
                          ▼
                          recompile, render again

 title block (90 mm slot) or references (58 mm slot) too tall
   ──▶ d3-poster.sty steps the font down: 0.92 · 0.85 · 0.78 · 0.72 · 0.66 · 0.6, then scales the block
   ──▶ poster.log: "d3-poster Warning: The title block was set at 0.85 of its normal size to fit its slot."
   ──▶ shorten the title, the author line or the references
```

### Two reviewers

At depth `standard` and `full` (see [Review depth](#review-depth-how-many-tokens-a-run-spends)) two `Explore` agents
read the rendered poster in parallel. Their reports appear in the chat verbatim, followed by a summary with the
verdict and the fixes.

```
                      ┌─▶ CONTENT · reads poster.tex and the PNG                    ─┐
                      │     glance test · information hierarchy · writing style      │
 poster.pdf ─▶ PNG ───┤     domain adaptation · emphasis · one message per box       │
   (150 dpi)          │     bibliography · cold read                                 ├─▶ both reports in chat
                      │                                                              │   verdict: ship or iterate
                      └─▶ VISUAL · scores the PNG, source for reference              │   fixes applied, recompiled,
                            layout · header & footer · box headers · colours         │   checks rerun
                            font · TikZ elements · tables · whitespace              ─┘

   each category 0–10 · Overall = the lowest category · 9 = ship-able with no fixes
   standard: one round · full: again until both Overall ≥ 9, at most 4 rounds, then the rest goes to you
   final scores and number of rounds ─▶ final/README.md
```

### What is checked, and how

| | Rule | Where |
|---|---|---|
| ⛔ **fails** | `d3-poster.sty` loaded without the baposter class | `d3-poster.sty` (package error) |
| ⛔ | `baposter.cls` not next to `poster.tex`, fonts missing from `assets/fonts/`, the upstream class with its Calibri block | XeLaTeX run, `references/error-handling.md` |
| ⛔ | sentences above 35 words (above 25 with `--ste`), "not X but Y", "fails to" about cited work, marker words such as "leverage" | `check_wording.py --genre poster` (exit 1) |
| ⚙️ **automatic** | university frame: header box with logo, title, authors and seal; grey section bars; footer rule, logo row, references slot | `d3-poster.sty` |
| ⚙️ | template defaults: 2 columns, header height, column gap, grey bars, `headershade=plain`; options in `\begin{poster}` or in a box override them | `d3-poster.sty` |
| ⚙️ | a title block or references block too tall for its slot is set smaller and reported | `d3-poster.sty`, `poster.log` |
| ⚙️ | Greek letters and math symbols the font lacks are set in math mode | `d3-poster.sty` (`newunicodechar`) |
| ⚙️ | `\d` released before siunitx; table numbers in the house font; `uniblue` mapped to navy; Helvetica clone under pdfLaTeX | `d3-poster.sty` |
| 📖 **guides** | save location next to the paper, confirmed before files are created; input tier printed and confirmed | `SKILL.md` |
| 📖 | content outline approved before any LaTeX; glance test: title, box headers and headline number convey the contribution from 2 m | `SKILL.md` |
| 📖 | 2 columns unless the content needs 3; literature in the footer slot (3 to 5 references); title in one or two lines, no subtitle unless asked | `SKILL.md` |
| 📖 | box budgets, cut when more than about 20 % over; ≤ 3 `\highlight` and 1 `\keypoint` per box; lists ≤ 5–6 items, tables ≤ 6 rows, 1–2 equations | `SKILL.md` |
| 📖 | exactly one A0 page, nothing clipped: compile after each box, render at 150 dpi and look | `SKILL.md`, `uv run --with pymupdf` |
| 📖 | log: `Overfull \hbox` above 50 pt, `Font ... not found`, `File ... not found`, `d3-poster Warning`, `Missing character` outside `nullfont` | `poster.log` |
| 📖 | vector figures first; raster below 2200 px reported, below 1500 px a redraw offered; architecture figures need your choice; no captions unless asked | `SKILL.md`, `references/extraction.md` |
| 📖 | D3 colours only, no `red`/`blue`/`green` or hex codes; orange for highlights and alerts; booktabs tables with the baselines above `\midrule` | `references/macros-and-styling.md` |
| 📖 | one `poster.tex` and `poster.pdf`, versions in git, `example-poster.tex` never copied | `SKILL.md` |
| 📖 | every wording error fixed, every warning decided; invisible marks removed only on your yes, before `final/` | `SKILL.md`, `d3-scientific-wording` |
| 📖 | two reviewers, Overall = lowest category; `full` until both are ≥ 9, at most 4 rounds | `references/dual-agent-review.md` |

</details>

## Talks as Beamer PDFs or HTML decks (d3-presentation)

`d3-presentation` builds the group's talks in the university design with D3 co-branding (see [Design](#design)), either as a
LaTeX Beamer PDF or as an interactive HTML deck written in Python (`slides.py`). Both routes share one slide
vocabulary (`\onecol` and `onecol()`, `\showsection{n}` and `section(n)`, and so on), the content rules and the
wording lint. Three principles run through the skill. The storyline belongs to the presenter: no slide is written
before the user has given or approved the sequence of action titles. Facts come from the sources: every number that
may reach a slide stands in a fact sheet with its file, page or table, and gaps are marked `[TO CHECK]`. In an HTML
deck every content slide centres on a designed object that carries its claim (a model figure that draws itself, bars
that grow out of each other, a gauge, a replayed study stimulus, a live instrument), and motion appears where it
reports something. Each talk lives in its own folder and needs nothing from the skill after scaffolding. The HTML deck
is one offline file with fonts, logos, figures and, when a slide holds math, MathJax embedded; its speaker notes
travel inside it unless it is built with `notes=False`. The university PowerPoint master for the `.pptx` export is not
part of the skill, because the repository is public: it stays on your machine, and `*.potx` is git-ignored.

<details>
<summary><b>In detail:</b> What the skill contains · Two routes, one storyline · Before the first slide · A deck, step by step · One designed object per slide, built in steps · The presenter window · Looks · PowerPoint export · What is checked, and how</summary>

### What the skill contains

```
skills/d3-presentation/
├── SKILL.md                          format and review depth · storyline gate · shared rules · checks · delivery
├── references/
│   ├── style-guide.md                layout · action titles · talk skeletons and time budgets · builds · wording
│   ├── latex-workflow.md             Beamer: folder, template, numbering options, the frame, code boxes
│   ├── html-workflow.md              slides.py API · looks · builds · figures · math · shoot.py · .pptx · keys
│   └── html-components.md            the bar per slide and deck · "the draft says ... build instead" · kit catalogue
└── assets/
    ├── latex/
    │   ├── d3-beamer.sty             the frame on the master's 1280 × 720 grid (XeLaTeX, aspectratio=169)
    │   ├── d3-template-library.tex   optional: code boxes, TikZ styles, chevrons, timelines
    │   └── example-presentation.tex  a working example of every slide type and component
    ├── html/
    │   ├── init.py                   scaffolds a talk folder: slides.py, figures/, d3deck/ with fonts and logos
    │   ├── example-slides.py         every slide type and every kit object once (sections 1 to 4 twin the .tex)
    │   ├── d3deck/                   the engine; a deck builds with the Python standard library only
    │   │   ├── deck.py               meta(), slide functions, numbering, busy-slide warnings, build()
    │   │   ├── chrome.py             the master's frame: logos, covers, dividers, agenda, closing slide, tracker
    │   │   ├── components.py         twins of the LaTeX macros: code boxes, chevrons, timeline, stat, scrim, mix()
    │   │   ├── kit.py                designed objects: tile, model, bars, gauge, proof, versus, chat, units, lab
    │   │   ├── figures.py            fig(): png, jpg, svg or pdf embedded with the aspect ratio pinned
    │   │   ├── engine.py             steps and ghosts, keys, #slide.step links, fullscreen, overview, B/W, laser
    │   │   ├── nav.py                jump tabs and links · / search over titles, summaries and notes · H backup hub
    │   │   ├── presenter.py          presenter window: notes, next step, clock, pace; relays clicks
    │   │   ├── shoot.py              every step shot · overflow audit · lint · budget · signature · contact sheets
    │   │   ├── pptx_export.py        editable .pptx on the university master; extract.js measures the slides
    │   │   └── mathjax/              MathJax 3.2.2, embedded only when a slide holds math
    │   └── tests/                    unit and browser tests (browser: Playwright; export: D3_UNI_MASTER)
    ├── fonts/                        Inclusive Sans UW (5 faces) · D3 Symbols (Greek, math; an Inter subset) · OFL
    └── logos/                        university logo and seals (svg, pdf) · D3 logo · Würzburg cover photo
```

### Two routes, one storyline

```
 topic · outline · notes · a paper · a repository · an old deck · feedback by slide.step ("4.3: move the box up")
                                                    │ read first; every number with its file, page or table
                                                    ▼
                     ┌──────────────────────────────────────────────────────────────────┐
                     │ storyline.md   approved action titles · audience · time slot     │
                     │                the one takeaway · fact sheet · ## Wording        │
                     └──────────────────────────────┬───────────────────────────────────┘
                                                    │ format chosen in Step 0
                     ┌──────────────────────────────┴────────────────────────────────┐
                     ▼ PDF                                                           ▼ HTML
 ┌───────────────────────────────────────┐                    ┌─────────────────────────────────────────────┐
 │ <name>/<name>.tex                     │                    │ <name>/slides.py + d3deck/ (from init.py)   │
 │ assets/: d3-beamer.sty, fonts, logos  │                    │ frame · component kit · engine · presenter  │
 │ xelatex twice                         │                    │ uv run slides.py                            │
 └───────────────────┬───────────────────┘                    └──────────────────────┬──────────────────────┘
                     ▼                                                               ▼
               <name>.pdf                                     dist/<name>.html   one offline file
                                                              dist/<name>.pdf    shoot.py --pdf (print view)
                                                              dist/<name>.pptx   pptx_export.py (university master)

 shared by both: slide vocabulary · brand colours · content rules · wording lint · review depth
```

### Before the first slide: two questions, then the storyline

The skill reads the request first and asks only what it leaves open. Sources (paper, repository, notes, old deck) are
read before anything is proposed.

```
 STEP 0   format and review depth named in the request? ──yes──▶ use them
            │ no
            ▼ ask both in one message, then never again
          format  ".tex", "Beamer", "LaTeX", "PDF" ─▶ PDF · "HTML", "interactive", "steps", "web" ─▶ HTML
          depth   "quick", "cheap", "short on tokens" ─▶ light · "full review", "thorough" ─▶ full
                  nothing said ─▶ standard                                                (see Review depth)

 STEP 1   "Do you already have a storyline in mind?"
            ├── yes ─▶ restate it as action titles; keep its order and emphasis; ask about at most two gaps
            └── no ──▶ two proposals that differ in kind, 6 to 12 action titles each, one recommended
                       answer first or build-up · chronological project story or argument by claims
                       HTML: each title with its designed object and its time, summed against the slot
          asked only when unclear, as one AskUserQuestion call (at most four questions):
            audience · time slot · the one takeaway · kind of talk · sources · wording: standard or STE
            HTML feel: calm (default) · rich · interactive
            a wording profile, when a literature folder, a vault or a NotebookLM notebook is at hand

 GATE     the user picks, edits or replaces ─▶ storyline.md; the slide titles must match it
          nobody to ask (batch run) ─▶ the better proposal, the choice and its reason at the top of storyline.md
```

### A deck, step by step

The steps are the same for both routes. The talk folder is named with 1 to 3 lowercase words joined by `_` (for
example `ai_healthcare`); `init.py` refuses other names and existing folders.

```
 ①ask    ─▶ ②folder  ─▶ ③rules     ─▶ ④storyline  ─▶ ⑤write    ─▶ ⑥build   ─▶ ⑦check     ─▶ ⑧review ─▶ ⑨deliver
   │          │           │             │              │            │           │             │          │
 format,    init.py     wording       yours, or two  .tex or      xelatex ×2  compile log   0, 1 or 2  file, scores,
 review     <name>      skill; style  proposals;     slides.py:   or uv run   or shoot.py;  reviewer   [TO CHECK],
 depth      or mkdir    guide; html-  approval       an object,   slides.py;  check_        agents     keys, feedback
 (Step 0)   + assets    components    gate           time=,       warnings    wording.py    (depth)    by slide.step
                                                     notes=
```

The HTML route on the command line (`<skill-dir>` and `<wording-dir>` as defined in `SKILL.md`):

```
uv run <skill-dir>/assets/html/init.py my_talk                         # ② creates ./my_talk; then cd my_talk
uv run slides.py                                                       # ⑥ "N slides · M steps · X MB → dist/…"
uv run --with playwright --with pillow d3deck/shoot.py dist/my_talk.html --contact --slot 15     # ⑦
uv run <wording-dir>/scripts/check_wording.py slides.py                # ⑦ add --ste in STE mode
uv run --with playwright --with python-pptx d3deck/pptx_export.py dist/my_talk.html             # optional
uv run --with playwright playwright install chromium                   # once per machine
```

The LaTeX route copies `assets/latex/*`, the fonts and five logo PDFs into `<name>/assets/` and compiles with
`xelatex <name>.tex` twice (three times with the `contentnumbering` option). Feedback comes back by `slide.step`, the
numbers of the `#12.3` deep links ("4.3: move the box up"). Structural changes are recorded in `storyline.md`, so the
next round does not undo them, and wording corrections go verbatim under its `## Wording` heading.

### One designed object per slide, built in steps

```
 the draft says                         build instead (html-components.md, section 2)
 "prior work assumes A leads to B"    ─▶ model() of the assumed relation, then a callout() with what breaks
 "three reasons"                      ─▶ three tile()s with icons in a grid3, the decisive one on its own step
 "what X does to Y"                   ─▶ bars() on one scale, each new bar growing out of the previous one
 "results"                            ─▶ a k-table with effect() bars; the disappointing row on its own step
 "a parameter matters"                ─▶ lab(): the figure, a slider() with presets, a readout()

 one slide, steps=3, opened as #5, #5.2 and #5.3 (deep links count steps from 1)
 ┌──────────────────────────────────┐   ┌──────────────────────────────────┐   ┌──────────────────────────────────┐
 │ KICKER  one claim         ● ○ ○  │   │ KICKER  one claim         ● ● ○  │   │ KICKER  one claim         ● ● ●  │
 │                                  │   │                                  │   │                                  │
 │ ● form ··▶ ○ verify ··▶ ○ rely   │   │ ● form ──▶ ● verify ··▶ ○ rely   │   │ ● form ──▶ ● verify ──▶ ● rely   │
 │                                  │   │                                  │   │                                  │
 └──────────────────────────────────┘   └──────────────────────────────────┘   └──────────────────────────────────┘
 ● sharp from its step: data-s="k", or s=k on kit objects (0-based)
 ○ ghost: already in its final place, 15 % opacity and grey (reveal='hide': invisible) · data-soft="1": 42 %
 data-hide="1": invisible on stage until its step · scrim(): a white cover over a region, lifted at its step
 nothing moves and nothing is removed between steps · the step dots under the top-right bar count the steps
 2 to 4 steps (a model built one relation per step: up to 6) · calm: about one slide in three builds
```

The agreed feel sets the motion budget: `calm` (the default) builds on about one slide in three, `rich` and
`interactive` wherever a step adds one idea; `interactive` adds Q&A interactions (hover-lit relations via `k=`,
click-for-detail badges, citations, preset chips) or a live instrument. Anything interactive is a bonus: every slide
reads completely in the PDF and the overview, which show the end state of every build.

### The presenter window

```
  MAIN WINDOW  dist/<name>.html                      PRESENTER WINDOW  dist/<name>.html?presenter
  what the room sees · F fullscreen                  N or S opens it · on the other screen when allowed
 ┌───────────────────────────────────┐                ┌──────────────────────┬──────────────────────────────┐
 │                                   │                │ current slide        │ next step or next slide      │
 │  the slide at its current step    │  ◀──────────── │ (half size)          │ (30 %)                       │
 │                                   │  keys, jumps,  │                      ├──────────────────────────────┤
 │  L laser pointer                  │  B and W,      │                      │ 14:05   07:32                │
 │  B or W black or white screen     │  clicks and    │                      │ clock   elapsed (P, T)       │
 │  O overview · / search · H backup │  slider input  │                      │ behind by 0:40               │
 │                                   │                ├──────────────────────┴──────────────────────────────┤
 │                                   │  slide, step   │ notes: "0: point one. 1: point two."                │
 └───────────────────────────────────┘  ────────────▶ └─────────────────────────────────────────────────────┘

  pace (only when slides carry time=): "on pace" · "ahead by m:ss" more than 20 s ahead of the budgets
  of the slides before · "behind by m:ss" more than 20 s past this slide's own budget · "over by" past the total
  popup blocked ─▶ N toggles a notes drawer in the main window
```

Keys: arrows for steps and slides · a number and Enter to jump · O overview · `/` search over titles, summaries and
notes · H backup hub · B or W blank screen · L laser (main window) · ? all keys. `#12.3` in the URL opens slide 12 at
step 3. The presenter window relays clicks on buttons and changes of inputs and selects; every clickable kit object
is a button.

### Looks: klar, beamer, uni

Every look sits on the frame of the university PowerPoint master: the university logo top left over a hairline, the
footer line `presenter | chair | title`, the page number in a navy tab, Inclusive Sans UW. `lang='de'` switches the
labels and the chair line to German.

| | `look='klar'` (default) | `look='beamer'` | `look='uni'` |
|---|---|---|---|
| For | D3 talks | an HTML deck that must match a Beamer PDF slide for slide | teaching and other university talks without D3 branding |
| D3 logo | co-branding slot, top right | co-branding slot, top right | none |
| Accent | D3 orange `#F29100`; titles as orange kicker plus one claim (`K()`) | D3 orange `#F29100` | coral `#ED6A5B` for graphic marks, berry `#821044` for text accents such as kickers |
| Structure | section tracker in the header; navy dividers list the part's slides (six at most) and replace the agenda slide | no tracker unless `tracker=True` (then in the footer band); dividers without the slide list; Beamer text sizes | no tracker unless `tracker=True`; dividers without the slide list |
| Cover default | `band` | `band` | `navy` |
| Kit objects | as in `html-components.md` | as in `html-components.md` | the master's plain style: no cards, no icons, sans-serif labels |

`meta(dividers='agenda')` repeats the agenda on navy at every `section()`, with the current part highlighted; teaching
decks use it so the room always sees where the session stands.

### PowerPoint export

For colleagues who want to edit the slides, `pptx_export.py` rebuilds a built HTML deck on the university master.

```
 dist/<name>.html ─▶ Playwright shows each slide at its last step and measures it on the 1280 × 720 canvas
                                                    │
            ┌───────────────────────────────────────┼─────────────────────────────────┐
            ▼                                       ▼                                 ▼
  layout of the master                native and editable                   pictures, transparent ground
  cover ─▶ Deckblatt 1, 2 or 4        placeholders: titles, subtitles,      figures, charts, inline SVG,
     (navy, photo, band)                 names, dates, divider names,       form controls, lines that
  divider ─▶ Trennseite 2                agenda entries                     hold only a formula
  agenda ─▶ Agenda 1                  text boxes, tables, shapes: text,
  plain list ─▶ Inhaltsfolie 1           lists, boxes, chevrons, bars,      the D3 logo of klar and beamer
  takeaway ─▶ Inhaltsfolie 2             timelines, cards                   (the master draws logo, rule,
  references, de ─▶ Quellenangaben    step builds ─▶ appear on click        footer, page number, seal)
  other ─▶ Blanko 1                   notes ─▶ notes pages
  closing ─▶ Abschlussseite           sections ─▶ PowerPoint sections
                                      jump() ─▶ click actions
            └───────────────────────────────────────┬─────────────────────────────────┘
                                                    ▼
                                            dist/<name>.pptx

 master: --master ─▶ $D3_UNI_MASTER ─▶ the deck's folder and its parents ─▶ d3deck/office/; none found: it stops
 differs from the HTML: the text takes the master's theme font Segoe UI, so a line can wrap at another word; page
 numbers count every slide; instruments, replays and Q&A are frozen in their final state; the closing slide's
 master prints a fixed "Tel." label, so thankyou() wants a phone line in contact=
```

### What is checked, and how

| | Rule | Where |
|---|---|---|
| ⛔ **refuses** | a talk folder name other than lowercase words joined by `_`, or a folder that exists | `init.py` |
| ⛔ | a slide before `meta()`; an unknown `look`, `feel`, `reveal`, `numbering` or `dividers`; `time=` not written as `m:ss` | build (`deck.py`) |
| ⛔ | `section(n)` outside the section list or after `appendix()`; `facts()` with more than four numbers; an unresolved or duplicate jump mark, a `mark()` with no slide after it | build (`deck.py`) |
| ⛔ | a missing figure, a PDF figure without `pdftoppm`, `chevrons()` outside 2 to 5 phases, a timeline range outside 0..1 | build |
| ⛔ | a `model()` node outside its region or an edge to an unknown node, a bar above its scale, a gauge mark outside its range, an unknown colour or icon | build (`kit.py`) |
| ⛔ **fails** (exit 1) | a visible element outside the slide box or cropped by its body box (2 px tolerance), on every step | `shoot.py` OVERFLOW |
| ⛔ | a formula MathJax cannot render | `shoot.py` MATH |
| ⛔ | emoji or dingbats used as icons (✓ ✕ ⚠ ★ ➜) | `shoot.py` LINT |
| ⛔ | console errors, uncaught exceptions and failed requests | `shoot.py` CONSOLE |
| ⛔ | wording errors (see [Wording](#wording-of-research-texts-d3-scientific-wording)) | `check_wording.py` |
| ⛔ | an export without the university master; it stops before the browser starts | `pptx_export.py` |
| ⚙️ **automatic** | one offline file: fonts, logos and figures embedded, MathJax only when a slide holds math | build |
| ⚙️ | warnings for busy slides of the main part: more than 4 steps, one step per bullet, more than 75 body words or 6 bullets, more than two kinds of visual component, a text-only slide, `display:none`; more than 7 sections | build |
| ⚙️ | `feel='calm'`: a warning when more than 40 % of the content slides build (from six content slides on) | build |
| ⚙️ | `feel='interactive'`: a warning when no content slide has an interaction (`k=`, a badge, a `cite()`, a button or an input) | build |
| ⚙️ | every slide shot at every step in its end state (480 ms settle, animations finished); contact sheets; `shots/report.json` | `shoot.py` |
| ⚙️ | warnings: holes (content ends more than 30 % of its region above the bottom and is not centred), more than 100 visible words, lowercase Greek in uppercase labels, a cut source line | `shoot.py` LINT |
| ⚙️ | the summed `time=` budgets against `--slot`; content slides without `time=` while others carry one | `shoot.py` |
| ⚙️ | the signature: content slides with builds, motion, a designed object, interactive elements; text-only slides by number | `shoot.py` |
| ⚙️ | `model()` arrows: sides that face each other, several edges on one side spread out, the tip on the target border | `kit.py` |
| ⚙️ | Greek letters and math symbols in running text set in math mode, since the house font lacks them | `d3-beamer.sty` |
| 📖 **guides** | format and review depth asked once; no slide before the storyline is approved | `SKILL.md` |
| 📖 | every number traceable to the fact sheet; illustrative numbers labelled; a redrawn figure keeps every edge, label and term | `SKILL.md`, style guide |
| 📖 | action titles that read as the argument on their own; one message and one visual idea per slide; HTML claims of at most 15 words | `SKILL.md`, style guide |
| 📖 | a designed object on every content slide; keywords on the slide, sentences in `notes=` (about 40 visible words) | `html-components.md` |
| 📖 | motion that reports something; 2 to 4 steps; clusters, never bullet by bullet; at most one orange element per slide | style guide |
| 📖 | brand colours only; coral only in the uni look | `SKILL.md` |
| 📖 | 45 to 60 s per content slide, up to 1:30 for a built figure, about 10 % of the slot as slack | style guide |
| 📖 | LaTeX: a clean compile log and no `Missing character` in the `.log` | `latex-workflow.md` |
| 📖 | notes ship inside the HTML file: `build(name, notes=False)` before sharing a deck with private notes | `html-workflow.md` |

Reviewer agents come on top of these checks (see [Review depth](#review-depth-how-many-tokens-a-run-spends)): none at `light`, one at `standard`, and at `full` two
(content and visual) that loop until every category scores 9 of 10.

</details>

## Explaining a project to its own authors (d3-explainer)

`d3-explainer` builds one offline HTML file that explains a research repository to the people who write it. The
page covers the question, the gap the project closes, how the core idea works and how each central derivation goes. It
also maps the paper to the code, reports the evidence, and lists what is still open. The readers are the author and
the co-authors. The skill therefore skips textbook background, marks interpretations as such, and gives assumptions,
paper-versus-code differences and open questions a section of their own. Every substantive claim points to its
source, and the build checks that the pointer exists. Interactive figures carry the intuition; each one needs a
sentence of the form "moving X shows that Y" before it is built. All files the skill creates sit in
`<repo>/explainer/`. A copy into the vault and a commit happen only on a yes. Fonts, MathJax and data are embedded in
the built page, so it works offline and can be sent by email. Its look follows [Design](#design), without logos: the
explainer stays unbranded.

<details>
<summary><b>In detail:</b> What the skill contains · Where things are read, and who writes what · First use · An explainer, step by step · What an explainer is made of · Source pointers, and how the build checks them · Interactive figures · Updating an explainer after the paper or the code changed · What is checked, and how</summary>

### What the skill contains

```
skills/d3-explainer/
├── SKILL.md                    question round · 5 phases · rules · update · checklist before delivery
├── scripts/
│   ├── scan.py                 one report on the repo: tier, paper, code symbols, results, vault, prior explainers
│   └── init.py                 creates <repo>/explainer/, prefills explainer.toml; --refresh swaps the engine
├── assets/
│   ├── d3x/                    the engine, copied into every explainer (a co-author rebuilds without the skill)
│   │   ├── build.py            sections → dist/<name>.html; validates pointers, pulls equations and code; packets
│   │   ├── check.py            headless browser: moves every control, steps every derivation, screenshots
│   │   ├── explainer.js        runtime D3X: widget, plot, flow, derivations, chips, notation drawer
│   │   ├── explainer.css       long-read in the university CD with the D3 accents and the role colours
│   │   ├── fonts/              Inclusive Sans UW · D3 Symbols · IBM Plex Mono (SIL OFL 1.1)
│   │   └── mathjax/            MathJax 3.2.2, inlined for offline math
│   ├── templates/make_data.py  computes the data of a figure with the project's own code
│   └── example/                toy repo (secretary problem) with a finished explainer: patterns, smoke test
├── references/                 scanning · content design · components · visualization · review
└── evals/                      3 task prompts on the example · 20 trigger prompts · offline grader
```

### Where things are read, and who writes what

```
  REPOSITORY                          <repo>/explainer/                        OUTPUT
  (read)                              (the only folder the skill writes)       (one file, works offline)
 ┌────────────────────────┐ read by  ┌──────────────────────────────────┐ build.py ┌────────────────────────────┐
 │ CLAUDE.md · README     │ scan.py, │ explainer.toml     init.py       │─────────▶│ dist/<name>.html           │
 │ paper/ .tex .aux .bib  │ Claude   │ brief.md           Claude        │          │  fonts, MathJax, JSON and  │
 │ src/   code, by symbol │─────────▶│ sections/NN-*.html Claude        │          │  images embedded           │
 │ results/ json · csv    │          │ data/*.json        make_data.py  │          ├────────────────────────────┤
 │ Vault/ the author's    │          │ d3x/               engine copy   │          │ review/ packets  build.py  │
 │        own notes       │          └──────────────────────────────────┘          │ review/check.md,           │
 │ earlier explainers     │                                                        │ review/shots/    check.py  │
 └───────────▲────────────┘                                                        └────────────────────────────┘
             │ at every build each pointer is checked, and each equation, code excerpt,
             └─ JSON file and image is pulled from here by build.py
```

- `scan.py` prints its report and writes a file only with `--out`.
- `init.py` also writes a `.gitignore` for `review/`, `figures/.cache/` and `scan.md`.
- `make_data.py` imports the project's modules. It writes JSON next to itself and never into the repository's own
  folders.
- `build.py` writes nothing when it finds an error.

### First use: the question round

```
 said in the request? ──yes──▶ use it, ask nothing
        │ no
        ▼ one message, then no further questions
 SCOPE     whole project · one part (a model, a derivation, a pipeline)
 DEPTH     focus · overview · standard (default) · deep        "keep it short", "just this derivation" ─▶ focus
 REVIEW    light · single · standard · full                    default follows the depth (see below)
 WORDING   ste (default) · standard                            "normal wording", "no STE" ─▶ standard
        │
        ▼ detected by scan.py and init.py, asked only when unclear
 TIER      A code and paper · B paper · C code · D PDF · E notes ──▶ printed as INPUT TIER, the user may override
 PAPER     several papers in the repo? ──yes──▶ ask which one ──▶ init.py --paper <folder>
 TOML      title, paper folder, macro files, vault ──▶ prefilled into explainer.toml
 LOCATION  <repo>/explainer/ at the root of the outer repo (not the paper submodule) ──▶ confirmed with the brief
 GAP       only inferred? ──▶ asked together with the brief
        │
        ▼ nobody can answer (batch or agent run)
 defaults, and every decision recorded in section 0 of brief.md
```

The recommended review follows the depth: `focus` light, `overview` single, `standard` and `deep` the two-agent
review. "quick", "no review", "cheap" or "short on tokens" mean light; "thorough" means full.

### An explainer, step by step

Every phase prints a status line (`[HH:MM:SS] PHASE: ...`). The brief is the one mandatory checkpoint: no section is
written before the author approves it.

```
 ①ask ─▶ ②scan+read ─▶ ③init+brief ─▶ ④write ─▶ ⑤build ─▶ ⑥check ─▶ ⑦lint ─▶ ⑧review ─▶ ⑨deliver
   │       │             │              │         │         │         │        │          │
 scope,  scan.py,      init.py;       one file  pointers, check.py  wording  light,     dist/<name>.html,
 depth,  then docs,    brief.md:      per       budget,   --shots:  lint on  single,    findings table;
 review, paper, prior  gap, plan,     section;  packets;  0 errors; the      standard   vault copy and
 wording explainers,   knob→insight   --draft   without   look at   sections or full;   commit on a yes
 in one  vault, code   per figure;    build     --draft   2 or 3             verify,
 message by symbol     approval       each time           shots              then fix
```

Reading follows a token budget and a fixed order (`references/scanning.md`). Orientation documents come first, then
the paper: abstract, introduction, contributions, model and method sections. Prior explainers follow
(`scan.py --explainer <file>` prints the outline, `--section N` one section), then at most 6 to 10 vault notes chosen
by title, then the code, read by symbol. One `Explore` subagent maps a code base of more than about 40 files or 8,000
lines. Recall or NotebookLM are offered only when the repository leaves the gap or the project history thin.

Review depths and their cost are in [Review depth](#review-depth-how-many-tokens-a-run-spends). Specific to this
skill: `single` runs one merged reviewer (about 50 to 70k tokens), and `full` stops after three rounds. Reviewers are
read-only and work from two packets that `build.py` writes. The fidelity packet (`fidelity-packet.md`) holds the text
with line numbers, every derivation step with its reason, and for every pointer the cited equation, code lines or
note. The figures packet (`figures-packet.md`) holds the caption and the script of every figure. A fidelity reviewer
reads the first and checks derivations, numbers, code claims, the gap, the honest inventory and the wording. An
experience reviewer reads the second, `check.md` and the screenshots, and checks that every figure teaches its
sentence. Blockers and majors are verified against the source before they are applied.

### What an explainer is made of

```
 hero  the central equation (pulled from the paper or written with the role macros), colour-coded, with a legend
 01    the project in one screen    claim · three or four KPI tiles
 02    setting and problem          actors · decisions · information · objective
 03    the research gap             2 to 5 strands: what each established, where it stops · gap table
 04…N  core ideas, one per section, each built up in the same order:
         ① plain sentence ─▶ ② figure to move ─▶ ③ formal statement ─▶ ④ derivation ─────▶ ⑤ where in the code
                             knob→insight         pulled from the .tex  3 to 8 steps, each  pointers, a short
                                                                        with its reason     excerpt
 N+1   how the code realizes it     pipeline flow (5 to 9 boxes) · paper-to-code map · 1 or 2 excerpts
 N+2   evidence                     the repository's numbers · what the experiments do not show
 N+3   honest inventory             assumptions · paper vs code · paper vs result files · open questions
 N+4   notation and sources         symbol · meaning · code name (also in the drawer, key n)

 tier B (no code): N+1 becomes "what an implementation needs" or is dropped
 tier C (no paper): formal statements stay [[reading]] until the author confirms them
 focus: one idea, a closing block on what it assumes and leaves open, a notation table
```

| Depth | Sections | Main-line words | Interactive figures | Derivations | Reading time |
|---|---|---|---|---|---|
| `focus` | 1 to 3 | up to 1,200 | 1 to 2 | 1 | about 5 min |
| `overview` | 4 to 6 | up to 2,500 | 2 to 4 | 0 to 1 | 10 to 15 min |
| `standard` | 7 to 10 | up to 6,000 | 4 to 8 | 1 to 3 | 20 to 35 min |
| `deep` | 10 to 14 | up to 12,000 | up to 14 | as needed | 40 to 60 min |

Text in `<details class="deep">` does not count toward the main line, and flow diagrams do not count as interactive
figures. "Deep on X" is a standard explainer in which X gets the room it needs.

### Source pointers, and how the build checks them

```
 written in a section                   build.py checks                                 shown on the page
 [[code:src/model.py:88 def solve]] ──▶ file · line within the file · symbol in file ──▶ code model.py:88 solve
                                        symbol moved: warning; chip and link follow it    (GitHub permalink)
 [[paper:eq:prob]]                  ──▶ a \label{eq:prob} in the paper folders ───────▶ paper Eq. (12), from .aux
 [[paper:§Optimal cutoff]]          ──▶ a \section or \subsection title contains it ──▶ paper § Optimal cutoff
 [[vault:Note name]]                ──▶ a note of that name in the configured vault ──▶ vault …, obsidian:// link
 [[result:results/x.json]]          ──▶ the file exists ───────────────────────────────▶ result results/x.json
 [[file:CLAUDE.md]]                 ──▶ the file exists ───────────────────────────────▶ file CLAUDE.md
 [[reading]] · [[src:…]]            ──▶ nothing ───────────────────────────────────────▶ my reading · source …

 <div class="eq" data-label="eq:prob">         ──▶ the equation from the .tex, numbered from the .aux
 <pre class="code" data-symbol="def f">        ──▶ the real lines, following the function when it moves
 <script type="application/json" data-src=…>   ──▶ the JSON file, embedded

 the evidence behind every pointer (equation, code lines, start of the note, small files whole) goes into the
 fidelity packet. A pointer that fails is a finding about its claim: fix the claim or the pointer, keep the chip.
```

### Interactive figures: where the numbers come from

```
 knob→insight sentence in the brief: "moving X shows that Y" ──▶ becomes the caption's Notice line
        │ no sentence ──▶ no figure (a table, a KPI tile or a static figure)
        ▼ numbers, in order of preference
 ① evidence              the repository's result files, embedded as JSON, [[result:…]] in the caption
 ② computed by its code  explainer/data/make_data.py calls the project's functions on a grid and writes JSON;
                         the sliders snap to the grid; one command regenerates it
 ③ toy                   the real formula at toy scale in the browser; toy: true adds an "illustrative toy" badge
        │
        ▼ every figure
 defaults at the paper's setting · 2 to 4 controls · seeded noise (ctx.rng) · fixed axes while a slider moves
 role colours (two to five, colour-blind safe palette) plus gray · two panels, never two y-axes
 caption: {fig} (numbered by the build), Try (an action), Notice (the insight, checkable in the figure)
```

`references/visualization.md` has a catalog of 14 figure patterns (a draggable optimum, a tangent at a draggable
point, sample paths with a time scrubber, a results explorer, a clickable flow and others).

### Updating an explainer after the paper or the code changed

```
 the page shows the commit it was built from
        │
        ▼ init.py explainer --refresh      newest engine; explainer.toml, brief and sections stay untouched
        ▼ build.py                         renamed label, missing file ─▶ error
                                           function moved ─▶ warning; the chip already follows the symbol
                                           excerpt selected by data-lines ─▶ warning with the line it now
                                           begins with; switch it to data-symbol
        ▼ git log <built-commit>..HEAD -- <paper and src paths>      what changed in substance
        ▼ edit the section files in place · rebuild · check.py · version with git, not with file names
        │
        ├── pointers only ────────────────▶ review light, no new brief
        └── claims, derivations, figures ─▶ tell the user which sections change, review them at the chosen depth
```

### What is checked, and how

| | Rule | Where |
|---|---|---|
| ⛔ **fails** | a pointer to a file, line, symbol, `\label` or section title that does not exist, or to a note missing from the configured vault; reported at every use | `build.py` |
| ⛔ | `data-label`, `data-src`, `data-symbol` or `data-lines` that the paper or the repository does not have | `build.py` |
| ⛔ | missing image or data file, data that is not valid JSON, a PDF figure without `pdftoppm` | `build.py` |
| ⛔ | a section file that is not one `<section id=…>` with an `<h2>`; duplicate ids; broken `#links` and `{fig:id}` | `build.py` |
| ⛔ | a widget figure without a script, or a script without a figure | `build.py` |
| ⛔ | leftover TODO, TBD, FIXME or XXX (allowed with `--draft`) | `build.py` |
| ⛔ | a `[[role]]` key or colour in the wrong form; a `[hero] equation` label that does not exist | `build.py` |
| ⛔ | NaN, undefined or Infinity in a figure, a script error, a control without visible effect, a handle that does not move | `check.py` |
| ⛔ | a label cut off in any state, raw TeX left visible, a formula MathJax cannot render | `check.py` |
| ⛔ | derivation steps that stay hidden, page overflow at 1280 or 390 px, content under the sidebar, a page that does not boot within 15 s | `check.py` |
| ⛔ | wording errors in the chosen mode (see [Wording](#wording-of-research-texts-d3-scientific-wording)) | `check_wording.py --genre explainer [--ste]` |
| ⚙️ **automatic** | equations pulled from the `.tex` with their numbers; code excerpts and data pulled from the repo | `build.py` |
| ⚙️ | one offline file: fonts, MathJax, JSON and images embedded (PDFs rasterized) | `build.py` |
| ⚙️ | section and figure numbers, contents, reading time, notation drawer, role colours in formulas and plots, build date and commit (marked when uncommitted changes exist) | `build.py`, `explainer.js` |
| ⚙️ | GitHub permalinks at the built commit when the remote is on GitHub | `build.py` (`code_links`) |
| ⚙️ | reviewer packets with the evidence for every pointer | `build.py` |
| ⚙️ | flags main-line words above 1.15 × the depth budget and more interactive figures than the budget | `build.py` |
| ⚙️ | flags captions without Try or Notice, hand-typed "Eq. (7)" or "Figure 3", `Math.random()`, a missing notation table, dashes and marker words, role colours that colour-blind readers cannot tell apart | `build.py` |
| ⚙️ | flags curves that use under 6 % of the panel height, overlapping labels, more than four parameters, a Reset that does not restore, steps without a reason, text under 7 px on a phone | `check.py` |
| ⚙️ | every figure gets Reset, keyboard controls, a legend and a hover readout; toys get a badge | `explainer.js` |
| 📖 **guides** | the brief is approved before any HTML; every figure has a knob→insight sentence | `SKILL.md` |
| 📖 | every derivation, number and claim about prior work carries a pointer or `[[reading]]`; nothing invented | `SKILL.md` |
| 📖 | intuition first: plain sentence, figure, formal statement, derivation, code | `references/content-design.md` |
| 📖 | the gap as strands (what each established, where it stops), in a neutral tone | `references/content-design.md` |
| 📖 | an honest inventory: paper versus code and result files, assumptions, open questions; if empty, what was compared | `references/content-design.md` |
| 📖 | figure numbers from result files first, then `make_data.py`, then declared toys; defaults at the paper's setting | `references/visualization.md` |
| 📖 | personal identifiers dropped or relabelled before data is embedded | `SKILL.md` |
| 📖 | reading on a token budget; an `Explore` subagent for large code bases | `references/scanning.md` |
| 📖 | reviewers read-only, at most 12 findings each; blockers and majors verified before they are applied | `references/review.md` |
| 📖 | commit (without `review/`) and the vault copy only on a yes | `SKILL.md` |

</details>

## Wording of research texts (d3-scientific-wording)

`d3-scientific-wording` decides how the sentences of a research text are phrased. The calling skill or the user owns the
content, the structure and the layout; this skill owns the wording. The goal is text that reads as written by a
researcher of the group. Such text states what was done and found, describes other work by what it did, claims what the
evidence carries, and keeps each sentence to one idea. All wording rules live in this one skill. d3-abstract, d3-poster,
d3-presentation and d3-explainer invoke it before they write text; d3-marimo and d3-server-use do not call it. Every D3
plugin ships the whole `skills/` folder, so the wording skill is always on disk next to the skill that calls it. Install
it as a plugin of its own to use it for papers, rebuttals, proposals or any other text.

<details>
<summary><b>In detail:</b> What the skill contains · Who calls it, and when · A text, step by step · The rules, one example per family · The wording brief · Corpus profiles · Simplified Technical English and the sentence caps · What is checked, and how</summary>

### What the skill contains

```
skills/d3-scientific-wording/
├── SKILL.md                         two ways in · brief · profile · write · adapt · check · revise · clean marks
├── references/
│   ├── rules.md                     the rules in 11 sections, each with its reason and before/after pairs
│   ├── outlets.md                   detection signals · genre profiles and caps · readers · term sheet · spelling
│   ├── outlets/                     one file per outlet family; only the one the brief names is read
│   │   ├── or-ms.md                 operations research, management science (Operations Research, EJOR, M&SOM)
│   │   ├── information-systems.md   information systems (ICIS, ECIS, WI, MISQ, ISR, BISE)
│   │   ├── machine-learning.md      machine learning (NeurIPS, ICML, ICLR, AAAI, JMLR, KDD)
│   │   ├── economics.md             economics, energy economics, econometrics (Energy Economics, The Energy Journal)
│   │   ├── energy.md                power systems and energy (IEEE Transactions, PES General Meeting, Applied Energy)
│   │   ├── nature.md                Nature-family journals (Nature, Nature Energy, Nature Communications)
│   │   ├── game-theory-and-games.md game theory and games research (Games and Economic Behavior, CHI PLAY)
│   │   ├── sports-science.md        sports science (Journal of Sports Sciences, sports analytics venues)
│   │   └── german.md                German-language outlets and occasions (WI in German, talks, teaching)
│   ├── ste.md                       Simplified Technical English (ASD-STE100) writing rules, adapted to research
│   └── profiles.md                  measured wording profiles: kinds, sources, corpus size, precedence, integrity
├── scripts/
│   ├── check_wording.py             lint for .tex, .html, .md, .txt and slides.py (standard library only)
│   └── wording_profile.py           list · measure · compare a corpus of PDFs, .tex, .md, .txt, .html (PyMuPDF)
└── evals/                           9 test prompts with input files and assertions: EJOR, NeurIPS and Energy
                                     Economics revisions, ICIS and Nature Energy abstracts from notes, a game-theory
                                     model section, an STE explainer section, an STE poster box, German slides;
                                     grade.py scores a skill-creator run of them with the lint
```

### Who calls it, and when

```
 caller            genre       brief in              lint: uv run <wording-dir>/scripts/check_wording.py ...
 d3-abstract       abstract    progress.md           v1_abstract.tex --genre abstract
 d3-poster         poster      progress.md           poster.tex --genre poster
 d3-presentation   slides      storyline.md          <name>/slides.py   (or <name>/<name>.tex)
 d3-explainer      explainer   explainer/brief.md    explainer/sections/*.html --genre explainer --ste   (ste mode)
        │
        ▼ invoke before the first text (Skill tool; if not listed, read <wording-dir>/SKILL.md)
 ┌───────────────────────────────────────────────────────────────────────────────────────────────┐
 │ question round   the caller's own round takes the open wording fields; the profile offer goes │
 │                  into its enrichment question where it has one; no second round               │
 │ write            rules.md before the first paragraph · ste.md in STE mode                     │
 │ lint             in the caller's verification step, on the sources                            │
 │ reviewer         the caller's content reviewer: cold read first, the rules as wording rubric  │
 │                  (review depth standard or full; at light the writer's own pass stands)       │
 │ delivery         the watermark question, once, in the caller's delivery message               │
 └───────────────────────────────────────────────────────────────────────────────────────────────┘
        ▲
        │ the same steps, run by the skill itself, with its own question round
 standalone: papers · rebuttals · proposals · thesis chapters · any research text
```

`<wording-dir>` is `<skill-dir>/../d3-scientific-wording`. Where the caller's genre conventions govern form (action
titles, verb-first poster bullets, Try/Notice captions, emphasis limits), the caller decides the form and this skill
decides the wording. Called by another skill, it adds no reviewer agent; used on its own, it has its own review depths
(see [Review depth](#review-depth-how-many-tokens-a-run-spends)).

### A text, step by step

Every text starts with a wording brief. The skill reads as many fields as it can from the sources and asks only for the
rest. The brief, the term sheet and the user's corrections go under a `## Wording` heading in the project's notes file
(`storyline.md`, `brief.md` or `progress.md`; standalone, `wording.md` next to the document).

```
 ①read ──────▶ ②ask ───────▶ ③profile ───▶ ④write ─────▶ ⑤lint ──────▶ ⑥compare ───▶ ⑦cold read ─▶ ⑧clean
   │             │             │             │             │             │             │             │
 template,     brief in one  optional:     rules.md      check_wording optional:     a reader with optional, at
 call, .bib,   line; open    list, then    first;        on the first  draft next    only the text delivery: one
 notes file,   fields in one measure       family file;  draft and the to the corpus lists claims  question; on a
 code imports  message;      (author,      term sheet    final text;   bands and     that do not   yes, sources
               ## Wording    outlet or     above one     then the own  terms         follow        only
                             topic)        page          pass
```

**Revising a text the user wrote.** A style edit keeps the content: no claim, example or hedge is added, and nothing
is dropped to satisfy a rule. Wording the user chose on purpose stays, and a rule it breaks is flagged. Each comment
of the user is logged verbatim under `## Wording` → Corrections and applied wherever the same defect recurs. After two
rejected versions of one sentence, the skill asks which direction the author wants. `--source draft.md` confirms that
a revision keeps every number and citation and adds none; `--notes notes.md` does the same for a text drafted from
notes.

**Removing invisible AI marks.** The lint's `invisible` findings show whether there is anything to remove. The
delivery message asks once, and the clean-up runs only on a yes: on the sources (`.tex`, `slides.py`, the explainer's
section files, `.md`), followed by a rebuild and the checks. It uses the deterministic layer of the third-party plugin
[watermarks-remover](https://github.com/guillaumemeyer/watermarks-remover) (MIT), which the user installs; the skill
never installs it. Cleaning changes nothing about disclosure: when a venue asks authors to declare AI assistance, the
declaration still applies.

### The rules, one example per family

`references/rules.md` gives every rule its reason, because a reason decides the cases no table covers. `SKILL.md`
condenses the rules into eight core rules. The lint catches the countable part; the rest is judgment.

| Core rule | Before | After | Lint label |
|---|---|---|---|
| 1 State the claim directly | "Our method is not a heuristic but an exact algorithm." | "Our method is an exact algorithm." | `contrast` |
| 2 Report related work neutrally | "The seminal work of Smith [3] overlooks delayed feedback." | "Smith [3] studies immediate feedback. We study delays of up to 7 days." | `related-work` |
| 3 Claim what the evidence carries | "dramatically improves performance" | "lowers regret by 31 % on 24 months of market data" | `overclaim`, `hedge` |
| 4 Keep sentences short | "The estimator, which reweights logged actions by their propensities, which are estimated from the logging policy, is unbiased if these are correct." | "The estimator reweights logged actions by their propensities. We estimate the propensities from the logging policy. If the estimates are correct, the estimator is unbiased." | `length` |
| 5 Be concise and scientific | "perform an analysis of", "leverage" | "analyze", "use" | `filler`, `marker` |
| 6 Sound like the researcher | "In today's rapidly evolving world" | "Battery operators schedule on day-ahead forecasts, and forecast errors become dispatch costs." | `dash`, `marker`, `opener`, `connectives`, `rhetorical`, `contraction`, `emoji` |
| 7 One term per concept | "approach", "framework", "method" and "pipeline" in turn for one thing | one term from the term sheet, defined once and repeated verbatim | own pass; `compare` lists spelling variants against a profile |
| 8 Say what does what | "the agent acquires more" | "the agent's permissions expand" | own pass, cold read |

Sections 9 and 10 of `rules.md` cover paragraphs, openings and endings, and numbers, figures and citations. Words with
an established technical meaning stay: the lint skips "doubly robust", "robust optimization", "naive Bayes", "key
performance indicators", "statistically significant", "loss landscape" and similar terms.

The rules merge the house rules of d3-abstract, d3-poster, d3-presentation and d3-explainer with the academic-voice
skill of a group colleague, which was built from many rounds of line-by-line corrections. From it come the
processing-load rules, terminology discipline and the scope rules for revisions. Where the two disagreed, the house
rule holds: a thesis is stated directly, and a contrast becomes two sentences.

### The wording brief: outlet, field and reader

```
 signals, read first                           brief       what it sets
 the request · the calling skill        ─────▶ genre       form and sentence cap (paper, abstract, poster, ...)
 \documentclass, .sty, \journal{} ·     ─────▶ outlet      reviewers' expectations · citation form · person · limits ·
   the call for papers · storyline.md                      anonymity (own earlier work in the third person)
 keywords · venues in the .bib · imports ────▶ field       the one family file in references/outlets/
 outlet and genre · storyline.md        ─────▶ reader      what gets defined · examples · notation in running text
 babel option · the existing text       ─────▶ language    US or UK English, or German · one variant per document
 the caller's default · the user        ─────▶ mode        standard, or Simplified Technical English (ste.md)
 a named literature folder, vault or    ─────▶ profile     none (default) · author · outlet · topic
   NotebookLM notebook
                                                  │
                                                  ▼
          brief stated in one line ─▶ open fields asked in one message ─▶ recorded under ## Wording
          example: "Wording: paper for EJOR, OR, experts, US English, standard mode."
          batch run: the field's journal norm · experts of the field · US English · standard mode (as defaults)

 when sources disagree, the higher one wins
   1  the user's stated corrections and the text they wrote or approved
   2  the d3 error rules: direct claims · no dashes · neutral related work · claims within the evidence · caps
   3  a measured profile: targets, vocabulary, conventions (it can turn a warning into an accepted convention)
   4  outlets.md and the family files, and the defaults
   a call for papers or a guide to authors wins over outlets.md; a template is strong evidence, an import weak
```

The outlet sets what its reviewers expect. ML venues expect an enumerated contribution list, IS a contribution to theory
and a research model, OR/MS a formal model with managerial insights. Economics puts identification before estimates,
energy states system boundaries and units, and Nature writes for the broad reader with "Here we show". The outlet also
sets citation form, person, length limits and anonymity. The topic sets the vocabulary. Terms, notation and
abbreviations come from the user's sources (the paper, its `.bib`, the notation table), never from memory alone.
Documents longer than a page keep a term sheet under `## Wording`: concept, term, the synonyms it replaces, where it is
defined. When the sources use two terms for one thing, the skill asks which one stays.

### Corpus profiles: measured, then compared

```
 corpus (PDF · .tex · .md · .txt · .html)   kind      --match on              gives
 the user's own papers               ─────▶ author    the user's surname      voice: length, stance, habits
 papers of the target venue          ─────▶ outlet    the journal name        register, person, rhetorical moves
 papers on the topic, any venue      ─────▶ topic     nothing (curated)       dominant terms, spellings, abbreviations
                    │
                    ▼ list <folder> [--match]      words, year and venue hint per file (above --limit 80: by folder)
                    ▼ measure <folder> --kind ... --name ... --match ... --out <project>/wording-profile-<name>
 ┌──────────────────────────────────────────────────────────────────────────────────────────────────┐
 │ wording-profile-<name>.md (read once) and .json (for compare), next to the project's notes file  │
 │ per metric: pooled value and the band p25 · median · p75 across documents (3 documents or more)  │
 │ evidence: solid 5+ documents and 20,000 words · usable 3+ and 10,000 · else weak (anecdotes)     │
 │ counts, term lists, excerpts of at most 25 words with their file; never full texts               │
 └──────────────────────────────────────────────────────────────────────────────────────────────────┘
                    │
                    ▼ compare <profile>.json <draft files>
   each metric of the draft against the band: above · in band · below
   below on passives, nominalizations, dashes, boosters, long sentences or questions: fine for the D3 rules
   terms: where the draft uses a form the corpus does not prefer · long forms the corpus abbreviates
```

`measure` reads the body text (running headers removed; captions, tables and the reference list dropped) and skips
documents with fewer than 10 sentences of it. It counts sentence length, hedges, boosters, person, passives,
nominalizations, punctuation and questions, and lists openers, connectives, recurring formulations, terms, spelling
variants, abbreviations and rhetorical moves with short exemplars. A profile adjusts targets and vocabulary. It never
overrides an error-level rule, and its exemplars are never copied into the user's text. The profile question is asked
only when a corpus source was found or named, with its cost (about a minute of counting, about 3k tokens to read the
profile); the skill never searches the home folder. NotebookLM sources are measured after the `notebooklm-import`
skill has put them into the vault.

### Simplified Technical English and the sentence caps

| Skill | Simplified Technical English (ASD-STE100) |
|---|---|
| d3-explainer | default; say "normal wording" or "no STE" to switch it off |
| d3-presentation, d3-poster | offered in the question round, off by default |
| d3-abstract, papers and other texts | on request |

```
 sentence caps of the lint      standard mode                 STE mode (--ste)
 (warning above · error above)
 paper, rebuttal                35 · 45                       20 · 25
 abstract, explainer            30 · 40                       20 · 25
 speaker notes (notes=)         30 · 40                       20 · 25
 poster                         25 · 35                       20 · 25
 slides                         20 · 30                       15 · 20

 STE adds   errors: semicolons (outside author-year citations) · contractions
            warnings: Latin abbreviations · phrasal verbs · passive constructions · paragraphs over six sentences
 own pass   noun clusters (at most three nouns) · -ing forms only in technical names · one meaning per word
 kept       mathematical register · definitions of record · established terms · citation style · hedging
```

The mode applies the writing rules of ASD-STE100 (Issue 9, January 2025), paraphrased for research text. It does not
include the approved dictionary; the plain-word list in `ste.md` is the group's own. Technical nouns and verbs of the
field (estimator, regret, propensity; estimate, regress, bootstrap) count as technical only in their technical sense.
STE exists only for English, so German text follows the genre's caps. With `--ste`, the lint applies no STE check to
German text and says so in its header.

### What is checked, and how

| | Rule | Where |
|---|---|---|
| ⛔ **fails** | contrast framing: "not only", "not ... but", ", not X", "it is not about" | `check_wording.py` (`contrast`) |
| ⛔ | related-work grades: "fails to", "suffers from", "overlooks", "falls short", "merely", "unlike previous", "existing methods cannot", "seminal", "a valuable first step", "laid the groundwork" | `check_wording.py` (`related-work`) |
| ⛔ | hype and certainty words: "unprecedented", "breakthrough", "paradigm shift", "obviously", "it is clear that" | `check_wording.py` (`overclaim`) |
| ⛔ | filler: "it is important to note", "in order to", "due to the fact that", "plays a crucial role", "it can be seen that" | `check_wording.py` (`filler`) |
| ⛔ | marker vocabulary: delve, leverage, utilize, harness, showcase, underscore, pivotal, seamless, comprehensive, ... | `check_wording.py` (`marker`) |
| ⛔ | dashes as punctuation: em-dash, `---`, spaced en-dash or `--` (ranges such as `2024--2026` stay); emoji | `check_wording.py` (`dash`, `emoji`) |
| ⛔ | a sentence more than 10 words above the genre's warning cap (STE: above 25, on slides above 20) | `check_wording.py` (`length`) |
| ⛔ | in STE mode: semicolons outside citations, contractions | `check_wording.py --ste` |
| ⛔ | a revision that drops or adds a number or citation; a text from notes that adds one | `--source FILE`, `--notes FILE` |
| ⛔ | German: "nicht nur", "nicht ... sondern", "scheitern", "bahnbrechend", "es ist wichtig", "nahtlos", "ganzheitlich" | `check_wording.py`, language detected or `--lang de` |
| ⚠️ **warns** | "rather than", "instead of", "goes beyond"; "while prior ...", "naive", "simply" | `contrast`, `related-work` warnings |
| ⚠️ | "novel", "the first", "state of the art", "significant" without a test, intensifiers, "outperform", "prove" | `overclaim` warnings |
| ⚠️ | stacked hedges ("may potentially", "seems to suggest"), "in terms of", roadmap sentences, "In conclusion," | `hedge`, `filler` warnings |
| ⚠️ | "intricate", "nuanced", "landscape", "foster", "key", "robust" outside technical terms; "The result?" hooks; contractions; dingbats | `marker`, `rhetorical`, `contraction`, `dingbat` warnings |
| ⚠️ | sentence above the genre cap; three sentences in a row with the same opener; two additive connectives in one paragraph | `length`, `opener`, `connectives` |
| ⚠️ | invisible characters (zero-width, bidi controls, tag characters, soft hyphens, unusual spaces) with count and lines | `invisible` |
| ⚠️ | in STE mode: Latin abbreviations, phrasal verbs, passive constructions, paragraphs over six sentences | `check_wording.py --ste` |
| ⚙️ **automatic** | markup, math, code and comments blanked; a formula counts as one word; line numbers of the original file | `check_wording.py` |
| ⚙️ | genre detected per file (Beamer or `slides.py`: slides, baposter: poster, `d3-abstract`: abstract, explainer sections: explainer, "rebuttal" or "response" in the name: rebuttal, else paper); language detected | `check_wording.py`, override with `--genre`, `--lang` |
| ⚙️ | `notes=` strings in `slides.py` checked as speaker notes; prose attributes of HTML (`data-why`, `alt`, `title`, ...) checked | `check_wording.py` |
| ⚙️ | established technical terms skipped ("doubly robust", "naive Bayes", "statistically significant", ...) | `check_wording.py` |
| ⚙️ | numbers (number words, thousands separators, German decimal comma normalized) and citations (`\cite` keys, explainer chips, `[n]`, author-year) compared with the original | `--source`, `--notes` |
| ⚙️ | exit code 0 without errors, 1 with an error, 2 on a usage error; `--errors-only` hides warnings | `check_wording.py` |
| ⚙️ | body text of PDFs extracted, bands and evidence level computed, house-rule hits of the corpus counted | `wording_profile.py measure` |
| ⚙️ | draft metrics against the corpus bands; term and abbreviation differences | `wording_profile.py compare` |
| 📖 **guides** | the brief: detect first, ask the rest in one message, record under `## Wording` | `SKILL.md`, Step 1 |
| 📖 | lint twice (first full draft, final text); every warning decided: fixed, or kept for a stated reason | `SKILL.md`, Step 4 |
| 📖 | claims against evidence (verb ladder, causal words only for causal designs), one term per concept, premises on the page | `references/rules.md`, own pass |
| 📖 | the cold read: a reader with only the text lists claims that do not follow and terms used before they are explained | caller's content reviewer; standalone a read-only agent |
| 📖 | outlet conventions: contribution form, citation form, person, anonymity | `references/outlets/<family>.md` |
| 📖 | term sheet for documents longer than a page | `references/outlets.md` |
| 📖 | revisions keep the content and the user's approved wording; corrections logged and applied where they recur | `SKILL.md` |
| 📖 | STE parts the lint cannot count: noun clusters, "-ing" forms, one meaning per word | `references/ste.md` |
| 📖 | profiles: never copy corpus sentences; errors stay errors; bands are document-level | `references/profiles.md` |
| 📖 | AI-mark clean-up: asked once, on sources, deterministic layer only, plugin installed by the user | `SKILL.md`, Step 5 |

</details>

## Teaching apps in the browser (d3-marimo)

`d3-marimo` builds interactive teaching apps as marimo notebooks that run in the student's browser through WebAssembly
(Pyodide). Students open a link: no install, no account, no server. The apps live in the `apps/` folder of the chair's
website repository (`academic-website`, remote `chrisflath/chrisflath.github.io`), which exports and deploys them on
every push to `main`. The skill ports Colab, Jupyter and molab notebooks and moves PuLP models to SciPy's HiGHS solver.
Every app gets the University of Würzburg look without D3 branding (see [Design](#design)). A headless browser checks
each app locally and again after the deploy. Four rules hold for every app:

- the port reproduces the original's numbers before any UI is written;
- every number in the app is reproducible;
- a competition app does not ship its solution;
- the app offers the switch that shows the instructive failure, for example the LP relaxation next to the integer
  solution.

<details>
<summary><b>In detail:</b> What the skill contains · Where things run · First use · An app, step by step · From Colab or molab to marimo · The university look · The check · What is checked, and how</summary>

### What the skill contains

```
skills/d3-marimo/
├── SKILL.md                 workflow in 10 steps · rules for course apps · files
├── assets/
│   ├── app_template.py      app skeleton: masthead, slot for the style cell, data loader, sliders, HiGHS, footer
│   ├── uw.css               the look: Inclusive Sans UW, university palette on marimo's theme variables, masthead
│   ├── uw-logo-navy.png     university logo for the masthead (960 × 283 px)
│   └── inline_uw_css.py     copies uw.css into a style cell of every app that uses it (runs in <site>)
├── scripts/
│   └── check_app.py         native run, WASM export, headless Chromium check, optional live check
└── references/
    └── pitfalls.md          what broke in WASM and in notebook ports (DSS apps, October 2026), with the fix
```

### Where things run

```
  LAPTOP                          WEBSITE REPO <site>                   STUDENT BROWSER
  (Claude Code, uv)               academic-website                      (Pyodide, nothing installed)
 ┌─────────────────────────┐ push ┌──────────────────────────────┐ link ┌──────────────────────────────┐
 │ apps/<app>.py           │─────▶│ GitHub Actions, about 2 min  │─────▶│ apps/<app>.html              │
 │ marimo edit (css_file)  │ main │ scripts/build.py exports     │      │   numpy · scipy · pandas ·   │
 │ check_app.py            │      │   apps/*.py: run mode,       │      │   altair · pure-Python pkgs  │
 │   native · WASM · local │      │              code hidden     │      │   linprog, milp (HiGHS)      │
 │ inline_uw_css.py        │      │   notebooks/*.py: edit mode  │      │   data through open_url      │
 └─────────────────────────┘      │ teaching_config.json lists   │      │   requests: simple GETs      │
              ▲                   │   the apps per course        │      └──────────────┬───────────────┘
              │                   └──────────────────────────────┘                     │
              └─── check_app.py --live https://chrisflath.github.io/apps/<app>.html ───┘

  cannot run in the browser:   PuLP's CBC binary · Gurobi · OR-Tools
  ignored by the WASM export:  css_file="uw.css" (a generated style cell carries the look)
  failed on GitHub Pages:      pd.read_csv(url) (load_csv uses pyodide.http.open_url)
```

### First use: the website and three questions

The skill ships the shared files; the website keeps its own copies. There is no fixed question round: the skill asks
three things when they come up.

```
 SKILL (<skill-dir>)                         WEBSITE (<site>)
 assets/uw.css             ── copy ──▶   apps/uw.css                    the look, edited here only
 assets/uw-logo-navy.png   ── copy ──▶   apps/public/uw-logo-navy.png   masthead logo
 assets/inline_uw_css.py   ── copy ──▶   scripts/inline_uw_css.py       run from <site>
 assets/app_template.py    ── cp ────▶   apps/<course>-<topic>.py       one per app
                                         apps/public/fonts/             Inclusive Sans UW (OFL), the same
                                                                        files as d3-presentation's assets/fonts/

 ASKS   where is <site>?           only if the path is not obvious
        a bug in the original?     fix silently · fix visibly (often the better lesson) · keep as the default
        first push of a new app?   pushing publishes; names unrelated local commits that would go out with it
 ONCE   uv run --with playwright playwright install chromium        before the first check on a machine
```

### An app, step by step

Every app starts from the source notebook, read in full: every cell and its outputs. The outputs are the reference
numbers the port must reproduce. Colab: `https://drive.google.com/uc?export=download&id=<file id>` returns the
`.ipynb` of a file shared by link. molab: append `.py` to the notebook URL.

```
 ①source ──▶ ②port ──▶ ③deps ──▶ ④template ──▶ ⑤data ──▶ ⑥look ──▶ ⑦check ──▶ ⑧list ──▶ ⑨deploy ──▶ ⑩slides
  │           │         │         │             │         │         │          │         │           │
 Colab or    model in  numpy,    cp to apps/,  public/   uw.css,   native,    entry in  ask, push   QR code
 molab;      Python,   scipy,    small cells,  data/,    inline_   WASM,      teaching  main,       from URL,
 all cells   HiGHS;    pandas,   UI apart      load_csv  uw_css    Chromium,  config,   --live      decodes
 + outputs   bugs      altair;                                     --expect   as text
                       no CBC
```

### From Colab or molab to marimo

```
 NOTEBOOK                            MARIMO APP                                        WHY
 PuLP model, CBC solver         ──▶  linprog(..., method="highs") for LPs              CBC cannot run in Pyodide;
                                     milp(..., integrality=...) for integer programs   results matched PuLP
 pd.read_csv(url)               ──▶  load_csv(name): open_url in the browser,          failed on GitHub Pages
                                     a plain path locally                              (compressed responses)
 cell structure                 ──▶  one idea per cell · UI in its own cell,
                                     results in the next
 a name defined in two cells    ──▶  prefix cell-local names with _                    marimo forbids it
 mo.md(f"... $e_{pd}$ ...")     ──▶  mo.md(f"## {icon} Title\n" "$e_{pd}$ ...")        {pd} is formatted as Python
 np.fill_diagonal(df.values, 1) ──▶  work on df.to_numpy().copy()                      read-only under copy-on-write
 printed outputs                ──▶  the numbers the port reproduces natively,
                                     before any UI is written

 CHECK THE MODEL ITSELF    each bug: fix silently · fix visibly · keep as the default, decided with the user
   no cat="Integer" / LpBinary       LP relaxation reported as the answer ("6.5 passports")
   positional diagonal               rows and columns in different orders: index by label, df.loc[p, p]
   "everything except X counts"      categories listed explicitly, or chosen by students (mo.ui.multiselect)
   mg and g in one objective         a normalised objective (each term divided by its limit) next to the original
   objective under "Total cost"      re-derive every printed quantity
```

### The university look: one stylesheet, two routes

marimo's `html-wasm` export copies `css_file` but never loads it. The look therefore reaches the app twice: through
`css_file` for local editing, and through a generated style cell for the export.

```
                                   ┌──▶ css_file="uw.css" in marimo.App(...) ──▶ read by marimo edit on the laptop
 <site>/apps/uw.css ───────────────┤
 (edit only this file)             └──▶ uv run scripts/inline_uw_css.py, run in <site>
                                        └ writes the cell _uw_style (code hidden) after the import cell of every
                                          app in apps/ with css_file="uw.css", replacing the old one ──▶ WASM export

 ┌───────────────────────────────────────────────────────────────────────────┐
 │ [university logo, 52 px high]                   DECISION SUPPORT SYSTEMS │  course name: berry, uppercase
 ├───────────────────────────────────────────────────────────────────────────┤  grey rule #D3D6DC
 │ The Toy Factory                                                          │  h1: navy, bold
 │ ... which product mix maximizes the weekly profit?                       │  bold text: navy
 │ ──────────────────────────────────────────────────────────────────────── │  h2 opens with a grey rule
 │ ● Your assumptions                                                       │  ● one lucide icon, coral
 │   Soldiers we can sell ──●── 40      Finishing hours ──●── 100           │  sliders: navy
 │ ──────────────────────────────────────────────────────────────────────── │
 │ ● The best plan                                                          │
 │   weekly profit · soldiers / trains · bar chart                          │  bars: navy
 │ ──────────────────────────────────────────────────────────────────────── │
 │ Solved in your browser with SciPy's HiGHS solver.                        │  footer
 └───────────────────────────────────────────────────────────────────────────┘
  font    Inclusive Sans UW (regular, italic, medium, semibold, bold) from apps/public/fonts/
  navy    #02246C  headings, bold text, controls, active tab, table headers
  coral   #ED6A5B  section icons, actions; left rule of quotes
  berry   #821044  masthead course name, kicker
  blue    #5E8AC7  links, focus ring
  sand    #F1EBDF  quote background
  tabs and tables sit in a shadow DOM: only the theme variables reach them,
  and a heading inside mo.ui.tabs takes an inline style
```

### The check: local, then live

```
 uv run --with playwright <skill-dir>/scripts/check_app.py <site>/apps/<app>.py --expect "<text>"
        [--click <role:name>] [--expect-after "<text>"] [--timeout <seconds>]
   ① native run          uvx --with <deps from # /// script> marimo export html: every cell must run
   ② WASM export         marimo export html-wasm --mode run --no-show-code; apps/public/ copied next to it
   ③ local server        127.0.0.1 on a free port, the page under /apps/<app>.html as on the website
   ④ headless Chromium   1300 × 1400 px; each --expect visible within --timeout (180 s) ──▶ --click ──▶
                         --expect-after (a 3 s pause after each click)
   ⑤ report              console errors · computed h1 font · CHECK PASSED or CHECK FAILED (exit 0 or 1)

 uv run --with playwright check_app.py --live https://chrisflath.github.io/apps/<app>.html --expect "<text>"
   skips ①–③ and runs ④ and ⑤ on the deployed page, once the deploy has finished
```

### What is checked, and how

The skill defines no reviewer agents and no review depth. Its automated part is `check_app.py`; the rest are rules
in `SKILL.md` and `references/pitfalls.md`.

| | Rule | Where |
|---|---|---|
| ⛔ **fails** | a cell fails in the native run (`marimo export html` reports failed cells or exits non-zero) | `check_app.py` (local) |
| ⛔ | the WASM export does not complete (the script stops with an error) | `check_app.py` (local) |
| ⛔ | an `--expect` text is not visible within `--timeout` seconds (default 180) | `check_app.py` |
| ⛔ | an `--expect-after` text is not visible after the `--click` steps | `check_app.py` |
| ⛔ | no `--expect` given, since a page that never renders would pass (usage error, exit 2) | `check_app.py` |
| ⛔ | any console error in the page | `check_app.py` |
| ⚙️ **automatic** | dependencies of the native run read from the app's `# /// script` block | `check_app.py` |
| ⚙️ | export in run mode with code hidden, `public/` copied, served on localhost | `check_app.py` |
| ⚙️ | `--click` by role and name for `tab:`, `button:`, `switch:`, `checkbox:`, `radio:`, else by text; 3 s pause after each click | `check_app.py` |
| ⚙️ | reports the computed heading font and points to `inline_uw_css.py` if Inclusive Sans UW is missing (a hint, no failure) | `check_app.py` |
| ⚙️ | the style cell `_uw_style` (code hidden) in every app with `css_file="uw.css"`, regenerated from `uw.css` | `inline_uw_css.py` |
| ⚙️ | WASM export of `apps/` (run mode, code hidden) and `notebooks/` (edit mode), deploy on every push to `main` | `<site>/scripts/build.py`, GitHub Actions |
| 📖 **guides** | the original's numbers reproduced in plain Python with the browser solver before any UI; the app's numbers compared with them | `SKILL.md` |
| 📖 | browser-safe packages only: SciPy HiGHS (`linprog`, `milp`) for PuLP models; no CBC, Gurobi, OR-Tools | `SKILL.md`, pitfalls |
| 📖 | each bug of the original fixed silently, fixed visibly or kept as the default, decided with the user | `SKILL.md`, pitfalls |
| 📖 | data in `apps/public/data/`, loaded with `load_csv`; source, date and licence stated in the app | `SKILL.md`, template |
| 📖 | small cells (one idea each, UI apart from results), `_` for cell-local names, LaTeX outside f-strings | `SKILL.md`, pitfalls |
| 📖 | a light look: theme variables, one coral icon per section heading, no further reskinning | `SKILL.md` |
| 📖 | `teaching_config.json` edited as text, never re-serialised | `SKILL.md` |
| 📖 | asks before the first push of a new app, names unrelated local commits; `--live` check after every deploy | `SKILL.md`, pitfalls |
| 📖 | competition apps show the student's own result only: no optimum, no "reveal optimum" button, no third-party leaderboard | `SKILL.md`, pitfalls |
| 📖 | every number reproducible (data source and date, solver checks in a comment); illustrative data labelled, fictional names | `SKILL.md` |
| 📖 | the switch that shows the instructive failure (LP relaxation vs integer, greedy vs optimal, raw vs weighted objective) | `SKILL.md` |
| 📖 | QR code on slides generated from the URL at build time and checked to decode from the rendered slide | `SKILL.md` |

</details>

## Running jobs on the group server (d3-server-use)

`d3-server-use` is the group's way of running compute jobs on the KiRegio Slurm server: Slurm for everything that
computes, uv only, jobs that survive the 24 h limit, a run ID for every run, fair use of the 4 GPUs, and a store
outside the small server home through which data travels between laptop and server. Server addresses and the user's
answers live in a local site file (`~/.config/d3-server/site.toml`), never in this repository.

<details>
<summary><b>In detail:</b> What the skill contains · Where things run, and who writes what · First use · A round, step by step · Run IDs · Splitting a round, and how wide each job is · One run as a chain of segments · Fair use · Storage · Experiment tracking, where a project uses it · What is enforced, and how</summary>

### What the skill contains

```
skills/d3-server-use/
├── SKILL.md                 quick submit or full setup · first use · rules · the full setup in 9 steps
├── scripts/
│   ├── d3run.py             login host: run IDs, registry, submit, fair use, sizing, S3, verified cleanup
│   ├── d3job.py             inside the job: end time, stop margin, checkpoints, resume, MLflow/W&B run
│   ├── d3track.py           login host: the runs' MLflow stores into the project's store, upload
│   └── check_sbatch.py      lint for hand-written job scripts
├── assets/
│   ├── job_template.sbatch  job clock, USR1 trap, GPU memory log, uv run --no-sync
│   ├── push_inputs.sh       the server's inputs from the laptop: into the bucket, or by rsync without one
│   └── site.example.toml    template of the user's local site file (no secrets)
├── references/              first-time setup · cluster · splitting and sizing · interruptible jobs
│                            data and storage · registry · tracking · alerts · pitfalls
└── evals/                   test prompts, toy projects, tests for the scripts (evals/tests, laptop only)
```

### Where things run, and who writes what

```
  LAPTOP                         LOGIN HOST                      COMPUTE NODE
  (Claude Code)                  (light commands only)           (Slurm jobs only)
 ┌──────────────────┐   ssh     ┌──────────────────────┐ sbatch ┌──────────────────────┐
 │ site.toml        │──────────▶│ git pull, uv sync    │───────▶│ job_template.sbatch  │
 │ ~/.ssh/config    │  <alias>  │ d3run.py             │        │  uv run --no-sync    │
 │ ~/.aws (yours)   │           │  └ registry.db       │◀───────│  your code + d3job   │
 │ push_inputs.sh   │           │    (only writer)     │ status │  └ runs/<id>/...     │
 └───┬──────────▲───┘           └──────────┬───────────┘  .json └──────────┬───────────┘
     │ inputs   │ results                  │ archive · push · pull         │ checkpoints, results
     │          │                          │ (verified)                    │ (uploaded by d3job)
     ▼          │                          ▼                               ▼
 ┌─────────────────────────────────────────────────────────────────────────────────────┐
 │ the store: the S3 bucket; data travels through it, git carries code only            │
 │ without a bucket: your computer (rsync, then a verified manifest)                   │
 └─────────────────────────────────────────────────────────────────────────────────────┘
   inputs: jobs/push_inputs.sh (allowed folders only), then `d3run.py pull … --checksum` on the server
   results: from the bucket to the laptop with `aws s3 sync`
   without a bucket yet: the same script rsyncs the inputs into the checkout, and results come back by rsync
```

### First use: detect, then ask only what is missing

```
 site.toml has it? ──yes──▶ use it, ask nothing
        │ no
        ▼
 LOGIN    ask once ("e.g. abcd") ─────────────────────────────────────────────▶ save
 SSH      alias works? ──yes──▶ save
            │ no
            ▼ Host block for the server in ~/.ssh/config? ──yes──▶ test ──▶ save
            │ no
            ▼ guide (the user runs it): key pair · public key to admin · Host block · first login
 BUCKET   ask once ──┬── yes ─▶ look at the AWS CLI + ~/.aws/config (laptop, server)
                     │          ─▶ ask only for bucket / endpoint / profile ─▶ aws s3 ls ─▶ save
                     └── no ──▶ ask the admin for one; meanwhile your computer is the store (rsync)
 TRACKING per project: MLflow or W&B in the project? ──yes──▶ fit it · no ─▶ ask once: MLflow · W&B · none ─▶ save
```

### A round, step by step

A request to run work first picks one of two paths, from the message ("just submit", "like last time" or "get it
ready", "set it up") or by asking once, with a recommendation from what the project already has:

```
 quick submit   project set up (tools/d3run.py, job scripts, entry in the site file), code ready
                lint ─▶ commit, pull (nothing queued) ─▶ new ─▶ submit with the user's or the last round's flags
                no smoke test, pilot or sizing; switches to the full setup for a lint error, a job above 24 h
                without checkpoints, or more than ~500 queued jobs
 full setup     everything else: the nine steps below
```

The full setup starts by reading the repository the skill is invoked in (project rules, existing job scripts, an
existing orchestrator, checkpoint code, folder layout) and adapts to it; the skill itself holds nothing
project-specific.

```
 ①setup ─▶ ②plan ─▶ ③interruptible ─▶ ④deploy ─▶ ⑤smoke ─▶ ⑥pilot+size ─▶ ⑦submit ─▶ ⑧watch ─▶ ⑨archive+clean
   │          │          │                │          │            │              │           │          │
 read repo, cut at    d3job +           commit,    local run,   `scale` on    queue, new  reconcile  verified copy,
 clone,     phases,   check_sbatch      git pull   resume test, the laptop;   --tag; CPU  every 15+  then delete;
 uv sync,   units;                      (queue     server smoke first units,  part first; min        `usage`
 init       CPU/GPU                     empty)     first time   then `size`   fair use

 data with a bucket:   ④ inputs laptop ─▶ bucket ─▶ server (push_inputs.sh, pull --checksum) · ⑨ results ─▶ laptop
 without a bucket yet: ④ push_inputs.sh rsyncs the inputs into the checkout · ⑨ results come back by rsync
 queue full:           ⑤ the first server smoke on CPUs · the first real GPU jobs check the GPU in minutes
```

### Run IDs

```
   20261104 - abcd - lstm-s42 - 7c1e
   └──date─┘  └─┬─┘  └──slug──┘  └rand┘
   sorts by     │    readable    unique per day (collision check)
   time         └── never clashes between users

   Slurm job name:  lstm-s42-7c1e        (queue views cut long names)
   Slurm job ID:    only in `attempts`, with its submit time (IDs restart when the server is rebuilt)
   Run folder:      runs/<id>/   =   s3://<bucket>/<project>/runs/<id>/
```

### Splitting a round, and how wide each job is

Checkpoints let a job survive the 24 h limit; they do not make one job that does everything a good job on a shared
server that never preempts. A round is cut where the hardware changes, then between independent units, and each job
gets as many CPUs and GPUs as it keeps busy, chosen against the queue of the moment.

```
 before: one script, one GPU job, four days            after: one job per phase and unit
 ┌──────────────────────────────────────────┐          train+predict DE ─┐
 │ train · predict · 1,095 MILPs · evaluate │          train+predict FR ─┼─▶ solve × 36 ─────▶ evaluate
 │ the GPU idles through the solver hours   │          train+predict NL ─┘   CPU chunks        1 CPU job
 └──────────────────────────────────────────┘          1 GPU each            --after-tag       --after-tag

 width   `d3run.py scale -- <slice>` on the laptop: speed-up, efficiency ≥ 70 % ─▶ --cpus 8
         first units at that width ─▶ `size` on them ─▶ the rest; two widths on the server only past the laptop
         billing per second = max(CPUs, 0.266 × GB, 41.5 × GPUs): a job that scales costs the same and ends
         sooner; CPUs that its memory or GPU already pays for are free
 queue   `d3run.py queue` ─▶ nobody waits: wide and many · others wait: the share · busy for hours: what is free now
 limits  units under ~10 min bundled into chunks · fewer than ~500 queued jobs (MaxJobCount 10,000 for everyone)
```

### One run as a chain of segments

```
  ◆ checkpoint (first after 5 min, then every 30 min)    ○ USR1: end confirmed, 10 min before
  ■ stop: time left < 1.5 × (longest step + longest save) + 30 s           ┤ Slurm's limit

 seg 1  ●──◆─────◆─────◆── … ──◆──────○──────◆■┤
 seg 2                                          ●──◆─────◆── … ──○──────◆■┤    resumes from the last ◆
 seg 3                                                                     ●✓  finds "done", exits in seconds

  example: 2 s steps, 10 s save → stops about 48 s before the limit
  last ◆ too close to the end → stays on the server, the next segment uploads it first
```

### Fair use: all GPUs or CPUs only while nobody else waits

```
                       ┌────────────────────────────────────┐
  submit · feed ──────▶│ squeue: is anyone else waiting?    │   (Resources / Priority)
                       └─────────┬────────────────┬─────────┘
                          nobody │                │ someone
                                 ▼                ▼
                    cap = whole machine      cap = share
                    GPUs 4 · CPUs 150        GPUs 3 · CPUs 112
                                 └───────┬────────┘
                                         ▼
                 your running + startable jobs within the cap?
                       yes ─▶ submit normally · release held jobs (oldest first)
                       no  ─▶ new jobs: --hold · pending: held back (newest first)
                              running jobs: never touched (no preemption on this cluster)

  feed runs with every `reconcile`, or as a 1-CPU feeder job: `d3run.py feed --submit`
  share per project: `d3run.py init --share-gpus N --share-cpus N`
```

### Storage: the server is scratch

```
                       while the run is active                after cleanup (verified copy)
 runs/<id>/
   run.json, status.json   server (+ store)                   stay on the server (tiny)
   checkpoints/        server: newest 1 (2 without a bucket)   in the store only
                       S3: newest 2
   results/, logs/     server (results to S3 at finish)        in the store only
 data/raw, processed   pulled from S3 once per round          in the store only
 registry.db           server                                 daily snapshot in S3

 the store   S3 bucket   archive --clean · push --clean        each file verified by size and MD5 (ETag)
                         laptop: push_inputs.sh · aws s3 sync   inputs from allowed folders only
             no bucket   rsync to your computer                manifest with SHA-256 · clean --manifest
                         inputs: push_inputs.sh by rsync       the same allowed folders
             fallback    university share, NAS, own cloud      same manifest route (unrestricted data only)
             git         small text results for the repo       moves them, does not free server space
```

### Experiment tracking, where a project uses it: one MLflow store per run

Tracking is optional. The skill looks for MLflow or W&B in the project (dependencies, imports, existing stores) and
otherwise asks once whether the user wants it; the answer is kept per project in the site file, and nothing is
added without a yes. For a new setup MLflow is the recommendation, since it keeps everything on university
infrastructure; Weights & Biases suits users who already work with it, for data without restrictions. A training
run spans several 24 h jobs, and many jobs must not write one SQLite file on NFS, so every run logs into its own
store and only the login host writes the project's store. Since 2026-11-05 the group also runs an MLflow server on
the cluster: a project can log there instead (`ctx.mlflow(server=True)`, one MLflow run across the segments, one UI
for everyone, no sync); the skill asks once which store a project uses.

```
 job, segment 1 ─┐                                     login host                      laptop
 job, segment 2 ─┼─▶ runs/<id>/mlflow/mlflow.db ─────▶ d3track.py sync ───────────▶  MLflow UI
 job, segment 3 ─┘   one MLflow run, one writer        snapshot · new points only     uvx --from mlflow==<v>
                     SCHEDULED between segments,       runs/mlflow.db (one writer)      mlflow ui
                     FINISHED or FAILED at the end     ─▶ s3://<bucket>/<project>/mlflow/mlflow.db

 in the code:  ctx = RunContext.from_env(); ctx.mlflow(); mlflow.log_metric("loss", value, step=epoch)
 group server: ctx.mlflow(server=True)   experiment <login>/<project>, artifacts on the NAS, no d3track.py sync
 W&B instead:  ctx.wandb()   id = run ID, resume="allow"; compute nodes reach W&B (tested); unrestricted data only
```

### What is enforced, and how

| | Rule | Where |
|---|---|---|
| ⛔ **refuses** | `--time` above 24 h | `submit`, linter |
| ⛔ | `--partition=main` without a GPU, `cpu` with one | `submit`, linter |
| ⛔ | new runs from uncommitted tracked code (except `--allow-dirty`) | `new` |
| ⛔ | the same config and commit twice (except `--allow-duplicate`) | `new` |
| ⛔ | registry writes from inside a job (one writer) | all writing commands |
| ⛔ | transfers or deletions above 1 GB or 2,000 files on the login host (asks for `--submit`) | `archive`, `push`, `pull`, `clean` |
| ⛔ | deleting without a checksum-verified copy (`--size-only` only on request), while a run is active, or anything git tracks | `--clean`, `clean --manifest` |
| ⛔ | pip / conda / venv, `#SBATCH` after the first command, secrets in scripts | linter |
| ⛔ | sending an input outside the project's allowed folders (into the bucket or by rsync), a path with `..` or a symbolic link (data an agreement keeps on the laptop never matches) | `push_inputs.sh` |
| ⛔ | `d3track.py sync` inside a job (one writer for the project's MLflow store) | `d3track.py` |
| ⛔ | a GPU job tagged or named smoke while no GPU is free or others wait for one (except `--allow-gpu-smoke`) | `submit` |
| ⚙️ **automatic** | run ID before `sbatch`; commit, config hash and logs per run | `new`, `submit` |
| ⚙️ | fair-use hold and release | `submit`, `feed`, `reconcile` |
| ⚙️ | chained segments; later segments exit if the run is done or failed, also after two hard crashes in a row | `submit`, `d3job` |
| ⚙️ | measured stop margin, deferred uploads, resume from the server or S3 | `d3job` |
| ⚙️ | `--time` / `--mem` / `--cpus` / segments from measured usage; speed-up between two pilot widths; notes when more CPUs cost no extra fair share, when a pilot kept all its CPUs busy, when runs are too short | `size` |
| ⚙️ | a phase waits for the runs of the previous phase | `submit --after-tag` |
| ⚙️ | free CPUs and GPUs, who waits, when the GPUs free up, whether a separate GPU smoke may run | `queue` |
| ⚙️ | width measured on your own computer before the first jobs: time, speed-up, efficiency, peak memory per width | `scale` (refuses on the cluster) |
| ⚙️ | a warning above 500 queued jobs | `submit` |
| ⚙️ | flags finished jobs that would trigger the admin's alerts (CPUs below 60 %, GPU below 15 %) | `reconcile`, `size` |
| ⚙️ | one MLflow run across all segments, tags from `run.json`, status SCHEDULED, FINISHED or FAILED from the run's state | `d3job` (`ctx.mlflow()`) |
| ⚙️ | the project's MLflow store from snapshots of the runs' stores, only new points, uploaded to the bucket | `d3track.py sync` |
| 📖 **guides** | light commands only on the login host | `SKILL.md` |
| 📖 | quick submit for a project that is set up, full setup otherwise; asked once unless the message says which | `SKILL.md` |
| 📖 | every full setup: a local smoke test and local sizing (`scale`), the first units as the pilot, CPU part first; a server smoke only for a project's first run, and while the queue is full on CPUs, with the GPU checks in the first real GPU jobs | `SKILL.md`, splitting and sizing |
| 📖 | a round split at its hardware phases, then its units; each job as wide as it keeps busy, fitted to the queue | `SKILL.md`, splitting and sizing |
| 📖 | code that cannot save its state is never chained into segments; the ways out (fit into 24 h, the solver's time limit and best solution, libraries that continue, splitting the problem) are chosen with the user | `SKILL.md`, interruptible jobs |
| 📖 | never pull while a round is queued | `SKILL.md` |
| 📖 | one data route per project: with a bucket through it (inputs laptop → bucket → server, results job → bucket → laptop), without one by rsync; git carries code | `SKILL.md`, data and storage |
| 📖 | tracking only where the project uses it or the user says yes: detect in the project, else ask once; the answer is kept per project | `SKILL.md`, tracking |
| 📖 | no `mlflow.db` that all jobs write, no `mlflow server` on the login host, no checkpoints as artifacts; sync before `archive --clean` | `SKILL.md`, tracking |
| 📖 | ssh and S3 setup: detect first, the user handles keys | `SKILL.md`, setup guide |
| 📖 | explains alerts from the monitoring channel (home quota, idle GPU, unused CPUs) and fixes the cause | `references/alerts.md` |
| 📖 | clean up after each round and above about 50 GB; a restore drill and a bucket lifecycle check before the store is the only copy | `SKILL.md`, references |
| 📖 | no scans of the whole home, not even in a job; stop idle JupyterHub servers | `SKILL.md`, references |

</details>

## Versions and releasing

Each skill has its own version in `.claude-plugin/marketplace.json` (semantic versioning: patch for fixes, minor for new
capabilities, major for changes that break existing projects). Users receive an update only when that number changes, so
a release is: edit the skill, bump its `version` in the manifest and in the table above, run `claude plugin validate .`,
commit, push. Users then run `/plugin marketplace update d3-skills`. `d3-explainer` stays below 1.0.0 until it has been used on a few real projects.

## Requirements

- [uv](https://docs.astral.sh/uv/) for all Python (`uv run`; no pip, no global installs)
- A LaTeX distribution with XeLaTeX for d3-abstract, d3-poster and the Beamer route of d3-presentation
- Playwright's Chromium for the browser checks of HTML outputs (`uv run --with playwright playwright install chromium`,
  once per machine). Without it, d3-presentation's `shoot.py` takes screenshots with an installed Chrome or Chromium but
  skips the overflow audit; d3-explainer's `check.py` falls back to an installed Chrome or Edge
- Poppler (`pdftoppm`) when an HTML deck or an explainer embeds a PDF figure
- For the `.pptx` export of d3-presentation: the university PowerPoint master (`.potx`), which is not in this repository
- For d3-marimo: a checkout of the chair website repository that you can push to
- For d3-server-use: an account on the group's server (ssh key sent to the admin); rsync; the AWS CLI (`uv tool install awscli`) once you have a bucket
- Optional: the `recall` skill and the `notebooklm` CLI for the enrichment step of d3-abstract and d3-poster; the
  third-party [watermarks-remover](https://github.com/guillaumemeyer/watermarks-remover) plugin for the removal of
  invisible AI marks

## Team setup

To offer the marketplace automatically in a shared project, add to its `.claude/settings.json`:

```json
{
  "extraKnownMarketplaces": {
    "d3-skills": { "source": { "source": "github", "repo": "d3group/d3-skills" } }
  }
}
```

## License

MIT for the skills' own text and code, see [LICENSE](LICENSE). Not covered: the logos and the cover photo of the University of Würzburg and the logo of the D3 group, which belong to their owners and are included for use by members of the group. Vendored third-party material keeps its own licence (Inclusive Sans UW, Inter and IBM Plex Mono: SIL OFL 1.1; MathJax: Apache 2.0; baposter.cls: GPL).
