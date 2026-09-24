# -*- coding: utf-8 -*-
"""Navigation: jump tabs, data-jump links, the / search palette and H for the backup hub.

Ported from d3group/DisputationNicoElbert (talk/deck.py NAV_JS). The palette
searches every slide's page label, title, group and summary from the manifest, and the speaker
notes (a notes-only hit shows a snippet). Jumps go through navTo, so they also work from the
presenter window.
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
#pall .pr .sn{display:block;margin-top:3px;font-size:11.5px;font-weight:400;color:#5B636D;line-height:1.4}
#pall .pr .sn mark{background:rgba(242,145,0,.25);color:inherit;border-radius:2px}
@media print{#pal{display:none!important}}
"""

JS = r"""
document.addEventListener('click',function(e){
 var t=e.target.closest('[data-jump]'); if(t){e.stopPropagation(); navTo(+t.dataset.jump)}});
document.querySelectorAll('.jt').forEach(function(b){b.onclick=function(){navTo(+b.dataset.go)}});
var HUB=__HUB__;
var QIXD=META.map(function(m,i){return [m.l||'', m.t, m.g, i]});
var pal=document.createElement('div'); pal.id='pal';
pal.innerHTML='<div class="palbox"><div class="palin"><input id="pali" placeholder="Search slides: title, section, summary, notes" autocomplete="off"></div><div id="pall"></div></div>';
document.body.appendChild(pal);
var psel=0,pin=document.getElementById('pali'),plist=document.getElementById('pall');
function pesc(x){return String(x).replace(/[&<>"]/g,function(c){return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]})}
/* a hit only in the speaker notes shows the words around it, so the row says why it matched */
function psnip(notes,q){var at=notes.toLowerCase().indexOf(q); if(at<0)return '';
 var a=Math.max(0,at-40), b=Math.min(notes.length,at+q.length+60);
 return '<span class="sn">'+(a?'&hellip;':'')+pesc(notes.slice(a,at))+'<mark>'+pesc(notes.slice(at,at+q.length))+'</mark>'+
  pesc(notes.slice(at+q.length,b))+(b<notes.length?'&hellip;':'')+'</span>'}
function pmatch(){var q=pin.value.toLowerCase().trim();
 return QIXD.filter(function(r){if(!q)return true;
  var head=(r[0]+' '+(META[r[3]].kk||'')+' '+r[1]+' '+r[2]+' '+(META[r[3]].s||'')).toLowerCase();
  return head.indexOf(q)>=0||(META[r[3]].n||'').toLowerCase().indexOf(q)>=0})}
function prender(){var m=pmatch(), q=pin.value.toLowerCase().trim(); if(psel>=m.length)psel=Math.max(0,m.length-1);
 plist.innerHTML=m.map(function(r,i){
  var head=(r[0]+' '+(META[r[3]].kk||'')+' '+r[1]+' '+r[2]+' '+(META[r[3]].s||'')).toLowerCase();
  var sn=(q&&head.indexOf(q)<0)?psnip(META[r[3]].n||'',q):'';
  return '<div class="pr'+(i===psel?' sel':'')+'" data-pi="'+i+'"><span class="n">'+(r[0]||String(r[3]+1))+
   '</span><span class="t">'+r[1]+sn+'</span><span class="g">'+r[2]+'</span></div>'}).join('');
 plist.querySelectorAll('.pr').forEach(function(el){el.onclick=function(){pjump(+el.dataset.pi)}})}
function pjump(i){var m=pmatch(); if(m[i]){pclose(); navTo(m[i][3])}}
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
 else if(HUB>=0&&(e.key==='h'||e.key==='H'))navTo(HUB)
},true);
"""
