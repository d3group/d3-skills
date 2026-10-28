# -*- coding: utf-8 -*-
"""Component kit: designed objects for slide bodies, the Q&A interactions and the live-module API.

Ported from M. Möhle's d3-presentation engine (d3-kit.css / d3-kit.js / d3-deck.css) and recoloured with the D3 tokens.
Every helper returns an HTML string, like the fragments in components.py. Root classes start with 'k-' so they never
collide with the engine (.sl, .gh, .body, .col, .tl, .stat, .facts, .hl, .kick) and so shoot.py can recognise a
designed object.

Motion rules the CSS follows:
  * animate only on the slide on screen: selectors start with '.sl.is-current';
  * the BASE style is the end state, so the print view, the presenter's next pane and the overview (which never carry
    .is-current) show the finished picture;
  * a part that arrives with the slide animates on arrival; a part inside a later step animates when that step is
    shown ('[data-s].is-shown');
  * print and reduced motion switch every animation off (engine.py).
"""
import datetime as _dt
import html as _html
import json as _json
import math as _math

from .components import esc

COLORS = ('navy', 'teal', 'orange', 'red', 'gray')
SIGNS = ('pos', 'neg', 'ind', 'plain', 'mod')
SIGN_LABEL = {'pos': 'positive', 'neg': 'negative', 'ind': 'indeterminate', 'mod': 'moderates'}

# Region sizes per look, in px: the body box and the column boxes of onecol/twocol/twocoltakeaway (chrome.py).
BOX = {look: {'body': (1137, 420), 'col': (548, 420), 'short': (548, 335)} for look in ('klar', 'beamer', 'uni')}   # one frame


def _attr(s=None, k=None, soft=False):
    """Step and Q&A attributes shared by every helper: s = step (0-based, like data-s), k = data-k key."""
    out = ''
    if s is not None:
        out += f' data-s="{int(s)}"'
        if soft:
            out += ' data-soft="1"'
    if k is not None:
        out += f' data-k="{_html.escape(str(k))}"'
    return out


def _color(c, allowed=COLORS):
    if c not in allowed:
        raise ValueError(f'color {c!r}: use one of {allowed}')
    return c


def _a(text):
    return _html.escape(str(text), quote=True)


# ── icons ────────────────────────────────────────────────────────────────
# 24 x 24 grid, 2 px stroke, round caps (from d3-kit.js). Inlined at build time, so the print view, the overview and
# the presenter window carry real paths. Never use emoji or dingbats (✓ ✕ ⚠ ★ ➜) as icons; shoot.py flags them.
ICONS = {
    'alert': '<path d="M10.3 3.9 1.8 18a2 2 0 0 0 1.7 3h17a2 2 0 0 0 1.7-3L13.7 3.9a2 2 0 0 0-3.4 0z"/><path d="M12 9v4M12 17h.01"/>',
    'arrowr': '<path d="M5 12h14M12 5l7 7-7 7"/>',
    'arrowl': '<path d="M19 12H5M12 19l-7-7 7-7"/>',
    'arrowup': '<path d="M12 19V5M5 12l7-7 7 7"/>',
    'arrowdown': '<path d="M12 5v14M19 12l-7 7-7-7"/>',
    'bars': '<path d="M3 21h18"/><rect x="5" y="11" width="3" height="7"/><rect x="10.5" y="6" width="3" height="12"/><rect x="16" y="13" width="3" height="5"/>',
    'book': '<path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20V3H6.5A2.5 2.5 0 0 0 4 5.5z"/><path d="M4 19.5A2.5 2.5 0 0 0 6.5 22H20v-5"/>',
    'bulb': '<path d="M9 18h6M10 21h4"/><path d="M12 3a6 6 0 0 0-4 10.5c.8.8 1 1.5 1 2.5h6c0-1 .2-1.7 1-2.5A6 6 0 0 0 12 3z"/>',
    'calendar': '<rect x="3" y="5" width="18" height="16" rx="2"/><path d="M3 10h18M8 3v4M16 3v4"/>',
    'chart': '<path d="M4 20V10M10 20V4M16 20v-7M22 20H2"/>',
    'check': '<path d="M20 6 9 17l-5-5"/>',
    'clock': '<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/>',
    'click': '<path d="m9 9 5 12 1.8-5.2L21 14z"/><path d="M7.2 2.2 8 5.1M5.1 8 2.2 7.2M14 4.1 12 6.2M6.2 12l-2.1 2"/>',
    'code': '<path d="m16 18 6-6-6-6M8 6l-6 6 6 6"/>',
    'cpu': '<rect x="5" y="5" width="14" height="14" rx="2"/><rect x="9" y="9" width="6" height="6"/><path d="M9 2v3M15 2v3M9 19v3M15 19v3M2 9h3M2 15h3M19 9h3M19 15h3"/>',
    'crosshair': '<circle cx="12" cy="12" r="3"/><path d="M12 2v3M12 19v3M2 12h3M19 12h3M4.9 4.9l2.1 2.1M17 17l2.1 2.1M4.9 19.1L7 17M17 7l2.1-2.1"/>',
    'cube': '<path d="m12 2 9 5v10l-9 5-9-5V7z"/><path d="m3 7 9 5 9-5M12 12v10"/>',
    'database': '<ellipse cx="12" cy="5" rx="8" ry="3"/><path d="M4 5v14c0 1.7 3.6 3 8 3s8-1.3 8-3V5M4 12c0 1.7 3.6 3 8 3s8-1.3 8-3"/>',
    'download': '<path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4M7 10l5 5 5-5M12 15V3"/>',
    'eye': '<path d="M2 12s3.6-7 10-7 10 7 10 7-3.6 7-10 7S2 12 2 12z"/><circle cx="12" cy="12" r="3"/>',
    'eyeoff': '<path d="M9.9 4.2A9.7 9.7 0 0 1 12 4c6.4 0 10 8 10 8a17.6 17.6 0 0 1-2.2 3.2M6.6 6.6C3.9 8.4 2 12 2 12s3.6 8 10 8a9.7 9.7 0 0 0 5.4-1.6M9.9 9.9a3 3 0 0 0 4.2 4.2M2 2l20 20"/>',
    'file': '<path d="M14 3H6a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V9z"/><path d="M14 3v6h6M8 13h8M8 17h6"/>',
    'flag': '<path d="M5 21V4M5 4h11l-2 4 2 4H5"/>',
    'flask': '<path d="M9 3h6M10 3v6L4.5 19a1.5 1.5 0 0 0 1.3 2h12.4a1.5 1.5 0 0 0 1.3-2L14 9V3M7 15h10"/>',
    'fork': '<path d="M3 12h6l6-6h4M9 12l6 6h4M17 4l2 2-2 2M17 16l2 2-2 2"/>',
    'frown': '<circle cx="12" cy="12" r="9"/><path d="M16 16s-1.5-2-4-2-4 2-4 2M9 9h.01M15 9h.01"/>',
    'globe': '<circle cx="12" cy="12" r="9"/><path d="M3 12h18M12 3a14 14 0 0 1 0 18M12 3a14 14 0 0 0 0 18"/>',
    'grid': '<rect x="3" y="3" width="7" height="7" rx="1"/><rect x="14" y="3" width="7" height="7" rx="1"/><rect x="3" y="14" width="7" height="7" rx="1"/><rect x="14" y="14" width="7" height="7" rx="1"/>',
    'hourglass': '<path d="M6 2h12M6 22h12M7 2v3l5 7-5 7v3M17 2v3l-5 7 5 7v3"/>',
    'infinity': '<path d="M12 12c-2-2.7-4-4-6-4a4 4 0 0 0 0 8c2 0 4-1.3 6-4zm0 0c2 2.7 4 4 6 4a4 4 0 0 0 0-8c-2 0-4 1.3-6 4z"/>',
    'jag': '<path d="M3 17l5-9 4 6 3-4 6 10"/>',
    'layers': '<path d="m12 2 10 5-10 5L2 7z"/><path d="m2 17 10 5 10-5M2 12l10 5 10-5"/>',
    'link': '<path d="M10 13a5 5 0 0 0 7.5.5l3-3a5 5 0 0 0-7-7l-1.7 1.7"/><path d="M14 11a5 5 0 0 0-7.5-.5l-3 3a5 5 0 0 0 7 7l1.7-1.7"/>',
    'listcheck': '<path d="m3 6 2 2 3-3M3 13l2 2 3-3M12 7h9M12 14h9M4 20h17"/>',
    'lock': '<rect x="4" y="11" width="16" height="10" rx="2"/><path d="M8 11V7a4 4 0 0 1 8 0v4"/>',
    'mail': '<rect x="3" y="5" width="18" height="14" rx="2"/><path d="m3 7 9 6 9-6"/>',
    'mappin': '<path d="M12 22s7-6.3 7-12a7 7 0 0 0-14 0c0 5.7 7 12 7 12z"/><circle cx="12" cy="10" r="2.5"/>',
    'message': '<path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>',
    'minus': '<path d="M5 12h14"/>',
    'monitor': '<rect x="2" y="3" width="20" height="14" rx="2"/><path d="M8 21h8M12 17v4"/>',
    'pause': '<rect x="6" y="4" width="4" height="16" rx="1"/><rect x="14" y="4" width="4" height="16" rx="1"/>',
    'play': '<path d="M6 4l14 8-14 8z"/>',
    'plus': '<path d="M12 5v14M5 12h14"/>',
    'question': '<circle cx="12" cy="12" r="9"/><path d="M9.1 9a3 3 0 0 1 5.8 1c0 2-3 3-3 3M12 17h.01"/>',
    'quote': '<path d="M7 7h4v4c0 3-2 5-4 6M15 7h4v4c0 3-2 5-4 6"/>',
    'refresh': '<path d="M21 12a9 9 0 1 1-3-6.7L21 8"/><path d="M21 3v5h-5"/>',
    'repeat': '<path d="m17 2 4 4-4 4M3 11v-1a4 4 0 0 1 4-4h14M7 22l-4-4 4-4M21 13v1a4 4 0 0 1-4 4H3"/>',
    'scale': '<path d="M12 3v18M7 21h10M3 7h18M6 7l-3 7a3 3 0 0 0 6 0zM18 7l-3 7a3 3 0 0 0 6 0z"/>',
    'search': '<circle cx="11" cy="11" r="7"/><path d="m21 21-4.3-4.3"/>',
    'send': '<path d="m22 2-7 20-4-9-9-4z"/><path d="M22 2 11 13"/>',
    'shield': '<path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/><path d="m9 12 2 2 4-4"/>',
    'sliders': '<path d="M4 21v-7M4 10V3M12 21v-9M12 8V3M20 21v-5M20 12V3M1 14h6M9 8h6M17 16h6"/>',
    'sparkle': '<path d="M12 3l1.9 5.1L19 10l-5.1 1.9L12 17l-1.9-5.1L5 10l5.1-1.9zM19 16l.8 2.2L22 19l-2.2.8L19 22l-.8-2.2L16 19l2.2-.8z"/>',
    'target': '<circle cx="12" cy="12" r="9"/><circle cx="12" cy="12" r="5"/><circle cx="12" cy="12" r="1"/>',
    'thumbsup': '<path d="M7 10v11H3V10zM7 10l4-8a3 3 0 0 1 3 3v4h5.5a2 2 0 0 1 2 2.3l-1.4 8A2 2 0 0 1 18.1 21H7"/>',
    'trenddown': '<path d="m22 17-8.5-8.5-5 5L2 7"/><path d="M16 17h6v-6"/>',
    'trendup': '<path d="m22 7-8.5 8.5-5-5L2 17"/><path d="M16 7h6v6"/>',
    'user': '<circle cx="12" cy="8" r="4"/><path d="M4 21v-1a7 7 0 0 1 16 0v1"/>',
    'users': '<circle cx="9" cy="8" r="4"/><path d="M1 21v-1a6 6 0 0 1 6-6h4a6 6 0 0 1 6 6v1M17 3.1a4 4 0 0 1 0 7.8M23 21v-1a6 6 0 0 0-4-5.7"/>',
    'x': '<path d="M18 6 6 18M6 6l12 12"/>',
    'xcircle': '<circle cx="12" cy="12" r="9"/><path d="m15 9-6 6M9 9l6 6"/>',
    'zap': '<path d="M13 2 3 14h9l-1 8 10-12h-9z"/>',
    'leaf': '<path d="M11 20A7 7 0 0 1 9.8 6.1C15.5 5 17 4.48 19 2c1 2 2 4.18 2 8 0 5.5-4.78 10-10 10Z"/><path d="M2 21c0-3 1.85-5.36 5.08-6C9.5 14.52 12 13 13 12"/>',
    'heartpulse': '<path d="M19 14c1.49-1.46 3-3.21 3-5.5A5.5 5.5 0 0 0 16.5 3c-1.76 0-3 .5-4.5 2-1.5-1.5-2.74-2-4.5-2A5.5 5.5 0 0 0 2 8.5c0 2.3 1.5 4.05 3 5.5l7 7Z"/><path d="M3.22 12H9.5l.5-1 2 4.5 2-7 1.5 3.5h5.27"/>',
    # method icons for course roadmaps: a linear function, chance (three dice in a throw), a nonlinear curve
    'linear': '<path d="M4 3v17h17"/><path d="M6.5 17 19 6"/>',
    'dice': '<g transform="rotate(-16 6.6 16.2)" stroke-width="1.6"><rect x="2.50" y="12.10" width="8.2" height="8.2" rx="1.9"/><circle cx="4.50" cy="14.10" r="0.95" fill="currentColor" stroke="none"/><circle cx="6.60" cy="16.20" r="0.95" fill="currentColor" stroke="none"/><circle cx="8.70" cy="18.30" r="0.95" fill="currentColor" stroke="none"/></g><g transform="rotate(12 17.2 16.8)" stroke-width="1.6"><rect x="13.10" y="12.70" width="8.2" height="8.2" rx="1.9"/><circle cx="15.30" cy="14.90" r="0.95" fill="currentColor" stroke="none"/><circle cx="19.10" cy="18.70" r="0.95" fill="currentColor" stroke="none"/></g><g transform="rotate(28 12.3 6.2)" stroke-width="1.6"><rect x="8.20" y="2.10" width="8.2" height="8.2" rx="1.9"/><circle cx="12.30" cy="6.20" r="0.95" fill="currentColor" stroke="none"/></g>',   # three dice in a throw
    'curve': '<path d="M4 3v17h17"/><path d="M6 17c2.5-9 5-10 7.5-4.5S17.5 15 19.5 5"/>',
}


