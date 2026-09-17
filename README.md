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

Or install directly: `/plugin install d3-explainer-skill@d3-skills` (likewise `d3-abstract-skill`, `d3-poster-skill`, `d3-presentation-skill`). Update later with `/plugin marketplace update d3-skills`.

## Available Skills

| Skill | Description | Resources |
|-------|-------------|-----------|
| [d3-abstract](skills/d3-abstract/) | Abstracts, extended abstracts, one-pagers and research updates as A4 PDFs | LaTeX template, style checker |
| [d3-poster](skills/d3-poster/) | A0 conference posters from a paper, an Overleaf submodule or a repo of results | baposter class, TikZ recipes, two-agent review |
| [d3-presentation](skills/d3-presentation/) | Presentations as LaTeX Beamer PDFs or interactive HTML decks with step builds | Beamer theme, HTML deck engine, overflow audit |
| [d3-explainer](skills/d3-explainer/) | Interactive HTML explainer of a research repo (code, paper, vault) for its own authors and co-authors: concepts, derivations, research gap, paper-to-code map, open points | Build and check engine, worked example |

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

MIT for the skills' own text and code, see [LICENSE](LICENSE). Not covered: the logos of the University of Würzburg and of the D3 group (they belong to their owners and are included for use by members of the group) and vendored third-party material, which keeps its own licence (Inter and IBM Plex Mono: SIL OFL 1.1; KaTeX: MIT; baposter.cls: GPL).
