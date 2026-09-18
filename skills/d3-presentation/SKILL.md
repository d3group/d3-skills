---
name: d3-presentation
description: |
  Create D3 (Data Driven Decisions) branded presentations as LaTeX Beamer PDFs or as interactive HTML decks. Use this skill when:
  (1) Creating a new presentation from a topic, outline, or notes with D3 branding
  (2) Generating PDF slides (LaTeX Beamer) with D3/University of Würzburg branding
  (3) Generating an interactive HTML slide deck with step builds, deep links, and a navigable backup
  (4) Working with .tex files or slides.py decks for academic/business presentations in the D3 style
  (5) Creating presentations for the Chair of Information Systems and Business Analytics
  MANDATORY TRIGGERS: D3, Data Driven Decisions, presentation, slides, Beamer, LaTeX, .tex, slide deck, HTML slides, interactive presentation, web slides, step build, animation, browser deck, WIBA, Würzburg
---

# D3 Presentations

> **`<skill-dir>`** in this skill means the skill's own base directory, which Claude Code shows when the skill loads (installed as a plugin: `${CLAUDE_PLUGIN_ROOT}/skills/d3-presentation`; copied by hand: `~/.claude/skills/d3-presentation`). Substitute the real path in every command.

Two output formats, one slide vocabulary, one set of rules.

| | PDF (LaTeX Beamer) | Interactive HTML |
|---|---|---|
| Best for | print-stable decks, email, archiving | step builds, deep links, a navigable backup, presenting from a browser |
| Source | `<name>.tex` | `slides.py` (Python, standard library only) |
| Build | `xelatex` twice | `uv run slides.py` |
| Output | `<name>.pdf` | `dist/<name>.html`: one file, fonts, figures and (when the deck has formulas) MathJax embedded |
| Workflow | [references/latex-workflow.md](references/latex-workflow.md) | [references/html-workflow.md](references/html-workflow.md) |

## Step 0: Choose the format and the review depth

Ask once, before anything else, unless the user already named both. Ask both parts in one message and include this hint:

> **Format.** PDF via LaTeX Beamer (print-stable, easy to email) or interactive HTML (step builds, deep links, backup navigation, speaker notes). Token cost is similar: the HTML source is about a third longer because HTML markup is wordier than the LaTeX macros; builds cost nothing; the visual check of HTML reads contact sheets, so it does not exceed a PDF page review.
> **Review depth.** `light`: automated checks only (compile log or overflow audit), no reviewer agents, almost no extra tokens. `standard` (default): one reviewer agent reads the source and the rendered pages or contact sheets once, one fix round; roughly doubles the cost of writing the deck. `full`: two reviewer agents (content and visual) loop until every category scores 9 of 10; typically two to four times the writing cost, more with iterations.

- Format words: ".tex", "Beamer", "LaTeX", "PDF" mean LaTeX; "HTML", "interactive", "browser", "steps", "animation", "web" mean HTML.
- Review words: "no review", "quick", "cheap" or "short on tokens" mean light; "review it" means standard; "full review" or "thorough" mean full. Nothing said means standard.
- Then proceed and do not ask again.

## Step 1: The storyline belongs to the user

A deck fails when the narrative is not the presenter's own. So the narrative is settled before any slide exists, in one exchange:

1. **Ask for theirs first.** "Do you already have a storyline in mind? Give it to me in a few sentences or as a list of sections, in any form, and I will build the deck on it. Or I propose one." Also ask, only if not already clear: audience, time slot, and the one thing the audience should remember.
2. **If they give one, keep it.** Restate it as the sequence of action titles (one complete sentence per slide), keep their order and emphasis, and point out at most two gaps or jumps as questions. Do not reorder their story into a framework they did not ask for.
3. **If they want a proposal, offer two that differ in kind,** each as a title-only outline of 6 to 12 action titles with one line on why one would choose it. Typical pairs: answer first (result, then evidence, then method) versus build-up (problem, approach, result); or chronological project story versus argument by claims. Recommend one.
4. **Approval gate.** The user picks, edits, or replaces. Save the approved titles to `<name>/storyline.md` with audience, time, and the one takeaway; the deck's slide titles must match it, and later change requests to the narrative start there. Re-ask only if the user changes the storyline.