def icon(name, cls='', size=None):
    """Inline stroke icon: icon('check'), icon('alert', size=28). Names: see ICONS."""
    if name not in ICONS:
        raise ValueError(f'unknown icon {name!r}; available: {", ".join(sorted(ICONS))}')
    st = f' style="width:{size}px;height:{size}px"' if size else ''
    c = ('ico ' + cls).strip()
    return f'<svg class="{c}" viewBox="0 0 24 24" aria-hidden="true" focusable="false"{st}>{ICONS[name]}</svg>'


# ── blocks ───────────────────────────────────────────────────────────────

def tile(big, lines=(), kick='', ico=None, color='navy', body='', s=None, k=None, soft=False):
    """The main content block: a kicker label (with an optional icon), a keyword headline, a few keyword lines.
    The coloured top rule carries the channel; decide once per deck what teal and red mean and keep it."""
    _color(color)
    head = ''
    if kick or ico:
        head = f'<div class="k-tkick">{icon(ico) if ico else ""}<span>{kick}</span></div>'
    big_html = f'<div class="k-tbig">{big}</div>' if big else ''
    items = ''.join(f'<li{" class=muted" if isinstance(x, tuple) and x[1] == "muted" else ""}>{x[0] if isinstance(x, tuple) else x}</li>'
                    for x in lines)
    lst = f'<ul class="k-tlines">{items}</ul>' if items else ''
    return f'<div class="k-tile {color}"{_attr(s, k, soft)}>{head}{big_html}{lst}{body}</div>'


def well(name, color='navy', size=None):
    """A round icon well: well('users', 'teal')."""
    _color(color)
    return f'<span class="k-well {color}">{icon(name, size=size)}</span>'


def middle(html):
    """Centre a short object vertically in its region instead of leaving a hole below it."""
    return f'<div class="k-mid">{html}</div>'


def callout(html, quiet=False, s=None):
    """The punchline band: one sentence the room must take away, with the carrying phrase in <b> (orange).
    Use it on about one slide in three at most; in the klar look, takeaway= on the slide is the quieter default."""
    q = ' quiet' if quiet else ''
    return f'<div class="k-callout{q}"{_attr(s)}>{html}</div>'


def chip(text, sign=None, solid=False, ico=None):
    """Rounded inline label, optionally led by a sign badge: chip('usability', sign='neg')."""
    lead = sign_badge(sign, ico) if sign else (icon(ico) if ico else '')
    cls = 'k-chip' + (' solid' if solid else '') + ('' if sign else ' plain')
    return f'<span class="{cls}">{lead}<span>{text}</span></span>'


SIGN_ICON = {'pos': 'plus', 'neg': 'minus', 'ind': 'question', 'nil': 'minus', 'ok': 'check', 'no': 'x'}


def sign_badge(kind, ico=None):
    """Round sign badge carrying an icon, never a glyph: pos (teal, +), neg (orange, -), ind (navy, ?), nil,
    ok (teal, check), no (red, x)."""
    if kind not in SIGN_ICON:
        raise ValueError(f'sign {kind!r}: use one of {tuple(SIGN_ICON)}')
    return f'<span class="k-sg {kind}">{icon(ico or SIGN_ICON[kind])}</span>'


def badge(text, color='navy', pop=None, k=None):
    """Small square identifier (H1, P3, S2). With pop= it is a button that opens the full text on click."""
    _color(color)
    if pop:
        return f'<button class="k-badge {color}" data-pop="{_a(pop)}"{_attr(k=k)}>{text}</button>'
    return f'<span class="k-badge {color}"{_attr(k=k)}>{text}</span>'


def stamp(text, color='red', s=None, style=''):
    """'removed', 'new', 'open': a rotated stamp that lands with a bounce when its step arrives. Position it with style=."""
    _color(color)
    st = f' style="{style}"' if style else ''
    return f'<span class="k-stamp {color}"{_attr(s)}{st}>{text}</span>'


def legend(*kinds):
    """Legend for signed edges: legend('pos', 'neg'). Every figure with signed edges shows one."""
    kinds = kinds or ('pos', 'neg')
    items = ''.join(f'<span><i class="{k}"></i>{SIGN_LABEL[k]}</span>' for k in kinds)
    return f'<div class="k-legend">{items}</div>'


# ── Q&A interactions ─────────────────────────────────────────────────────

def pop(label, detail, cls=''):
    """Click for detail: a button that opens a popover with detail (HTML allowed) inside the slide."""
    c = ('k-pop ' + cls).strip()
    return f'<button class="{c}" data-pop="{_a(detail)}">{label}</button>'


def cite(short, ref, where=''):
    """Clickable citation: cite('Vasconcelos et al. 2023', 'Vasconcelos, H. et al. (2023). Explanations can reduce
    overreliance on AI systems. CSCW.', 'p. 7'). Short form on the slide, the full reference on click."""
    detail = f'<b>{esc(ref)}</b>' + (f'<span class="k-where">{esc(where)}</span>' if where else '')
    return f'<button class="k-cite" data-pop="{_a(detail)}">{short}</button>'


def nocaps(text):
    """Keep a symbol lowercase inside an uppercase label: alpha stays alpha, s_i stays s_i."""
    return f'<span class="nocaps">{text}</span>'


# ── numbers ──────────────────────────────────────────────────────────────

def count(value, frm=0, s=None):
    """An integer that counts from frm to value when it arrives (on stage only; every preview shows value)."""
    return f'<span class="k-count"{_attr(s)} style="--v:{int(value)};--from:{int(frm)}"></span>'


def bar(label, value, color='navy', sub='', text=None, grow_from=None, s=None, k=None):
    """One row for bars(): label, value, colour (navy, teal, orange, red, gray, hatch), a grey sub-label, the printed
    value (text=, default: the number with thousands separators) and grow_from= (the row grows out of that value,
    so the room sees what changed)."""
    if color not in COLORS + ('hatch',):
        raise ValueError(f'bar color {color!r}: use one of {COLORS + ("hatch",)}')
    return dict(label=label, value=float(value), color=color, sub=sub, text=text, grow_from=grow_from, s=s, k=k)


