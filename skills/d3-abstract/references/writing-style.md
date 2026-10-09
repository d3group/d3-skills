# Writing Style

Read this before filling content (Pass 2), after invoking `d3-scientific-wording`. The goal is text that reads as written by a researcher in the group: direct, specific, and free of stock phrasing. The wording rules themselves live in `<wording-dir>/references/rules.md` (`<wording-dir>` is `<skill-dir>/../d3-scientific-wording`); this file covers what is specific to abstracts. The checker (`scripts/check_abstract.py`) enforces the mechanical part.

## Contents

1. Information hierarchy
2. Lead paragraph
3. Sentence and section rules
4. Wording rules: dashes in LaTeX, and where the shared rules live
5. References
6. Style by document type
7. Domain adaptation

## 1. Information Hierarchy

Use the inverted pyramid: the most important information comes first, details follow.

```
Title (+ subtitle)   identity and topic
Lead paragraph       the message in 2 to 3 sentences
Left column          primary content: problem, approach, evidence
Right column         supporting content: numbers, figures, status, questions or references
Footer               university line, project, or venue
```

Within each column:

1. Section heading: what this part is about
2. The most important number or fact
3. Supporting text: context and explanation
4. Details: lists, tables, secondary information

## 2. Lead Paragraph

The lead paragraph is the most-read element after the title.

- It states a claim: what was shown, built, or decided, with the headline number
- 2 to 3 sentences, at most 50 words
- 1 to 2 `\highlight{}` terms
- Research updates: contribution, headline metric, target venue
- Weekly updates: date first, then the headline result or milestone
- Submission abstracts: contribution, data or setting, headline metric

| Topic statement (weak) | Claim (strong) |
|------------------------|----------------|
| "This update covers our bandit research." | "Our new estimator \highlight{halves the regret} of DRL across all OPE benchmarks." |
| "This page presents the project status." | "We completed the proof pipeline and target \highlight{NeurIPS 2026}." |
| "We investigate battery scheduling with machine learning." | "Training price forecasts on dispatch cost lowers regret by \highlight{31\%} on 24 months of market data." |

**Scan Test.** Title, lead paragraph, and section heads of page 1 convey the full message without the body text. If they do not, rewrite the lead or rename the sections.

## 3. Sentence and Section Rules

- **Concise.** Every sentence carries information. Cut filler.
- **Scannable.** Headings, bullets, bold run-in labels, and infoboxes carry the structure. Paragraphs stay short.
- **Data first.** Numbers, tables, and figures carry more than prose. A 3-row table replaces 3 sentences of comparison.
- **Active voice.** "We derived X."
- **One message per section.** Each section under a `\sectionhead{}` makes one point. Two points become two sections. A section without a point gets deleted.
- **Parallel lists.** All items of a list share the same grammatical form.

| Mixed forms | Parallel |
|-------------|----------|
| "Prove upper bound" / "Lower bound was derived" / "Running experiments" | "Prove upper bound" / "Derive lower bound" / "Run experiments" |

- **Emphasis discipline.** At most 3 `\highlight{}` and 3 infoboxes per page, 1 `\keypoint{}` per column, 2 `card alert` per page. The headline number is highlighted once, in the lead paragraph. Infoboxes show other numbers. Best-value highlights in tables are exempt.
- **Run-in labels end with a period:** `\item \textbf{Sepsis model v2.} Retrained on 12{,}000 ICU stays.`
- **No "Contact" section.** Contact details go into the footer through `\projektname`.

## 4. Wording Rules

### 4.1 Dashes only in number ranges

`--` appears between numbers: `2024--2026`, `pp. 9--26`. Everywhere else, the sentence gets a comma, a colon, parentheses, or a full stop. This covers `---`, a spaced `--`, and the Unicode dash characters.

