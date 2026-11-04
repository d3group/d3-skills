# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""Grade the d3-scientific-wording eval runs: writes grading.json into every run-*/ folder of an iteration.

    uv run evals/grade.py <workspace>/iteration-1

An iteration is a skill-creator run of evals.json (eval-<n>-<name>/<config>/run-<k>/outputs/). The inputs are read
from <iteration>/inputs/ when the run copied them there, otherwise from evals/files/ next to this script.
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

SKILL = Path(__file__).resolve().parents[1]
LINT = SKILL / "scripts" / "check_wording.py"
sys.path.insert(0, str(LINT.parent))
import check_wording as cw  # noqa: E402


def lint(path: Path, *args: str) -> tuple[int, int, str]:
    out = subprocess.run(["uv", "run", "--quiet", str(LINT), str(path), *args], capture_output=True, text=True).stdout
    m = re.search(r"RESULT: \w+ \((\d+) error\(s\), (\d+) warning\(s\)\)", out)
    errors = [ln.strip() for ln in out.splitlines() if ln.strip().startswith("ERROR")]
    return (int(m.group(1)), int(m.group(2)), "; ".join(errors[:4])) if m else (-1, -1, out[-300:])


def numbers(text: str) -> set[str]:
    text = re.sub(r"(?<=\d),(?=\d{3})", "", text)
    return {n.lstrip("0") or "0" for n in re.findall(r"\d+(?:\.\d+)?", text)}


def check(text: str, passed: bool, evidence: str) -> dict:
    return {"text": text, "passed": bool(passed), "evidence": evidence}


def prose_of(path: Path) -> str:
    raw = path.read_text(encoding="utf-8")
    mk, _ = cw.mask_any(path, raw)
    return " ".join(mk.text().split())


def grade_ejor(out: Path, inputs: Path) -> list[dict]:
    f = out / "ejor_intro_revised.md"
    if not f.exists():
        return [check("Output file ejor_intro_revised.md exists", False, "missing")]
    text = f.read_text(encoding="utf-8")
    src = (inputs / "ejor_intro.md").read_text(encoding="utf-8")
    e, w, errs = lint(f, "--genre", "paper")
    res = [check("Lint (check_wording.py, genre paper) reports 0 errors", e == 0, f"{e} errors, {w} warnings. {errs}")]
    dashes = re.findall("\u2014|\\s\u2013\\s|\\s--\\s", text)
    res.append(check("No em-dashes or spaced dashes", not dashes, f"{len(dashes)} found"))
    contrast = re.findall(r"\bnot\s+(?:only|just)\b|\bnot\b[^.;:\n]{0,80}?\bbut\b|,\s+not\s+\w", text, re.I)
    res.append(check("No 'not X but Y' family", not contrast, "; ".join(contrast) or "none"))
    grades = re.findall(r"\b(seminal|merely|fail(?:s|ed)?\s+to|suffer(?:s|ed)?\s+from|overlook\w*|significant\s+strides|while\s+prior\s+work)\b", text, re.I)
    res.append(check("Related work is reported without grades (seminal, merely, fails to, suffers from, overlooks)", not grades, "; ".join(grades) or "none"))
    hype = re.findall(r"\b(dramatically|significantly|novel|comprehensive|paradigm\s+shift|pave\s+the\s+way|pivotal|crucial|leverag\w+|delve\w*)\b", text, re.I)
    res.append(check("No intensifiers or hype (dramatically, significantly, novel, comprehensive, paradigm shift, pave the way)", not hype, "; ".join(hype) or "none"))
    sota = bool(re.search(r"state[\s-]of[\s-]the[\s-]art", text, re.I))
    asked = bool(re.search(r"state[\s-]of[\s-]the[\s-]art|which (method|baseline)|compared (to|with) (which|what)|baseline", notes_of(out), re.I))
    res.append(check("'State of the art' removed, or kept with a question to the author in notes.md (a revision drops no claim)", not sota or asked,
                     f"in text: {sota}; question in notes: {asked}"))
    cites = [bool(re.search(r"Elmachtoub\s+and\s+Grigas,?\s*\(?2022", text)), bool(re.search(r"Mandi\s+et\s+al\.,?\s*\(?2020", text))]
    res.append(check("Both cited works kept with their years (Elmachtoub and Grigas 2022; Mandi et al. 2020)", all(cites), f"Elmachtoub 2022: {cites[0]}, Mandi 2020: {cites[1]}"))
    need = {"31%": r"31\s?%|31 per", "24 months": r"24\s+months", "2021": r"2021", "2023": r"2023", "12 MW": r"12\s?MW\b", "24 MWh": r"24\s?MWh", "4.2": r"4\.2"}
    missing = [k for k, p in need.items() if not re.search(p, text)]
    res.append(check("All numbers kept (31%, 24 months, 2021 to 2023, 12 MW, 24 MWh, 4.2 times)", not missing, f"missing: {missing}" if missing else "all present"))
    new = numbers(text) - numbers(src)
    res.append(check("No numbers that are not in the source", not new, f"new: {sorted(new)}" if new else "none"))
    return res


