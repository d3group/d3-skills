# Question Section Guide

Internal documents close with a question section: "Open Questions" for Research Updates, "Questions for the Team" for all other internal types. Submission Abstracts have no question section.

The questions are working tools. They move the conversation forward, surface blind spots, and invite the supervisor or peers to steer the work. In multi-page documents the section sits at the end of the right column on page 1.

## Design Principles

1. **Ask what you do not know.** Every question reflects a real uncertainty of the user
2. **Be specific.** "Should we add a fairness constraint to the objective?" beats "Any thoughts on the model?"
3. **Make each question actionable.** The answer changes what happens next
4. **Use 2 to 5 questions.** More than 5 dilutes the focus. Questions from the user's notes come first. Questions that you derive yourself are marked as such in the approval step, so the user can delete them

## Question Categories

Pick 2 to 5 questions across these categories. Few documents need all of them.

| Category | Purpose | Example |
|----------|---------|---------|
| **Direction** | Pivot, extend, or narrow the scope? | "Should we extend to the multi-agent setting, or focus on single-agent for the submission?" |
| **Methodology** | Is the technical approach sound? | "Is minimax regret the right criterion, or should we target Bayesian regret?" |
| **Validation** | Are we measuring the right things? | "Are synthetic benchmarks sufficient, or do we need a real-world dataset before submission?" |
| **Positioning** | How does the work relate to the literature? | "How should we position the paper relative to [Author 2024]: as an extension or as an alternative?" |
| **Prioritization** | What comes next? | "Given the deadline, should we prioritize the lower bound proof or the additional experiments?" |
| **Risk** | What could go wrong? | "The runtime scales as $O(n^2)$. Is this acceptable for the target application?" |
| **Feedback** | Direct request for critique | "Does the problem formulation in Section 2 need more formal notation?" |

## Templates by Document Type

**Research Update, "Open Questions"**
- 1 to 2 Methodology or Direction questions (guidance on technical choices)
- 1 Validation question (are the experiments convincing?)
- 1 Prioritization question (focus before the deadline)

**Weekly Update, "Questions for the Team"**
- 1 Prioritization question (what matters most this week)
- 1 to 2 Feedback questions (review of specific deliverables)
- 1 Risk question (flag blockers early)

**Project Overview, "Questions for the Team"**
- 1 to 2 Direction questions (scope and ambition)
- 1 Positioning question (relation to similar projects)

**Research Summary, "Questions for the Team"**
- 1 Validation question (strength of evidence)
- 1 Direction question (next steps, follow-up studies)

## Weak and Strong Questions

| Weak | Problem | Stronger |
|------|---------|----------|
| "Any feedback?" | Vague, invites silence | "Does the lead paragraph capture our main contribution?" |
| "Is this good?" | Leads to no action | "Should we replace the synthetic benchmark with real clinical data?" |
| "What do you think about the results?" | No focus | "Is the 15% improvement over DRL large enough to claim state of the art?" |
| "Should we continue?" | Binary, low information | "Should we submit to NeurIPS as planned, or strengthen the lower bound and target ICML?" |

## LaTeX Formatting

Use `enumerate`, so that supervisors can reply by number ("For Q2, let's switch to Bayesian regret"):

```latex
\sectionhead{Open Questions}
\begin{enumerate}
\item Should we extend the analysis to the multi-agent setting, or is single-agent sufficient for the NeurIPS submission?
\item Is minimax regret the right optimality criterion for the energy trading application?
\item Given the deadline, should we prioritize the lower bound proof or additional experiments on real data?
\end{enumerate}
```

## Confirmation

Show the drafted questions to the user before writing them into the `.tex` file, and write them after the user approves or edits them (see "Confirm generated questions" in `SKILL.md`). The wording rules of `references/writing-style.md` apply to questions as well.
