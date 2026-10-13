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
UW_LOGO = {'navy': 'uw-logo-navy.png', 'white': 'uw-logo-white.png'}
UW_SEAL = 'uw-seal-coral.png'        # pre-coloured: CSS masks print with visible edges in Chrome's PDF output
UW_SEAL_FAINT = 'uw-seal-faint.png'  # navy at 12 % alpha, for the closing slide
UW_COVER = 'uw-cover.jpg'

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


def _data_uri(name):
    """A raster from the logos folder as a data URI (cached)."""
    if name not in _cache:
        mime = 'image/jpeg' if name.endswith('.jpg') else 'image/png'
        with open(os.path.join(paths.asset_dir('logos'), name), 'rb') as fh:
            _cache[name] = f'data:{mime};base64,' + base64.b64encode(fh.read()).decode()
    return _cache[name]


def content_frame(title, inner, page='', foot='', tracker='', dots='', prov=''):
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
    if prov:
        parts.append(f'<div class="prov">{prov}</div>')
    parts.append(dots)
    return ''.join(parts)


def klar_frame(title, inner, page='', foot='', tracker='', dots='', prov=''):
    """The 'klar' content frame: tracker on top, kicker and claim, a quiet mono foot with the D3 mark.
    No logos or bars compete with the content; the corporate frame stays on the title slide."""
    parts = [tracker or '']
    if title:
        parts.append(f'<div class="kf-title">{title}</div>')
    parts.append(inner)
    prov = f'<span class="prov">{prov}</span>' if prov else ''
    parts.append(f'<div class="kf-foot"><span class="kf-sec">{foot}</span>{prov}<span class="kf-num">{page}</span>'
                 f'<span class="kf-d3">{_logo(D3_SVG)}</span></div>')
    parts.append(dots)
    return ''.join(parts)


def klar_divider(n, sections, question, part):
    """The klar section divider: outlined part numeral, 'Part n of N', the question the part answers and, beside it,
    the part's slides (numbered, clickable), so the structure is visible without an agenda slide."""
    q = question or sections[n - 1]
    h = (f'<div class="secn" aria-hidden="true">{n:02d}</div>'
         f'<div class="secq{" has-part" if part else ""}"><div class="pt">Part {n} of {len(sections)} · {sections[n - 1]}</div>'
         f'<div class="stmt">{q}</div></div>')
    if part:
        rows = ''.join(f'<div class="spi" data-jump="{j}"><span class="spn">{num}</span><span>{c}</span></div>'
                       for j, num, c in part[:6])
        more = f'<div class="spm">and {len(part) - 6} more</div>' if len(part) > 6 else ''
        h += f'<div class="spart"><div class="sph">In this part</div>{rows}{more}</div>'
    return h


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


# ── look 'uni': the PowerPoint master of the University of Würzburg (PPT-Master-Universitaet-Wuerzburg.potx).
# Geometry comes from the slide layouts: the canvas is 12192000 EMU wide, so 1 px = 9525 EMU on 1280x720.

UNI_WORDS = {
    'en': dict(agenda='Agenda', part='Part {n} of {N}', thanks='Thank you', contact='Contact', refs='References'),
    'de': dict(agenda='Agenda', part='Teil {n} von {N}', thanks='Vielen Dank', contact='Kontakt', refs='Quellenangaben'),
}


def uni_words(lang):
    return UNI_WORDS.get((lang or 'en')[:2], UNI_WORDS['en'])


def uni_logo(color='navy'):
    return f'<div class="uw-logo uw-logo-{color}" role="img" aria-label="Universität Würzburg"></div>'


def _uw_seal(cls='uw-seal'):
    return f'<div class="{cls}"></div>'


