# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Build a D3 explainer: sections/*.html + explainer.toml -> dist/<name>.html (one offline file).

    uv run d3x/build.py            # from the explainer folder
    uv run d3x/build.py --draft    # TODO markers allowed

Beyond concatenation, the build keeps the explainer honest against the repository:
  * [[code:path:line symbol]] chips must point at a file, line and symbol that exist
  * [[paper:eq:label]] chips must match a \\label in the paper sources
  * <pre class="code" data-src=... data-lines=...> is filled with the real lines from the repo
  * <div class="eq" data-label=...> is filled with the real equation from the paper .tex
Exit code 1 means at least one error; warnings never fail the build.
"""
from __future__ import annotations

import argparse
import base64
import datetime as dt
import html
import json
import re
import shutil
import subprocess
import sys
import tomllib
import urllib.parse
from pathlib import Path

ENGINE = Path(__file__).resolve().parent
BUDGET = {"focus": (1200, 2), "overview": (2500, 4), "standard": (6000, 8), "deep": (12000, 14)}   # main-line words, widgets
LABEL_PREFIX = re.compile(r"^(eq|eqn|sec|subsec|fig|tab|tbl|thm|lem|prop|cor|def|alg|app|ass|asm|rem|ex)[:.]", re.I)
PAPER_NAMES = {"eq": "Eq.", "eqn": "Eq.", "sec": "§", "subsec": "§", "fig": "Fig.", "tab": "Table", "tbl": "Table", "thm": "Thm.",
               "lem": "Lemma", "prop": "Prop.", "cor": "Cor.", "def": "Def.", "alg": "Alg.", "app": "App.", "ass": "Ass.", "asm": "Ass.",
               "rem": "Remark", "ex": "Ex."}
MATH_ENVS = "equation|align|gather|multline|eqnarray|alignat|flalign|dmath"
OPTIONAL_KATEX_FONTS = {"Fraktur": r"\\(mathfrak|frak)\b", "SansSerif": r"\\(mathsf|textsf)\b", "Script": r"\\mathscr\b",
                        "Typewriter": r"\\(mathtt|texttt)\b", "Caligraphic": r"\\(mathcal|cal)\b"}
WORDING = [  # (pattern, advice) -- same house rules as d3-abstract / d3-presentation, warnings only
    (r"(?<!\d)\s[\u2013\u2014]\s|\u2014", "dash as punctuation: use a comma, a colon, or a new sentence"),
    (r"\bnot\s+(only|just|merely|simply)\b", "contrast framing: state the positive claim"),
    (r"\b(leverag\w+|delv\w+|seamless\w*|transformative|synerg\w+|robust framework|comprehensive\w*|holistic\w*|paradigm shift|game.chang\w+|cutting.edge|state.of.the.art)\b",
     "marker vocabulary: say the concrete thing"),
]
GAP_WORDING = [  # only in sections about prior work (id, data-nav or data-kicker mentions gap / related / prior): elsewhere these are ordinary technical phrases
    (r"\b(fail(s|ed)? to|suffer(s|ed)? from|overlook(s|ed)?|neglect(s|ed)?|merely|seminal|pioneering)\b", "related work: state what it established and where it stops, as a fact"),
]


class Report:
    def __init__(self) -> None:
        self.errors: list[str] = []
        self.warnings: list[str] = []

    def error(self, msg: str) -> None:
        self.errors.append(msg)

    def warn(self, msg: str) -> None:
        self.warnings.append(msg)


def lineno(text: str, pos: int) -> int:
    return text.count("\n", 0, pos) + 1


def git(repo: Path, *args: str) -> str:
    try:
        return subprocess.run(["git", "--no-optional-locks", "-C", str(repo), *args], capture_output=True, text=True, timeout=10).stdout.strip()
    except (OSError, subprocess.SubprocessError):
        return ""


# ---------------------------------------------------------------- paper index
class Paper:
    """Labels, numbers and equation bodies from the paper's .tex / .aux files."""

    def __init__(self, repo: Path, dirs: list[str]) -> None:
        self.labels: dict[str, tuple[Path, int]] = {}
        self.numbers: dict[str, str] = {}
        self.texts: dict[Path, str] = {}
        for d in dirs:
            root = (repo / d)
            if not root.exists():
                continue
            files = [root] if root.is_file() else sorted(root.rglob("*.tex"))[:400]
            for f in files:
                try:
                    t = f.read_text(encoding="utf-8", errors="replace")
                except OSError:
                    continue
                self.texts[f] = t
                for m in re.finditer(r"\\label\{([^}]+)\}", t):
                    self.labels.setdefault(m.group(1), (f, m.start()))
            if root.is_dir():
                for aux in sorted(root.rglob("*.aux"))[:200]:
                    for m in re.finditer(r"\\newlabel\{([^}]+)\}\{\{([^{}]*)\}", aux.read_text(encoding="utf-8", errors="replace")):
                        self.numbers.setdefault(m.group(1), m.group(2))

    def titles(self) -> list[str]:
        out = []
        for t in self.texts.values():
            out += [re.sub(r"\\[a-zA-Z]+\*?|[{}$]", "", h).strip() for h in re.findall(r"\\(?:sub)*section\*?\{((?:[^{}]|\{[^{}]*\})*)\}", re.sub(r"(?<!\\)%.*", "", t))]
        return out

    def nice(self, label: str) -> str:
        pre = label.split(":")[0].split(".")[0].lower()
        name, num = PAPER_NAMES.get(pre), self.numbers.get(label)
        if name and num:
            return f"{name} ({num})" if name == "Eq." else f"{name}{'' if name == '§' else ' '}{num}"
        return label

    def equation(self, label: str) -> str | None:
        if label not in self.labels:
            return None
        f, pos = self.labels[label]
        t = self.texts[f]
        begins = [m for m in re.finditer(r"\\begin\{(%s)(\*?)\}" % MATH_ENVS, t[:pos])]
        if not begins:
            return None
        b = begins[-1]
        env = b.group(1) + b.group(2)
        end = t.find("\\end{%s}" % env, pos)
        if end < 0 or "\\end{%s}" % env in t[b.end():pos]:
            return None
        body = t[b.end():end]
        if b.group(1) == "alignat":
            body = re.sub(r"^\s*\{\d+\}", "", body)
        n_labels = len(re.findall(r"\\label\{", body))
        body = re.sub(r"(?<!\\)%.*", "", body)
        body = re.sub(r"\\label\{[^}]*\}|\\nonumber\b|\\notag\b", "", body)
        body = re.sub(r"\\(?:eq|c|C|auto)?ref\{([^}]+)\}", lambda m: r"\text{(%s)}" % self.numbers.get(m.group(1), "?"), body)
        body = body.strip()
        kind = b.group(1)
        if kind in ("align", "flalign", "alignat", "eqnarray"):
            if kind == "eqnarray":
                body = re.sub(r"&\s*(=|\\leq?|\\geq?|<|>|\\approx|\\equiv)\s*&", r"&\1", body)
            body = "\\begin{aligned}\n%s\n\\end{aligned}" % body
        elif kind in ("gather", "multline"):
            body = "\\begin{gathered}\n%s\n\\end{gathered}" % body
        elif ("\\\\" in body or "&" in body) and "\\begin{" not in body:
            body = "\\begin{aligned}\n%s\n\\end{aligned}" % body
        if n_labels == 1 and label in self.numbers:
            body += "\n\\tag{%s}" % self.numbers[label]
        return body


