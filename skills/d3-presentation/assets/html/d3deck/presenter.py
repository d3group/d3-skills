# -*- coding: utf-8 -*-
"""Speaker notes.

N in the deck opens the same file with ?presenter in a second window named d3notes. That window
renders presenter mode: the current slide at half size, the next step or slide
at 30 percent, the notes, a clock and an elapsed timer. The two windows stay in
step through postMessage, so keys work in either. If the popup is blocked, N
toggles a notes drawer in the main window instead.
"""

CSS = r"""
#ndrawer{display:none;position:fixed;left:0;right:0;bottom:34px;max-height:30vh;overflow:auto;background:#15181d;color:#E6E8EB;
 padding:14px 20px;font-size:16px;line-height:1.5;white-space:pre-wrap;z-index:65;border-top:1px solid rgba(255,255,255,.1)}
body.notes #ndrawer{display:block}
body.presenter{background:#0B0D10}
body.presenter #top,body.presenter #foot,body.presenter #bar,body.presenter #play,body.presenter #pexit,body.presenter #ndrawer{display:none!important}
body.presenter #stage{position:absolute;left:20px;top:20px;width:640px;height:360px;right:auto;bottom:auto}
body.presenter #stage .sl{box-shadow:0 10px 40px rgba(0,0,0,.5)}
#pnext{position:absolute;left:690px;top:20px;width:384px;height:216px;overflow:hidden;background:#15181d;border-radius:4px}
#pnext .sl{left:50%;top:50%;box-shadow:none}
#pnext .pend{color:#8A929B;font-size:14px;padding:20px}
#pnotes{position:absolute;left:20px;top:400px;right:20px;bottom:50px;overflow:auto;white-space:pre-wrap;color:#E6E8EB;
 font-size:22px;line-height:1.5}
#pclock{position:absolute;left:690px;top:250px;color:#E6E8EB;font-size:34px;font-variant-numeric:tabular-nums}
#pclock b{margin-right:24px;font-weight:600}
#pclock span{color:var(--orange)}
#phint{position:absolute;left:20px;bottom:14px;color:#565E68;font-size:11px}
@media print{#ndrawer,#pnext,#pnotes,#pclock,#phint{display:none!important}}
"""

JS = r"""
(function(){
 const isP=/[?&]presenter(?:[&=]|$)/.test(location.search);
 const drawer=document.createElement('div'); drawer.id='ndrawer'; document.body.appendChild(drawer);
 function notesOf(i){return (META[i]&&META[i].n)||''}
 if(!isP){
  /* ── main window ── */
  let PW=null;
  document.addEventListener('d3paint',e=>{
   drawer.textContent=notesOf(e.detail.cur);
   if(PW&&!PW.closed)PW.postMessage({type:'sync',cur:e.detail.cur,st:e.detail.st},'*');});
  addEventListener('message',e=>{const d=e.data||{}; if(!PW||e.source!==PW)return;
   if(d.type==='nav'){if(d.a==='fwd')fwd(); else if(d.a==='back')back(); else if(d.a==='go')show(d.i,d.s||0)}
   else if(d.type==='hello'){PW.postMessage({type:'sync',cur:cur,st:st},'*')}});
  addEventListener('keydown',e=>{
   if(e.target&&e.target.tagName==='INPUT')return;
   if(e.key==='n'||e.key==='N'){e.preventDefault(); e.stopImmediatePropagation();
    const base=location.href.split('#')[0].split('?')[0];
    const w=window.open(base+'?presenter','d3notes','width=1100,height=700');
    if(w){PW=w} else {document.body.classList.toggle('notes'); drawer.textContent=notesOf(cur)}}
  },true);
  drawer.textContent=notesOf(cur);
  return;
 }
 /* ── presenter window ── */
 document.body.classList.add('presenter');
 const nextBox=document.createElement('div'); nextBox.id='pnext';
 const notes=document.createElement('div'); notes.id='pnotes';
 const clock=document.createElement('div'); clock.id='pclock';
 const hint=document.createElement('div'); hint.id='phint';
 hint.innerHTML='<kbd>&rarr;</kbd> step &nbsp;<kbd>&darr;</kbd> slide &nbsp;<kbd>T</kbd> reset timer';
 document.body.append(nextBox,notes,clock,hint);
 fit=function(){SL.forEach(s=>s.style.transform='translate(-50%,-50%) scale(.5)')};
 addEventListener('resize',()=>fit()); fit();
 let t0=Date.now();
 function tick(){const e=Math.floor((Date.now()-t0)/1000);
  const mm=String(Math.floor(e/60)).padStart(2,'0'), ss=String(e%60).padStart(2,'0');
  clock.innerHTML='<b>'+new Date().toLocaleTimeString([],{hour:'2-digit',minute:'2-digit'})+'</b><span>'+mm+':'+ss+'</span>'}
 setInterval(tick,1000); tick();
 function renderNext(){
  let i=cur, s=st+1;
  if(s>=steps(cur)){i=cur+1; s=0}
  nextBox.innerHTML='';
  if(i>=N){nextBox.innerHTML='<div class="pend">End of deck</div>'; return}
  const c=SL[i].cloneNode(true); c.querySelectorAll('[id]').forEach(n=>n.removeAttribute('id'));
  c.classList.add('on'); c.style.transform='translate(-50%,-50%) scale(.3)';
  applyStep(c,s); nextBox.appendChild(c);}
 function refresh(){notes.textContent=notesOf(cur); renderNext()}
 document.addEventListener('d3paint',refresh);
 addEventListener('message',e=>{const d=e.data||{};
  if(!window.opener||e.source!==window.opener)return;
  if(d.type==='sync'&&(d.cur!==cur||d.st!==st))show(d.cur,d.st)});
 addEventListener('keydown',e=>{
  if(e.key==='t'||e.key==='T'){t0=Date.now(); tick(); return}
  if(!window.opener||window.opener.closed)return;      /* opened directly: the engine handles keys locally */
  if(['f','F','p','P','Escape'].indexOf(e.key)>=0){e.preventDefault(); e.stopImmediatePropagation(); return}
  const map={'ArrowRight':'fwd','PageDown':'fwd',' ':'fwd','ArrowLeft':'back','PageUp':'back'};
  let msg=null;
  if(map[e.key])msg={type:'nav',a:map[e.key]};
  else if(e.key==='ArrowDown')msg={type:'nav',a:'go',i:cur+1};
  else if(e.key==='ArrowUp')msg={type:'nav',a:'go',i:cur-1};
  else if(e.key==='Home')msg={type:'nav',a:'go',i:0};
  else if(e.key==='End')msg={type:'nav',a:'go',i:N-1};
  if(msg){e.preventDefault(); e.stopImmediatePropagation(); window.opener.postMessage(msg,'*')}
 },true);
 if(window.opener&&!window.opener.closed)window.opener.postMessage({type:'hello'},'*');
 refresh();
})();
"""