def bars(*rows, scale=None, unit='', label_w=220, gap=14, height=30, value_w=170):
    """Horizontal bars on ONE scale, growing on arrival (or on their step). rows: bar(...) dicts.
    scale= fixes the maximum, so bars on several slides compare; unit= is appended to the printed values;
    value_w= is the room kept right of the longest bar for its printed value."""
    if not rows:
        raise ValueError('bars(): give at least one bar(...)')
    top = scale or max(r['value'] for r in rows)
    if top <= 0:
        raise ValueError('bars(): the scale maximum must be positive')
    out = [f'<div class="k-bars" style="--lw:{label_w}px;--bh:{height}px;--vw:{value_w}px;row-gap:{gap}px">']
    for i, r in enumerate(rows):
        w = r['value'] / top * 100
        if w > 100.001:
            raise ValueError(f'bars(): {r["label"]!r} = {r["value"]} exceeds scale={top}')
        s0 = (r['grow_from'] / r['value']) if r['grow_from'] and r['value'] else 0
        txt = r['text'] if r['text'] is not None else (f'{r["value"]:,.0f}' if r['value'] == int(r['value']) else f'{r["value"]:,}')
        sub = f'<small>{r["sub"]}</small>' if r['sub'] else ''
        out.append(f'<div class="k-brow"{_attr(r["s"], r["k"])} style="--i:{i}">'
                   f'<div class="k-blab">{r["label"]}{sub}</div>'
                   f'<div class="k-btrack"><div class="k-bfill {r["color"]}" style="width:{w:.2f}%;--s0:{s0:.4f}"></div>'
                   f'<span class="k-bval">{txt}{unit}</span></div></div>')
    out.append('</div>')
    return ''.join(out)


def effect(value, sign='pos', text=None, scale=1.0):
    """Effect-size bar for a table cell: effect(.72) teal, effect(-.31, 'neg') orange, effect(.12, 'weak') hatched
    (underpowered or uncertain). Bar width = |value| / scale."""
    if sign not in ('pos', 'neg', 'weak', 'plain'):
        raise ValueError("effect sign: 'pos', 'neg', 'weak' or 'plain'")
    w = min(abs(float(value)) / scale * 100, 100)
    txt = text if text is not None else f'{value}'
    return f'<span class="k-effect {sign}"><span class="k-etrk"><i style="width:{w:.1f}%"></i></span><span>{txt}</span></span>'


def gauge(lo, hi, marks, zone=None, ends=True, unit=''):
    """Two or three values on one scale, a hatched zone, the gap is the point.
    marks: [(value, label, color)], color in navy/teal/orange/red. zone: (a, b) or (a, b, color).
    Keep marker labels apart by at least an eighth of the scale."""
    if hi <= lo:
        raise ValueError('gauge(): hi must exceed lo')

    def pct(v):
        if not lo <= v <= hi:
            raise ValueError(f'gauge(): {v} lies outside {lo}..{hi}')
        return (v - lo) / (hi - lo) * 100
    out = ['<div class="k-gauge"><div class="k-gtrack">']
    if zone:
        a, b = zone[0], zone[1]
        zc = _color(zone[2]) if len(zone) > 2 else 'red'
        out.append(f'<div class="k-gzone {zc}" style="left:{pct(a):.2f}%;width:{pct(b) - pct(a):.2f}%"></div>')
    for i, (v, label, color) in enumerate(marks):
        _color(color)
        out.append(f'<i class="k-gmark {color}" style="left:{pct(v):.2f}%;--i:{i}"><b>{label}</b></i>')
    out.append('</div>')
    if ends:
        out.append(f'<div class="k-gends"><span>{lo}{unit}</span><span>{hi}{unit}</span></div>')
    out.append('</div>')
    return ''.join(out)


def units(groups, size=16, legend_=True):
    """Unit chart: one square per unit, coloured by class, staggered in. groups: [(n, color, label)]."""
    sq, leg, i = [], [], 0
    for n, color, label in groups:
        _color(color)
        for _ in range(int(n)):
            sq.append(f'<i class="{color}" style="--i:{i}"></i>')
            i += 1
        leg.append(f'<span><i class="{color}"></i>{n} {label}</span>')
    lg = f'<div class="k-ulegend">{"".join(leg)}</div>' if legend_ else ''
    return f'<div class="k-units" style="--u:{size}px"><div class="k-usq">{"".join(sq)}</div>{lg}</div>'


def bub(n, color='navy', pop=None):
    """A circle sized by a count; with pop= a click opens the names behind the count. n=0 draws an empty ring."""
    _color(color)
    cls = f'k-bub {color}' + (' nil' if not n else '')
    if pop:
        return f'<button class="{cls}" style="--n:{int(n)}" data-pop="{_a(pop)}">{n}</button>'
    return f'<span class="{cls}" style="--n:{int(n)}">{n}</span>'


# ── derivations ──────────────────────────────────────────────────────────

def line(formula, why='', kind='', s=None):
    """One row of proof(): a formula (LaTeX in $...$ works), its reason, and kind '' | 'wrong' (a tempting wrong step,
    red) | 'key' (the step that carries the argument, teal)."""
    if kind not in ('', 'wrong', 'key'):
        raise ValueError("line kind: '', 'wrong' or 'key'")
    return dict(formula=formula, why=why, kind=kind, s=s)


def proof(*rows):
    """A derivation as numbered rows on a rail, each justified on the right. rows: line(...) dicts."""
    out = ['<div class="k-proof">']
    for i, r in enumerate(rows):
        out.append(f'<div class="k-prow {r["kind"]}"{_attr(r["s"])}><span class="k-pn">{i}</span>'
                   f'<div class="k-pbox"><span class="k-pf">{r["formula"]}</span><span class="k-why">{r["why"]}</span></div></div>')
    out.append('</div>')
    return ''.join(out)


def brace(term, label, color='navy'):
    """A braced term naming its part of an identity; put several side by side in a flex row. Braces draw on arrival."""
    _color(color)
    return f'<span class="k-brace {color}"><span class="k-bx">{term}</span><span class="k-bb"></span><span class="k-bl">{label}</span></span>'


# ── comparisons ──────────────────────────────────────────────────────────

def versus(left, right, rows, left_ico=None, right_ico=None, left_color='red', right_color='teal', lstep=None, rstep=None):
    """Mirror comparison: two things compared row by row around a centre column of row labels.
    rows: [(left html, label, right html)]. lstep/rstep reveal a whole column on a step."""
    _color(left_color), _color(right_color)
    li = icon(left_ico) if left_ico else ''
    ri = icon(right_ico) if right_ico else ''
    out = [f'<div class="k-vs"><div class="k-vhead"><div class="l {left_color}">{left}{li}</div><div></div>'
           f'<div class="r {right_color}">{ri}{right}</div></div>']
    for l, m, r in rows:
        out.append(f'<div class="k-vrow"><div class="l"{_attr(lstep)}>{l}</div><div class="m">{m}</div>'
                   f'<div class="r"{_attr(rstep)}>{r}</div></div>')
    out.append('</div>')
    return ''.join(out)


def selector(options, chosen, color='navy'):
    """Every option of a classification on one axis, the chosen one lit; the highlight slides onto it on arrival.
    chosen: 0-based index."""
    if not 0 <= chosen < len(options):
        raise ValueError(f'selector(): chosen={chosen} outside 0..{len(options) - 1}')
    _color(color)
    spans = ''.join(f'<span{" class=on" if i == chosen else ""}>{o}</span>' for i, o in enumerate(options))
    return f'<div class="k-select {color}" style="--sel:{chosen}"><i class="k-shl"></i>{spans}</div>'


# ── stimuli ──────────────────────────────────────────────────────────────

def flag(text):
    """Mark the manipulated detail inside a chat() answer."""
    return f'<span class="k-flag">{text}</span>'


def chat(question, answer, title='', who='AI', replay=True, user_color=None, s=None):
    """A chat interface rebuilt in HTML (sharp on any projector, word for word from the study).
    replay=True: on arrival the question pops, typing dots run, the answer streams in (about 3 s; only at step 0).
    user_color: the stimulus' own bubble colour when the replica must be faithful (default navy)."""
    uc = f' style="--cw-user:{user_color}"' if user_color else ''
    rp = ' replay' if replay else ''
    return (f'<div class="k-chat{rp}"{uc}{_attr(s)} role="img" aria-label="{_a(title or "chat interface")}">'
            f'<div class="cw-bar"><i></i><i></i><i></i><span>{title}</span></div>'
            f'<div class="cw-body"><div class="cw-user">{question}</div>'
            f'<div class="cw-row"><span class="cw-av">{who}</span><div class="cw-typing"><i></i><i></i><i></i></div>'
            f'<div class="cw-ai">{answer}</div></div></div></div>')


# ── time ─────────────────────────────────────────────────────────────────

def _date(d):
    return d if isinstance(d, _dt.date) else _dt.date.fromisoformat(str(d))


def milestones(start, end, items, today=None, pad=70):
    """A to-scale timeline: items [(date 'YYYY-MM-DD', title, sub, kind)] with kind '' | 'done' | 'key' (the one orange
    milestone). A 'today' dot and fill are placed for today= (default: the build date) and moved to the real date when
    the deck opens. Keep labels apart; a label is centred on its date. pad: px kept free at both ends for labels."""
    a, b = _date(start), _date(end)
    if b <= a:
        raise ValueError('milestones(): end must be after start')
    t = _date(today) if today else _dt.date.today()
    span = (b - a).days

    def pos(d):
        d = _date(d)
        if not a <= d <= b:
            raise ValueError(f'milestones(): {d} outside {a}..{b}')
        return (d - a).days / span * 100
    now = min(max((t - a).days / span * 100, 0), 100)
    out = [f'<div class="k-ms" data-start="{a}" data-end="{b}" style="--pad:{pad}px"><div class="k-mline"></div>'
           f'<div class="k-mfill" style="width:{now:.2f}%"></div><i class="k-mnow" style="left:{now:.2f}%"></i>']
    for it in items:
        d, title = it[0], it[1]
        sub = it[2] if len(it) > 2 else ''
        kind = it[3] if len(it) > 3 else ''
        if kind not in ('', 'done', 'key'):
            raise ValueError("milestone kind: '', 'done' or 'key'")
        label = f'{_date(d).day} {_date(d).strftime("%b")}'
        out.append(f'<div class="k-mi {kind}" style="left:{pos(d):.2f}%"><span class="d">{label}</span><i></i>'
                   f'<b>{title}</b><span>{sub}</span></div>')
    out.append('</div>')
    return ''.join(out)


def countdown(date, what='to go', today=None):
    """A chip counting the days to a date; updated to the real date when the deck opens."""
    d = _date(date)
    t = _date(today) if today else _dt.date.today()
    n = (d - t).days
    return (f'<span class="k-chip plain k-cd" data-date="{d}" data-what="{_a(what)}"><b>{n}</b>'
            f'<span>{"day" if n == 1 else "days"} {what}</span></span>')


# ── model figures ────────────────────────────────────────────────────────

