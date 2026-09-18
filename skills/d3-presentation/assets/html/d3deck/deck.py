# -*- coding: utf-8 -*-
"""Deck state, slide functions and the build (the module is named deck so that the
exported build() function does not shadow it on the package).

Slides are appended in call order, like frames in a .tex file. build() renders
every slide inside the D3 frame, resolves jump marks, embeds the Inter fonts and
writes one self-contained HTML file.
"""
import base64
import html as _html
import json
import os
import re
import warnings

from . import chrome, components, engine, nav, paths, presenter

STRUCTURAL = ('title', 'agenda', 'section', 'thankyou')
NUMBERED_KINDS = ('content', 'agenda', 'section', 'backuphome')
FACES = (('Inter_18pt-Regular.ttf', 400, 'normal'), ('Inter_18pt-Italic.ttf', 400, 'italic'),
         ('Inter_18pt-SemiBold.ttf', 600, 'normal'), ('Inter_18pt-Bold.ttf', 700, 'normal'),
         ('Inter_18pt-BoldItalic.ttf', 700, 'italic'))
DEFAULT_CHAIR = 'Chair of Information Systems and Business Analytics'


class Slide:
    def __init__(self, kind, title, inner, steps=1, notes='', src='', cls='', group=None, num=True, sec=None):
        if steps < 1:
            raise ValueError('steps must be >= 1')
        self.kind, self.title, self.inner = kind, title, inner
        self.steps, self.notes, self.src, self.cls = steps, notes, src, cls
        self.group, self.num, self.sec = group, num, sec


class Deck:
    def __init__(self):
        self.reset()

    def reset(self):
        self.meta = None
        self.slides = []
        self.marks = {}            # mark name -> slide index
        self.pending = []          # mark names waiting for the next slide
        self.extra_css = []
        self.cur_sec = None        # 0-based index of the current section
        self.backup_at = None      # index of the first backup slide
        self.hub_at = None         # index of the backuphome slide
        self.section_slides = {}   # 0-based section index -> divider slide index


D = Deck()


def _strip(s):
    return re.sub(r'<[^>]+>', '', s)


def meta(title, subtitle='', date='', presenter='', chair=DEFAULT_CHAIR, sections=(),
         tracker=False, numbering='all', lang='en', reveal='ghost', look='klar', math=None, macros=None):
    """Deck metadata; call once before the first slide. Resets the deck. date is stored for the
    manifest only, like \\date in LaTeX; put it into the subtitle if it should appear.
    look='klar' (default): calm content slides: section tracker on top, kicker and one-claim title, mono foot with the
    D3 logo, takeaway on a fixed baseline. look='beamer': the frame of the LaTeX template (uni logo, bar, footer tab).
    reveal='ghost' (default): later steps stand as pale grey ghosts, so nothing is ever removed and nothing moves.
    reveal='hide': later steps are invisible until their step (they keep their place).
    math=None (default): MathJax is embedded when a slide contains $...$, \\(...\\), $$...$$ or \\[...\\]; True / False force it.
    macros: LaTeX macros for the formulas, e.g. {'E': r'\\mathbb{E}', 'norm': r'\\lVert #1 \\rVert'}."""
    if look not in ('klar', 'beamer'):
        raise ValueError("look must be 'klar' or 'beamer'")
    if reveal not in ('hide', 'ghost'):
        raise ValueError("reveal must be 'hide' or 'ghost'")
    if numbering not in ('all', 'content'):
        raise ValueError("numbering must be 'all' or 'content'")
    sections = list(sections)
    if len(sections) > 7:
        warnings.warn(f'{len(sections)} sections; agenda and tracker are designed for at most 7')
    D.reset()
    D.meta = dict(title=title, subtitle=subtitle, date=date, presenter=presenter, chair=chair,
                  sections=sections, tracker=bool(tracker), numbering=numbering, lang=lang, reveal=reveal, look=look,
                  math=math, macros=dict(macros or {}))
    return D.meta