If nobody can answer (batch run), take the better of your two proposals, record that choice and the reason at the top of `storyline.md`, and continue.

## CRITICAL: Project structure

> **ALWAYS create a dedicated subfolder for each presentation**, for both formats. LaTeX writes auxiliary files (`.aux`, `.log`, `.nav`, ...) and HTML writes `dist/` and `shots/`. Never create a presentation in the project root.

Folder name: 1 to 3 lowercase words joined by `_` (for example `ai_healthcare`, `q4_results`).

## Workflow (both formats)

1. **Create the subfolder.** HTML: `uv run <skill-dir>/assets/html/init.py <name>` creates it with everything inside. LaTeX: `mkdir <name>`.
2. **Assemble the assets.** LaTeX: `mkdir <name>/assets && cp -r <skill-dir>/assets/latex/* <skill-dir>/assets/fonts <name>/assets/`. HTML: done by `init.py`.
3. **Read the style guide:** [references/style-guide.md](references/style-guide.md), including the Wording section and, for HTML, the Step builds section.
4. **Agree on the storyline** (Step 1 above). No slide is written before the user has set or approved it.
5. **Write the deck** following the workflow reference for the format.
6. **Build.** LaTeX: `xelatex <name>.tex` twice (three times with `contentnumbering`). HTML: `uv run slides.py`.
7. **Verify** at the chosen review depth (below).
8. **Deliver** the PDF or the HTML file with the verification scores.

All Python in this skill runs through uv (`uv run`, `uv run --with <pkg>`); never install packages globally.

## Slide vocabulary (identical in both formats)

| Slide | LaTeX | HTML |
|---|---|---|
| Title | `\titleslide` | `titleslide()` |
| Agenda (clickable) | `\showagenda` | `agenda()` (klar look: none, use `section(n, question=...)`) |
| Statement, headline numbers | none | `statement()`, `facts()` |
| Section divider n | `\showsection{n}` | `section(n)` |
| One column | `\onecol{title}{content}` | `onecol(title, html)` |
| Two columns | `\twocol{title}{left}{right}` | `twocol(title, left, right)` |
| Two columns + takeaway | `\twocoltakeaway{title}{l}{r}{takeaway}` | `twocoltakeaway(title, l, r, takeaway)` |
| Thank you | `\thankyouslide` | `thankyou()` |
| Backup part | `\appendix` | `appendix()` then `backuphome()` |
| Column header | `\columnheader{}` | `columnheader()` |
| Highlight | `\highlight{}` | `highlight()` |
| Code boxes | `codebox`, `errorbox`, `terminalbox` | `codebox()`, `errorbox()`, `terminalbox()` |
| Process flow | `\twochevron` ... `\fourchevron` | `chevrons(active, phases)` |
| Timeline | `projecttimeline` + `\workpackage` | `timeline(start, end, packages)` |

HTML adds step builds (`steps=`, `data-s`, `scrim()`), speaker notes (`notes=`), stat cards and big numbers; see the HTML workflow.

Equations: LaTeX decks use Beamer's math as usual; HTML decks take the same LaTeX (`$…$`, `\[…\]`, macros via `meta(macros=...)`) and typeset it with an embedded MathJax, see the Math section of the HTML workflow.

## Rules that apply to both formats

### Brand colors: use only these

| Name | LaTeX | CSS token | Hex | Usage |
|---|---|---|---|---|
| Navy | `d3-navy` | `var(--navy)` | #153F87 | text, titles, dark elements |
| Orange | `d3-orange` | `var(--orange)` | #F29100 | accents, highlights, takeaways |
| Gray | `d3-gray` | `var(--gray)` | #808080 | subtle text, borders |
| Light blue | `d3-lightblue` | `var(--lightblue)` | #C8DCF0 | chart fills, backgrounds |
| Dark blue | `d3-darkblue` | `var(--darkblue)` | #0A2864 | darker variant |
| Chart colors | `d3-teal`, `d3-yellow`, `d3-peach`, `d3-lavender` | `--teal`, `--yellow`, `--peach`, `--lavender` | #4D9AAA, #D8DE6F, #F5C8AA, #C5CAE9 | timeline bars, series |

