# -*- coding: utf-8 -*-
"""The D3 frame, rebuilt from the Beamer template PDFs.

All geometry is in px on the 1280x720 canvas. The template PDFs are
959.76x540 pt; rendered at 96 dpi they are exactly 1280x720, and the numbers
below were measured on those renders (navy pixel bounding boxes) or converted
from the logo rectangles in assets/logos/build_templates.py at 1280/959.76.
Text anchors are the Beamer fractions of the paper size from d3-beamer.sty.
"""
import base64
import os
import re

from . import paths

UNI_SVG = 'Universitaet_Wuerzburg_Logo.svg'
D3_SVG = 'DataDrivenDecisions_2c.svg'
SEAL = os.path.join(paths.PKG, 'seal.png')

_cache = {}
_n = [0]


def inline_svg(path):
    """Inline a kit SVG: drop the XML prolog, comments, <text>, <metadata> and editor
    attributes, give class names a unique prefix, make sure there is a viewBox, and
    let CSS size it."""
    with open(path, encoding='utf-8') as fh:
        raw = fh.read()
    raw = re.sub(r'<\?xml[^>]*\?>', '', raw)
    raw = re.sub(r'<!--.*?-->', '', raw, flags=re.S)
    raw = re.sub(r'<text\b.*?</text>', '', raw, flags=re.S)
    raw = re.sub(r'<metadata\b.*?</metadata>', '', raw, flags=re.S)
    raw = re.sub(r'\s(?:id|inkscape:[\w-]+|sodipodi:[\w-]+)=(?:"[^"]*"|\'[^\']*\')', '', raw)
    _n[0] += 1
    raw = re.sub(r'\bcls-(\d+)\b', lambda m: f'd3l{_n[0]}-{m.group(1)}', raw)
    head = re.search(r'<svg\b[^>]*>', raw, re.S).group(0)
    new = head
    if 'viewBox' not in new:
        w = re.search(r'\swidth=["\']([\d.]+)', new).group(1)
        h = re.search(r'\sheight=["\']([\d.]+)', new).group(1)
        new = new.replace('<svg', f'<svg viewBox="0 0 {w} {h}"', 1)
    new = re.sub(r'\s(?:width|height)=(?:"[^"]*"|\'[^\']*\')', '', new)
    new = new.replace('<svg', '<svg preserveAspectRatio="xMinYMin meet"', 1)
    return raw.replace(head, new, 1).strip()


def _logo(name):
    if name not in _cache:
        _cache[name] = inline_svg(os.path.join(paths.asset_dir('logos'), name))
    return _cache[name]


def seal_uri():
    if 'seal' not in _cache:
        with open(SEAL, 'rb') as fh:
            _cache['seal'] = 'data:image/png;base64,' + base64.b64encode(fh.read()).decode()
    return _cache['seal']


def content_frame(title, inner, page='', foot='', tracker='', dots=''):
    """Slide_template look: uni logo, navy bar, page tab, D3 logo, number, footer, title, body."""
    parts = [f'<div class="fr-uni">{_logo(UNI_SVG)}</div>', '<div class="fr-bar"></div>',
             '<div class="fr-tab"></div>', f'<div class="fr-d3">{_logo(D3_SVG)}</div>']
    if page:
        parts.append(f'<div class="fr-num">{page}</div>')
    if foot:
        parts.append(f'<div class="fr-foot">{foot}</div>')
    if tracker:
        parts.append(tracker)
    if title:
        parts.append(f'<div class="fr-title">{title}</div>')
    parts.append(inner)
    parts.append(dots)
    return ''.join(parts)


def title_frame(inner):
    """Title_template look: uni logo, left navy bar, large D3 logo, seal watermark."""
    return (f'<div class="fr-uni">{_logo(UNI_SVG)}</div><div class="fr-tbar"></div>'
            f'<div class="fr-d3t">{_logo(D3_SVG)}</div><img class="fr-seal" src="{seal_uri()}" alt="">{inner}')


def title_inner(title, subtitle=''):
    h = f'<div class="fr-ttitle">{title}</div>'
    if subtitle:
        h += f'<div class="fr-tsub">{subtitle}</div>'
    return h


def thankyou_inner(name):
    return f'<div class="fr-ttitle" style="top:288px">Thank You!</div><div class="fr-tname">{name}</div>'


