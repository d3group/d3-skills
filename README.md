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

Or install directly: `/plugin install d3-explainer@d3-skills` (likewise `d3-abstract`, `d3-poster`, `d3-presentation`). Skills are then invoked as `/d3-explainer:d3-explainer`, or simply by asking. Update later with `/plugin marketplace update d3-skills`.

## Available Skills

| Skill | Version | Description | Resources |
|-------|---------|-------------|-----------|
| [d3-abstract](skills/d3-abstract/) | 1.1.0 | Abstracts, extended abstracts, one-pagers and research updates as A4 PDFs | LaTeX template, style checker |
| [d3-poster](skills/d3-poster/) | 1.1.0 | A0 conference posters from a paper, an Overleaf submodule or a repo of results | baposter class, TikZ recipes, two-agent review |
| [d3-presentation](skills/d3-presentation/) | 1.3.0 | Presentations as LaTeX Beamer PDFs or interactive HTML decks in a calm talk design with step builds | Beamer theme, HTML deck engine, overflow audit |
| [d3-explainer](skills/d3-explainer/) | 0.10.0 | Interactive HTML explainer of a research repo (code, paper, vault) for its own authors and co-authors: concepts, derivations, research gap, paper-to-code map, open points | Build and check engine, worked example |

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