def grade_ste(out: Path, inputs: Path) -> list[dict]:
    f = out / "section-ste_revised.html"
    if not f.exists():
        return [check("Output file section-ste_revised.html exists", False, "missing")]
    text = f.read_text(encoding="utf-8")
    e, w, errs = lint(f, "--genre", "explainer", "--ste")
    res = [check("Lint in STE mode (check_wording.py --ste, genre explainer) reports 0 errors", e == 0, f"{e} errors, {w} warnings. {errs}")]
    chips = ["[[paper:eq:ips]]", "[[result:results/clipping.csv]]"]
    res.append(check("Source chips kept unchanged", all(c in text for c in chips), ", ".join(f"{c}: {c in text}" for c in chips)))
    fixed = ['<div class="eq" data-label="eq:ips"></div>', 'id="fig-clip"', 'id="deriv-bias"',
             r"$$\mathbb{E}[\hat V_\tau] - V = -\,\mathbb{E}\big[(w - \tau)^+ \, r\big]$$"]
    res.append(check("Equation placeholder, figure id, derivation id and formula kept unchanged", all(x in text for x in fixed),
                     ", ".join(f"{x[:30]}: {x in text}" for x in fixed)))
    nums = {"94 %": r"94\s?%", "0.8 %": r"0\.8\s?%", "tau = 10": r"\\tau\s*=\s*10\b", "1 to 100": r"\b1\b[^.]{0,12}\b100\b"}
    missing = [k for k, p in nums.items() if not re.search(p, text)]
    res.append(check("Numbers kept (94 %, 0.8 %, tau = 10, slider 1 to 100)", not missing, f"missing: {missing}" if missing else "all present"))
    prose = prose_of(f)
    semis = prose.count(";")
    res.append(check("No semicolons in the prose", semis == 0, f"{semis} found"))
    phrasal = re.findall(r"\b(carried\s+out|set\s+up|turns\s+out|look\s+at)\b", prose, re.I)
    res.append(check("No phrasal verbs of the source (carried out, set up, turns out, look at)", not phrasal, "; ".join(phrasal) or "none"))
    m = re.search(r'<span class="try">(.*?)</span>', text, re.S)
    if m:
        try_text = re.sub(r"<[^>]+>|\$[^$]*\$", "x", m.group(1))
        sents = [s.strip() for s in re.split(r"(?<=[.!?])\s+", try_text) if s.strip()]
        long = [s for s in sents if len(s.split()) > 20]
        nonimp = [s for s in sents if s.split()[0].lower() in {"the", "a", "an", "you", "it", "this", "we", "if", "as", "when"}]
        res.append(check("Try caption: imperative sentences of at most 20 words", not long and not nonimp,
                         f"{len(sents)} sentences; too long: {long}; not imperative: {nonimp}"))
    else:
        res.append(check("Try caption: imperative sentences of at most 20 words", False, "no try span"))
    sents = [s for s in cw.split_sentences(*(lambda mk: (mk.text(), mk.breaks))(cw.mask_any(f, text)[0])) if s.words]
    longest = max((s.words for s in sents), default=0)
    res.append(check("Every sentence has at most 25 words", longest <= 25, f"longest: {longest} words"))
    return res