def read_macros(repo: Path, files: list[str], rep: Report) -> dict[str, str]:
    """Simple \\newcommand / \\DeclareMathOperator definitions -> KaTeX macros."""
    out: dict[str, str] = {}

    def group(t: str, i: int) -> tuple[str, int] | None:
        if i >= len(t) or t[i] != "{":
            return None
        depth, j = 0, i
        while j < len(t):
            if t[j] == "\\":
                j += 2
                continue
            if t[j] == "{":
                depth += 1
            elif t[j] == "}":
                depth -= 1
                if depth == 0:
                    return t[i + 1:j], j + 1
            j += 1
        return None

    for name in files:
        f = repo / name
        if not f.exists():
            rep.warn(f"macros_from: {name} not found")
            continue
        t = re.sub(r"(?<!\\)%.*", "", f.read_text(encoding="utf-8", errors="replace"))
        for m in re.finditer(r"\\(?:re|provide)?newcommand\*?\s*(?:\{(\\[A-Za-z@]+)\}|(\\[A-Za-z@]+))\s*(?:\[(\d)\])?\s*(\[)?", t):
            if m.group(4):          # optional-argument default: KaTeX macros cannot express it
                continue
            g = group(t, m.end())
            if g:
                out[m.group(1) or m.group(2)] = g[0]
        for m in re.finditer(r"\\DeclareMathOperator(\*?)\s*\{(\\[A-Za-z]+)\}\s*", t):
            g = group(t, m.end())
            if g:
                out[m.group(2)] = "\\operatorname%s{%s}" % (m.group(1), g[0])
        for m in re.finditer(r"\\def\s*(\\[A-Za-z]+)\s*(?=\{)", t):
            g = group(t, m.end())
            if g:
                out.setdefault(m.group(1), g[0])
    for k in list(out):
        out[k] = out[k].replace("\\xspace", "").replace("\\ensuremath", "")
        if re.search(r"\\(usepackage|begin\{(?!aligned|cases|pmatrix|bmatrix|matrix|array))", out[k]):
            del out[k]
    return out


# ---------------------------------------------------------------- source text passes
PROTECT = re.compile(r"<!--.*?-->|<script\b.*?</script>|<style\b.*?</style>|<pre\b.*?</pre>|<code\b.*?</code>", re.S | re.I)
MATH = re.compile(r"\$\$(.+?)\$\$|\\\[(.+?)\\\]|\\\((.+?)\\\)|(?<![\\$\w])\$(?![\s$])([^$\n]{1,400}?)(?<![\s\\])\$(?![\d\w])", re.S)
REAL_TAG = re.compile(r"</|<[A-Za-z][A-Za-z0-9]*(\s[^<>]*)?/?>")


def outside_protected(text: str):
    """Yield (is_protected, chunk) pairs covering text."""
    pos = 0
    for m in PROTECT.finditer(text):
        if m.start() > pos:
            yield False, text[pos:m.start()]
        yield True, m.group(0)
        pos = m.end()
    if pos < len(text):
        yield False, text[pos:]


def escape_math(text: str, where: str, rep: Report, stats: dict) -> str:
    """HTML-escape <, >, & inside math so `$a<b$` survives the HTML parser."""
    def fix(m: re.Match) -> str:
        seg = m.group(0)
        inner = next(g for g in m.groups() if g is not None)
        if REAL_TAG.search(inner):
            if m.group(4) is not None:      # `$` pair that spans real markup: a literal dollar, not math
                rep.warn(f"{where}: a '$' pair spans HTML tags near '{seg[:40]}...'; for a literal dollar write <span class=\"usd\">$</span>")
                return seg
            rep.warn(f"{where}: HTML tag inside display math near '{inner.strip()[:40]}...'")
            return seg
        stats["equations"] += 1
        stats["display"] += m.group(1) is not None or m.group(2) is not None
        stats["math_src"].append(inner)
        esc = re.sub(r"&(?!(?:amp|lt|gt|#\d+);)", "&amp;", inner).replace("<", "&lt;").replace(">", "&gt;")
        return seg.replace(inner, esc, 1)

    return "".join(chunk if prot else MATH.sub(fix, chunk) for prot, chunk in outside_protected(text))


def plain_words(fragment: str) -> int:
    fragment = re.sub(r'data-why="([^"]*)"', lambda m: '> ' + m.group(1) + ' <span ', fragment)   # the reason of a derivation step is prose the reader reads
    fragment += " " + " ".join(m.group(2) for m in re.finditer(r"detail:\s*(['\"])(.*?)(?<!\\)\1", fragment, flags=re.S))   # so is the text inside flow boxes
    t = PROTECT.sub(" ", fragment)
    t = MATH.sub(" x ", t)
    t = re.sub(r"<[^>]+>", " ", t)
    t = re.sub(r"\[\[[^\]]*\]\]", " ", t)
    return len(re.findall(r"[A-Za-zÀ-ÿ0-9][\w'’-]*", html.unescape(t)))


def strip_details(fragment: str) -> str:
    return re.sub(r"<details\b.*?</details>", " ", fragment, flags=re.S | re.I)