def _need_meta():
    if D.meta is None:
        raise RuntimeError('call meta(...) before adding slides')


def _add(kind, title, inner, steps=1, notes='', src='', cls='', group=None, num=True):
    _need_meta()
    in_backup = D.backup_at is not None
    if group is None:
        if in_backup:
            group = 'Backup'
        elif D.cur_sec is not None:
            group = D.meta['sections'][D.cur_sec]
        else:
            group = 'Start'
    s = Slide(kind, title, inner, steps, notes, src, cls, group, num, None if in_backup else D.cur_sec)
    idx = len(D.slides)
    D.slides.append(s)
    for name in D.pending:
        D.marks[name] = idx
    D.pending = []
    return idx


# ── slide functions (twins of the LaTeX macros) ──────────────────────────

def titleslide(**kw):
    _need_meta()
    m = D.meta
    return _add('title', _strip(m['title']), chrome.title_inner(m['title'], m['subtitle']), **kw)


def _links():
    return {i + 1: f'sec-{i + 1}' for i in D.section_slides}


def agenda(**kw):
    _need_meta()

    def inner():
        return '<div class="fr-title">Agenda</div>' + chrome.agenda_list(D.meta['sections'], None, _links())
    return _add('agenda', 'Agenda', inner, **kw)


def K(kick, claim, sub=''):
    """Slide title as kicker and claim: K('Method', 'A cutoff rule needs only one number').
    The kicker names the category in one or two words; the claim is a full sentence of at most 15 words."""
    sub = f'<span class="sub">{sub}</span>' if sub else ''
    return f'<span class="kick">{kick}</span>{claim}{sub}'


def section(n, question='', **kw):
    """Section divider n (1-based); also makes n the current section.
    question: the question this part answers; in the 'klar' look the divider shows it instead of an agenda list."""
    _need_meta()
    secs = D.meta['sections']
    if not 1 <= n <= len(secs):
        raise ValueError(f'section({n}): meta() defines {len(secs)} section(s)')
    if D.backup_at is not None:
        raise ValueError('section() after appendix(): backup slides carry no section')
    D.cur_sec = n - 1
    mark(f'sec-{n}')

    def inner():
        if D.meta.get('look') == 'klar':
            return (f'<div class="secq"><div class="pt">Part {n} of {len(secs)} · {secs[n - 1]}</div>'
                    f'<div class="stmt">{question or secs[n - 1]}</div></div>')
        return chrome.agenda_list(secs, n, _links())
    idx = _add('section', secs[n - 1], inner, **kw)
    D.section_slides[n - 1] = idx
    return idx


def onecol(title, body, **kw):
    return _add('content', title, f'<div class="body">{body}</div>', **kw)


def twocol(title, left, right, **kw):
    return _add('content', title, f'<div class="col l">{left}</div><div class="col r">{right}</div>', **kw)


def twocoltakeaway(title, left, right, takeaway, **kw):
    inner = (f'<div class="col l short">{left}</div><div class="col r short">{right}</div>'
             f'<div class="fr-take">{components.takeaway(takeaway)}</div>')
    return _add('content', title, inner, **kw)


def statement(text, title='', **kw):
    """One sentence, large, alone on the slide. Mark the one word that carries it with <b>; use it a few times per talk."""
    top = '250px' if title else '230px'
    return _add('content', title, f'<div class="body" style="top:{top}"><div class="stmt">{text}</div></div>', **kw)


def facts(title, items, takeaway='', **kw):
    """Two to four headline numbers side by side. items: (value, label) or (value, label, True) for the one accented number."""
    if not 1 <= len(items) <= 4:
        raise ValueError('facts(): one to four numbers; more than four is a table')
    inner = f'<div class="body">{components.facts(items)}</div>'
    if takeaway:
        inner += f'<div class="fr-take">{components.takeaway(takeaway)}</div>'
    return _add('content', title, inner, **kw)


