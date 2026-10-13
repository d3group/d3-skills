# Wording rules

Read this before writing or revising the first paragraph. Every rule states its reason, because a reason lets you decide the cases no table covers. The lint (`scripts/check_wording.py`) catches the countable part; the rest is judgment.

## Contents

1. State the claim directly
2. Related work
3. Claims and evidence
4. Sentence length and structure
5. Concise and scientific vocabulary
6. Marks of generated text
7. Terminology
8. Precision: who does what, and why it follows
9. Paragraphs, openings and endings
10. Numbers, figures and citations
11. Where these rules come from

## 1. State the claim directly

Say what the method is, what it does and what was measured. The "not X but Y" family announces the correction of something nobody said: the reader has to process X only to discard it, and the construction is the most recognizable mark of generated text.

Patterns to replace: "not X but Y", "not only X but also Y", "not just X", "X, not Y", "it is not about X, it is about Y", "more than just X", "goes beyond X", "rather than X", "instead of X". In German: "nicht X, sondern Y", "nicht nur ..., sondern auch", "statt X".

| Before | After |
|---|---|
| "Our method is not a heuristic but an exact algorithm." | "Our method is an exact algorithm." |
| "We not only reduce regret but also cut runtime." | "We reduce regret by 31 % and runtime by 58 %." |
| "The bottleneck is the solver, not the network." | "The solver accounts for 85 % of the training time." |
| "We optimize decisions rather than predictions." | "We train the forecast on the dispatch cost." |
| "This is more than just a forecasting problem." | "The forecast enters a scheduling decision with storage constraints." |
| "It is not about accuracy; it is about cost." | "We evaluate the forecasts by the cost of the schedules they produce." |

- If a contrast carries information, give both facts their own sentence: "The two-stage model minimizes RMSE. The decision-focused model minimizes regret."
- If the contrast is the finding (two conditions of an experiment), report both numbers: "Participants accepted 64 % of flawed outputs with the simple design and 41 % with the detailed design."
- If the text corrects a belief someone holds, cite who holds it, then state the own result: "Smith et al. (2021) attribute the gap to data quality. In our data, 70 % of the gap remains after cleaning."
- "Rather than" and "instead of" are warnings, not errors: keep them where the sentence names a design choice between two alternatives the text describes, and check whether the positive statement alone is enough.

## 2. Related work

For each cited work, state what it does, under which assumptions, and with which result. Then state the own setting as a fact. The difference between the two sentences is the positioning, and it needs no adjectives. Grades in either direction cost credibility with the reviewers who wrote the cited papers.

Avoid:

- **Dismissal:** "fails to", "suffers from", "struggles with", "overlooks", "neglects", "falls short", "merely", "simply", "only", "unlike previous approaches", "existing methods cannot", "naive" (outside established terms)
- **Courtesy praise before a dismissal:** "seminal", "pioneering", "groundbreaking", "a valuable first step", "has made significant strides", "laid the groundwork", "While prior work ..., it ..."

| Before | After |
|---|---|
| "While prior work has made significant strides, existing methods fail to handle state constraints." | "SPO+ [1] covers linear objectives without state dynamics. Storage scheduling adds inter-temporal state constraints." |
| "Unlike previous approaches, which suffer from high variance, our estimator is stable." | "The IPS estimator [2] has variance proportional to the inverse propensity. Our estimator bounds the weights at $\tau$." |
| "The seminal work of Smith [3] overlooks delayed feedback." | "Smith [3] studies immediate feedback. We study delays of up to 7 days." |
| "Naive two-stage baselines" | "Two-stage models trained on MSE" |
| "Research has largely neglected the role of display design." | "Studies of reliance on decision aids vary the aid's accuracy [4, 5]. The display design is held constant in these studies." |

Further conventions:

