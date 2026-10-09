# /// script
# requires-python = ">=3.10"
# dependencies = ["pymupdf>=1.24"]
# ///
"""Measure how a corpus is written: the user's own papers (author profile), papers of one outlet (outlet profile)
or papers on one topic (topic profile). Part of d3-scientific-wording; see references/profiles.md.

    uv run <skill-dir>/scripts/wording_profile.py list literature/
    uv run <skill-dir>/scripts/wording_profile.py measure literature/ --match "European Journal of Operational Research" \\
        --kind outlet --name EJOR --out wording-profile-ejor
    uv run <skill-dir>/scripts/wording_profile.py compare wording-profile-ejor.json paper/sections/*.tex

`list` shows what a folder holds (words, year, venue hint per file), `measure` writes <out>.md for reading and
<out>.json for `compare`, `compare` puts a draft next to the corpus bands. A profile holds counts, term lists and
excerpts of at most 25 words with their source file; it never holds full texts. Reads .pdf, .tex, .md, .txt, .html.
Masking, sentence splitting and the house rules come from check_wording.py, so both tools count the same way.
"""

from __future__ import annotations

import argparse
import json
import math
import re
import statistics
import sys
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import check_wording as cw  # noqa: E402

SUFFIXES = {".pdf", ".tex", ".md", ".txt", ".html", ".htm"}
LIGATURES = str.maketrans({"\ufb00": "ff", "\ufb01": "fi", "\ufb02": "fl", "\ufb03": "ffi", "\ufb04": "ffl", "\ufb05": "st", "\ufb06": "st"})
SKIP_DIRS = {".git", ".obsidian", ".trash", "node_modules", "__pycache__", ".venv", "venv", "dist", "build"}
VENUE_HINT = re.compile(
    r"journal|proceedings|conference|transactions|symposium|workshop|quarterly|letters|neurips|icml|iclr|aistats|aaai|"
    r"kdd|icis|ecis|pacis|amcis|wirtschaftsinformatik|management science|operations research|informs|elsevier|springer|"
    r"arxiv", re.I)

HEDGES = re.compile(r"\b(may|might|could|suggests?|suggested|appears?|appeared|seems?|seemed|likely|unlikely|possibly|"
                    r"potentially|perhaps|indicates?|indicated|tends?\s+to|plausibl[ey]|presumabl[ey]|arguably)\b", re.I)
BOOSTERS = re.compile(r"\b(clearly|obviously|certainly|undoubtedly|indeed|demonstrates?|demonstrated|proves?|proved|"
                      r"significantly|strongly|substantially|dramatically|novel|unprecedented|state[\s-]of[\s-]the[\s-]art|"
                      r"always|never)\b", re.I)
WE = re.compile(r"\b(we|our|ours|us)\b", re.I)
SINGULAR = re.compile(r"\b(I|my|me)\b")
NOMINAL = re.compile(r"\b[a-z]{4,}(tion|sion|ment|ness|ity|ance|ence)s?\b", re.I)
CONNECTIVES = ("however", "therefore", "thus", "hence", "moreover", "furthermore", "in addition", "additionally",
               "in contrast", "whereas", "while", "because", "since", "consequently", "accordingly", "nevertheless",
               "instead", "specifically", "notably", "importantly", "overall", "finally", "first", "second", "third")
