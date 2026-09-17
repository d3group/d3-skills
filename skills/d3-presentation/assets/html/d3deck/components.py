# -*- coding: utf-8 -*-
"""Fragment helpers: HTML strings composed inside slide bodies, plus their CSS.

Twins of the LaTeX template library: column headers, highlight, the three code
boxes, chevron process flows, the project timeline, the takeaway box. New for
HTML: stat cards, big numbers, step/scrim wrappers and breadcrumbs.
"""
import html as _html

TOKENS = {
    'navy': (21, 63, 135), 'orange': (242, 145, 0), 'gray': (128, 128, 128),
    'lightblue': (200, 220, 240), 'darkblue': (10, 40, 100), 'teal': (77, 154, 170),
    'yellow': (216, 222, 111), 'peach': (245, 200, 170), 'lavender': (197, 202, 233),
    'white': (255, 255, 255), 'black': (0, 0, 0),
}

ROW = 52   # timeline: px between work-package rows (LaTeX: 7mm)
BAR = 38   # timeline: bar height (LaTeX: 5mm)
AXIS = 30  # timeline: px reserved under the axis for year labels


def mix(spec):
    """'teal!60' -> 60% teal on white, like xcolor. 'teal' -> teal. '#hex' passes through. Besides the brand tokens, 'white' and 'black' are accepted for mixing."""
    if spec.startswith('#'):
        return spec
    name, _, pct = spec.partition('!')
    if name not in TOKENS:
        raise ValueError(f'unknown color token {name!r}; use one of {sorted(TOKENS)}')
    p = float(pct) / 100 if pct else 1.0
    r, g, b = (round(c * p + 255 * (1 - p)) for c in TOKENS[name])
    return f'#{r:02X}{g:02X}{b:02X}'


def esc(text):
    return _html.escape(text, quote=False)


def columnheader(text):
    return f'<div class="colhead">{text}</div>'


def highlight(text):
    return f'<b class="hl">{text}</b>'


def _pre(cls, code):
    body = esc(code.strip('\n'))
    return f'<pre class="{cls}">{body}</pre>'


def codebox(code):
    return _pre('code', code)


def errorbox(code):
    return _pre('code err', code)


def terminalbox(code):
    return _pre('code term', code)


def chevrons(active, phases):
    """Process flow. phases: 2 to 5 entries, each (label, title) or a title string. active is 1-based."""
    if not 2 <= len(phases) <= 5:
        raise ValueError('chevrons: give 2 to 5 phases')
    if not 1 <= active <= len(phases):
        raise ValueError(f'chevrons: active={active} is outside 1..{len(phases)}')
    out = ['<div class="chev">']
    for i, ph in enumerate(phases, 1):
        label, title = ('', ph) if isinstance(ph, str) else (ph[0], ph[1])
        cur = ' cur' if i == active else ''
        out.append(f'<div class="c{cur}"><div class="cl">{label}</div><div class="ct">{title}</div></div>')
    out.append('</div>')
    return ''.join(out)


def timeline(start_year, end_year, packages):
    """Gantt timeline. packages: (label, color, start, end, row, milestone); start/end in 0..1, row 1 = bottom."""
    years = end_year - start_year
    if years < 1:
        raise ValueError('timeline: end_year must be after start_year')
    rows = 0
    for label, color, start, end, row, ms in packages:
        if not (0 <= start < end <= 1):
            raise ValueError(f'timeline: {label!r} needs 0 <= start < end <= 1')
        if not 1 <= row <= 12:
            raise ValueError(f'timeline: {label!r} row must be 1..12')
        rows = max(rows, row)
    height = AXIS + rows * ROW + 8
    parts = [f'<div class="tl" style="height:{height}px">']
    for i in range(years + 1):
        x = i / years * 100
        parts.append(f'<div class="tl-tick" style="left:{x:.2f}%"></div>'
                     f'<div class="tl-year" style="left:{x:.2f}%">{start_year + i}</div>')
    parts.append('<div class="tl-axis"></div>')
    for label, color, start, end, row, ms in packages:
        bottom = AXIS + (row - 1) * ROW + 8
        parts.append(f'<div class="tl-bar" style="left:{start * 100:.2f}%;width:{(end - start) * 100:.2f}%;'
                     f'bottom:{bottom}px;background:{mix(color)}"><span>{label}</span></div>')
        mid = bottom + BAR // 2
        parts.append(f'<div class="tl-ms" style="left:{end * 100:.2f}%;bottom:{mid}px"></div>'
                     f'<div class="tl-msl" style="left:{end * 100:.2f}%;bottom:{mid}px">{ms}</div>')
    parts.append('</div>')
    return ''.join(parts)


def takeaway(text):
    return f'<div class="take"><b class="tk">Key Takeaway:</b> {text}</div>'


def facts(items):
    out = []
    for it in items:
        acc = ' acc' if len(it) > 2 and it[2] else ''
        out.append(f'<div class="fact{acc}"><div class="fv">{it[0]}</div><div class="fk">{it[1]}</div></div>')
    return '<div class="facts">' + ''.join(out) + '</div>'


def stat(value, label, accent=False):
    o = ' o' if accent else ''
    return f'<div class="stat{o}"><div class="sv">{value}</div><div class="sk">{label}</div></div>'


def bignum(value, label):
    return f'<div class="bignum"><div class="bv">{value}</div><div class="bk">{label}</div></div>'