def slide(title, body, **kw):
    """A content slide with the frame but no body box; position your own elements."""
    return _add('content', title, body, **kw)


def thankyou(**kw):
    _need_meta()
    return _add('thankyou', 'Thank You!', chrome.thankyou_inner(D.meta['presenter']), **kw)


def appendix():
    """Everything after this call is backup."""
    _need_meta()
    if D.backup_at is not None:
        raise ValueError('appendix() called twice')
    D.backup_at = len(D.slides)
    D.cur_sec = None


def backuphome(title='Backup', **kw):
    """Hub slide listing every later backup slide by group; the H key jumps here."""
    if D.backup_at is None:
        raise ValueError('backuphome() needs appendix() first')
    mark('bhome')

    def inner():
        groups = {}
        for i in range(D.hub_at + 1, len(D.slides)):
            groups.setdefault(D.slides[i].group, []).append(i)
        cols = []
        for g, idxs in groups.items():
            rows = ''.join(f'<div class="hi" data-jump="{i}"><span class="hn">B{i - D.backup_at}</span>'
                           f'<span>{_strip(D.slides[i].title)}</span></div>' for i in idxs)
            cols.append(f'<div><h4>{g}</h4>{rows}</div>')
        return f'<div class="body"><div class="hub">{"".join(cols)}</div></div>'
    idx = _add('backuphome', title, inner, **kw)
    D.hub_at = idx
    return idx


# ── marks, links, css ────────────────────────────────────────────────────

def mark(name):
    """Name the next slide so jump()/link()/crumb() can target it."""
    if not re.fullmatch(r'[\w-]+', name):
        raise ValueError(f'mark name {name!r}: use letters, digits, _ and -')
    if name in D.marks or name in D.pending:
        raise ValueError(f'duplicate mark {name!r}')
    D.pending.append(name)


def jump(name):
    return f'data-jump="@@{name}@@"'


def link(name, text):
    return f'<span class="jl" {jump(name)}>{text}</span>'


def css(text):
    """Append a stylesheet fragment; scope it with a class you also pass as cls=."""
    D.extra_css.append(text)


# ── numbering ────────────────────────────────────────────────────────────

def page_labels(slides, mode, backup_at):
    """-> [(page tab label, shell foot label)] per slide. See spec 8.3."""
    main = slides[:backup_at] if backup_at is not None else slides
    backup = slides[backup_at:] if backup_at is not None else []
    labels = []
    if mode == 'all':
        total = sum(1 for s in slides if s.num)
        n = 0
        for i, s in enumerate(slides):
            if s.num:
                n += 1
            tab = f'{n}/{total}' if (s.num and s.kind in NUMBERED_KINDS) else ''
            if backup_at is not None and i >= backup_at:
                foot = (f'backup {i - backup_at + 1} of {len(backup)}' if s.num
                        else f'backup &mdash; of {len(backup)}')
            else:
                foot = f'{n} / {total}' if s.num else f'&mdash; / {total}'
            labels.append((tab, foot))
        return labels

    def part(part_slides, is_backup):
        total = sum(1 for s in part_slides if s.num and s.kind not in STRUCTURAL)
        n = 0
        for s in part_slides:
            counted = s.num and s.kind not in STRUCTURAL
            if counted:
                n += 1
            tab = f'{n}/{total}' if counted else ''
            if is_backup:
                foot = f'backup {n} of {total}' if counted else f'backup &mdash; of {total}'
            else:
                foot = f'{n} / {total}' if counted else f'&mdash; / {total}'
            labels.append((tab, foot))
    part(main, False)
    part(backup, True)
    return labels


# ── fonts ────────────────────────────────────────────────────────────────

