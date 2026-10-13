# Outlets, genres, fields and readers

The rules in `rules.md` hold for every text. This file sets the register around them: what a genre allows, what an outlet's reviewers expect, what a reader already knows. Conventions of venues change; when the call for papers or the author guidelines are at hand, they win over this file.

## Contents

1. Detecting the brief
2. Genre profiles
3. Outlet families (one file per family in `outlets/`)
4. Reader
5. Topic: the term sheet
6. Language and spelling

## 1. Detecting the brief

Read before asking. A template is strong evidence; library imports are weak evidence. When two signals disagree, ask.

| Signal | Where | Means |
|---|---|---|
| `neurips_20xx.sty`, `icml20xx.sty`, `iclr20xx_conference.sty`, `aistats20xx.sty`, `jmlr2e.sty`, `tmlr.sty` | the paper's preamble | ML venue; anonymous at submission unless a `final` or `preprint` option is set |
| `\documentclass[conference]{IEEEtran}` / `[journal]{IEEEtran}` | preamble | IEEE conference (PES General Meeting, ISGT, IEEE Conference on Games) or IEEE Transactions (Power Systems, Smart Grid, Sustainable Energy): numeric citations |
| `aaai2x.sty` | preamble | AAAI |
| `sn-jnl` class, "Nature" in the call or the folder name | preamble, call | Springer Nature journal; Nature and Nature Energy follow their own guide to authors |
| `interact` class (Taylor & Francis) | preamble | for example Journal of Sports Sciences |
| "JEL" codes on the first page, `\JEL{}` | preamble, first page | economics |
| `\documentclass{acmart}` | preamble | an ACM conference; the template does not name the field, the conference does (see "ACM conferences" below); `anonymous` option means double-blind |
| `\documentclass{elsarticle}` | preamble; the `\journal{}` field | Elsevier journal (EJOR, Applied Energy, Decision Support Systems) |
| `informs3`, `informs4`, `\MNSC`, `\OPRE`, `\IJOC` | preamble | INFORMS journal (Management Science, Operations Research, INFORMS JoC, M&SOM) |
| `llncs` | preamble | Springer LNCS proceedings |
| AIS template, or `ICIS`, `ECIS`, `PACIS`, `AMCIS`, `WI` in file or folder names | paper folder | AIS conference (IS) |
| `beamer` with `d3-beamer`, or a `slides.py` | deck folder | slides; `storyline.md` holds audience, time and kind of talk |
| `baposter` with `d3-poster` | poster folder | poster; the conference is usually in the paper or the footer |
| `d3-abstract` | abstract folder | abstract; `\projektname` in the footer names venue and deadline |
| `explainer.toml`, `explainer/brief.md` | repo root | explainer for the authors |
| `booktitle` and `journal` fields of the `.bib` | the paper's bibliography | the field: count the venues |
| `torch`, `jax`, `sklearn` / `gurobipy`, `pyomo`, `ortools` / `statsmodels`, `linearmodels`, SmartPLS or lavaan files / `pypsa`, `pandapower` / `nashpy`, `gambit` / tracking or event data of matches | the code's imports and data | ML / OR / econometrics or empirical IS / energy / game theory / sports (weak evidence) |
| a call for papers in the repo or the request | anywhere | page and word limits, anonymity, required sections: these override everything below |

## 2. Genre profiles

The sentence caps are those of the lint: a warning above the first number, an error above the second. In STE mode the error cap is 25 words, 20 on slides, and the warning comes 5 words earlier.

| Genre | Sentence cap | Form | Claims |
|---|---|---|---|
| Paper (journal, conference), thesis chapter, proposal | 35 / 45 | Full prose. Paragraphs of 4 to 8 sentences with a topic sentence. Contributions stated in the introduction; related work neutral; limitations in their own place | per outlet; a proposal states expected results as expectations |
| Abstract, extended abstract | 30 / 40 | Problem, approach, result with its number, contribution. An abstract argues; it does not list definitions. At most the one central definition, verbatim | the last sentence names what is new; the word limit is counted, not estimated |
| Poster | 25 / 35 | Verb-first bullets, numbers before prose, bold run-in labels, no throat-clearing, no future work | as in the paper, shorter |
| Slides | 20 / 30 | Action titles (one complete sentence each), labels on the designed object, full sentences in the speaker notes (notes use the explainer cap) | present, do not defend; every number explained where it stands |
| Explainer | 30 / 40 | Short paragraphs (2 to 5 sentences), definitions inline at first use, Try / Notice captions, questions to the reader before a figure. STE by default | interpretations marked as readings; the honest inventory states what is open |
| Rebuttal (response to reviewers) | 35 / 45 | See below | concede fast, decline with a reason and a plan |
| Internal update | 25 / 35 | Lead with what changed, numbers in boxes, questions or decisions at the end | direct |

**Rebuttals.** The defining habit is to show the change, not describe it.