def agenda_list(sections, current=None, links=None):
    """Numbered circles and names at the Beamer anchors. current: 1-based highlighted
    item (None = all navy). links: {1-based n: mark name} for clickable items."""
    n = len(sections)
    start = 360 - (n - 1) * 32.4
    out = []
    for i, name in enumerate(sections):
        k = i + 1
        y = start + i * 64.8
        off = ' off' if (current is not None and k != current) else ''
        j = f' data-jump="@@{links[k]}@@"' if links and k in links else ''
        out.append(f'<div class="ag{off}" style="top:{y - 28:.1f}px">'
                   f'<div class="agn"{j}>{k}</div><div class="agt"{j}>{name}</div></div>')
    return ''.join(out)


def tracker(sections, current):
    """Section tracker for the footer band. current is 0-based."""
    items = []
    for i, name in enumerate(sections):
        c = ' cur' if i == current else (' done' if i < current else '')
        items.append(f'<div class="ti{c}">{name}</div>')
    return '<div class="trk">' + ''.join(items) + '</div>'


CSS = r"""
/* ── Slide_template ── */
.fr-uni{position:absolute;left:45px;top:54px;width:173px;height:76px}
.fr-uni svg{width:100%;height:100%;display:block}
.fr-bar{position:absolute;left:1190px;top:54px;width:15px;height:75px;background:var(--bar)}
.fr-tab{position:absolute;left:45px;top:679px;width:79px;height:15px;background:var(--bar)}
.fr-d3{position:absolute;left:1054px;top:671px;width:151px;height:31px}
.fr-d3 svg{width:100%;height:100%;display:block}
.fr-num{position:absolute;left:73px;bottom:27px;color:#fff;font-size:var(--fs-tiny);line-height:1;z-index:2}
.fr-foot{position:absolute;left:147px;bottom:24px;color:#000;font-size:var(--fs-tiny);line-height:1;white-space:nowrap}
.fr-title{position:absolute;left:243px;top:65px;width:922px;font-size:var(--fs-Large);font-weight:700;line-height:1.15;color:var(--navy)}
.body{position:absolute;left:73px;top:173px;width:1133px;height:432px;overflow:hidden}
.col{position:absolute;top:173px;width:547px;height:432px;overflow:hidden}
.col.l{left:73px}
.col.r{left:653px}
.col.short{height:274px}
/* ── Title_template ── */
.fr-tbar{position:absolute;left:107px;top:190px;width:16px;height:224px;background:var(--bar)}
.fr-d3t{position:absolute;left:955px;top:61px;width:288px;height:58px}
.fr-d3t svg{width:100%;height:100%;display:block}
.fr-seal{position:absolute;left:882px;top:332px;width:398px;height:388px}
.fr-ttitle{position:absolute;left:173px;top:238px;width:934px;font-size:var(--fs-LARGE);font-weight:700;line-height:1.2;color:var(--navy)}
.fr-tsub{position:absolute;left:173px;top:360px;width:934px;font-size:var(--fs-large);color:var(--navy);line-height:1.3}
.fr-tname{position:absolute;left:173px;top:389px;width:934px;font-size:var(--fs-normal);color:var(--navy)}
/* ── agenda and section dividers ── */
.ag{position:absolute;left:151px;height:56px;display:flex;align-items:center}
.agn{width:56px;height:56px;border-radius:50%;background:var(--navy);color:#fff;font-weight:700;font-size:var(--fs-normal);
 display:flex;align-items:center;justify-content:center;flex:none}
.agt{margin-left:23px;font-weight:700;font-size:var(--fs-normal);color:var(--navy);white-space:nowrap}
.ag.off .agn{background:#B3B3B3}
.ag.off .agt{color:#808080}
/* ── section tracker (footer band, replaces the footer text) ── */
.trk{position:absolute;left:147px;top:676px;width:883px;height:22px;display:flex}
.trk .ti{flex:1;display:flex;align-items:center;padding:0 10px 0 18px;font-size:var(--fs-chrome);font-weight:600;white-space:nowrap;
 overflow:hidden;text-overflow:ellipsis;background:#F4F6F9;color:var(--gray);
 clip-path:polygon(0 0,calc(100% - 9px) 0,100% 50%,calc(100% - 9px) 100%,0 100%,9px 50%)}
.trk .ti:first-child{padding-left:10px;clip-path:polygon(0 0,calc(100% - 9px) 0,100% 50%,calc(100% - 9px) 100%,0 100%)}
.trk .ti+.ti{margin-left:-7px}
.trk .ti.done{background:var(--lightblue);color:var(--navy)}
.trk .ti.cur{background:var(--navy);color:#fff;z-index:3}
"""