MOVES = {  # rhetorical moves: how a corpus states contributions, gaps, limitations and implications
    "contribution": re.compile(r"\b(we|this\s+(paper|study|article|work))\s+(propose|introduce|develop|derive|"
                               r"contribute|extend|demonstrate)\w*|\bour\s+(main\s+)?contributions?\b|\bcontributes?\s+to\b", re.I),
    "gap": re.compile(r"\bto\s+the\s+best\s+of\s+our\s+knowledge\b|\blittle\s+is\s+known\b|\b(has|have)\s+(not|rarely)\s+been\b"
                      r"|\bremains?\s+(unclear|unexplored|open|understudied|scarce)\b|\bno\s+(prior\s+)?(study|work|research)\b"
                      r"|\bresearch\s+gap\b", re.I),
    "limitation": re.compile(r"\blimitations?\b|\bfuture\s+(research|work)\b|\bbeyond\s+the\s+scope\b", re.I),
    "assumption": re.compile(r"\bwe\s+(assume|restrict|focus\s+on)\b|\bfor\s+simplicity\b|\bwithout\s+loss\s+of\s+generality\b", re.I),
    "implication": re.compile(r"\bimplications?\b|\bmanagerial\b|\bpractitioners?\b|\bpolicy\s*makers?\b|\bdecision[\s-]makers\b", re.I),
}
STOP = set("""a an the of in on at to for from by with and or but nor as is are was were be been being this that these those
it its we our they their them there here which who whom whose what when where how than then thus also not no can could may
might will would shall should must do does did has have had such into over under between among about above below up down
out off very more most less least each every both either neither any all some other another same so if because while
whereas however therefore i e g et al via per one two three us his her he she you your only just even well""".split())
ONE_SIDED = {"passive_1k", "nominal_100w", "dashes_100s", "boosters_1k", "over35_share", "sent_p90", "questions_100s"}
# below the corpus band is what the D3 rules ask for anyway, so only 'above' is a finding
METRICS = [  # (key, label, unit)
    ("sent_mean", "sentence length, mean", "words"), ("sent_median", "sentence length, median", "words"),
    ("sent_p90", "sentence length, 90th percentile", "words"), ("over35_share", "sentences over 35 words", "%"),
    ("hedges_1k", "hedges", "per 1k words"), ("boosters_1k", "boosters", "per 1k words"),
    ("we_1k", "we / our / us", "per 1k words"), ("i_1k", "I / my / me", "per 1k words"),
    ("passive_1k", "passive constructions", "per 1k words"), ("nominal_100w", "nominalizations", "per 100 words"),
    ("colons_100s", "colons", "per 100 sentences"), ("semicolons_100s", "semicolons (outside citations)", "per 100 sentences"),
    ("parens_100s", "parentheses", "per 100 sentences"), ("dashes_100s", "dashes as punctuation", "per 100 sentences"),
    ("questions_100s", "questions", "per 100 sentences"),
]


# ---------------------------------------------------------------- reading

def collect(paths: list[Path]) -> list[Path]:
    out: list[Path] = []
    for p in paths:
        if p.is_dir():
            for f in sorted(p.rglob("*")):
                rel = f.relative_to(p).parts[:-1]
                if f.is_file() and f.suffix.lower() in SUFFIXES and not any(x in SKIP_DIRS or x.startswith(".") for x in rel):
                    out.append(f)
        elif p.is_file() and p.suffix.lower() in SUFFIXES:
            out.append(p)
    return out


def pdf_text(path: Path) -> tuple[str, str]:
    """Body text of a PDF, paragraphs separated by blank lines, and its head (metadata, first page) for matching."""
    import pymupdf

    doc = pymupdf.open(path)
    pages = []
    for page in doc:
        blocks = [b[4] for b in page.get_text("blocks") if b[6] == 0]
        pages.append([" ".join(t.translate(LIGATURES).split()) for t in blocks if t.strip()])
    md = doc.metadata or {}
    year = re.match(r"D:(\d{4})", md.get("creationDate") or "")
    fields = [md.get(k) for k in ("title", "author", "subject", "keywords") if md.get(k)]   # format and producer say nothing
    head = "\n".join(fields + ([f"year {year.group(1)}"] if year else []) + (pages[0][:40] if pages else []))

    def norm(t: str) -> str:
        return re.sub(r"\d+", "#", t.lower())[:80]

    n = len(pages)
    recur = Counter(norm(t) for p in pages for t in set(p[:3] + p[-3:]))
    running = {k for k, c in recur.items() if n >= 4 and c >= max(3, 0.4 * n)}   # running headers and footers
    paras: list[str] = []
    for k, p in enumerate(pages):
        for t in p:
            if norm(t) in running:
                continue
            if k >= n / 2 and re.match(r"^(references|bibliography|literaturverzeichnis|literatur)\b", t, re.I):
                return dehyphenate("\n\n".join(paras)), head                        # the reference list starts
            letters = len(re.findall(r"[A-Za-zÄÖÜäöüß]", t))
            if letters < 0.6 * len(t.replace(" ", "")):
                continue                                                            # tables, formulas
            if re.match(r"^(fig(ure)?|table|tab)\.?\s*\d", t, re.I) or re.match(r"^acknowledge?ments?\b", t, re.I):
                continue                                                            # captions, acknowledgements
            if len(t.split()) < 6 and not re.search(r"[.!?]$", t):
                continue                                                            # headings, labels, affiliations
            paras.append(t)
    return dehyphenate("\n\n".join(paras)), head


