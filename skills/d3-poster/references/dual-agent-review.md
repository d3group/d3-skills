# Dual-Agent Review Reference

Full reviewer agent prompts, iteration loop, and the rationale for the 4-round cap. Load this file when you're about to dispatch the dual-agent verification (after Pass 2 of the multi-pass build is complete). SKILL.md has a short pointer to this file in the Dual-Agent Verification section.

## How to dispatch

Use the `Agent` tool with `subagent_type=Explore` (Read + Bash, no edit/write powers — exactly right for a reviewer). Dispatch BOTH agents in parallel (single message, two tool calls) so the user doesn't wait twice.

After both agents return, **paste their reports into chat verbatim** so the user sees what was checked, what passed, what failed. Then emit a one-paragraph orchestrator summary (Verdict: Ship | Iterate, fixes to apply) and apply fixes if Verdict is Iterate.

## Agent 1 prompt — Content Reviewer

```
You are reviewing a D3-branded research poster for CONTENT quality.

Inputs:
- LaTeX source: <abs path to poster.tex>
- Rendered PNG: <abs path to poster-150dpi.png>

Score each category 0-10 (10 = production-ready, 9 = ship-able with no fixes, <=8 = needs work). Be honest -- inflated scores waste the user's time.

Categories:
1. Glance test -- title + box headers + headline number telegraph the contribution at 2m?
2. Information hierarchy -- Motivation -> Problem -> Approach -> Results flows logically?
3. Writing style -- concise, active voice, parallel lists, no LLM-isms ("leverage", "delve into", "key insight" filler)?
4. Domain adaptation -- notation appropriate for the research field?
5. Emphasis discipline -- \highlight{} <= 3 per box, \keypoint{} <= 1 per box?
6. One message per box -- each box makes exactly one point?
7. Bibliography -- 3-5 references, bold venue names, no orphan citations?

Output strictly in this Markdown format (the orchestrator will parse it):

## Content Review
| Category | Score | Notes |
|---|---|---|
| Glance test | N/10 | one-line observation |
| Information hierarchy | N/10 | ... |
| Writing style | N/10 | ... |
| Domain adaptation | N/10 | ... |
| Emphasis discipline | N/10 | ... |
| One message per box | N/10 | ... |
| Bibliography | N/10 | ... |
| **Overall** | **N/10** | minimum of the above |

### Specific fixes (only if Overall < 9)
- File:line -- what to change and why
- ...
```

## Agent 2 prompt — Visual Design Reviewer

```
You are reviewing a D3-branded research poster for VISUAL DESIGN quality.

Inputs:
- Rendered PNG: <abs path to poster-150dpi.png>
- (LaTeX source available at <abs path> for cross-reference, but score on what's visible)

Score each category 0-10. Be honest.

Categories:
1. Layout -- 2- or 3-column grid, no content clipping at box edges, balanced box heights?
2. Header -- both logos render, title fully visible, no overlap with logo cell?
3. Box headers -- white text on d3-navy fill, consistent height across boxes?
4. Colors -- d3-navy for headers, d3-orange ONLY for highlights, no rogue colors (red/blue/green/random hex)?
5. Font -- Inter renders throughout (not a fallback serif)?
6. TikZ elements -- infoboxes, cards, placeholders fit inside parent boxes?
7. Tables -- aligned, booktabs rules render, no overfull hbox visible?
8. Whitespace -- no large empty regions, no cramped boxes?

Output strictly in this Markdown format:

## Visual Design Review
| Category | Score | Notes |
|---|---|---|
| Layout | N/10 | ... |
| Header | N/10 | ... |
| Box headers | N/10 | ... |
| Colors | N/10 | ... |
| Font | N/10 | ... |
| TikZ elements | N/10 | ... |
| Tables | N/10 | ... |
| Whitespace | N/10 | ... |
| **Overall** | **N/10** | minimum of the above |

### Specific fixes (only if Overall < 9)
- Visual observation -- proposed fix (file:line if applicable)
- ...
```

## Orchestrator summary template

After pasting both agent reports verbatim, emit this summary:

```markdown
## Review summary -- iteration N

**Content score:** X/10
**Visual score:** Y/10
**Verdict:** [Ship | Iterate]

[If Iterate:]
Fixes I'll apply now:
- [bullet from content review]
- [bullet from visual review]
- ...
```

If either Overall is < 9, automatically apply the fixes (read the cited file:line, edit, recompile, re-render) and run another round. If both Overall >= 9, stop and write the final scores into `final/README.md`.

## Iteration loop (capped at 4 rounds)

1. Dispatch both agents in parallel
2. Print BOTH reports verbatim in chat
3. Print the orchestrator summary
4. If Overall < 9 on either side: apply the fixes, recompile, re-render, go to (1) with iteration counter incremented
5. If both Overall >= 9: stop. Print:
   ```
   [HH:MM:SS] VERIFIED iter=N: Content X/10, Visual Y/10 -- ready to deliver
   ```
6. **Cap at 4 iterations.** If after 4 rounds either score is still below 9, surface the remaining issues to the user with a question: "I've hit my iteration cap. The remaining issues require your judgment -- here they are, what would you like me to do?" -- then stop.

## Why the cap?

Posters can get stuck in cosmetic loops (e.g., a `\keypoint{}` causes clipping → fixing it shifts the next box → spacing issues there → ad infinitum). After 4 iterations of mechanical fixes, the marginal gain is small and the user should be in the loop. The cap forces escalation when escalation is needed.

## Write the scores into final/README.md

When promoting drafts to final, capture the dual-agent verdict for posterity:

```markdown
# Poster: [Title]
- Venue: [conference / target]
- Date: YYYY-MM-DD
- Final scores: Content X/10, Visual Y/10
- Iterations to convergence: N
- Files: poster.tex, poster.pdf, baposter.cls, assets/
```