def node(id, label, x=None, y=0, w=200, h=64, sub='', color='navy', col=None, s=None, k=None, soft=False):
    """A construct of model(): position in px inside the region (x, y = top-left), or col= a lane index (0-based) to
    centre it in that lane. color: navy (default), teal, orange, red, gray, or 'solid'."""
    if color not in COLORS + ('solid',):
        raise ValueError(f'node color {color!r}: use one of {COLORS + ("solid",)}')
    if x is None and col is None:
        raise ValueError(f'node({id!r}): give x= or col=')
    return dict(id=id, label=label, x=x, y=y, w=w, h=h, sub=sub, color=color, col=col, s=s, k=k, soft=soft)


def edge(a, b, sign='plain', tag='', s=None, k=None, at=0.5, bend=None):
    """A relation of model() from node a to node b. b may also be another edge as a pair (a2, b2): the arrow then
    points at the middle of that relation, the notation for a moderator (use sign='mod').
    sign: pos (teal), neg (orange), ind (navy), mod (grey, dashed), plain (grey-blue, unsigned). tag: a label on the
    edge (P2, H1, +), cutting the line with a white ground, at= the fraction along the edge. s: the step it draws in on
    (it draws only on its step; static otherwise). k: Q&A key. bend: override the curve depth in px."""
    if sign not in SIGNS:
        raise ValueError(f'edge sign {sign!r}: use one of {SIGNS}')
    return dict(a=a, b=b, sign=sign, tag=tag, s=s, k=k, at=at, bend=bend)


def _anchor(box, side, frac):
    x, y, w, h = box
    if side == 'r':
        return (x + w, y + h * frac)
    if side == 'l':
        return (x, y + h * frac)
    if side == 'b':
        return (x + w * frac, y + h)
    return (x + w * frac, y)


NORMAL = {'r': (1, 0), 'l': (-1, 0), 'b': (0, 1), 't': (0, -1)}
HEAD_L, HEAD_W = 10.0, 9.0


def model(nodes, edges, lanes=(), box='body', legend_=True, lane_gap=40, lane_h=46):
    """A theory model or process as nodes and edges, geometry computed: edges leave and enter node borders on the side
    facing the other node, several edges on one side spread out, curves have tangents normal to the border, and the
    arrowhead's tip touches the target border. lanes: stage labels over equal columns, each 'Label' or ('Label', 'sub').
    box: 'body' | 'col' | 'short' | (w, h); the figure has exactly that size in px."""
    from . import deck as _deck
    look = (_deck.D.meta or {}).get('look', 'klar')
    W, H = BOX[look][box] if isinstance(box, str) else box
    n_l = len(lanes)
    lane_w = (W - lane_gap * (n_l - 1)) / n_l if n_l else 0
    boxes, out_nodes = {}, []
    for n in nodes:
        if n['id'] in boxes:
            raise ValueError(f'model(): duplicate node id {n["id"]!r}')
        if n['col'] is not None:
            if not 0 <= n['col'] < max(n_l, 1) or not n_l:
                raise ValueError(f'node({n["id"]!r}): col={n["col"]} needs lanes= with more than {n["col"]} entries')
            x = n['col'] * (lane_w + lane_gap) + (lane_w - n['w']) / 2
        else:
            x = n['x']
        boxes[n['id']] = (x, n['y'], n['w'], n['h'])
        if x < -0.5 or n['y'] < -0.5 or x + n['w'] > W + 0.5 or n['y'] + n['h'] > H + 0.5:
            raise ValueError(f'node({n["id"]!r}) at ({x:.0f}, {n["y"]}) size {n["w"]}x{n["h"]} leaves the {W}x{H} region')
    node_edges = [e for e in edges if not isinstance(e['b'], (tuple, list))]
    rel_edges = [e for e in edges if isinstance(e['b'], (tuple, list))]
    for e in edges:
        for end in (e['a'],) + (tuple(e['b']) if isinstance(e['b'], (tuple, list)) else (e['b'],)):
            if end not in boxes:
                raise ValueError(f'edge {e["a"]!r} -> {e["b"]!r}: unknown node {end!r}')
    # sides: horizontal when the centres are further apart in x than in y
    sides = []
    for e in node_edges:
        ax, ay, aw, ah = boxes[e['a']]
        bx, by, bw, bh = boxes[e['b']]
        dx = (bx + bw / 2) - (ax + aw / 2)
        dy = (by + bh / 2) - (ay + ah / 2)
        if abs(dx) >= abs(dy):
            sides.append(('r', 'l') if dx > 0 else ('l', 'r'))
        else:
            sides.append(('b', 't') if dy > 0 else ('t', 'b'))
    # spread several edges on one side, ordered by the far end so they do not cross
    groups = {}
    for i, e in enumerate(node_edges):
        sa, sb = sides[i]
        for nid, side, other in ((e['a'], sa, e['b']), (e['b'], sb, e['a'])):
            ox, oy, ow, oh = boxes[other]
            key = oy + oh / 2 if side in 'lr' else ox + ow / 2
            groups.setdefault((nid, side), []).append((key, i, nid == e['a']))
    frac = {}
    for (nid, side), lst in groups.items():
        lst.sort()
        m = len(lst)
        for j, (_, i, is_a) in enumerate(lst):
            frac[(i, is_a)] = 0.5 if m == 1 else 0.22 + 0.56 * j / (m - 1)
    paths, tags, used, mids = [], [], [], {}

    def draw(e, p0, na, tip, nb):
        dist = abs(tip[0] - p0[0]) if na[0] else abs(tip[1] - p0[1])
        d = e['bend'] if e['bend'] is not None else max(24.0, 0.45 * dist)
        base = (tip[0] + nb[0] * HEAD_L, tip[1] + nb[1] * HEAD_L)     # the shaft ends where the head begins
        c1 = (p0[0] + na[0] * d, p0[1] + na[1] * d)
        c2 = (base[0] + nb[0] * d, base[1] + nb[1] * d)

        def at(t):
            return tuple((1 - t) ** 3 * p0[j] + 3 * (1 - t) ** 2 * t * c1[j] + 3 * (1 - t) * t ** 2 * c2[j] + t ** 3 * base[j]
                         for j in (0, 1))
        path = f'M{p0[0]:.1f} {p0[1]:.1f} C{c1[0]:.1f} {c1[1]:.1f} {c2[0]:.1f} {c2[1]:.1f} {base[0]:.1f} {base[1]:.1f}'
        ux, uy = -nb[0], -nb[1]                                       # the head points into the target
        px, py = -uy, ux
        head = (f'M{tip[0]:.1f} {tip[1]:.1f} L{base[0] + px * HEAD_W / 2:.1f} {base[1] + py * HEAD_W / 2:.1f} '
                f'L{base[0] - px * HEAD_W / 2:.1f} {base[1] - py * HEAD_W / 2:.1f}Z')
        drawn = ' draw' if e['s'] is not None and e['sign'] != 'mod' else ''
        pl = '' if e['sign'] == 'mod' else ' pathLength="1"'           # a dashed edge keeps its dashes in px
        paths.append(f'<g class="k-e {e["sign"]}{drawn}"{_attr(e["s"], e["k"])}>'
                     f'<path class="k-ep"{pl} d="{path}"/><path class="k-eh" d="{head}"/></g>')
        if e['tag']:
            x_, y_ = at(e['at'])
            tags.append(f'<span class="k-etag {e["sign"]}"{_attr(e["s"], e["k"])} style="left:{x_:.1f}px;top:{y_:.1f}px">{e["tag"]}</span>')
        if e['sign'] in SIGN_LABEL and e['sign'] not in used:
            used.append(e['sign'])
        return at(0.5)

    for i, e in enumerate(node_edges):
        sa, sb = sides[i]
        p0 = _anchor(boxes[e['a']], sa, frac[(i, True)])
        tip = _anchor(boxes[e['b']], sb, frac[(i, False)])
        mids[(e['a'], e['b'])] = draw(e, p0, NORMAL[sa], tip, NORMAL[sb])
    for e in rel_edges:                                                # moderators: onto the middle of a relation
        key = tuple(e['b'])
        if key not in mids:
            raise ValueError(f'edge {e["a"]!r} -> {key}: no edge {key[0]!r} -> {key[1]!r} to point at')
        mx, my = mids[key]
        ax, ay, aw, ah = boxes[e['a']]
        dx, dy = mx - (ax + aw / 2), my - (ay + ah / 2)
        if abs(dy) >= abs(dx):
            sa, sb = ('b', 't') if dy > 0 else ('t', 'b')
            tip = (mx, my - 3 if dy > 0 else my + 3)                  # the head stops just short of the line
        else:
            sa, sb = ('r', 'l') if dx > 0 else ('l', 'r')
            tip = (mx - 3 if dx > 0 else mx + 3, my)
        draw(e, _anchor(boxes[e['a']], sa, 0.5), NORMAL[sa], tip, NORMAL[sb])
    html = [f'<div class="k-model" style="width:{W}px;height:{H}px">']
    for j, lab in enumerate(lanes):
        name, sub = (lab if isinstance(lab, tuple) else (lab, ''))
        x = j * (lane_w + lane_gap)
        sub = f'<span>{sub}</span>' if sub else ''
        html.append(f'<div class="k-lane" style="left:{x:.1f}px;width:{lane_w:.1f}px;height:{lane_h}px">{name}{sub}</div>')
    html.append(f'<svg class="k-edges" viewBox="0 0 {W} {H}" width="{W}" height="{H}" aria-hidden="true">{"".join(paths)}</svg>')
    for n in nodes:
        x, y, w, h = boxes[n['id']]
        sub = f'<small>{n["sub"]}</small>' if n['sub'] else ''
        html.append(f'<div class="k-node {n["color"]}"{_attr(n["s"], n["k"], n["soft"])} '
                    f'style="left:{x:.1f}px;top:{y}px;width:{n["w"]}px;height:{h}px"><span>{n["label"]}{sub}</span></div>')
    html.extend(tags)
    if legend_ and used:
        html.append(f'<div class="k-mlegend">{legend(*[u for u in SIGN_LABEL if u in used])}</div>')
    html.append('</div>')
    return ''.join(html)


# ── instruments ──────────────────────────────────────────────────────────

def slider(id, label, lo, hi, value, step=1, note='', presets=(), fmt='int'):
    """A labelled range input whose value shows beside its name. presets: rehearsed values as chips, one click each
    (the presenter window relays the click). fmt: 'int' | 'pct' | '1' | '2' (decimals) for the shown value.
    Read it from a live module: document.getElementById(id).valueAsNumber."""
    chips = ''.join(f'<button class="k-preset" data-kit-set="#{id}={p}">{p}</button>' for p in presets)
    chips = f'<div class="k-presets">{chips}</div>' if chips else ''
    nt = f'<p class="k-note">{note}</p>' if note else ''
    return (f'<div class="k-ctl"><div class="k-ctop"><span class="k-cname">{label}</span>'
            f'<span class="k-cval" id="{id}-val"></span></div>'
            f'<input type="range" id="{id}" min="{lo}" max="{hi}" step="{step}" value="{value}" data-fmt="{fmt}">{chips}{nt}</div>')