def dehyphenate(text: str) -> str:
    """Join words split at a line end ('deci- sion'), but keep real compounds ('day- ahead' stays 'day-ahead')."""
    vocab = set(re.findall(r"[a-zäöüß]+", text.lower()))
    return re.sub(r"(\w+)- ([a-zäöüß]\w*)",
                  lambda m: m.group(1) + m.group(2) if (m.group(1) + m.group(2)).lower() in vocab else m.group(1) + "-" + m.group(2),
                  text)


def load(path: Path) -> tuple[str, set[int], str]:
    """(prose, unit breaks, head) of one file."""
    if path.suffix.lower() == ".pdf":
        text, head = pdf_text(path)
        return text, set(), head
    raw = path.read_text(encoding="utf-8", errors="replace")
    mk, _ = cw.mask_any(path, raw)
    return mk.text(), mk.breaks, raw[:3000]


# ---------------------------------------------------------------- measuring

def per(n: float, base: float, unit: float) -> float:
    return round(n / base * unit, 2) if base else 0.0


def tokens(text: str) -> list[str]:
    """Words of two letters or more; single letters are mostly math symbols left over from PDF extraction."""
    return [w for w in re.findall(r"[a-zäöüß][a-zäöüß'\-]*[a-zäöüß]|\b[ai]\b", text.lower())]


def ngrams(toks: list[str], n: int):
    for i in range(len(toks) - n + 1):
        yield tuple(toks[i:i + n])


def measure_doc(prose: str, breaks: set[int], lang: str) -> dict:
    sents = [s for s in cw.split_sentences(prose, breaks) if s.terminal and s.words >= 3]
    words = sum(s.words for s in sents)
    lengths = sorted(s.words for s in sents)
    body = "\n".join(s.text for s in sents)
    m: dict = {"words": words, "sentences": len(sents)}
    if not sents:
        return m | {"_sents": [], "_body": ""}
    m["sent_mean"] = round(statistics.mean(lengths), 1)
    m["sent_median"] = statistics.median(lengths)
    m["sent_p90"] = lengths[min(len(lengths) - 1, math.ceil(0.9 * len(lengths)) - 1)]
    m["over35_share"] = per(sum(x > 35 for x in lengths), len(lengths), 100)
    citations = [c.span() for c in re.finditer(r"\([^()]*\b(19|20)\d{2}[a-z]?\b[^()]*\)", body)]
    m["semicolons_100s"] = per(sum(1 for c in re.finditer(";", body) if not any(a <= c.start() < b for a, b in citations)),
                               len(sents), 100)
    m["colons_100s"] = per(len(re.findall(r"(?<!\d):(?!\d)", body)), len(sents), 100)
    m["parens_100s"] = per(body.count("("), len(sents), 100)
    m["dashes_100s"] = per(len(re.findall("—|\\s–\\s|\\s--\\s", body)), len(sents), 100)
    m["questions_100s"] = per(sum(s.text.endswith("?") for s in sents), len(sents), 100)
    m["nominal_100w"] = per(len(NOMINAL.findall(body)), words, 100)
    if lang == "en":
        m["hedges_1k"] = per(len(HEDGES.findall(body)), words, 1000)
        m["boosters_1k"] = per(len(BOOSTERS.findall(body)), words, 1000)
        m["we_1k"] = per(len(WE.findall(body)), words, 1000)
        m["i_1k"] = per(len(SINGULAR.findall(body)), words, 1000)
        m["passive_1k"] = per(len(cw.PASSIVE.findall(body)), words, 1000)
    m["_sents"] = [s.text for s in sents]
    m["_body"] = body
    return m


