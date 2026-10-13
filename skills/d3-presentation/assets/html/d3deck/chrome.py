# -*- coding: utf-8 -*-
"""The slide frame: the University of Würzburg PowerPoint master (PPT-Master-Universitaet-Wuerzburg.potx, 2025
corporate design), with the D3 logo in the master's co-branding slot.

All geometry is in px on the 1280x720 canvas. The master is 12192000 EMU wide, so 1 px = 9525 EMU, and the numbers
below are the boxes of its slide layouts. All looks share the frame:
  klar (default) and beamer: D3 logo top right (next to the university logo on title and closing slides), D3 orange
  as the accent, the seal in blue on navy;
  uni: the plain university master without D3 branding, for teaching: coral seal, berry text accents.
Logos and seals are vector SVGs, embedded once per file as CSS backgrounds (assets_css), not once per slide.
"""
import base64
import os
import re

from . import paths

D3_SVG = 'DataDrivenDecisions_2c.svg'
UW_LOGO = {'navy': 'uw-logo-navy.svg', 'white': 'uw-logo-white.svg'}
UW_SEAL = {'blue': 'uw-seal-blue.svg', 'coral': 'uw-seal-coral.svg', 'faint': 'uw-seal-faint.svg'}
UW_COVER = 'uw-cover.jpg'
D3_NEG = {'#1f2043': '#ffffff'}      # the D3 logo on navy: dark parts white, orange stays
COVERS = ('band', 'navy', 'photo')

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


def svg_uri(name, recolor=None):
    """An SVG from the logos folder as a data URI (cached); <text> nodes go (the D3 logo carries an empty one)."""
    key = (name, tuple(sorted((recolor or {}).items())))
    if key not in _cache:
        with open(os.path.join(paths.asset_dir('logos'), name), encoding='utf-8') as fh:
            raw = fh.read()
        raw = re.sub(r'<\?xml[^>]*\?>', '', raw)
        raw = re.sub(r'<text\b.*?</text>', '', raw, flags=re.S).strip()
        for a, b in (recolor or {}).items():
            raw = re.sub(re.escape(a), b, raw, flags=re.I)
        _cache[key] = 'data:image/svg+xml;base64,' + base64.b64encode(raw.encode()).decode()
    return _cache[key]


def _data_uri(name):
    """A raster from the logos folder as a data URI (cached)."""
    if name not in _cache:
        mime = 'image/jpeg' if name.endswith('.jpg') else 'image/png'
        with open(os.path.join(paths.asset_dir('logos'), name), 'rb') as fh:
            _cache[name] = f'data:{mime};base64,' + base64.b64encode(fh.read()).decode()
    return _cache[name]


def assets_css(look='klar', photo=False):
    """Logos and seals as CSS backgrounds, embedded once per file. D3 looks get the D3 logo and the blue seal,
    the uni look the coral seal. photo: also the cover photo (about 0.3 MB)."""
    d3 = look != 'uni'
    css = (f'.uw-logo-navy{{background-image:url({svg_uri(UW_LOGO["navy"])})}}'
           f'.uw-logo-white{{background-image:url({svg_uri(UW_LOGO["white"])})}}'
           f'.uw-seal{{background-image:url({svg_uri(UW_SEAL["blue" if d3 else "coral"])})}}'
           f'.uw-seal.uw-seal-end{{background-image:url({svg_uri(UW_SEAL["faint"])})}}')
    if d3:
        css += (f'.d3-co{{background-image:url({svg_uri(D3_SVG)})}}'
                f'.d3-co.neg{{background-image:url({svg_uri(D3_SVG, D3_NEG)})}}')
    if photo:
        css += f'.uw-photo{{background-image:url({_data_uri(UW_COVER)})}}'
    return css


WORDS = {
    'en': dict(agenda='Agenda', part='Part {n} of {N}', thanks='Thank you', contact='Contact', refs='References',
               inpart='In this part', more='and {k} more'),
    'de': dict(agenda='Agenda', part='Teil {n} von {N}', thanks='Vielen Dank', contact='Kontakt', refs='Quellenangaben',
               inpart='In diesem Teil', more='und {k} weitere'),
}
UNI_WORDS = WORDS


def uni_words(lang):
    return WORDS.get((lang or 'en')[:2], WORDS['en'])


def uni_logo(color='navy'):
    return f'<div class="uw-logo uw-logo-{color}" role="img" aria-label="Universität Würzburg"></div>'


