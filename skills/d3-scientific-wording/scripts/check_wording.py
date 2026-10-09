# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""Check the wording of a D3 text against the d3-scientific-wording rules.

Run with uv (standard library only):

    uv run <skill-dir>/scripts/check_wording.py paper/sections/*.tex
    uv run <skill-dir>/scripts/check_wording.py talk/slides.py --ste
    uv run <skill-dir>/scripts/check_wording.py explainer/sections/*.html --genre explainer --ste

Reads .tex, .html, .md, .txt and slides.py (its string literals; `notes=` strings count as speaker notes).
Markup, math, code and comments are blanked before checking, so line numbers refer to the original file.
A formula counts as one word. Exit code 0 means no errors (warnings may remain), 1 means at least one error,
2 means a usage error.
"""

from __future__ import annotations

import argparse
import ast
import bisect
import html
import re
import sys
from dataclasses import dataclass
from pathlib import Path

# Sentence caps per genre: (warning above, error above). STE replaces them, see caps().
CAPS = {"paper": (35, 45), "rebuttal": (35, 45), "abstract": (30, 40), "explainer": (30, 40),
        "notes": (30, 40), "poster": (25, 35), "slides": (20, 30)}
GENRES = ("paper", "abstract", "poster", "slides", "explainer", "rebuttal")
PROSE_GENRES = {"paper", "rebuttal", "abstract", "explainer", "notes"}


def caps(genre: str, ste: bool) -> tuple[int, int]:
    warn, err = CAPS[genre]
    if ste:
        err = 20 if genre == "slides" else 25
        warn = err - 5
    return warn, err


# (level, label, pattern, advice). Patterns run case-insensitive on the masked text.
EN_RULES: list[tuple[str, str, str, str]] = [
    # Contrast framing
    ("E", "contrast", r"\bnot\s+(only|just|merely|simply|solely)\b", "state the positive claim directly"),
    ("E", "contrast", r"\bnot\b[^.;:!?\n]{0,80}?\bbut\b", "state the positive claim directly"),
    ("E", "contrast", r",\s+not\s+(?!(only|just|merely|simply|surprisingly|least|necessarily|yet|always|all|every|to)\b)\w",
     "state the positive claim directly"),
    ("E", "contrast", r"\b(it|this)\s+is\s+not\s+about\b|\b(it|this)'s\s+not\s+about\b", "state the positive claim directly"),
    ("E", "contrast", r"\b(is|are|was|were)n't\b[^.;:!?\n]{0,60}?\b(it's|it\s+is|they're|they\s+are)\b",
     "state the positive claim directly"),
    ("W", "contrast", r"\brather\s+than\b", "check whether the positive claim alone is enough"),
    ("W", "contrast", r"\binstead\s+of\b", "check whether the positive claim alone is enough"),
    ("W", "contrast", r"\bmore\s+than\s+(just|merely)\b|\bgo(es)?\s+beyond\b",
     "check whether the positive claim alone is enough"),
    # Tone toward related work
    ("E", "related-work", r"\bfail(s|ed|ing)?\s+to\b", "report what the cited work does and under which assumptions"),
    ("E", "related-work", r"\bsuffer(s|ed|ing)?\s+from\b", "report the property as a neutral fact"),
    ("E", "related-work", r"\bstruggl(e|es|ed|ing)\s+(to|with)\b", "report the property as a neutral fact"),
    ("E", "related-work", r"\b(overlook|neglect)(s|ed|ing)?\b", "state the scope of the cited work"),
    ("E", "related-work", r"\b(fall|falls|fell)\s+short\b", "give the measured difference"),
    ("E", "related-work", r"\bmerely\b", "delete the qualifier"),
    ("E", "related-work", r"\bunlike\s+(previous|prior|existing|earlier|traditional|conventional|other)\b",
     "describe both settings as facts in separate sentences"),
    ("E", "related-work",
     r"\b(existing|prior|previous|current|traditional|conventional)\s+(methods?|approaches|work|models?|studies)\s+"
     r"(cannot|can\s*not|are\s+unable|is\s+unable|do\s+not|does\s+not)\b",
     "report what the cited work does and under which assumptions"),
    ("E", "related-work", r"\b(seminal|pioneering|groundbreaking|ground-breaking|landmark)\b",
     "cite the work without grading it"),
    ("E", "related-work", r"\b(valuable|important|promising|useful|good)\s+first\s+step\b", "cite the work without grading it"),
    ("E", "related-work", r"\b(significant|great|considerable|remarkable)\s+(strides|progress)\b",
     "cite the work without grading it"),
    ("E", "related-work", r"\blaid\s+the\s+(groundwork|foundations?)\b", "cite the work without grading it"),
    ("W", "related-work", r"\bwhile\s+(prior|previous|existing|earlier|recent)\b",
     "check the sentence for a concession followed by a dismissal"),
    ("W", "related-work", r"\b(shortcoming|drawback|deficienc(y|ies)|weakness(es)?)\b", "prefer a factual scope statement"),
    ("W", "related-work", r"\b(naive(ly)?|simplistic|outdated|inferior)\b", "keep only as an established technical term"),
    ("W", "related-work", r"\blimited\s+to\b|\bignor(e|es|ed|ing)\b|\bsimply\b", "prefer a factual scope statement"),
    # Claims beyond the evidence
    ("E", "overclaim", r"\b(revolutionar(y|ize[sd]?)|unprecedented|game[\s-]?chang\w*|breakthroughs?|paradigm\s+shifts?)\b",
     "describe what changed, with a number"),
    ("E", "overclaim", r"\b(obviously|undoubtedly|unquestionabl[ey]|indisputabl[ey])\b",
     "state the evidence; the adverb adds nothing"),
    ("E", "overclaim", r"\bit\s+is\s+(evident|obvious|clear)\s+that\b", "state what the evidence shows"),
    ("W", "overclaim", r"\b(clearly|evidently|certainly)\b", "state the evidence; keep only if it qualifies a definition"),
    ("W", "overclaim", r"\bnovel(ty)?\b", "name what is new instead"),
    ("W", "overclaim",
     r"\bthe\s+first\s+(to|time|study|paper|work|method|approach|framework|model)\b|\bfor\s+the\s+first\s+time\b",
     "claim 'first' only after a confirmed search; otherwise 'we found no study that ...'"),
    ("W", "overclaim", r"\bstate[\s-]of[\s-]the[\s-]art\b|\bSOTA\b", "name the benchmark, the compared methods and the metric"),
    ("W", "overclaim", r"\bsignificant(ly)?\b", "only for a statistical test (report it); otherwise give the size"),
    ("W", "overclaim",
     r"\b(dramatic(ally)?|remarkabl[ey]|impressive(ly)?|vastly|massive(ly)?|tremendous(ly)?|substantial(ly)?|"
     r"considerabl[ey]|drastic(ally)?|huge(ly)?|extremely|exceptional(ly)?|outstanding|excellent|superior)\b",
     "give the number instead of the intensifier"),
    ("W", "overclaim", r"\boutperform\w*", "give metric, margin and conditions in the sentence"),
    ("W", "overclaim", r"\bprov(e|es|ed|en|ing)\b", "fine for a proof; for data write 'show' with the conditions"),
    ("W", "overclaim", r"\bsolve[sd]?\s+the\s+problem\b", "state what is solved and under which assumptions"),
    # Stacked hedges
    ("W", "hedge",
     r"\b(may|might|could|can)\s+(potentially|possibly|perhaps|conceivably)\b|\b(potentially|possibly|perhaps)\s+(may|might|could)\b"
     r"|\b(seems?|appears?)\s+to\s+(suggest|indicate|imply)\b|\bit\s+(may|might|could)\s+be\s+(argued|suggested|the\s+case)\s+that\b"
     r"|\bto\s+some\s+(extent|degree)\b",
     "one hedge per claim"),
    # Filler and metadiscourse
    ("E", "filler",
     r"\bit('s|\s+is)\s+(important|worth|interesting|crucial|essential)\s+to\s+(note|mention|point\s+out|emphasi[sz]e|highlight)\b"
     r"|\bworth\s+(noting|mentioning)\b|\bneedless\s+to\s+say\b|\bit\s+goes\s+without\s+saying\b",
     "delete and state the point"),
    ("E", "filler", r"\bin\s+order\s+to\b", 'write "to"'),
    ("E", "filler", r"\b(due|owing)\s+to\s+the\s+fact\s+that\b", 'write "because"'),
    ("E", "filler", r"\bplay(s|ed|ing)?\s+an?\s+(crucial|key|vital|pivotal|critical|central|important|significant|major|essential)\s+role\b",
     "name the specific role"),
    ("E", "filler", r"\b(at\s+the\s+end\s+of\s+the\s+day|first\s+and\s+foremost|last\s+but\s+not\s+least|as\s+a\s+matter\s+of\s+fact)\b",
     "delete"),
    ("E", "filler", r"\bit\s+(can|could)\s+be\s+(seen|observed|noted)\s+that\b", "state what is seen"),
    ("W", "filler", r"\ba\s+(large|great|significant|considerable|substantial|wide)\s+(number|amount|range|variety)\s+of\b",
     '"many", "much", or the number'),
    ("W", "filler", r"\bin\s+terms\s+of\b|\bwith\s+regard\s+to\b|\bin\s+the\s+context\s+of\b", "name the relation directly"),
    ("W", "filler",
     r"\b(in\s+this|the\s+following)\s+(section|chapter|subsection),?\s+we\s+(will\s+)?(discuss|present|describe|introduce|explore|outline)\b"
     r"|\bthe\s+(remainder|rest)\s+of\s+(this|the)\s+(paper|article|chapter)\s+is\s+(organi[sz]ed|structured)\b",
     "metadiscourse: state the section's first claim (keep a roadmap only where the outlet expects one)"),
    ("W", "filler", r"(?:^|(?<=[.!?]\s))\s*(in\s+conclusion|in\s+summary|to\s+summari[sz]e|to\s+sum\s+up|overall|all\s+in\s+all),",
     "a closing sentence lands a consequence; drop the label"),
    # Marker vocabulary
    ("E", "marker", r"\bdelv(e|es|ed|ing)\b", 'write "examine" or state the finding'),
    ("E", "marker", r"\bleverag(e|es|ed|ing)\b", 'write "use"'),
    ("E", "marker", r"\butili[sz](e|es|ed|ing)\b", 'write "use"'),
    ("E", "marker", r"\bharness(es|ed|ing)?\b", 'write "use"'),
    ("E", "marker", r"\b(showcas|underscor)(e|es|ed|ing)\b", 'write "show"'),
    ("E", "marker", r"\bshed(s|ding)?\s+(new\s+)?light\s+on\b", 'write "clarify" or state the finding'),
    ("E", "marker", r"\bpav(e|es|ed|ing)\s+the\s+way\b", "state what it enables"),
    ("E", "marker",
     r"\b(crucial(ly)?|pivotal|seamless(ly)?|cutting[\s-]edge|transformative|holistic(ally)?|synerg\w*|multifaceted|paramount|"
     r"meticulous(ly)?|tapestry|realm|plethora|myriad|testament|ever[\s-]evolving|rapidly\s+evolving|fast[\s-]paced|"
     r"streamlin\w*|endeavou?rs?|embark\w*)\b",
     "use a specific, measurable description, or delete"),
    ("E", "marker", r"\bcomprehensive(ly)?\b", "delete, or name what is covered"),
    ("E", "marker", r"\bunlock(s|ed|ing)?\s+the\s+(full\s+)?potential\b|\bempower\w*", "say what becomes possible"),
    ("E", "marker", r"\bhere('s|\s+is)\s+the\s+(catch|thing|twist|kicker)\b|\blet's\s+(dive|delve)\b|\blet\s+us\s+dive\b",
     "state the point"),
    ("W", "marker", r"\b(intricate|nuanced|landscapes?|navigat\w+|foster\w*|elevat\w+|notabl[ey]|importantly|insofar)\b",
     "check: say the concrete thing"),
    ("W", "marker", r"\bkey\b", 'write "main" or "central", or drop it (fine as a technical term)'),
    ("W", "marker", r"\brobust(ly|ness)?\b", "fine as a technical term, otherwise name the property"),
    ("W", "rhetorical", r"\b(the\s+)?(result|answer|catch|outcome|verdict|takeaway|twist)\?\s", "state it as a sentence"),
    # Contractions (errors in STE mode)
    ("W", "contraction", r"\b\w+n't\b|\b(it|that|there|what|here|let|who)'s\b|\b\w+'(re|ve|ll|m)\b",
     "write the full form"),
]

DE_RULES: list[tuple[str, str, str, str]] = [
    ("E", "contrast", r"\bnicht\s+nur\b", "state the positive claim directly"),
    ("E", "contrast", r"\bnicht\b[^.;:!?\n]{0,80}?\bsondern\b", "state the positive claim directly"),
    ("W", "contrast", r"\b(an)?statt\b", "check whether the positive claim alone is enough"),
    ("E", "related-work", r"\b(scheiter\w*|versäum\w*|vernachlässig\w*|übersieh\w*|übersehen|wegweisend\w*|bahnbrechend\w*)\b",
     "report what the cited work does, without grading it"),
    ("W", "related-work", r"\b(lediglich|bloß|naiv\w*)\b", "prefer a factual scope statement"),
    ("E", "filler", r"\bes\s+ist\s+(wichtig|erwähnenswert|hervorzuheben|anzumerken)\b|\ban\s+dieser\s+Stelle\s+sei\b",
     "delete and state the point"),
    ("W", "filler", r"\bim\s+Rahmen\s+(von|des|der|dieser|dieses)\b|\bin\s+Bezug\s+auf\b|\bhinsichtlich\b",
     "name the relation directly"),
    ("E", "marker", r"\b(nahtlos\w*|ganzheitlich\w*|Synergie\w*|revolution\w*|zukunftsweisend\w*|Paradigmenwechsel)\b",
     "use a specific, measurable description, or delete"),
    ("W", "overclaim", r"\b(signifikant\w*|neuartig\w*|erstmal(s|ig\w*)|enorm\w*|massiv\w*|innovativ\w*|dramatisch\w*|rasant\w*|bahnbrechend\w*)\b",
     "give the number, or name what is new"),
]

PHRASAL = [  # (verb forms, particle, plain verb)
    (r"carr(?:y|ies|ied|ying)", r"out", "do, perform, run"),
    (r"(?:find|finds|found|finding|figur(?:e|es|ed|ing))", r"out", "find, determine"),
    (r"(?:set|sets|setting)", r"up", "prepare, configure, build"),
    (r"(?:point|points|pointed|pointing)", r"out", "show, state"),
    (r"(?:look|looks|looked|looking)", r"(?:into|at)", "examine"),
    (r"(?:go|goes|went|gone|going)", r"through", "examine"),
    (r"(?:come|comes|came|coming)", r"up\s+with", "propose"),
    (r"(?:put|puts|putting)", r"forward", "propose"),
    (r"(?:bring|brings|brought|bringing)", r"about", "cause"),
    (r"(?:make|makes|made|making)", r"up", "form"),
    (r"(?:take|takes|took|taken|taking)", r"into\s+account", "consider, include"),
    (r"rul(?:e|es|ed|ing)", r"out", "exclude"),
    (r"(?:break|breaks|broke|broken|breaking)", r"down", "divide (or: fail)"),
    (r"(?:build|builds|built|building)", r"up", "increase"),
    (r"(?:cut|cuts|cutting)", r"down", "decrease"),
    (r"(?:turn|turns|turned|turning)", r"out", "is, proves to be"),
    (r"(?:end|ends|ended|ending)", r"up", "become, get"),
    (r"(?:get|gets|got|getting)", r"rid\s+of", "remove"),
    (r"(?:sum|sums|summed|summing)", r"up", "summarize"),
]

STE_RULES: list[tuple[str, str, str, str]] = [
    ("W", "latin", r"\be\.\s?g\.|\bi\.\s?e\.|\betc\.|\bcf\.|\bviz\.|\bvice\s+versa\b",
     'STE: "for example", "that is", or the complete list'),
] + [("W", "phrasal-verb", rf"\b{verb}\s+{particle}\b", f"STE: one verb ({plain})") for verb, particle, plain in PHRASAL]

PASSIVE = re.compile(
    r"\b(?:is|are|was|were|be|been|being)\s+(?:\w+ly\s+)?"
    r"(?!(?:indeed|need|speed|seed|feed|red|bed|shed|bred|wed|based|interested|related|concerned|limited|supposed|used\s+to|"
    r"biased|unbiased|bounded|unbounded|correlated|uncorrelated|distributed|fixed|constrained|unconstrained|skewed|censored|"
    r"truncated|balanced|unbalanced|nested|detailed|advanced|sophisticated|complicated|experienced|motivated|informed|"
    r"uninformed|undefined|unknown|unobserved|observed)\b)"
    r"(?:\w+ed|shown|given|done|made|taken|known|seen|found|chosen|drawn|written|built|kept|held|run|put|brought|sent|spent|"
    r"left|lost|meant|paid|told|understood|driven|grown|hidden|led|read|set|sold|thought|won)\b",
    re.IGNORECASE)

# Established technical terms that contain a flagged word. Matches inside these are skipped.
TECHNICAL = re.compile(
    r"doubly[\s-]+robust|distributionally[\s-]+robust"
    r"|robust\s+(?:optimi[sz]ation|regression|statistics|control|estimat\w+|standard\s+errors?|counterparts?|mdps?|solutions?)"
    r"|na[i\u00ef]ve\s+bayes|(?:public|private|primary|foreign|secret|api|encryption)[\s-]+keys?|key[\s-]+value"
    r"|key\s+performance\s+indicators?|(?:financial|operating)\s+leverage|leverage\s+(?:ratios?|effects?|scores?|points?)"
    r"|high[\s-]leverage|(?:loss|fitness|energy|optimi[sz]ation)\s+landscapes?"
    r"|statistically\s+(?:in)?significan\w*|significan(?:ce|t)\s+(?:levels?|tests?|at)\b|(?:not|non)[\s-]significant\w*"
    r"|test\s+harness(?:es)?",
    re.IGNORECASE)

ABBREV = {"e.g", "i.e", "al", "fig", "figs", "eq", "eqs", "eqn", "sec", "secs", "tab", "ref", "refs", "vs", "cf",
          "approx", "resp", "no", "nos", "dr", "prof", "mr", "ms", "mrs", "p", "pp", "vol", "ch", "chap", "app", "thm",
          "lem", "prop", "def", "cor", "alg", "ass", "assm", "ca", "bzw", "z.b", "d.h", "u.a", "abb", "gl", "kap",
          "vgl", "bspw", "st", "jr", "sr", "inc", "ltd", "co", "corp", "ed", "eds", "min", "max", "u.s", "s"}
ENUMERATORS = {"first", "second", "third", "fourth", "fifth", "finally", "next", "then", "step", "erstens",
               "zweitens", "drittens", "schließlich"}
ADDITIVE = re.compile(r"(moreover|furthermore|additionally|in\s+addition|also|außerdem|zudem|darüber\s+hinaus)\b", re.I)
WORD = re.compile(r"[^\W_][\w'\u2019\-]*")

INVISIBLE = [  # (class, pattern, advice)
    ("zero-width", "[\u200b\u200c\u200d\u2060\u180e]", "remove with the optional cleaning step (SKILL.md, Step 5)"),
    ("byte-order mark", "(?<!^)\ufeff", "remove with the optional cleaning step (SKILL.md, Step 5)"),
    ("bidi control", "[\u200e\u200f\u202a-\u202e\u2066-\u2069\u061c]", "remove with the optional cleaning step (SKILL.md, Step 5)"),
    ("tag character", "[\U000e0000-\U000e007f]", "remove with the optional cleaning step (SKILL.md, Step 5)"),
    ("invisible operator or filler", "[\u2061-\u2064\u115f\u1160\u3164\uffa0\ufff0-\ufff8]",
     "remove with the optional cleaning step (SKILL.md, Step 5)"),
    ("variation selector", "[\ufe00-\ufe0f]", "remove unless it belongs to a symbol you kept on purpose"),
    ("soft hyphen", "\u00ad", "remove with the optional cleaning step (SKILL.md, Step 5)"),
    ("unusual space", "[\u00a0\u2000-\u200a\u202f\u205f\u3000]",
     "intended? the cleaning step normalizes it unless run with --no-normalize-spaces"),
]
EMOJI = re.compile("[\U0001F000-\U0001FAFF]")
DINGBAT = re.compile("[\u2600-\u27bf]")


@dataclass
class Finding:
    line: int
    level: str
    label: str
    snippet: str
    advice: str


@dataclass
class Sentence:
    start: int
    end: int
    text: str
    words: int
    terminal: bool
    para: int


# ---------------------------------------------------------------- masking: blank everything that is not prose

class Mask:
    """The text with non-prose blanked to spaces (newlines kept), plus unit breaks and extra findings."""

    def __init__(self, text: str, start_blank: bool = False) -> None:
        self.buf = [("\n" if c == "\n" else " ") for c in text] if start_blank else list(text)
        self.breaks: set[int] = set()
        self.dashes: list[tuple[int, str, str]] = []   # (position, level, snippet) found while masking entities
        self.notes: list[tuple[int, int]] = []          # spans of speaker notes (slides.py)

    def text(self) -> str:
        return "".join(self.buf)

    def blank(self, a: int, b: int) -> None:
        for i in range(a, b):
            if self.buf[i] != "\n":
                self.buf[i] = " "

    def formula(self, a: int, b: int) -> None:
        """A formula counts as one word."""
        self.blank(a, b)
        self.buf[a] = "x"

    def sub(self, pattern: str, flags: int = 0, how: str = "blank") -> None:
        for m in re.finditer(pattern, self.text(), flags):
            if how == "formula":
                self.formula(*m.span())
            else:
                self.blank(*m.span())


def group_end(text: str, i: int, open_ch: str = "{", close_ch: str = "}") -> int:
    """Index of the bracket closing the one at text[i], or -1."""
    depth = 0
    j = i
    while j < len(text):
        ch = text[j]
        if ch == "\\":
            j += 2
            continue
        if ch == open_ch:
            depth += 1
        elif ch == close_ch:
            depth -= 1
            if depth == 0:
                return j
        j += 1
    return -1


def skip_space(text: str, i: int) -> int:
    while i < len(text) and text[i] in " \t\n":
        i += 1
    return i


TEX_DROP = {  # commands whose first n brace arguments are not prose
    "ref": 1, "eqref": 1, "autoref": 1, "cref": 1, "Cref": 1, "pageref": 1, "label": 1, "url": 1, "href": 1,
    "includegraphics": 1, "input": 1, "include": 1, "usepackage": 1, "RequirePackage": 1, "documentclass": 1,
    "bibliography": 1, "bibliographystyle": 1, "addbibresource": 1, "definecolor": 3, "colorlet": 2, "color": 1,
    "pagecolor": 1, "textcolor": 1, "colorbox": 1, "fcolorbox": 2, "setlength": 2, "addtolength": 2, "setcounter": 2,
    "vspace": 1, "hspace": 1, "newcommand": 1, "renewcommand": 1, "providecommand": 1, "DeclareMathOperator": 2,
    "newenvironment": 1, "begin": 1, "end": 1, "hypersetup": 1, "graphicspath": 1, "geometry": 1,
    "usetikzlibrary": 1, "tikzset": 1, "pgfplotsset": 1, "fontsize": 2, "rule": 2, "resizebox": 2, "scalebox": 1,
    "raisebox": 1, "parbox": 1, "multicolumn": 2, "multirow": 2, "newlength": 1, "setbeamercolor": 2,
    "setbeamerfont": 2, "setbeamertemplate": 1, "pgfmathsetmacro": 2, "usetheme": 1, "usecolortheme": 1,
    "usefonttheme": 1, "setmainfont": 1, "setsansfont": 1, "setmonofont": 1, "bibitem": 1, "thispagestyle": 1,
    "pagestyle": 1, "selectlanguage": 1, "foreignlanguage": 1,
}
TEX_ENV_ARGS = {"tabular": 1, "tabular*": 2, "tabularx": 2, "tabulary": 2, "array": 1, "longtable": 1,
                "projecttimeline": 2}   # environment arguments that are not prose
TEX_HEADINGS = {  # commands whose first n arguments are headings or separate units
    "section": 1, "subsection": 1, "subsubsection": 1, "paragraph": 1, "subparagraph": 1, "chapter": 1, "part": 1,
    "title": 1, "subtitle": 1, "frametitle": 1, "framesubtitle": 1, "sectionhead": 1, "headerbox": 1,
    "columnheader": 1, "onecol": 2, "twocol": 3, "twocoltakeaway": 4, "showsection": 1, "keypoint": 1, "caption": 1,
    "author": 1, "date": 1, "institute": 1, "projektname": 1, "workpackage": 1,
}
TEX_HEADING_DROP = {"headerbox": 1, "workpackage": 5}   # arguments after the heading that are not prose
MATH_ENVS = r"(?:equation|align|alignat|gather|multline|eqnarray|flalign|displaymath|math|dmath)\*?"
TIKZ_LINE = re.compile(r"^\s*\\(draw|path|fill|filldraw|clip|addplot|shade|shadedraw|coordinate|foreach|pgfmathsetmacro)\b")


def mask_tex(text: str) -> Mask:
    mk = Mask(text)
    mk.sub(r"(?<!\\)%[^\n]*")
    mk.sub(r"\\begin\{(verbatim\*?|Verbatim|lstlisting|minted|comment)\}.*?\\end\{\1\}", re.S)
    mk.sub(r"\\begin\{(" + MATH_ENVS + r")\}.*?\\end\{\1\}", re.S, "formula")
    for pat in (r"\$\$.*?\$\$", r"\\\[.*?\\\]", r"\\\(.*?\\\)", r"(?<!\\)\$(?:\\.|[^$\\])+?\$"):
        mk.sub(pat, re.S, "formula")
    lines = text.split("\n")
    starts = [0]
    for ln in lines[:-1]:
        starts.append(starts[-1] + len(ln) + 1)
    for k, ln in enumerate(lines):  # TikZ paths carry coordinates, not prose
        if TIKZ_LINE.match(ln):
            mk.blank(starts[k], starts[k] + len(ln))
    mk.sub(r"\\[,;:!> ]")           # spacing commands; \; would read as a semicolon
    cur = mk.text()
    for m in re.finditer(r"\\\\(\[[^\]]*\])?", cur):  # line break: a new unit
        mk.blank(*m.span())
        mk.breaks.add(m.start())
    for m in re.finditer(r"(?<!\\)&", cur):           # table cell separator
        mk.blank(*m.span())
        mk.breaks.add(m.start())
    cur = mk.text()
    for m in re.finditer(r"\\([a-zA-Z@]+)(\*?)", cur):
        if mk.buf[m.start()] != "\\":   # blanked by an earlier command
            continue
        name = m.group(1) + m.group(2)
        start, i = m.start(), m.end()
        mk.blank(start, i)
        if name == "item":
            mk.breaks.add(start)
        drop = 1 if re.fullmatch(r"[a-z]*cite[a-z]*\*?", name) else TEX_DROP.get(m.group(1))
        if m.group(1) == "begin":
            env = re.match(r"\s*\{([^}]*)\}", cur[i:])
            if env and env.group(1) in TEX_ENV_ARGS:
                drop = 1 + TEX_ENV_ARGS[env.group(1)]
        if drop is not None:
            done = 0
            while True:
                j = skip_space(cur, i)
                if j < len(cur) and cur[j] == "[":
                    e = group_end(cur, j, "[", "]")
                    if e < 0:
                        break
                    mk.blank(j, e + 1)
                    i = e + 1
                    continue
                if j < len(cur) and cur[j] == "{" and done < drop:
                    e = group_end(cur, j)
                    if e < 0:
                        break
                    mk.blank(j, e + 1)
                    i = e + 1
                    done += 1
                    continue
                break
        elif m.group(1) in TEX_HEADINGS:
            mk.breaks.add(start)
            for _ in range(TEX_HEADINGS[m.group(1)]):
                j = skip_space(cur, i)
                while j < len(cur) and cur[j] == "[":
                    e = group_end(cur, j, "[", "]")
                    if e < 0:
                        break
                    mk.blank(j, e + 1)
                    j = skip_space(cur, e + 1)
                if j >= len(cur) or cur[j] != "{":
                    break
                e = group_end(cur, j)
                if e < 0:
                    break
                mk.blank(j, j + 1)
                mk.blank(e, e + 1)
                mk.breaks.add(e)
                i = e + 1
            for _ in range(TEX_HEADING_DROP.get(m.group(1), 0)):
                j = skip_space(cur, i)
                if j >= len(cur) or cur[j] != "{":
                    break
                e = group_end(cur, j)
                if e < 0:
                    break
                mk.blank(j, e + 1)
                i = e + 1
        elif i < len(cur) and cur[i] == "[":
            e = group_end(cur, i, "[", "]")
            if e > 0:
                mk.blank(i, e + 1)
    cur = mk.text()
    for m in re.finditer(r"\\([%&_#$])", cur):    # escaped characters keep the character
        mk.buf[m.start()] = " "
    for m in re.finditer(r"[{}~\\]", mk.text()):
        mk.buf[m.start()] = " "
    return mk


HTML_BLOCK = {"p", "div", "li", "ul", "ol", "h1", "h2", "h3", "h4", "h5", "h6", "br", "hr", "td", "th", "tr", "table",
              "section", "article", "figcaption", "figure", "details", "summary", "blockquote", "dt", "dd", "header",
              "footer", "nav", "aside", "caption", "button", "option", "label", "main", "body", "title"}
HTML_PROSE_ATTR = re.compile(r"\b(data-why|title|alt|aria-label|data-note|data-caption)\s*=\s*\"([^\"]*)\"")


def mask_html(mk: Mask) -> Mask:
    mk.sub(r"<span class=\"usd\">\$</span>")
    mk.sub(r"<!--.*?-->", re.S)
    mk.sub(r"<(script|style|pre|code|svg|math|template|textarea)\b[^>]*>.*?</\1\s*>", re.S | re.I)
    for pat in (r"\$\$.*?\$\$", r"\\\[.*?\\\]", r"\\\(.*?\\\)"):
        mk.sub(pat, re.S, "formula")
    mk.sub(r"(?<![\\$\w])\$(?=\S)[^$\n]{1,300}?(?<=\S)\$(?!\w)", 0, "formula")
    mk.sub(r"\[\[[^\]\n]*\]\]")                   # source chips of the explainer
    mk.sub(r"\{fig(:[\w-]+)?\}", 0, "formula")      # figure references of the explainer count as one word
    for m in re.finditer(r"<span class=\"(h|try|notice)\">.*?</span>", mk.text(), re.S):   # run-in headings, caption parts
        mk.breaks.update(m.span())
    cur = mk.text()
    for m in re.finditer(r"</?([a-zA-Z][\w-]*)\b[^>]*>", cur):
        mk.blank(*m.span())
        if m.group(1).lower() in HTML_BLOCK:
            mk.breaks.add(m.start())
        for a in HTML_PROSE_ATTR.finditer(m.group(0)):
            s, e = m.start() + a.start(2), m.start() + a.end(2)
            mk.buf[s:e] = list(cur[s:e])
            mk.breaks.add(s)
            mk.breaks.add(e)
    cur = mk.text()
    for m in re.finditer(r"&(#\d+|#x[0-9a-fA-F]+|[a-zA-Z]+);", cur):
        ch = html.unescape(m.group(0))
        if ch in ("\u2013", "\u2014"):
            before = cur[m.start() - 1:m.start()]
            after = cur[m.end():m.end() + 1]
            if ch == "\u2014" or before.isspace() or after.isspace():
                mk.dashes.append((m.start(), "E", m.group(0)))
            mk.blank(*m.span())
        elif len(ch) == 1 and not ch.isspace():
            mk.blank(*m.span())
            mk.buf[m.start()] = "'" if ch in "\u2018\u2019" else ch
        else:
            mk.blank(*m.span())
    return mk


def mask_md(text: str) -> Mask:
    mk = Mask(text)
    if text.startswith("---\n"):
        end = text.find("\n---", 4)
        if end > 0:
            mk.blank(0, end + 4)
    mk.sub(r"(?ms)^(```|~~~).*?^\1[^\n]*$")
    mk.sub(r"`[^`\n]+`")
    for pat in (r"\$\$.*?\$\$", r"(?<![\\$\w])\$(?=\S)[^$\n]{1,300}?(?<=\S)\$(?!\w)"):
        mk.sub(pat, re.S, "formula")
    mk.sub(r"(?m)^\s*([-*_])(\s*\1){2,}\s*$")
    cur = mk.text()
    for m in re.finditer(r"(?m)^(\s*)(#{1,6}\s|[-*+]\s|\d+[.)]\s|>\s?)", cur):
        mk.blank(m.start(2), m.end(2))
        mk.breaks.add(m.start(2))
    for m in re.finditer(r"(?m)^\s*\|?(\s*:?-{3,}:?\s*\|)+\s*:?-*:?\s*$", cur):   # table separator rows
        mk.blank(*m.span())
    for m in re.finditer(r"\|", mk.text()):
        mk.blank(*m.span())
        mk.breaks.add(m.start())
    cur = mk.text()
    for m in re.finditer(r"(!?)\[([^\]\n]*)\]\([^)\n]*\)", cur):
        if m.group(1):
            mk.blank(*m.span())
        else:
            mk.blank(m.start(), m.start(2))
            mk.blank(m.end(2), m.end())
    return mask_html(mk)


def looks_like_prose(s: str) -> bool:
    if len(re.findall(r"[A-Za-zÄÖÜäöüß]{2,}", s)) < 2 or not re.search(r"\s", s.strip()):
        return False
    if re.search(r"^\s*[\w-]+\s*:\s*[^;]+;|;\s*[\w-]+\s*:", s):          # CSS
        return False
    if re.fullmatch(r"[MmLlHhVvCcSsQqTtAaZz0-9 ,.\-]+", s.strip()):      # SVG path data
        return False
    if re.search(r"=>|\bfunction\b|\bdocument\.|\b(const|let|var|return)\s|[;{}]\s*\n", s) and s.count(";") + s.count("{") >= 2:
        return False                                                       # JavaScript
    return True


def mask_py(text: str) -> Mask:
    tree = ast.parse(text)
    line_starts = [0]
    for ln in text.split("\n")[:-1]:
        line_starts.append(line_starts[-1] + len(ln) + 1)
    lines = text.split("\n")

    def pos(lineno: int, col: int) -> int:
        line = lines[lineno - 1]
        return line_starts[lineno - 1] + len(line.encode("utf-8")[:col].decode("utf-8", "ignore"))

    docstrings: set[int] = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)) and node.body:
            first = node.body[0]
            if isinstance(first, ast.Expr) and isinstance(first.value, ast.Constant):
                docstrings.add(id(first.value))
    inside_fstring: set[int] = set()
    notes: set[int] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.JoinedStr):
            inside_fstring.update(id(v) for v in ast.walk(node) if v is not node)
        if isinstance(node, ast.Call):
            for kw in node.keywords:
                if kw.arg == "notes":
                    notes.update(id(v) for v in ast.walk(kw.value))
    mk = Mask(text, start_blank=True)
    for node in ast.walk(tree):
        is_str = isinstance(node, ast.Constant) and isinstance(node.value, str)
        if not (is_str or isinstance(node, ast.JoinedStr)) or id(node) in docstrings or id(node) in inside_fstring:
            continue
        if node.end_lineno is None or node.end_col_offset is None:
            continue
        a, b = pos(node.lineno, node.col_offset), pos(node.end_lineno, node.end_col_offset)
        seg = text[a:b]
        content = node.value if is_str else re.sub(r"\{[^{}]*\}", " ", seg)
        if not looks_like_prose(content):
            continue
        mk.buf[a:b] = list(seg)
        q = re.match(r"[rRbBuUfF]{0,2}('''|\"\"\"|'|\")", seg)
        if q:
            mk.blank(a, a + q.end())
            mk.blank(b - len(q.group(1)), b)
        for m in re.finditer(r"\\[ntr'\"\\]|\\\n", seg):
            mk.blank(a + m.start(), a + m.end())
        if not is_str:
            for m in re.finditer(r"\{[^{}]*\}", seg):
                mk.blank(a + m.start(), a + m.end())
        mk.breaks.update((a, b))
        if id(node) in notes:
            mk.notes.append((a, b))
    return mask_html(mk)


def mask_any(path: Path, text: str) -> tuple[Mask, str]:
    suffix = path.suffix.lower()
    if suffix == ".tex":
        return mask_tex(text), "tex"
    if suffix in (".html", ".htm"):
        return mask_html(Mask(text)), "html"
    if suffix == ".md":
        return mask_md(text), "md"
    if suffix == ".py":
        return mask_py(text), "py"
    return Mask(text), "txt"


# ---------------------------------------------------------------- detection

def detect_genre(path: Path, text: str, kind: str) -> str:
    name = path.name.lower()
    if kind == "py":
        return "slides"
    if kind == "tex":
        if re.search(r"\\documentclass(\[[^\]]*\])?\{beamer\}|d3-beamer", text):
            return "slides"
        if "baposter" in text or "d3-poster" in text:
            return "poster"
        if "d3-abstract" in text:
            return "abstract"
    if kind == "html" and ("data-nav=" in text or "sections" in path.parts):
        return "explainer"
    if re.search(r"rebuttal|response", name):
        return "rebuttal"
    if "abstract" in name:
        return "abstract"
    return "paper"


def detect_lang(prose: str) -> str:
    words = re.findall(r"[a-zäöüß]+", prose.lower())
    de = sum(w in {"der", "die", "das", "und", "ist", "nicht", "wir", "ein", "eine", "mit", "für", "auf", "den", "dem",
                   "des", "zu", "von", "im", "sich", "werden", "wird"} for w in words)
    en = sum(w in {"the", "and", "is", "of", "we", "a", "an", "with", "for", "on", "to", "in", "that", "this", "are",
                   "be", "by"} for w in words)
    return "de" if de > en else "en"


# ---------------------------------------------------------------- sentences

def split_sentences(prose: str, breaks: set[int]) -> list[Sentence]:
    cuts = sorted(set(breaks) | {m.start() for m in re.finditer(r"\n[ \t]*\n", prose)} | {0, len(prose)})
    sentences: list[Sentence] = []
    para = 0
    for a, b in zip(cuts, cuts[1:]):
        block = prose[a:b]
        if not WORD.search(block):
            continue
        para += 1
        pos = 0
        for m in re.finditer(r"[.!?]+[\"')\]\u2019\u201d]*(?=\s|$)", block):
            head = re.search(r"([A-Za-z.]+)\.$", block[max(0, m.start() - 20):m.start() + 1])   # bounded: linear time
            if head and m.group(0).startswith(".") and (head.group(1).lower() in ABBREV or re.fullmatch(r"[A-Z]", head.group(1))):
                continue
            nxt = block[m.end():].lstrip()
            if nxt and nxt[0].islower():
                continue
            chunk = block[pos:m.end()]
            n = len(WORD.findall(chunk))
            if n:
                off = len(chunk) - len(chunk.lstrip())
                sentences.append(Sentence(a + pos + off, a + m.end(), " ".join(chunk.split()), n, True, para))
            pos = m.end()
        rest = block[pos:]
        n = len(WORD.findall(rest))
        if n:
            off = len(rest) - len(rest.lstrip())
            sentences.append(Sentence(a + pos + off, b, " ".join(rest.split()), n, False, para))
    return sentences


# ---------------------------------------------------------------- checks

class LineIndex:
    def __init__(self, text: str) -> None:
        self.starts = [0] + [m.end() for m in re.finditer("\n", text)]

    def __call__(self, pos: int) -> int:
        return bisect.bisect_right(self.starts, pos)


def excerpt(prose: str, start: int, end: int, pad: int = 28) -> str:
    s = " ".join(prose[max(0, start - pad):end + pad].split())
    return s


def check_text(path: Path, raw: str, genre_opt: str | None, ste: bool, lang_opt: str | None,
               against: tuple[str, Path] | None = None) -> tuple[list[Finding], str]:
    mk, kind = mask_any(path, raw)
    prose = mk.text()
    genre = genre_opt or detect_genre(path, raw, kind)
    lang = lang_opt or detect_lang(prose)
    line = LineIndex(raw)
    out: list[Finding] = []

    # Patterns
    rules = (EN_RULES if lang == "en" else DE_RULES) + (STE_RULES if ste and lang == "en" else [])
    protected = [t.span() for t in TECHNICAL.finditer(prose)]
    taken: set[int] = set()
    for level, label, pattern, advice in rules:
        for m in re.finditer(pattern, prose, flags=re.IGNORECASE):
            if any(a <= m.start() and m.end() <= b for a, b in protected) or m.start() in taken:
                continue
            taken.add(m.start())
            if label == "contraction" and ste:
                level = "E"
            out.append(Finding(line(m.start()), level, label, excerpt(prose, m.start(), m.end()), advice))

    # Units of text; a dash or a symbol alone in a table cell is not punctuation
    sentences = split_sentences(prose, mk.breaks)
    spans = [(s.start, s.end) for s in sentences]

    def in_text(pos: int) -> bool:
        k = bisect.bisect_right(spans, (pos, len(prose))) - 1
        return k >= 0 and spans[k][0] <= pos < spans[k][1]

    # Dashes as punctuation (ranges such as 2024--2026, P1–P3 or Bellman--Ford stay)
    for pos, level, snippet in mk.dashes:
        if in_text(pos):
            out.append(Finding(line(pos), level, "dash", snippet, "rewrite with a comma, colon, parentheses, or two sentences"))
    for m in re.finditer("\u2014|\u2015|---|(?<!-)--(?!-)|\u2013|\u2012", prose):
        if not in_text(m.start()):
            continue
        before, after = prose[m.start() - 1:m.start()], prose[m.end():m.end() + 1]
        if m.group(0) in ("--", "\u2013", "\u2012"):
            if not (before.isspace() or after.isspace()):
                continue
            b2, a2 = prose[:m.start()].rstrip()[-1:], prose[m.end():].lstrip()[:1]
            if (b2.isdigit() and a2.isdigit()) or b2 in ")]" or a2 in "([+" or not b2 or not a2:
                continue
        out.append(Finding(line(m.start()), "E", "dash", excerpt(prose, m.start(), m.end()),
                           "rewrite with a comma, colon, parentheses, or two sentences"))

    # Emoji and dingbats
    for m in EMOJI.finditer(prose):
        out.append(Finding(line(m.start()), "E", "emoji", excerpt(prose, m.start(), m.end()), "delete; icons are the layout's job"))
    for m in DINGBAT.finditer(prose):
        if not in_text(m.start()):
            continue
        out.append(Finding(line(m.start()), "W", "dingbat", excerpt(prose, m.start(), m.end()),
                           "a symbol as an icon: use a word, or the layout's icon"))

    # Invisible characters, in the raw file
    for cls, pattern, advice in INVISIBLE:
        hits = [m.start() for m in re.finditer(pattern, raw)]
        if hits:
            where = ", ".join(f"L{line(p)}" for p in hits[:6]) + (" ..." if len(hits) > 6 else "")
            out.append(Finding(line(hits[0]), "W", "invisible", f"{len(hits)} x {cls} ({where})", advice))

    # Sentence length
    notes = mk.notes

    def genre_of(s: Sentence) -> str:
        return "notes" if any(a <= s.start < b for a, b in notes) else genre

    for s in sentences:
        g = genre_of(s)
        warn, err = caps(g, ste)
        if s.words > warn:
            level = "E" if s.words > err else "W"
            out.append(Finding(line(s.start), level, "length", f"{s.text[:70]}... ({s.words} words)",
                               f"split: one idea per sentence ({g}{', STE' if ste else ''}: warning above {warn}, error above {err})"))

    # Same opener three times in a row; additive connective chains
    run_word, run_len = "", 0
    for s in sentences:
        if not s.terminal or genre_of(s) not in PROSE_GENRES:
            run_word, run_len = "", 0
            continue
        first = (WORD.findall(s.text) or [""])[0].lower()
        if first in ENUMERATORS:
            run_word, run_len = "", 0
            continue
        run_len = run_len + 1 if first == run_word else 1
        run_word = first
        if run_len == 3:
            out.append(Finding(line(s.start), "W", "opener", f"three sentences in a row start with '{first}'",
                               "vary the openers; join or reorder sentences"))
    by_para: dict[int, list[Sentence]] = {}
    for s in sentences:
        by_para.setdefault(s.para, []).append(s)
    for para in by_para.values():
        additive = [s for s in para if ADDITIVE.match(s.text)]
        if len(additive) >= 2:
            out.append(Finding(line(additive[1].start), "W", "connectives", additive[1].text[:60] + "...",
                               "two additive connectives in one paragraph: keep the logical ones (because, therefore, however)"))
        if ste and sum(s.terminal for s in para) > 6:
            out.append(Finding(line(para[0].start), "W", "paragraph",
                               f"{sum(s.terminal for s in para)} sentences in one paragraph", "STE: at most six sentences per paragraph"))

    if ste:
        citations = [c.span() for c in re.finditer(r"\([^()]*\b(19|20)\d{2}[a-z]?\b[^()]*\)", prose)]   # (A, 2020; B, 2021)
        for m in re.finditer(";", prose):
            if any(a <= m.start() < b for a, b in citations):
                continue
            out.append(Finding(line(m.start()), "E", "semicolon", excerpt(prose, m.start(), m.end()), "STE: two sentences"))
        if lang == "en":
            hits = [m.start() for s in sentences for m in PASSIVE.finditer(prose, s.start, s.end)]
            if hits:
                where = ", ".join(f"L{line(p)}" for p in hits[:12]) + (" ..." if len(hits) > 12 else "")
                out.append(Finding(line(hits[0]), "W", "passive", f"{len(hits)} passive constructions ({where})",
                                   "STE: active voice where the actor matters ('We estimate ...')"))

    if against:
        out += compare_with(path, raw, prose, against[1], against[0], lang)

    terminal = [s for s in sentences if s.terminal]
    if terminal:
        longest = max(terminal, key=lambda s: s.words)
        mean = sum(s.words for s in terminal) / len(terminal)
        stats = (f"{len(terminal)} sentences, mean {mean:.1f} words, longest {longest.words} (L{line(longest.start)}); "
                 f"{len(sentences) - len(terminal)} other units (titles, bullets, cells)")
    else:
        stats = f"no full sentences; {len(sentences)} units (titles, bullets, cells)"
    header = f"genre {genre}, {lang}{', STE' if ste else ''}; {stats}"
    return out, header


# ---------------------------------------------------------------- comparison with the source (--source, --notes)

NUMBER_WORDS = {"two": "2", "three": "3", "four": "4", "five": "5", "six": "6", "seven": "7", "eight": "8", "nine": "9",
                "ten": "10", "eleven": "11", "twelve": "12", "zwei": "2", "drei": "3", "vier": "4", "fünf": "5",
                "sechs": "6", "sieben": "7", "acht": "8", "neun": "9", "zehn": "10", "zwölf": "12"}


def numbers_in(prose: str, lang: str) -> set[str]:
    """Numbers of the prose, normalized: thousands separators dropped, decimal commas (German) as points, 'three' as 3."""
    text = re.sub(r"\b(" + "|".join(NUMBER_WORDS) + r")\b", lambda m: NUMBER_WORDS[m.group(1).lower()], prose, flags=re.I)
    out: set[str] = set()
    for m in re.finditer(r"(?<![\w.])\.?\d+(?:[.,]\d+)*", text):
        n = m.group(0)
        if lang == "de":
            n = n.replace(".", "").replace(",", ".") if re.fullmatch(r"\d{1,3}(\.\d{3})+(,\d+)?", n) else n.replace(",", ".")
        elif re.fullmatch(r"\d{1,3}(,\d{3})+(\.\d+)?", n):
            n = n.replace(",", "")
        n = "0" + n if n.startswith(".") else n
        out.add(n if "." in n else (n.lstrip("0") or "0"))
    return out


def citations_in(raw: str, prose: str) -> set[str]:
    """Citation keys: \\cite keys, explainer chips, numeric [n], and author-year as 'Surname Year'."""
    keys: set[str] = set()
    for m in re.finditer(r"\\\w*cite\w*\*?(?:\[[^\]]*\])*\{([^}]+)\}", raw):
        keys |= {"\\cite{" + k.strip() + "}" for k in m.group(1).split(",")}
    keys |= {"[[" + m.group(1).strip() + "]]" for m in re.finditer(r"\[\[([^\]\n]+)\]\]", raw)}
    for m in re.finditer(r"\[(\d+(?:\s*[,–-]\s*\d+)*)\]", prose):
        for part in re.split(r"\s*,\s*", m.group(1)):
            ends = [int(x) for x in re.split(r"\s*[–-]\s*", part) if x]
            nums = range(ends[0], ends[-1] + 1) if len(ends) == 2 and ends[1] - ends[0] < 200 else ends
            keys |= {f"[{n}]" for n in nums}
    for m in re.finditer(r"\b([A-Z][\w'’-]+)(?:\s+et\s+al\.|\s+(?:and|&|und)\s+[A-Z][\w'’-]+)?,?\s*\(((?:19|20)\d{2}[a-z]?)\)", prose):
        keys.add(f"{m.group(1)} {m.group(2)}")
    for m in re.finditer(r"\(([^()]*\b(?:19|20)\d{2}[a-z]?[^()]*)\)", prose):
        for part in m.group(1).split(";"):
            mm = re.match(r"\s*(?:e\.\s?g\.,?\s*|see\s+|cf\.\s*)?([A-Z][\w'’-]+)\D*?((?:19|20)\d{2}[a-z]?)\b", part)
            if mm:
                keys.add(f"{mm.group(1)} {mm.group(2)}")
    return keys


def compare_with(path: Path, raw: str, prose: str, other: Path, mode: str, lang: str) -> list[Finding]:
    """--source (a revision keeps every number and citation) or --notes (a text drafted from notes adds none)."""
    oraw = other.read_text(encoding="utf-8", errors="replace")
    omk, _ = mask_any(other, oraw)
    oprose = omk.text()
    out: list[Finding] = []
    what = "source" if mode == "source" else "notes"
    n_new, n_old = numbers_in(prose, lang), numbers_in(oprose, lang)
    c_new, c_old = citations_in(raw, prose), citations_in(oraw, oprose)

    def name_in(key: str, text: str) -> bool:
        """'Surname Year' keys whose name occurs in the other text are rephrasings (or capitalized nouns), not new references."""
        m = re.fullmatch(r"([^\s\[\\]+) \d{4}[a-z]?", key)
        return bool(m) and re.search(rf"\b{re.escape(m.group(1))}\b", text) is not None

    c_new, c_old = {c for c in c_new if c in c_old or not name_in(c, oprose)}, {c for c in c_old if c in c_new or not name_in(c, prose)}
    for n in sorted(n_new - n_old):
        out.append(Finding(0, "E", what, f"number {n}", f"not in the {what}: check it against the {what}, never invent a number"))
    for c in sorted(c_new - c_old):
        out.append(Finding(0, "E", what, f"citation {c}", f"not in the {what}: cite only what the {what} cites"))
    if mode == "source":
        for n in sorted(n_old - n_new):
            out.append(Finding(0, "E", what, f"number {n}", "missing from the revision: a style edit keeps every number"))
        for c in sorted(c_old - c_new):
            out.append(Finding(0, "E", what, f"citation {c}", "missing from the revision: a style edit keeps every citation"))
    if not out:
        out.append(Finding(0, "I", what, f"{len(n_new)} numbers, {len(c_new)} citations", f"consistent with the {what}"))
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description="Check the wording of a D3 text against the d3-scientific-wording rules.")
    parser.add_argument("files", nargs="+", type=Path, help=".tex, .html, .md, .txt or slides.py files")
    parser.add_argument("--genre", choices=GENRES, help="sets the sentence caps (default: detected per file)")
    parser.add_argument("--ste", action="store_true", help="Simplified Technical English mode (ASD-STE100 writing rules)")
    parser.add_argument("--lang", choices=("en", "de"), help="language of the rule set (default: detected per file)")
    parser.add_argument("--errors-only", action="store_true", help="print errors only")
    cmp = parser.add_mutually_exclusive_group()
    cmp.add_argument("--source", type=Path, metavar="FILE",
                     help="revision: every number and citation of FILE must still be there, and none may be added")
    cmp.add_argument("--notes", type=Path, metavar="FILE",
                     help="text drafted from notes: no number or citation that is not in FILE")
    args = parser.parse_args()
    other = args.source or args.notes
    if other and (len(args.files) != 1 or not other.is_file()):
        print("--source and --notes take one checked file and an existing source file", file=sys.stderr)
        return 2
    against = ("source", args.source) if args.source else ("notes", args.notes) if args.notes else None

    errors = warnings = 0
    for path in args.files:
        if not path.is_file():
            print(f"File not found: {path}", file=sys.stderr)
            return 2
        raw = path.read_text(encoding="utf-8", errors="replace")
        try:
            findings, header = check_text(path, raw, args.genre, args.ste, args.lang, against)
        except SyntaxError as exc:
            print(f"{path}: cannot parse ({exc})", file=sys.stderr)
            return 2
        errors += sum(f.level == "E" for f in findings)
        warnings += sum(f.level == "W" for f in findings)
        print(f"d3-scientific-wording check: {path} ({header})")
        shown = [f for f in sorted(findings, key=lambda f: (f.line, f.level)) if f.level == "E" or not args.errors_only]
        shown = [f for f in shown if f.level != "I"] + [f for f in shown if f.level == "I"]
        for f in shown:
            tag = {"E": "ERROR", "W": "warn ", "I": "ok   "}[f.level]
            where = f"L{f.line:<4}" if f.line else "  -  "
            print(f"  {tag} {where} {f.label:<13} \"{f.snippet}\"  -> {f.advice}")
        if not shown:
            print("  ok")
    print(f"RESULT: {'FAIL' if errors else 'PASS'} ({errors} error(s), {warnings} warning(s))")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
