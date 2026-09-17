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
         tracker=False, numbering='all', lang='en'):
    """Deck metadata; call once before the first slide. Resets the deck. date is stored for the
    manifest only, like \\date in LaTeX; put it into the subtitle if it should appear."""
    if numbering not in ('all', 'content'):
        raise ValueError("numbering must be 'all' or 'content'")
    sections = list(sections)
    if len(sections) > 7:
        warnings.warn(f'{len(sections)} sections; agenda and tracker are designed for at most 7')
    D.reset()
    D.meta = dict(title=title, subtitle=subtitle, date=date, presenter=presenter, chair=chair,
                  sections=sections, tracker=bool(tracker), numbering=numbering, lang=lang)
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


def section(n, **kw):
    """Section divider n (1-based); also makes n the current section."""
    _need_meta()
    secs = D.meta['sections']
    if not 1 <= n <= len(secs):
        raise ValueError(f'section({n}): meta() defines {len(secs)} section(s)')
    if D.backup_at is not None:
        raise ValueError('section() after appendix(): backup slides carry no section')
    D.cur_sec = n - 1
    mark(f'sec-{n}')

    def inner():
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


# ── rendering ────────────────────────────────────────────────────────────

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
        dots = ('<div class="stepdots">' + '<i></i>' * s.steps + '</div>') if s.steps > 1 else ''
        in_backup = D.backup_at is not None and i >= D.backup_at
        if s.kind in ('title', 'thankyou'):
            body = chrome.title_frame(inner)
        else:
            trk = ''
            foot_text = f"{m['chair']} | {m['presenter']}"
            if m['tracker'] and s.kind == 'content' and not in_backup and s.sec is not None:
                trk = chrome.tracker(m['sections'], s.sec)
                foot_text = ''
            title = s.title if s.kind in ('content', 'backuphome') else ''
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
    doc = f'''<!doctype html><html lang="{m['lang']}"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{_html.escape(_strip(m['title']))}</title>
<style>{fonts}</style>
<style>{engine.CSS}</style>
<style>{chrome.CSS}</style>
<style>{components.CSS}</style>
<style>{nav.CSS}</style>
<style>{presenter.CSS}</style>
<style>{extra}</style>
</head><body>
<div id="bar"></div>
<button id="play" title="Present fullscreen (F)">&#9654; Present</button>
<div id="pexit"><kbd>Esc</kbd> exit &nbsp; <kbd>&rarr;</kbd> step &nbsp; <kbd>&darr;</kbd> slide</div>
<div id="top"><span class="lb">Jump</span>{tabs}</div>
<div id="stage">{body}</div>
<div id="foot"><span id="fl"></span><span>{HINTS}<b id="fr"></b></span></div>
<script>{engine.JS.replace('__META__', meta_json)}</script>
<script>{nav.JS.replace('__HUB__', str(hub))}</script>
<script>{presenter.JS}</script>
</body></html>'''
    if out is None:
        out = os.path.join(paths.talk_dir(), 'dist', f'{name}.html')
    os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
    with open(out, 'w', encoding='utf-8') as fh:
        fh.write(doc)
    total_steps = sum(s.steps for s in D.slides)
    print(f'{len(D.slides)} slides · {total_steps} steps · {len(doc) / 1e6:.2f} MB → {out}')
    return out