def grade_icis(out: Path, inputs: Path) -> list[dict]:
    f = out / "icis_abstract.md"
    if not f.exists():
        return [check("Output file icis_abstract.md exists", False, "missing")]
    text = f.read_text(encoding="utf-8")
    body = "\n".join(ln for ln in text.splitlines() if not ln.lstrip().startswith("#") and not re.match(r"^\*\*.*\*\*$", ln.strip()))
    n = len(body.split())
    res = [check("Abstract has at most 150 words (the call's limit)", n <= 150, f"{n} words"),
           check("Abstract uses the space: at least 120 words", n >= 120, f"{n} words")]
    e, w, errs = lint(f, "--genre", "abstract")
    res.append(check("Lint (check_wording.py, genre abstract) reports 0 errors", e == 0, f"{e} errors, {w} warnings. {errs}"))
    has = [bool(re.search(r"184", body)), bool(re.search(r"64\s?%", body)), bool(re.search(r"41\s?%", body))]
    res.append(check("Reports the sample and the main result (N = 184; 64% vs 41%)", all(has), f"184: {has[0]}, 64%: {has[1]}, 41%: {has[2]}"))
    src = (inputs / "icis_notes.md").read_text(encoding="utf-8")
    new = numbers(body) - numbers(src)
    res.append(check("No numbers that are not in the notes", not new, f"new: {sorted(new)}" if new else "none"))
    sig_sents = [s for s in re.split(r"(?<=[.!?])\s+", body) if re.search(r"significan", s, re.I)]
    bad = [s for s in sig_sents if not re.search(r"p\s*<|test|mixed model|regression", s, re.I)]
    res.append(check("'Significant' appears only together with its test, or not at all", not bad, f"{len(sig_sents)} sentences with 'significan'; untested: {bad}"))
    res.append(check("Names the construct 'scrutiny cues'", bool(re.search(r"scrutiny cues", body, re.I)), "found" if re.search(r"scrutiny cues", body, re.I) else "not found"))
    res.append(check("States a contribution to theory (explains, theory)", bool(re.search(r"\b(theor\w*|explain\w*)\b", body, re.I)),
                     ", ".join(sorted(set(m.lower() for m in re.findall(r"\b(theor\w*|explain\w*)\b", body, re.I)))) or "none"))
    contrast = re.findall(r"\bnot\s+(?:only|just)\b|\bnot\b[^.;:\n]{0,80}?\bbut\b|\u2014", body, re.I)
    res.append(check("No 'not X but Y' family and no em-dashes", not contrast, "; ".join(contrast) or "none"))
    return res


def sentences_with(body: str, pattern: str) -> list[str]:
    return [x for x in re.split(r"(?<=[.!?])\s+(?=[A-Z])", body) if re.search(pattern, x, re.I)]


def notes_of(out: Path) -> str:
    f = out / "notes.md"
    return f.read_text(encoding="utf-8") if f.exists() else ""