def house_rule_hits(body: str, lang: str) -> dict[str, Counter]:
    """What the corpus does that the D3 rules flag, by label, with the matched phrases."""
    rules = cw.EN_RULES if lang == "en" else cw.DE_RULES
    protected = [t.span() for t in cw.TECHNICAL.finditer(body)]
    hits: dict[str, Counter] = defaultdict(Counter)
    taken: set[int] = set()
    for _, label, pattern, _ in rules:
        for m in re.finditer(pattern, body, flags=re.IGNORECASE):
            if m.start() in taken or any(a <= m.start() and m.end() <= b for a, b in protected):
                continue
            taken.add(m.start())
            hits[label][" ".join(m.group(0).lower().split())[:40]] += 1
    return hits


def abbreviations(body: str) -> Counter:
    found: Counter = Counter()
    for m in re.finditer(r"((?:[A-Za-z][\w\-]*\s+){0,6}[A-Za-z][\w\-]*)\s+\(([A-Z][A-Za-z]{1,7}?)s?\)", body):
        abbr, caps = m.group(2), [c for c in m.group(2) if c.isupper()]
        words = m.group(1).split()
        for k in range(len(caps), min(len(words), len(caps) + 2) + 1):   # long forms may carry 'of', 'and'
            cand = words[-k:]
            initials = [w[0].upper() for w in cand if w.lower() not in STOP]
            if initials == caps or "".join(w[0] for w in re.split(r"[\s\-]", " ".join(cand)) if w).upper() == abbr.upper():
                found[(abbr, " ".join(cand).lower())] += 1
                break
    return found


def band(values: list[float]) -> dict:
    values = sorted(v for v in values if v is not None)
    if len(values) >= 3:
        q = statistics.quantiles(values, n=4, method="inclusive")
        return {"p25": round(q[0], 2), "median": round(q[1], 2), "p75": round(q[2], 2)}
    return {}


