# Content Mapping

How to turn raw user input (notes, bullet points, data, a paper draft) into the slot structure. Read this before drafting the outline (Pass 0).

## Contents

1. Input to LaTeX mapping
2. Transformation process
3. Section structure per document type
4. Slot mappings
5. Allocation across pages

## 1. Input to LaTeX Mapping

Classify each piece of information and map it to a construct:

| User input | LaTeX construct | Example |
|------------|-----------------|---------|
| The headline number | `\highlight{}` in the lead paragraph, once | "Hit the 92% milestone" becomes `\highlight{92\% AUC}` |
| Supporting metrics | `infobox`, with numbers other than the headline number | "94% coverage" becomes `\node[infobox] {\textbf{\color{d3-navy}\Large 94\%}\quad Calibration coverage};` |
| A blocker, or a deadline that the footer does not show | `card alert` | "ICML deadline Jan 31" becomes `\node[card alert] {\textbf{\color{d3-orange} Deadline:}\enspace ICML 2026, Jan 31};` |
| The main takeaway | `\keypoint{}` | "Halves regret" becomes `\keypoint{Our estimator halves the regret of DRL across all benchmarks.}` |
| A theorem or result | Numbered `\textbf{Theorem N}` in `enumerate` | `\item \textbf{Theorem 1} (Upper bound). ...` |
| A math formulation | Display math `\[ ... \]` | `\[ R(\hat\pi) = \sup_{P} V(\pi^*_P) - V(\hat\pi) \]` |
| Comparative data | `booktabs` table | Comparison methods above `\midrule`, ours below, `\highlight{}` on the best value |
| A wide table or figure | `\helbredde` slot | Results by season and configuration |
| A planned figure (internal only) | `card gray` placeholder | "Regret vs n plot" becomes a placeholder with figure number and description |
| Paper section status | `booktabs` status table | "Theorems done, intro to write" |
| Open questions (internal only) | `enumerate` under the question section | See `references/questions.md` |
| Background or problem | Plain paragraph under the first section | Formal setup or brief context |
| A cited source | `[n]` in the text plus a `reflist` entry | See `references/macros.md`, section 8 |

## 2. Transformation Process

1. **Extract structure** from the input:
   - Supporting metrics become infoboxes in the section that the document type assigns: "Main Results" (left) for a Research Update, "Status" or "Headline Results" (right) for the other types
   - Narrative (what happened, how it works) goes to the left column as sections
   - Blockers and risks go to the right column as `card alert`
   - Action items go to the right column as a numbered list
   - Questions go to the end of the right column on page 1 (internal documents)
   - Sources go to the reference list on the last page (submission abstracts)
2. **Prioritize.** The headline number appears in the lead paragraph. Infoboxes show the supporting numbers, and tables carry the full comparison.
3. **Allocate** sections to pages and columns (section 5) and budget every column.
4. **Generate LaTeX** with the macros from `references/macros.md`.

## 3. Section Structure per Document Type

### Research Update (default for paper-driven internal work)

**Left column** (about 45 units)
1. **Problem Formulation**: formal setup in the notation of the domain
2. **Main Results**: infoboxes with supporting metrics, then 2 to 4 numbered contributions or theorems
3. **Benchmark Comparison** (or "Experimental Results"): `booktabs` table
4. `\keypoint{}`: one-sentence takeaway

**Right column** (about 40 units)
1. **Paper Progress**: `booktabs` table with section, proof, and experiment status
2. **Figures Needed**: `card gray` placeholders for planned figures
3. **Open Questions**: see `references/questions.md`

The status table leads the right column because it answers "where does the paper stand". With one placeholder or none, the comparison table can move to the right column.

### Weekly Update and Status Report

**Left column**
1. **Background**: brief context
2. **Content section**, named after the update type. Ask the user if unclear:
   - **Details This Week** or **Update** for weekly updates and status reports
   - **Our Approach** for project overviews and proposals
   - **Methods** for research summaries and technical reports
   - **Results** for experiment reports and evaluations
3. `\keypoint{}` (optional)

**Right column**
1. **Status** or **Headline Figures**: infoboxes with the most important numbers, `card alert` for blockers
2. **Supporting content**: tables, lists, next steps
3. **Questions for the Team**: always last

### Project Overview and Research Summary

Same frame as the Weekly Update: **Background** first, then **Our Approach** (overview) or **Methods** and **Results** (summary) on the left. On the right: headline figures, partners or publications, and **Questions for the Team**.

### Submission Abstract

