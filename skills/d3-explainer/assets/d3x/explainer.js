/* D3 explainer runtime (global D3X). Inlined by build.py; never edited per project.
   API reference: references/components.md in the d3-explainer skill. */
(function () {
'use strict';
var NS = 'http://www.w3.org/2000/svg';
/* Theme colours. A project adds its own colour code through [[role]] in explainer.toml (window.D3X_ROLES):
   color('choice') then resolves to that role, in plots exactly as \\choice{...} does in formulas. */
var THEME = {ink: '#0F2347', ink2: '#3F4F6B', ink3: '#74809A', rule: '#CFDAEA', rule2: '#B5C4DB', paper: '#F2F5FA', paper2: '#E4EBF5', card: '#FFFFFF',
  navy: '#153F87', orange: '#F29100', teal: '#4D9AAA', darkblue: '#0A2864', lightblue: '#C8DCF0', gray: '#808080',
  accent: '#F29100', c1: '#153F87', c2: '#4D9AAA', c3: '#0A2864', idle: '#808080', control: '#153F87', white: '#FFFFFF', black: '#000000'};
var SERIES = ['navy', 'orange', 'teal'];   // default order for unnamed series; a 4th series gets idle + dash, see visualization.md

function hex2rgb(h) { h = h.replace('#', ''); if (h.length === 3) h = h.replace(/(.)/g, '$1$1');
  return [0, 2, 4].map(function (i) { return parseInt(h.substr(i, 2), 16); }); }
/** a theme colour ('c1', 'accent', 'idle', 'ink' ...), a project role ('choice'), a tint ('c1!30', mixed with the card colour), '#hex', or any CSS colour */
function color(spec) {
  if (!spec) return THEME.c1;
  var m = /^([a-z0-9]+)!(\d+(?:\.\d+)?)$/i.exec(spec);
  var name = m ? m[1] : spec, base = (window.D3X_ROLES || {})[name] || THEME[name];
  if (!base) return spec;
  if (!m) return base;
  var t = Math.max(0, Math.min(100, +m[2])) / 100, c = hex2rgb(base), bg = hex2rgb(THEME.card);      // tints mix with the card colour, not with white
  return '#' + c.map(function (v, i) { return ('0' + Math.round(v * t + bg[i] * (1 - t)).toString(16)).slice(-2); }).join('');
}
function S(tag, attrs, parent, text) {
  var e = document.createElementNS(NS, tag), k;
  for (k in attrs) if (attrs[k] != null) e.setAttribute(k, attrs[k]);
  if (text != null) e.textContent = tag === 'text' || tag === 'title' ? plain(text) : text;
  if (parent) parent.appendChild(e);
  return e;
}
function H(tag, cls, parent, text) {
  var e = document.createElement(tag);
  if (cls) e.className = cls;
  if (text != null) e.textContent = text;
  if (parent) parent.appendChild(e);
  return e;
}
function clamp(v, a, b) { return Math.max(a, Math.min(b, v)); }
/* SVG <text> cannot host KaTeX. Labels inside figures may still be written as '$c_{\\max}$':
   plain() turns simple TeX into Unicode (Greek, sub- and superscripts, common operators). */
var GREEK = {alpha: 'α', beta: 'β', gamma: 'γ', delta: 'δ', epsilon: 'ε', varepsilon: 'ε', zeta: 'ζ', eta: 'η', theta: 'θ', vartheta: 'ϑ', iota: 'ι',
  kappa: 'κ', lambda: 'λ', mu: 'μ', nu: 'ν', xi: 'ξ', pi: 'π', rho: 'ρ', sigma: 'σ', tau: 'τ', upsilon: 'υ', phi: 'φ', varphi: 'φ', chi: 'χ', psi: 'ψ', omega: 'ω',
  Gamma: 'Γ', Delta: 'Δ', Theta: 'Θ', Lambda: 'Λ', Xi: 'Ξ', Pi: 'Π', Sigma: 'Σ', Phi: 'Φ', Psi: 'Ψ', Omega: 'Ω',
  star: '*', ast: '*', cdot: '·', times: '×', leq: '≤', le: '≤', geq: '≥', ge: '≥', neq: '≠', approx: '≈', infty: '∞', pm: '±', to: '→', rightarrow: '→',
  partial: '∂', nabla: '∇', sum: 'Σ', prod: 'Π', int: '∫', in: '∈', ell: 'ℓ', dots: '…', ldots: '…', quad: ' ', qquad: '  ', euro: '€', sqrt: '√'};
var SUB = {'0': '₀', '1': '₁', '2': '₂', '3': '₃', '4': '₄', '5': '₅', '6': '₆', '7': '₇', '8': '₈', '9': '₉', '+': '₊', '-': '₋', a: 'ₐ', e: 'ₑ', h: 'ₕ', i: 'ᵢ', j: 'ⱼ',
  k: 'ₖ', l: 'ₗ', m: 'ₘ', n: 'ₙ', o: 'ₒ', p: 'ₚ', r: 'ᵣ', s: 'ₛ', t: 'ₜ', u: 'ᵤ', v: 'ᵥ', x: 'ₓ'};
var SUP = {'0': '⁰', '1': '¹', '2': '²', '3': '³', '4': '⁴', '5': '⁵', '6': '⁶', '7': '⁷', '8': '⁸', '9': '⁹', '+': '⁺', '-': '⁻', n: 'ⁿ', i: 'ⁱ', '*': '*', T: 'ᵀ'};
function script(body, map, fallback) {
  var out = '', i; for (i = 0; i < body.length; i++) { if (!map[body[i]]) return fallback + body; out += map[body[i]]; } return out; }
function plain(str) {
  if (str == null) return str; str = String(str);
  if (str.indexOf('$') < 0 && str.indexOf('\\') < 0) return str;
  return str.replace(/\$/g, '')
    .replace(/\\(?:mathrm|mathbf|mathit|mathcal|mathbb|text|operatorname|bar|hat|tilde|vec|boldsymbol)\s*\{([^{}]*)\}/g, '$1')
    .replace(/\\(?:bar|hat|tilde|vec|mathbf|mathrm|boldsymbol|mathcal|mathbb)\b\s*/g, '')
    .replace(/\\frac\s*\{([^{}]*)\}\s*\{([^{}]*)\}/g, '($1)/($2)')
    .replace(/\\([A-Za-z]+)/g, function (m, name) { return GREEK[name] != null ? GREEK[name] : name; })
    .replace(/_\{([^{}]*)\}/g, function (m, b) { return script(b, SUB, '_'); }).replace(/_([A-Za-z0-9])/g, function (m, b) { return script(b, SUB, '_'); })
    .replace(/\^\{([^{}]*)\}/g, function (m, b) { return script(b, SUP, '^'); }).replace(/\^([A-Za-z0-9*])/g, function (m, b) { return script(b, SUP, '^'); })
    .replace(/[{}]/g, '').replace(/\\[,;! ]/g, ' ').replace(/\s+/g, ' ').trim();
}
function niceStep(span, n) {
  var raw = span / Math.max(1, n), mag = Math.pow(10, Math.floor(Math.log10(raw))), r = raw / mag;
  return (r >= 7.5 ? 10 : r >= 3.5 ? 5 : r >= 1.5 ? 2 : 1) * mag;
}
function ticks(a, b, n) {
  if (!(b > a)) return [a];
  var st = niceStep(b - a, n || 5), t0 = Math.ceil(a / st - 1e-9) * st, out = [], v;
  for (v = t0; v <= b + st * 1e-9; v += st) out.push(Math.abs(v) < st * 1e-9 ? 0 : v);
  return out;
}
function fmtFor(step) {
  var d = clamp(-Math.floor(Math.log10(Math.abs(step) || 1) + 1e-9), 0, 8);
  return function (v) {
    if (Math.abs(v) >= 10000) return v.toLocaleString('en-US', {maximumFractionDigits: 0});
    return v.toFixed(d);
  };
}
function fmtAuto(v) {
  if (v == null || !isFinite(v)) return String(v);
  var a = Math.abs(v);
  if (a >= 10000) return v.toLocaleString('en-US', {maximumFractionDigits: 0});
  if (a >= 100) return v.toFixed(0);
  if (a >= 10) return v.toFixed(1);
  if (a >= 1) return v.toFixed(2);
  if (a === 0) return '0';
  return v.toPrecision(2);
}
/** Seeded RNG (mulberry32). r() in [0,1); r.normal(); r.range(a,b); r.int(n) */
function rng(seed) {
  var s = seed >>> 0;
  function r() { s = (s + 0x6D2B79F5) >>> 0; var t = s; t = Math.imul(t ^ (t >>> 15), t | 1);
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61); return ((t ^ (t >>> 14)) >>> 0) / 4294967296; }
  r.normal = function (mu, sd) { var u = 0, v = 0; while (!u) u = r(); while (!v) v = r();
    return (mu || 0) + (sd == null ? 1 : sd) * Math.sqrt(-2 * Math.log(u)) * Math.cos(2 * Math.PI * v); };
  r.range = function (a, b) { return a + (b - a) * r(); };
  r.int = function (n) { return Math.floor(r() * n); };
  return r;
}
function hash(str) { var h = 2166136261, i; str = String(str); for (i = 0; i < str.length; i++) { h ^= str.charCodeAt(i); h = Math.imul(h, 16777619); } return h >>> 0; }

/* ------------------------------------------------------------------ math + chips */
var MATH_OPTS = null;
function renderMath(el) {
  if (!window.renderMathInElement) return;
  if (!MATH_OPTS) MATH_OPTS = {
    delimiters: [{left: '$$', right: '$$', display: true}, {left: '\\[', right: '\\]', display: true},
      {left: '\\(', right: '\\)', display: false}, {left: '$', right: '$', display: false}],
    macros: Object.assign({}, window.D3X_MACROS || {}), throwOnError: false, errorColor: '#B4572A', strict: 'ignore',
    ignoredClasses: ['nomath', 'chip']};
  try { window.renderMathInElement(el, MATH_OPTS); } catch (e) { console.error('D3X math: ' + e.message); }
}
var CHIP_RE = /\[\[(code|paper|vault|result|file|reading|src)(?::([^\]]*))?\]\]/g;
var KIND_LABEL = {code: 'code', paper: 'paper', vault: 'vault', result: 'result', file: 'file', reading: 'my reading', src: 'source'};
function makeChip(kind, body) {
  var key = kind + (body ? ':' + body : ''), info = (window.D3X_CHIPS || {})[key] || {};
  var e = document.createElement(info.href ? 'a' : 'span');
  e.className = 'chip k-' + kind + (info.ok === false ? ' bad' : '');
  if (info.href) { e.href = info.href; e.target = '_blank'; e.rel = 'noopener'; }
  e.title = info.title || (body || KIND_LABEL[kind]);
  H('i', '', e, KIND_LABEL[kind]);
  var label = info.label || (body || '').split('|').pop();
  if (label) e.appendChild(document.createTextNode(label));
  return e;
}
function chipify(root) {
  var walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT, {acceptNode: function (n) {
    if (n.nodeValue.indexOf('[[') < 0) return NodeFilter.FILTER_REJECT;
    for (var p = n.parentNode; p && p !== root.parentNode; p = p.parentNode)
      if (/^(SCRIPT|STYLE|PRE|CODE|TEXTAREA)$/.test(p.nodeName)) return NodeFilter.FILTER_REJECT;
    return NodeFilter.FILTER_ACCEPT; }});
  var nodes = [], n; while ((n = walker.nextNode())) nodes.push(n);
  nodes.forEach(function (node) {
    var txt = node.nodeValue, frag = document.createDocumentFragment(), last = 0, m;
    CHIP_RE.lastIndex = 0;
    while ((m = CHIP_RE.exec(txt))) {
      if (m.index > last) frag.appendChild(document.createTextNode(txt.slice(last, m.index)));
      frag.appendChild(makeChip(m[1], m[2] || '')); last = m.index + m[0].length;
    }
    if (!last) return;
    if (last < txt.length) frag.appendChild(document.createTextNode(txt.slice(last)));
    node.parentNode.replaceChild(frag, node);
  });
}
function enrich(el) { chipify(el); renderMath(el); }