def fonts_css(font_dir=None):
    font_dir = font_dir or paths.asset_dir('fonts')
    out = []
    for f, w, s in FACES:
        p = os.path.join(font_dir, f)
        if not os.path.exists(p):
            raise FileNotFoundError(f'{p} missing; run init.py to copy the Inter fonts into d3deck/fonts/')
        with open(p, 'rb') as fh:
            b = base64.b64encode(fh.read()).decode()
        out.append(f"@font-face{{font-family:'Inter';font-weight:{w};font-style:{s};font-display:block;"
                   f"src:url(data:font/ttf;base64,{b}) format('truetype')}}")
    return '\n'.join(out)


# ── math ─────────────────────────────────────────────────────────────────
# MathJax 3 tex-svg-full: one script, glyphs as SVG paths, so the deck stays a single offline file. It is embedded
# only when a slide holds math (about 2.2 MB). A lone '$' (a price, a shell prompt) is not math; two of them on one
# slide can pair up: write the literal one as <span class="nomath">$</span>. fontCache 'none' keeps the SVG free of ids,
# because the presenter view clones slides and strips ids.

MATH = re.compile(r'\$\$.+?\$\$|\\\[.+?\\\]|\\\(.+?\\\)|(?<![\\$\w])\$(?![\s$])[^$\n]{1,400}?(?<![\s\\])\$(?![\d\w])', re.S)
NO_MATH = re.compile(r'<(pre|code|script|style)\b.*?</\1>|<[^>]+>', re.S | re.I)
MATH_BOOT = '''window.D3_MATH_READY=false;
window.MathJax={tex:{inlineMath:[['$','$'],['\\\\(','\\\\)']],displayMath:[['$$','$$'],['\\\\[','\\\\]']],macros:__MACROS__,
  packages:{'[-]':['noundefined']}},   /* an unknown command fails its formula, so shoot.py can name it */
 svg:{fontCache:'none'},options:{ignoreHtmlClass:'nomath'},
 startup:{typeset:false,ready:function(){MathJax.startup.defaultReady();
  /* hidden slides are display:none and cannot be measured: lay all of them out (invisibly) while typesetting */
  document.body.classList.add('mjx-measure');
  try{MathJax.typeset()}catch(e){console.error('d3deck math: '+e.message)}
  document.body.classList.remove('mjx-measure');window.D3_MATH_READY=true;}}};'''
MATH_CSS = ('body.mjx-measure .sl{display:block!important;visibility:hidden}'
            'mjx-container[display="true"]{margin:.5em 0!important}')


def has_math(text):
    return bool(MATH.search(NO_MATH.sub(' ', text)))


def mathjax_macros(macros):
    """{'E': r'\\mathbb{E}', r'\\norm': r'\\lVert #1 \\rVert'} -> MathJax's macro table ([body, n] when the body uses #1..#n)."""
    out = {}
    for k, v in macros.items():
        name = k.lstrip('\\')
        if not re.fullmatch(r'[A-Za-z]+', name):
            raise ValueError(f'macro name {k!r}: letters only')
        if isinstance(v, (list, tuple)):
            out[name] = list(v)
            continue
        n = max([int(d) for d in re.findall(r'(?<!#)#(\d)', v)] or [0])
        out[name] = [v, n] if n else v
    return out


def math_head(body):
    """(css, script tags) for MathJax, or ('', '') for a deck without math."""
    want = D.meta.get('math')
    if want is False or (want is None and not has_math(body)):
        return '', ''
    p = os.path.join(paths.PKG, 'mathjax', 'tex-svg-full.js')
    if not os.path.exists(p):
        raise FileNotFoundError(f'{p} missing; refresh d3deck/ from the skill (init.py) to get MathJax')
    with open(p, encoding='utf-8') as fh:
        js = fh.read().replace('</script', '<\\/script')
    boot = MATH_BOOT.replace('__MACROS__', json.dumps(mathjax_macros(D.meta.get('macros', {}))).replace('</', '<\\/'))
    return MATH_CSS, f'<script>{boot}</script>\n<script>{js}</script>\n'


