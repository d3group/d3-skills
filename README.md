# D3 Skills

Claude Code skills of the Data Driven Decisions (D3) group for research communication in the D3 corporate design, teaching apps, and running jobs on the group's compute server.

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

Or install directly: `/plugin install d3-explainer@d3-skills` (likewise `d3-abstract`, `d3-poster`, `d3-presentation`, `d3-scientific-wording`, `d3-marimo`, `d3-server-use`). Skills are then invoked as `/d3-explainer:d3-explainer`, or simply by asking. Update later with `/plugin marketplace update d3-skills`.

## Available Skills

| Skill | Version | Description | Resources |
|-------|---------|-------------|-----------|
| [d3-abstract](skills/d3-abstract/) | 1.3.0 | Abstracts, extended abstracts, one-pagers and research updates as A4 PDFs | LaTeX template, style checker |
| [d3-poster](skills/d3-poster/) | 1.3.0 | A0 conference posters from a paper, an Overleaf submodule or a repo of results | baposter class, TikZ recipes, two-agent review |
| [d3-presentation](skills/d3-presentation/) | 1.8.3 | Presentations as LaTeX Beamer PDFs or interactive HTML decks (also in the University of Würzburg design for teaching, `look='uni'`; exportable to an editable PowerPoint on the university master) where every slide centres on a designed object: model figures that build, bars, gauges, replayed stimuli, live instruments; presenter window with pace, overview and Q&A interactions | Beamer theme, HTML deck engine and component kit, layout and signature lint |
| [d3-explainer](skills/d3-explainer/) | 0.12.0 | Interactive HTML explainer of a research repo (code, paper, vault) for its own authors and co-authors: concepts, derivations, research gap, paper-to-code map, open points | Build and check engine, worked example |
| [d3-scientific-wording](skills/d3-scientific-wording/) | 0.1.0 | The wording layer of all D3 skills, also for papers, rebuttals and proposals: direct claims, neutral related work, claims within the evidence, short sentences, wording adapted to outlet and field, optional Simplified Technical English (ASD-STE100), optional removal of invisible AI marks | Rules with examples, outlet profiles, STE guide, wording lint, corpus profiler |
| [d3-marimo](skills/d3-marimo/) | 0.1.1 | Teaching apps as marimo notebooks that run in the browser (WASM) on the chair website: port Colab/molab notebooks, SciPy HiGHS instead of PuLP, university look, deploy and check | App template, look stylesheet, headless browser check, pitfalls |
| [d3-server-use](skills/d3-server-use/) | 0.2.0 | Compute jobs on the group's KiRegio Slurm server: first login and ssh, uv only, run IDs and a registry that tie code, config, logs, checkpoints and results together, jobs that checkpoint and resume within the 24 h limit, smoke test and sizing before a round, fair use of the GPUs, the S3 bucket (or the user's own computer) as the store with verified cleanup | Registry and S3 transfer CLI, job-side checkpoint helper, job template, sbatch lint |

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

`d3-server-use` runs no reviewer agents and has no review depth: its checks are deterministic (the refusals and
verification in `d3run.py`, the stop logic in `d3job.py`, the `check_sbatch.py` lint) and cost no extra tokens.

## Running jobs on the group server (d3-server-use)

`d3-server-use` is the group's way of running compute jobs on the KiRegio Slurm server: Slurm for everything that
computes, uv only, jobs that survive the 24 h limit, a run ID for every run, fair use of the 4 GPUs, and a store
outside the small server home. Server addresses and the user's answers live in a local site file
(`~/.config/d3-server/site.toml`), never in this repository.

### What the skill contains

```
skills/d3-server-use/
├── SKILL.md                 first use · rules · a round in 9 steps
├── scripts/
│   ├── d3run.py             login host: run IDs, registry, submit, fair use, sizing, S3, verified cleanup
│   ├── d3job.py             inside the job: end time, stop margin, checkpoints, resume
│   └── check_sbatch.py      lint for hand-written job scripts
├── assets/
│   ├── job_template.sbatch  job clock, USR1 trap, GPU memory log, uv run --no-sync
│   └── site.example.toml    template of the user's local site file (no secrets)
├── references/              first-time setup · cluster · interruptible jobs
│                            data and storage · registry · pitfalls
└── evals/                   test prompts and two toy projects
```

