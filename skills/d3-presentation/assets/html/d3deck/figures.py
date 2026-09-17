# -*- coding: utf-8 -*-
"""Figure embedding.

fig(name) finds figures/<name>.(png|jpg|jpeg|svg|pdf), embeds it as a data URI
and sets aspect-ratio from the parsed image size, so a container never
distorts the figure and SVG annotations drawn over it stay anchored. PDFs are
rasterized once with pdftoppm into figures/.cache/.
"""
import base64
import os
import re
import shutil
import struct
import subprocess

from . import paths

EXTS = ('png', 'jpg', 'jpeg', 'svg', 'pdf')
MIME = {'png': 'image/png', 'jpg': 'image/jpeg', 'jpeg': 'image/jpeg', 'svg': 'image/svg+xml'}
FIG_DIR = None   # override; default is <talk>/figures


def _fig_dir(fig_dir):
    return fig_dir or FIG_DIR or os.path.join(paths.talk_dir(), 'figures')


def find_figure(name, fig_dir=None):
    fig_dir = _fig_dir(fig_dir)
    ext = os.path.splitext(name)[1].lstrip('.').lower()
    if ext in EXTS:
        p = os.path.join(fig_dir, name)
        if os.path.exists(p):
            return p
        raise FileNotFoundError(f'figure not found: {p}')
    for e in EXTS:
        p = os.path.join(fig_dir, f'{name}.{e}')
        if os.path.exists(p):
            return p
    raise FileNotFoundError(f'no figure named {name!r} with one of {EXTS} in {fig_dir}/')


def png_size(data):
    if data[:8] != b'\x89PNG\r\n\x1a\n' or data[12:16] != b'IHDR':
        raise ValueError('not a PNG')
    return struct.unpack('>II', data[16:24])


def jpeg_size(data):
    if data[:2] != b'\xff\xd8':
        raise ValueError('not a JPEG')
    sof = (0xC0, 0xC1, 0xC2, 0xC3, 0xC5, 0xC6, 0xC7, 0xC9, 0xCA, 0xCB, 0xCD, 0xCE, 0xCF)
    i = 2
    while i + 4 <= len(data):
        if data[i] != 0xFF:
            i += 1
            continue
        marker = data[i + 1]
        if marker in (0xD8, 0x01, 0xFF) or 0xD0 <= marker <= 0xD7:
            i += 2
            continue
        seglen = struct.unpack('>H', data[i + 2:i + 4])[0]
        if marker in sof:
            h, w = struct.unpack('>HH', data[i + 5:i + 9])
            return w, h
        i += 2 + seglen
    raise ValueError('JPEG without a SOF marker')


def svg_size(data):
    text = data.decode('utf-8', 'replace')
    m = re.search(r'<svg\b[^>]*>', text, re.S)
    if not m:
        raise ValueError('not an SVG')
    tag = m.group(0)
    vb = re.search(r'viewBox="([^"]+)"', tag)
    if vb:
        parts = vb.group(1).replace(',', ' ').split()
        return float(parts[2]), float(parts[3])
    w = re.search(r'\swidth="([\d.]+)', tag)
    h = re.search(r'\sheight="([\d.]+)', tag)
    if w and h:
        return float(w.group(1)), float(h.group(1))
    raise ValueError('SVG without viewBox or width/height')


def image_size(data, ext):
    ext = ext.lower().lstrip('.')
    if ext == 'png':
        return png_size(data)
    if ext in ('jpg', 'jpeg'):
        return jpeg_size(data)
    if ext == 'svg':
        return svg_size(data)
    raise ValueError(f'unsupported image type: {ext}')


def rasterize_pdf(path, fig_dir):
    cache = os.path.join(fig_dir, '.cache')
    os.makedirs(cache, exist_ok=True)
    stem = os.path.splitext(os.path.basename(path))[0]
    out = os.path.join(cache, stem)
    png = out + '.png'
    if os.path.exists(png) and os.path.getmtime(png) >= os.path.getmtime(path):
        return png
    if not shutil.which('pdftoppm'):
        raise RuntimeError(f'{path}: PDF figures need pdftoppm (poppler). Install with: brew install poppler')
    subprocess.run(['pdftoppm', '-png', '-r', '200', '-singlefile', path, out], check=True)
    return png


def load(name, fig_dir=None):
    """-> (data_uri, width, height) for figures/<name>."""
    fig_dir = _fig_dir(fig_dir)
    path = find_figure(name, fig_dir)
    ext = os.path.splitext(path)[1].lstrip('.').lower()
    if ext == 'pdf':
        path = rasterize_pdf(path, fig_dir)
        ext = 'png'
    with open(path, 'rb') as fh:
        data = fh.read()
    w, h = image_size(data, ext)
    return f'data:{MIME[ext]};base64,{base64.b64encode(data).decode()}', w, h


def fig(name, width=None, height=None, cls='', style='', alt=''):
    """<img> for figures/<name> with its aspect ratio pinned."""
    uri, w, h = load(name)
    st = f'aspect-ratio:{w:g}/{h:g};'
    if width:
        st += f'width:{width};'
    if height:
        st += f'height:{height};'
    st += style
    classes = ('fig ' + cls).strip()
    return f'<img class="{classes}" src="{uri}" alt="{alt}" style="{st}">'