- Open with thanks that names the improvements as a colon list, once. No "we thank the reviewer for this insightful comment" on every point.
- Per comment: a heading (`Validity: overstated attribution`), the reviewer's words quoted verbatim and indented, a bold run-in `Response.`, the answer, and the location of the change (`Section 4.2, p. 6`).
- The answer quotes the revised manuscript text verbatim.
- The length of an answer follows the size of the fix: "Removed. The figure's information did not justify the space."
- Agree in three words, then give the fix: "We agree. The revised section now ..."
- Decline with a reason and a plan, never with deflection: "Within the page limit we prioritized the pilot study (AE, comment 2). A running example is planned for the extended version."
- Volunteer errors nobody caught. No defensiveness, no grovelling.

## 3. Outlet families

Each family has its own file in `references/outlets/`. Read the one the brief names, not all of them. A measured outlet profile (`profiles.md`) beats these files wherever both exist.

| Family | Venues | File |
|---|---|---|
| Operations research and management science | Operations Research, Management Science, EJOR, INFORMS Journal on Computing, M&SOM, Transportation Science | `outlets/or-ms.md` |
| Information systems | ICIS, ECIS, PACIS, AMCIS, WI, MISQ, ISR, JAIS, JMIS, EJIS, BISE | `outlets/information-systems.md` |
| Machine learning | NeurIPS, ICML, ICLR, AAAI, AISTATS, JMLR, TMLR, and ACM conferences such as KDD | `outlets/machine-learning.md` |
| Economics, energy economics and econometrics | Energy Economics, The Energy Journal, economics journals | `outlets/economics.md` |
| Power systems and energy | IEEE Transactions on Power Systems, IEEE Transactions on Smart Grid, IEEE PES General Meeting, IEEE ISGT, Applied Energy, Energy Policy, ACM e-Energy | `outlets/energy.md` |
| Nature-family journals | Nature, Nature Energy, Nature Communications | `outlets/nature.md` |
| Game theory and games research | Games and Economic Behavior, International Journal of Game Theory, Dynamic Games and Applications, ICOG; IEEE Conference on Games, CHI PLAY, FDG | `outlets/game-theory-and-games.md` |
| Sports science | Journal of Sports Sciences, Medicine & Science in Sports & Exercise, International Journal of Sports Physiology and Performance, Journal of Quantitative Analysis in Sports, MIT Sloan Sports Analytics Conference | `outlets/sports-science.md` |
| German-language outlets and occasions | WI in German, talks, teaching | `outlets/german.md` |

### ACM conferences

ACM runs conferences in almost every field the group works in: machine learning (KDD and others), energy (e-Energy, BuildSys), games (CHI PLAY, FDG), sports (the MMSports workshop) and more. They share the `acmart` template, numeric citations, CCS concepts and keywords after the abstract, and often double-blind review. The wording follows the field family of the specific conference (table above), so name the conference in the brief, not just "ACM".

### Unknown outlet

Use the journal norm of the field, record it as the default under `## Wording`, and say so in one line. If the user writes for this outlet again, offer an outlet profile (`profiles.md`).

## 4. Reader

The principle underneath every reader profile: minimize the effort of the reader who is new to the material. Spell out where a term is new, abbreviate where it is familiar; run an example long where the idea is hard; motivate before naming.

| Reader | Knows | Wording consequence |
|---|---|---|
| Experts of the field | the field's terms and methods | no textbook background; the paper's own constructs are defined |
| Adjacent researchers (a mixed session, a group meeting) | the broad area | define every term the adjacent field does not share; one example per new concept |
| Practitioners | the domain, not the method | the decision and the number first, the method second; no notation in running text |
| Students | little | build up, define everything, examples before formalism |
| Co-authors (explainer) | the project's terms and goals | define the derivation steps, not the vocabulary they coined themselves |

## 5. Topic: the term sheet

For any document longer than a page, keep a term sheet under the `## Wording` heading of the project's notes file. It makes rule 7 checkable and survives across sessions.

1. Collect the defined terms, symbols and abbreviations from the sources: the paper's definitions, its notation table and `\newcommand` macros, the explainer's notation table, the deck's fact sheet.
2. For each concept, fix one term and note the synonyms it replaces.
3. The field's established names come from the sources, never from memory alone. A term the literature has is used, not re-coined.
4. After a rename, search the whole document for the old term, figures and tables included.

```markdown
## Wording
Brief: paper · EJOR · OR · experts · US English · standard mode (outlet from elsarticle \journal{})

### Terms
| Concept | Term | Not | Defined at |
|---|---|---|---|
| hourly charge or discharge choice of the battery | dispatch decision | schedule, action, control | Sec. 3.1 |
| cost of the realized schedule minus the optimal cost | regret | loss, error, gap | Eq. (4) |

### Corrections
- 2026-10-09 · Sec. 2, para. 3 · "write decision-focused learning, never end-to-end" · told fix · applied in Sec. 1, 2, 5
- 2026-10-09 · abstract · "the last sentence sounds like a sales pitch" · verdict · rewritten; no general rule yet
```

## 6. Language and spelling

- US English by default for international venues; UK English when the outlet or the existing text uses it. One variant per document, notes and captions included; quotations keep their original spelling.
- Oxford comma in US English.
- Digits for measured quantities and anything with a unit; words for small counts in an argument.
- German: current spelling, decimal comma, "wir" for the group.
