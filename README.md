# D3 Skills

Claude Code skills of the Data Driven Decisions (D3) group, Chair of Information Systems and Business Analytics,
University of Würzburg. They turn a research repository (code, paper, notes) into communication artefacts in the D3
corporate design.

| Skill | What it produces |
|---|---|
| [`d3-abstract`](skills/d3-abstract) | Abstracts, extended abstracts, one-pagers and research updates as A4 PDFs (LaTeX) |
| [`d3-poster`](skills/d3-poster) | A0 conference posters from a paper or repo (LaTeX, baposter) |
| [`d3-presentation`](skills/d3-presentation) | Presentations as LaTeX Beamer PDFs or interactive HTML decks |
| [`d3-explainer`](skills/d3-explainer) | An interactive HTML explainer of a project for its own authors and co-authors: concepts, derivations, research gap, paper-to-code map, open points |

## Install

As a Claude Code plugin marketplace:

```
/plugin marketplace add d3group/d3-skills
/plugin install d3-explainer-skill@d3-skills
```

(likewise `d3-abstract-skill`, `d3-poster-skill`, `d3-presentation-skill`), or copy a folder from `skills/` into
`~/.claude/skills/`.

## Requirements

- [uv](https://docs.astral.sh/uv/) for all Python (`uv run`, no pip, no global installs)
- A LaTeX distribution with XeLaTeX for the abstract, poster and Beamer skills
- A Chromium-based browser for the automated checks of the HTML outputs (Playwright falls back to an installed Chrome or Edge)

## Conventions shared by the skills

- They scan the repository first (paper folder or submodule, code, results, Obsidian vault) and agree on a content
  brief before writing.
- Automated checks run before any reviewer agent; review depth is a dial, so token cost is a choice.
- Writing rules: no dashes as punctuation, no "not X but Y", neutral description of related work, concrete numbers.

## Third-party material

Inter and IBM Plex Mono (SIL Open Font License 1.1) and KaTeX (MIT) are vendored with their licence files. The logos of
the University of Würzburg and the D3 group belong to their owners and are included for use by members of the group.