/* ------------------------------------------------------------------ plot */
function Plot(w, o) {
  o = o || {};
  var cell = o.cell || [0, 1], stack = w.narrow && cell[1] > 1;      // on a phone, side-by-side panels stack
  var cw = stack ? w.W : w.W / cell[1], ox = stack ? 0 : cw * cell[0];
  var m = Object.assign({l: 56, r: 20, t: o.title ? 30 : 16, b: o.x && o.x.label || o.xlabel ? 46 : 32}, o.margin || {});
  var X = axisSpec(o.x, o.xlabel), Y = axisSpec(o.y, o.ylabel);
  var top = stack ? cell[0] * w.H0 : (o.top || 0), height = stack ? w.H0 : (o.height || (w.H0 - top));
  w.usedH = Math.max(w.usedH || 0, top + height);
  var x0 = ox + m.l, x1 = ox + cw - m.r, y0 = top + height - m.b, y1 = top + m.t;
  var self = this;
  this.w = w; this.X = X; this.Y = Y; this.box = {x0: x0, x1: x1, y0: y0, y1: y1}; this.series = [];
  function axisSpec(a, label) {
    if (Array.isArray(a)) a = {domain: a};
    a = Object.assign({domain: [0, 1]}, a || {});
    if (label && !a.label) a.label = label;
    if (a.bands) a.domain = [0, a.bands.length];
    return a;
  }
  function sc(A, lo, hi) {
    var d0 = A.domain[0], d1 = A.domain[1];
    if (A.log) { var l0 = Math.log10(d0), l1 = Math.log10(d1);
      return {f: function (v) { return lo + (Math.log10(Math.max(v, 1e-300)) - l0) / (l1 - l0) * (hi - lo); },
              i: function (p) { return Math.pow(10, l0 + (p - lo) / (hi - lo) * (l1 - l0)); }}; }
    return {f: function (v) { return lo + (v - d0) / (d1 - d0) * (hi - lo); },
            i: function (p) { return d0 + (p - lo) / (hi - lo) * (d1 - d0); }};
  }
  var sx = sc(X, x0, x1), sy = sc(Y, y0, y1);
  this.sx = sx.f; this.sy = sy.f; this.ix = sx.i; this.iy = sy.i;
  this.bx = function (i) { return sx.f(i + 0.5); };            // centre of band i
  this.bw = function () { return Math.abs(sx.f(1) - sx.f(0)); }; // width of one band

  var g = S('g', {'class': 'plot'}, w.content);
  var clipId = w.id + '-clip' + w.plots.length;
  S('rect', {x: x0, y: y1, width: x1 - x0, height: y0 - y1}, S('clipPath', {id: clipId}, S('defs', {}, g)));
  var gAxes = S('g', {}, g);
  this.marks = S('g', {'clip-path': 'url(#' + clipId + ')'}, g);
  this.dots = S('g', {}, g);
  this.over = S('g', {}, g);
  if (o.title) S('text', {x: x0, y: top + 16, 'font-size': 10, 'letter-spacing': '.14em', fill: THEME.ink3}, gAxes, String(o.title).toUpperCase());

  // y grid + ticks
  var yt = Y.log ? logTicks(Y.domain) : ticks(Y.domain[0], Y.domain[1], Y.ticks || 5);
  var yf = Y.fmt || (Y.log ? fmtLog : fmtFor(yt.length > 1 ? yt[1] - yt[0] : 1));
  yt.forEach(function (v) {
    var py = sy.f(v);
    if (o.grid !== false) S('line', {x1: x0, x2: x1, y1: py, y2: py, stroke: v === 0 ? THEME.rule2 : THEME.rule, 'stroke-width': 1}, gAxes);
    S('text', {x: x0 - 8, y: py + 3.8, 'text-anchor': 'end', 'font-size': 10, fill: THEME.ink3}, gAxes, yf(v));
  });
  S('line', {x1: x0, x2: x1, y1: y0, y2: y0, stroke: THEME.rule2, 'stroke-width': 1}, gAxes);
  if (X.bands) X.bands.forEach(function (name, i) {
    S('text', {x: self.bx(i), y: y0 + 16, 'text-anchor': 'middle', 'font-size': 10.5, fill: THEME.ink2}, gAxes, name); });
  else {
    var xt = X.log ? logTicks(X.domain) : ticks(X.domain[0], X.domain[1], X.ticks || 6);
    var xf = X.fmt || (X.log ? fmtLog : fmtFor(xt.length > 1 ? xt[1] - xt[0] : 1));
    xt.forEach(function (v) {
      var px = sx.f(v);
      S('line', {x1: px, x2: px, y1: y0, y2: y0 + 4, stroke: THEME.rule2}, gAxes);
      S('text', {x: px, y: y0 + 16, 'text-anchor': 'middle', 'font-size': 10, fill: THEME.ink3}, gAxes, xf(v));
    });
    this.xfmt = xf;
  }
  this.yfmt = yf;
  if (X.label) S('text', {x: (x0 + x1) / 2, y: y0 + 36, 'text-anchor': 'middle', 'font-size': 10.5, 'letter-spacing': '.06em', fill: THEME.ink2}, gAxes, X.label);
  if (Y.label) S('text', {x: ox + 14, y: (y0 + y1) / 2, 'text-anchor': 'middle', 'font-size': 10.5, 'letter-spacing': '.06em', fill: THEME.ink2,
    transform: 'rotate(-90 ' + (ox + 14) + ' ' + (y0 + y1) / 2 + ')'}, gAxes, Y.label);
  function logTicks(d) { // decades, plus 2 and 5 when the axis spans three decades or fewer
    var out = [], e, lo = Math.floor(Math.log10(d[0]) + 1e-9), hi = Math.ceil(Math.log10(d[1]) - 1e-9), mult = hi - lo <= 3 ? [1, 2, 5] : [1];
    for (e = lo; e <= hi; e++) mult.forEach(function (k) { var v = k * Math.pow(10, e); if (v >= d[0] * (1 - 1e-9) && v <= d[1] * (1 + 1e-9)) out.push(v); });
    return out; }
  function fmtLog(v) { return v >= 1 ? (v >= 10000 ? v.toLocaleString('en-US') : String(Math.round(v))) : String(+v.toPrecision(2)); }
  w.plots.push(this);
}
Plot.prototype._path = function (xs, ys) {
  var d = '', pen = false, i, px, py;
  for (i = 0; i < xs.length; i++) {
    px = this.sx(xs[i]); py = this.sy(ys[i]);
    if (!isFinite(px) || !isFinite(py)) { pen = false; continue; }
    d += (pen ? 'L' : 'M') + px.toFixed(1) + ' ' + py.toFixed(1); pen = true;
  }
  return d;
};
Plot.prototype._legend = function (o, shape) {
  if (o.label) this.w.legend.push({label: o.label, color: color(o.color), shape: o.dash ? 'dash' : shape});
};
/** line through (xs, ys). opts: color, label, width, dash, end (direct label at the line end), hover (default true) */
Plot.prototype.line = function (xs, ys, o) {
  o = o || {};
  var c = color(o.color || SERIES[this.series.length % 3]);
  S('path', {d: this._path(xs, ys), fill: 'none', stroke: c, 'stroke-width': o.width || 2, 'stroke-linejoin': 'round',
    'stroke-linecap': 'round', 'stroke-dasharray': o.dash ? (o.dash === true ? '6 4' : o.dash) : null, opacity: o.opacity, 'data-series': 1}, this.marks);
  if (o.hover !== false) this.series.push({xs: xs, ys: ys, color: c, label: o.label || ''});
  this._legend(Object.assign({}, o, {color: c}), 'line');
  if (o.end && xs.length) { var n = xs.length - 1;
    S('circle', {cx: this.sx(xs[n]), cy: this.sy(ys[n]), r: 4, fill: c, stroke: THEME.card, 'stroke-width': 2}, this.over);
    S('text', {x: this.sx(xs[n]) + 8, y: this.sy(ys[n]) + 4, 'font-size': 10.5, fill: THEME.ink2}, this.over, o.end === true ? (o.label || '') : o.end); }
  return this;
};
/** plot y = f(x) over the x-domain (or opts.from/to) with opts.n samples */
Plot.prototype.fn = function (f, o) {
  o = o || {};
  var a = o.from != null ? o.from : this.X.domain[0], b = o.to != null ? o.to : this.X.domain[1], n = o.n || 240, xs = [], ys = [], i, x;
  for (i = 0; i <= n; i++) { x = this.X.log ? a * Math.pow(b / a, i / n) : a + (b - a) * i / n; xs.push(x); ys.push(f(x)); }
  return this.line(xs, ys, o);
};
/** filled area between ys and base (number or array, default 0) */
Plot.prototype.area = function (xs, ys, base, o) {
  if (base && typeof base === 'object' && !Array.isArray(base)) { o = base; base = 0; }
  o = o || {}; if (base == null) base = 0;
  var self = this, c = color(o.color || 'c1'), d = '', run = [], i;
  function b(k) { return Array.isArray(base) ? base[k] : base; }
  function flush() { if (run.length > 1) {
      d += run.map(function (k, j) { return (j ? 'L' : 'M') + self.sx(xs[k]).toFixed(1) + ' ' + self.sy(ys[k]).toFixed(1); }).join('');
      d += run.slice().reverse().map(function (k) { return 'L' + self.sx(xs[k]).toFixed(1) + ' ' + self.sy(b(k)).toFixed(1); }).join('') + 'Z'; } run = []; }
  for (i = 0; i < xs.length; i++) { if (isFinite(xs[i]) && isFinite(ys[i]) && isFinite(b(i))) run.push(i); else flush(); }   // NaN breaks the area, as it breaks a line
  flush();
  S('path', {d: d, fill: c, opacity: o.opacity != null ? o.opacity : 0.12, stroke: 'none'}, this.marks);
  this._legend(Object.assign({}, o, {color: c}), 'box');
  return this;
};
Plot.prototype.band = function (xs, lo, hi, o) { return this.area(xs, hi, lo, o); };
/** scatter. opts: color, r, label, opacity, titles (array of hover strings) */
Plot.prototype.scatter = function (xs, ys, o) {
  o = o || {};
  var c = color(o.color || SERIES[0]), r = o.r || 4, i, e, px, py, B = this.box;
  for (i = 0; i < xs.length; i++) {
    px = this.sx(xs[i]); py = this.sy(ys[i]);
    if (!isFinite(px) || !isFinite(py)) continue;
    if (!(px >= B.x0 - 0.5 && px <= B.x1 + 0.5 && py >= B.y1 - 0.5 && py <= B.y0 + 0.5)) {        // off the scale: a hollow mark at the edge, never a silent drop
      e = S('circle', {cx: clamp(px, B.x0, B.x1), cy: clamp(py, B.y1, B.y0), r: r, fill: '#fff', stroke: c, 'stroke-width': 1.5, 'data-offscale': 1}, this.dots);
      S('title', {}, e, 'off the scale: ' + (this.xfmt ? this.xfmt(xs[i]) : xs[i]) + ', ' + fmtAuto(ys[i])); continue; }
    e = S('circle', {cx: px, cy: py, r: r, fill: c, opacity: o.opacity != null ? o.opacity : 0.8,
      stroke: THEME.card, 'stroke-width': r >= 4 ? 1.5 : 0.5}, this.dots);
    S('title', {}, e, o.titles ? o.titles[i] : (this.xfmt ? this.xfmt(xs[i]) : xs[i]) + ', ' + fmtAuto(ys[i]));
  }
  if (o.hover !== false && o.label) this.series.push({xs: xs, ys: ys, color: c, label: o.label, nearest: true});
  this._legend(Object.assign({}, o, {color: c}), 'dot');
  return this;
};
/** bars over a band axis (x: {bands:[...]}). values[i] belongs to band i. opts: color, colors[], label, series:[k,n] for grouped bars, values:true to print values */
Plot.prototype.bars = function (values, o) {
  o = o || {};
  var grp = o.series || [0, 1], bw = Math.min(28, this.bw() * 0.7 / grp[1]), self = this, zero = this.sy(Math.max(this.Y.domain[0], 0));
  values.forEach(function (v, i) {
    var cx = self.bx(i) + (grp[0] - (grp[1] - 1) / 2) * (bw + 2), py = self.sy(v), c = color((o.colors && o.colors[i]) || o.color || 'c1');
    var yTop = Math.min(py, zero), h = Math.max(1, Math.abs(zero - py)), r = Math.min(4, h, bw / 2);
    var up = py <= zero, x = cx - bw / 2;
    var d = up
      ? 'M' + x + ' ' + (yTop + h) + 'V' + (yTop + r) + 'Q' + x + ' ' + yTop + ' ' + (x + r) + ' ' + yTop + 'H' + (x + bw - r) + 'Q' + (x + bw) + ' ' + yTop + ' ' + (x + bw) + ' ' + (yTop + r) + 'V' + (yTop + h) + 'Z'
      : 'M' + x + ' ' + yTop + 'V' + (yTop + h - r) + 'Q' + x + ' ' + (yTop + h) + ' ' + (x + r) + ' ' + (yTop + h) + 'H' + (x + bw - r) + 'Q' + (x + bw) + ' ' + (yTop + h) + ' ' + (x + bw) + ' ' + (yTop + h - r) + 'V' + yTop + 'Z';
    var e = S('path', {d: d, fill: c}, self.marks);
    S('title', {}, e, (self.X.bands ? self.X.bands[i] : i) + (o.label ? ' · ' + o.label : '') + ': ' + fmtAuto(v));
    if (o.values) S('text', {x: cx, y: up ? yTop - 5 : yTop + h + 13, 'text-anchor': 'middle', 'font-size': 10.5, 'font-weight': 600, fill: THEME.ink},
      self.over, (o.fmt || fmtAuto)(v));
  });
  this._legend(o, 'box');
  return this;
};
Plot.prototype.hline = function (y, o) { o = o || {};
  var py = this.sy(y), c = color(o.color || 'idle');
  if (!(py >= this.box.y1 - 0.5 && py <= this.box.y0 + 0.5)) return this;      // outside the axis: nothing to draw, and no stray label
  S('line', {x1: this.box.x0, x2: this.box.x1, y1: py, y2: py, stroke: c, 'stroke-width': o.width || 1.5, 'stroke-dasharray': o.dash === false ? null : '5 4'}, this.marks);
  if (o.label) S('text', {x: o.anchor === 'start' ? this.box.x0 + 4 : this.box.x1 - 4, y: py - 5 + (o.dy || 0), 'text-anchor': o.anchor === 'start' ? 'start' : 'end', 'font-size': 10.5, fill: THEME.ink2, 'paint-order': 'stroke', stroke: THEME.card, 'stroke-width': 3}, this.over, o.label);
  return this; };
