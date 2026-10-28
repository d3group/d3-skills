// Measure the visible slide (.sl.on) into a flat list of items for the PPTX writer.
// Coordinates are px on the 1280x720 canvas. Called as (opts) => items, where
// opts = {chrome: [selectors], boxOnly: [selectors], roles: [[selector, role]]}: chrome elements are drawn
// by the slide layout (logo, rule, page tab) and left out; boxOnly elements keep their text but leave their
// background and borders to the layout; roles name the text that goes into a layout placeholder.
(opts) => {
  const S = document.querySelector('.sl.on'), B = S.getBoundingClientRect();
  const items = [];
  let xid = 0;
  const R = el => { const r = el.getBoundingClientRect(); return {x: r.left - B.left, y: r.top - B.top, w: r.width, h: r.height}; };
  // display:contents has no box of its own (a grid row wrapper): it is visible when what it holds is
  const visible = el => getComputedStyle(el).display === 'contents'
    ? [...el.childNodes].some(n => (n.nodeType === 3 && /\S/.test(n.textContent)) || (n.nodeType === 1 && visible(n)))
    : el.checkVisibility({opacityProperty: true, visibilityProperty: true});
  const color = c => {
    const m = /rgba?\(([^)]+)\)/.exec(c || ''); if (!m) return null;
    const p = m[1].split(/[\s,\/]+/).filter(Boolean).map(Number);
    const a = p.length > 3 ? p[3] : 1;
    return a < 0.02 ? null : [p[0], p[1], p[2], a];
  };
  const tag = el => el.tagName.toLowerCase();
  const matches = (el, sels) => sels.some(s => el.matches(s));
  const stepOf = el => { const g = el.closest('[data-s]'); return g && S.contains(g) ? parseInt(g.dataset.s) || 0 : 0; };
  const jumpOf = el => { const g = el.closest('[data-jump]'); return g && S.contains(g) ? parseInt(g.dataset.jump) : null; };
  const isInline = el => {
    const d = getComputedStyle(el).display;
    if (tag(el) === 'mjx-container') return el.getAttribute('display') !== 'true';
    if (tag(el) === 'img' || tag(el) === 'svg' || tag(el) === 'br') return tag(el) === 'br';
    return d === 'inline' || d === 'inline-block' || d === 'contents';
  };
  const hasText = el => /\S/.test(el.textContent || '') || !!el.querySelector('mjx-container');

  // ── runs: the inline content of a paragraph ──
  const opacityOf = e => { let o = 1; for (let x = e; x && x !== S.parentElement; x = x.parentElement) o *= parseFloat(getComputedStyle(x).opacity); return o; };
  function style(e) {
    const cs = getComputedStyle(e);
    const ls = cs.letterSpacing === 'normal' ? 0 : parseFloat(cs.letterSpacing);
    return {c: color(cs.color), b: parseInt(cs.fontWeight) >= 600, i: cs.fontStyle === 'italic', sz: parseFloat(cs.fontSize),
            mono: /mono|menlo|consolas|courier/i.test(cs.fontFamily), up: cs.textTransform === 'uppercase', ls: ls,
            va: cs.verticalAlign === 'super' ? 'sup' : cs.verticalAlign === 'sub' ? 'sub' : '', pre: cs.whiteSpace.startsWith('pre'),
            op: opacityOf(e)};
  }
  function mathRuns(container, out) {
    const base = style(container);
    const mml = container.querySelector('mjx-assistive-mml math');
    if (!mml) { out.push(Object.assign({}, base, {t: container.textContent})); return; }
    const walk = (n, va) => {
      const t = n.tagName ? n.tagName.toLowerCase() : '';
      const kids = [...n.children];
      const put = (text, it) => { if (text) out.push(Object.assign({}, base, {t: text, i: !!it, va: va || base.va})); };
      if (t === 'mi') put(n.textContent, n.textContent.length === 1 && n.getAttribute('mathvariant') !== 'normal');
      else if (t === 'mn' || t === 'mo' || t === 'mtext' || t === 'ms') put(n.textContent, false);
      else if (t === 'mspace') put(' ', false);
      else if (t === 'msup' || t === 'msub') { walk(kids[0], va); walk(kids[1], t === 'msup' ? 'sup' : 'sub'); }
      else if (t === 'msubsup') { walk(kids[0], va); walk(kids[1], 'sub'); walk(kids[2], 'sup'); }
      else if (t === 'mfrac') { put('(', false); walk(kids[0], va); put(')/(', false); walk(kids[1], va); put(')', false); }
      else if (t === 'msqrt') { put('√(', false); kids.forEach(k => walk(k, va)); put(')', false); }
      else if (t === 'mover' && kids[1] && /^[\^ˆ]$/.test(kids[1].textContent)) { walk(kids[0], va); put('̂', false); }
      else if (t === 'mover' && kids[1] && /^[~˜]$/.test(kids[1].textContent)) { walk(kids[0], va); put('̃', false); }
      else if (t === 'mover' && kids[1] && /^[¯‾_]$/.test(kids[1].textContent)) { walk(kids[0], va); put('̄', false); }
      else if (t === 'munder' || t === 'mover' || t === 'munderover') { walk(kids[0], va); kids.slice(1).forEach(k => walk(k, t === 'munder' ? 'sub' : 'sup')); }
      else kids.forEach(k => walk(k, va));
    };
    walk(mml, '');
  }
  function atomRuns(n, out) {
    if (n.nodeType === 3) {
      if (n.textContent.length) out.push(Object.assign(style(n.parentElement), {t: n.textContent}));
    } else if (n.nodeType === 1 && visible(n)) {
      if (tag(n) === 'br') out.push({br: true});
      else if (tag(n) === 'mjx-container') { if (n.getAttribute('display') !== 'true') mathRuns(n, out); }
      else if (isInline(n)) {
        const cs = getComputedStyle(n), fs = parseFloat(cs.fontSize);
        if (parseFloat(cs.marginLeft) > 0.15 * fs) out.push(Object.assign(style(n), {t: ' '}));
        runs(n, out);
        if (parseFloat(cs.marginRight) > 0.15 * fs) out.push(Object.assign(style(n), {t: ' '}));
      }
    }
    return out;
  }
  function runs(el, out) { for (const n of el.childNodes) atomRuns(n, out); return out; }
  // a paragraph is a block whose own children include text or inline elements with text
  const isPara = el => [...el.childNodes].some(n => (n.nodeType === 3 && /\S/.test(n.textContent)) ||
                                                      (n.nodeType === 1 && isInline(n) && tag(n) !== 'br' && hasText(n)));
  const blockKids = el => [...el.children].filter(c => !isInline(c) && visible(c));

  function inlineRect(nodes) {
    let L = 1e9, T = 1e9, Rr = -1e9, Bt = -1e9, glyph = 0;
    for (const n of nodes) {
      let rects = [];
      if (n.nodeType === 3 && /\S/.test(n.textContent)) { const rg = document.createRange(); rg.selectNodeContents(n); rects = [...rg.getClientRects()]; }
      else if (n.nodeType === 1 && tag(n) !== 'br' && visible(n) && hasText(n)) rects = [...n.getClientRects()];
      for (const r of rects) {
        if (r.width === 0 && r.height === 0) continue;
        if (!glyph) glyph = r.height;
        L = Math.min(L, r.left); T = Math.min(T, r.top); Rr = Math.max(Rr, r.right); Bt = Math.max(Bt, r.bottom);
      }
    }
    return T < 1e9 ? {x: L - B.left, y: T - B.top, w: Rr - L, h: Bt - T, glyph: glyph} : null;
  }
  // an inline element that holds a block (a <cite> in a <span>) is opened up, so the block becomes its own item
  const holdsBlock = n => [...n.querySelectorAll('*')].some(d => !d.closest('mjx-container') && !isInline(d) && visible(d));
  function segments(el) {
    const out = []; let cur = [];
    const flat = n => {
      if (n.nodeType === 3) { cur.push(n); return; }
      if (n.nodeType !== 1 || !visible(n)) return;
      if (tag(n) === 'br' || isInline(n)) { if (tag(n) !== 'br' && tag(n) !== 'mjx-container' && holdsBlock(n)) [...n.childNodes].forEach(flat); else cur.push(n); return; }
      if (cur.length) out.push(cur);
      cur = [];
      out.push(n);                       // a block, picture or display formula between the text runs
    };
    [...el.childNodes].forEach(flat);
    if (cur.length) out.push(cur);
    return out;
  }
  function para(el, extra, nodes) {
    const cs = getComputedStyle(el);
    const lh = cs.lineHeight === 'normal' ? 1.2 * parseFloat(cs.fontSize) : parseFloat(cs.lineHeight);
    const rs = nodes ? nodes.reduce((o, n) => atomRuns(n, o), []) : runs(el, []);
    return Object.assign({runs: rs, align: cs.textAlign, lh: lh, sz: parseFloat(cs.fontSize),
                          c: color(cs.color), b: parseInt(cs.fontWeight) >= 600, step: stepOf(el)}, extra || {});
  }
  const ALPHA = 'abcdefghijklmnopqrstuvwxyz';
  const ROMAN = [[1000, 'm'], [900, 'cm'], [500, 'd'], [400, 'cd'], [100, 'c'], [90, 'xc'], [50, 'l'], [40, 'xl'], [10, 'x'], [9, 'ix'], [5, 'v'], [4, 'iv'], [1, 'i']];
  const counterText = (n, st) => {
    if (/alpha|latin/.test(st)) { const a = ALPHA[(n - 1) % 26]; return st.startsWith('upper') ? a.toUpperCase() : a; }
    if (/roman/.test(st)) { let r = '', k = n; for (const [v, t] of ROMAN) while (k >= v) { r += t; k -= v; } return st.startsWith('upper') ? r.toUpperCase() : r; }
    return String(n);
  };
  // the text a ::before draws: strings and counter(name, style); the nth item of its list stands in for the counter value
  function markerText(el, content) {
    if (!content || content === 'none' || content === 'normal') return '';
    const n = [...el.parentElement.children].filter(c => c.tagName === el.tagName).indexOf(el) + 1;
    let out = '';
    for (const m of content.matchAll(/"((?:[^"\\]|\\.)*)"|counters?\(\s*[\w-]+\s*(?:,\s*([\w-]+)\s*)?(?:,\s*"[^"]*"\s*)?\)/g))
      out += m[1] !== undefined ? m[1].replace(/\\(.)/g, '$1') : counterText(n, m[2] || 'decimal');
    return out;
  }
  function bulletOf(li) {
    const list = li.parentElement;
    const lcs = getComputedStyle(li), b = getComputedStyle(li, '::before');
    const ind = parseFloat(lcs.paddingLeft) + (tag(list) === 'ol' ? parseFloat(getComputedStyle(list).paddingLeft) : 0);
    if (b.display === 'none') return null;
    const text = markerText(li, b.content);
    if (text.trim()) {
      const st = style(li);
      return {kind: 'text', t: text.trim(), run: Object.assign(st, {c: color(b.color), b: parseInt(b.fontWeight) >= 600, sz: parseFloat(b.fontSize)}),
              ind: Math.max(ind, parseFloat(b.width) || 0, 1.4 * parseFloat(b.fontSize))};
    }
    if (tag(list) === 'ol' && lcs.listStyleType !== 'none')
      return {kind: 'num', start: [...list.children].indexOf(li) + 1, ind: parseFloat(getComputedStyle(list).paddingLeft)};
    if (b.content === 'none' || !color(b.backgroundColor)) return null;
    return {kind: 'sq', c: color(b.backgroundColor), size: parseFloat(b.width), ind: parseFloat(lcs.paddingLeft)};
  }

  // ── boxes: backgrounds, borders, clip-path shapes, ::before strips ──
  function box(el, r) {
    const cs = getComputedStyle(el);
    const fill = color(cs.backgroundColor);
    const sides = {};
    for (const s of ['Top', 'Right', 'Bottom', 'Left']) {
      const w = parseFloat(cs['border' + s + 'Width']);
      const c = color(cs['border' + s + 'Color']);
      if (w > 0 && cs['border' + s + 'Style'] !== 'none' && c) sides[s.toLowerCase()] = {w: w, c: c};
    }
    let shape = 'rect', notch = 0;
    if (cs.clipPath && cs.clipPath.startsWith('polygon')) {
      const pts = cs.clipPath.split(',').length;
      const m = /calc\(100% - ([\d.]+)px\)/.exec(cs.clipPath);
      notch = m ? parseFloat(m[1]) : 0;
      shape = pts >= 6 ? 'chevron' : 'pentagon';
    } else if (cs.transform && cs.transform !== 'none') {
      const m = /matrix\(([^)]+)\)/.exec(cs.transform);
      if (m) { const [a, b] = m[1].split(',').map(Number); if (Math.abs(Math.abs(Math.atan2(b, a)) - Math.PI / 4) < 0.05) shape = 'diamond'; }
    }
    const radius = parseFloat(cs.borderTopLeftRadius) || 0;
    const all = ['top', 'right', 'bottom', 'left'].every(s => sides[s]);
    return {fill: fill, sides: sides, all: all, shape: shape, notch: notch, radius: radius, r: r};
  }
  function emitBox(bx, el) {
    if (bx.fill || bx.all) items.push({type: 'box', x: bx.r.x, y: bx.r.y, w: bx.r.w, h: bx.r.h, fill: bx.fill,
      line: bx.all ? bx.sides.top : null, shape: bx.shape, notch: bx.notch, radius: bx.radius, step: stepOf(el), jump: jumpOf(el)});
    if (!bx.all) for (const [s, b] of Object.entries(bx.sides)) {
      const r = bx.r, h = b.w / 2;
      const seg = {top: [r.x, r.y + h, r.x + r.w, r.y + h], bottom: [r.x, r.y + r.h - h, r.x + r.w, r.y + r.h - h],
                   left: [r.x + h, r.y, r.x + h, r.y + r.h], right: [r.x + r.w - h, r.y, r.x + r.w - h, r.y + r.h]}[s];
      items.push({type: 'line', pts: seg, w: b.w, c: b.c, step: stepOf(el)});
    }
  }
  function pseudoStrip(el, r) {
    if (tag(el) === 'li') return;
    const b = getComputedStyle(el, '::before');
    if (b.content === 'none' || b.position !== 'absolute') return;
    const fill = color(b.backgroundColor); if (!fill) return;
    const w = parseFloat(b.width), h = parseFloat(b.height);
    if (!(w > 0 && h > 0)) return;
    items.push({type: 'box', x: r.x + (parseFloat(b.left) || 0), y: r.y + (parseFloat(b.top) || 0), w: w, h: h,
                fill: fill, line: null, shape: 'rect', notch: 0, radius: 0, step: stepOf(el)});
  }
  function pads(el) {
    const cs = getComputedStyle(el), f = k => parseFloat(cs[k]) || 0;
    return [f('paddingLeft') + f('borderLeftWidth'), f('paddingTop') + f('borderTopWidth'),
            f('paddingRight') + f('borderRightWidth'), f('paddingBottom') + f('borderBottomWidth')];
  }
  const role = el => { for (const [sel, name] of opts.roles || []) if (el.matches(sel)) return name; return ''; };
  const shot = (el, target) => { const id = 'x' + (xid++); (target || el).setAttribute('data-xid', id); return id; };

  function visit(el) {
    if (!visible(el) || el.matches('.stepdots') || matches(el, opts.chrome)) return;
    if (getComputedStyle(el).display === 'contents' && !isPara(el)) { [...el.children].forEach(c => visit(c)); return; }
    const boxOnly = matches(el, opts.boxOnly);
    const r = R(el);
    if (r.w < 0.5 || r.h < 0.5) { if (tag(el) !== 'svg') [...el.children].forEach(c => visit(c)); return; }
    const t = tag(el);

    if (t === 'img') {
      items.push({type: 'img', x: r.x, y: r.y, w: r.w, h: r.h, src: el.currentSrc || el.src,
                                xid: (el.currentSrc || el.src).startsWith('data:image/svg') ? shot(el) : null, step: stepOf(el)});
      return;
    }
    const bgImage = !el.children.length && !hasText(el) && /url\(/.test(getComputedStyle(el).backgroundImage);
    if (t === 'svg' || t === 'canvas' || t === 'video' || t === 'input' || t === 'select' || bgImage ||
        (t === 'mjx-container' && el.getAttribute('display') === 'true')) {
      const target = t === 'mjx-container' ? el.querySelector('svg') : el;
      if (target) { const q = R(target); items.push({type: 'img', x: q.x, y: q.y, w: q.w, h: q.h, xid: shot(el, target), step: stepOf(el), role: role(el)}); }
      return;
    }
    const bx = boxOnly ? {fill: null, sides: {}, all: false, r: r} : box(el, r);
    pseudoStrip(el, r);

    // a native table holds text only: a table with badges, bars or icons in its cells is rebuilt cell by cell
    const rich = t === 'table' && [...el.querySelectorAll('td *, th *')].some(e => ['svg', 'img', 'button', 'input', 'canvas'].includes(tag(e)) ||
                                                                              color(getComputedStyle(e).backgroundColor));
    if (t === 'table' && !rich) {
      emitBox(bx, el);
      const rows = [...el.rows].map(tr => [...tr.cells].map(td => {
        const cb = box(td, R(td));
        return {r: R(td), p: para(td), bottom: cb.sides.bottom || null, top: cb.sides.top || null, fill: cb.fill, pad: pads(td), span: td.colSpan};
      }));
      items.push({type: 'table', x: r.x, y: r.y, w: r.w, h: r.h, rows: rows, step: stepOf(el)});
      return;
    }
    if ((t === 'ul' || t === 'ol') && [...el.children].every(li => tag(li) === 'li' && blockKids(li).length === 0)) {
      emitBox(bx, el);
      const lis = [...el.children].filter(visible);
      let prev = null;
      const paras = lis.map(li => {
        emitBox(box(li, R(li)), li);
        const q = R(li), p = para(li, {bullet: bulletOf(li), before: prev === null ? 0 : q.y - prev});
        prev = q.y + q.h; return p;
      });
      const lcs = getComputedStyle(el), ncol = parseInt(lcs.columnCount) || 1;
      items.push({type: 'text', x: r.x, y: r.y, w: r.w, h: r.h, pad: [0, R(lis[0] || el).y - r.y, 0, 0], paras: paras,
                  cols: ncol > 1 ? [ncol, parseFloat(lcs.columnGap) || 0] : null,
                  step: stepOf(el), jump: jumpOf(el), role: ''});
      return;
    }
    if (isPara(el)) {
      const pd = pads(el), segs = segments(el), texts = segs.filter(g => Array.isArray(g));
      const fillMe = (bx.fill || bx.all) && !Object.keys(bx.sides).some(s => !bx.all) && texts.length === 1;
      if (!fillMe) emitBox(bx, el);
      const cL = r.x + pd[0], cR = r.x + r.w - pd[2];
      let first = true;
      for (const g of segs) {
        if (!Array.isArray(g)) { visit(g); continue; }
        const ir = inlineRect(g);
        if (!ir) continue;
        // a line that is only a formula stays a formula: a picture of the typeset math, not linearised text
        const maths = g.filter(n => n.nodeType === 1 && tag(n) === 'mjx-container');
        const lone = maths.length && g.every(n => maths.includes(n) || (n.nodeType === 1 && tag(n) === 'br') ||
                                                    (n.nodeType === 3 && !/\S/.test(n.textContent)));
        if (lone && (maths.length === 1 || g.some(n => n.nodeType === 1 && tag(n) === 'br'))) {
          for (const mj of maths) {
            const sv = mj.querySelector('svg');
            if (sv) { const q = R(sv); items.push({type: 'img', x: q.x, y: q.y, w: q.w, h: q.h, xid: shot(mj, sv), step: stepOf(mj)}); }
          }
          first = false;
          continue;
        }
        const bullet = t === 'li' && first ? bulletOf(el) : null;
        const p = para(el, {bullet: bullet, before: 0}, g);
        // the first line box starts half a leading above the glyphs
        const glyph = ir.glyph || Math.min(ir.h, p.lh);
        const lines = 1 + Math.max(0, Math.round((ir.h - glyph) / p.lh));
        const top = ir.y - Math.max(0, (p.lh - glyph) / 2);
        const left = /^(left|start|justify)$/.test(p.align);
        let bx2, pad;
        if (fillMe || bullet) {          // the element's own box (its fill, or room for the marker), text moved to where it is drawn
          const ind = bullet ? bullet.ind : 0;
          const lpad = !bullet && lines === 1 && left ? ir.x - r.x : pd[0] - ind;   // flex centring shows up in ir.x
          bx2 = {x: r.x, y: r.y, w: r.w, h: r.h};
          pad = [Math.max(0, lpad), Math.max(0, top - r.y), lines === 1 && left ? 0 : pd[2], 0];
        } else if (lines === 1 && left) {
          bx2 = {x: ir.x, y: top, w: Math.max(cR - ir.x, ir.w + 4), h: p.lh};
          pad = [0, 0, 0, 0];
        } else {
          bx2 = {x: cL, y: top, w: cR - cL, h: lines * p.lh};
          pad = [0, 0, 0, 0];
        }
        items.push({type: 'text', x: bx2.x, y: bx2.y, w: bx2.w, h: bx2.h, pad: pad, paras: [p],
                    fill: fillMe ? bx.fill : null, line: fillMe && bx.all ? bx.sides.top : null, radius: bx.radius,
                    step: stepOf(el), jump: jumpOf(el), role: first ? role(el) : '', single: lines === 1});
        first = false;
      }
      return;
    }
    emitBox(bx, el);
    [...el.children].forEach(c => visit(c));
  }
  [...S.children].forEach(c => visit(c));
  return items;
}
