'use strict';
// Normalize imperfect model Markdown, then escape every text fragment.
// No model-supplied HTML, URLs or event handlers are enabled.
window.formatAI=function(text){
 let source=String(text??'').replace(/\r\n?/g,'\n');
 source=source.replace(/\\n/g,'\n').replace(/\\([#*`_])/g,'$1');
 source=source.replace(/^\s*```(?:markdown|md)?\s*\n?/i,'').replace(/\n?```\s*$/,'');
 // Providers sometimes collapse every section and bullet onto a single line.
 source=source.replace(/[ \t]+(#{1,6}\s+)/g,'\n$1')
  .replace(/[ \t]+([*•]\s+(?=\*\*|[A-Z]))/g,'\n$1')
  .replace(/[ \t]+(-\s+(?=\*\*))/g,'\n$1');
 const titles=['Pause and verify','What to check next','Alternative explanations','Recommended verification','Observations','Result','Evidence','Limits','Summary','Next steps'];
 const known=new RegExp('^(?:#{1,6}\\s+|\\*\\*)('+titles.join('|')+')(?:\\*\\*)?\\s*:?[ \\t]+(.+)$','i');
 source=source.split('\n').map(line=>{const m=line.match(known);return m?'## '+m[1]+'\n'+m[2]:line}).join('\n');
 const inline=t=>esc(t).replace(/\*\*([^*]+)\*\*/g,'<strong>$1</strong>').replace(/`([^`]+)`/g,'<code>$1</code>');
 let out='',list=null,section=false;
 const closeList=()=>{if(list){out+=`</${list}>`;list=null}};
 const closeSection=()=>{closeList();if(section){out+='</section>';section=false}};
 for(const raw of source.split('\n')){
  const line=raw.trim();if(!line){closeList();continue}
  const heading=line.match(/^#{1,6}\s+(.+)/)||line.match(/^\*\*([^*]+)\*\*\s*:?$/);
  const bullet=line.match(/^[-*•]\s+(.+)/),number=line.match(/^\d+[.)]\s+(.+)/);
  if(heading){
   closeSection();const title=heading[1].replace(/\*\*/g,'');
   const tone=/pause|limit|uncertaint/i.test(title)?'caution':/next|verification|check/i.test(title)?'action':'standard';
   out+=`<section class="answer-section answer-${tone}"><h4>${inline(title)}</h4>`;section=true;
  }else if(bullet||number){const kind=bullet?'ul':'ol';if(list!==kind){closeList();out+=`<${kind}>`;list=kind}out+=`<li>${inline((bullet||number)[1])}</li>`}
  else{closeList();out+=`<p>${inline(line)}</p>`}
 }
 closeSection();return `<div class="answer-cards">${out}</div>`;
};
(()=>{
 let context=null, current=null, timer=null, started=0;
 const box=document.getElementById('inspection-support');
 const progress=document.getElementById('check-progress');
 window.resetInspection=()=>{context=null;current=null;box.classList.add('hidden');box.innerHTML='';window.inspectionBusy(false)};
 window.inspectionBusy=active=>{
  clearInterval(timer);progress.classList.toggle('hidden',!active);
  if(active){started=Date.now();const tick=()=>{progress.innerHTML=`<span class="pulse-dot"></span><div><b>AI investigation in progress</b><p>${Math.floor((Date.now()-started)/1000)} seconds elapsed · Waiting for the server. Agent activity appears when the request finishes.</p></div>`};tick();timer=setInterval(tick,1000)}
 };
 window.showInspection=(r,payload)=>{
  if(current===r&&!box.classList.contains('hidden'))return;
  current=r;context=payload;const q=r.quality,v=r.verification;
  if(!q||!v)return;
  box.classList.remove('hidden');
  box.innerHTML=`<div class="decision-banner ${q.status==='review_required'?'needs-review':''}"><span class="eyebrow">SCREENING · ${r.cycle_id?'RECORDING '+r.cycle_id:'UPLOAD'}</span><h2>${esc(q.title)}</h2><p><b>Model suggests: ${esc(r.label_name)}</b></p><ul>${q.reasons.map(t=>`<li>${esc(t)}</li>`).join('')}</ul><p class="small-text">A result is a clue for inspection, not a confirmed fault.</p></div>
  <div class="panel pad spaced"><p class="eyebrow">NEXT BEST CHECKS</p><h2>${esc(v.title)}</h2><p class="small-text">Expand a step to see why it matters. Tick it after reviewing it; this does not confirm a repair.</p><div class="check-count" role="status">0 of ${v.checks.length} steps reviewed</div><progress id="review-progress" value="0" max="${v.checks.length}" aria-label="Inspection steps reviewed"></progress>
  ${v.checks.map((c,i)=>`<div class="verification-step"><label class="check"><input type="checkbox" class="inspection-check"><b>${i+1}. ${esc(c.title)}</b></label><details ${i===0?'open':''}><summary>Why and what to verify</summary><p>${esc(c.why)}</p><p><b>What we need:</b> ${esc(c.needed)}</p><p><b>How it helps:</b> ${esc(c.decision)}</p>${c.references.length?`<small>Reference: ${esc(c.references.join(', '))}</small>`:''}</details></div>`).join('')}
  <details class="simple-details"><summary>What we still do not know</summary><ul>${v.missing_context.map(t=>`<li>${esc(t)}</li>`).join('')}</ul><p>${esc(q.limitation)}</p></details></div>
  <details class="panel pad spaced simple-details"><summary>Manual guidance & source</summary>${v.manual_references.map(ref=>`<h3>${esc(ref.title)}</h3><p class="small-text">${esc(ref.section)} · ${esc(ref.id)}</p><p>${esc(ref.summary)}</p><p class="reference-scope">${esc(ref.applicability)}</p><a href="${esc(ref.url)}" target="_blank" rel="noopener noreferrer" class="text-link">Read source manual ↗</a><p class="small-text">${esc(ref.method)}</p>`).join('')}</details>
  <div class="panel pad spaced"><p class="eyebrow">TAKE IT TO AN ENGINEER</p><h3>Download an inspection report</h3><p class="small-text">PDF with measurements, uncertainty flags, next checks and cited guidance. No AI connection needed. Your notes stay in this tab until exported.</p><label>Engineer name (optional)<input id="pdf-engineer" maxlength="120" placeholder="Name"></label><label class="spaced">Inspection notes (optional)<textarea id="pdf-notes" maxlength="2000" rows="2" placeholder="Write actual findings or questions here"></textarea></label><button class="primary spaced" id="pdf-download">↓ Download PDF report</button><p id="pdf-status" role="status"></p></div>
  <details class="panel pad spaced simple-details"><summary>How well does the uncertainty check work?</summary><div id="gate-evaluation">Loading measured results…</div></details>`;
  box.querySelectorAll('.inspection-check').forEach(c=>c.onchange=()=>{const n=box.querySelectorAll('.inspection-check:checked').length;box.querySelector('.check-count').textContent=`${n} of ${v.checks.length} steps reviewed`;box.querySelector('progress').value=n});
  const target=box.querySelector('#gate-evaluation');
  api('/api/quality/evaluation').then(m=>{if(!target.isConnected)return;target.innerHTML=`<p>On <b>${m.test_cycles}</b> held-out recordings, these rules flagged <b>${m.flagged_cycles}</b> for review.</p><ul><li>Flagged ${m.flagged_classifier_errors} of ${m.total_classifier_errors} classifier mistakes.</li><li>Also flagged ${m.flagged_correct_predictions} correct predictions.</li><li>Missed ${m.unflagged_classifier_errors} mistake: an unflagged result still needs review.</li></ul><p class="small-text">${esc(m.limitations)}</p>`}).catch(e=>{if(target.isConnected)target.textContent=e.message});
  box.querySelector('#pdf-download').onclick=async()=>{
   const button=box.querySelector('#pdf-download'),status=box.querySelector('#pdf-status');button.disabled=true;status.textContent='Building report…';
   try{const live=window.inspectionContext();const res=await fetch('/api/report.pdf',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({...live,engineer:box.querySelector('#pdf-engineer').value,notes:box.querySelector('#pdf-notes').value})});if(!res.ok){const d=await res.json();throw Error(d.error||'Report failed')}
    const url=URL.createObjectURL(await res.blob()),a=document.createElement('a');a.href=url;a.download='hydraulic-inspection.pdf';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);status.textContent='PDF downloaded. This remains an inspection draft.';
   }catch(e){status.textContent=e.message}finally{button.disabled=false}
  };
 };
})();