def measure(files: list[Path], kind: str, name: str, lang_opt: str | None) -> dict:
    docs = []
    for f in files:
        try:
            prose, breaks, _ = load(f)
        except Exception as exc:  # noqa: BLE001 -- a broken PDF must not stop the corpus
            print(f"  skipped {f.name}: {exc}", file=sys.stderr)
            continue
        lang = lang_opt or cw.detect_lang(prose)
        m = measure_doc(prose, breaks, lang)
        if m["sentences"] >= 10:
            docs.append((f, lang, m))
        else:
            print(f"  skipped {f.name}: fewer than 10 sentences of body text", file=sys.stderr)
    if not docs:
        sys.exit("no document with body text; check the files with `list`")
    lang = Counter(d[1] for d in docs).most_common(1)[0][0]
    pooled_body = "\n\n".join(t for d in docs for t in d[2]["_sents"])   # one sentence per block
    pooled = measure_doc(pooled_body, set(), lang)
    words = sum(d[2]["words"] for d in docs)
    n = len(docs)
    confidence = ("solid" if n >= 5 and words >= 20000 else "usable" if n >= 3 and words >= 10000
                  else "weak: read it as anecdotes, not as norms")

    metrics = {}
    for key, label, unit in METRICS:
        if key in pooled:
            metrics[key] = {"label": label, "unit": unit, "pooled": pooled[key], **band([d[2].get(key) for d in docs])}

    openers: Counter = Counter()
    connectives: Counter = Counter()
    df: dict[int, Counter] = {k: Counter() for k in range(1, 7)}
    tf: dict[int, Counter] = {k: Counter() for k in range(1, 7)}
    moves: dict[str, list] = {k: [] for k in MOVES}
    move_docs: Counter = Counter()
    for f, _, m in docs:
        seen: dict[int, set] = {k: set() for k in range(1, 7)}
        doc_moves = set()
        for s in m["_sents"]:
            toks = tokens(s)
            if toks:
                openers[toks[0]] += 1
                head = " ".join(toks[:2])
                conn = next((c for c in CONNECTIVES if head == c or toks[0] == c), None)
                if conn:
                    connectives[conn] += 1
            for k in range(1, 7):
                for g in ngrams(toks, k):
                    tf[k][g] += 1
                    seen[k].add(g)
            for mv, pat in MOVES.items():
                if pat.search(s):
                    doc_moves.add(mv)
                    moves[mv].append((len(s.split()), f.name, s))
        for k in range(1, 7):
            df[k].update(seen[k])
        move_docs.update(doc_moves)

    min_df = max(2, math.ceil(0.25 * n)) if n > 1 else 1
    min_tf = 3

    def content(g: tuple) -> bool:
        return g[0] not in STOP and g[-1] not in STOP and not any(re.search(r"\d", w) for w in g)

    merged: dict[tuple, list] = {}
    for k in (2, 3):
        for g in tf[k]:
            if not content(g) or any(w in STOP for w in g):
                continue
            key = g[:-1] + (re.sub(r"s$", "", g[-1]),)          # singular and plural are one term
            e = merged.setdefault(key, [g, 0, 0])
            if tf[k][g] > tf[k].get(e[0], 0):
                e[0] = g
            e[1] = max(e[1], df[k][g])
            e[2] += tf[k][g]
    terms = [(g, d_, t_) for g, d_, t_ in merged.values() if d_ >= min_df and t_ >= min_tf]
    terms.sort(key=lambda t: (-t[1], -t[2]))
    formulations = [(g, df[k][g], tf[k][g]) for k in (3, 4, 5, 6) for g in tf[k]
                    if df[k][g] >= min_df and tf[k][g] >= min_tf and any(w in STOP for w in g)
                    and any(w not in STOP for w in g) and g[0] not in {"and", "or", "of"} and g[-1] not in {"the", "a", "an", "of", "and", "or", "to", "in"}
                    and not any(re.search(r"\d", w) for w in g)]
    formulations.sort(key=lambda t: (-len(t[0]), -t[1]))
    kept: list = []
    for g, d_, t_ in formulations:                       # keep the longest form of nested phrases
        text = " ".join(g)
        if any(text in " ".join(k[0]) and k[1] >= 0.8 * d_ for k in kept):
            continue
        kept.append((g, d_, t_))
    kept.sort(key=lambda t: (-t[1], -t[2]))

    groups: dict[str, Counter] = defaultdict(Counter)
    for k in (1, 2, 3):
        for g, c in tf[k].items():
            if c >= 2 and content(g):
                key = re.sub(r"[\s\-]", "", " ".join(g))
                key = key[:-1] if key.endswith("s") and len(key) > 5 else key
                groups[key][" ".join(g)] += c
    real = {g[0] for g, c in tf[1].items() if c >= 5}            # words that stand alone, not fragments like 'sys tem'
    variants = []
    for c in groups.values():
        c = Counter({f: n_ for f, n_ in c.items() if all(w in real for w in re.split(r"[\s\-]", f))})
        if len(c) >= 2 and sorted(c.values())[-2] >= 2 and len({re.sub(r"s$", "", f.replace(" ", "")) for f in c}) >= 2:
            variants.append((dict(c.most_common()), sum(c.values())))
    variants.sort(key=lambda v: -v[1])

    abbr = abbreviations(pooled_body)

    def exemplars(items: list) -> list[dict]:
        out, files_used = [], set()
        for length, fname, s in sorted(items, key=lambda x: abs(x[0] - 20)):   # typical sentences, not the shortest
            if length < 10 or fname in files_used:
                continue
            words_ = s.split()
            out.append({"file": fname, "text": " ".join(words_[:25]) + (" ..." if len(words_) > 25 else "")})
            files_used.add(fname)
            if len(out) == 3:
                break
        return out

    hits = house_rule_hits(pooled_body, lang)
    return {
        "kind": kind, "name": name, "created": date.today().isoformat(), "language": lang,
        "confidence": confidence, "documents": n, "words": words,
        "sources": [{"file": str(f), "words": m["words"], "sentences": m["sentences"]} for f, _, m in docs],
        "metrics": metrics,
        "openers": [[w, round(c / max(1, pooled["sentences"]) * 100, 1)] for w, c in openers.most_common(15)],
        "connectives": [[w, round(c / max(1, pooled["sentences"]) * 100, 2)] for w, c in connectives.most_common(15)],
        "house_rules": {lab: {"per_1k": per(sum(c.values()), words, 1000), "top": c.most_common(5)} for lab, c in sorted(hits.items())},
        "formulations": [[" ".join(g), d_, t_] for g, d_, t_ in kept[:30]],
        "terms": [[" ".join(g), d_, t_] for g, d_, t_ in terms[:40]],
        "variants": [v[0] for v in variants[:20]],
        "abbreviations": [[a, lf, c] for (a, lf), c in abbr.most_common(30)],
        "moves": {mv: {"documents_share": round(move_docs[mv] / n * 100), "sentences": len(moves[mv]),
                       "exemplars": exemplars(moves[mv])} for mv in MOVES},
    }