# ── rendering ────────────────────────────────────────────────────────────

def _calm(i, s, inner):
    """Warn about what makes a slide look busy. One idea, one visual, few builds."""
    name = f'slide {i + 1} ({_strip(s.title)[:40]!r})'
    text = _strip(MATH.sub(' formula ', re.sub(r'<(pre|svg|style)\b.*?</\1>', ' ', inner, flags=re.S)))   # a formula reads as one word, not as its TeX tokens
    words, bullets = len(text.split()), inner.count('<li')
    kinds = [k for k, pat in (('figure', r'<img|class="fig'), ('stat cards', r'class="(stat|bignum)'), ('chevrons', r'class="chev'),
                              ('timeline', r'class="tl\b|class="tl"'), ('code box', r'<pre'), ('table', r'<table')) if re.search(pat, inner)]
    if s.steps > 4:
        warnings.warn(f'{name}: {s.steps} steps. More than 4 builds on one slide reads as fidgeting; split the slide or reveal clusters')
    if s.steps > 1 and bullets and s.steps >= bullets >= 3:
        warnings.warn(f'{name}: one step per bullet. Reveal a cluster, a column or a region, or show the list at once')
    if words > 75:
        warnings.warn(f'{name}: {words} words in the body. Over about 60 the audience reads instead of listening; cut, or move detail to the backup')
    if bullets > 6:
        warnings.warn(f'{name}: {bullets} bullets; keep to 3 to 5, or split the slide')
    if len(kinds) > 2:
        warnings.warn(f'{name}: {", ".join(kinds)} on one slide. One visual idea per slide; give each its own slide')


def render_slides():
    """-> (section html list, manifest list, jump tab html, hub index or -1)."""
    m = D.meta
    labels = page_labels(D.slides, m['numbering'], D.backup_at)
    secs, manifest = [], []
    for i, s in enumerate(D.slides):
        tab, foot = labels[i]
        inner = s.inner() if callable(s.inner) else s.inner
        if 'display:none' in inner.replace(' ', ''):
            warnings.warn(f'slide {i + 1} ({_strip(s.title)[:40]!r}) uses display:none; ghost it with data-s instead')
        if s.kind == 'content' and not (D.backup_at is not None and i >= D.backup_at):
            _calm(i, s, inner)
        dots = ('<div class="stepdots">' + '<i></i>' * s.steps + '</div>') if s.steps > 1 else ''
        in_backup = D.backup_at is not None and i >= D.backup_at
        if s.kind in ('title', 'thankyou'):
            body = chrome.title_frame(inner)
        else:
            trk = ''
            title = s.title if s.kind in ('content', 'backuphome') else ''
            if m.get('look') == 'klar':
                if s.sec is not None and not in_backup and m['sections']:
                    trk = chrome.tracker(m['sections'], s.sec)
                foot_text = 'Backup' if in_backup else (m['sections'][s.sec] if s.sec is not None and m['sections'] else m['presenter'])
                body = chrome.klar_frame(title, inner, foot or tab, foot_text, trk, dots)
            else:
                foot_text = f"{m['chair']} | {m['presenter']}"
                if m['tracker'] and s.kind == 'content' and not in_backup and s.sec is not None:
                    trk = chrome.tracker(m['sections'], s.sec)
                    foot_text = ''
                body = chrome.content_frame(title, inner, tab, foot_text, trk, dots)
        cls = f'sl k-{s.kind}' + (f' {s.cls}' if s.cls else '')
        secs.append(f'<section class="{cls}" data-steps="{s.steps}" data-i="{i}">{body}</section>')
        manifest.append(dict(i=i, k=s.kind, t=_strip(s.title), g=s.group, s=s.src, n=s.notes,
                             st=s.steps, f=foot, l=tab, sec=s.sec))
    tabs = ''.join(f'<button class="jt" data-go="{D.section_slides[k]}">{m["sections"][k]}</button>'
                   for k in sorted(D.section_slides))
    hub = -1
    if D.backup_at is not None:
        hub = D.hub_at if D.hub_at is not None else D.backup_at
        tabs += f'<button class="jt" data-go="{hub}">Backup</button>'
    return secs, manifest, tabs, hub