| Section | Content | 1 page | 2 or more pages |
|---------|---------|--------|-----------------|
| **Motivation** | Problem, why it matters, related work in 2 to 4 neutral sentences | Left | Page 1, left |
| **Problem and Approach** | Formal setup, method | Left | Page 1, left |
| **Results** | Headline infoboxes, comparison table | Right | Page 1, right |
| **Contributions** | 2 to 4 numbered items | Right | Page 1, right |
| **Experimental Protocol** | Data, evaluation design, comparison conditions | one sentence in Results | Page 2 |
| **Discussion** | Interpretation of the results | omit | Page 2 |
| **Scope** | Assumptions and limits | one sentence | Page 2 |
| **Conclusion and Outlook** | Result in one sentence, next steps | Right, 2 sentences | Last page |
| **References** | `reflist` | Right, last | Last page, right, last |

A Submission Abstract has final figures only, no question section, and no progress table. The submission deadline stays out of the document and goes into `progress.md` and `SUMMARY.md`. Descriptions of cited work follow the Content Integrity rules in `SKILL.md`. `example-extended-abstract.tex` shows the two-page form.

### Conventions Across Types

| Document type | Left sections | Right sections | Footer |
|---------------|---------------|----------------|--------|
| **Research Update** | Problem Formulation, Main Results, Benchmarks, keypoint | Paper Progress, Figures Needed, Open Questions | Venue and deadline (bold) |
| **Weekly Update** | Background, Details This Week | Status, Next Week, Questions | Project name |
| **Project Overview** | Background, Our Approach | Headline Figures, Partners, Questions | University or project |
| **Research Summary** | Background, Methods, Results | Main Findings, Publications, Questions | University or project |
| **Submission Abstract** | Motivation, Problem and Approach | Results, Contributions, Conclusion, References | Venue and page limit |

- Research Updates start with "Problem Formulation" and end with "Open Questions"
- Other internal types start with "Background" and end with "Questions for the Team"
- Submission Abstracts start with "Motivation" and end with "References"

## 4. Slot Mappings

### Research Update

```
User provides: "Working on paper X for venue Y. We proved/built/evaluated Z, deadline is D."

\tittel        paper name
\projektname   \textbf{Target: VENUE YEAR}\enspace|\enspace\textbf{Deadline: Month Day, Year}
\abstractpages 1 unless the user chose more
\undertittel   Research Update\enspace|\enspace Month Day, Year (exact date)
\innledning    contribution + headline metric + target venue, with \highlight{}
\venstre       Problem Formulation
               Main Results (infoboxes, then numbered contributions)
               Benchmark Comparison (booktabs, \highlight{} on best values)
               keypoint
\hoyre         Paper Progress (booktabs status table)
               Figures Needed (card gray placeholders)
               Open Questions (enumerate)
```

### Weekly Update

```
User provides: "This week we did X, Y, Z. Main result was A. Blocked on B. Next week: C, D."

\innledning    date + headline result
\venstre       Background (1 paragraph) + Details This Week (list with run-in labels) + keypoint
\hoyre         Status (infoboxes, card alert for blockers)
               Next Week (numbered list)
               Questions for the Team (enumerate)
```

### Submission Abstract

```
User provides: a paper draft, notes, or results, plus venue and page limit.

\tittel        paper title
\projektname   \textbf{Extended abstract for VENUE YEAR}\enspace|\enspace\textbf{Page limit: N}
\abstractpages N (the user's choice, at most the page limit)
Page 1
  \undertittel authors\enspace|\enspace affiliation
  \innledning  contribution + setting + headline metric
  \venstre     Motivation, Problem and Approach
  \hoyre       Headline Results, Comparison, Contributions, keypoint
Page 2 to N
  \undertittel theme of the page
  \innledning  empty
  \helbredde   wide table or figure (optional)
  \venstre     Experimental Protocol, Discussion
  \hoyre       Scope, Conclusion and Outlook, References
```

## 5. Allocation Across Pages

For documents with two or more pages:

1. **Page 1 carries the whole argument in short form.** Claim, approach, headline result. It passes the Scan Test alone.
2. **Later pages add depth**: protocol, extended results, discussion, scope, references. Every later page contains information that page 1 lacks.
3. **Each section sits on one page in one column.** Long material gets split into two named sections.
4. **Wide material goes into `\helbredde`** at the top of a continuation page. Subtract its height from both column budgets.
5. **Internal documents** keep the question section on page 1, where every reader sees it. Later pages hold detailed metrics, trackers, and risk tables.
6. **Budget per column:** 45 line units with a lead paragraph, 50 without. Aim for 75% to 95% fill, and at least 60% on the last page.
7. **When the material is too thin for N pages**, propose N-1 pages. When it is too rich, cut from the last page upward, and ask the user before adding a page.