def readout(*cells):
    """Live numbers under an instrument: cells (label, id, initial value). Update with D3Deck.set(id, text): the value
    flashes once when it changes."""
    body = ''.join(f'<div class="k-rc"><span class="k-rk">{k}</span><span class="k-rv" id="{i}">{v}</span></div>' for k, i, v in cells)
    return f'<div class="k-readout" style="--n:{len(cells)}">{body}</div>'


def lab(figure, rack, cap='', rack_w=340):
    """An instrument: the figure (a canvas or svg the live module paints) left, the controls rack right.
    Paint a still in setup() so the print view and the previews show a finished figure."""
    c = f'<div class="k-lcap">{cap}</div>' if cap else ''
    return f'<div class="k-lab" style="--rw:{rack_w}px"><div class="k-lfig">{figure}{c}</div><div class="k-rack">{rack}</div></div>'


# ── CSS ──────────────────────────────────────────────────────────────────

CSS = r"""
:root{--teal-ink:#007A6E;--orange-ink:#B86E00;--red:#C0392B;--navy-10:#E6E9F0;--teal-10:#E6F4F3;--teal-25:#BFE4E0;
 --orange-10:#FEF4E6;--red-10:#F9EBEA;--red-25:#EBC3BF;--gray-10:#F2F3F5;--ease:cubic-bezier(.22,.61,.36,1);
 --k-lg:26px;--k-md:21px;--k-sm:19px;--k-xs:16px;--k-mi:11.5px}
@property --v{syntax:'<integer>';inherits:false;initial-value:0}
@keyframes k-pop{from{opacity:0;transform:translateY(8px)}}
@keyframes k-appear{from{opacity:0}}
@keyframes k-grow-x{from{transform:scaleX(var(--s0,0))}}
@keyframes k-draw{from{stroke-dashoffset:1}}
@keyframes k-count{from{--v:var(--from)}}
@keyframes k-ring{0%{box-shadow:0 0 0 0 rgba(2,36,108,.35)}70%{box-shadow:0 0 0 14px rgba(2,36,108,0)}100%{box-shadow:0 0 0 0 rgba(2,36,108,0)}}
@keyframes k-stream{from{clip-path:inset(0 0 100% 0 round 12px)}to{clip-path:inset(0 0 0 0 round 12px)}}
@keyframes k-typing{0%,100%{opacity:0}10%,86%{opacity:1}}
@keyframes k-blink{0%,70%,100%{transform:none;opacity:.4}35%{transform:translateY(-3px);opacity:1}}
@keyframes k-slide-hl{from{top:0;opacity:.35}}
@keyframes k-stamp{from{transform:rotate(-6deg) scale(1.7);opacity:0}}
@keyframes k-bump{50%{color:var(--orange);transform:translateY(-2px)}}
/* micro-motion for mocks and examples (html-components.md): press, nudge, slide in from a side, recede */
@keyframes k-press{50%{transform:scale(.92);filter:brightness(.85)}}
@keyframes k-nudge{50%{transform:translateX(6px)}}
@keyframes k-slide-l{from{opacity:0;transform:translateX(-18px)}}
@keyframes k-slide-r{from{opacity:0;transform:translateX(18px)}}
@keyframes k-fade-back{to{opacity:.5}}
.nocaps{text-transform:none!important;letter-spacing:normal!important}
.k-mid{height:100%;display:flex;flex-direction:column;justify-content:center}

/* ── icons ── */
svg.ico{display:inline-block;width:1em;height:1em;fill:none;stroke:currentColor;stroke-width:2;stroke-linecap:round;stroke-linejoin:round;
 flex:none;vertical-align:-.14em}

/* ── micro label style shared by kit parts: the klar mono caps ── */
.k-tkick,.k-lane,.k-why,.k-cname,.k-rk,.k-lcap,.k-legend,.k-ulegend,.k-gends,.k-mi .d,.k-mi span,.k-vrow .m,.k-bl,.prov{
 font-family:var(--mono);font-size:var(--k-mi);letter-spacing:.14em;text-transform:uppercase;color:#6B7688;font-weight:400;line-height:1.35}

/* ── tile ── */
.k-tile{position:relative;background:#fff;border:1px solid var(--line);border-top:3px solid var(--navy);border-radius:8px;padding:15px 18px;
 font-size:var(--k-md);line-height:1.35;color:#1B2740}
.k-tile.teal{border-top-color:var(--teal)}.k-tile.orange{border-top-color:var(--orange)}.k-tile.red{border-top-color:var(--red)}
.k-tile.gray{border-top-color:#C4C9D2}
.k-tkick{display:flex;align-items:center;gap:8px}
.k-tkick .ico{width:16px;height:16px;color:var(--navy)}
.k-tile.teal .k-tkick .ico{color:var(--teal-ink)}.k-tile.orange .k-tkick .ico{color:var(--orange-ink)}.k-tile.red .k-tkick .ico{color:var(--red)}
.k-tbig{font-size:var(--k-lg);font-weight:600;line-height:1.2;color:var(--navy);margin-top:7px;letter-spacing:-.01em}
.k-tile.teal .k-tbig{color:var(--teal-ink)}.k-tile.orange .k-tbig{color:var(--orange-ink)}.k-tile.red .k-tbig{color:var(--red)}
.k-tlines{list-style:none;margin:10px 0 0;padding:0;display:grid;gap:6px;font-size:var(--k-sm);line-height:1.3}
.sl .k-tlines>li{padding-left:16px;margin:0}
.sl .k-tlines>li::before{top:.5em;width:6px;height:6px;background:var(--teal)}
.sl .k-tlines>li.muted{color:#6B7688}.sl .k-tlines>li.muted::before{background:#C4C9D2}
.k-well{display:inline-grid;place-items:center;width:38px;height:38px;border-radius:50%;flex:none;background:var(--navy-10);color:var(--navy)}
.k-well .ico{width:19px;height:19px}
.k-well.teal{background:var(--teal-10);color:var(--teal-ink)}.k-well.orange{background:var(--orange-10);color:var(--orange-ink)}
.k-well.red{background:var(--red-10);color:var(--red)}.k-well.gray{background:var(--gray-10);color:var(--gray)}

/* ── callout band: navy, the carrying phrase in orange ── */
.k-callout{background:var(--navy);color:#fff;border-radius:8px;padding:18px 28px;font-size:22px;font-weight:600;line-height:1.35;text-align:center}
.k-callout b{color:#FFB547;font-weight:700}
.k-callout.quiet{background:var(--navy-5);border:1px solid var(--navy-15);color:#1B2740;font-weight:400;text-align:left}
.k-callout.quiet b{color:var(--orange-ink)}

/* ── chips, signs, badges, stamps, legends ── */
.k-chip{display:inline-flex;align-items:center;gap:7px;padding:3px 11px 3px 3px;border-radius:999px;background:#fff;border:1px solid var(--line);
 font-size:var(--k-xs);font-weight:600;color:#1B2740;white-space:nowrap;vertical-align:middle}
.k-chip.plain{padding:3px 11px}
.k-chip.solid{padding:3px 11px;background:var(--navy);border-color:var(--navy);color:#fff}
.k-sg{display:inline-grid;place-items:center;width:22px;height:22px;border-radius:50%;flex:none;color:#fff;vertical-align:middle}
.k-sg .ico{width:62%;height:62%;stroke-width:3}
.k-sg.pos,.k-sg.ok{background:var(--teal-ink)}.k-sg.neg{background:var(--orange)}.k-sg.ind{background:var(--navy)}
.k-sg.no{background:var(--red)}.k-sg.nil{background:#fff;color:#8A93A3;border:1px solid var(--line)}
.k-badge{display:inline-grid;place-items:center;min-width:30px;height:22px;padding:0 6px;border-radius:4px;background:var(--navy);color:#fff;
 font-family:inherit;font-size:12px;font-weight:700;letter-spacing:.04em;font-variant-numeric:tabular-nums;border:0;line-height:1;vertical-align:middle}
.k-badge.teal{background:var(--teal-ink)}.k-badge.orange{background:var(--orange)}.k-badge.red{background:var(--red)}.k-badge.gray{background:#8A93A3}
.k-stamp{position:absolute;z-index:3;padding:2px 10px;border:2px solid var(--red);border-radius:5px;background:rgba(255,255,255,.92);color:var(--red);
 font-size:11px;font-weight:700;letter-spacing:.16em;text-transform:uppercase;transform:rotate(-6deg)}
.k-stamp.teal{border-color:var(--teal-ink);color:var(--teal-ink)}.k-stamp.navy{border-color:var(--navy);color:var(--navy)}
.k-stamp.orange{border-color:var(--orange);color:var(--orange-ink)}.k-stamp.gray{border-color:#8A93A3;color:#6B7688}
.sl.is-current .k-stamp:not([data-s] .k-stamp):not([data-s]),.sl.is-current .k-stamp[data-s].is-shown{animation:k-stamp .4s cubic-bezier(.3,1.7,.5,1) .3s both}
.k-legend{display:flex;gap:22px}
.k-legend span{display:inline-flex;align-items:center;gap:8px}
.k-legend i{display:inline-block;width:24px;border-top:2px solid}
.k-legend .pos{border-color:var(--teal-ink)}.k-legend .neg{border-color:var(--orange)}.k-legend .ind{border-color:var(--navy)}
.k-legend .mod{border-top-style:dashed;border-color:#8A93A3}

/* ── Q&A: data-k lighting, popovers, citations ── */
[data-k],[data-pop]{cursor:pointer}
button.k-pop,button.k-cite{font:inherit;background:none;border:0;padding:0;cursor:pointer;color:inherit}
button.k-pop{color:var(--navy);border-bottom:1px dotted var(--navy);font-weight:600}
button.k-cite{color:var(--teal-ink);font-weight:600;border-bottom:1px dotted var(--teal-ink)}
button.k-cite:hover,button.k-pop:hover{background:var(--teal-10)}
.k-lighting [data-k]:not(.lit){transition:opacity .25s}
.k-lighting .k-e[data-k]:not(.lit),.k-lighting .k-node[data-k]:not(.lit),.k-lighting .k-etag[data-k]:not(.lit){opacity:.22}
.k-e.lit .k-ep{stroke-width:3.5}
.k-node.lit,.k-tile.lit,.k-badge.lit{box-shadow:0 0 0 3px #fff,0 0 0 5px var(--orange)}
.k-popover{position:absolute;z-index:40;max-width:400px;padding:12px 15px;border-radius:8px;background:#fff;border:1px solid var(--navy-15);
 box-shadow:0 14px 34px -14px rgba(10,40,100,.45);font-size:15px;line-height:1.45;color:#1B2740;animation:k-pop .25s var(--ease) both;text-align:left}
.k-popover b{color:var(--navy);font-weight:600}
.k-popover .k-where{display:block;margin-top:6px;font-family:var(--mono);font-size:11px;letter-spacing:.1em;text-transform:uppercase;color:var(--orange-ink)}

/* ── numbers: counter, bars, effect bars, gauge, units, bubbles ── */
.k-count{counter-reset:v var(--v);font-variant-numeric:tabular-nums}
.k-count::after{content:counter(v)}
.sl.is-current .k-count:not([data-s] .k-count):not([data-s]),.sl.is-current [data-s].is-shown .k-count,.sl.is-current .k-count[data-s].is-shown{
 animation:k-count .9s var(--ease) .3s both}
.k-bars{display:grid;grid-template-columns:var(--lw) 1fr;align-items:center;column-gap:18px}
.k-brow{display:contents}
.k-blab{font-size:var(--k-sm);font-weight:600;color:#1B2740;text-align:right;line-height:1.2}
.k-blab small{display:block;font-weight:400;font-size:12.5px;color:#6B7688;margin-top:2px}
.k-btrack{display:flex;align-items:center;gap:10px;height:var(--bh);padding-right:var(--vw,170px)}   /* room for the value right of the longest bar */
.k-bfill{height:100%;border-radius:3px;background:var(--navy);transform-origin:left;flex:none}
.k-bfill.teal{background:var(--teal)}.k-bfill.orange{background:var(--orange)}.k-bfill.red{background:var(--red)}.k-bfill.gray{background:#C4C9D2}
.k-bfill.hatch{background:repeating-linear-gradient(135deg,var(--navy-50) 0 4px,var(--navy-15) 4px 8px)}
.k-bval{font-size:var(--k-sm);font-weight:700;color:var(--navy);font-variant-numeric:tabular-nums;white-space:nowrap}
.sl.is-current .k-bars:not([data-s] .k-bars) .k-brow:not([data-s]) .k-bfill,.sl.is-current .k-brow[data-s].is-shown .k-bfill{
 animation:k-grow-x .8s var(--ease) calc(.25s + var(--i) * .12s) both}
.sl.is-current .k-bars:not([data-s] .k-bars) .k-brow:not([data-s]) .k-bval,.sl.is-current .k-brow[data-s].is-shown .k-bval{
 animation:k-appear .3s calc(.8s + var(--i) * .12s) both}
.k-brow.gh .k-blab,.k-brow.gh .k-btrack{opacity:.15;filter:grayscale(1)}
body.reveal-hide .k-brow.gh .k-blab,body.reveal-hide .k-brow.gh .k-btrack{opacity:0}
.k-effect{display:inline-grid;grid-template-columns:140px auto;align-items:center;gap:12px;font-size:var(--k-xs);font-weight:700;
 font-variant-numeric:tabular-nums;color:var(--navy);white-space:nowrap;vertical-align:middle}
.k-etrk{position:relative;height:9px;border-radius:5px;background:var(--navy-10);overflow:hidden}
.k-etrk i{position:absolute;inset:0 auto 0 0;border-radius:5px;transform-origin:left;background:var(--navy)}
.k-effect.pos .k-etrk i{background:var(--teal)}.k-effect.neg .k-etrk i{background:var(--orange)}
.k-effect.weak .k-etrk i{background:repeating-linear-gradient(135deg,var(--teal) 0 4px,var(--teal-25) 4px 8px)}
.sl.is-current .k-effect:not([data-s] .k-effect) .k-etrk i,.sl.is-current [data-s].is-shown .k-effect .k-etrk i{animation:k-grow-x .9s var(--ease) .35s both}
.k-gauge{padding:40px 0 0}
.k-gtrack{position:relative;height:10px;border-radius:5px;background:var(--navy-10)}
.k-gzone{position:absolute;top:0;bottom:0;border-radius:5px;transform-origin:left;
 background:repeating-linear-gradient(135deg,rgba(192,57,43,.30) 0 5px,rgba(192,57,43,.12) 5px 10px)}
.k-gzone.orange{background:repeating-linear-gradient(135deg,rgba(242,145,0,.36) 0 5px,rgba(242,145,0,.14) 5px 10px)}
.k-gzone.teal{background:repeating-linear-gradient(135deg,rgba(77,154,170,.40) 0 5px,rgba(77,154,170,.15) 5px 10px)}
.k-gzone.navy,.k-gzone.gray{background:repeating-linear-gradient(135deg,rgba(2,36,108,.25) 0 5px,rgba(2,36,108,.10) 5px 10px)}
.k-gmark{position:absolute;top:-7px;width:3px;height:24px;margin-left:-1.5px;border-radius:2px;background:var(--navy)}
.k-gmark.teal{background:var(--teal-ink)}.k-gmark.orange{background:var(--orange)}.k-gmark.red{background:var(--red)}
.k-gmark b{position:absolute;bottom:30px;left:50%;transform:translateX(-50%);font-size:var(--k-md);font-weight:700;white-space:nowrap;color:var(--navy)}
.k-gmark.teal b{color:var(--teal-ink)}.k-gmark.orange b{color:var(--orange-ink)}.k-gmark.red b{color:var(--red)}
.k-gends{display:flex;justify-content:space-between;margin-top:10px}
.sl.is-current .k-gauge:not([data-s] .k-gauge) .k-gmark,.sl.is-current [data-s].is-shown .k-gauge .k-gmark{animation:k-pop .5s var(--ease) calc(.3s + var(--i) * .2s) both}
.sl.is-current .k-gauge:not([data-s] .k-gauge) .k-gzone,.sl.is-current [data-s].is-shown .k-gauge .k-gzone{animation:k-grow-x .7s var(--ease) .8s both}
.k-units{display:grid;gap:12px}
.k-usq{display:flex;flex-wrap:wrap;gap:4px}
.k-usq i,.k-ulegend i{width:var(--u,16px);height:var(--u,16px);border-radius:3px;background:#D5DAE3;display:inline-block}
.k-ulegend{display:flex;flex-wrap:wrap;gap:20px}.k-ulegend span{display:inline-flex;align-items:center;gap:8px}.k-ulegend i{width:12px;height:12px}
.k-units i.navy{background:var(--navy)}.k-units i.teal{background:var(--teal)}.k-units i.orange{background:var(--orange)}.k-units i.red{background:var(--red)}
.sl.is-current .k-units:not([data-s] .k-units) .k-usq i,.sl.is-current [data-s].is-shown .k-units .k-usq i{animation:k-pop .3s var(--ease) calc(.2s + var(--i) * 18ms) both}
.k-bub{display:inline-grid;place-items:center;border-radius:50%;font-family:inherit;font-size:12px;font-weight:700;color:#fff;background:var(--navy);border:0;
 width:calc(20px + var(--n) * 1.6px);height:calc(20px + var(--n) * 1.6px);vertical-align:middle}
.k-bub.teal{background:var(--teal-ink)}.k-bub.orange{background:var(--orange)}.k-bub.red{background:var(--red)}.k-bub.gray{background:#8A93A3}
.k-bub.nil{background:#fff;color:#8A93A3;border:1px dashed #C4C9D2}
.sl.is-current .k-bub:not([data-s] .k-bub){animation:k-pop .4s var(--ease) .2s both}

/* ── proof rail and braced identity ── */
.k-proof{position:relative;display:grid;gap:12px}
.k-proof::before{content:'';position:absolute;left:17px;top:18px;bottom:18px;width:2px;background:var(--navy-15)}
.k-prow{position:relative;display:grid;grid-template-columns:36px 1fr;gap:18px;align-items:center}
.k-pn{width:36px;height:36px;border-radius:50%;display:grid;place-items:center;z-index:1;background:#fff;border:2px solid var(--navy);
 font-size:var(--k-xs);font-weight:700;color:var(--navy)}
.k-pbox{display:flex;align-items:center;justify-content:space-between;gap:24px;min-height:54px;padding:6px 20px;border-radius:8px;
 border:1px solid var(--line);background:#fff;font-size:var(--k-lg);color:var(--navy)}
.k-why{text-align:right}
.k-prow.wrong .k-pbox{background:var(--red-10);border-color:var(--red-25);color:var(--red)}.k-prow.wrong .k-why{color:var(--red)}
.k-prow.wrong .k-pn{border-color:var(--red);color:var(--red)}
.k-prow.key .k-pbox{background:var(--teal-10);border-color:var(--teal-25);color:var(--teal-ink)}.k-prow.key .k-why{color:var(--teal-ink)}
.k-prow.key .k-pn{border-color:var(--teal-ink);color:var(--teal-ink)}
.k-brace{display:inline-grid;justify-items:center;gap:5px;color:var(--navy);vertical-align:top}
.k-bx{font-size:var(--k-lg);white-space:nowrap;padding:1px 6px;border-radius:5px;background:var(--navy-10)}
.k-bb{width:100%;height:9px;border:2px solid currentColor;border-top:0;border-radius:0 0 9px 9px}
.k-bl{color:inherit}
.k-brace.teal{color:var(--teal-ink)}.k-brace.teal .k-bx{background:var(--teal-10)}
.k-brace.red{color:var(--red)}.k-brace.red .k-bx{background:var(--red-10)}
.k-brace.orange{color:var(--orange-ink)}.k-brace.orange .k-bx{background:var(--orange-10)}
.k-brace.gray{color:#6B7688}.k-brace.gray .k-bx{background:var(--gray-10)}
.sl.is-current .k-brace:not([data-s] .k-brace) .k-bb,.sl.is-current [data-s].is-shown .k-brace .k-bb{animation:k-grow-x .5s var(--ease) .3s both}
.sl.is-current .k-brace:not([data-s] .k-brace) .k-bl,.sl.is-current [data-s].is-shown .k-brace .k-bl{animation:k-appear .3s .6s both}

/* ── mirror comparison, selector ── */
.k-vs{font-size:var(--k-sm);line-height:1.3}
.k-vhead,.k-vrow{display:grid;grid-template-columns:1fr 170px 1fr;align-items:center;column-gap:24px}
.k-vhead{padding-bottom:12px}
.k-vhead>div{display:flex;align-items:center;gap:10px;font-size:var(--k-lg);font-weight:600}
.k-vhead .l{justify-content:flex-end}
.k-vhead .navy{color:var(--navy)}.k-vhead .teal{color:var(--teal-ink)}.k-vhead .orange{color:var(--orange-ink)}.k-vhead .red{color:var(--red)}.k-vhead .gray{color:#6B7688}
.k-vhead .ico{width:26px;height:26px}
.k-vrow{border-top:1px solid var(--line);padding:11px 0}
.k-vrow:last-child{border-bottom:1px solid var(--line)}
.k-vrow .l{text-align:right}
.k-vrow .m{text-align:center}
.k-select{position:relative;display:grid;gap:4px}
.k-select>span{position:relative;z-index:1;height:38px;display:flex;align-items:center;padding:0 12px;border-radius:6px;font-size:var(--k-sm);color:#6B7688;white-space:nowrap}
.k-select>span.on{color:#fff;font-weight:600}
.k-shl{position:absolute;left:0;right:0;height:38px;top:calc(var(--sel) * 42px);border-radius:6px;background:var(--navy)}
.k-select.teal .k-shl{background:var(--teal-ink)}.k-select.orange .k-shl{background:var(--orange)}.k-select.red .k-shl{background:var(--red)}
.sl.is-current .k-select:not([data-s] .k-select) .k-shl,.sl.is-current [data-s].is-shown .k-select .k-shl{animation:k-slide-hl .75s var(--ease) .35s both}

/* ── chat replica ── */
.k-chat{position:relative;display:flex;flex-direction:column;overflow:hidden;background:#F3F4F7;border:1px solid #DEE2E8;border-radius:12px;
 box-shadow:0 22px 44px -24px rgba(10,40,100,.35);color:#111827;text-align:left}
.k-chat .cw-bar{display:flex;align-items:center;gap:6px;height:28px;flex:none;padding:0 12px;background:#fff;border-bottom:1px solid #E6E9EE}
.k-chat .cw-bar i{width:9px;height:9px;border-radius:50%;background:#E1E4EA}
.k-chat .cw-bar span{margin-left:auto;font-family:var(--mono);font-size:10px;letter-spacing:.14em;text-transform:uppercase;color:#8A93A3}
.k-chat .cw-body{flex:1;min-height:0;padding:14px 16px;display:flex;flex-direction:column;gap:8px;background:#FAFBFC}
.k-chat .cw-user{align-self:flex-end;max-width:86%;background:var(--cw-user,var(--navy));color:#fff;font-size:17px;line-height:1.4;padding:8px 14px;border-radius:14px}
.k-chat .cw-row{position:relative;display:flex;gap:9px;align-items:flex-start;margin-top:4px}
.k-chat .cw-av{display:grid;place-items:center;flex:none;width:26px;height:26px;margin-top:2px;border-radius:50%;background:var(--navy-90);color:#fff;
 font-size:9.5px;font-weight:700}
.k-chat .cw-ai{background:#fff;border:1px solid #E5E7EB;border-radius:14px;padding:11px 16px;font-size:17px;line-height:1.45}
.k-chat .cw-ai p{margin:0 0 5px}
.k-chat .cw-typing{position:absolute;left:35px;top:0;display:flex;gap:4px;padding:10px 13px;background:#fff;border:1px solid #E5E7EB;border-radius:14px;opacity:0}
.k-chat .cw-typing i{width:6px;height:6px;border-radius:50%;background:#9CA3AF}
.k-flag{background:rgba(242,145,0,.24);box-shadow:inset 0 -2px 0 var(--orange);border-radius:2px}
.sl.is-current[data-step="0"] .k-chat.replay .cw-user{animation:k-pop .45s var(--ease) .45s both}
.sl.is-current[data-step="0"] .k-chat.replay .cw-typing{animation:k-typing 1.35s linear .95s both}
.sl.is-current .k-chat.replay .cw-typing i{animation:k-blink .9s infinite}
.sl.is-current .k-chat.replay .cw-typing i:nth-child(2){animation-delay:.15s}
.sl.is-current .k-chat.replay .cw-typing i:nth-child(3){animation-delay:.3s}
.sl.is-current[data-step="0"] .k-chat.replay .cw-av{animation:k-appear .3s .95s both}
.sl.is-current[data-step="0"] .k-chat.replay .cw-ai{animation:k-appear .15s 2.25s both,k-stream 1.5s cubic-bezier(.45,.05,.55,.95) 2.25s both}

/* ── to-scale timeline ── */
.k-ms{position:relative;height:118px;margin:0 var(--pad)}
.k-mline,.k-mfill{position:absolute;left:0;top:34px;height:4px;border-radius:2px}
.k-mline{right:0;background:var(--navy-10)}
.k-mfill{background:var(--navy);transform-origin:left}
.sl.is-current .k-mfill{animation:k-grow-x 1s var(--ease) .3s both}
.k-mnow{position:absolute;top:30px;width:12px;height:12px;margin-left:-6px;border-radius:50%;background:var(--navy);z-index:2}
.sl.is-current .k-mnow{animation:k-ring 1.4s var(--ease) 1.2s 3}
/* rows fixed so the dot centre lands on the line centre: 22 px date + 6 px gap + 16 px dot / 2 = 36 = 34 + 4 / 2 */
.k-mi{position:absolute;top:0;transform:translateX(-50%);display:grid;grid-template-rows:22px 16px auto;justify-items:center;gap:6px;text-align:center}
.k-mi .d{align-self:end;white-space:nowrap;line-height:1}
.k-mi i{width:16px;height:16px;border-radius:50%;background:#fff;border:3px solid var(--navy);box-sizing:border-box}
.k-mi b{font-size:var(--k-md);font-weight:600;color:var(--navy);white-space:nowrap;line-height:1.2}
.k-mi span:last-child{white-space:nowrap;margin-top:-4px}
.k-mi.done i{background:var(--navy)}
.k-mi.key i{width:22px;height:22px;margin-top:-3px;background:var(--orange);border-color:var(--orange)}
.k-mi.key b{color:var(--orange-ink)}
.k-cd b{font-variant-numeric:tabular-nums;color:var(--navy)}

/* ── model figure ── */
.k-model{position:relative}
.k-lane{position:absolute;top:0;text-align:center;color:var(--navy);font-weight:600}
.k-lane span{display:block;font-family:inherit;letter-spacing:0;text-transform:none;font-size:12.5px;color:#6B7688;font-weight:400;margin-top:2px}
.k-edges{position:absolute;left:0;top:0;overflow:visible;pointer-events:none}
.k-e .k-ep{fill:none;stroke:var(--navy-50);stroke-width:2}
.k-e .k-eh{fill:var(--navy-50);stroke:none}
.k-e.pos .k-ep{stroke:var(--teal-ink)}.k-e.pos .k-eh{fill:var(--teal-ink)}
.k-e.neg .k-ep{stroke:var(--orange)}.k-e.neg .k-eh{fill:var(--orange)}
.k-e.ind .k-ep{stroke:var(--navy)}.k-e.ind .k-eh{fill:var(--navy)}
.k-e.mod .k-ep{stroke:#8A93A3;stroke-dasharray:6 5}.k-e.mod .k-eh{fill:#8A93A3}
.k-e .k-ep{stroke-dasharray:1;stroke-dashoffset:0}
.k-e.mod .k-ep{stroke-dasharray:6 5}
.sl.is-current .k-e.draw.is-shown .k-ep{animation:k-draw .6s var(--ease) both}
.sl.is-current .k-e.draw.is-shown .k-eh{animation:k-appear .15s .55s both}
.k-node{position:absolute;display:grid;place-items:center;text-align:center;padding:6px 12px;border-radius:8px;
 font-size:17px;font-weight:600;line-height:1.22;color:var(--navy);background:var(--navy-10);border:1px solid var(--navy-15)}
.k-node small{display:block;font-weight:400;font-size:12.5px;color:#6B7688;margin-top:3px}
.k-node.teal{background:var(--teal-10);border-color:var(--teal-25);color:var(--teal-ink)}
.k-node.orange{background:var(--orange-10);border-color:#F8D9A8;color:var(--orange-ink)}
.k-node.red{background:var(--red-10);border-color:var(--red-25);color:var(--red)}
.k-node.gray{background:var(--gray-10);border-color:#DDE1E7;color:#5B6576}
.k-node.solid{background:var(--navy);border-color:var(--navy);color:#fff}.k-node.solid small{color:rgba(255,255,255,.75)}
.k-etag{position:absolute;transform:translate(-50%,-50%);white-space:nowrap;background:#fff;padding:0 5px;font-size:12px;font-weight:700;
 letter-spacing:.04em;color:var(--navy);line-height:1.3;z-index:2}
.k-etag.pos{color:var(--teal-ink)}.k-etag.neg{color:var(--orange-ink)}.k-etag.mod,.k-etag.plain{color:#6B7688}
.k-mlegend{position:absolute;left:0;bottom:0}

/* ── instruments ── */
.k-lab{display:grid;grid-template-columns:1fr var(--rw);gap:26px;height:100%}
.k-lfig{position:relative;background:#fff;border:1px solid var(--line);border-radius:8px;padding:12px;display:grid;gap:8px;align-content:start}
.k-lfig canvas{display:block;border-radius:6px;background:var(--navy-5)}
.k-rack{display:grid;gap:16px;align-content:start}
body.look-uni .k-rack{gap:10px}
body.look-uni .k-lab{height:calc(100% - 8px)}   /* keep the figure box's bottom border inside the cropping body */   /* the uni body box is shorter; keep the last row of controls clear of its edge */
.k-ctl{display:grid;gap:6px}
.k-ctop{display:flex;align-items:baseline;justify-content:space-between;gap:10px}
.k-cval{font-size:var(--k-md);font-weight:700;color:var(--navy);font-variant-numeric:tabular-nums}
.k-note{font-size:var(--k-xs);color:#4A5568;line-height:1.4;margin:0}
.k-presets{display:flex;flex-wrap:wrap;gap:6px}
.k-preset{font:inherit;font-size:12px;font-weight:600;padding:4px 11px;border-radius:999px;cursor:pointer;border:1px solid var(--line);background:#fff;color:#4A5568}
.k-preset.lit,.k-preset:hover{background:var(--navy);border-color:var(--navy);color:#fff}
.k-ctl input[type=range]{-webkit-appearance:none;appearance:none;width:100%;height:22px;background:transparent;cursor:grab;margin:0}
.k-ctl input[type=range]::-webkit-slider-runnable-track{height:5px;border-radius:3px;background:var(--navy-15)}
.k-ctl input[type=range]::-webkit-slider-thumb{-webkit-appearance:none;appearance:none;width:19px;height:19px;margin-top:-7px;border-radius:50%;
 background:var(--navy);border:3px solid #fff;box-shadow:0 1px 5px rgba(2,36,108,.4)}
.k-ctl input[type=range]::-moz-range-track{height:5px;border-radius:3px;background:var(--navy-15)}
.k-ctl input[type=range]::-moz-range-thumb{width:13px;height:13px;border-radius:50%;background:var(--navy);border:3px solid #fff}
.k-readout{display:grid;grid-template-columns:repeat(var(--n),1fr);gap:12px;padding:12px 14px;background:var(--navy-5);border:1px solid var(--navy-15);border-radius:8px}
.k-rc{display:grid;gap:2px}
.k-rv{font-size:24px;font-weight:700;line-height:1.15;color:var(--navy);font-variant-numeric:tabular-nums;display:inline-block}
.k-rv.bump{animation:k-bump .42s var(--ease)}
.k-btn{all:unset;box-sizing:border-box;cursor:pointer;display:inline-flex;align-items:center;gap:7px;padding:8px 16px;border-radius:7px;
 background:var(--navy-10);color:var(--navy);font-size:var(--k-xs);font-weight:600}
.k-btn.primary{background:var(--navy);color:#fff}

/* ── data table: <table class="k-table">; rows that build in keep their rules (separate borders fade with the cells) ── */
table.k-table{width:100%;border-collapse:separate;border-spacing:0;font-size:var(--k-sm);line-height:1.3;color:#1B2740}
table.k-table th{text-align:left;padding:0 16px 9px 0;font-family:var(--mono);font-size:var(--k-mi);letter-spacing:.14em;text-transform:uppercase;
 color:#6B7688;font-weight:400;border-bottom:1px solid var(--navy-15)}
table.k-table td{padding:11px 16px 11px 0;border-bottom:1px solid var(--line);vertical-align:middle}
table.k-table tr:last-child td{border-bottom:0}

/* ── provenance line ── */
.prov{white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.uw-fl>.prov{flex:0 1 auto;max-width:50%;margin-left:auto;height:23px;line-height:23px;text-align:right;color:#6B7688}   /* in the footer line, left of the page tab: up to half of it */
body.look-beamer .trk~.uw-fl>.prov{max-width:300px}   /* beamer: the tracker holds the footer line up to x 834 */
"""