def step(n, html, soft=False, until=None, tag='div', cls=''):
    """Wrap html so it is ghosted until step n (0-based)."""
    attrs = f' data-s="{n}"'
    if soft:
        attrs += ' data-soft="1"'
    if until is not None:
        attrs += f' data-until="{until}"'
    if cls:
        attrs += f' class="{cls}"'
    return f'<{tag}{attrs}>{html}</{tag}>'


def _px(v):
    return f'{v}px' if isinstance(v, (int, float)) else str(v)


def scrim(off, left, top, right, bottom):
    """A 69.97% white cover over a region of the slide, lifted at step `off`."""
    return (f'<div class="scrim" data-off="{off}" style="left:{_px(left)};top:{_px(top)};'
            f'right:{_px(right)};bottom:{_px(bottom)}"></div>')


def crumb(*items):
    """Breadcrumb for backup slides: items are (text, markname or None); the hub comes first."""
    parts = ['<span class="cstep" data-jump="@@bhome@@">Backup</span>']
    for i, (text, m) in enumerate(items):
        last = i == len(items) - 1
        attr = '' if (m is None or last) else f' data-jump="@@{m}@@"'
        cls = 'cstep cur' if last else 'cstep'
        parts.append(f'<span class="{cls}"{attr}>{text}</span>')
    return '<div class="crumb">' + '<span class="csep">/</span>'.join(parts) + '</div>'


CSS = r"""
.colhead{font-size:var(--fs-normal);font-weight:700;color:var(--navy);margin-bottom:8px}
.hl{color:var(--orange);font-weight:700}
pre.code{font-family:var(--mono);font-size:var(--fs-script);line-height:1.4;white-space:pre;overflow:hidden;
 background:var(--navy-5);border:1.4px solid var(--navy-50);border-radius:6px;padding:8px 12px;margin:10px 0;color:var(--navy)}
pre.code.err{background:#FFF2F2;border-color:#FF8080}
pre.code.term{background:var(--navy-90);border-color:var(--navy);color:#fff}
.chev{display:flex;gap:8px;width:100%;margin:10px 0}
.chev .c{flex:1;height:78px;display:flex;flex-direction:column;justify-content:center;align-items:center;text-align:center;
 padding:0 34px 0 44px;background:var(--navy-15);color:var(--navy);
 clip-path:polygon(0 0,calc(100% - 22px) 0,100% 50%,calc(100% - 22px) 100%,0 100%,22px 50%)}
.chev .c:first-child{clip-path:polygon(0 0,calc(100% - 22px) 0,100% 50%,calc(100% - 22px) 100%,0 100%);padding-left:30px}
.chev .c.cur{background:var(--navy);color:#fff}
.chev .cl{font-size:var(--fs-tiny);line-height:1.2}
.chev .ct{font-size:var(--fs-footnote);font-weight:700;line-height:1.2}
.tl{position:relative;width:92%;margin:0 auto}
.tl-axis{position:absolute;left:0;right:0;bottom:30px;height:2px;background:var(--navy)}
.tl-tick{position:absolute;bottom:26px;width:2px;height:10px;background:var(--navy);transform:translateX(-50%)}
.tl-year{position:absolute;bottom:4px;transform:translateX(-50%);font-size:var(--fs-tiny);color:var(--navy)}
.tl-bar{position:absolute;height:38px;display:flex;align-items:center;padding-left:8px;font-size:var(--fs-tiny);
 font-weight:700;color:var(--navy);white-space:nowrap;overflow:hidden}
.tl-ms{position:absolute;width:12px;height:12px;background:var(--navy);transform:translate(-16px,50%) rotate(45deg)}
.tl-msl{position:absolute;transform:translate(6px,50%);font-size:var(--fs-tiny);color:var(--navy);line-height:1}
.take{background:var(--orange-5);border-left:4px solid var(--orange);padding:10px 14px;font-size:var(--fs-small);color:var(--navy)}
.take b{color:var(--orange)}
.fr-take{position:absolute;left:73px;top:475px;width:1114px}
.stat{border-radius:6px;padding:18px 22px;position:relative;overflow:hidden;background:var(--navy-5)}
.stat::before{content:'';position:absolute;left:0;top:0;bottom:0;width:5px;background:var(--lightblue)}
.stat.o{background:var(--orange-5)}.stat.o::before{background:var(--orange)}
.stat .sv{font-size:var(--fs-LARGE);font-weight:700;letter-spacing:-.02em;color:var(--navy);line-height:1}
.stat.o .sv{color:var(--orange)}
.stat .sk{font-size:var(--fs-footnote);color:var(--gray);margin-top:8px;line-height:1.3}
.bignum .bv{font-size:var(--fs-display);line-height:.9;font-weight:700;letter-spacing:-.04em;color:var(--navy);font-variant-numeric:tabular-nums}
.bignum .bk{font-size:var(--fs-normal);color:var(--gray);margin-top:18px;max-width:26ch}
.grid2{display:grid;grid-template-columns:1fr 1fr;gap:20px}
.grid3{display:grid;grid-template-columns:1fr 1fr 1fr;gap:20px}
.grid4{display:grid;grid-template-columns:repeat(4,1fr);gap:20px}
.fig{display:block;max-width:100%;max-height:100%}
.crumb{display:flex;align-items:center;gap:10px;font-size:var(--fs-tiny);letter-spacing:.06em;text-transform:uppercase;color:var(--gray);margin-bottom:14px}
.crumb .cstep[data-jump]:hover{color:var(--orange)}
.crumb .csep{color:var(--navy-15)}
.crumb .cur{color:var(--orange)}
"""