Plot.prototype.vline = function (x, o) { o = o || {};
  var px = this.sx(x), c = color(o.color || 'idle');
  if (!(px >= this.box.x0 - 0.5 && px <= this.box.x1 + 0.5)) return this;
  S('line', {x1: px, x2: px, y1: this.box.y0, y2: this.box.y1, stroke: c, 'stroke-width': o.width || 1.5, 'stroke-dasharray': o.dash === false ? null : '5 4'}, this.marks);
  if (o.label) S('text', {x: px + (o.anchor === 'end' ? -5 : 5), y: this.box.y1 + 12 + (o.dy || 0), 'text-anchor': o.anchor === 'end' ? 'end' : 'start', 'font-size': 10.5, fill: THEME.ink2, 'paint-order': 'stroke', stroke: THEME.card, 'stroke-width': 3}, this.over, o.label);
  return this; };
/** shaded vertical region x in [a,b] */
Plot.prototype.region = function (a, b, o) { o = o || {};
  var xa = this.sx(a), xb = this.sx(b);
  S('rect', {x: Math.min(xa, xb), y: this.box.y1, width: Math.abs(xb - xa), height: this.box.y0 - this.box.y1, fill: color(o.color || 'c1!22'), opacity: o.opacity != null ? o.opacity : 0.35}, this.marks);
  if (o.label) S('text', {x: (xa + xb) / 2, y: this.box.y1 + 14, 'text-anchor': 'middle', 'font-size': 11.5, fill: THEME.ink2}, this.over, o.label);
  return this; };
