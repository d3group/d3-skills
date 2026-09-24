# -*- coding: utf-8 -*-
"""Speaker notes and the presenter window.

N (or S) in the deck opens the same file with ?presenter in a second window named d3notes, moved
to another screen when the browser grants window placement. That window renders presenter mode:
the current slide at half size, the next step or slide at 30 percent, the notes, a clock, an
elapsed timer (P pauses, T resets) and, when slides carry time= budgets, a pace meter. The two
windows stay in step through postMessage, so keys work in either; the presenter's overview,
number jumps and B/W screen act on the projected window, and clicks on buttons and changes of
inputs in the presenter's current slide are relayed to the same element on the projected slide.
If the popup is blocked, N toggles a notes drawer in the main window instead.
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
#ppace{position:absolute;left:690px;top:300px;width:384px;color:#8A929B;font-size:13px;line-height:1.5}
#ppace b{display:block;font-size:20px;font-weight:600;color:#E6E8EB}
#ppace b.ahead{color:#7FC3D0}
#ppace b.behind{color:var(--orange)}
#ppace b.paused{color:#8A929B}
#phint{position:absolute;left:20px;bottom:14px;color:#565E68;font-size:11px}
@media print{#ndrawer,#pnext,#pnotes,#pclock,#ppace,#phint{display:none!important}}
"""

