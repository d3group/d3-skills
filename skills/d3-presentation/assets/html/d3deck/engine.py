# -*- coding: utf-8 -*-
"""Step engine and shell.

CSS: design tokens, the fixed 1280x720 canvas, ghosting (never display:none),
scrims, step dots, the dark shell around the slide, present mode, shot mode
(for headless screenshots) and print. JS: slide and step state, keys, hash deep
links, present mode, viewport fit. Ported from d3group/DisputationNicoElbert
(flow/engine.py) and recolored with the D3 tokens.
"""

CSS = r"""
*{box-sizing:border-box;margin:0;padding:0}
html,body{height:100%;background:#0B0D10;overflow:hidden;-webkit-font-smoothing:antialiased;
 font-family:'Inter',system-ui,sans-serif}
:root{
 --navy:#153F87;--orange:#F29100;--gray:#808080;--lightblue:#C8DCF0;--darkblue:#0A2864;
 --teal:#4D9AAA;--yellow:#D8DE6F;--peach:#F5C8AA;--lavender:#C5CAE9;
 --bar:#004389;--navy-5:#F3F5F9;--navy-15:#DCE2ED;--navy-50:#8A9FC3;--navy-90:#2C5293;--orange-5:#FEFAF2;
 --line:#E4E8ED;
 --fs-LARGE:49px;--fs-Large:41px;--fs-large:34px;--fs-normal:31px;--fs-small:28px;
 --fs-footnote:25px;--fs-script:23px;--fs-tiny:17px;--fs-chrome:13px;--fs-display:150px;
 --mono:ui-monospace,'SF Mono',Menlo,Consolas,monospace;
}
#stage{position:fixed;left:0;right:0;top:54px;bottom:34px}
.sl{position:absolute;left:50%;top:50%;width:1280px;height:720px;overflow:hidden;display:none;
 transform-origin:center center;box-shadow:0 34px 100px rgba(0,0,0,.6);background:#fff;color:var(--navy);
 font-size:var(--fs-small);line-height:1.35}
.sl.on{display:block}
@media (prefers-reduced-motion:reduce){.sl *{animation:none!important;transition:none!important}}

/* ══ ghosting: the build device. Never display:none, never reflow. ══ */
[data-s]{transition:opacity .42s cubic-bezier(.4,0,.2,1),filter .42s,color .42s,background .42s,
 border-color .42s,transform .42s}
.gh{opacity:0}                                   /* later steps are invisible and keep their place */
body.reveal-ghost .gh{opacity:.15;filter:grayscale(1)}   /* opt-in: meta(reveal='ghost') */
.gh-soft{opacity:.42;filter:grayscale(.8)}
.sl.is-current [data-hide].gh{opacity:0;filter:none}   /* data-hide: no ghost on stage, for reveals the ghost would give away */
.scrim{position:absolute;background:rgba(255,255,255,.6997);pointer-events:none;z-index:4;
 transition:opacity .4s cubic-bezier(.4,0,.2,1)}
.scrim.off{opacity:0}
.stepdots{position:absolute;right:80px;top:140px;display:flex;gap:5px;z-index:8}
.stepdots i{width:18px;height:3px;background:var(--line);display:block;transition:background .3s}
.stepdots i.on{background:var(--orange)}

/* ══ body text defaults, Beamer-like ══ */
b,strong{font-weight:700}
p{margin:0 0 .5em}
ul{list-style:none}
ul>li{position:relative;padding-left:.9em;margin:.15em 0}
ul>li::before{content:'';position:absolute;left:0;top:.48em;width:.4em;height:.4em;background:var(--navy)}
ol{padding-left:1.2em}
ol>li{margin:.15em 0}
table{border-collapse:collapse}
td,th{padding:.2em .6em;text-align:left;vertical-align:top}
th{border-bottom:2px solid var(--navy)}

/* ══ shell ══ */
#bar{position:fixed;left:0;top:0;height:3px;background:var(--orange);z-index:70;transition:width .2s}
#top{position:fixed;left:0;right:0;top:0;height:54px;background:#0B0D10;border-bottom:1px solid rgba(255,255,255,.08);
 display:flex;align-items:center;gap:8px;padding:0 132px 0 14px;z-index:60;overflow-x:auto;scrollbar-width:none}
#top::-webkit-scrollbar{display:none}
#top .lb{font-size:9.5px;letter-spacing:.2em;text-transform:uppercase;color:#565E68;flex:none;margin-right:4px}
.jt{padding:5px 10px;border-radius:7px;border:1px solid rgba(255,255,255,.11);background:rgba(255,255,255,.03);
 color:#C3C8CE;font-size:11px;cursor:pointer;white-space:nowrap;flex:none;transition:.14s;font-family:inherit}
.jt:hover{background:rgba(255,255,255,.1)}
.jt.on{background:#fff;color:#0B0D10;border-color:#fff;font-weight:600}
#foot{position:fixed;left:0;right:0;bottom:0;height:34px;display:flex;align-items:center;justify-content:space-between;
 padding:0 16px;color:#565E68;font-size:11px;z-index:60;background:#0B0D10}
#foot b{color:#E6E8EB;font-weight:600}
#foot .d{color:#6E7681}
#foot .stp{color:var(--orange);font-weight:600}
kbd{background:#171A1F;border:1px solid #262B32;border-radius:4px;padding:1px 6px;font-family:monospace;color:#8A929B;font-size:10px}
#play{position:fixed;right:12px;top:9px;z-index:65;display:flex;align-items:center;gap:8px;padding:6px 13px;border-radius:8px;
 border:1px solid rgba(242,145,0,.55);background:rgba(242,145,0,.14);color:#F7B24D;font-size:11px;font-weight:600;
 letter-spacing:.02em;cursor:pointer;white-space:nowrap;transition:.14s;font-family:'Inter',system-ui,sans-serif}
#play::before{content:'';position:fixed;right:0;top:0;width:156px;height:54px;
 background:linear-gradient(90deg,rgba(11,13,16,0) 0,#0B0D10 32px);z-index:-1;pointer-events:none}
#play:hover{background:var(--orange);border-color:var(--orange);color:#0B0D10}
#pexit{position:fixed;right:14px;bottom:12px;z-index:80;display:none;font-family:monospace;font-size:10px;letter-spacing:.08em;
 color:#7C848E;background:rgba(11,13,16,.7);border:1px solid rgba(255,255,255,.1);border-radius:6px;padding:5px 10px;
 transition:opacity .6s;pointer-events:none}

/* ══ present mode ══ */
body.pres #play,body.pres #top,body.pres #foot,body.pres #bar{display:none!important}
body.pres #stage{top:0;bottom:0}
body.pres .sl{box-shadow:none}
body.pres.nocur,body.pres.nocur *{cursor:none!important}
body.pres #pexit{display:block}
body.pres.nocur #pexit{opacity:0}

/* ══ shot mode: ?shot in the URL, for headless screenshots ══ */
body.shot #top,body.shot #foot,body.shot #bar,body.shot #play,body.shot #pexit{display:none!important}
body.shot #stage{top:0;bottom:0}
body.shot .sl{box-shadow:none}

/* ══ operator surface: overview (O), help (?), jump toast, black/white screen (B/W), laser (L).
   Injected by the JS at boot; dark shell styling like the search palette; never printed. ══ */
.opov{position:fixed;inset:0;z-index:92;display:none;flex-direction:column;background:rgba(6,8,12,.97);
 font-family:'Inter',system-ui,sans-serif;color:#E6E8EB}
.opov.on{display:flex}
.opov header{flex:none;display:flex;align-items:baseline;gap:16px;padding:16px 24px 10px}
.opov header h2{font-size:15px;font-weight:600;letter-spacing:.01em}
.opov header span{font-size:11px;color:#6E7681}
#ovg{flex:1;overflow-y:auto;display:grid;grid-template-columns:repeat(auto-fill,minmax(240px,1fr));gap:18px 16px;
 padding:6px 24px 28px;align-content:start}
.ovt{display:flex;flex-direction:column;gap:6px;background:none;border:0;padding:0;cursor:pointer;text-align:left;
 font-family:inherit;color:#C3C8CE}
.ovf{position:relative;width:240px;height:135px;overflow:hidden;border-radius:4px;background:#fff;
 outline:2px solid transparent;outline-offset:2px;transition:outline-color .12s}
.ovf .sl{position:absolute!important;left:0!important;top:0!important;transform:scale(.1875)!important;
 transform-origin:0 0;box-shadow:none;pointer-events:none}
.ovt .ovl{font-size:11px;line-height:1.3;display:flex;gap:8px;max-width:240px}
.ovt .ovl b{font-family:var(--mono);font-size:10px;color:#8A929B;font-weight:600;flex:none}
.ovt .ovl span{overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.ovt.cur .ovf{outline-color:var(--orange)}
.ovt.sel .ovf,.ovt:hover .ovf{outline-color:#fff}
.ovt.cur .ovl b{color:var(--orange)}
#okeys{flex:1;overflow-y:auto;padding:6px 24px 28px;display:grid;grid-template-columns:repeat(auto-fill,minmax(330px,1fr));
 gap:6px 36px;align-content:start}
#okeys div{display:grid;grid-template-columns:150px 1fr;gap:12px;align-items:baseline;padding:6px 0;
 border-bottom:1px solid rgba(255,255,255,.07);font-size:13px}
#okeys kbd{margin-right:3px}
#otoast{position:fixed;left:50%;bottom:56px;transform:translateX(-50%);z-index:95;display:none;padding:8px 16px;
 border-radius:8px;background:rgba(11,13,16,.92);border:1px solid rgba(255,255,255,.12);color:#E6E8EB;
 font-family:var(--mono);font-size:14px;letter-spacing:.04em}
#otoast.on{display:block}
#ocover{position:fixed;inset:0;z-index:90;display:none}
body.cover-b #ocover{display:block;background:#000}
body.cover-w #ocover{display:block;background:#fff}
#olaser{position:fixed;left:0;top:0;z-index:91;width:14px;height:14px;margin:-7px 0 0 -7px;border-radius:50%;
 background:#F29100;box-shadow:0 0 0 3px rgba(242,145,0,.28),0 0 16px 4px rgba(242,145,0,.55);pointer-events:none;display:none}
body.laser #olaser{display:block}
body.laser,body.laser *{cursor:none!important}

/* ══ print: one slide per page, final state ══ */
@media print{
 html,body{overflow:visible;background:#fff}
 #top,#bar,#foot,#play,#pexit,.opov,#otoast,#ocover,#olaser{display:none!important}
 #stage{position:static}
 .sl{display:block!important;position:relative;left:0;top:0;transform:none!important;page-break-after:always;box-shadow:none}
 .gh,.gh-soft{opacity:1!important;filter:none!important}
 .sl *{animation:none!important;transition:none!important}   /* every page shows the end state */
 .scrim{display:none}
 @page{size:1280px 720px;margin:0}
}
"""