Plot.prototype.point = function (x, y, o) { o = o || {};
  S('circle', {cx: this.sx(x), cy: this.sy(y), r: o.r || 5, fill: color(o.color || 'accent'), stroke: THEME.card, 'stroke-width': 2}, this.over);
  if (o.label) this.text(x, y, o.label, {dx: o.dx != null ? o.dx : 9, dy: o.dy != null ? o.dy : -8, anchor: o.anchor});
  return this; };
Plot.prototype.text = function (x, y, str, o) { o = o || {};
  // labels flip to the other side of their anchor instead of running off the figure
  var size = o.size || 10.5, dx = o.dx || 0, px = this.sx(x), py = this.sy(y) + (o.dy || 0), anchor = o.anchor || 'start';
  var wEst = String(str).length * size * 0.62, W = this.w.W, Hh = this.w.H;
  if (anchor === 'start' && px + dx + wEst > W - 4) { anchor = 'end'; dx = -Math.abs(dx); }
  else if (anchor === 'end' && px + dx - wEst < 4) { anchor = 'start'; dx = Math.abs(dx); }
  else if (anchor === 'middle') px = clamp(px, wEst / 2 + 4, W - wEst / 2 - 4);
  S('text', {x: px + dx, y: clamp(py, size + 2, Hh - 4), 'text-anchor': anchor, 'font-size': size,
    'font-weight': o.bold ? 600 : null, fill: color(o.color || 'ink2'), 'paint-order': 'stroke', stroke: THEME.card, 'stroke-width': 3, 'stroke-linejoin': 'round'}, this.over, str);
  return this; };
Plot.prototype.arrow = function (xa, ya, xb, yb, o) { o = o || {};
  var c = color(o.color || 'ink2'), id = this.w.arrowMarker(c);
  S('line', {x1: this.sx(xa), y1: this.sy(ya), x2: this.sx(xb), y2: this.sy(yb), stroke: c, 'stroke-width': 1.5, 'marker-end': 'url(#' + id + ')'}, this.over);
  if (o.label) this.text(xa, ya, o.label, {dx: o.dx || 0, dy: o.dy != null ? o.dy : -6, anchor: o.anchor || 'middle'});
  return this; };
/** draggable handle at (x, y). opts.setX / opts.setY name the widget params it writes; opts.label */
Plot.prototype.handle = function (x, y, o) { o = o || {};
  // a handle that leaves the plot area would be impossible to grab again: pin it to the frame
  var px = clamp(this.sx(x), this.box.x0, this.box.x1), py = clamp(this.sy(y), this.box.y1, this.box.y0), gH = S('g', {'class': 'handle'}, this.over);
  S('circle', {cx: px, cy: py, r: 13, fill: color('orange'), opacity: 0.18}, gH);
  S('circle', {cx: px, cy: py, r: 6.5, fill: color('orange'), stroke: THEME.card, 'stroke-width': 2}, gH);
  if (o.label) this.text(this.ix(px), this.iy(py), o.label, {dx: 12, dy: -10, bold: true, color: 'ink'});
  this.w.handles.push({px: px, py: py, plot: this, setX: o.setX, setY: o.setY});
  return this; };