def grade_neurips(out: Path, inputs: Path) -> list[dict]:
    f = out / "neurips_intro_revised.md"
    if not f.exists():
        return [check("Output file neurips_intro_revised.md exists", False, "missing")]
    text, src = f.read_text(encoding="utf-8"), (inputs / "neurips_intro.md").read_text(encoding="utf-8")
    e, w, errs = lint(f, "--genre", "paper")
    res = [check("Lint (check_wording.py, genre paper) reports 0 errors", e == 0, f"{e} errors, {w} warnings. {errs}")]
    own = re.findall(r"\bour\s+(previous|prior|earlier)\s+(work|paper|study)\b", text, re.I)
    res.append(check("Own earlier work in the third person (no 'our previous work'), citation kept",
                     not own and "Keller et al." in text, f"'our previous work': {len(own)}; citation kept: {'Keller et al.' in text}"))
    hype = re.findall(r"\b(cornerstone|pivotal|groundbreaking|seamless\w*|undoubtedly|comprehensive|novel|large\s+margin|extensive\s+experiments)\b", text, re.I)
    res.append(check("No hype words (cornerstone, pivotal, groundbreaking, seamlessly, undoubtedly, comprehensive, novel, large margin)", not hype, "; ".join(hype) or "none"))
    sota = sentences_with(text, r"state[\s-]of[\s-]the[\s-]art")
    bad = [x for x in sota if not re.search(r"\bMSE\b|mean squared error", x)]
    res.append(check("'State-of-the-art' only in a sentence that names the metric", not bad, f"{len(sota)} uses; without metric: {bad}"))
    contrast = re.findall(r"\bnot\s+(?:only|just)\b|\bnot\b[^.;:\n]{0,80}?\bbut\b|—|\s–\s", text, re.I)
    res.append(check("No 'not X but Y' family and no em-dashes", not contrast, "; ".join(contrast) or "none"))
    need = {"9": r"\b9\b|\bnine\b", "47%": r"47\s?%", "3 times": r"\b3\s*(times|x|×)|three times", "SNIPS": r"SNIPS", "CLIP-DR": r"CLIP-DR"}
    missing = [k for k, p_ in need.items() if not re.search(p_, text)]
    res.append(check("Numbers and names kept (9 datasets, 47%, 3 times, SNIPS, CLIP-DR)", not missing, f"missing: {missing}" if missing else "all present"))
    new = numbers(text) - numbers(src)
    res.append(check("No numbers that are not in the source", not new, f"new: {sorted(new)}" if new else "none"))
    n = notes_of(out)
    res.append(check("The 'provably' claim is raised with the author (notes.md mentions the proof)", bool(re.search(r"proof|provabl|prove", n, re.I)),
                     "mentioned" if re.search(r"proof|provabl|prove", n, re.I) else "not mentioned"))
    return res


def grade_econ(out: Path, inputs: Path) -> list[dict]:
    f = out / "energy_econ_revised.md"
    if not f.exists():
        return [check("Output file energy_econ_revised.md exists", False, "missing")]
    text, src = f.read_text(encoding="utf-8"), (inputs / "energy_econ.md").read_text(encoding="utf-8")
    e, w, errs = lint(f, "--genre", "paper")
    res = [check("Lint (check_wording.py, genre paper) reports 0 errors", e == 0, f"{e} errors, {w} warnings. {errs}")]
    grades = re.findall(r"\b(seminal|laid\s+the\s+groundwork|merely|fail(?:s|ed)?\s+to|overlook\w*|great\s+progress|significant\s+strides|multifaceted)\b", text, re.I)
    res.append(check("Related work is reported without grades", not grades, "; ".join(grades) or "none"))
    cause = re.findall(r"\bcause[sd]?\b|\bcausing\b", text, re.I)
    res.append(check("No causal claim from the opt-in design ('cause' absent)", not cause, "; ".join(cause) or "none"))
    hype = re.findall(r"\b(proves?|clearly\s+demonstrat\w+|key\s+to|game[\s-]?changer|highly\s+significant)\b", text, re.I)
    res.append(check("No 'proves', 'clearly demonstrate', 'key to', 'game-changer', 'highly significant'", not hype, "; ".join(hype) or "none"))
    cites = {"Faruqui and Sergici 2010": r"Faruqui\s+and\s+Sergici,?\s*\(?2010", "Allcott 2011": r"Allcott,?\s*\(?2011",
             "Fabra et al. 2021": r"Fabra\s+et\s+al\.,?\s*\(?2021", "Harding and Lamarche 2016": r"Harding\s+and\s+Lamarche,?\s*\(?2016"}
    missing = [k for k, p_ in cites.items() if not re.search(p_, text)]
    res.append(check("All four cited works kept with their years", not missing, f"missing: {missing}" if missing else "all present"))
    need = {"2,340": r"2,340|2340", "2019": r"2019", "2023": r"2023", "9.4%": r"9\.4\s?%", "14.1%": r"14\.1\s?%", "0.01": r"0\.01"}
    missing = [k for k, p_ in need.items() if not re.search(p_, text)]
    res.append(check("All numbers kept (2,340; 2019 to 2023; 9.4%; 14.1%; p < 0.01)", not missing, f"missing: {missing}" if missing else "all present"))
    new = numbers(text) - numbers(src)
    res.append(check("No numbers that are not in the source", not new, f"new: {sorted(new)}" if new else "none"))
    return res