def uni_assets_css(cover=False):
    """The rasters of the uni look as CSS backgrounds, so every image is embedded once, not once per slide."""
    css = (f'body.look-uni .uw-logo-navy{{background-image:url({_data_uri(UW_LOGO["navy"])})}}'
           f'body.look-uni .uw-logo-white{{background-image:url({_data_uri(UW_LOGO["white"])})}}'
           f'body.look-uni .uw-seal{{background-image:url({_data_uri(UW_SEAL)})}}'
           f'body.look-uni .uw-seal.uw-seal-end{{background-image:url({_data_uri(UW_SEAL_FAINT)})}}')
    if cover:
        css += f'body.look-uni .uw-photo{{background-image:url({_data_uri(UW_COVER)})}}'
    return css


def uni_frame(title, inner, page='', foot='', tracker='', dots='', prov=''):
    """Inhaltsfolie: logo top left over a hairline, title below, footer line bottom left, page number in a navy tab."""
    parts = [uni_logo(), '<div class="uw-rule"></div>', tracker or '']
    if title:
        parts.append(f'<div class="uw-title">{title}</div>')
    parts.append(inner)
    if prov:
        parts.append(f'<div class="prov">{prov}</div>')
    if foot:
        parts.append(f'<div class="uw-foot">{foot}</div>')
    if page:
        parts.append(f'<div class="uw-num">{page}</div>')
    parts.append(dots)
    return ''.join(parts)


def uni_title(title, subtitle='', presenter='', date='', cover='navy'):
    """Deckblatt. cover='navy' (all navy, seal), 'band' (white, navy band with the seal), 'photo' (Würzburg skyline)."""
    if cover not in ('navy', 'band', 'photo'):
        raise ValueError("cover must be 'navy', 'band' or 'photo'")
    who = ''.join(f'<div class="{c}">{t}</div>' for c, t in (('uw-tname', presenter), ('uw-tdate', date)) if t)
    lines = (f'<div class="uw-meta">' + (f'<div class="uw-tsub">{subtitle}</div>' if subtitle else '<div></div>')
             + f'<div class="uw-who">{who}</div></div>')
    h = f'<div class="uw-cover uw-c-{cover}">'
    if cover == 'photo':
        h += '<div class="uw-photo"></div><div class="uw-box"></div>'
    elif cover == 'band':
        h += '<div class="uw-band"></div>'
    h += uni_logo('navy' if cover == 'band' else 'white') + _uw_seal()
    return h + f'<div class="uw-ttitle"><span>{title}</span></div>{lines}</div>'


def uni_divider(n, sections, question, lang):
    """Trennseite: navy, white logo over a white hairline, the part number in sky blue, the part name, the question."""
    w = uni_words(lang)
    q = f'<div class="uw-sq">{question}</div>' if question else ''
    return (f'<div class="uw-dark">{uni_logo("white")}<div class="uw-rule"></div>{_uw_seal()}'
            f'<div class="uw-sk">{w["part"].format(n=n, N=len(sections))}</div>'
            f'<div class="uw-sn">{n:02d}</div><div class="uw-st">{sections[n - 1]}{q}</div></div>')


def uni_agenda(sections, links=None, lang='en'):
    """Agenda: two-digit numbers in sky blue, topics beside them, 60 px apart, as in the master."""
    rows = ''.join(f'<div class="uw-ag"><span class="uw-agn"{j}>{k:02d}</span><span class="uw-agt"{j}>{name}</span></div>'
                   for k, name in enumerate(sections, 1)
                   for j in [f' data-jump="@@{links[k]}@@"' if links and k in links else ''])
    return f'<div class="uw-title">{uni_words(lang)["agenda"]}</div><div class="uw-agl">{rows}</div>'