# ---------------------------------------------------------------- builder
class Builder:
    def __init__(self, proj: Path, draft: bool) -> None:
        self.proj, self.draft, self.rep = proj, draft, Report()
        cfg_file = proj / "explainer.toml"
        if not cfg_file.exists():
            sys.exit(f"error: {cfg_file} not found. Scaffold a project with the skill's scripts/init.py")
        self.cfg = tomllib.loads(cfg_file.read_text(encoding="utf-8"))
        self.repo = (proj / self.cfg.get("repo", "..")).resolve()
        paper = self.cfg.get("paper", [])
        self.paper = Paper(self.repo, [paper] if isinstance(paper, str) else paper)
        self.vault = (self.repo / self.cfg["vault"]) if self.cfg.get("vault") else None
        self.vault_notes: dict[str, Path] | None = None
        self.chips: dict[str, dict] = {}
        self.figures: dict[str, int] = {}
        self.fig_no = 0
        self.raw: dict[str, str] = {}
        self.evidence: dict[str, str] = {}
        self.chip_state: dict[str, str] = {}
        self.stats = {"equations": 0, "display": 0, "pulled": 0, "math_src": [], "widgets": 0, "flows": 0, "derivations": 0, "code": 0, "images": 0}
        self.commit = git(self.repo, "rev-parse", "--short", "HEAD")
        self.dirty = bool(git(self.repo, "status", "--porcelain", "--untracked-files=no"))
        self.remote = self._github(git(self.repo, "remote", "get-url", "origin"))
        self.full_commit = git(self.repo, "rev-parse", "HEAD")

    @staticmethod
    def _github(url: str) -> str:
        m = re.match(r"(?:git@github\.com:|https://github\.com/)([^/]+/[^/]+?)(?:\.git)?/?$", url)
        return f"https://github.com/{m.group(1)}" if m else ""

    # ---- directives
    def fill_code(self, text: str, where: str) -> str:
        def repl(m: re.Match) -> str:
            attrs = dict(re.findall(r'([\w-]+)="([^"]*)"', m.group(1)))
            src, lines = attrs.get("data-src"), attrs.get("data-lines", "")
            if not src:
                return m.group(0)
            f = self.repo / src
            if not f.is_file():
                self.rep.error(f"{where}: <pre class=code> data-src=\"{src}\" does not exist in the repository")
                return m.group(0)
            all_lines = f.read_text(encoding="utf-8", errors="replace").splitlines()
            lm = re.match(r"(\d+)(?:-(\d+))?$", lines)
            a, b = (int(lm.group(1)), int(lm.group(2) or lm.group(1))) if lm else (1, min(len(all_lines), 40))
            sym = attrs.get("data-symbol")
            if sym:                                  # anchored by symbol: the excerpt follows the code when it moves
                hit = next((i for i, ln in enumerate(all_lines, 1) if sym in ln), None)
                if hit is None:
                    self.rep.error(f"{where}: <pre class=code> data-symbol=\"{sym}\" does not occur in {src}")
                    return m.group(0)
                indent0 = len(all_lines[hit - 1]) - len(all_lines[hit - 1].lstrip())
                end = hit
                for i in range(hit + 1, min(len(all_lines), hit + int(attrs.get("data-max", 40))) + 1):
                    ln = all_lines[i - 1]
                    if ln.strip() and len(ln) - len(ln.lstrip()) <= indent0 and not ln.lstrip().startswith((")", "]", "}")):
                        break
                    if ln.strip():
                        end = i
                a, b = hit, end
            elif lm and b - a >= 2:
                first = next((x.strip() for x in all_lines[a - 1:b] if x.strip()), "")
                self.rep.warn(f"{where}: code excerpt {src}:{a}-{b} is selected by line numbers and shows other lines once the file changes. It now begins with `{first[:70]}`: "
                              f"is that still the intended code? Anchor it with data-symbol=\"def name\" instead")
            if a < 1 or b > len(all_lines) or a > b:
                self.rep.error(f"{where}: data-lines=\"{lines}\" is outside {src} (1-{len(all_lines)})")
                return m.group(0)
            if b - a > 60:
                self.rep.warn(f"{where}: code excerpt {src}:{a}-{b} is {b - a + 1} lines; excerpts over ~40 lines rarely get read")
            body = all_lines[a - 1:b]
            indent = min((len(s) - len(s.lstrip()) for s in body if s.strip()), default=0)
            code = html.escape("\n".join(s[indent:] for s in body), quote=False)
            lang = attrs.get("data-lang") or {".py": "py", ".js": "js", ".ts": "js", ".jl": "jl", ".r": "r", ".R": "r"}.get(f.suffix, "py")
            href = self.code_href(src, a, b)
            cap = f'<a href="{href}" target="_blank" rel="noopener">{html.escape(src)}:{a}-{b}</a>' if href else f"{html.escape(src)}:{a}-{b}"
            self.stats["code"] += 1
            note = html.escape(attrs.get("data-note", ""))
            return f'<pre class="code"><span class="cap"><span>{cap}</span><span>{note}</span></span><code data-lang="{lang}" data-start="{a}">{code}\n</code></pre>'

        return re.sub(r'<pre\s+([^>]*class="code"[^>]*)>\s*</pre>', repl, text)

    def fill_equations(self, text: str, where: str) -> str:
        def repl(m: re.Match) -> str:
            attrs = dict(re.findall(r'([\w-]+)="([^"]*)"', m.group(1)))
            label = attrs.get("data-label")
            if "eq" not in attrs.get("class", "").split() or not label:
                return m.group(0)
            body = self.paper.equation(label)
            if body is None:
                known = ", ".join(sorted(k for k in self.paper.labels if k.startswith(label.split(":")[0]))[:12]) or "none found"
                self.rep.error(f"{where}: <div class=eq data-label=\"{label}\">: no equation with that \\label in the paper sources (labels with that prefix: {known})")
                return m.group(0)
            self.stats["pulled"] += 1
            return f'<div {m.group(1)}>$${body}$$<div class="eqsrc">[[paper:{label}]]</div></div>'

        return re.sub(r"<div\s+([^>]*data-label=[^>]*)>\s*</div>", repl, text)

    def fill_data(self, text: str, where: str) -> str:
        def repl(m: re.Match) -> str:
            src = re.search(r'data-src="([^"]+)"', m.group(1))
            if not src:
                return m.group(0)
            f = self.find_file(src.group(1))
            if f is None:
                self.rep.error(f"{where}: data file \"{src.group(1)}\" not found (looked in the explainer folder and the repository)")
                return m.group(0)
            raw = f.read_text(encoding="utf-8")
            try:
                data = json.loads(raw)
            except json.JSONDecodeError as e:
                self.rep.error(f"{where}: {src.group(1)} is not valid JSON ({e})")
                return m.group(0)
            packed = json.dumps(data, separators=(",", ":")).replace("</", "<\\/")
            if len(packed) > 400_000:
                self.rep.warn(f"{where}: {src.group(1)} embeds {len(packed) // 1000} kB; aggregate or subsample before embedding")
            return f"<script {m.group(1)}>{packed}</script>"

        return re.sub(r'<script\s+([^>]*type="application/json"[^>]*)>\s*</script>', repl, text)

    def find_file(self, rel: str) -> Path | None:
        for base in (self.proj, self.repo):
            f = (base / rel)
            if f.is_file():
                return f
        return None

    def inline_images(self, text: str, where: str) -> str:
        def repl(m: re.Match) -> str:
            src = m.group(2)
            if re.match(r"(data:|https?:)", src):
                if src.startswith("http"):
                    self.rep.warn(f"{where}: remote image {src[:60]} breaks the offline file; copy it into figures/")
                return m.group(0)
            f = self.find_file(src)
            if f is None:
                self.rep.error(f"{where}: image \"{src}\" not found (looked in the explainer folder and the repository)")
                return m.group(0)
            if f.suffix.lower() == ".pdf":
                f = self.rasterize(f, where)
                if f is None:
                    return m.group(0)
            mime = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".svg": "image/svg+xml", ".webp": "image/webp", ".gif": "image/gif"}.get(f.suffix.lower())
            if not mime:
                self.rep.error(f"{where}: unsupported image type {f.suffix} ({src})")
                return m.group(0)
            raw = f.read_bytes()
            if len(raw) > 1_500_000:
                self.rep.warn(f"{where}: {src} is {len(raw) // 1000} kB; downscale it, the explainer should stay easy to email")
            self.stats["images"] += 1
            return f'{m.group(1)}data:{mime};base64,{base64.b64encode(raw).decode()}{m.group(3)}'

        return re.sub(r'(<img\b[^>]*?\ssrc=")([^"]+)(")', repl, text)

    def rasterize(self, pdf: Path, where: str) -> Path | None:
        if not shutil.which("pdftoppm"):
            self.rep.error(f"{where}: {pdf.name} is a PDF and pdftoppm (poppler) is not installed; export the figure as PNG or SVG")
            return None
        cache = self.proj / "figures" / ".cache"
        cache.mkdir(parents=True, exist_ok=True)
        out = cache / (pdf.stem + ".png")
        if not out.exists() or out.stat().st_mtime < pdf.stat().st_mtime:
            subprocess.run(["pdftoppm", "-png", "-r", "170", "-singlefile", str(pdf), str(out.with_suffix(""))], check=True)
        return out

    # ---- chips
    def code_href(self, path: str, a: int | None, b: int | None = None) -> str:
        mode = self.cfg.get("code_links", "auto")
        if mode == "auto":
            mode = "github" if self.remote and self.full_commit else "none"
        if mode == "github" and self.remote:
            frag = f"#L{a}" + (f"-L{b}" if b and b != a else "") if a else ""
            return f"{self.remote}/blob/{self.full_commit or 'HEAD'}/{urllib.parse.quote(path)}{frag}"
        if mode == "vscode":
            return f"vscode://file/{urllib.parse.quote(str(self.repo / path))}" + (f":{a}" if a else "")
        return ""

    def check_chip(self, kind: str, body: str, where: str) -> dict:
        target, _, label = body.partition("|")
        target = target.strip()
        key = kind + (":" + body if body else "")
        info: dict = {"ok": True}
        if label:
            info["label"] = label.strip()
        if kind == "code":
            m = re.match(r"(?P<path>[^:\s]+)(?::(?P<a>\d+)(?:-(?P<b>\d+))?)?(?:\s+(?P<sym>\S.*))?$", target)
            if not m:
                self.rep.error(f"{where}: cannot parse [[code:{body}]]; expected path[:line[-line]] [symbol]")
                return {"ok": False}
            f = self.repo / m["path"]
            if not f.is_file():
                self.rep.error(f"{where}: [[code:{body}]]: {m['path']} does not exist in the repository")
                return {"ok": False}
            lines = f.read_text(encoding="utf-8", errors="replace").splitlines()
            a = int(m["a"]) if m["a"] else None
            b = int(m["b"]) if m["b"] else None
            if a and a > len(lines):
                self.rep.error(f"{where}: [[code:{body}]]: line {a} is beyond the end of {m['path']} ({len(lines)} lines)")
                return {"ok": False}
            if m["sym"]:
                hits = [i + 1 for i, s in enumerate(lines) if m["sym"] in s]
                if not hits:
                    self.rep.error(f"{where}: [[code:{body}]]: '{m['sym']}' does not occur in {m['path']}")
                    return {"ok": False}
                near = min(hits, key=lambda h: abs(h - (a or h)))
                if a is not None and abs(near - a) > 2:
                    self.rep.warn(f"{where}: [[code:{body}]]: '{m['sym']}' is now at line {near}, not {a}; the chip shows and links {near}. Update the number, and reread the sentence: moved code has often changed")
                if a is None or near != a:
                    a, b = near, None          # the symbol is the anchor; the number is a hint
            if a:
                lo, hi = max(1, a - 3), min(len(lines), (b or a) + 6)
                self.evidence[key] = "\n".join(f"{i:>5}  {lines[i - 1]}" for i in range(lo, hi + 1))
            sym = re.sub(r"^(def|class|function|struct|async def)\s+", "", m["sym"]).split("(")[0] if m["sym"] else ""
            short = Path(m["path"]).name if sym else "/".join(Path(m["path"]).parts[-2:])
            info.setdefault("label", short + (f":{a}" if a else "") + (f" {sym}" if sym else ""))
            info["title"] = m["path"] + (f":{a}" if a else "") + (f"  {m['sym']}" if m["sym"] else "")
            href = self.code_href(m["path"], a, b)
            if href:
                info["href"] = href
        elif kind == "paper":
            if target.startswith("§") and self.paper.texts:
                want = re.sub(r"\W+", " ", target[1:]).strip().lower()
                titles = self.paper.titles()
                hit = next((t for t in titles if want and want in re.sub(r"\W+", " ", t).strip().lower()), None)
                if hit is None:
                    self.rep.error(f"{where}: [[paper:{body}]]: no \\section or \\subsection title contains '{target[1:].strip()}' (titles: {'; '.join(titles[:14])})")
                    return {"ok": False}
                info.setdefault("label", "§ " + hit)
            elif target in self.paper.labels:
                info.setdefault("label", self.paper.nice(target))
                f, pos = self.paper.labels[target]
                eq = self.paper.equation(target) if re.match(r"eqn?[:.]", target, re.I) else None
                ctx_lines = self.paper.texts[f].splitlines()
                ln = lineno(self.paper.texts[f], pos)
                self.evidence[key] = eq if eq else "\n".join(ctx_lines[max(0, ln - 2):ln + 3])[:700]
                info["title"] = f"{f.relative_to(self.repo)}:{lineno(self.paper.texts[f], pos)}  \\label{{{target}}}"
            elif LABEL_PREFIX.match(target) and self.paper.texts:
                pre = target.split(":")[0]
                known = ", ".join(sorted(k for k in self.paper.labels if k.startswith(pre))[:12]) or "none"
                self.rep.error(f"{where}: [[paper:{body}]]: no \\label{{{target}}} in the paper sources ({pre} labels: {known})")
                return {"ok": False}
        elif kind == "vault":
            if self.vault is None or not self.vault.exists():
                self.rep.warn(f"{where}: [[vault:{body}]] used but no vault is configured in explainer.toml")
            else:
                if self.vault_notes is None:
                    self.vault_notes = {p.stem.lower(): p for p in self.vault.rglob("*.md")}
                p = self.vault_notes.get(Path(target).stem.lower())
                if p is None:
                    self.rep.error(f"{where}: [[vault:{body}]]: no note named '{Path(target).stem}' in {self.vault.name}")
                    return {"ok": False}
                note = re.sub(r"\A---.*?---\s*", "", p.read_text(encoding="utf-8", errors="replace"), flags=re.S)
                self.evidence[key] = re.sub(r"\s+", " ", note)[:420]
                rel = p.relative_to(self.vault).with_suffix("")
                info["href"] = "obsidian://open?vault=%s&file=%s" % (urllib.parse.quote(self.vault.name), urllib.parse.quote(str(rel)))
                info.setdefault("label", p.stem)
        elif kind in ("result", "file"):
            f = self.repo / target.split(":")[0]
            if not f.exists():
                self.rep.error(f"{where}: [[{kind}:{body}]]: {target} does not exist in the repository")
                return {"ok": False}
            info.setdefault("label", "/".join(Path(target).parts[-2:]))
            info["title"] = target
            if f.is_file() and f.suffix.lower() in {".json", ".csv", ".md", ".txt", ".yaml", ".yml", ".toml", ".tex"}:
                body_text = f.read_text(encoding="utf-8", errors="replace")      # a reviewer checks numbers against this: small files go in whole
                self.evidence[key] = body_text if len(body_text) <= 6000 else body_text[:1500] + f"\n... ({len(body_text):,} characters in total; open the file for the rest)"
        return info

    def collect_chips(self, text: str, where: str) -> None:
        for m in re.finditer(r"\[\[(code|paper|vault|result|file|reading|src)(?::([^\]]*))?\]\]", text):
            key = m.group(1) + (":" + m.group(2) if m.group(2) else "")
            here = f"{where}:{lineno(text, m.start())}"
            if key not in self.chips:
                n_err, n_warn = len(self.rep.errors), len(self.rep.warnings)
                self.chips[key] = self.check_chip(m.group(1), m.group(2) or "", here)
                self.chip_state[key] = "error" if len(self.rep.errors) > n_err else "warn" if len(self.rep.warnings) > n_warn else "ok"
            elif self.chip_state.get(key) == "error":         # every place that uses a broken pointer needs the fix, not only the first
                self.rep.error(f"{here}: [[{key}]]: the same unresolved pointer again")
            elif self.chip_state.get(key) == "warn":
                self.rep.warn(f"{here}: [[{key}]]: the same outdated pointer again")

    # ---- lint
    def lint(self, text: str, where: str, gap_section: bool = False) -> None:
        if not self.draft:
            for m in re.finditer(r"\b(TODO|TBD|FIXME|XXX)\b", text):
                self.rep.error(f"{where}:{lineno(text, m.start())}: leftover {m.group(1)} (use --draft while writing)")
        keep_why = re.sub(r'data-why="([^"]*)"', lambda m: ">" + " " * 9 + m.group(1) + "<", text)      # step reasons are prose; same length, so line numbers hold
        prose = "".join(" " * len(c) if p else c for p, c in outside_protected(keep_why))
        prose = MATH.sub(lambda m: " " * len(m.group(0)), prose)
        prose = re.sub(r">\s*[\u2013\u2014-]\s*<", lambda m: ">" + " " * (len(m.group(0)) - 2) + "<", prose)   # a lone dash in a table cell means "no"
        prose = re.sub(r"<[^>]+>", lambda m: " " * len(m.group(0)), prose)
        prose = re.sub(r"\[\[[^\]]*\]\]", lambda m: " " * len(m.group(0)), prose)      # note and file names inside chips are not the author's prose
        for pat, advice in WORDING + (GAP_WORDING if gap_section else []):
            for m in re.finditer(pat, prose, flags=re.I):
                self.rep.warn(f"{where}:{lineno(text, m.start())}: \"{m.group(0).strip()}\": {advice}")
        for m in re.finditer(r"\\(mathcal|mathbb)\s*\{?\s*([a-z])\b", text):
            self.rep.warn(f"{where}:{lineno(text, m.start())}: \\{m.group(1)}{{{m.group(2)}}}: calligraphic and blackboard fonts have capitals only; the lowercase letter falls back to another font")
        if self.paper.numbers:       # the paper's numbers are known: hand-typed ones go stale when the paper changes, chips do not
            for m in re.finditer(r"\b(Eq(?:uation|\.|s\.)?\s*\(\d+\)|(?:Theorem|Thm\.|Lemma|Proposition|Prop\.)\s*\d+)", prose):
                self.rep.warn(f"{where}:{lineno(text, m.start())}: hand-typed \"{m.group(1)}\": a [[paper:<label>]] chip prints the number from the paper's .aux and stays right when the paper is renumbered")
        for m in re.finditer(r"<figcaption>\s*(?:<b>)?\s*(Fig(?:ure|\.)\s*\d+)", text):
            self.rep.warn(f"{where}:{lineno(text, m.start())}: hard-coded \"{m.group(1)}\": write {{fig}} and the build numbers it; refer to it elsewhere as {{fig:<figure id>}}")
        for m in re.finditer(r"Math\.random\s*\(", text):
            self.rep.warn(f"{where}:{lineno(text, m.start())}: Math.random() reshuffles the noise on every slider move; use ctx.rng()")

    # ---- sections
    def load_sections(self) -> list[dict]:
        files = sorted((self.proj / "sections").glob("*.html"))
        if not files:
            sys.exit("error: no sections/*.html found")
        out, ids = [], {}
        for n, f in enumerate(files, 1):
            where = f"sections/{f.name}"
            text = f.read_text(encoding="utf-8")
            self.raw[f.name] = text
            m = re.match(r"\s*(?:<!--.*?-->\s*)*<section\b([^>]*)>", text, flags=re.S)
            if not m or not text.rstrip().endswith("</section>"):
                self.rep.error(f"{where}: a section file must be exactly one <section id=... data-nav=...> ... </section>")
                continue
            attrs = dict(re.findall(r'([\w-]+)="([^"]*)"', m.group(1)))
            sid = attrs.get("id")
            if not sid:
                self.rep.error(f"{where}: <section> needs an id")
                continue
            h2 = re.search(r"<h2[^>]*>(.*?)</h2>", text, flags=re.S)
            if not h2:
                self.rep.error(f"{where}: section has no <h2>")
            self.lint(text, where, gap_section=bool(re.search(r"gap|related|prior", " ".join(attrs.get(k, "") for k in ("id", "data-nav", "data-kicker")), re.I)))
            text = self.fill_code(text, where)
            text = self.fill_equations(text, where)
            text = self.fill_data(text, where)
            text = self.inline_images(text, where)
            text = escape_math(text, where, self.rep, self.stats)
            self.collect_chips(text, where)
            for i in re.finditer(r'\sid="([^"]+)"', text):
                if i.group(1) in ids:
                    self.rep.error(f"{where}: duplicate id \"{i.group(1)}\" (also in {ids[i.group(1)]})")
                ids[i.group(1)] = where
            figs = set(re.findall(r'<figure\b[^>]*class="[^"]*\bwidget\b[^"]*"[^>]*\sid="([^"]+)"', text)) | \
                set(re.findall(r'<figure\b[^>]*\sid="([^"]+)"[^>]*class="[^"]*\bwidget\b', text))
            calls = re.findall(r"D3X\.(widget|flow)\(\s*['\"]([^'\"]+)['\"]", text)
            for kind, wid in calls:
                self.stats["widgets" if kind == "widget" else "flows"] += 1
                if wid not in figs:
                    self.rep.error(f"{where}: D3X.{kind}('{wid}') has no <figure class=\"widget\" id=\"{wid}\"> in this section")
            for wid in figs - {w for _, w in calls}:
                self.rep.error(f"{where}: <figure class=\"widget\" id=\"{wid}\"> is never drawn (no D3X.widget/flow call)")
            for fm in re.finditer(r'<figure\b[^>]*class="[^"]*\bwidget\b.*?</figure>', text, flags=re.S):
                if 'class="try"' not in fm.group(0) or 'class="notice"' not in fm.group(0):
                    wid = re.search(r'id="([^"]+)"', fm.group(0))
                    self.rep.warn(f"{where}: widget {wid.group(1) if wid else '?'}: caption lacks <span class=\"try\"> / <span class=\"notice\">; say what to do and what to see")
            self.stats["derivations"] += len(re.findall(r'class="derivation"', text))

            def number(fm: re.Match) -> str:
                fid = re.search(r'\sid="([^"]+)"', fm.group(1))
                self.fig_no += 1
                if fid:
                    self.figures[fid.group(1)] = self.fig_no
                return fm.group(0).replace("{fig}", f"Figure {self.fig_no}")

            text = re.sub(r"<figure\b([^>]*)>.*?</figure>", number, text, flags=re.S)
            kicker = attrs.get("data-kicker", "")
            head = f'<div class="step"><span class="n">{n:02d}</span><span class="lbl">{html.escape(kicker)}</span></div>'
            text = text[:m.end()] + head + text[m.end():]
            out.append({"id": sid, "n": n, "nav": attrs.get("data-nav") or re.sub(r"<[^>]+>", "", h2.group(1) if h2 else sid),
                        "html": text, "words": plain_words(strip_details(text)), "fold_words": plain_words(text), "file": f.name})
        def figref(m: re.Match) -> str:
            if m.group(1) not in self.figures:
                self.rep.error(f"{{fig:{m.group(1)}}} refers to a figure id that does not exist (figures: {', '.join(self.figures) or 'none'})")
                return m.group(0)
            return f'<a href="#{m.group(1)}">Figure {self.figures[m.group(1)]}</a>'

        for sec in out:
            sec["html"] = re.sub(r"\{fig:([\w-]+)\}", figref, sec["html"])
        hrefs = {h for s in out for h in re.findall(r'href="#([^"]+)"', s["html"])}
        for h in sorted(hrefs - set(ids)):
            (self.rep.warn if self.draft else self.rep.error)(f"internal link #{h} does not resolve to any id" + (" (allowed in --draft: the target section may not exist yet)" if self.draft else ""))
        return out

    # ---- assets
    def fonts_css(self) -> str:
        css = []
        for family, weight, style, name in (("Inter", 400, "normal", "Inter-Regular"), ("Inter", 400, "italic", "Inter-Italic"), ("Inter", 600, "normal", "Inter-SemiBold"), ("Inter", 700, "normal", "Inter-Bold"),
                                            ("IBM Plex Mono", 400, "normal", "IBMPlexMono-400-latin"), ("IBM Plex Mono", 500, "normal", "IBMPlexMono-500-latin"), ("IBM Plex Mono", 600, "normal", "IBMPlexMono-600-latin")):
            b64 = base64.b64encode((ENGINE / "fonts" / f"{name}.woff2").read_bytes()).decode()
            css.append(f"@font-face{{font-family:'{family}';font-style:{style};font-weight:{weight};font-display:swap;src:url(data:font/woff2;base64,{b64}) format('woff2')}}")
        return "\n".join(css)

    def katex_css(self) -> str:
        css = (ENGINE / "katex" / "katex.min.css").read_text(encoding="utf-8")
        used = "\n".join(self.stats["math_src"]) + json.dumps(self.cfg.get("macros", {}))

        def face(m: re.Match) -> str:
            block = m.group(0)
            fm = re.search(r"url\((fonts/(KaTeX_([A-Za-z0-9]+)-[A-Za-z]+)\.woff2)\)", block)
            if not fm:
                return ""
            family = fm.group(3)
            if family in OPTIONAL_KATEX_FONTS and not re.search(OPTIONAL_KATEX_FONTS[family], used):
                return ""
            b64 = base64.b64encode((ENGINE / "katex" / fm.group(1)).read_bytes()).decode()
            return re.sub(r"src:[^}]*", f"src:url(data:font/woff2;base64,{b64}) format('woff2')", block)

        return re.sub(r"@font-face\{[^}]*\}", face, css)

    def roles(self) -> list[dict]:
        """[[role]] entries: the project's colour code, kept in every equation and figure."""
        out = []
        for r in self.cfg.get("role", []):
            key, col = str(r.get("key", "")), str(r.get("color", ""))
            if not re.fullmatch(r"[A-Za-z]{2,20}", key) or not re.fullmatch(r"#[0-9A-Fa-f]{6}", col):
                self.rep.error(f"explainer.toml [[role]]: key must be 2 to 20 letters and color a #RRGGBB value (got key={key!r}, color={col!r})")
                continue
            out.append({"key": key, "color": col, "label": str(r.get("label", key))})
        return out

    def page(self, sections: list[dict]) -> str:
        cfg = self.cfg
        title = cfg.get("title", "Project explainer")
        macros = read_macros(self.repo, cfg.get("macros_from", []), self.rep)
        roles = self.roles()
        for r in roles:                                # \choice{b} colours b in the role's colour, in any formula
            if "\\" + r["key"] in macros:
                self.rep.warn(f"[[role]] key '{r['key']}' hides the paper macro \\{r['key']}; pick another key")
            macros["\\" + r["key"]] = "\\textcolor{%s}{#1}" % r["color"].lstrip("#")      # no '#': inside a macro body "#2A..." would read as argument 2
        macros.update(cfg.get("macros", {}))
        self.stats["math_src"].append(json.dumps(macros))
        js = lambda p: (ENGINE / p).read_text(encoding="utf-8").replace("</script", "<\\/script")
        words = sum(s["words"] for s in sections)
        minutes = round(words / 220 + 1.5 * (self.stats["widgets"] + self.stats["flows"]))
        today = dt.date.today().isoformat()
        built = f"built {today}" + (f" from {html.escape(self.repo.name)} @ {self.commit}{' + uncommitted changes' if self.dirty else ''}" if self.commit else "")
        authors = ", ".join(cfg.get("authors", []))
        hero = cfg.get("hero", {})
        key = "".join(f'<span style="color:{r["color"]}"><i></i><span class="lab">{html.escape(r["label"])}</span></span>' for r in roles)
        hero_eq = ""
        if hero.get("equation") or hero.get("tex"):
            tex = hero.get("tex") or self.paper.equation(hero["equation"])
            if tex is None:
                self.rep.error(f"explainer.toml [hero] equation = \"{hero['equation']}\": no equation with that \\label in the paper sources")
            else:
                tex = re.sub(r"\\tag\{[^}]*\}", "", tex)
                self.stats["math_src"].append(tex)
                esc = tex.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
                hero_eq = f'<div class="hero-eq">$${esc}$$' + (f'<div class="key">{key}</div>' if key else "") + "</div>"
        elif key:
            hero_eq = f'<div class="key">{key}</div>'
        hero_note = f"<small>{hero['note']}</small>" if hero.get("note") else ""
        hud = cfg.get("hud", {})
        hud_html = ""
        if hud.get("lines"):
            for ln in hud["lines"]:
                self.stats["math_src"].append(str(ln))
            lines_html = "".join(f'<div class="line" data-hud="{i}">{ln}</div>' for i, ln in enumerate(hud["lines"], 1))
            hud_html = f'<aside id="hud" aria-hidden="true"><div class="t">{html.escape(hud.get("title", "the idea, assembling"))}</div>{lines_html}<div class="f">{html.escape(hud.get("foot", "Each piece is introduced in one step. Scroll to build it."))}</div></aside>'
            levels = {int(x) for sec in sections for x in re.findall(r'<section\b[^>]*data-hud="(\d+)"', sec["html"])}
            if not levels:
                self.rep.warn("[hud] is defined but no section carries data-hud=\"k\": the panel never lights up")
            elif max(levels) > len(hud["lines"]):
                self.rep.warn(f"a section has data-hud=\"{max(levels)}\" but [hud] has only {len(hud['lines'])} lines")
        toc = "".join(f'<li><span class="n">{s["n"]:02d}</span><a href="#{s["id"]}">{html.escape(s["nav"])}</a></li>' for s in sections)
        meta = " · ".join(x for x in [html.escape(authors), built, f"about {minutes} min", html.escape(cfg.get("status", ""))] if x)
        role_css = ":root{" + "".join(f"--r-{r['key']}:{r['color']};" for r in roles) + "}" + "".join(f".r-{r['key']}{{color:{r['color']}}}" for r in roles)
        boot = "window.D3X_MACROS=%s;window.D3X_CHIPS=%s;window.D3X_ROLES=%s;window.D3X_META=%s;" % tuple(
            json.dumps(x, ensure_ascii=False).replace("</", "<\\/") for x in (
                macros, self.chips, {r["key"]: r["color"] for r in roles}, {"title": title, "commit": self.commit, "built": today, "sections": [s["id"] for s in sections]}))
        self.stats["math_src"].append(json.dumps(macros))
        return f"""<!doctype html>
<html lang="{cfg.get('lang', 'en')}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="generator" content="d3-explainer">
<title>{html.escape(re.sub(r"<[^>]+>", "", title))}</title>
<style>
{self.fonts_css()}
{self.katex_css()}
{(ENGINE / 'explainer.css').read_text(encoding='utf-8')}
{role_css}
{cfg.get('css', {}).get('extra', '')}
</style>
<script>{js('katex/katex.min.js')}</script>
<script>{js('katex/auto-render.min.js')}</script>
<script>{boot}</script>
<script>{js('explainer.js')}</script>
</head>
<body>
<div id="bar"></div>
{hud_html}
<header class="hero">
  <div class="wrap">
    <p class="eyebrow">{html.escape(cfg.get('eyebrow', 'project explainer · for the authors'))}</p>
    <h1>{cfg.get('title_html') or html.escape(title)}</h1>
    <p class="lede">{cfg.get('subtitle', '')}</p>
    {hero_eq}
    {hero_note}
  </div>
</header>
<main>
<div class="wrap"><nav class="toc"><div class="t">contents</div><ol>{toc}</ol><div class="meta">{meta}</div></nav></div>
{chr(10).join(s['html'] for s in sections)}
</main>
<footer><div class="wrap">
  {built}. Source pointers were checked against the repository at build time; a pointer with a red outline did not resolve.<br>
  Figures marked <span class="toy">illustrative toy</span> run a small model in your browser and are not experiments from the repository.
</div></footer>
<button id="notation-btn" class="btn ghost" type="button">notation (n)</button>
<aside id="drawer"><div class="dh"><span>Notation</span><button class="btn ghost" type="button">close</button></div><div class="db"></div></aside>
</body>
</html>
"""

    def write_packets(self, sections: list[dict]) -> None:
        """Two compact files for the reviewers, so that they read evidence instead of roaming the repository."""
        review = self.proj / "review"
        review.mkdir(exist_ok=True)
        title = self.cfg.get("title", "")
        fid = [f"# Fidelity packet: {title}", "",
               f"Built from {self.repo.name} @ {self.commit or 'no git'}. Line numbers (L12) refer to the section file named in each heading.",
               "Lines marked PULLED were copied from the paper or the code by the build and cannot deviate from the source; verify the hand-written text and math around them.",
               "Chips [[kind:target]] exist (the build checked). Whether the cited source says what the sentence claims is for you to judge, with the evidence at the end of this file.", ""]
        figs = [f"# Figures packet: {title}", "", "One block per interactive figure: caption, then the script that draws it. The knob-to-insight sentence of each figure is in brief.md.",
                "Built into every figure by the runtime, so not visible in these scripts and not a finding when absent from them: a Reset button, the legend (from the label of each series), "
                "a hover crosshair with a value tooltip on every line plot, hover titles on dots and bars, keyboard-accessible controls, and the 'illustrative toy' badge for toy: true.", ""]
        for sec in sections:
            raw = self.raw[sec["file"]]
            fid += [f"## {sec['n']:02d} {sec['nav']}   (sections/{sec['file']})", ""]
            in_script = False
            for i, line in enumerate(raw.splitlines(), 1):
                if in_script:
                    in_script = "</script>" not in line
                    continue
                if re.search(r"<script\b", line) and "</script>" not in line:
                    in_script = True
                    continue
                t = re.sub(r"<script\b.*?</script>", " ", line)
                t = re.sub(r'<div[^>]*class="derivation"[^>]*data-title="([^"]*)"[^>]*>', r"DERIVATION: \1 ", t)
                t = re.sub(r'<div[^>]*class="dstep"[^>]*data-why="([^"]*)"[^>]*>', r"STEP. Reason given: \1 || ", t)
                t = re.sub(r'<div[^>]*data-label="([^"]+)"[^>]*>\s*</div>',
                           lambda m: f"EQUATION PULLED from the paper, \\label{{{m.group(1)}}}: $$ " + re.sub(r"\s+", " ", self.paper.equation(m.group(1)) or "?") + " $$", t)
                t = re.sub(r'<pre[^>]*data-src="([^"]+)"[^>]*data-lines="([^"]*)"[^>]*>', r"CODE EXCERPT PULLED from \1:\2 ", t)
                t = re.sub(r'<figure[^>]*class="[^"]*widget[^"]*"[^>]*id="([^"]+)"[^>]*>', r"FIGURE \1 (script in figures-packet.md) ", t)
                t = re.sub(r"<summary[^>]*>", "FOLDED BLOCK: ", t)
                t = re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", t))).strip().replace("{fig}", "Figure")
                if t:
                    fid.append(f"L{i}: {t}")
            for fm in re.finditer(r"D3X\.flow\(\s*['\"]([^'\"]+)['\"](.*?)</script>", raw, flags=re.S):      # claims inside flow boxes are prose too
                for nm in re.finditer(r"label:\s*(['\"])(.*?)\1.*?detail:\s*(['\"])(.*?)(?<!\\)\3", fm.group(2), flags=re.S):
                    text = re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", nm.group(4).replace("\\\\", "\\")))).strip()
                    fid.append(f"L{lineno(raw, fm.start(2) + nm.start())}: FLOW BOX \"{nm.group(2)}\" in {fm.group(1)}: {text}")
            fid.append("")
            scripts = [(m.start(), m.group(1)) for m in re.finditer(r"<script(?![^>]*application/json)[^>]*>(.*?)</script>", raw, flags=re.S) if m.group(1).strip()]
            shared = [code for _, code in scripts if not re.search(r"D3X\.(widget|flow)\(", code)]
            for fm in re.finditer(r'<figure\b[^>]*class="[^"]*\bwidget\b[^"]*"[^>]*>.*?</figure>', raw, flags=re.S):
                wid = re.search(r'\sid="([^"]+)"', fm.group(0))
                if not wid:
                    continue
                cap = re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", re.sub(r'<span class="try">', " TRY: ", re.sub(r'<span class="notice">', " NOTICE: ", fm.group(0)))))).strip()
                figs += [f"## {wid.group(1)}   (Figure {self.figures.get(wid.group(1), '?')}, sections/{sec['file']}:{lineno(raw, fm.start())})", "", f"Caption: {cap}", ""]
                for pos, code in scripts:
                    if re.search(r"D3X\.(widget|flow)\(\s*['\"]%s['\"]" % re.escape(wid.group(1)), code):
                        figs += [f"Script (sections/{sec['file']}:{lineno(raw, pos)}):", "```js", code.strip("\n"), "```", ""]
            for code in shared:
                figs += [f"## shared constants or helpers in sections/{sec['file']}", "```js", code.strip("\n"), "```", ""]
        fid += ["## Evidence for the chips", ""]
        shown: dict[str, str] = {}
        for key, info in self.chips.items():
            if key in self.evidence and info.get("ok", True):
                target = key.split("|")[0]
                if self.evidence[key] in shown.values():                 # same evidence under another label or line hint: point to it once
                    continue
                shown[target] = self.evidence[key]
                fid += [f"### [[{target}]]", "```", self.evidence[key].rstrip(), "```", ""]
        files = sorted({k.split(":", 1)[1].split("|")[0].split(":")[0].split(" ")[0] for k in self.chips if k.startswith(("code:", "result:", "file:"))})
        tex = sorted(str(f.relative_to(self.repo)) for f in self.paper.texts)
        fid += ["## Source files cited (open one only when the evidence above does not settle a claim)", ""] + [f"- {self.repo / x}" for x in tex[:12] + files]
        (review / "fidelity-packet.md").write_text("\n".join(fid) + "\n", encoding="utf-8")
        (review / "figures-packet.md").write_text("\n".join(figs) + "\n", encoding="utf-8")

    def run(self) -> int:
        sections = self.load_sections()
        rep = self.rep
        name = self.cfg.get("name", "explainer")
        out = self.proj / "dist" / f"{name}.html"
        if not rep.errors:
            page = self.page(sections)
            out.parent.mkdir(exist_ok=True)
            out.write_text(page, encoding="utf-8")
            self.write_packets(sections)
        depth = self.cfg.get("depth", "standard")
        words = sum(s["words"] for s in sections)
        folded = sum(s["fold_words"] for s in sections) - words
        nw = self.stats["widgets"]            # flow diagrams are structure, not knobs: they do not count against the figure budget
        bw, bn = BUDGET.get(depth, BUDGET["standard"])
        if words > bw * 1.15:
            rep.warn(f"over budget for depth={depth}: {words:,} main-line words (budget {bw:,}). Fold detail into <details class=\"deep\"> or cut")
        if nw > bn:
            rep.warn(f"over budget for depth={depth}: {nw} interactive figures (budget {bn}). Keep the ones whose Notice line states a real insight")
        if not any('id="notation"' in s["html"] or "data-notation" in s["html"] for s in sections):
            rep.warn("no notation table (id=\"notation\"): the Notation drawer stays empty")
        bad = [k for k, v in self.chips.items() if not v.get("ok", True)]
        for w in rep.warnings:
            print(f"  warning  {w}")
        for e in rep.errors:
            print(f"  ERROR    {e}")
        print("\n  section                          words  (+folded)")
        for s in sections:
            print(f"  {s['n']:02d} {s['nav'][:28]:<28} {s['words']:>6}  {s['fold_words'] - s['words']:>8}")
        print(f"\n  depth={depth}: budget {bw:,} main-line words (warns above {int(bw * 1.15):,}) and {bn} interactive figures")
        print(f"  {len(sections)} sections · {words:,} words (+{folded:,} folded) · {nw} interactive figures + {self.stats['flows']} flows · {self.stats['derivations']} derivations · "
              f"{self.stats['display']} display equations ({self.stats['pulled']} pulled from the paper) · {len(self.chips)} source chips unique ({len(bad)} unresolved) · {self.stats['code']} code excerpts")
        if rep.errors:
            print(f"\n  BUILD FAILED: {len(rep.errors)} error(s), {len(rep.warnings)} warning(s). Nothing written.")
            return 1
        print(f"  {out.stat().st_size / 1e6:.2f} MB -> {out.relative_to(self.proj)}   ({len(rep.warnings)} warning(s))   reviewer packets -> review/")
        return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("project", nargs="?", default=None, help="explainer folder (default: the folder that contains d3x/)")
    ap.add_argument("--draft", action="store_true", help="allow TODO markers")
    a = ap.parse_args()
    proj = Path(a.project).resolve() if a.project else ENGINE.parent
    return Builder(proj, a.draft).run()


if __name__ == "__main__":
    sys.exit(main())