**NEVER** use `red`, `blue`, `green`, or arbitrary hex codes. Lighter tints follow the xcolor syntax in both formats: `d3-navy!15` in LaTeX, `mix('navy!15')` in HTML.

### Content rules

- **Action titles**: every slide title is a complete sentence stating the message; the titles alone must read as the argument.
- **Parallel lists**: bullets are grammatically parallel.
- **One message per slide, one visual idea per slide.** A figure, a row of stat cards, a process flow and a code box each get their own slide.
- **HTML look.** HTML decks use the calm `klar` look by default (tracker on top, orange kicker plus one-claim title via `K()`, question dividers instead of an agenda, `statement()` and `facts()` slides, takeaway on a fixed baseline, D3 logo in the foot, university logo on the title slide). `meta(look='beamer')` reproduces the LaTeX frame when the HTML must match a PDF. See "The look" in references/html-workflow.md.
- **Builds are the exception.** Most slides are static. Use a step build only where the argument needs sequencing, reveal a cluster or a region (never bullet by bullet), and keep to 2 or 3 steps. Later steps wait as pale ghosts in their final place, so nothing moves and nothing is removed. The build warns about slides that look busy; treat each warning as a request to simplify.
- **Viewport**: content never overlaps the header, the footer, or the margins. In HTML, the body box crops overflow and the audit reports it.
- **Key messages**: bold orange text (`\textbf{\textcolor{d3-orange}{...}}` or `highlight()`), never a colored box.

### Wording

Prose must read as written by the presenter. No "not X, but Y" constructions. No em-dashes: use commas, colons, or a new sentence. Describe related work by what it contributed and state the gap as a fact, without "merely", "simply", or "fail to". No leverage, robust framework, comprehensive, transformative, synergies. Vary title length. No forced groups of three. The full list is in the style guide.

## Verification by review depth

Automated checks come first in every depth. LaTeX: the compile log shows no errors. HTML: `uv run --with playwright --with pillow d3deck/shoot.py dist/<name>.html --contact` reports `overflow audit: clean`. The first run on a machine needs the browser once: `uv run --with playwright playwright install chromium`.

**light.** Stop after the automated checks. Look at the pages or the contact sheets yourself once.

**standard (default).** Spawn **one reviewer subagent**. It reads the source (`.tex` or `slides.py`) and the rendered output (PDF pages, or for HTML `shots/contact_*.png`, which need Pillow; without it read the per-step shots) once and returns content findings (flow, one message per slide, wording rules) and visual findings (overlaps, alignment, brand colors, figures) in one list. Apply the findings, rebuild, rerun the automated checks, done.

**full.** Spawn **two reviewer subagents** in parallel.

**Agent 1, content reviewer.** Reads `storyline.md` and the source and scores 0 to 10: fidelity to the approved storyline (titles, order, emphasis), horizontal flow (slide to slide), vertical flow (content supports the title), didactic structure, consistency, and the wording rules above. Output: scores plus specific suggestions.

**Agent 2, visual design reviewer.** Inspects the rendered output. PDF: the pages. HTML: the contact sheets first, individual step shots in `shots/` only for slides it flags, and the overflow report. Scores 0 to 10: calm (one visual idea per slide, whitespace, builds only where the argument needs them, no bullet-by-bullet reveals), layout (nothing overlaps the frame, nothing cropped), alignment, colors (brand tokens only), figures (sized, no chart junk), visual appeal (squint test); for HTML also that every step reveals something.

**Loop:** run both, collect scores; any category below 9 means fix, rebuild, re-verify; repeat until every category is 9 or better.

## Delivery

Provide the final file (`<name>.pdf`, or `dist/<name>.html` plus the optional `dist/<name>.pdf` from `shoot.py --pdf`) with the review depth used and, for standard and full, a summary of the findings or scores. For HTML, mention the presenter keys: arrows for steps and slides, F for fullscreen, P for print, `/` for search, H for the backup hub, N for speaker notes.