- **The gap is a statement about the literature, not a verdict on its authors.** "No study we found varies X and Y together" is checkable; "researchers have ignored X" is not.
- **Name methods by their published names** and cite them. When only a bare citation is known, describe the work at the level of its title. Never reconstruct authors, years, results or page numbers from memory.
- **Cite at the claim.** A sentence that says "evidence shows" carries its citations in that sentence, even when the next sentences elaborate.
- **Integral citation for one specific result**, with the author as grammatical subject: "Bertsimas and Kallus (2020) show that ..." **Parenthetical citation for a general claim** that several sources support: "... increases reliance (A, 2019; B and C, 2021)." In numeric styles the same distinction is "Smith et al. [3] show" versus "[3, 4, 7]".
- **State a source's finding, not its table.** "Smith et al. [3] find that delays double the variance" reads as a finding; "Smith et al. report 0.42 vs. 0.21 in Table 3" reads as a re-reading of their results. Keep a direct quote only where the source's own wording does work (a definition).
- **Words with an established technical meaning stay:** "naive Bayes", "robust optimization", "doubly robust estimator".
- **The own limits take the same neutral register:** "Scope: price-taking operator, perfect foresight of the battery state."

## 3. Claims and evidence

A claim is as strong as the evidence on the page. Overclaiming is the fastest way to lose a reviewer, and inflated wording reads as generated.

**The verb ladder.** Choose the verb by the evidence, not by the wish.

| Evidence | Verb |
|---|---|
| A formal proof | prove, derive, establish |
| Data, under stated conditions | show, find, observe, measure |
| Indirect or limited evidence (one setting, small sample, a proxy) | indicate, suggest |
| A mechanism that is argued but not tested | may, can, we expect, we hypothesize |

**Numbers replace intensifiers.**

| Before | After |
|---|---|
| "dramatically improves performance" | "lowers regret by 31 % on 24 months of market data" |
| "significantly faster" (no test) | "4.2 times faster (median over 50 instances)" |
| "remarkable accuracy" | "AUC 0.92 on the held-out year" |
| "vastly outperforms the state of the art" | "lowers cost by 6 % relative to SPO+ [1], the best of the four compared methods" |
| "a novel framework" | "a decomposition that separates forecast and dispatch errors" |

- **"Significant"** is reserved for a statistical test, and then the test is reported ("p < 0.01, two-sided t-test"). Otherwise give the size.
- **"Novel", "first", "unique"**: name what is new instead. "The first" requires a search the user confirms; otherwise "we found no study that ..." with the scope of the search.
- **"State-of-the-art"** only with the benchmark, the compared methods and the metric.
- **Causal words** ("effect", "drives", "leads to", "causes", "increases") only for causal designs: an experiment, or an identification strategy that is stated. Otherwise "is associated with", "co-occurs with".
- **Scope statements** come with every general claim: data, period, setting. "On German day-ahead prices from 2021 to 2023" belongs in the sentence that claims the result.
- **Hedge on data, be firm on structure.** Definitions, derivations, design decisions and the logic of the argument are stated without hedges. Empirical findings carry the hedge their evidence needs.
- **One hedge per claim.** "may potentially suggest" stacks three; "suggests" is enough.
- **A mechanism that holds only under a condition takes "if", not "because".** "Because" asserts that it always runs.
- **A simplification is stated as one:** "For simplicity, we assume linear costs." Do not present an assumption the authors expect to be false as a falsifiable claim.
- **Null results are reported plainly:** "The data provide no evidence for or against a direct effect." No apology, no spin.
- **A limitation is stated with its mechanism, then the text moves on:** "The panel's flat payment likely suppresses effort: participants have little reason to check outputs." Boundary conditions get their own section; the introduction does not open on what the paper does not claim.
- **Expected results in a proposal are expectations:** "We expect ..." and why.
- **Interpretations follow the numbers.** Check every interpretive sentence ("X explains most of the difference") against the numbers before writing it.

## 4. Sentence length and structure

A long sentence makes the reader hold several open clauses at once. The lint warns above the cap of the genre (paper 35 words, abstract and explainer 30, poster 25, slides 20) and reports an error 10 words above it; STE caps descriptive sentences at 25 and instructions at 20. A formula, a citation key and a number with its unit count as one word. The caps are the outer limit; the test is whether a reader new to the material must parse the sentence twice.