/* ------------------------------------------------------------------ widget */
var widgets = [], queue = [], booted = false;
function Widget(id, spec) {
  var fig = document.getElementById(id);
  if (!fig) { console.error('D3X.widget: no element with id "' + id + '"'); return; }
  var w = this; this.id = id; this.spec = spec; this.fig = fig;
  this.W0 = spec.width || (fig.classList.contains('wide') ? 960 : 720); this.H0 = spec.height || 320; this.W = this.W0; this.H = this.H0;
  this.params = spec.params || {}; this.state = {seed: spec.seed || 1}; this.defaults = {};
  Object.keys(this.params).forEach(function (k) { var v = w.params[k].value; if (v === undefined) v = w.params[k].min || 0; w.state[k] = v; w.defaults[k] = v; });

  var box = H('div', 'figbox'), cap = fig.querySelector('figcaption');
  fig.insertBefore(box, cap);
  this.stage = H('div', 'stage', box);
  this.svg = S('svg', {viewBox: '0 0 ' + this.W + ' ' + this.H, role: 'img', 'aria-label': spec.alt || (cap ? cap.textContent.trim().slice(0, 140) : id)}, this.stage);
  this.defs = S('defs', {}, this.svg);
  this.content = S('g', {}, this.svg);
  this.hover = S('g', {'pointer-events': 'none'}, this.svg);
  this.tip = H('div', 'tip', this.stage);
  this.legendEl = H('div', 'legend', box);
  this.ctrlEl = H('div', 'ctrls', box);
  this.actEl = H('div', 'acts', box);
  this.roEl = H('div', 'readouts', box);
  this.dynEl = H('div', 'dyn', box); this.dynEl.style.display = 'none';
  if (spec.toy && cap) { var b = cap.querySelector('b'); H('span', 'toy', b || cap, 'illustrative toy').title = 'A toy model that isolates the mechanism. Not an experiment from the repository.'; }
  this.inputs = {};
  this.buildControls();
  this.bindPointer();
  this.draw();
  var timer = 0; window.addEventListener('resize', function () { clearTimeout(timer); timer = setTimeout(function () {
    if ((w.stage.clientWidth < 560) !== w.narrow) w.draw(); }, 120); });
}
Widget.prototype.arrowMarker = function (c) {
  var id = this.id + '-arr-' + c.replace(/[^a-z0-9]/gi, '');
  if (!this.defs.querySelector('#' + id)) S('path', {d: 'M0 0L8 4L0 8z', fill: c},
    S('marker', {id: id, viewBox: '0 0 8 8', refX: 7, refY: 4, markerWidth: 7, markerHeight: 7, orient: 'auto-start-reverse'}, this.defs));
  return id;
};
Widget.prototype.fmt = function (k) { var P = this.params[k], v = this.state[k];
  if (P.fmt) return P.fmt(v);
  if (typeof v !== 'number') return String(v);
  var st = P.step || 1, d = clamp(-Math.floor(Math.log10(st) + 1e-9), 0, 6);
  return v.toFixed(d) + (P.unit ? ' ' + P.unit : ''); };
Widget.prototype.buildControls = function () {
  var w = this, any = false;
  Object.keys(this.params).forEach(function (k) {
    var P = w.params[k], type = P.type || (P.options ? 'select' : typeof P.value === 'boolean' ? 'toggle' : 'range');
    P.type = type; if (type === 'hidden') return; any = true;
    var row = H('label', 'ctrl ' + type, w.ctrlEl), inp, val;
    if (type === 'toggle') {
      inp = H('input', '', row); inp.type = 'checkbox'; inp.checked = !!w.state[k]; enrich(H('span', '', row, P.label || k));
      inp.addEventListener('change', function () { w.set(k, inp.checked); });
    } else if (type === 'select') {
      enrich(H('span', '', row, P.label || k)); H('span', '', row, '');
      inp = H('select', '', row);
      P.options.forEach(function (op) { var e = H('option', '', inp, plain(op.label || op)); e.value = op.value != null ? op.value : op; });
      inp.value = w.state[k];
      inp.addEventListener('change', function () { w.set(k, inp.value); });
    } else {
      var lab = H('span', '', row); lab.textContent = P.label || k; enrich(lab);
      if (type === 'time') { var play = H('button', 'btn', null, '▶'); play.type = 'button'; play.setAttribute('aria-label', 'Play'); row.insertBefore(play, lab);
        play.addEventListener('click', function (ev) { ev.preventDefault(); w.togglePlay(k, play); }); P._play = play; }
      val = H('span', 'val', row, '');
      inp = H('input', '', row); inp.type = 'range'; inp.min = P.min; inp.max = P.max; inp.step = P.step || 'any'; inp.value = w.state[k];
      inp.addEventListener('input', function () { w.set(k, +inp.value); });
      P._val = val;
    }
    inp.setAttribute('data-param', k);
    w.inputs[k] = inp;
  });
  var presets = this.spec.presets || {}, acts = this.spec.actions || {};
  Object.keys(presets).forEach(function (name) {
    var b = H('button', 'btn', w.actEl, plain(name)); b.type = 'button'; b.setAttribute('data-preset', name);
    b.addEventListener('click', function () { Object.keys(presets[name]).forEach(function (k) { w.state[k] = presets[name][k]; }); w.sync(); w.draw(); }); });
  Object.keys(acts).forEach(function (name) {
    var a = acts[name], b = H('button', 'btn', w.actEl, typeof a === 'string' ? a : a.label || name); b.type = 'button'; b.setAttribute('data-action', name);
    b.addEventListener('click', function () { if (name === 'resample' && typeof a === 'string') w.state.seed++; else if (a.run) a.run(w.state, w); w.sync(); w.draw(); }); });
  if (any) { var r = H('button', 'btn ghost', this.actEl, 'Reset'); r.type = 'button'; r.setAttribute('data-action', 'reset');
    r.addEventListener('click', function () { Object.keys(w.defaults).forEach(function (k) { w.state[k] = w.defaults[k]; }); w.state.seed = w.spec.seed || 1; w.sync(); w.draw(); }); }
  if (!this.ctrlEl.children.length) this.ctrlEl.style.display = 'none';
  if (!this.actEl.children.length) this.actEl.style.display = 'none';
};
Widget.prototype.sync = function () { var w = this;
  Object.keys(this.inputs).forEach(function (k) { var i = w.inputs[k]; if (i.type === 'checkbox') i.checked = !!w.state[k]; else i.value = w.state[k]; }); };
Widget.prototype.set = function (k, v) {
  var P = this.params[k];
  if (P && typeof v === 'number' && P.min != null) { v = clamp(v, P.min, P.max); if (P.step) v = +(Math.round((v - P.min) / P.step) * P.step + P.min).toFixed(10); }
  if (this.state[k] === v) return;
  this.state[k] = v; var w = this;
  if (this.inputs[k] && this.inputs[k].type === 'range' && +this.inputs[k].value !== v) this.inputs[k].value = v;
  if (!this._raf) this._raf = requestAnimationFrame(function () { w._raf = 0; w.draw(); });
};
Widget.prototype.togglePlay = function (k, btn) {
  var w = this, P = this.params[k];
  if (this._timer) { clearInterval(this._timer); this._timer = 0; btn.textContent = '▶'; return; }
  if (this.state[k] >= P.max) this.set(k, P.min);
  btn.textContent = '❚❚';
  this._timer = setInterval(function () {
    var nv = w.state[k] + (P.step || 1);
    if (nv > P.max) { if (P.loop) nv = P.min; else { clearInterval(w._timer); w._timer = 0; btn.textContent = '▶'; return; } }
    w.set(k, nv);
  }, 1000 / (P.fps || 20));
};
Widget.prototype.draw = function () {
  var w = this, k;
  while (this.content.firstChild) this.content.removeChild(this.content.firstChild);
  while (this.hover.firstChild) this.hover.removeChild(this.hover.firstChild);
  this.tip.style.display = 'none';
  this.plots = []; this.legend = []; this.handles = []; this.readouts = []; this.dyn = null;
  this.narrow = !this.spec.fixed && this.stage.clientWidth > 0 && this.stage.clientWidth < 560;
  this.W = this.narrow ? 440 : this.W0; this.H = this.H0; this.usedH = 0;
  var ctx = {W: this.W, H: this.H, narrow: this.narrow, svg: this.content, state: this.state,
    plot: function (o) { return new Plot(w, o); },
    el: function (tag, attrs, text, parent) { return S(tag, attrs, parent || w.content, text); },
    rng: function (stream) { return rng(w.state.seed * 7919 + (stream == null ? 0 : hash(stream))); },
    readout: function (label, value, o) { w.readouts.push({label: label, value: value, accent: o && o.accent}); },
    note: function (html) { w.dyn = html; },
    legend: function (label, c, shape) { w.legend.push({label: label, color: color(c), shape: shape || 'line'}); },
    arrow: function (c) { return w.arrowMarker(color(c || 'ink2')); },
    color: color, fmt: fmtAuto};
  try { this.spec.draw(Object.assign({}, this.state), ctx); this.failed = false; }
  catch (e) {
    this.failed = true; console.error('D3X widget "' + this.id + '" draw failed: ' + (e && e.stack || e));
    S('text', {x: 16, y: 28, 'font-size': 13, fill: '#B4572A'}, this.content, 'Widget error: ' + (e && e.message || e));
  }
  for (k in this.params) if (this.params[k]._val) this.params[k]._val.textContent = this.fmt(k);
  // legend (dedupe by label); a single unlabeled series needs none
  this.legendEl.textContent = ''; var seen = {};
  this.legend.forEach(function (L) { if (seen[L.label]) return; seen[L.label] = 1;
    var s = H('span', '', w.legendEl), i = H('i', L.shape === 'box' ? '' : L.shape, s); i.style.color = L.color;
    var t = H('span', '', s, L.label); enrich(t); });
  this.legendEl.style.display = this.legendEl.children.length ? '' : 'none';
  this.roEl.textContent = '';
  this.readouts.forEach(function (R) { var d = H('div', 'ro' + (R.accent ? ' accent' : ''), w.roEl); H('div', 'v', d, R.value); var l = H('div', 'l', d, R.label); enrich(l); });
  this.roEl.style.display = this.readouts.length ? '' : 'none';
  if (this.dyn != null) { this.dynEl.innerHTML = this.dyn; enrich(this.dynEl); this.dynEl.style.display = ''; } else this.dynEl.style.display = 'none';
  this.H = Math.max(this.H0, this.usedH || 0);
  this.svg.setAttribute('viewBox', '0 0 ' + this.W + ' ' + this.H);
  this.svg.style.touchAction = this.handles.length ? 'none' : '';
};
Widget.prototype.toView = function (ev) {
  var pt = this.svg.createSVGPoint(); pt.x = ev.clientX; pt.y = ev.clientY;
  var m = this.svg.getScreenCTM(); return m ? pt.matrixTransform(m.inverse()) : pt; };
