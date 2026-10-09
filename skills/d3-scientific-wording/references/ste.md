# Simplified Technical English (STE) mode

Read this when STE mode is on: by default in d3-explainer, as an option in d3-presentation and d3-poster, and on request for any other text. All rules of `rules.md` still apply; STE adds a stricter layer on top of them.

## Contents

1. What STE is, and what this mode takes from it
2. Technical nouns and technical verbs in research text
3. The writing rules, adapted
4. Where research conventions win
5. Before and after
6. How strict, per genre

## 1. What STE is, and what this mode takes from it

ASD-STE100 Simplified Technical English is a controlled language from the aerospace industry, now a standard for technical documentation in all sectors. Issue 9 (January 2025) has 53 writing rules in nine sections and a dictionary of approved words with one meaning each. The maintenance group gives the standard out free of charge on request at [asd-ste100.org](https://www.asd-ste100.org). STE makes text easier to read for readers whose first language is not English, and easier to translate. It also removes most ambiguity, which is the reason the explainers use it: their readers are co-authors from several countries who need the derivation, not the prose.

This mode applies the **writing rules** of STE, paraphrased and adapted to research text below. It does not include the approved dictionary. The plain-word preferences in section 3 are the group's own list in the spirit of STE, not the STE dictionary. When a deliverable must conform to the standard itself (a contract or a certification), work from the official document.

## 2. Technical nouns and technical verbs in research text

STE permits words of the subject field that are not in its dictionary: technical nouns and technical verbs. In research text these are the field's established terms, used in their technical meaning:

- **Technical nouns:** estimator, regret, propensity, constraint, solver, posterior, construct, hypothesis, dispatch, day-ahead market, policy (in reinforcement learning), and the project's defined constructs from the term sheet.
- **Technical verbs:** estimate, sample, regress, converge, optimize, discount, dispatch, randomize, bootstrap.

A word is technical only in its technical sense. "Policy" in reinforcement learning is technical; "policy" for a rule of the institute is not, and takes a plain word. Everything outside the technical vocabulary takes the plainest word that carries the meaning. Every technical noun is in the term sheet; a technical noun that the reader may not know is defined at first use.

## 3. The writing rules, adapted

### Words

- **One word, one meaning; one meaning, one word.** Use a word only in one sense in the whole text, and use the same word for the same thing every time (`rules.md`, section 7).
- **Plain words.** Use the simplest word that is correct.

  | Avoid | Use |
  |---|---|
  | utilize, employ, leverage | use |
  | commence, initiate | start |
  | terminate | stop, end |
  | prior to, subsequent to | before, after |
  | in order to | to |
  | approximately | about (keep "approximately" for a mathematical approximation) |
  | numerous | many |
  | facilitate | help, make possible |
  | demonstrate | show |
  | obtain | get, find (keep "we obtain" in a derivation) |
  | sufficient | enough (keep "sufficient" in "sufficient statistic" and "sufficient condition") |
  | ascertain, determine (as "find out") | find |
  | regarding, with regard to | about, for |
  | in the event that | if |

- **Verbs for actions, not nouns.** "Do a comparison of" becomes "compare"; "the estimation of the propensities is done" becomes "we estimate the propensities".
- **No phrasal verbs.** They have many meanings and are hard for non-native readers.

  | Phrasal verb | Use |
  |---|---|
  | carry out | do, perform, run |
  | find out, figure out | find, determine |
  | set up | prepare, configure, build |
  | point out | show, state |
  | look into, look at, go through | examine |
  | come up with, put forward | propose |
  | bring about | cause |
  | make up | form |
  | take into account | consider, include |
  | rule out | exclude |
  | break down | divide (or "fail") |
  | build up, cut down | increase, decrease |
  | turn out | is, proves to be |
  | end up | become, get |

- **Keep the small words.** Do not drop articles or "that" to make a sentence shorter: "Make sure that the slider is at zero", not "Make sure slider at zero".
- **No ambiguous pronouns.** Replace "it", "this" and "they" with the noun when more than one noun can be the antecedent.
- **No contractions, no Latin abbreviations in running text:** "for example" for "e.g.", "that is" for "i.e.", a complete list for "etc.". "Et al." in citations stays.

### Noun clusters

- **At most three nouns in a row.** Longer clusters hide which noun modifies which.

  | Cluster | Rewrite |
  |---|---|
  | "decision-focused learning loss gradient estimation" | "the estimate of the gradient of the decision-focused loss" |
  | "battery dispatch cost regret bound" | "the bound on the regret of the dispatch cost" |
  | "user reliance calibration intervention design" | "the design of an intervention that calibrates the reliance of users" |

- When a long cluster is the field's technical name, keep it, define it once, and then use it unchanged. A hyphen can join a compound modifier ("day-ahead price").

### Verbs

- **Simple tenses:** present for what holds and what the text shows, past for what was done in the study, future for what will be done. No progressive or perfect constructions where a simple tense works: "the model learns", not "the model is learning"; "we tested", not "we have been testing".
- **Past participles only as adjectives:** "the estimated propensities", "the trained model".
- **"-ing" forms only inside technical names:** "decision-focused learning", "rolling-horizon scheduling", "importance sampling". Elsewhere use a verb: "by reweighting the actions" becomes "we reweight the actions".
- **Active voice.** In instructions, always. In descriptions, as much as possible: "We estimate the propensities", not "The propensities are estimated". Passive is acceptable when the actor is unknown or does not matter ("The data were collected in 2023" for a public data set).

### Sentences

- **One topic per sentence.**
- **Descriptions: at most 25 words per sentence. Instructions: at most 20.** In an explainer, "Try" captions and usage steps are instructions; everything else is description. On slides, the cap is 20 words for all text on the slide; speaker notes are descriptions.
- **Condition first:** "If the propensity is below 0.01, the weight is clipped."
- **Vertical lists** for steps and for three or more parallel items.
- **Connecting words between sentences** whose topics are related: then, because, therefore, however, if, but. They replace the subordinate clauses that the length limit removes.

### Instructions (procedural text)

- **Imperative:** "Drag the slider to 0.3." "Run the build." "Compare the two curves."
- **One instruction per sentence,** unless two actions happen at the same time.
- **A note gives information, not an instruction.**

### Descriptions

- **Give only the information the reader needs.**
- **The first sentence of a paragraph states its topic.** One topic per paragraph.
- **At most six sentences per paragraph.**

### Punctuation and word count

- **No semicolons.** Write two sentences.
- **No dashes as punctuation** (already a house rule); hyphens join compound modifiers.
- **Parentheses** for symbols, units, abbreviations at first use and citations; not for asides.
- **Word count:** a formula, a number with its unit, a citation key and a hyphenated compound count as one word. The lint counts the same way.

## 4. Where research conventions win

STE was made for maintenance manuals. Five research conventions stay, because changing them would change the meaning or break the conventions of the field:

1. **Mathematical register.** "Let $x$ be ...", "for all", "such that", "if and only if", and theorem and lemma statements keep their formal wording. The sentence around a formula follows STE.
2. **Definitions of record.** A construct's definition stays verbatim as it is in the paper, even when it is longer than 25 words. Quote it, and explain it in the next sentences in STE.
3. **Established terms of the field,** including "-ing" terms and long technical names (section 2).
4. **Citations** keep their style ("Smith et al. (2021)", "[3, 4]").
5. **Hedging** follows `rules.md`, section 3. STE does not make a claim stronger or weaker than its evidence.

## 5. Before and after

| Standard scientific | STE |
|---|---|
| "Having established the regret decomposition, we now turn to the question of how the forecast error propagates into the dispatch cost, which, as we show below, depends on the curvature of the cost function." (36 words) | "The regret has two parts. Next, we show how the forecast error changes the dispatch cost. This change depends on the curvature of the cost function." |
| "The propensities are estimated using a logistic regression model fitted on the logged contexts; extreme weights are subsequently clipped." | "We estimate the propensities with a logistic regression on the logged contexts. Then we clip the extreme weights." |
| "By dragging the slider, the effect of a larger skip fraction on the success rate can be explored." | "Drag the slider. A larger skip fraction changes the success rate." |
| "We carry out a comparison of the two estimators across a number of sample sizes." | "We compare the two estimators at five sample sizes." |
| "This holds since it is bounded." | "The bound holds because the weights are bounded." |

## 6. How strict, per genre

- **Explainer (STE by default).** All prose, captions and notes. "Try" captions are instructions (imperative, at most 20 words); "Notice" is a description. Derivation reasons (`data-why`) are descriptions. Equations and pulled code are exempt.
- **Slides (option).** Titles, labels and bullets at most 20 words; speaker notes follow the description rules. Action titles stay complete sentences.
- **Poster (option).** Box text at most 25 words per sentence, bullets in the imperative or verb-first form, no semicolons.
- **Other genres (on request).** Apply all rules. Tell the user which research conventions of section 4 you kept.

Run the lint with `--ste`. It reports sentence length against the STE cap, semicolons, contractions, Latin abbreviations, phrasal verbs, passive constructions and paragraphs over six sentences. Noun clusters, "-ing" forms and one-meaning-per-word need your own pass.