def d3_logo(cover=False, neg=False):
    """The D3 logo in the master's co-branding slot: top right on content slides, next to the university logo on
    title and closing slides (cover=True). neg: the white variant for navy and photo backgrounds."""
    cls = 'd3-co' + (' cov' if cover else '') + (' neg' if neg else '')
    return f'<div class="{cls}" role="img" aria-label="Data Driven Decisions"></div>'


def _uw_seal(cls='uw-seal'):
    return f'<div class="{cls}"></div>'


def frame(title, inner, page='', foot='', tracker='', dots='', prov='', d3=True):
    """Inhaltsfolie: university logo top left over a hairline, the D3 logo top right (d3), title, body, footer line
    bottom left, page number in a navy tab bottom right."""
    parts = [uni_logo(), '<div class="uw-rule"></div>', d3_logo() if d3 else '', tracker or '']
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


def uni_frame(title, inner, page='', foot='', tracker='', dots='', prov=''):
    """The frame without the D3 logo (look 'uni')."""
    return frame(title, inner, page, foot, tracker, dots, prov, d3=False)


def cover_slide(title, subtitle='', presenter='', date='', cover='band', d3=True):
    """Deckblatt. cover='band' (white, navy band with the seal; the D3 default), 'navy' (all navy, seal; the uni
    default) or 'photo' (Würzburg skyline). d3: the D3 logo next to the university logo."""
    if cover not in COVERS:
        raise ValueError(f"cover must be one of {COVERS}")
    who = ''.join(f'<div class="{c}">{t}</div>' for c, t in (('uw-tname', presenter), ('uw-tdate', date)) if t)
    lines = (f'<div class="uw-meta">' + (f'<div class="uw-tsub">{subtitle}</div>' if subtitle else '<div></div>')
             + f'<div class="uw-who">{who}</div></div>')
    h = f'<div class="uw-cover uw-c-{cover}">'
    if cover == 'photo':
        h += '<div class="uw-photo"></div><div class="uw-box"></div>'
    elif cover == 'band':
        h += '<div class="uw-band"></div>'
    h += uni_logo('navy' if cover == 'band' else 'white') + _uw_seal()
    if d3:
        h += d3_logo(cover=True, neg=cover != 'band')
    return h + f'<div class="uw-ttitle"><span>{title}</span></div>{lines}</div>'


def uni_title(title, subtitle='', presenter='', date='', cover='navy'):
    """Deckblatt of the uni look (no D3 logo)."""
    return cover_slide(title, subtitle, presenter, date, cover, d3=False)


def divider(n, sections, question, lang, part=None):
    """Trennseite: navy, white logo over a white hairline, 'Part n of N', the part number in sky blue, the part name
    and its question. part: [(slide index, number, claim)] lists the part's slides beside it (the klar look)."""
    w = uni_words(lang)
    q = f'<div class="uw-sq">{question}</div>' if question else ''
    h = (f'<div class="uw-dark">{uni_logo("white")}<div class="uw-rule"></div>{_uw_seal()}'
         f'<div class="uw-sk">{w["part"].format(n=n, N=len(sections))}</div>'
         f'<div class="uw-sn">{n:02d}</div><div class="uw-st">{sections[n - 1]}{q}</div>')
    if part:
        rows = ''.join(f'<div class="spi" data-jump="{j}"><span class="spn">{num}</span><span>{c}</span></div>'
                       for j, num, c in part[:6])
        more = f'<div class="spm">{w["more"].format(k=len(part) - 6)}</div>' if len(part) > 6 else ''
        h += f'<div class="uw-part"><div class="sph">{w["inpart"]}</div>{rows}{more}</div>'
    return h + '</div>'


def uni_divider(n, sections, question, lang):
    return divider(n, sections, question, lang)


def uni_agenda(sections, links=None, lang='en'):
    """Agenda: two-digit numbers in sky blue, topics beside them, 60 px apart, as in the master."""
    rows = ''.join(f'<div class="uw-ag"><span class="uw-agn"{j}>{k:02d}</span><span class="uw-agt"{j}>{name}</span></div>'
                   for k, name in enumerate(sections, 1)
                   for j in [f' data-jump="@@{links[k]}@@"' if links and k in links else ''])
    return f'<div class="uw-title">{uni_words(lang)["agenda"]}</div><div class="uw-agl">{rows}</div>'


def uni_thankyou(text, contact, lang='en', d3=False):
    """Abschlussseite: thanks in navy, a navy contact box, grey right half with the seal; d3: the D3 logo next to
    the university logo."""
    w = uni_words(lang)
    rows = ''.join(f'<div>{c}</div>' for c in contact if c)
    return ((d3_logo(cover=True) if d3 else '') +
            f'<div class="uw-end"></div>{_uw_seal("uw-seal uw-seal-end")}<div class="uw-thx">{text or w["thanks"]}</div>'
            f'<div class="uw-box uw-contact"><b>{w["contact"]}</b>{rows}<div class="uw-web">uni-wuerzburg.de</div></div>')