Widget.prototype.bindPointer = function () {
  var w = this, drag = null;
  this.svg.addEventListener('pointerdown', function (ev) {
    var p = w.toView(ev), best = null, bd = 26;
    w.handles.forEach(function (h) { var d = Math.hypot(h.px - p.x, h.py - p.y); if (d < bd) { bd = d; best = h; } });
    if (!best) return;
    // plots are rebuilt on every draw, so remember the plot by index, not by object
    drag = {setX: best.setX, setY: best.setY, index: Math.max(0, w.plots.indexOf(best.plot))};
    try { w.svg.setPointerCapture(ev.pointerId); } catch (e) {} w.stage.classList.add('dragging'); ev.preventDefault();
  });
  this.svg.addEventListener('pointermove', function (ev) {
    var p = w.toView(ev);
    if (drag) { var pl = w.plots[drag.index]; if (!pl) return;
      if (drag.setX) w.set(drag.setX, pl.ix(p.x)); if (drag.setY) w.set(drag.setY, pl.iy(p.y)); return; }
    w.showHover(p);
  });
  function end(ev) { if (drag) { drag = null; w.stage.classList.remove('dragging'); try { w.svg.releasePointerCapture(ev.pointerId); } catch (e) {} } }
  this.svg.addEventListener('pointerup', end); this.svg.addEventListener('pointercancel', end);
  this.svg.addEventListener('pointerleave', function () { if (!drag) { while (w.hover.firstChild) w.hover.removeChild(w.hover.firstChild); w.tip.style.display = 'none'; } });
};
function interp(xs, ys, x) {
  var n = xs.length, lo = 0, hi = n - 1, mid;
  if (n < 2 || x < xs[0] || x > xs[n - 1]) return null;
  while (hi - lo > 1) { mid = (lo + hi) >> 1; if (xs[mid] <= x) lo = mid; else hi = mid; }
  var t = (x - xs[lo]) / ((xs[hi] - xs[lo]) || 1), y = ys[lo] + t * (ys[hi] - ys[lo]);
  return isFinite(y) ? y : null;
}
Widget.prototype.showHover = function (p) {
  var w = this, pl = null;
  while (this.hover.firstChild) this.hover.removeChild(this.hover.firstChild);
  this.plots.forEach(function (q) { if (p.x >= q.box.x0 && p.x <= q.box.x1 && p.y >= q.box.y1 && p.y <= q.box.y0 && q.series.length) pl = q; });
  if (!pl) { this.tip.style.display = 'none'; return; }
  var x = pl.ix(p.x), rows = [];
  pl.series.forEach(function (s) {
    if (s.nearest) { var bi = -1, bd = 14, i, d; for (i = 0; i < s.xs.length; i++) { d = Math.abs(pl.sx(s.xs[i]) - p.x); if (d < bd && isFinite(s.ys[i])) { bd = d; bi = i; } }
      if (bi >= 0) rows.push({s: s, y: s.ys[bi], px: pl.sx(s.xs[bi])}); return; }
    var y = interp(s.xs, s.ys, x); if (y != null) rows.push({s: s, y: y}); });
  if (!rows.length) { this.tip.style.display = 'none'; return; }
  S('line', {x1: p.x, x2: p.x, y1: pl.box.y0, y2: pl.box.y1, stroke: THEME.ink3, 'stroke-width': 1}, this.hover);
  rows.forEach(function (r) { S('circle', {cx: r.px != null ? r.px : p.x, cy: pl.sy(r.y), r: 4.5, fill: r.s.color, stroke: THEME.card, 'stroke-width': 2}, w.hover); });
  this.tip.textContent = '';
  H('div', 'x', this.tip, (pl.X.label ? plain(pl.X.label) + ' ' : 'x ') + (pl.xfmt ? fmtAuto(x) : x));
  rows.forEach(function (r) { var d = H('div', 'r', w.tip), i = H('i', '', d); i.style.color = r.s.color; if (r.s.nearest) i.style.cssText += ';width:7px;height:7px;border:0;border-radius:50%;background:currentColor'; H('span', '', d, plain(r.s.label)); H('b', '', d, fmtAuto(r.y)); });
  var sw = this.stage.clientWidth, k = sw / this.W, left = p.x * k + 14;
  this.tip.style.display = 'block';
  if (left + this.tip.offsetWidth > sw - 4) left = p.x * k - 14 - this.tip.offsetWidth;
  this.tip.style.left = Math.max(2, left) + 'px'; this.tip.style.top = Math.max(2, pl.box.y1 * k + 4) + 'px';
};

/* ------------------------------------------------------------------ flow diagram */
var KIND = {data: ['lightblue!55', 'navy!45', 'ink'], code: ['card', 'navy', 'ink'], model: ['navy', 'navy', 'white'],
  result: ['orange!20', 'orange', 'ink'], external: ['card', 'gray', 'ink2']};