### Where things run, and who writes what

```
  LAPTOP                         LOGIN HOST                      COMPUTE NODE
  (Claude Code)                  (light commands only)           (Slurm jobs only)
 ┌──────────────────┐   ssh     ┌──────────────────────┐ sbatch ┌──────────────────────┐
 │ site.toml        │──────────▶│ git pull, uv sync    │───────▶│ job_template.sbatch  │
 │ ~/.ssh/config    │  <alias>  │ d3run.py             │        │  uv run --no-sync    │
 │ ~/.aws (yours)   │           │  └ registry.db       │◀───────│  your code + d3job   │
 └──────────────────┘           │    (only writer)     │ status │  └ runs/<id>/...     │
                                └──────────┬───────────┘  .json └──────────┬───────────┘
                                           │ archive · push · pull         │ checkpoints, results
                                           ▼ (verified by size)            ▼ (uploaded by d3job)
                                ┌──────────────────────────────────────────────────────┐
                                │ the store: S3 bucket, or without one your computer   │
                                └──────────────────────────────────────────────────────┘
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
```

### A round, step by step

Every use starts by reading the repository the skill is invoked in (project rules, existing job scripts, an
existing orchestrator, checkpoint code, folder layout) and adapts to it; the skill itself holds nothing
project-specific.

```
 ①setup ─▶ ②plan ─▶ ③interruptible ─▶ ④deploy ─▶ ⑤smoke ─▶ ⑥pilot+size ─▶ ⑦submit ─▶ ⑧watch ─▶ ⑨archive+clean
   │          │          │                │          │            │              │           │          │
 read repo, CPU or    d3job +           commit,    tiny job,    full-size     new --tag,  reconcile  verified copy,
 clone,     GPU per   check_sbatch      git pull   GPU check,   run, then     CPU part    every 15+  then delete;
 uv sync,   part                        (queue     resume       `size`        first;      min        `usage`
 init                                   empty)     test                       fair use
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
 data/raw, processed   pulled once per round                  in the store only
 registry.db           server                                 daily snapshot in S3

 the store   S3 bucket   archive --clean · push --clean        each file verified by size and MD5 (ETag)
             no bucket   rsync to your computer                manifest with SHA-256 · clean --manifest
             fallback    university share, NAS, own cloud      same manifest route (unrestricted data only)
             git         small text results for the repo       moves them, does not free server space
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
| ⚙️ **automatic** | run ID before `sbatch`; commit, config hash and logs per run | `new`, `submit` |
| ⚙️ | fair-use hold and release | `submit`, `feed`, `reconcile` |
| ⚙️ | chained segments; later segments exit if the run is done or failed | `submit`, `d3job` |
| ⚙️ | measured stop margin, deferred uploads, resume from the server or S3 | `d3job` |
| ⚙️ | `--time` / `--mem` / `--cpus` / segments from measured usage | `size` |
| 📖 **guides** | light commands only on the login host | `SKILL.md` |
| 📖 | smoke test and pilot before every round; CPU part first | `SKILL.md` |
| 📖 | never pull while a round is queued | `SKILL.md` |
| 📖 | ssh and S3 setup: detect first, the user handles keys | `SKILL.md`, setup guide |
| 📖 | clean up after each round and above about 50 GB; a restore drill and a bucket lifecycle check before the store is the only copy | `SKILL.md`, references |
| 📖 | no scans of the whole home, not even in a job; stop idle JupyterHub servers | `SKILL.md`, references |

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
- For d3-server-use: an account on the group's server (ssh key sent to the admin); rsync; the AWS CLI (`uv tool install awscli`) once you have a bucket

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