# ---------------------------------------------------------------- writing

def to_markdown(p: dict) -> str:
    L = [f"# Wording profile: {p['name']} ({p['kind']})", "",
         f"Measured {p['created']} from {p['documents']} documents, {p['words']:,} words of body text ({p['language']}). "
         f"Evidence: **{p['confidence']}**.", "",
         "How to use it (d3-scientific-wording, references/profiles.md): bands are document-level targets, never per "
         "paragraph. The D3 error rules hold whatever the corpus does. Exemplars show structure; never reuse their wording. "
         "A phrase missing here is not evidence against it.", "",
         "## Sentences, stance, punctuation", "", "| Metric | Pooled | Band across documents (p25, median, p75) | Unit |", "|---|---|---|---|"]
    for key, m in p["metrics"].items():
        bandtxt = f"{m['p25']}, {m['median']}, {m['p75']}" if "p25" in m else "fewer than 3 documents"
        L.append(f"| {m['label']} | {m['pooled']} | {bandtxt} | {m['unit']} |")
    L += ["", "## Sentence openers (share of sentences, %)", "", ", ".join(f"{w} {s}" for w, s in p["openers"]), "",
          "## Sentence-initial connectives (share of sentences, %)", "", ", ".join(f"{w} {s}" for w, s in p["connectives"]) or "none", "",
          "## What the corpus does that the D3 rules flag", "",
          "Per 1k words, with the most frequent phrases. Errors of the D3 rules stay errors for us; a warning that is an "
          "outlet habit may be kept with the reason \"outlet convention (profile)\".", "",
          "| Rule | Per 1k words | Most frequent |", "|---|---|---|"]
    for lab, h in p["house_rules"].items():
        L.append(f"| {lab} | {h['per_1k']} | {'; '.join(f'{t} ({c})' for t, c in h['top'])} |")
    L += ["", "## Recurring formulations", "", "Phrases of three to six words that recur across documents "
          "(documents, occurrences). Short conventional phrases may be used; longer ones are structure, not text to copy.", ""]
    L += [f"- {t} ({d_}, {c})" for t, d_, c in p["formulations"]] or ["- none above the threshold"]
    L += ["", "## Terms", "", "Two- and three-word terms (documents, occurrences). They seed the term sheet.", ""]
    L += [f"- {t} ({d_}, {c})" for t, d_, c in p["terms"]] or ["- none above the threshold"]
    L += ["", "## Spelling variants of one term", "", "The most frequent form is the corpus's choice.", ""]
    L += ["- " + " · ".join(f"{f} ({c})" for f, c in v.items()) for v in p["variants"]] or ["- none"]
    L += ["", "## Abbreviations defined in the corpus", ""]
    L += [f"- {a}: {lf} ({c})" for a, lf, c in p["abbreviations"]] or ["- none"]
    L += ["", "## Rhetorical moves", "", "Share of documents with at least one sentence of the move, and short exemplars "
          "for the structure only.", ""]
    for mv, d_ in p["moves"].items():
        L.append(f"**{mv}**: {d_['documents_share']} % of documents, {d_['sentences']} sentences")
        L += [f"- \"{e['text']}\" ({e['file']})" for e in d_["exemplars"]]
        L.append("")
    L += ["## Sources", ""] + [f"- {s['file']} ({s['words']:,} words)" for s in p["sources"]]
    return "\n".join(L) + "\n"


