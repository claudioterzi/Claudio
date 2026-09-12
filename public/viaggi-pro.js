/* Raffaello Flight Enrichment v2 — Claudio Terzi · C.Terzi
   I risultati live arricchiscono automaticamente la memoria locale.
   La verifica manuale resta un'evidenza aggiuntiva, non il motore principale. */
(function(){
'use strict';
if(window.RaffaelloFlightEnrichment)return;

const HISTORY_KEY='claudio.flight.hunter.verified.v1';
const BEST_KEY='claudio.flight.hunter.best.v2';
const INTENT_KEY='claudio.travel.intent.v1';
const MAX_HISTORY=300,MAX_BEST=80;
const $=id=>document.getElementById(id);
const esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
function load(k,f){try{const x=JSON.parse(localStorage.getItem(k)||'null');return x??f}catch{return f}}
function save(k,v){try{localStorage.setItem(k,JSON.stringify(v));return true}catch{return false}}
function now(){return new Date().toISOString()}
function normalizePlace(v){const s=String(v||'').trim();return /^[A-Za-z]{3}$/.test(s)?s.toUpperCase():s}
function monthOf(v){const s=String(v||'').trim();return /^\d{4}-\d{2}/.test(s)?s.slice(0,7):s}
function fmt(v){return Number.isFinite(Number(v))?new Intl.NumberFormat('it-IT',{style:'currency',currency:'EUR'}).format(Number(v)):'—'}
function currentRoute(){return {
  from:normalizePlace($('r-origine')?.value||$('fh-da')?.value||''),
  to:normalizePlace($('r-dest')?.value||$('fh-a')?.value||''),
  month:monthOf($('r-mese')?.value||$('fh-data')?.value||''),
  baggage:Boolean($('r-bagaglio')?.checked),objective:$('r-objective')?.value||'balanced'
}}
function fingerprint(c){return [normalizePlace(c.from||c.origine),normalizePlace(c.to||c.destinazione),monthOf(c.month||c.mese),c.baggage?'bag':'light',c.objective||c.obiettivo||'balanced'].join('|').toLowerCase()}
function signature(x){const legs=(x.flights||x.voli||[]).map(v=>[v.da,v.a,v.giorno,Number(v.prezzo||0).toFixed(2),v.vettore].join(':')).join('>');return [x.provider||x.provider_ricerca||x.source||'',x.total??x.totale??x.price??'',x.risk||x.rischio||'',legs].join('|')}
function history(){const x=load(HISTORY_KEY,[]);return Array.isArray(x)?x:[]}
function bests(){const x=load(BEST_KEY,[]);return Array.isArray(x)?x:[]}
function compactCandidate(x,ctx,certainty,scope){return {
  id:'F-'+btoa(unescape(encodeURIComponent((fingerprint(ctx)+'|'+signature(x)))).slice(0,60),
  source:'api-live',provider:x.provider_ricerca||x.provider||((x.voli||[])[0]?.vettore)||'rete-live',
  from:normalizePlace(ctx.from||ctx.origine),to:normalizePlace(ctx.to||ctx.destinazione),month:monthOf(ctx.month||ctx.mese),
  baggage:Boolean(ctx.baggage??ctx.bagaglio),objective:ctx.objective||ctx.obiettivo||'balanced',
  total:Number(x.totale??x.total??x.prezzo??x.price)||0,risk:x.rischio||x.risk||null,type:x.tipo||x.type||'volo',
  score:Number(x.score)||null,flights:x.voli||x.flights||[],observed_at:now(),certainty:certainty||'OBSERVED_IN_LIVE_SEARCH',
  scope:scope?{whole_month:Boolean(scope.whole_month),providers_successful:scope.providers_successful||[],stages:scope.stages||[]}:null
}}
function writeHistory(records){
  const all=history(),seen=new Set();const merged=[...all,...records].reverse().filter(x=>{const k=x.id||[x.source,x.provider,x.from,x.to,x.month,x.total,x.observed_at||x.at].join('|');if(seen.has(k))return false;seen.add(k);return true}).reverse();
  save(HISTORY_KEY,merged.slice(-MAX_HISTORY));
}
function writeBest(snapshot){
  const list=bests(),fp=snapshot.fingerprint;const kept=list.filter(x=>x.fingerprint!==fp);kept.push(snapshot);save(BEST_KEY,kept.slice(-MAX_BEST));
}
function ingest(payload,context){
  if(!payload||typeof payload!=='object')return null;
  const ctx={...context};ctx.from=normalizePlace(ctx.from||ctx.origine||payload.origine);ctx.to=normalizePlace(ctx.to||ctx.destinazione||payload.destinazione);ctx.month=monthOf(ctx.month||ctx.mese||payload.mese);ctx.baggage=Boolean(ctx.baggage??ctx.bagaglio??payload.bagaglio);ctx.objective=ctx.objective||ctx.obiettivo||payload.obiettivo||'balanced';
  let candidates=[],best=null,certainty=payload.certainty||'OBSERVED_IN_LIVE_SEARCH',scope=payload.scope||null;
  if(payload.best){best=payload.best;candidates=[payload.best,...(payload.alternatives||[])]}
  else if(Array.isArray(payload.itinerari)){candidates=payload.itinerari;best=candidates[0]||null}
  else if(Array.isArray(payload.mete)){candidates=payload.mete.map(x=>({...x,tipo:'meta',rischio:'basso'}));best=candidates[0]||null;ctx.to=ctx.to||'*'}
  else if(Array.isArray(payload.voli)){candidates=payload.voli.map(x=>({totale:x.prezzo,prezzo:x.prezzo,tipo:'occasione',rischio:'basso',voli:[x],provider:x.vettore}));best=candidates[0]||null;ctx.to=ctx.to||'*'}
  if(!candidates.length)return null;
  const records=candidates.slice(0,8).map(x=>compactCandidate(x,ctx,certainty,scope));writeHistory(records);
  if(best){const bestRecord=compactCandidate(best,ctx,certainty,scope);writeBest({schema:'RAFFAELLO_FLIGHT_BEST_V2',fingerprint:fingerprint(ctx),from:ctx.from,to:ctx.to,month:ctx.month,baggage:ctx.baggage,objective:ctx.objective,best:bestRecord,alternatives:records.slice(1,6),why_best:payload.why_best||'',assumptions:payload.assumptions||'',scope,updated_at:now()})}
  const detail={context:ctx,payload,best:best?compactCandidate(best,ctx,certainty,scope):null};window.dispatchEvent(new CustomEvent('raffaello:flight:enriched',{detail}));renderPanel();return detail;
}
function bestFor(context){const fp=fingerprint(context);return bests().find(x=>x.fingerprint===fp)||null}
function recordManual(data){
  const ctx={...currentRoute(),...data};const price=Number(data.price);if(!(price>0))throw new Error('Prezzo non valido.');
  const rec={id:'M-'+Date.now(),source:'manual-check',provider:String(data.provider||'Verifica manuale').trim(),from:normalizePlace(ctx.from),to:normalizePlace(ctx.to),month:monthOf(ctx.month),baggage:Boolean(ctx.baggage),objective:ctx.objective||'balanced',total:price,price,observed_at:now(),at:now(),verified_by:'manual',certainty:'MANUALLY_OBSERVED'};writeHistory([rec]);renderPanel();return rec;
}
function prefillFromIntent(){
  const p=new URLSearchParams(location.search),saved=load(INTENT_KEY,null);const src=p.get('source')==='fabbrica'?Object.fromEntries(p.entries()):(saved&&saved.source==='fabbrica'?saved:null);if(!src)return;
  const pairs=[['from','r-origine'],['to','r-dest'],['destination','r-dest']];pairs.forEach(([k,id])=>{if(src[k]&&$(id)&&!$(id).value)$(id).value=src[k]});
  const m=monthOf(src.date||src.month||'');if(m&&$('r-mese')&&!$('r-mese').value)$('r-mese').value=m;
  if(src.from&&$('o-origine')&&!$('o-origine').value)$('o-origine').value=src.from;if(m&&$('o-mese')&&!$('o-mese').value)$('o-mese').value=m;
}
function renderPanel(){
  const host=$('flight-memory-panel');if(!host)return;const r=currentRoute(),snap=bestFor(r);const box=host.querySelector('[data-memory-best]');
  if(!snap){box.innerHTML='<p class="fem-muted">Nessun risultato memorizzato per questa rotta. La prossima ricerca live lo registrerà automaticamente.</p>';return}
  const b=snap.best;box.innerHTML='<strong>'+esc(fmt(b.total))+'</strong><span>'+esc((b.provider||'rete live')+' · rischio '+(b.risk||'—')+(b.score?' · score '+b.score:'')+' · '+new Date(snap.updated_at).toLocaleString('it-IT'))+'</span><small>'+esc(snap.why_best||'Migliore trovato nello spazio cercato.')+'</small>';
}
function mountPanel(){
  if(!$('form-rotta')||$('flight-memory-panel'))return;const panel=document.createElement('section');panel.id='flight-memory-panel';panel.innerHTML='<p class="fem-kicker">MEMORIA RAFFAELLO · AUTO-ENRICH</p><h2>Ogni ricerca migliora la prossima.</h2><p class="fem-muted">Il risultato live e le alternative vengono conservati automaticamente sul dispositivo. La verifica manuale è solo una prova aggiuntiva.</p><div data-memory-best class="fem-best"></div><details><summary>Aggiungi una verifica manuale esterna</summary><form id="fem-manual"><label>Prezzo totale visto (€)<input id="fem-price" type="number" min="0" step="0.01" required></label><label>Fonte<input id="fem-provider" maxlength="80" placeholder="es. sito compagnia"></label><button type="submit">Aggiungi evidenza</button></form></details>';
  const style=document.createElement('style');style.textContent='.fem-kicker{color:#8a6f2e;font-size:.7rem;letter-spacing:.14em}.fem-muted{color:#7a7468;font-size:.82rem}#flight-memory-panel{margin:2rem 0;padding:1rem;border:1px solid #2a2a32;border-radius:10px;background:#141418}#flight-memory-panel h2{font:400 1.25rem Georgia,serif;color:#c9a84c;margin:.25rem 0}.fem-best{display:grid;gap:.2rem;padding:.8rem;margin:.8rem 0;background:#0c0c0e;border-radius:8px}.fem-best strong{font:1.25rem Courier New,monospace;color:#4c9a6b}.fem-best span,.fem-best small{color:#8d877b}.fem-best small{font-size:.72rem}#flight-memory-panel summary{cursor:pointer;color:#c9a84c}#fem-manual{display:grid;grid-template-columns:1fr 1fr auto;gap:.6rem;margin-top:.8rem;padding:0;background:transparent;border:0}#fem-manual input,#fem-manual button{min-height:42px;background:#0c0c0e;border:1px solid #3b3940;color:#e8e4d8;border-radius:7px;padding:.5rem}#fem-manual button{color:#c9a84c;cursor:pointer}@media(max-width:650px){#fem-manual{grid-template-columns:1fr}}';document.head.appendChild(style);
  $('form-rotta').insertAdjacentElement('afterend',panel);$('fem-manual').addEventListener('submit',e=>{e.preventDefault();try{recordManual({price:$('fem-price').value,provider:$('fem-provider').value});$('fem-price').value='';}catch(err){alert(err.message)}});['r-origine','r-dest','r-mese','r-bagaglio','r-objective'].forEach(id=>$(id)?.addEventListener('input',renderPanel));renderPanel();
}
window.addEventListener('raffaello:flight:result',e=>{if(e.detail)ingest(e.detail.payload||e.detail,e.detail.context||{})});
window.RaffaelloFlightEnrichment={ingest,bestFor,history,bests,recordManual,normalizePlace,version:'2.0.0'};
function boot(){prefillFromIntent();mountPanel()}
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',boot);else boot();
})();