def resolve_marks(text):
    def rep(mo):
        name = mo.group(1)
        if name not in D.marks:
            hint = ' (crumb() and link("bhome") need backuphome())' if name == 'bhome' else ''
            raise ValueError(f'unresolved jump mark {name!r}{hint}')
        return str(D.marks[name])
    return re.sub(r'@@([\w-]+)@@', rep, text)


HINTS = ('<kbd>&rarr;</kbd> step &nbsp;<kbd>&darr;</kbd> slide &nbsp;<kbd>F</kbd> present &nbsp;'
         '<kbd>P</kbd> print &nbsp;<kbd>/</kbd> search &nbsp;<kbd>N</kbd> notes &nbsp;&nbsp;')


def build(name, out=None, embed_fonts=True, notes=True):
    """Write dist/<name>.html (or out) and return its path. notes=False strips speaker notes from the file."""
    _need_meta()
    if not D.slides:
        raise ValueError('no slides')
    if D.pending:
        raise ValueError(f'mark() without a following slide: {D.pending}')
    m = D.meta
    secs, manifest, tabs, hub = render_slides()
    if not notes:
        for m_ in manifest:
            m_['n'] = ''
    body = resolve_marks(''.join(secs))
    meta_json = json.dumps(manifest, ensure_ascii=False).replace('<', '\\u003c')
    fonts = fonts_css() if embed_fonts else ''
    extra = '\n'.join(D.extra_css)
    math_css, math_js = math_head(body)
    doc = f'''<!doctype html><html lang="{m['lang']}"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{_html.escape(_strip(m['title']))}</title>
<style>{fonts}</style>
<style>{engine.CSS}</style>
<style>{chrome.CSS}</style>
<style>{components.CSS}</style>
<style>{nav.CSS}</style>
<style>{presenter.CSS}</style>
<style>{math_css}</style>
<style>{extra}</style>
</head><body class="{'reveal-ghost' if m.get('reveal') == 'ghost' else 'reveal-hide'} look-{m.get('look', 'klar')}">
<div id="bar"></div>
<button id="play" title="Present fullscreen (F)">&#9654; Present</button>
<div id="pexit"><kbd>Esc</kbd> exit &nbsp; <kbd>&rarr;</kbd> step &nbsp; <kbd>&darr;</kbd> slide</div>
<div id="top"><span class="lb">Jump</span>{tabs}</div>
<div id="stage">{body}</div>
<div id="foot"><span id="fl"></span><span>{HINTS}<b id="fr"></b></span></div>
{math_js}<script>{engine.JS.replace('__META__', meta_json)}</script>
<script>{nav.JS.replace('__HUB__', str(hub))}</script>
<script>{presenter.JS}</script>
</body></html>'''
    if out is None:
        out = os.path.join(paths.talk_dir(), 'dist', f'{name}.html')
    os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
    with open(out, 'w', encoding='utf-8') as fh:
        fh.write(doc)
    total_steps = sum(s.steps for s in D.slides)
    content = [x for x in D.slides if x.kind == 'content']
    built = [x for x in content if x.steps > 1]
    if len(content) >= 6 and len(built) > 0.4 * len(content):
        warnings.warn(f'{len(built)} of {len(content)} content slides use step builds. Builds are for the few slides whose argument needs sequencing; a deck where most slides build feels restless')
    print(f'{len(D.slides)} slides · {total_steps} steps · {len(doc) / 1e6:.2f} MB' + (' (MathJax embedded)' if math_js else '') + f' → {out}')
    return out