def grade_nature(out: Path, inputs: Path) -> list[dict]:
    f = out / "nature_energy_abstract.md"
    if not f.exists():
        return [check("Output file nature_energy_abstract.md exists", False, "missing")]
    text = f.read_text(encoding="utf-8")
    body = "\n".join(ln for ln in text.splitlines() if not ln.lstrip().startswith("#"))
    n = len(body.split())
    res = [check("At most 150 words", n <= 150, f"{n} words")]
    e, w, errs = lint(f, "--genre", "abstract")
    res.append(check("Lint (check_wording.py, genre abstract) reports 0 errors", e == 0, f"{e} errors, {w} warnings. {errs}"))
    res.append(check("Uses the Nature convention 'Here we ...' (show, report, combine, ...)", bool(re.search(r"\bHere,?\s+we\s+[a-z]+", body)),
                     "found" if re.search(r"\bHere,?\s+we", body) else "not found"))
    bad = []
    if re.search(r"\bFCR\b", body) and not re.search(r"frequency containment reserve", body, re.I):
        bad.append("FCR")
    if re.search(r"\bEVs?\b", body) and not re.search(r"electric[\s-]vehicle", body, re.I):
        bad.append("EV")
    res.append(check("Abbreviations FCR and EV are spelled out where used", not bad, f"undefined: {bad}" if bad else "ok"))
    s18 = sentences_with(body, r"\b18\s?%")
    ok18 = all(re.search(r"scenario|could|project|would|by 2030", x, re.I) for x in s18)
    res.append(check("The 2030 number is framed as a scenario or projection", ok18, f"{len(s18)} sentence(s) with 18%"))
    res.append(check("No 'significant' (no test in the notes)", not re.search(r"significan", body, re.I), "absent" if not re.search(r"significan", body, re.I) else "present"))
    src = (inputs / "nature_notes.md").read_text(encoding="utf-8")
    new = numbers(body) - numbers(src)
    res.append(check("No numbers that are not in the notes", not new, f"new: {sorted(new)}" if new else "none"))
    res.append(check("Reports the main result with its magnitude (41% lower lifecycle cost)", bool(re.search(r"41\s?%", body)), "found" if re.search(r"41\s?%", body) else "not found"))
    return res