JS = r"""
(function(){
 const isP=/[?&]presenter(?:[&=]|$)/.test(location.search);
 const drawer=document.createElement('div'); drawer.id='ndrawer'; document.body.appendChild(drawer);
 function notesOf(i){return (META[i]&&META[i].n)||''}
 const CTL='button,input,select';
 if(!isP){
  /* ── main window ── */
  let PW=null;
  document.addEventListener('d3paint',e=>{
   drawer.textContent=notesOf(e.detail.cur);
   if(PW&&!PW.closed)PW.postMessage({type:'sync',cur:e.detail.cur,st:e.detail.st},'*');});
  addEventListener('message',e=>{const d=e.data||{}; if(!PW||e.source!==PW)return;
   if(d.type==='nav'){if(d.a==='fwd')fwd(); else if(d.a==='back')back(); else if(d.a==='go')show(d.i,d.s||0)}
   else if(d.type==='hello'){PW.postMessage({type:'sync',cur:cur,st:st},'*')}
   else if(d.type==='cover')coverKey(d.k);
   else if(d.type==='relay'){            /* a control used in the presenter window drives its twin here */
    const el=SL[d.i]&&SL[d.i].querySelectorAll(CTL)[d.k]; if(!el)return;
    if(d.ev==='click'){if(el.tagName==='BUTTON')el.click(); return}
    if(el.type==='checkbox'||el.type==='radio')el.checked=!!d.checked; else el.value=d.value;
    el.dispatchEvent(new Event(d.ev,{bubbles:true}))}});
  function place(w){          /* second screen when the browser allows window placement; any refusal is fine */
   try{if(window.getScreenDetails)window.getScreenDetails().then(det=>{
    const o=det.screens.find(x=>x!==det.currentScreen); if(!o)return;
    w.moveTo(o.availLeft,o.availTop); w.resizeTo(o.availWidth,o.availHeight)}).catch(()=>{})}catch(_){}}
  addEventListener('keydown',e=>{
   if(e.target&&(e.target.tagName==='INPUT'||e.target.tagName==='TEXTAREA'))return;
   if(e.metaKey||e.ctrlKey||e.altKey)return;
   if(['n','N','s','S'].indexOf(e.key)>=0){e.preventDefault(); e.stopImmediatePropagation();
    const base=location.href.split('#')[0].split('?')[0];
    const w=window.open(base+'?presenter','d3notes','width=1100,height=700');
    if(w){PW=w; place(w)} else {document.body.classList.toggle('notes'); drawer.textContent=notesOf(cur)}}
  },true);
  drawer.textContent=notesOf(cur);
  return;
 }
 /* ── presenter window ── */
 document.body.classList.add('presenter');
 const linked=()=>!!(window.opener&&!window.opener.closed);
 const post=m=>window.opener.postMessage(m,'*');
 /* overview clicks, number jumps, search hits and B/W act on the projected window */
 const localNav=navTo, localCover=coverKey;
 navTo=i=>linked()?post({type:'nav',a:'go',i:i}):localNav(i);
 coverKey=k=>linked()?post({type:'cover',k:k}):localCover(k);
 const nextBox=document.createElement('div'); nextBox.id='pnext';
 const notes=document.createElement('div'); notes.id='pnotes';
 const clock=document.createElement('div'); clock.id='pclock';
 const pace=document.createElement('div'); pace.id='ppace';
 const hint=document.createElement('div'); hint.id='phint';
 hint.innerHTML='<kbd>&rarr;</kbd> step &nbsp;<kbd>&darr;</kbd> slide &nbsp;<kbd>P</kbd> pause timer &nbsp;<kbd>T</kbd> reset timer &nbsp;<kbd>B</kbd> black screen &nbsp;<kbd>?</kbd> keys';
 document.body.append(nextBox,notes,clock,pace,hint);
 fit=function(){SL.forEach(s=>s.style.transform='translate(-50%,-50%) scale(.5)')};
 addEventListener('resize',()=>fit()); fit();
 let t0=Date.now(), paused=false, held=0;
 const elapsed=()=>paused?held:Math.floor((Date.now()-t0)/1000);
 const fmt=x=>{x=Math.max(0,Math.round(x)); return String(Math.floor(x/60)).padStart(2,'0')+':'+String(x%60).padStart(2,'0')};
 const TOTAL=META.reduce((a,m)=>a+(m.tm||0),0);
 function tick(){const e=elapsed();
  clock.innerHTML='<b>'+new Date().toLocaleTimeString([],{hour:'2-digit',minute:'2-digit'})+'</b><span>'+fmt(e)+'</span>';
  if(!TOTAL){pace.innerHTML=paused?'<b class="paused">paused</b>':''; return}
  /* where you should be: every budget before this slide; behind only once this slide's own budget is spent too */
  const target=META.slice(0,cur).reduce((a,m)=>a+(m.tm||0),0), own=(META[cur]&&META[cur].tm)||0;
  let lab, cls;
  if(paused){lab='paused'; cls='paused'}
  else if(e>TOTAL){lab='over by '+fmt(e-TOTAL); cls='behind'}
  else if(e<target-20){lab='ahead by '+fmt(target-e); cls='ahead'}
  else if(e>target+own+20){lab='behind by '+fmt(e-target-own); cls='behind'}
  else {lab='on pace'; cls='onpace'}
  pace.innerHTML='<b class="'+cls+'">'+lab+'</b>budget '+fmt(TOTAL)+' &middot; '+fmt(target)+' before this slide'+
   (own?' &middot; this slide '+fmt(own):'')}
 function togglePause(){if(paused){t0=Date.now()-held*1000; paused=false} else {held=elapsed(); paused=true} tick()}
 setInterval(tick,1000); tick();
 function renderNext(){
  let i=cur, s=st+1;
  if(s>=steps(cur)){i=cur+1; s=0}
  nextBox.innerHTML='';
  if(i>=N){nextBox.innerHTML='<div class="pend">End of deck</div>'; return}
  const c=SL[i].cloneNode(true); c.querySelectorAll('[id]').forEach(n=>n.removeAttribute('id'));
  c.classList.add('on'); c.classList.remove('is-current'); c.style.transform='translate(-50%,-50%) scale(.3)';
  applyStep(c,s); nextBox.appendChild(c);}
 function refresh(){notes.textContent=notesOf(cur); renderNext(); tick()}
 document.addEventListener('d3paint',refresh);
 addEventListener('message',e=>{const d=e.data||{};
  if(!window.opener||e.source!==window.opener)return;
  if(d.type==='sync'&&(d.cur!==cur||d.st!==st))show(d.cur,d.st)});
 /* relay: only what a person did here (isTrusted), so a preset chip's own synthetic input event is not sent twice */
 function relay(e){if(!e.isTrusted||!linked())return;
  const sl=e.target.closest&&e.target.closest('#stage .sl.on'); if(!sl)return;
  const el=e.type==='click'?e.target.closest('button'):e.target.closest('input,select'); if(!el||!sl.contains(el))return;
  const k=[...sl.querySelectorAll(CTL)].indexOf(el); if(k<0)return;
  post({type:'relay',i:+sl.dataset.i,k:k,ev:e.type,value:el.value,checked:el.checked})}
 ['click','input','change'].forEach(t=>document.addEventListener(t,relay,true));
 addEventListener('keydown',e=>{
  if(e.target&&(e.target.tagName==='INPUT'||e.target.tagName==='TEXTAREA'))return;
  if(e.key==='t'||e.key==='T'){t0=Date.now(); held=0; paused=false; tick(); return}
  if(e.key==='p'||e.key==='P'){e.preventDefault(); e.stopImmediatePropagation(); togglePause(); return}
  if(!linked())return;      /* opened directly: the engine handles keys locally */
  if(['f','F','Escape'].indexOf(e.key)>=0){e.preventDefault(); e.stopImmediatePropagation(); return}
  const map={'ArrowRight':'fwd','PageDown':'fwd',' ':'fwd','ArrowLeft':'back','PageUp':'back'};
  let msg=null;
  if(map[e.key])msg={type:'nav',a:map[e.key]};
  else if(e.key==='ArrowDown')msg={type:'nav',a:'go',i:cur+1};
  else if(e.key==='ArrowUp')msg={type:'nav',a:'go',i:cur-1};
  else if(e.key==='Home')msg={type:'nav',a:'go',i:0};
  else if(e.key==='End')msg={type:'nav',a:'go',i:N-1};
  if(msg){e.preventDefault(); e.stopImmediatePropagation(); post(msg)}
 },true);
 if(linked())post({type:'hello'});
 refresh();
})();
"""