def tracker(sections, current):
    """Section tracker (klar: in the header between the logos; beamer: in the footer band). current is 0-based."""
    items = []
    for i, name in enumerate(sections):
        c = ' cur' if i == current else (' done' if i < current else '')
        items.append(f'<div class="ti{c}">{name}</div>')
    return '<div class="trk">' + ''.join(items) + '</div>'


CSS = r"""
/* references(): small, two columns, no bullets, in every look (body .sl outweighs body.look-* ul>li) */
body .sl ul.refs{font-size:14px;line-height:1.45;columns:2;column-gap:40px}
body .sl ul.refs>li{break-inside:avoid;margin:0 0 8px;padding-left:0}
body .sl ul.refs>li::before{display:none}

/* ══ the frame of every look: the master's Inhaltsfolie (1 px = 9525 EMU) ══ */
.uw-logo{position:absolute;left:72px;top:23px;width:186px;height:55px;background:left center/contain no-repeat}
.uw-rule{position:absolute;left:73px;top:94px;width:1138px;height:1px;background:#D3D6DC}
.d3-co{position:absolute;left:1037px;top:35px;width:174px;height:35px;background:right center/contain no-repeat}
.d3-co.cov{left:295px;top:33px;background-position:left center}
.uw-title{position:absolute;left:74px;top:111px;width:1137px;font-size:32px;font-weight:600;line-height:1.2;color:var(--navy);text-wrap:pretty}
.uw-title .kick{color:var(--orange);margin-right:.3em}
.uw-title .sub{display:block;font-size:19px;font-weight:400;line-height:1.45;color:#3C4658;margin-top:6px;max-width:80ch}
.body{position:absolute;left:74px;top:225px;width:1137px;height:420px;overflow:hidden}
.col{position:absolute;top:225px;width:548px;height:420px;overflow:hidden}
.col.l{left:74px}
.col.r{left:663px}
.col.short{height:335px}
.uw-foot{position:absolute;left:74px;top:680px;width:760px;height:23px;display:flex;align-items:center;font-size:13.3px;color:#000;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.uw-num{position:absolute;left:1169px;top:671px;width:42px;height:49px;background:var(--navy);color:#fff;font-size:13.3px;
 display:flex;align-items:center;justify-content:center;line-height:1}
body .stepdots{left:74px;right:auto;top:660px}
body .fr-take{position:static}
/* section tracker: klar in the header between the logos, beamer in the footer band (replaces the footer text) */
.trk{position:absolute;left:300px;top:40px;width:700px;height:24px;display:flex}
.trk .ti{flex:1;display:flex;align-items:center;padding:0 10px 0 18px;font-size:11px;font-weight:600;letter-spacing:.01em;white-space:nowrap;
 overflow:hidden;text-overflow:ellipsis;background:#F2F4F8;color:var(--gray);
 clip-path:polygon(0 0,calc(100% - 9px) 0,100% 50%,calc(100% - 9px) 100%,0 100%,9px 50%)}
.trk .ti:first-child{padding-left:10px;clip-path:polygon(0 0,calc(100% - 9px) 0,100% 50%,calc(100% - 9px) 100%,0 100%)}
.trk .ti+.ti{margin-left:-7px}
.trk .ti.done{background:var(--lightblue);color:var(--navy)}
.trk .ti.cur{background:var(--navy);color:#fff;z-index:3}
body.look-beamer .trk{left:74px;top:680px;width:760px;height:23px}
body.look-uni .trk{left:700px;top:42px;width:511px}

/* ── covers (Deckblatt): band (D3 default), navy (uni default), photo ── */
.uw-cover,.uw-dark{position:absolute;inset:0;background:var(--navy);color:#fff}
.uw-c-band{background:#fff;color:var(--navy)}
.uw-cover .uw-logo,.uw-dark .uw-logo{top:22px}
.uw-seal{position:absolute;left:972px;top:412px;width:308px;height:308px;background:center/contain no-repeat}
.uw-c-band .uw-seal{left:1013px;top:442px;width:228px;height:228px}
.uw-band,.uw-box{position:absolute;left:39px;top:425px;height:245px;background:var(--navy)}
.uw-band{width:1202px}
.uw-box{width:616px}
.uw-photo{position:absolute;inset:0;background:center/cover no-repeat}
.uw-ttitle{position:absolute;left:74px;top:202px;width:1137px;height:159px;display:flex;align-items:flex-end;
 font-size:40px;font-weight:700;line-height:1.15;text-wrap:pretty}
.uw-c-band .uw-ttitle{top:168px;height:192px}
.uw-c-photo .uw-ttitle{top:113px;font-size:56px;text-shadow:0 2px 18px rgba(0,0,0,.35)}
.uw-meta{position:absolute;left:74px;top:440px;width:858px;height:215px;display:flex;flex-direction:column;
 justify-content:space-between;color:#fff}
.uw-c-band .uw-meta,.uw-c-photo .uw-meta{top:455px;height:188px}
.uw-c-band .uw-meta{width:900px}
.uw-c-photo .uw-meta{width:546px}
.uw-tsub{font-size:24px;font-weight:600;line-height:1.3;text-wrap:pretty}
.uw-tsub::before{content:'';display:block;width:44px;height:3px;background:var(--orange);margin-bottom:14px}
.uw-tname{font-size:20px;font-weight:600}
.uw-tdate{font-size:17px;opacity:.78;margin-top:4px}
/* ── divider (Trennseite) ── */
.uw-dark .uw-rule{background:rgba(255,255,255,.55)}
.uw-sk{position:absolute;left:74px;top:350px;font-size:15px;font-weight:500;letter-spacing:.12em;text-transform:uppercase;color:var(--orange)}
.uw-sn{position:absolute;left:68px;top:380px;font-size:133px;font-weight:700;line-height:1;color:var(--sky)}
.uw-st{position:absolute;left:74px;top:527px;width:857px;font-size:36px;font-weight:600;line-height:1.2;color:#fff}
.uw-sq{font-size:22px;font-weight:400;line-height:1.4;color:#DCE4F2;margin-top:12px;max-width:44ch}
.uw-part{position:absolute;left:700px;top:138px;width:480px}
.uw-part .sph{font-size:13px;font-weight:500;letter-spacing:.12em;text-transform:uppercase;color:#A9B8D6;
 padding-bottom:9px;border-bottom:1px solid rgba(255,255,255,.28)}
.uw-part .spi{display:grid;grid-template-columns:34px 1fr;gap:10px;padding:9px 0;border-bottom:1px solid rgba(255,255,255,.18);
 font-size:17px;line-height:1.35;color:#fff;cursor:pointer}
.uw-part .spi:hover{color:var(--orange)}
.uw-part .spn{font-size:13px;color:var(--sky);padding-top:3px;font-weight:600}
.uw-part .spm{font-size:14px;color:#A9B8D6;padding-top:8px}
/* ── agenda ── */
.uw-agl{position:absolute;left:73px;top:197px;width:1138px}
.uw-ag{display:flex;align-items:baseline;height:60px}
.uw-agn{width:66px;flex:none;font-size:32px;font-weight:700;color:var(--sky);cursor:pointer}
.uw-agt{font-size:24px;color:#000;cursor:pointer}
/* ── closing slide (Abschlussseite) ── */
.uw-end{position:absolute;left:625px;top:0;width:655px;height:720px;background:#F2F2F2}
.uw-thx{position:absolute;left:74px;top:171px;width:514px;height:189px;display:flex;align-items:flex-end;font-size:40px;font-weight:700;line-height:1.15;color:var(--navy)}
.uw-contact{top:426px;padding:40px 35px 0;box-sizing:border-box;color:#fff;font-size:21px;line-height:1.7}
.uw-contact b{display:block;font-weight:700;margin-bottom:6px}
.uw-web{margin-top:4px}

/* ══ D3 looks (klar, beamer): black body text, D3 orange accents, the sand takeaway bar with an orange rule ══ */
body.look-klar .sl,body.look-beamer .sl{color:#000}
body.look-klar .sl{font-size:22px;line-height:1.6;font-weight:400}
body.look-klar ul>li{margin:.35em 0}
body.look-klar ul>li::before,body.look-beamer ul>li::before{background:var(--blue)}
body.look-klar ul>li::before{top:.62em;width:.32em;height:.32em}
body.look-klar .colhead{font-family:ui-monospace,SFMono-Regular,Menlo,monospace;font-size:11px;letter-spacing:.16em;text-transform:uppercase;color:#6B7688;font-weight:400;margin-bottom:10px}
:is(body.look-klar,body.look-beamer) .take{position:absolute;left:74px;bottom:58px;width:902px;min-height:84px;box-sizing:border-box;display:block;
 background:var(--sand);border:0;border-left:4px solid var(--orange);padding:28px 24px 26px 26px;font-size:20px;font-weight:500;color:#000;line-height:1.35}
:is(body.look-klar,body.look-beamer) .take .tk{display:none}
:is(body.look-klar,body.look-beamer) .take b{color:var(--orange-ink)}
:is(body.look-klar,body.look-beamer) .stmt{font-size:48px;line-height:1.18;font-weight:400;letter-spacing:-.015em;max-width:25ch;color:var(--navy);text-wrap:balance}
:is(body.look-klar,body.look-beamer) .stmt b{font-weight:600;color:var(--orange)}
:is(body.look-klar,body.look-beamer) .stmt .bl{font-weight:600;color:var(--navy)}
:is(body.look-klar,body.look-beamer) .facts{display:grid;grid-auto-flow:column;grid-auto-columns:1fr;gap:34px;margin-top:60px}
:is(body.look-klar,body.look-beamer) .fact{border-top:4px solid var(--blue);padding-top:18px}
:is(body.look-klar,body.look-beamer) .fact.acc{border-top-color:var(--orange)}
:is(body.look-klar,body.look-beamer) .fact .fv{font-size:66px;line-height:1;font-weight:600;letter-spacing:-.02em;color:var(--navy)}
:is(body.look-klar,body.look-beamer) .fact.acc .fv{color:var(--orange)}
:is(body.look-klar,body.look-beamer) .fact .fk{font-size:18px;line-height:1.45;color:#3C4658;margin-top:14px;max-width:26ch}
:is(body.look-klar,body.look-beamer) .bignum .bv{font-weight:600;font-size:112px}
:is(body.look-klar,body.look-beamer) .bignum .bk{font-size:19px;color:#3C4658}

/* ══ look 'uni': University of Würzburg master without D3 branding (teaching) ══ */
body.look-uni{
 --navy:#02246C;--darkblue:#011646;--bar:#02246C;--navy-5:#F2F4F8;--navy-10:#E6E9F0;--navy-15:#D9DEE9;--navy-50:#8092B6;--navy-90:#1B3A7B;
 --coral:#ED6A5B;--uwblue:#5E8AC7;--sky:#5AA1D8;--sand:#F1EBDF;--berry:#821044;
 --orange:#821044;--orange-ink:#821044;--orange-5:#F9F1F4;--orange-10:#F3E4EA;
 --lightblue:#CBD9EE;--teal:#009485;--teal-ink:#007A6E;--teal-10:#E6F4F3;--teal-25:#BFE4E0;
 --yellow:#F8C300;--peach:#F8CDC6;--lavender:#D9CCE6;--line:#D9DCE1;
 }   /* berry takes the role of D3 orange for text accents; the seal is coral on navy (the booklet's 'Heritage' mark) */
body.look-uni .sl{color:#000;font-size:24px;line-height:1.4;font-weight:400}
body.look-uni .uw-title .kick{color:var(--berry)}
body.look-uni .uw-tsub::before{background:var(--coral)}
body.look-uni .uw-sk{color:var(--sky)}
body.look-uni ul>li::before{background:var(--uwblue)}
body.look-uni .colhead{font-size:18px;font-weight:600;color:var(--navy);margin-bottom:8px}
body.look-uni .hl{color:var(--berry)}
body.look-uni .take{position:absolute;left:74px;bottom:58px;width:902px;min-height:84px;box-sizing:border-box;display:block;
 background:var(--sand);border:0;padding:28px 24px 26px 72px;font-size:20px;font-weight:500;color:#000;line-height:1.35}
body.look-uni .take::before{content:'';position:absolute;left:14px;top:50%;width:37px;height:32px;transform:translateY(-50%);
 background:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 37 32'%3E%3Cpath d='M0 16h35M19 .5 35 16 19 31.5' stroke='%231E1F1C' stroke-width='1.5' fill='none'/%3E%3C/svg%3E") center/contain no-repeat}
body.look-uni .take .tk{display:none}
body.look-uni .take b{color:var(--berry)}
body.look-uni .stmt{font-size:46px;line-height:1.2;font-weight:400;max-width:26ch;color:var(--navy);text-wrap:balance}
body.look-uni .stmt b{font-weight:600;color:var(--berry)}
body.look-uni .facts{display:grid;grid-auto-flow:column;grid-auto-columns:1fr;gap:34px;margin-top:40px}
body.look-uni .fact{border-top:4px solid var(--uwblue);padding-top:18px}
body.look-uni .fact.acc{border-top-color:var(--coral)}
body.look-uni .fact .fv{font-size:64px;line-height:1;font-weight:600;color:var(--navy)}
body.look-uni .fact.acc .fv{color:var(--berry)}
body.look-uni .fact .fk{font-size:19px;line-height:1.4;color:#3C4658;margin-top:12px;max-width:26ch}
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