def uni_thankyou(text, contact, lang='en'):
    """Abschlussseite: thanks in navy, a navy contact box, grey right half with the seal."""
    w = uni_words(lang)
    rows = ''.join(f'<div>{c}</div>' for c in contact if c)
    return (f'<div class="uw-end"></div>{_uw_seal("uw-seal uw-seal-end")}<div class="uw-thx">{text or w["thanks"]}</div>'
            f'<div class="uw-box uw-contact"><b>{w["contact"]}</b>{rows}<div class="uw-web">uni-wuerzburg.de</div></div>')


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
/* ══ look 'klar': calm content slides (layout after N. Elbert's defense talk), D3 colours ══ */
body.look-klar .sl{color:#1B2740;font-size:22px;line-height:1.6;font-weight:400}
body.look-klar .trk{left:86px;top:40px;width:1108px;height:26px}
body.look-klar .trk .ti{font-size:11px;font-weight:600;letter-spacing:.01em}
body.look-klar .kf-title{position:absolute;left:86px;top:88px;width:1108px;font-size:34px;line-height:1.22;font-weight:400;letter-spacing:-.02em;color:var(--navy);text-wrap:balance}
body.look-klar .kf-title .kick{color:var(--orange);font-weight:500;margin-right:.28em}
body.look-klar .kf-title .sub{display:block;font-size:17px;line-height:1.5;color:#4A5568;letter-spacing:0;margin-top:8px;max-width:72ch}
body.look-klar .body{left:86px;top:196px;width:1108px;height:400px}
body.look-klar .col{top:196px;width:530px;height:400px}
body.look-klar .col.l{left:86px}
body.look-klar .col.r{left:664px}
body.look-klar .col.short{height:318px}
body.look-klar .kf-foot{position:absolute;left:86px;right:86px;top:646px;border-top:1px solid #E1E6EE;padding-top:12px;display:flex;align-items:center;
 font-family:ui-monospace,SFMono-Regular,Menlo,monospace;font-size:10.5px;letter-spacing:.14em;text-transform:uppercase;color:#8A93A3}
body.look-klar .kf-num{margin-left:auto;margin-right:18px}
body.look-klar .kf-d3{width:132px;height:27px;display:block}
body.look-klar .kf-d3 svg{width:100%;height:100%;display:block}
body.look-klar .stepdots{left:86px;right:auto;top:630px}
body.look-klar ul>li{margin:.35em 0}
body.look-klar ul>li::before{top:.62em;width:.32em;height:.32em;background:var(--navy-50)}
body.look-klar .colhead{font-family:ui-monospace,SFMono-Regular,Menlo,monospace;font-size:11px;letter-spacing:.16em;text-transform:uppercase;color:#6B7688;font-weight:400;margin-bottom:10px}
body.look-klar .take{position:absolute;left:86px;right:86px;bottom:92px;background:none;border-left:3px solid var(--orange);padding:2px 0 2px 14px;font-size:19px;font-weight:600;color:var(--navy);line-height:1.35}
body.look-klar .take .tk{display:none}
body.look-klar .fr-take{position:static}
body.look-klar .stmt{font-size:50px;line-height:1.18;font-weight:400;letter-spacing:-.028em;max-width:25ch;color:#0F1B33;text-wrap:balance}
body.look-klar .stmt b{font-weight:600;color:var(--orange)}
body.look-klar .stmt .bl{font-weight:600;color:var(--navy)}
body.look-klar .facts{display:grid;grid-auto-flow:column;grid-auto-columns:1fr;gap:34px;margin-top:70px}
body.look-klar .fact .fv{font-size:68px;line-height:.9;font-weight:400;letter-spacing:-.04em;color:var(--navy);font-variant-numeric:tabular-nums}
body.look-klar .fact.acc .fv{color:var(--orange)}
body.look-klar .fact .fk{font-size:18px;line-height:1.45;color:#4A5568;margin-top:16px;max-width:26ch}
body.look-klar .bignum .bv{font-weight:400;font-size:112px}
body.look-klar .bignum .bk{font-size:19px;color:#4A5568}
body.look-klar .secq{position:absolute;left:86px;top:250px;width:1000px}
body.look-klar .secq.has-part{width:560px}
body.look-klar .secq.has-part .stmt{font-size:44px}
body.look-klar .secn{position:absolute;left:66px;top:58px;font-size:210px;font-weight:600;line-height:1;letter-spacing:-.04em;
 color:transparent;-webkit-text-stroke:2px var(--navy-15);pointer-events:none}
body.look-klar .spart{position:absolute;left:720px;top:250px;width:474px}
body.look-klar .sph{font-family:ui-monospace,SFMono-Regular,Menlo,monospace;font-size:11px;letter-spacing:.16em;text-transform:uppercase;
 color:#6B7688;padding-bottom:10px;border-bottom:1px solid #E1E6EE}
body.look-klar .spi{display:grid;grid-template-columns:34px 1fr;gap:10px;padding:10px 0;border-bottom:1px solid #E1E6EE;
 font-size:17px;line-height:1.35;color:var(--navy);cursor:pointer}
body.look-klar .spi:hover{color:var(--orange-ink,#B86E00)}
body.look-klar .spn{font-family:ui-monospace,SFMono-Regular,Menlo,monospace;font-size:12px;color:#8A93A3;padding-top:3px}
body.look-klar .spm{font-size:14px;color:#8A93A3;padding-top:8px}
body.look-klar .secq .pt{font-family:ui-monospace,SFMono-Regular,Menlo,monospace;font-size:11px;letter-spacing:.24em;text-transform:uppercase;color:var(--orange);margin-bottom:22px}
/* ══ look 'uni': University of Würzburg master (PPT-Master-Universitaet-Wuerzburg.potx) ══ */
body.look-uni{font-family:'Inclusive Sans UW',system-ui,sans-serif;
 --navy:#02246C;--darkblue:#011646;--bar:#02246C;--navy-5:#F2F4F8;--navy-10:#E6E9F0;--navy-15:#D9DEE9;--navy-50:#8191B5;--navy-90:#1B3A7B;
 --coral:#ED6A5B;--uwblue:#5E8AC7;--sky:#5AA1D8;--sand:#F1EBDF;--berry:#821044;
 --orange:#821044;--orange-ink:#821044;--orange-5:#F9F1F4;--orange-10:#F3E4EA;
 --lightblue:#CBD9EE;--teal:#009485;--teal-ink:#007A6E;--teal-10:#E6F4F3;--teal-25:#BFE4E0;
 --yellow:#F8C300;--peach:#F8CDC6;--lavender:#D9CCE6;--line:#D9DCE1;
 }   /* the seal is the booklet's 'Heritage' mark: coral on navy (pre-coloured PNG) */
body.look-uni .sl{color:#000;font-size:24px;line-height:1.4;font-weight:400}
body.look-uni .uw-logo{position:absolute;left:72px;top:23px;width:186px;height:55px;background:center/contain no-repeat}
body.look-uni .uw-rule{position:absolute;left:73px;top:94px;width:1138px;height:1px;background:#D3D6DC}
body.look-uni .uw-title{position:absolute;left:74px;top:111px;width:1137px;font-size:32px;font-weight:600;line-height:1.2;color:var(--navy);text-wrap:pretty}
body.look-uni .uw-title .kick{color:var(--berry);margin-right:.3em}
body.look-uni .uw-title .sub{display:block;font-size:19px;font-weight:400;line-height:1.45;color:#3C4658;margin-top:6px;max-width:80ch}
body.look-uni .body{left:74px;top:225px;width:1137px;height:420px}
body.look-uni .col{top:225px;width:548px;height:420px}
body.look-uni .col.l{left:74px}
body.look-uni .col.r{left:663px}
body.look-uni .col.short{height:335px}
body.look-uni .uw-foot{position:absolute;left:74px;top:680px;width:760px;height:23px;display:flex;align-items:center;font-size:13.3px;color:#000;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
body.look-uni .uw-num{position:absolute;left:1169px;top:671px;width:42px;height:49px;background:var(--navy);color:#fff;font-size:13.3px;
 display:flex;align-items:center;justify-content:center;line-height:1}
body.look-uni .trk{left:700px;top:42px;width:511px;height:24px}
body.look-uni .trk .ti{font-size:11px}
body.look-uni .stepdots{left:74px;right:auto;top:660px}
body.look-uni ul>li::before{background:var(--uwblue)}
body.look-uni .colhead{font-size:18px;font-weight:600;color:var(--navy);margin-bottom:8px}
body.look-uni .hl{color:var(--berry)}
body.look-uni .take{position:absolute;left:74px;bottom:58px;width:902px;min-height:84px;box-sizing:border-box;display:block;
 background:var(--sand);border:0;padding:28px 24px 26px 72px;font-size:20px;font-weight:500;color:#000;line-height:1.35}
body.look-uni .take::before{content:'';position:absolute;left:14px;top:50%;width:37px;height:32px;transform:translateY(-50%);
 background:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 37 32'%3E%3Cpath d='M0 16h35M19 .5 35 16 19 31.5' stroke='%231E1F1C' stroke-width='1.5' fill='none'/%3E%3C/svg%3E") center/contain no-repeat}
body.look-uni .take .tk{display:none}
body.look-uni .take b{color:var(--berry)}
body.look-uni .fr-take{position:static}
body.look-uni .stmt{font-size:46px;line-height:1.2;font-weight:400;max-width:26ch;color:var(--navy);text-wrap:balance}
body.look-uni .stmt b{font-weight:600;color:var(--berry)}
body.look-uni .facts{display:grid;grid-auto-flow:column;grid-auto-columns:1fr;gap:34px;margin-top:40px}
body.look-uni .fact{border-top:4px solid var(--uwblue);padding-top:18px}
body.look-uni .fact.acc{border-top-color:var(--coral)}
body.look-uni .fact .fv{font-size:64px;line-height:1;font-weight:600;color:var(--navy);font-variant-numeric:tabular-nums}
body.look-uni .fact.acc .fv{color:var(--berry)}
body.look-uni .fact .fk{font-size:19px;line-height:1.4;color:#3C4658;margin-top:12px;max-width:26ch}
body.look-uni .refs{font-size:14px;line-height:1.45;columns:2;column-gap:40px}
body.look-uni .refs li{break-inside:avoid;margin:0 0 8px;padding-left:0}
body.look-uni .refs li::before{display:none}
/* agenda */
body.look-uni .uw-agl{position:absolute;left:73px;top:197px;width:1138px}
body.look-uni .uw-ag{display:flex;align-items:baseline;height:60px}
body.look-uni .uw-agn{width:66px;flex:none;font-size:32px;font-weight:700;color:var(--sky);cursor:pointer}
body.look-uni .uw-agt{font-size:24px;color:#000;cursor:pointer}
/* navy slides: cover, divider */
body.look-uni .uw-cover,body.look-uni .uw-dark{position:absolute;inset:0;background:var(--navy);color:#fff}
body.look-uni .uw-c-band{background:#fff;color:var(--navy)}
body.look-uni .uw-cover .uw-logo,body.look-uni .uw-dark .uw-logo{top:22px}
body.look-uni .uw-seal{position:absolute;left:972px;top:412px;width:308px;height:308px;background:center/contain no-repeat}
body.look-uni .uw-c-band .uw-seal{left:1013px;top:442px;width:228px;height:228px}
body.look-uni .uw-band,body.look-uni .uw-box{position:absolute;left:39px;top:425px;height:245px;background:var(--navy)}
body.look-uni .uw-band{width:1202px}
body.look-uni .uw-box{width:616px}
body.look-uni .uw-photo{position:absolute;inset:0;background:center/cover no-repeat}
body.look-uni .uw-ttitle{position:absolute;left:74px;top:202px;width:1137px;height:159px;display:flex;align-items:flex-end;
 font-size:40px;font-weight:700;line-height:1.15;text-wrap:pretty}
body.look-uni .uw-c-band .uw-ttitle{top:168px;height:192px}
body.look-uni .uw-c-photo .uw-ttitle{top:113px;font-size:56px;text-shadow:0 2px 18px rgba(0,0,0,.35)}
body.look-uni .uw-meta{position:absolute;left:74px;top:440px;width:858px;height:215px;display:flex;flex-direction:column;
 justify-content:space-between;color:#fff}
body.look-uni .uw-c-band .uw-meta,body.look-uni .uw-c-photo .uw-meta{top:455px;width:546px;height:188px}
body.look-uni .uw-tsub{font-size:24px;font-weight:600;line-height:1.3;text-wrap:pretty}
body.look-uni .uw-tsub::before{content:'';display:block;width:44px;height:3px;background:var(--coral);margin-bottom:14px}
body.look-uni .uw-tname{font-size:20px;font-weight:600}
body.look-uni .uw-tdate{font-size:17px;opacity:.78;margin-top:4px}
body.look-uni .uw-dark .uw-rule{background:rgba(255,255,255,.55)}
body.look-uni .uw-sk{position:absolute;left:74px;top:350px;font-size:15px;font-weight:500;letter-spacing:.12em;text-transform:uppercase;color:var(--sky)}
body.look-uni .uw-sn{position:absolute;left:68px;top:380px;font-size:133px;font-weight:700;line-height:1;color:var(--sky)}
body.look-uni .uw-st{position:absolute;left:74px;top:527px;width:857px;font-size:36px;font-weight:600;line-height:1.2;color:#fff}
body.look-uni .uw-sq{font-size:22px;font-weight:400;line-height:1.4;color:#DCE4F2;margin-top:12px;max-width:44ch}
/* closing slide */
body.look-uni .uw-end{position:absolute;left:625px;top:0;width:655px;height:720px;background:#F2F2F2}
body.look-uni .uw-seal-end{}
body.look-uni .uw-thx{position:absolute;left:74px;top:171px;width:514px;height:189px;display:flex;align-items:flex-end;font-size:40px;font-weight:700;line-height:1.15;color:var(--navy)}
body.look-uni .uw-contact{top:426px;padding:40px 35px 0;box-sizing:border-box;color:#fff;font-size:21px;line-height:1.7}
body.look-uni .uw-contact b{display:block;font-weight:700;margin-bottom:6px}
body.look-uni .uw-web{margin-top:4px}
/* kit objects toned down to the master's plain style: no cards, no icons, sans-serif labels */
body.look-uni :is(.k-tkick,.k-lane,.k-why,.k-cname,.k-rk,.k-lcap,.k-legend,.k-ulegend,.k-gends,.k-vrow .m,.k-bl,.prov){
 font-family:inherit;letter-spacing:.01em;text-transform:none;font-size:14px}
body.look-uni .k-tile{background:none;border:0;border-top:1px solid #D3D6DC;border-radius:0;padding:12px 4px 4px;color:#000;font-size:20px}
body.look-uni .k-tile.orange{border-top:2px solid var(--coral)}
body.look-uni .k-tkick{font-size:15px;font-weight:600;color:var(--uwblue)}
body.look-uni .k-tkick .ico{display:none}
body.look-uni .k-tbig,body.look-uni .k-tile.teal .k-tbig,body.look-uni .k-tile.gray .k-tbig{color:var(--navy);font-size:22px;margin-top:4px}
body.look-uni .k-tile.orange .k-tbig{color:var(--berry)}
body.look-uni .k-tlines{font-size:19px;gap:4px}
body.look-uni .sl .k-tlines>li::before{background:var(--uwblue);width:7px;height:7px}
body.look-uni .k-callout{border-radius:0}
body.look-uni .k-callout.quiet{background:var(--sand);border:0;color:#000}
body.look-uni .k-callout.quiet b{color:var(--berry)}
body.look-uni .k-chip{border-radius:0;border-color:#D3D6DC}
body.look-uni .k-proof .k-pbox{border-radius:0}
body.look-uni .k-table th{font-family:inherit;letter-spacing:.01em;text-transform:none;font-size:15px;font-weight:600;color:var(--navy)}
"""