| Before | After |
|--------|-------|
| "The model converges quickly --- within 10 epochs --- on all datasets." | "The model converges within 10 epochs on all datasets." |
| "Sepsis model v2 -- retrained on new data" | "Sepsis model v2. Retrained on new data." |
| "Research Update -- March 6, 2026" | "Research Update\enspace\|\enspace March 6, 2026" |
| "One result stands out -- the regret halves." | "One result stands out: the regret halves." |

### 4.2 The shared wording rules

Direct claims instead of the "not X but Y" family, neutral reports of related work, claims within the evidence, short sentences and plain vocabulary are the rules of all D3 documents. They live in one place, with before/after examples: `<wording-dir>/references/rules.md`, sections 1 (direct claims), 2 (related work), 3 (claims and evidence), 4 (sentences) and 5 (vocabulary). For abstracts, three of them matter most:

- **The lead paragraph states a claim with its number** (section 2 above) and stays within the evidence: "lowers regret by 31\%", never "dramatically improves".
- **Related work in 2 to 4 sentences**, each saying what a work does, under which assumptions, with which result. The own setting follows as a fact.
- **A Submission Abstract argues; it does not list definitions.** At most the one central definition, verbatim as in the paper.

## 5. References

Submission abstracts cite their sources. Internal documents cite when they compare against published methods.

- Cite only sources that come from the user, from the project's `.bib` file, or from the enrichment step with full bibliographic data
- Copy bibliographic data from the source as given, including abbreviated author lists. Never reconstruct authors, years, or page numbers from memory
- Mark incomplete or unverified fields with `% TODO verify` in the `.tex` file and list them for the user with the accuracy question
- Check every interpretive sentence against the supplied numbers before writing it
- 4 to 8 references fit a two-page abstract. Ask whether references count toward the page limit
- Format and macro: see `references/macros.md`, section 8

## 6. Style by Document Type

**Research Update** (paper-driven, for supervisors and peers)
- Formal, in the notation of the domain
- 2 to 4 numbered contributions or theorems, one line each
- A comparison table with our methods below the `\midrule`
- Paper progress: which sections, proofs, and experiments are done
- Footer with target venue and deadline, lead paragraph names the target

**Weekly Update and other internal documents**
- Direct: lead with what changed and skip background the team knows
- Actionable: end with questions, decisions needed, or next steps
- Status-oriented: infoboxes for metrics, `card alert` for blockers
- Time-anchored: the lead paragraph starts with "**Week of [date].**"

**Submission Abstract**
- Complete and self-standing: motivation, approach, results, conclusion
- Every figure and table is final. No placeholders, no question section, no progress table
- Related work in 2 to 4 sentences, reported as in 4.3
- Claims match the evidence shown. Report the evaluation protocol and the comparison conditions
- A "Scope" section or sentence states the assumptions
- Authors and affiliation in the page 1 subtitle, references at the end of the last page

## 7. Domain Adaptation

| Domain | Problem formulation style | Typical metrics | Common venues |
|--------|---------------------------|-----------------|---------------|
| **ML/Statistics** | Math notation, objective functions, assumptions | Regret, AUC, accuracy, loss | NeurIPS, ICML, AISTATS, JMLR |
| **Operations Research** | Optimization model, constraints, decision variables | Optimality gap, solve time, cost reduction | OR, EJOR, Management Science, INFORMS |
| **Energy Informatics** | System model, data sources, research questions | Forecast error, cost savings, efficiency | Energy Informatics, Applied Energy, IEEE |
| **Information Systems** | Design science, research model, hypotheses | Effect sizes, R², adoption rates | ICIS, ECIS, ISR, MISQ |
| **Applied ML** | Pipeline description, data, evaluation protocol | F1, RMSE, latency, throughput | KDD, WWW, AAAI, domain journals |

Examples of notation: ML/Stats uses $\pi$, $\mathcal{X}$, $\tilde{O}(n^{-1/2})$. OR uses $\min c^\top x$ s.t. $Ax \leq b$. IS uses research models and system diagrams.