- **One idea per sentence.** A sentence that defines a construct, gives its condition and adds a concession is three sentences.
- **One comparison or one condition per sentence.** Numbers with different reference groups never share a sentence. Put "compared to X" at the front instead of a trailing "than X".
- **Condition and cause first, with a connective,** when they carry the claim: "Because the reviewer sees only part of what the system did, the approval can fail without a visible sign." A trailing "because" is fine for a detail attached to a claim already made.
- **No stacked relative clauses.** "the share of the evidence a decision requires that the log presents" becomes "the evidence the log presents, divided by the evidence the decision requires."
- **Split coordinate chains.** "X holds when A, whatever B, and it decreases as C" is three claims in one sentence.
- **No staccato either.** In running prose, more than two very short sentences in a row read as choppy. Vary the length; the exception is an explicit enumeration ("First, ... Second, ...").
- **Vertical lists for three or more parallel items** that each carry a condition or a number. List items share one grammatical form.

| Before | After |
|---|---|
| "Professionals using the tool produced work of more than 30 % higher quality on tasks within its capabilities but were 15 percentage points less likely than unaided colleagues to solve a task outside them." (39 words, two comparisons) | "On tasks within the tool's capabilities, professionals using it produced work of more than 30 % higher quality. Compared to unaided colleagues, they were 15 percentage points less likely to solve a task outside them." |
| "The estimator, which reweights logged actions by their propensities, which are estimated from the logging policy, is unbiased if these are correct." | "The estimator reweights logged actions by their propensities. We estimate the propensities from the logging policy. If the estimates are correct, the estimator is unbiased." |

## 5. Concise and scientific vocabulary

Every word earns its place. Filler delays the claim; nominal style hides the actor and the action.

**Filler and metadiscourse**

| Avoid | Write |
|---|---|
| "It is important to note that", "It is worth noting", "Needless to say" | delete and state the point |
| "in order to" | "to" |
| "due to the fact that" | "because" |
| "a large number of", "a significant amount of" | "many", "much", or the number |
| "in terms of", "with regard to" | name the relation ("in cost", "for the schedule") |
| "plays a crucial role in" | name the role |
| "In this section, we will discuss" | state the section's first claim |
| "It can be seen that", "It is clear that" | state what is seen |

**Verbs instead of nouns**

| Nominal | Verbal |
|---|---|
| "perform an analysis of" | "analyze" |
| "provide a description of" | "describe" |
| "lead to a reduction in" | "reduce" |
| "the decoupling of configuration from display" | "configuration and display are separate" |
| "Durchführung einer Analyse" | "analysieren" |

**Plain verbs and adjectives**

| Avoid | Write |
|---|---|
| "leverage", "utilize", "harness" | "use" |
| "delve into" | "examine", or state the finding |
| "showcase", "underscore" | "show" |
| "shed light on" | "clarify", or state the finding |
| "pave the way" | state what it enables |
| "key" (adjective) | "main", "central", or drop it |
| "crucial", "pivotal", "seamless", "cutting-edge", "comprehensive" | a specific, measurable description, or delete |
| "robust" (outside a technical meaning) | name the property: "stable across seeds", "valid under misspecification" |

**Both directions of word choice.** An ordinary thing takes the common word; a theoretical thing takes the field's term. Both errors come from the same lack of care.

- *Elevated word for an ordinary thing:* "the arrangement is designed" (what arrangement?), "grants latitude", "the stretch of work", "concealed", "scopes the claim". Write "the controls are set up", "gives more tasks", "the work one approval covers", "hidden", "limits the claim".
- *Generic word for a theoretical thing:* "we turn the difference into a quantity" when the paper defines a construct; "a tool" for an estimator; "an idea" for a mechanism. Theoretical acts keep their names: conceptualize, define, specify, operationalize, estimate, identify, bound.
- "Can" for what a system is able to do; "may" for possibility.
- No compressed adverbial objects: "cues change how selectively users rely" becomes "cues change which outputs users accept".

## 6. Marks of generated text

Readers and reviewers now recognize generated text by a handful of habits. Each one also has a cost of its own, which is the better reason to avoid it.

