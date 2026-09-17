# -*- coding: utf-8 -*-
"""Navigation: jump tabs, data-jump links, the / search palette and H for the backup hub.

Ported from d3group/DisputationNicoElbert (talk/deck.py NAV_JS). The palette
searches every slide's page label, title and group from the manifest.
"""

CSS = r"""
[data-jump]{cursor:pointer}
.jl{color:var(--navy);text-decoration:underline;text-decoration-color:var(--orange);text-underline-offset:3px}
.hub{display:grid;grid-template-columns:1fr 1fr;gap:18px 48px;font-size:var(--fs-footnote)}
.hub h4{font-size:var(--fs-normal);font-weight:700;margin-bottom:6px}
.hub .hi{display:flex;gap:12px;padding:4px 0;border-bottom:1px solid var(--line)}
.hub .hi .hn{color:var(--gray);min-width:3em;font-variant-numeric:tabular-nums}
.hub .hi:hover{color:var(--orange)}
#pal{position:fixed;inset:0;background:rgba(6,8,12,.55);z-index:90;display:none;align-items:flex-start;justify-content:center;padding-top:11vh}
#pal.on{display:flex}
#pal .palbox{width:640px;max-height:64vh;background:#fff;border-radius:10px;overflow:hidden;box-shadow:0 30px 90px rgba(0,0,0,.5);
 display:flex;flex-direction:column;font-family:'Inter',system-ui,sans-serif}
#pal .palin{padding:14px 18px;border-bottom:1px solid #E4E8ED}
#pali{width:100%;border:0;outline:0;font-size:16px;font-family:inherit;color:#0A0C10}
#pall{overflow-y:auto}
#pall .pr{display:grid;grid-template-columns:52px 1fr auto;gap:12px;align-items:baseline;padding:9px 18px;cursor:pointer;border-bottom:1px solid #F6F8FA}
#pall .pr.sel{background:rgba(242,145,0,.10)}
#pall .pr .n{font-family:var(--mono);font-size:10px;font-weight:600;color:var(--navy)}
#pall .pr .t{font-size:13.5px;font-weight:500;color:#0A0C10}
#pall .pr .g{font-family:var(--mono);font-size:9px;color:#5B636D}
@media print{#pal{display:none!important}}
"""

JS = r"""
document.addEventListener('click',function(e){
 var t=e.target.closest('[data-jump]'); if(t){e.stopPropagation(); go(+t.dataset.jump)}});
document.querySelectorAll('.jt').forEach(function(b){b.onclick=function(){go(+b.dataset.go)}});
var HUB=__HUB__;
var QIXD=META.map(function(m,i){return [m.l||'', m.t, m.g, i]});
var pal=document.createElement('div'); pal.id='pal';
pal.innerHTML='<div class="palbox"><div class="palin"><input id="pali" placeholder="Search slides: title, section, summary" autocomplete="off"></div><div id="pall"></div></div>';
document.body.appendChild(pal);
var psel=0,pin=document.getElementById('pali'),plist=document.getElementById('pall');
function pmatch(){var q=pin.value.toLowerCase().trim();
 return QIXD.filter(function(r){return !q||((r[0]+' '+r[1]+' '+r[2]+' '+(META[r[3]].s||'')).toLowerCase().indexOf(q)>=0)})}
function prender(){var m=pmatch(); if(psel>=m.length)psel=Math.max(0,m.length-1);
 plist.innerHTML=m.map(function(r,i){
  return '<div class="pr'+(i===psel?' sel':'')+'" data-pi="'+i+'"><span class="n">'+(r[0]||String(r[3]+1))+
   '</span><span class="t">'+r[1]+'</span><span class="g">'+r[2]+'</span></div>'}).join('');
 plist.querySelectorAll('.pr').forEach(function(el){el.onclick=function(){pjump(+el.dataset.pi)}})}
function pjump(i){var m=pmatch(); if(m[i]){pclose(); go(m[i][3])}}
function popen(){pal.classList.add('on'); pin.value=''; psel=0; prender(); pin.focus()}
function pclose(){pal.classList.remove('on'); pin.blur()}
pin.addEventListener('input',function(){psel=0; prender()});
addEventListener('keydown',function(e){
 var open=pal.classList.contains('on');
 if(open){e.stopImmediatePropagation();
  if(e.key==='Escape')pclose();
  else if(e.key==='ArrowDown'){e.preventDefault(); psel=Math.min(psel+1,Math.max(0,pmatch().length-1)); prender()}
  else if(e.key==='ArrowUp'){e.preventDefault(); psel=Math.max(psel-1,0); prender()}
  else if(e.key==='Enter')pjump(psel);
  return}
 if(e.target&&(e.target.tagName==='INPUT'||e.target.tagName==='TEXTAREA'))return;
 if(e.key==='/'){e.preventDefault(); e.stopImmediatePropagation(); popen()}
 else if(HUB>=0&&(e.key==='h'||e.key==='H'))show(HUB,0)
},true);
"""