function Flow(id, spec) {
  var fig = document.getElementById(id);
  if (!fig) { console.error('D3X.flow: no element with id "' + id + '"'); return; }
  var cols = spec.cols || 1 + Math.max.apply(null, spec.nodes.map(function (n) { return n.col || 0; }));
  var rows = spec.rows || 1 + Math.max.apply(null, spec.nodes.map(function (n) { return n.row || 0; }));
  var W = fig.classList.contains('wide') ? 960 : 720, cw = W / cols, nw = Math.min(190, cw - 34), nh = 56, ch = spec.rowHeight || 96, Hh = rows * ch + 20, lanes = {};
  var box = H('div', 'figbox'), cap = fig.querySelector('figcaption'); fig.insertBefore(box, cap);
  var stage = H('div', 'stage flow', box), svg = S('svg', {viewBox: '0 0 ' + W + ' ' + Hh, role: 'img', 'aria-label': cap ? cap.textContent.trim().slice(0, 140) : id}, stage);
  svg.style.minWidth = Math.round(W * 0.89) + 'px';       // on a phone the diagram scrolls sideways instead of shrinking; wide diagrams need proportionally more
  var defs = S('defs', {}, svg), mk = id + '-arrow';
  S('path', {d: 'M0 0L8 4L0 8z', fill: THEME.ink3}, S('marker', {id: mk, viewBox: '0 0 8 8', refX: 7.5, refY: 4, markerWidth: 7, markerHeight: 7, orient: 'auto'}, defs));
  // edges that travel in the gap below a row get their own lane, so that they do not draw over each other
  function lane(g) { var i = lanes[g] = (lanes[g] || 0) + 1; i -= 1; return (i % 2 ? 1 : -1) * Math.ceil(i / 2) * 9; }
  var gE = S('g', {}, svg), gN = S('g', {}, svg), byId = {}, detail = H('div', 'flowdetail', box), active = null;
  spec.nodes.forEach(function (n) { n.cx = (n.col || 0) * cw + cw / 2; n.cy = (n.row || 0) * ch + ch / 2 + 4; byId[n.id] = n; });
  (spec.edges || []).forEach(function (e) {
    if (Array.isArray(e)) e = {from: e[0], to: e[1], label: e[2]};
    var a = byId[e.from], b = byId[e.to], d, lx, ly, anchor = 'middle';
    if (!a || !b) { console.error('D3X.flow "' + id + '": edge references unknown node ' + e.from + ' -> ' + e.to); return; }
    var dc = (b.col || 0) - (a.col || 0), dr = (b.row || 0) - (a.row || 0), sgn, my;
    if (dc === 0) { sgn = dr > 0 ? 1 : -1; d = 'M' + a.cx + ' ' + (a.cy + sgn * nh / 2) + 'V' + (b.cy - sgn * nh / 2); lx = a.cx + 6; ly = (a.cy + b.cy) / 2 + 4; anchor = 'start'; }
    else if (dr === 0 && Math.abs(dc) === 1) { sgn = dc > 0 ? 1 : -1; d = 'M' + (a.cx + sgn * nw / 2) + ' ' + a.cy + 'H' + (b.cx - sgn * nw / 2); lx = (a.cx + b.cx) / 2; ly = a.cy - 7; }
    else if (dr === 0) { my = a.cy + ch / 2 - 4 + lane(a.row || 0); sgn = dc > 0 ? 1 : -1;        // same row, not neighbours: duck under the boxes in between
      d = 'M' + (a.cx + sgn * nw / 4) + ' ' + (a.cy + nh / 2) + 'V' + my + 'H' + (b.cx - sgn * nw / 4) + 'V' + (b.cy + nh / 2);
      lx = a.cx + sgn * (nw / 4 + 8); ly = my - 4; anchor = sgn > 0 ? 'start' : 'end'; }
    else if (Math.abs(dc) === 1 && dc > 0) { var xa = a.cx + nw / 2, xb = b.cx - nw / 2, mx = (xa + xb) / 2;       // next column, other row: bend in the column gap
      d = 'M' + xa + ' ' + a.cy + 'H' + mx + 'V' + b.cy + 'H' + xb; lx = mx + 5; ly = (a.cy + b.cy) / 2 + 4; anchor = 'start'; }
    else { sgn = dr > 0 ? 1 : -1; my = a.cy + sgn * ch / 2 - 4 * sgn + lane(Math.min(a.row || 0, b.row || 0) + (Math.abs(dr) > 1 && sgn < 0 ? Math.abs(dr) - 1 : 0));
      var hs = b.cx > a.cx ? 1 : -1;                                       // anything else (wrap-around, backwards): travel in the gap between the rows
      d = 'M' + a.cx + ' ' + (a.cy + sgn * nh / 2) + 'V' + my + 'H' + b.cx + 'V' + (b.cy - sgn * nh / 2); lx = a.cx + hs * 8; ly = my - 4; anchor = hs > 0 ? 'start' : 'end'; }
    S('path', {d: d, fill: 'none', stroke: THEME.ink3, 'stroke-width': 1.4, 'stroke-dasharray': e.dash ? '5 4' : null, 'marker-end': 'url(#' + mk + ')', 'data-from': e.from, 'data-to': e.to}, gE);
    if (e.label) S('text', {x: lx, y: ly, 'text-anchor': anchor, 'font-size': 11, fill: THEME.ink2, 'paint-order': 'stroke', stroke: THEME.card, 'stroke-width': 4}, gE, e.label);
  });
  function wrap(str, max) { if (str.length <= max) return [str]; var cut = str.lastIndexOf(' ', max); if (cut < 4) cut = max; return [str.slice(0, cut), str.slice(cut).trim()]; }
  function select(n, g) {
    if (active) active.querySelector('rect').setAttribute('stroke-width', 1.4);
    if (active === g) { active = null; detail.textContent = ''; H('span', 'hint', detail, 'Select a box to see what it does and where it lives.'); return; }   // second click closes
    active = g; g.querySelector('rect').setAttribute('stroke-width', 3); g.querySelector('rect').setAttribute('stroke', color('orange'));
    detail.textContent = ''; H('div', 't', detail, n.label + (n.sub ? ' · ' + n.sub : ''));
    var b = H('div', '', detail); b.innerHTML = n.detail || ''; enrich(detail);
  }
  spec.nodes.forEach(function (n) {
    var k = KIND[n.kind || 'code'] || KIND.code, g = S('g', {tabindex: 0, role: 'button', 'data-node': n.id, style: n.detail ? 'cursor:pointer' : ''}, gN);
    S('rect', {x: n.cx - nw / 2, y: n.cy - nh / 2, width: nw, height: nh, rx: 8, fill: color(k[0]), stroke: color(k[1]), 'stroke-width': 1.4,
      'stroke-dasharray': n.kind === 'external' ? '5 4' : null}, g);
    var lines = wrap(n.label, Math.floor(nw / 7.6)), hasSub = !!n.sub, y = n.cy - (lines.length - 1) * 7.5 - (hasSub ? 6 : 0) + 4.5;
    lines.forEach(function (ln, i) { S('text', {x: n.cx, y: y + i * 15, 'text-anchor': 'middle', 'font-size': 11.5, 'font-weight': 600, fill: color(k[2])}, g, ln); });
    if (hasSub) S('text', {x: n.cx, y: y + lines.length * 15 + 1, 'text-anchor': 'middle', 'font-size': 9.5, fill: n.kind === 'model' ? '#C8DCF0' : THEME.ink3,
      'font-family': 'ui-monospace,Menlo,monospace'}, g, n.sub);
    if (n.detail) { g.addEventListener('click', function () { select(n, g); });
      g.addEventListener('keydown', function (ev) { if (ev.key === 'Enter' || ev.key === ' ') { ev.preventDefault(); select(n, g); } }); }
  });
  (spec.rowLabels || []).forEach(function (txt, r) { if (txt) S('text', {x: 6, y: r * ch + 13, 'font-size': 10.5, 'font-weight': 600, fill: THEME.ink3, 'letter-spacing': '.06em'}, gE, String(txt).toUpperCase()); });
  var KIND_NAME = {data: 'data', code: 'code', model: 'the project\'s contribution', result: 'result', external: 'external'}, used = [], key = H('div', 'legend', null);
  spec.nodes.forEach(function (n) { var k = n.kind || 'code'; if (used.indexOf(k) < 0) used.push(k); });
  if (used.length > 1) { used.forEach(function (k) { var sp = H('span', '', key), i = H('i', 'box', sp), c = KIND[k] || KIND.code;
      i.style.cssText = 'background:' + color(c[0]) + ';border:1.4px ' + (k === 'external' ? 'dashed ' : 'solid ') + color(c[1]) + ';height:11px;width:16px'; H('span', '', sp, KIND_NAME[k] || k); });
    box.insertBefore(key, detail); }
  var first = spec.nodes.filter(function (n) { return n.detail; })[0];
  if (first) H('span', 'hint', detail, 'Select a box to see what it does and where it lives.'); else detail.style.display = 'none';
  if (spec.select && byId[spec.select] && byId[spec.select].detail) select(byId[spec.select], gN.querySelector('[data-node="' + spec.select + '"]'));
  function reset() { if (active) select(null, active); if (spec.select && byId[spec.select] && byId[spec.select].detail) select(byId[spec.select], gN.querySelector('[data-node="' + spec.select + '"]')); }
  widgets.push({id: id, kind: 'flow', nodes: spec.nodes.length, reset: reset});
}