- **Dashes as punctuation.** No em-dashes, no spaced en-dashes, no `---` or spaced `--` in LaTeX. Use a comma, a colon, parentheses or a new sentence. Ranges keep their dash: `2024--2026`, `pp. 9--26`, `P1–P3`.
- **Marker vocabulary:** delve, tapestry, realm, landscape (figurative), multifaceted, intricate, meticulous, pivotal, paramount, nuanced, holistic, synergy, transformative, seamless, cutting-edge, game-changing, paradigm shift, testament, plethora, myriad, ever-evolving, rapidly evolving, embark, unlock, empower, foster, elevate, navigate (figurative), streamline, endeavor. Replace with the concrete thing.
- **Forced groups of three.** "fast, flexible, and scalable" when only one of the three is shown. List what the text supports, however many that is.
- **Rhetorical hooks.** "The result? X." "Here is the catch:" "What if ...?" State X.
- **Connective chains.** "Moreover, ... Furthermore, ... Additionally, ..." Use a connective only for the relation it names, and not two additive ones in a paragraph. Prefer the logical ones: because, therefore, however, if.
- **Same opener, three times.** Never three consecutive sentences that start with the same word ("We ... We ... We ...", "This ... This ..."); enumerations ("First, ... Second, ...") excepted.
- **Synonym cycling.** Calling one thing "approach", "framework", "method" and "pipeline" in turn. See section 7.
- **Generic openings.** "In today's rapidly evolving world", "X has gained significant attention", "With the advent of". Open with the situation and its tension: "Battery operators schedule on day-ahead forecasts, and forecast errors become dispatch costs."
- **Summary closers.** "In conclusion,", "Overall,", "In summary," followed by a restatement. A closing sentence lands a concrete consequence or a new claim.
- **Emphasis inflation.** Bold for the first mention of a defined term or the caller's emphasis macros, within the caller's limits. No bold sentences in running text, no exclamation marks.
- **Emoji and dingbats.** None. Icons are the caller's business (SVG icons in HTML decks).
- **Contractions.** None in scientific text: "do not", "it is".
- **Person.** "We" for the group's own work, also in a single-author paper unless the outlet or the faculty requires "I". Never "the authors" for the own team, never "one".

## 7. Terminology

The reader should never have to work out whether two words mean the same thing.

- **One term per concept, held across the document.** Pick the umbrella term and keep it. A paragraph that moves between "items", "steps", "actions" and "tool calls" for what an agent does makes the reader count four things.
- **One term pair per concept.** "Flawed/sound" for output quality; "correct" only for what a source or a judgment states. Write the pair into the term sheet.
- **A word with two senses in one text** is renamed in one of them. "Work" as the agent's activity in one paragraph and as the approval's function in the next is a collision.
- **Repeating a defined term is right; repeating a common noun is not.** The central construct may appear forty times without a synonym. "the answer ... The answer ... the answer" within two sentences is clumsy; keep the pronoun when it has one antecedent.
- **Define at first use, in words the reader already has.** Every noun inside a definition is either ordinary language or defined before.
- **Motivate before naming.** First the problem, then the distinction the problem forces, then the name. A section does not open on a definition or a list.
- **One new term at a time,** each connected to the one before and to the preceding section. Every term a passage announces must visibly do work in it.
- **Define once, repeat verbatim.** Before writing a definition, find every earlier statement of it (abstract included) and match the wording. If a later section needs more precision, restate the original first, then refine. A definition ends at the definition; examples go into the next sentence.
- **One phenomenon per definition.** A definition that covers two phenomena is split.
- **Ordinary words used in a narrow sense** are explained at first use ("flawed: less accurate than the user's own judgment"), or replaced by a word that needs no definition.
- **No coined terms for things the literature names.** A coinage is marked as the paper's own and says what it rests on.
- **Category discipline.** Before a term takes a verb or fills a table column, ask what kind of thing it is: design feature, perception, behavior, outcome, construct, mechanism or theory. "Trust" is a construct, not a mechanism; "perceived ease of use" is not a theory.
- **Verbs with one reading.** "Falls" can mean "decreases" and "belongs to"; write "decreases".
- **Abbreviations follow reader load.** Introduce at first use and then use them where the term is familiar and frequent. Spell them out in introductions and wherever a reader would have to page back to find them.
- **After a rename, search the whole document** for the old term, figures and tables included, and map every survivor onto a defined term.

