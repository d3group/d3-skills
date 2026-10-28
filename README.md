# D3 Skills

Claude Code skills of the Data Driven Decisions (D3) group for research communication in the D3 corporate design.

> Chair of Information Systems and Business Analytics, University of Würzburg.

## Installation

1. Add marketplace (run in Claude Code):
   ```
   /plugin marketplace add d3group/d3-skills
   ```
2. Run `/plugin` in Claude Code
3. Go to **Discover** tab, find the skill
4. Select **Install for you (user scope)**
5. Restart Claude Code

Or install directly: `/plugin install d3-explainer@d3-skills` (likewise `d3-abstract`, `d3-poster`, `d3-presentation`, `d3-scientific-wording`). Skills are then invoked as `/d3-explainer:d3-explainer`, or simply by asking. Update later with `/plugin marketplace update d3-skills`.

## Available Skills

| Skill | Version | Description | Resources |
|-------|---------|-------------|-----------|
| [d3-abstract](skills/d3-abstract/) | 1.3.0 | Abstracts, extended abstracts, one-pagers and research updates as A4 PDFs | LaTeX template, style checker |
| [d3-poster](skills/d3-poster/) | 1.3.0 | A0 conference posters from a paper, an Overleaf submodule or a repo of results | baposter class, TikZ recipes, two-agent review |
| [d3-presentation](skills/d3-presentation/) | 1.7.0 | Presentations as LaTeX Beamer PDFs or interactive HTML decks (also in the University of Würzburg design for teaching, `look='uni'`) where every slide centres on a designed object: model figures that build, bars, gauges, replayed stimuli, live instruments; presenter window with pace, overview and Q&A interactions | Beamer theme, HTML deck engine and component kit, layout and signature lint |
| [d3-explainer](skills/d3-explainer/) | 0.12.0 | Interactive HTML explainer of a research repo (code, paper, vault) for its own authors and co-authors: concepts, derivations, research gap, paper-to-code map, open points | Build and check engine, worked example |
| [d3-scientific-wording](skills/d3-scientific-wording/) | 0.1.0 | The wording layer of all D3 skills, also for papers, rebuttals and proposals: direct claims, neutral related work, claims within the evidence, short sentences, wording adapted to outlet and field, optional Simplified Technical English (ASD-STE100), optional removal of invisible AI marks | Rules with examples, outlet profiles, STE guide, wording lint, corpus profiler |
| [d3-marimo](skills/d3-marimo/) | 0.1.0 | Teaching apps as marimo notebooks that run in the browser (WASM) on the chair website: port Colab/molab notebooks, SciPy HiGHS instead of PuLP, university look, deploy and check | App template, look stylesheet, headless browser check, pitfalls |

## Design

All D3 outputs follow the 2026 corporate design of the University of Würzburg with D3 co-branding: the new round university logo top left, the D3 logo in the co-branding slot (top right, or next to the university logo on title pages), the university navy `#02246C`, D3 orange `#F29100` as the only accent, the house font Inclusive Sans UW (SIL OFL), and the seal on title and divider pages. Slides follow the university PowerPoint master, posters the university poster template, one-pagers the letterhead. The university's coral is not used next to D3 orange. Inclusive Sans UW has no Greek letters or math operators: the HTML skills embed a small fallback font (D3 Symbols, an Inter subset), the LaTeX skills set these characters in math mode. The CD will replace the seal by a faculty ornament in faculty communication; until that package is released the seal stands in. For teaching decks without D3 branding, d3-presentation offers `look='uni'`; d3-marimo uses the university look throughout.

## Wording

The wording rules live in one skill, `d3-scientific-wording`. The other four invoke it before they write text, ask its questions in their own question round, run its lint (`scripts/check_wording.py`, for `.tex`, `.html`, `.md` and `slides.py`) and use its rules as the reviewers' wording rubric. It adds no reviewer agent: its cold read (does every claim follow, is every term explained before use) is a task of each skill's existing content reviewer at review depth `standard` or `full`. Every D3 plugin ships the whole `skills/` folder, so the wording skill is always on disk next to the skill that calls it. Install it as a plugin of its own to use it for papers, rebuttals or any other text.

| Skill | Simplified Technical English (ASD-STE100) |
|---|---|
| d3-explainer | default; say "normal wording" or "no STE" to switch it off |
| d3-presentation, d3-poster | offered in the question round, off by default |
| d3-abstract, papers and other texts | on request |

The wording adapts to the outlet and the field (venue templates, the call for papers, the `.bib` are read first; open points are asked). Optionally it measures a wording profile from a literature folder, a vault or a NotebookLM notebook: the user's own papers (author), papers of the target venue (outlet) or the topic's literature (terms). `scripts/wording_profile.py` counts sentence length, stance, punctuation, terms, abbreviations and recurring phrases, and `compare` puts a draft next to the corpus bands; profiles hold counts and short excerpts, never full texts. The removal of invisible AI marks is offered once at delivery. It uses the third-party [watermarks-remover](https://github.com/guillaumemeyer/watermarks-remover) plugin, deterministic layer only, and needs a yes from the user each time. Several rules are adapted from the academic-voice skill of a group colleague.

## Review depth: how many tokens a run spends

Every skill checks its output automatically (compile log, overflow and layout audits, source-pointer validation) and can
then have reviewer agents look at it. The reviewers are where the tokens go, so the depth is your choice. Say it in your
request ("light review", "I'm short on tokens", "full review"); otherwise the default runs.

| Depth | What runs | Use when |
|---|---|---|
| `light` | Automated checks plus Claude's own pass over the review rubric. No reviewer agents. | You are short on tokens, or the document is a quick internal draft |
| `standard` (default) | Reviewer agents, one round, fixes applied. d3-abstract and d3-poster: two reviewers (content, visual). d3-presentation: one reviewer. d3-explainer: two reviewers (one merged reviewer with `single`) | Normal use |
| `full` | Reviewers loop until every score is 9 of 10, capped at three to four rounds | Submission-ready output |

A reviewer costs roughly 50k tokens regardless of document size, so `standard` adds about 50 to 150k tokens and `full` a
multiple of that; `light` adds almost nothing.

## Versions and releasing

Each skill has its own version in `.claude-plugin/marketplace.json` (semantic versioning: patch for fixes, minor for new
capabilities, major for changes that break existing projects). Users receive an update only when that number changes, so
a release is: edit the skill, bump its `version` in the manifest and in the table above, run `claude plugin validate .`,
commit, push. Users then run `/plugin marketplace update d3-skills`. `d3-explainer` is at 0.9.0 until it has been used
on a few real projects.

## Requirements

- [uv](https://docs.astral.sh/uv/) for all Python (`uv run`; no pip, no global installs)
- A LaTeX distribution with XeLaTeX for d3-abstract, d3-poster and the Beamer route of d3-presentation
- Chrome, Edge or Playwright's Chromium for the automated checks of HTML outputs

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

MIT for the skills' own text and code, see [LICENSE](LICENSE). Not covered: the logos of the University of Würzburg and of the D3 group (they belong to their owners and are included for use by members of the group) and vendored third-party material, which keeps its own licence (Inter and IBM Plex Mono: SIL OFL 1.1; MathJax: Apache 2.0; baposter.cls: GPL).