def grade_gt(out: Path, inputs: Path) -> list[dict]:
    f = out / "gt_revised.md"
    if not f.exists():
        return [check("Output file gt_revised.md exists", False, "missing")]
    text = f.read_text(encoding="utf-8")
    e, w, errs = lint(f, "--genre", "paper")
    res = [check("Lint (check_wording.py, genre paper) reports 0 errors", e == 0, f"{e} errors, {w} warnings. {errs}")]
    notes = notes_of(out)
    bad = [x for x in sentences_with(text, r"\bprov\w*") if re.search(r"simulat", x, re.I)]
    flagged = bool(re.search(r"simulat", notes, re.I) and re.search(r"prov|proof", notes, re.I))
    res.append(check("'Prove using simulations' is reworded, or flagged in notes.md (the prompt froze doubtful math)", not bad or flagged,
                     f"still in text: {bool(bad)}; flagged in notes: {flagged}"))
    hype = re.findall(r"\b(not\s+only|deep\s+insights?|key\s+insight)\b|—", text, re.I)
    res.append(check("No 'not only', 'deep insights', 'key insight' or em-dash", not hype, "; ".join(map(str, hype)) or "none"))
    dram = bool(re.search(r"dramatically", text, re.I))
    res.append(check("'Dramatically' in Proposition 2 is removed, or flagged in notes.md", not dram or bool(re.search(r"dramatically", notes, re.I)),
                     f"still in text: {dram}; flagged in notes: {bool(re.search(r'dramatically', notes, re.I))}"))
    keep = [r"Proposition\s+1", r"Proposition\s+2", r"e_i", r"c_i\s*e_i", r"Tullock", r"e_i\s*/\s*\(e_1\s*\+\s*e_2\)"]
    missing = [k for k in keep if not re.search(k, text)]
    res.append(check("Both propositions and the model's math kept", not missing, f"missing: {missing}" if missing else "all present"))
    n = notes_of(out) + "\n" + text
    flagged = bool(re.search(r"always\s+wins?|probabil", n, re.I))
    res.append(check("notes.md flags the 'always wins' claim (Tullock contests are probabilistic)", flagged, "flagged" if flagged else "not flagged"))
    return res


def grade_sports(out: Path, inputs: Path) -> list[dict]:
    f = out / "poster_results_box.md"
    if not f.exists():
        return [check("Output file poster_results_box.md exists", False, "missing")]
    text, src = f.read_text(encoding="utf-8"), (inputs / "sports_results.md").read_text(encoding="utf-8")
    e, w, errs = lint(f, "--genre", "poster", "--ste")
    res = [check("Lint in STE mode (check_wording.py --ste, genre poster) reports 0 errors", e == 0, f"{e} errors, {w} warnings. {errs}")]
    need = ["8", "14", "13", "1.92", "0.08", "1.86", "0.07", "0.03", "2.9", "0.71", "0.12", "1.30"]
    have = numbers(text)
    missing = [x for x in need if (x.lstrip("0") or "0") not in have and x not in text]
    res.append(check("All numbers kept", not missing, f"missing: {missing}" if missing else "all present"))
    new = numbers(text) - numbers(src)
    res.append(check("No numbers that are not in the source", not new, f"new: {sorted(new)}" if new else "none"))
    gen = re.findall(r"\ball\s+(athletes|sports|levels)\b", text, re.I)
    named = bool(re.search(r"U19|soccer|football", text, re.I))
    res.append(check("No generalization beyond the sample ('all athletes', 'all sports' absent; the sample is named)", not gen and named,
                     f"generalizations: {gen}; sample named: {named}"))
    hype = re.findall(r"\b(essential|game[\s-]?changer|clearly\s+demonstrat\w+)\b", text, re.I)
    res.append(check("No 'essential', 'game-changer', 'clearly demonstrates'", not hype, "; ".join(hype) or "none"))
    bad = [x for x in sentences_with(text, r"significan") if not re.search(r"p\s*[=<]", x)]
    res.append(check("'Significant' only together with its test, or not at all", not bad, f"{bad}" if bad else "ok"))
    res.append(check("Effect size kept with its confidence interval", bool(re.search(r"0\.71", text) and re.search(r"0\.12", text) and re.search(r"1\.30?", text)),
                     "kept" if re.search(r"0\.71", text) else "missing"))
    res.append(check("No semicolons", ";" not in prose_of(f), f"{prose_of(f).count(';')} found"))
    return res