/* ------------------------------------------------------------------ page chrome */
function derivations() {
  [].forEach.call(document.querySelectorAll('.derivation'), function (D) {
    var steps = [].filter.call(D.children, function (c) { return c.classList.contains('dstep'); }), open = D.getAttribute('data-mode') === 'open', shown = open ? steps.length : 1;
    var head = H('div', 'dhead'), t = H('div', 't', head, D.getAttribute('data-title') || 'Derivation'), c = H('div', 'c', head);
    var count = H('span', '', c), next = H('button', 'btn primary', c, 'Next step'), all = H('button', 'btn', c, 'Show all');
    next.type = all.type = 'button'; next.setAttribute('data-next', ''); all.setAttribute('data-all', '');
    D.insertBefore(head, D.firstChild);
    steps.forEach(function (s, i) {
      var body = H('div', 'body'); while (s.firstChild) body.appendChild(s.firstChild);
      H('div', 'n', s, String(i + 1));
      var why = H('div', 'why', s); why.innerHTML = s.getAttribute('data-why') || '';
      s.appendChild(body);
    });
    function paint(fresh) {
      steps.forEach(function (s, i) { s.classList.toggle('hidden', i >= shown); s.classList.toggle('fresh', fresh === i); });
      count.textContent = shown < steps.length ? 'Step ' + shown + ' of ' + steps.length : steps.length + ' steps';
      next.style.display = shown < steps.length ? '' : 'none';
      all.textContent = shown < steps.length ? 'Show all' : 'Restart';
      all.style.display = open ? 'none' : '';
    }
    next.addEventListener('click', function () { shown = Math.min(steps.length, shown + 1); paint(shown - 1); });
    all.addEventListener('click', function () { shown = shown < steps.length ? steps.length : 1; paint(); });
    paint();
  });
}
var KW = {py: 'def class return if elif else for while in not and or import from as with try except finally raise lambda yield pass break continue None True False self assert global nonlocal async await is del',
  js: 'function return if else for while const let var new class extends import export from default try catch finally throw async await of in typeof null undefined true false this switch case break continue',
  jl: 'function end return if elseif else for while in struct mutable module using import export begin let do try catch finally const true false nothing macro where abstract type',
  r: 'function return if else for while in repeat break next TRUE FALSE NULL NA library require'};
function highlight() {
  [].forEach.call(document.querySelectorAll('pre.code code'), function (code) {
    var lang = (code.getAttribute('data-lang') || 'py').toLowerCase(), start = +(code.getAttribute('data-start') || 1);
    lang = {python: 'py', javascript: 'js', ts: 'js', typescript: 'js', julia: 'jl'}[lang] || lang;
    var kw = {}; (KW[lang] || KW.py).split(' ').forEach(function (k) { kw[k] = 1; });
    var cmt = /^(js|c|cpp|java|rs|go)$/.test(lang) ? '\\/\\/.*$' : '#.*$';
    var re = new RegExp('(' + cmt + ')|("(?:[^"\\\\]|\\\\.)*"|\'(?:[^\'\\\\]|\\\\.)*\')|(\\b\\d+(?:\\.\\d+)?(?:e[+-]?\\d+)?\\b)|(\\b[A-Za-z_]\\w*\\b)', 'g');
    var lines = code.textContent.replace(/\n$/, '').split('\n'); code.textContent = '';
    lines.forEach(function (ln, i) {
      H('span', 'ln', code, String(start + i));
      var last = 0, m; re.lastIndex = 0;
      while ((m = re.exec(ln))) {
        var cls = m[1] ? 'c' : m[2] ? 's' : m[3] ? 'd' : kw[m[4]] ? 'k' : null;
        if (!cls) continue;
        if (m.index > last) code.appendChild(document.createTextNode(ln.slice(last, m.index)));
        H('span', cls, code, m[0]); last = m.index + m[0].length;
      }
      code.appendChild(document.createTextNode(ln.slice(last) + '\n'));
    });
  });
}
function chrome() {
  var bar = document.getElementById('bar');
  function progress() { var h = document.documentElement.scrollHeight - window.innerHeight; if (bar) bar.style.width = (h > 0 ? window.scrollY / h * 100 : 0) + '%'; }
  window.addEventListener('scroll', progress, {passive: true}); window.addEventListener('resize', progress); progress();
  // the assembling panel: the last section whose top has passed 45 % of the window sets the level; data-hud="k" lights lines 1..k
  var hud = document.getElementById('hud');
  if (hud) {
    var lines = [].slice.call(hud.querySelectorAll('.line')), secs = [].slice.call(document.querySelectorAll('main > section[data-hud]'));
    var level = function () { var k = 0, y = window.innerHeight * 0.45; secs.forEach(function (x) { if (x.getBoundingClientRect().top < y) k = +x.getAttribute('data-hud'); });
      lines.forEach(function (l) { l.classList.toggle('on', +l.getAttribute('data-hud') <= k); }); };
    window.addEventListener('scroll', level, {passive: true}); window.addEventListener('resize', level); level();
  }
  var src = document.querySelector('[data-notation]') || document.getElementById('notation'), drawer = document.getElementById('drawer'), btn = document.getElementById('notation-btn');
  if (src && drawer) {
    drawer.querySelector('.db').appendChild(src.cloneNode(true)).removeAttribute('id');
    var toggle = function (on) { drawer.classList.toggle('open', on); };
    if (btn) btn.addEventListener('click', function () { toggle(); });
    drawer.querySelector('.dh button').addEventListener('click', function () { toggle(false); });
    document.addEventListener('keydown', function (e) {
      if (/^(INPUT|SELECT|TEXTAREA)$/.test(e.target.nodeName) && e.target.type !== 'range') return;
      if (e.key === 'n' && !e.metaKey && !e.ctrlKey && !e.altKey) toggle(); if (e.key === 'Escape') toggle(false); });
  } else if (btn) btn.style.display = 'none';
}
function boot() {
  if (booted) return; booted = true;
  derivations();
  enrich(document.body);
  highlight();
  chrome();
  queue.forEach(function (q) { q(); }); queue = [];
  window.D3X_READY = true;
}
function later(fn) { if (booted) fn(); else queue.push(fn); }

window.D3X = {
  widget: function (id, spec) { later(function () { var w = new Widget(id, spec); if (w.fig) widgets.push(w); }); },
  flow: function (id, spec) { later(function () { Flow(id, spec); }); },
  widgets: widgets, color: color, rng: rng, enrich: enrich, plain: plain, fmt: fmtAuto, ticks: ticks, THEME: THEME, SERIES: SERIES,
  /** small numeric helpers that explainers need again and again */
  linspace: function (a, b, n) { var out = [], i; for (i = 0; i < n; i++) out.push(a + (b - a) * i / (n - 1)); return out; },
  mean: function (a) { return a.reduce(function (s, v) { return s + v; }, 0) / a.length; },
  quantile: function (a, q) { var s = a.slice().sort(function (x, y) { return x - y; }), p = (s.length - 1) * q, i = Math.floor(p); return s[i] + (s[Math.min(i + 1, s.length - 1)] - s[i]) * (p - i); },
  normPdf: function (x, mu, sd) { mu = mu || 0; sd = sd == null ? 1 : sd; var z = (x - mu) / sd; return Math.exp(-0.5 * z * z) / (sd * Math.sqrt(2 * Math.PI)); },
  normCdf: function (x, mu, sd) { mu = mu || 0; sd = sd == null ? 1 : sd; var z = (x - mu) / (sd * Math.SQRT2), t = 1 / (1 + 0.3275911 * Math.abs(z));
    var e = 1 - (((((1.061405429 * t - 1.453152027) * t) + 1.421413741) * t - 0.284496736) * t + 0.254829592) * t * Math.exp(-z * z); return 0.5 * (1 + (z < 0 ? -e : e)); },
  data: function (id) { var e = document.getElementById(id); if (!e) { console.error('D3X.data: no <script type="application/json" id="' + id + '">'); return null; } return JSON.parse(e.textContent); }
};
if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', boot); else boot();
})();