# ---------------------------------------------------------------- commands

def matching(files: list[Path], pattern: str | None) -> list[Path]:
    if not pattern:
        return files
    rx = re.compile(pattern, re.I)
    keep = []
    for f in files:
        try:
            _, _, head = load(f)
        except Exception:  # noqa: BLE001
            continue
        if rx.search(head) or rx.search(f.name):
            keep.append(f)
    return keep


def cmd_list(args: argparse.Namespace) -> int:
    files = matching(collect(args.paths), args.match)
    if not files:
        print("No .pdf, .tex, .md, .txt or .html files found (or none matches --match).")
        return 1
    if len(files) > args.limit:
        by_dir = Counter(str(f.parent) for f in files)
        print(f"{len(files)} files in {len(by_dir)} folders. Narrow down with a folder or --match:")
        for d, c in by_dir.most_common(40):
            print(f"  {c:5}  {d}")
        return 0
    total = 0
    for i, f in enumerate(files, 1):
        try:
            prose, _, head = load(f)
        except Exception as exc:  # noqa: BLE001
            print(f"{i:3}. {f}  (unreadable: {exc})")
            continue
        words = len(cw.WORD.findall(prose))
        total += words
        year = re.search(r"\byear (\d{4})\b", head) or re.search(r"\b(19[89]\d|20[0-4]\d)\b", head)
        venue = next((" ".join(ln.split())[:80] for ln in head.splitlines() if VENUE_HINT.search(ln)), "")
        print(f"{i:3}. {f}  | {words:,} words | {year.group(1) if year else '----'} | {venue}")
    print(f"{len(files)} files, {total:,} words of body text")
    return 0


def cmd_measure(args: argparse.Namespace) -> int:
    files = matching(collect(args.paths), args.match)
    if not files:
        print("No files to measure (check the paths and --match).", file=sys.stderr)
        return 1
    print(f"measuring {len(files)} files ...", file=sys.stderr)
    prof = measure(files, args.kind, args.name or args.kind, args.lang)
    out = Path(args.out)
    out.with_suffix(".json").write_text(json.dumps(prof, ensure_ascii=False, indent=1), encoding="utf-8")
    out.with_suffix(".md").write_text(to_markdown(prof), encoding="utf-8")
    print(f"{prof['documents']} documents, {prof['words']:,} words, evidence {prof['confidence']}")
    print(f"-> {out.with_suffix('.md')} and {out.with_suffix('.json')}")
    return 0