## 8. Precision: who does what, and why it follows

- **Literal verbs for systems.** A model estimates, predicts, assigns, stores; it does not understand, know, think, see or touch. An agent acts on a file; it does not "touch" it. A bare comparative says what increased: "the agent's permissions expand", not "the agent acquires more".
- **Attribute each action to the component that performs it.** The interface renders, the agent acts, the user decides, the outcome results. Keep the loci apart, also in figure labels.
- **A pronoun only where exactly one antecedent fits.** "Two settings determine it" (coverage? the approval? the view?) names the referent. Do not over-apply: replacing an unambiguous "it" with a repeated noun is worse than the ambiguity it was meant to fix.
- **No vague reference in a load-bearing claim.** "the claim others read into it" names the claim: "what the organization takes the approval to certify: that a person checked the agent's actions".
- **Derive, do not report.** Every connective that claims a dependency (so, therefore, thus, hence, because, which means) has all its premises on the page, in the order the reader needs them. If A leads to B through C, C is written down. A claim comes after the steps that make it follow. Internal shorthand from working discussions is defined where used or replaced by the argument it stands for.
- **An abstract announces, the body derives.** An abstract may say "We explain why ease of use can lower decision quality" without the chain; it must not assert the dependency as established fact with a bare "so".

## 9. Paragraphs, openings and endings

- **The first sentence states the paragraph's topic**; the rest develops one topic.
- **Every topic shift has a hinge.** A paragraph does not open on a new subject cold: the first sentence connects to the previous paragraph's point and says what comes.
- **Given before new.** The end of one sentence becomes the start of the next.
- **A paragraph ends on a concrete consequence**, not on a hedge and not on a summary of itself.
- **Length follows the genre.** In papers, 4 to 8 sentences; a two-sentence paragraph is merged into its neighbour. In explainers, 2 to 5. In STE, at most 6. Definitional paragraphs may be short; do not pad them.
- **Sections open on a claim about the subject**, never on the document ("This section describes ...") and never on a definition before the reader knows why it is needed.
- **A text opens on the situation and its tension**, not on the importance of the topic.
- **The closing paragraph adds no new term.** It says plainly what the reader now has.

## 10. Numbers, figures and citations

- **Every number is explained where it stands:** a percentage with its base, a difference with its reference ("6 % lower cost than SPO+"), a total with its parts where the room must follow it. A number the reader cannot place is noise.
- **Digits for measured quantities** and anything with a unit; words for small counts in an argument ("two assumptions"). One decimal convention per document.
- **Every number traces to a source** (a result file, a table of the paper, the user's notes). Illustrative numbers are labelled illustrative and never borrow a real study's number.
- **A figure is read in the text.** Where a figure appears, one or two sentences say how to read it (axes, what the marks carry, where the effect sits); the text then uses it at the mechanism.
- **A sentence that describes a figure is a claim about the figure.** Check it against what is drawn whenever either changes.
- **Citations sit at the claim.** No page numbers in in-text citations unless the style requires them.

## 11. Where these rules come from

The rules merge two sources. The first is the house rules of the D3 skills (d3-abstract, d3-poster, d3-presentation, d3-explainer), which this skill now holds in one place. The second is the academic-voice skill of a group colleague, built from many rounds of line-by-line corrections. From it come the processing-load rules (section 4), the two directions of word choice (section 5), terminology discipline (section 7), "derive, do not report" (section 8), and the scope rules for revisions in SKILL.md.

Where the two disagreed, the house rule holds. The academic-voice skill uses a full "not X but Y" sentence as the carrier of a paper's thesis. Here, the thesis is stated directly and a contrast becomes two sentences. Its author-specific measurements (colon density, sentence-length bands of one corpus) are not carried over: they describe one person's voice, and this skill describes the group's floor.