# ── JS ───────────────────────────────────────────────────────────────────

JS = r"""
(function(){
 'use strict';
 const calm=!!(window.matchMedia&&matchMedia('(prefers-reduced-motion: reduce)').matches);
 const slideOf=el=>el.closest('.sl');
 /* ── data-k: hovering or focusing one element lights every element on the slide that shares its key ── */
 function light(el,on){const s=slideOf(el); if(!s)return; const k=el.getAttribute('data-k');
  s.querySelectorAll('[data-k]').forEach(x=>{if(x.getAttribute('data-k')===k)x.classList.toggle('lit',on)});
  s.classList.toggle('k-lighting',on)}
 ['mouseover','focusin'].forEach(t=>document.addEventListener(t,e=>{const el=e.target.closest&&e.target.closest('[data-k]'); if(el)light(el,true)}));
 ['mouseout','focusout'].forEach(t=>document.addEventListener(t,e=>{const el=e.target.closest&&e.target.closest('[data-k]');
  if(el&&!(e.relatedTarget&&el.contains(e.relatedTarget)))light(el,false)}));
 /* ── data-pop: a popover inside the slide, below the button (above near the foot); Esc, a click elsewhere or a slide change closes ── */
 let pop=null,popFor=null;
 function closePop(){if(pop){pop.remove();pop=null;popFor=null}}
 document.addEventListener('click',e=>{
  const set=e.target.closest&&e.target.closest('[data-kit-set]');
  if(set){const [sel,val]=set.getAttribute('data-kit-set').split('=');
   const s=slideOf(set); const inp=(s&&s.querySelector(sel))||document.querySelector(sel);
   if(inp){inp.value=val;inp.dispatchEvent(new Event('input',{bubbles:true}));inp.dispatchEvent(new Event('change',{bubbles:true}))}
   set.parentNode.querySelectorAll('[data-kit-set]').forEach(c=>c.classList.toggle('lit',c===set))}
  const el=e.target.closest&&e.target.closest('[data-pop]');
  if(pop&&pop.contains(e.target))return;
  if(pop&&(!el||el===popFor)){closePop();return}
  if(!el)return;
  closePop(); const host=slideOf(el); if(!host)return;
  pop=document.createElement('div'); pop.className='k-popover'; pop.innerHTML=el.getAttribute('data-pop');
  host.appendChild(pop); popFor=el;
  const hr=host.getBoundingClientRect(), r=el.getBoundingClientRect(), k=hr.width/1280||1;
  let x=(r.left-hr.left)/k, y=(r.bottom-hr.top)/k+8; const w=pop.offsetWidth, h=pop.offsetHeight;
  if(y+h>630)y=(r.top-hr.top)/k-h-8;
  pop.style.left=Math.max(40,Math.min(1240-w,x))+'px'; pop.style.top=Math.max(40,y)+'px';
 });
 document.addEventListener('keydown',e=>{if(e.key==='Escape')closePop()},true);
 document.addEventListener('d3paint',e=>{if(e.detail.prev!==e.detail.cur)closePop()});
 /* ── sliders show their value; data-fmt int | pct | 1 | 2 ── */
 function fmt(v,f){if(f==='pct')return Math.round(v*100)+'\u00a0%'; if(f==='1'||f==='2')return v.toFixed(+f); return Math.round(v).toLocaleString('en-US')}
 function showVal(inp){const o=document.getElementById(inp.id+'-val'); if(o)o.textContent=fmt(inp.valueAsNumber,inp.dataset.fmt)}
 document.querySelectorAll('.k-ctl input[type=range]').forEach(showVal);
 document.addEventListener('input',e=>{if(e.target.matches&&e.target.matches('.k-ctl input[type=range]'))showVal(e.target)});
 /* ── to-scale timelines and countdowns follow the real date ── */
 const DAY=864e5, utc=s=>{const p=s.split('-').map(Number);return Date.UTC(p[0],p[1]-1,p[2])};
 const now=new Date(), today=Date.UTC(now.getFullYear(),now.getMonth(),now.getDate());
 document.querySelectorAll('.k-ms[data-start]').forEach(t=>{const a=utc(t.dataset.start), b=utc(t.dataset.end);
  const p=Math.max(0,Math.min(100,(today-a)/(b-a)*100)).toFixed(2)+'%';
  const d=t.querySelector('.k-mnow'), f=t.querySelector('.k-mfill'); if(d)d.style.left=p; if(f)f.style.width=p});
 document.querySelectorAll('.k-cd[data-date]').forEach(c=>{const n=Math.round((utc(c.dataset.date)-today)/DAY);
  const b=c.querySelector('b'), s=c.querySelector('span'); if(!b||!s)return;
  if(n>=0){b.textContent=n; s.textContent=(n===1?'day ':'days ')+c.dataset.what}
  else {b.textContent='–'; s.textContent='passed'}});
 /* ── live modules: D3Deck.live(el, {setup, enter, leave, step, frame}) ──
    setup(el) once at boot (paint a still: print and previews show it); enter(el) when its slide comes on screen;
    leave(el) when it goes (stop, reset to the still); step(el, n) on every step change, n 0-based, also right after
    enter; frame(el, dt) every animation frame while its slide is on screen, dt in ms. */
 const mods=[]; let raf=0, last=0, lastSt=-1, lastCur=-1;
 function tick(ts){raf=0; const dt=last?Math.min(ts-last,100):16; last=ts; let any=false;
  mods.forEach(m=>{if(m.on&&m.mod.frame){any=true; try{m.mod.frame(m.el,dt)}catch(err){console.error(err)}}});
  if(any&&!document.hidden)raf=requestAnimationFrame(tick); else last=0}
 function sync(){const s=SL[cur];
  mods.forEach(m=>{const here=m.slide===s;
   try{
    if(here&&!m.on){m.on=true; m.mod.enter&&m.mod.enter(m.el); m.mod.step&&m.mod.step(m.el,st)}
    else if(!here&&m.on){m.on=false; m.mod.leave&&m.mod.leave(m.el)}
    else if(here&&(st!==lastSt||cur!==lastCur)){m.mod.step&&m.mod.step(m.el,st)}
   }catch(err){console.error(err)}});
  lastSt=st; lastCur=cur;
  if(!raf&&mods.some(m=>m.on&&m.mod.frame))raf=requestAnimationFrame(tick)}
 document.addEventListener('d3paint',sync);
 document.addEventListener('visibilitychange',()=>{if(!document.hidden)sync()});
 let seedN=1;
 window.D3Deck=Object.assign(window.D3Deck||{},{
  calm:calm,
  live(target,mod){const el=typeof target==='string'?document.querySelector(target):target;
   if(!el){console.error('D3Deck.live: no element '+target);return}
   const slide=slideOf(el); if(!slide){console.error('D3Deck.live: element is not on a slide');return}
   const m={el,slide,mod,on:false}; mods.push(m);
   try{mod.setup&&mod.setup(el)}catch(err){console.error(err)}
   sync()},
  /* deterministic random numbers: the run on stage is the run you rehearsed */
  rng(seed){let a=(seed===undefined?seedN++:seed)>>>0;
   return function(){a|=0;a=a+0x6D2B79F5|0;let t=Math.imul(a^a>>>15,1|a);t=t+Math.imul(t^t>>>7,61|t)^t;return((t^t>>>14)>>>0)/4294967296}},
  /* a crisp canvas: CSS size w x h, backing store at device resolution; returns the 2d context */
  canvas(cv,w,h){const r=Math.max(2,window.devicePixelRatio||1); cv.width=w*r; cv.height=h*r; cv.style.width=w+'px'; cv.style.height=h+'px';
   const c=cv.getContext('2d'); c.setTransform(r,0,0,r,0,0); return c},
  /* set a readout value; it flashes once when it changes */
  set(id,text){const el=document.getElementById(id); if(!el)return; const t=String(text); if(el.textContent===t)return;
   el.textContent=t; el.classList.remove('bump'); void el.offsetWidth; el.classList.add('bump')},
  ease:t=>t<.5?2*t*t:1-Math.pow(-2*t+2,2)/2,
  clamp:(v,lo,hi)=>Math.max(lo,Math.min(hi,v))});
})();
"""