def cmd_compare(args: argparse.Namespace) -> int:
    prof = json.loads(Path(args.profile).read_text(encoding="utf-8"))
    files = collect(args.paths)
    parts = [load(f) for f in files]
    lang = prof.get("language", "en")
    prose = "\n\n".join(p[0] for p in parts)
    breaks: set[int] = set()
    offset = 0
    for p in parts:
        breaks |= {offset + b for b in p[1]}
        offset += len(p[0]) + 2
    draft = measure_doc(prose, breaks, lang)
    print(f"Draft ({draft['sentences']} sentences, {draft['words']:,} words) against the {prof['kind']} profile "
          f"'{prof['name']}' ({prof['documents']} documents, evidence {prof['confidence']})")
    print(f"  {'metric':40} {'draft':>8}   corpus band (p25 to p75, else pooled)")
    for key, m in prof["metrics"].items():
        if key not in draft:
            continue
        v = draft[key]
        lo, hi = (m["p25"], m["p75"]) if "p25" in m else (m["pooled"], m["pooled"])
        flag = "" if "p25" not in m else ("above" if v > hi else "below" if v < lo else "in band")
        if flag == "below" and key in ONE_SIDED:
            flag = "below (fine: the D3 rules ask for less)"
        rng = f"{lo} to {hi}" if "p25" in m else f"{m['pooled']} (pooled)"
        print(f"  {m['label'][:40]:40} {v:>8}   {rng:22} {flag}")
    body = draft["_body"].lower()
    lines = []
    for forms in prof["variants"]:
        used = {f: len(re.findall(rf"\b{re.escape(f)}\b", body)) for f in forms}
        used = {f: c for f, c in used.items() if c}
        top = next(iter(forms))
        if used and any(f != top for f in used):
            lines.append(f"  draft uses {', '.join(f'{f} ({c})' for f, c in used.items())}; corpus prefers '{top}' "
                         f"({forms[top]} of {sum(forms.values())})")
    own = {lf for (_, lf) in abbreviations(draft["_body"])}          # long forms the draft abbreviates itself
    for a, lf, c in prof["abbreviations"]:
        if any(lf in o for o in own):
            continue
        if re.search(rf"\b{re.escape(lf)}\b", body) and not re.search(rf"\b{re.escape(a)}\b", draft["_body"]):
            lines.append(f"  draft writes '{lf}' without an abbreviation; the corpus defines it as {a} ({c} times)")
    if lines:
        print("Terms:")
        print("\n".join(lines))
    print("Move a draft toward the band from whichever side it is on; a band is a document-level target.")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Measure how a corpus is written (d3-scientific-wording).")
    sub = parser.add_subparsers(dest="cmd", required=True)
    p_list = sub.add_parser("list", help="what a folder holds: words, year and venue hint per file")
    p_list.add_argument("paths", nargs="+", type=Path)
    p_list.add_argument("--match", help="keep files whose metadata, first page or name matches this regex")
    p_list.add_argument("--limit", type=int, default=80, help="above this many files, summarize by folder")
    p_meas = sub.add_parser("measure", help="write a wording profile (.md and .json)")
    p_meas.add_argument("paths", nargs="+", type=Path)
    p_meas.add_argument("--kind", choices=("author", "outlet", "topic"), required=True)
    p_meas.add_argument("--name", help="name of the author, outlet or topic")
    p_meas.add_argument("--match", help="keep files whose metadata, first page or name matches this regex")
    p_meas.add_argument("--lang", choices=("en", "de"))
    p_meas.add_argument("--out", default="wording-profile", help="output path without suffix")
    p_cmp = sub.add_parser("compare", help="put a draft next to a profile's bands and terms")
    p_cmp.add_argument("profile", type=Path)
    p_cmp.add_argument("paths", nargs="+", type=Path)
    args = parser.parse_args()
    return {"list": cmd_list, "measure": cmd_measure, "compare": cmd_compare}[args.cmd](args)


if __name__ == "__main__":
    sys.exit(main())