def grade_folien(out: Path, inputs: Path) -> list[dict]:
    import ast
    f = out / "folien_revised.py"
    if not f.exists():
        return [check("Output file folien_revised.py exists", False, "missing")]
    text, src = f.read_text(encoding="utf-8"), (inputs / "folien.py").read_text(encoding="utf-8")
    e, w, errs = lint(f, "--genre", "slides")
    res = [check("Lint (check_wording.py, genre slides) reports 0 errors", e == 0, f"{e} errors, {w} warnings. {errs}")]
    try:
        tree = ast.parse(text)
        calls = sum(1 for nd in ast.walk(tree) if isinstance(nd, ast.Call) and getattr(nd.func, "id", "") == "slide")
        res.append(check("Still valid Python with both slide() calls", calls == 2, f"slide() calls: {calls}"))
    except SyntaxError as exc:
        res.append(check("Still valid Python with both slide() calls", False, f"SyntaxError: {exc}"))
    res.append(check("Still German", cw.detect_lang(prose_of(f)) == "de", cw.detect_lang(prose_of(f))))
    prose = prose_of(f)
    bad = re.findall(r"\bnicht\s+nur\b|\s–\s|—|\bscheiter\w*|\binnovativ\w*|\bganzheitlich\w*|\bnahtlos\w*|\bdramatisch\w*", prose, re.I)
    res.append(check("No 'nicht nur', Gedankenstrich, 'scheitern', 'innovativ', 'ganzheitlich', 'nahtlos', 'dramatisch'", not bad, "; ".join(bad) or "none"))
    res.append(check("No 'signifikant' (no test given)", not re.search(r"signifikan", prose, re.I), "absent" if not re.search(r"signifikan", prose, re.I) else "present"))
    need = {"2019": r"2019", "2023": r"2023", "1,2": r"1,2\b", "3,1": r"3,1\b", "23": r"\b23\b", "4": r"\b4\b|\bvier\b", "2030": r"2030"}
    missing = [k for k, p_ in need.items() if not re.search(p_, text)]
    res.append(check("All numbers kept (2019, 2023, 1,2, 3,1, 23, 4, 2030)", not missing, f"missing: {missing}" if missing else "all present"))
    new = numbers(prose) - numbers(prose_of(inputs / "folien.py"))
    res.append(check("No numbers that are not in the source", not new, f"new: {sorted(new)}" if new else "none"))
    return res


GRADERS = {"ejor-intro-revision": grade_ejor, "explainer-ste-rewrite": grade_ste, "icis-abstract-from-notes": grade_icis,
           "neurips-intro-revision": grade_neurips, "energy-econ-revision": grade_econ, "nature-energy-abstract": grade_nature,
           "game-theory-model-section": grade_gt, "sports-poster-ste": grade_sports, "german-slides": grade_folien}


def main() -> int:
    it = Path(sys.argv[1]).resolve()
    inputs = it / "inputs" if (it / "inputs").is_dir() else Path(__file__).resolve().parent / "files"
    for eval_dir in sorted(it.glob("eval-*")):
        name = re.sub(r"^eval-\d+-", "", eval_dir.name)
        for run in sorted(eval_dir.glob("*/run-*")):
            exps = GRADERS[name](run / "outputs", inputs)
            p = sum(x["passed"] for x in exps)
            grading = {"expectations": exps, "summary": {"passed": p, "failed": len(exps) - p, "total": len(exps),
                                                          "pass_rate": round(p / len(exps), 2)}}
            # timing and tokens stay in timing.json, where the aggregator reads both
            (run / "grading.json").write_text(json.dumps(grading, indent=2), encoding="utf-8")
            print(f"{eval_dir.name}/{run.parent.name}: {p}/{len(exps)}")
            for x in exps:
                if not x["passed"]:
                    print(f"    FAIL {x['text']}: {x['evidence'][:160]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