JS = r"""
const SL=[...document.querySelectorAll('.sl')], N=SL.length;
const META=__META__;
let cur=0, st=0, painted=-1;
function steps(i){return Math.max(1,parseInt(SL[i].dataset.steps||'1'))}
function pres(){return document.body.classList.contains('pres')}
function shot(){return document.body.classList.contains('shot')}
function fit(){
 if(shot()){SL.forEach(s=>s.style.transform='translate(-50%,-50%) scale(1)');return}
 const p=pres();
 const w=(p?innerWidth-16:innerWidth-56), h=(p?innerHeight-16:innerHeight-54-34-40);
 const k=Math.min(w/1280,h/720);
 SL.forEach(s=>s.style.transform='translate(-50%,-50%) scale('+k+')');}
function applyStep(s,step){
 s.querySelectorAll('[data-s]').forEach(n=>{
  const need=parseInt(n.dataset.s), soft=n.dataset.soft==='1';
  n.classList.toggle('gh',!soft&&step<need);
  n.classList.toggle('gh-soft',soft&&step<need);
  n.classList.toggle('is-shown',step>=need);});   /* motion keys on .is-shown: '.sl.is-current .is-shown ...' */
 s.querySelectorAll('.scrim').forEach(n=>n.classList.toggle('off',step>=parseInt(n.dataset.off)));
 s.querySelectorAll('[data-until]').forEach(n=>{if(step>parseInt(n.dataset.until)){n.classList.add('gh');n.classList.remove('is-shown')}});
 const dots=s.querySelector('.stepdots');
 if(dots)[...dots.children].forEach((d,i)=>d.classList.toggle('on',i<=step));
}
function paint(){
 const s=SL[cur]; s.dataset.step=st; applyStep(s,st);
 /* .is-current marks the slide on screen; clones (presenter next pane, overview) never carry it, so arrival
    animations keyed on it run only here and every preview shows the end state */
 SL.forEach(x=>{if(x!==s)x.classList.remove('is-current')}); s.classList.add('is-current');
 const m=META[cur];
 document.getElementById('bar').style.width=((cur+1)/N*100)+'%';
 document.getElementById('fl').innerHTML='<b>'+m.g+'</b>'+(m.s?' <span class="d">&middot;</span> '+m.s:'');
 document.getElementById('fr').innerHTML=m.f+(steps(cur)>1?
   ' <span class="stp">&middot; step '+(st+1)+'/'+steps(cur)+'</span>':'');
 let on=null; document.querySelectorAll('.jt').forEach(b=>{if(+b.dataset.go<=cur)on=b});
 document.querySelectorAll('.jt').forEach(b=>b.classList.toggle('on',b===on));
 location.hash=(cur+1)+(st?'.'+(st+1):'');
 const prev=painted; painted=cur;          /* prev !== cur: the slide changed (live modules leave/enter on it) */
 document.dispatchEvent(new CustomEvent('d3paint',{detail:{cur:cur,st:st,prev:prev}}));
}
function show(i,step){
 SL[cur].classList.remove('on'); cur=Math.max(0,Math.min(N-1,i));
 st=Math.max(0,Math.min(steps(cur)-1, step===undefined?0:(step<0?steps(cur)-1:step)));
 SL[cur].classList.add('on'); paint();
}
function fwd(){ if(st<steps(cur)-1){st++;paint()} else if(cur<N-1) show(cur+1,0) }
function back(){ if(st>0){st--;paint()} else if(cur>0) show(cur-1,-1) }
function go(i){show(i,0)}
addEventListener('keydown',e=>{
 if(e.target&&(e.target.tagName==='INPUT'||e.target.tagName==='TEXTAREA'))return;
 if(['ArrowRight','PageDown',' '].includes(e.key)){e.preventDefault();fwd()}
 else if(['ArrowLeft','PageUp'].includes(e.key)){e.preventDefault();back()}
 else if(e.key==='ArrowDown'){e.preventDefault();show(cur+1,0)}
 else if(e.key==='ArrowUp'){e.preventDefault();show(cur-1,0)}
 else if(e.key==='Home')show(0,0); else if(e.key==='End')show(N-1,0);
 else if(e.key==='p'||e.key==='P')print();
 else if(e.key==='f'||e.key==='F'){e.preventDefault();togglePres()}
 else if(e.key==='Escape'&&pres()){e.preventDefault();exitPres()}
});

/* ── present mode: fullscreen and shell hidden, decoupled so it works when fullscreen is refused ── */
function isFS(){return !!(document.fullscreenElement||document.webkitFullscreenElement)}
let curT;
function armCursor(){clearTimeout(curT); document.body.classList.remove('nocur');
 curT=setTimeout(()=>{if(pres())document.body.classList.add('nocur')},2800)}
function setPres(on){document.body.classList.toggle('pres',on); fit();
 if(on)armCursor(); else {clearTimeout(curT); document.body.classList.remove('nocur')}}
function enterPres(){const el=document.documentElement;
 const rq=el.requestFullscreen||el.webkitRequestFullscreen;
 if(rq){try{const r=rq.call(el); if(r&&r.catch)r.catch(()=>{})}catch(_){}}
 setPres(true)}
function exitPres(){const ex=document.exitFullscreen||document.webkitExitFullscreen;
 if(isFS()&&ex){try{const r=ex.call(document); if(r&&r.catch)r.catch(()=>{})}catch(_){}}
 setPres(false)}
function togglePres(){pres()?exitPres():enterPres()}
['fullscreenchange','webkitfullscreenchange'].forEach(ev=>
 document.addEventListener(ev,()=>{if(!isFS()&&pres())setPres(false)}));
addEventListener('mousemove',()=>{if(pres())armCursor()});
{const b=document.getElementById('play'); if(b)b.onclick=enterPres;}
addEventListener('resize',fit);
if(location.search.indexOf('shot')>=0)document.body.classList.add('shot');
fit();
{const h=(location.hash.slice(1)||'1').split('.');
 show((parseInt(h[0])||1)-1,(parseInt(h[1])||1)-1);}
addEventListener('hashchange',()=>{
 const h=(location.hash.slice(1)||'1').split('.');
 const i=(parseInt(h[0])||1)-1, s=(parseInt(h[1])||1)-1;
 if(i!==cur||s!==st)show(i,s);
});

/* ── operator surface: O overview, ? help, number+Enter jump, B/W screen, L laser ──
   navTo and coverKey are hooks: the presenter window reassigns them so that its overview, jumps and
   black screen act on the projected window instead of on itself. */
let navTo=i=>show(i,0), coverKey=null;
(function(){
coverKey=k=>setCover(document.body.classList.contains('cover-'+k)?'':k);
const KEYS=[['&rarr; &nbsp;Space &nbsp;PgDn','next step, then next slide'],['&larr; &nbsp;PgUp','previous step'],
 ['&darr; &nbsp;&uarr;','next or previous slide'],['Home &nbsp;End','first or last slide'],
 ['12 &nbsp;Enter','jump to slide 12'],['O','overview of all slides'],['/','search titles, summaries and notes'],
 ['H','backup hub'],['F','fullscreen present mode'],['B &nbsp;W','black or white screen'],['L','laser pointer'],
 ['N &nbsp;S','presenter window: notes, next step, timer'],['P','print (in the presenter window: pause the timer)'],
 ['T','reset the timer (presenter window)'],['?','this list'],['Esc','close, uncover, leave fullscreen']];
function opEl(tag,id,cls,html){const e=document.createElement(tag); e.id=id; if(cls)e.className=cls; if(html)e.innerHTML=html;
 document.body.appendChild(e); return e}
const ovBox=opEl('div','ov','opov','<header><h2>Overview</h2><span>click a slide or use the arrows and Enter &middot; Esc closes</span></header><div id="ovg"></div>');
const helpBox=opEl('div','ohelp','opov','<header><h2>Keys</h2><span>? or Esc closes</span></header><div id="okeys">'+
 KEYS.map(k=>'<div><span>'+k[0].split(' &nbsp;').map(x=>'<kbd>'+x+'</kbd>').join(' ')+'</span><span>'+k[1]+'</span></div>').join('')+'</div>');
const toast=opEl('div','otoast'), cover=opEl('div','ocover'), laser=opEl('div','olaser');
let ovSel=0, digits='', digitT, toastT;
function say(t,ms){toast.textContent=t; toast.classList.add('on'); clearTimeout(toastT);
 toastT=setTimeout(()=>toast.classList.remove('on'),ms||1600)}
function ovOpen(){
 const g=document.getElementById('ovg'); g.innerHTML='';
 SL.forEach((s,i)=>{
  const b=document.createElement('button'); b.className='ovt'+(i===cur?' cur':''); b.dataset.i=i;
  const f=document.createElement('div'); f.className='ovf';
  const c=s.cloneNode(true); c.querySelectorAll('[id]').forEach(n=>n.removeAttribute('id'));
  c.classList.remove('is-current'); c.classList.add('on'); applyStep(c,steps(i)-1);   /* the finished slide */
  f.appendChild(c); b.appendChild(f);
  const l=document.createElement('div'); l.className='ovl'; l.innerHTML='<b>'+(i+1)+'</b>';
  const t=document.createElement('span'); t.textContent=(META[i]&&META[i].t)||''; l.appendChild(t); b.appendChild(l);
  b.onclick=()=>{ovClose(); navTo(i)}; g.appendChild(b);});
 ovSel=cur; ovBox.classList.add('on'); ovMark();}
function ovClose(){ovBox.classList.remove('on'); document.getElementById('ovg').innerHTML=''}
function ovMark(){const t=[...document.querySelectorAll('.ovt')];
 t.forEach((b,i)=>b.classList.toggle('sel',i===ovSel)); if(t[ovSel])t[ovSel].scrollIntoView({block:'nearest'})}
function ovMove(key){const t=[...document.querySelectorAll('.ovt')]; if(!t.length)return;
 const cols=t.filter(b=>b.offsetTop===t[0].offsetTop).length||1;
 const d={ArrowLeft:-1,ArrowRight:1,ArrowUp:-cols,ArrowDown:cols}[key];
 ovSel=Math.max(0,Math.min(t.length-1,ovSel+d)); ovMark()}
function setCover(k){document.body.classList.remove('cover-b','cover-w'); if(k)document.body.classList.add('cover-'+k)}
addEventListener('mousemove',e=>{if(document.body.classList.contains('laser')){laser.style.left=e.clientX+'px'; laser.style.top=e.clientY+'px'}});
/* capture phase, registered before the search palette and the presenter: an open overlay swallows every key */
addEventListener('keydown',e=>{
 const t=e.target; if(t&&(t.tagName==='INPUT'||t.tagName==='TEXTAREA'||t.tagName==='SELECT'||t.isContentEditable))return;
 if(e.metaKey||e.ctrlKey||e.altKey)return;
 const pal=document.getElementById('pal'); if(pal&&pal.classList.contains('on'))return;
 const k=e.key, stop=()=>{e.preventDefault(); e.stopImmediatePropagation()};
 if(ovBox.classList.contains('on')){stop();
  if(k==='Escape'||k==='o'||k==='O')ovClose();
  else if(k==='Enter'){const i=ovSel; ovClose(); navTo(i)}
  else if(k.indexOf('Arrow')===0)ovMove(k);
  return}
 if(helpBox.classList.contains('on')){stop(); if(k==='Escape'||k==='?')helpBox.classList.remove('on'); return}
 if(/^[0-9]$/.test(k)){stop(); digits=(digits+k).slice(-4); say('go to slide '+digits,2200);
  clearTimeout(digitT); digitT=setTimeout(()=>{digits=''},2200); return}
 if(digits&&(k==='Enter'||k==='Escape'||k==='Backspace')){stop();
  if(k==='Backspace'){digits=digits.slice(0,-1); if(digits)say('go to slide '+digits,2200); else toast.classList.remove('on'); return}
  const n=parseInt(digits); digits=''; clearTimeout(digitT); toast.classList.remove('on');
  if(k==='Enter'&&n>=1)navTo(Math.min(N,n)-1); return}
 if(k==='Escape'&&(document.body.classList.contains('cover-b')||document.body.classList.contains('cover-w'))){stop(); setCover(''); return}
 if(k==='o'||k==='O'){stop(); ovOpen()}
 else if(k==='?'){stop(); helpBox.classList.add('on')}
 else if(k==='b'||k==='B'){stop(); coverKey('b')}
 else if(k==='w'||k==='W'){stop(); coverKey('w')}
 else if((k==='l'||k==='L')&&!document.body.classList.contains('presenter')){stop();
  const on=document.body.classList.toggle('laser'); say(on?'laser on':'laser off')}
},true);
})();
"""
