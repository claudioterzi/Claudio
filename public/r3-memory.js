(function(){
'use strict';
// R3 memory integrity hardening v1.1.0 — Claudio Terzi · C.Terzi
// Local-only. Reload older tabs before writing; never disable access controls.
const KEY='r3.memory.ledger.v1';
const META='r3.memory.meta.v1';
const REPORT='r3.memory.collate.latest.v1';
const VERSION='1.1.0';
const LOCK=KEY+'.write';
const STATES=new Set(['FATTO','INFERENZA','IPOTESI','SIMULAZIONE']);
const MAX_EVENTS=5000, MAX_IMPORT_BYTES=8*1024*1024;
let latest=null;
let activeCanon={priorities:[],current_evidence:[]};
let canonStatus={state:'not_loaded',error:'Canone non ancora caricato.'};
let writeQueue=Promise.resolve();
const enc=new TextEncoder();
const esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
async function sha256(text){const d=await crypto.subtle.digest('SHA-256',enc.encode(text));return [...new Uint8Array(d)].map(b=>b.toString(16).padStart(2,'0')).join('');}
// V1 records remain byte-compatible: never rehash or renumber existing events.
function load(){
 const raw=localStorage.getItem(KEY);
 if(raw===null)return [];
 const ledger=JSON.parse(raw);
 if(!Array.isArray(ledger))throw new Error('Ledger locale non valido: esportare una copia prima del ripristino.');
 return ledger;
}
function stable(e){return JSON.stringify({id:e.id,ts:e.ts,state:e.state,claim:e.claim,evidence:e.evidence,falsifier:e.falsifier,source:e.source,priority:e.priority,previous_hash:e.previous_hash||null});}
function validRecord(e){
 if(!e||typeof e!=='object'||Array.isArray(e))return false;
 const fields=['id','ts','state','claim','evidence','falsifier','source','priority','previous_hash','hash'];
 if(Object.keys(e).some(k=>!fields.includes(k)))return false;
 if(!fields.filter(k=>k!=='previous_hash').every(k=>typeof e[k]==='string'&&e[k].length<=50000))return false;
 return !!e.id&&e.id.length<=256&&e.ts.length<=64&&Number.isFinite(Date.parse(e.ts))&&
  STATES.has(e.state)&&!!e.claim.trim()&&e.priority.length<=128&&/^[a-f0-9]{64}$/.test(e.hash)&&
  (e.previous_hash===null||typeof e.previous_hash==='string'&&/^[a-f0-9]{64}$/.test(e.previous_hash));
}
async function verifyLedger(ledger){
 if(!Array.isArray(ledger)||ledger.length>MAX_EVENTS)return {ok:false,index:0,reason:'schema_or_limit'};
 const ids=new Set(),hashes=new Set();
 for(let i=0;i<ledger.length;i++){
  const e=ledger[i];
  if(!validRecord(e))return {ok:false,index:i,reason:'schema'};
  if(ids.has(e.id)||hashes.has(e.hash))return {ok:false,index:i,reason:'duplicate_identity'};
  ids.add(e.id);hashes.add(e.hash);
  if(e.hash!==await sha256(stable(e)))return {ok:false,index:i,reason:'hash'};
  if(e.previous_hash!==(i?ledger[i-1].hash:null))return {ok:false,index:i,reason:i?'chain':'genesis'};
 }
 return {ok:true,count:ledger.length};
}
async function verify(){try{return await verifyLedger(load())}catch{return {ok:false,index:0,reason:'storage_or_json'}}}
function withWriteLock(task){
 // A per-page Promise alone does NOT protect other tabs. Never pretend it does.
 const run=async()=>{
  if(!globalThis.navigator?.locks?.request)throw new Error('Scrittura disabilitata: Web Locks non disponibile. Usare un browser HTTPS compatibile; i dati restano intatti.');
  return navigator.locks.request(LOCK,{mode:'exclusive'},task);
 };
 const pending=writeQueue.then(run,run);
 writeQueue=pending.catch(()=>{});
 return pending;
}
function commitLedger(ledger,expectedRaw){
 const serialized=JSON.stringify(ledger);
 if(enc.encode(serialized).length>MAX_IMPORT_BYTES)throw new Error('Ledger troppo grande: esportare e archiviare prima di proseguire.');
 if(localStorage.getItem(KEY)!==expectedRaw)throw new Error('Memoria cambiata durante la scrittura. Ricaricare tutte le vecchie schede e riprovare.');
 // The ledger is ONE storage write, after all validation. Metadata is non-authoritative.
 localStorage.setItem(KEY,serialized);
 try{localStorage.setItem(META,JSON.stringify({updated_at:new Date().toISOString(),count:ledger.length,writer_version:VERSION,head:ledger.at(-1)?.hash||null}))}catch{}
}
function checkedInput(input){
 if(!input||!STATES.has(input.state))throw new Error('Stato della memoria non valido.');
 const result={state:input.state};
 for(const key of ['claim','evidence','falsifier','source','priority']){
  const value=input[key]??'';
  if(typeof value!=='string'||value.length>50000)throw new Error('Campo non valido: '+key);
  result[key]=value.trim();
 }
 if(!result.claim)throw new Error('La memoria deve contenere una dichiarazione.');
 result.priority=result.priority||'R3-019';
 if(result.priority.length>128)throw new Error('Priorità non valida.');
 return result;
}
async function append(input){
 const data=checkedInput(input); // Snapshot caller input before waiting for the lock.
 return withWriteLock(async()=>{
  const before=localStorage.getItem(KEY),ledger=load(),v=await verifyLedger(ledger);
  if(!v.ok)throw new Error('Scrittura rifiutata: catena esistente non valida ('+v.reason+').');
  if(ledger.length>=MAX_EVENTS)throw new Error('Limite locale raggiunto: esportare il ledger.');
  const e={id:'R3E-'+crypto.randomUUID(),ts:new Date().toISOString(),...data,previous_hash:ledger.at(-1)?.hash||null};
  e.hash=await sha256(stable(e));
  ledger.push(e);commitLedger(ledger,before);return e;
 });
}
function render(){const ledger=load();const list=document.getElementById('r3-ledger-list');const count=document.getElementById('r3-ledger-count');if(count)count.textContent=String(ledger.length);if(!list)return;list.innerHTML='';ledger.slice().reverse().slice(0,40).forEach(e=>{const a=document.createElement('article');a.className='memory-event';a.innerHTML=`<div class="event-top"><span class="tag ${esc(e.state.toLowerCase())}">${esc(e.state)}</span><code>${esc(e.priority)}</code><time>${new Date(e.ts).toLocaleString('it-IT')}</time></div><h3>${esc(e.claim)}</h3><p><strong>Evidenza:</strong> ${esc(e.evidence||'—')}</p><p><strong>Cade se:</strong> ${esc(e.falsifier||'—')}</p><p><strong>Fonte:</strong> ${esc(e.source||'locale')}</p><small>${esc(e.hash.slice(0,18))}…</small>`;list.appendChild(a)});if(!ledger.length)list.innerHTML='<p class="muted">Nessun evento locale ancora registrato.</p>';}
function download(){const data={schema:'R3_MEMORY_LEDGER_V1',exported_at:new Date().toISOString(),events:load()};const blob=new Blob([JSON.stringify(data,null,2)],{type:'application/json'});const a=document.createElement('a');a.href=URL.createObjectURL(blob);a.download='R3_MEMORY_LEDGER_'+new Date().toISOString().slice(0,10)+'.json';a.click();setTimeout(()=>URL.revokeObjectURL(a.href),1000);}
async function importFile(file){
 if(!file||typeof file.text!=='function'||file.size>MAX_IMPORT_BYTES)throw new Error('File non valido o troppo grande.');
 const text=await file.text();
 if(enc.encode(text).length>MAX_IMPORT_BYTES)throw new Error('File troppo grande.');
 const raw=JSON.parse(text);
 if(!Array.isArray(raw)&&(!raw||typeof raw!=='object'||raw.schema&&raw.schema!=='R3_MEMORY_LEDGER_V1'))throw new Error('Formato non valido.');
 const incoming=Array.isArray(raw)?raw:raw.events;
 const check=await verifyLedger(incoming);
 if(!check.ok)throw new Error('Import non valido ('+check.reason+'): memoria precedente intatta.');
 return withWriteLock(async()=>{
  const before=localStorage.getItem(KEY),current=load(),existing=await verifyLedger(current);
  if(!existing.ok)throw new Error('Catena locale non valida: ripristino manuale necessario, nessun dato sovrascritto.');
  // V1 is a linear chain. Only a matching prefix/extension is mergeable without
  // changing history. Independent roots/forks must remain separate exports.
  for(let i=0;i<Math.min(current.length,incoming.length);i++){
   if(current[i].hash!==incoming[i].hash||stable(current[i])!==stable(incoming[i]))
    throw new Error('Catene divergenti o indipendenti: import rifiutato senza modifiche. Conservare entrambi gli export.');
  }
  if(incoming.length>current.length)commitLedger(incoming,before);
  return Math.max(current.length,incoming.length);
 });
}
function nextAction(canon){const ledger=load();const counts={};ledger.forEach(e=>counts[e.priority]=(counts[e.priority]||0)+1);const open=(canon.priorities||[]).filter(p=>!/verificat|canonic/i.test(p.state));open.sort((a,b)=>(counts[a.id]||0)-(counts[b.id]||0));return open[0]||null;}

// R3_COLLATE_ALL ------------------------------------------------------------
const STOP=new Set('a ad al alla alle allo ai agli da dal dalla dalle di del della delle e ed o oppure che chi con come per tra fra su nel nella nello nei nelle un una uno il lo la i gli le si no non più meno molto anche già ancora essere avere questo questa questi queste quello quella ogni tutto tutti tutte quando dove perché poi solo soltanto'.split(' '));
function norm(s){return String(s||'').toLowerCase().normalize('NFD').replace(/[\u0300-\u036f]/g,'').replace(/[^a-z0-9à-ÿ∞³-]+/gi,' ').replace(/\s+/g,' ').trim();}
function tokens(s){return new Set(norm(s).split(' ').filter(x=>x.length>2&&!STOP.has(x)));}
function jaccard(a,b){const A=tokens(a),B=tokens(b);if(!A.size||!B.size)return 0;let inter=0;A.forEach(x=>{if(B.has(x))inter++});return inter/(A.size+B.size-inter);}
// Heuristics, not a truth classifier: negation has local scope, matches whole
// words/stems, and a candidate conflict can never simultaneously be a duplicate.
const NEG_WORD=/^(nessun[oa]?|mai|fallit[oaie]|error[ei]|assent[ei]|manca\w*|invalid[oaie]|fals[oaie]|spent[oaie]|impossibil[ei])$/;
const POS_WORD=/^(riuscit[oaie]|present[ei]|valid[oaie]|ver[oaie]|attiv[oaie]|funzion\w*|conferm\w*|integr[oaie]|complet[oaie]|acces[oaie]|possibil[ei])$/;
function polarity(s){
 const words=String(s||'').toLowerCase().normalize('NFC').match(/[\p{L}\p{N}]+/gu)||[];let score=0,negated=false,age=0;
 for(const raw of words){
  const word=norm(raw);
  if(['ma','pero','mentre','invece','e'].includes(word)&&raw!=='è'){negated=false;age=0;continue}
  if(word==='non'){negated=!negated;age=0;continue}
  const val=NEG_WORD.test(word)?-1:POS_WORD.test(word)?1:0;
  if(val){score+=negated?-val:val;negated=false;age=0}
  else if(++age>3)negated=false;
 }
 return Math.sign(score);
}
function relation(a,b){
 const textA=[a.claim,a.evidence,a.falsifier].join(' '),textB=[b.claim,b.evidence,b.falsifier].join(' ');
 const lexical=jaccard(textA,textB),claimSimilarity=jaccard(a.claim,b.claim);
 const samePriority=a.priority&&b.priority&&a.priority===b.priority?0.15:0;
 const sameState=a.state===b.state?0.05:0;
 const score=Math.min(1,lexical+samePriority+sameState),pa=polarity(a.claim),pb=polarity(b.claim);
 const stripNegation=s=>norm(s).split(' ').filter(w=>!['non','mai','nessun','nessuna','nessuno'].includes(w)).join(' ');
 const negationParity=s=>norm(s).split(' ').filter(w=>['non','mai','nessun','nessuna','nessuno'].includes(w)).length%2;
 const explicitNegation=negationParity(a.claim)!==negationParity(b.claim)&&stripNegation(a.claim)===stripNegation(b.claim);
 const conflict=claimSimilarity>=0.24&&(explicitNegation||pa!==0&&pb!==0&&pa!==pb);
 const duplicate=!conflict&&lexical>=0.78&&claimSimilarity>=0.78&&norm(a.claim)!==''&&norm(b.claim)!=='';
 return {score:+score.toFixed(3),lexical:+lexical.toFixed(3),duplicate,conflict};
}
const LEGACY_PRIORITIES={'memoria locale append-only':'R3-011','r3_collate_all':'R3-011','r3_collaborate':'R3-012','meta-scacchiera':'R3-012'};
function canonicalPriority(x,canon){
 const priorities=canon.priorities||[];
 const explicit=x.priority||x.priority_id;
 if(explicit)return priorities.some(p=>p.id===explicit)?explicit:null;
 const label=String(x.label||'').toLowerCase();
 const candidate=LEGACY_PRIORITIES[label]||priorities.find(p=>p.id===x.label||p.name&&norm(p.name)===norm(x.label))?.id;
 return priorities.some(p=>p.id===candidate)?candidate:null;
}
function canonicalEvents(canon){
 const ids=new Set();
 return (canon.current_evidence||[]).map(x=>{
  const id='CANON-'+encodeURIComponent(x.id||x.label);
  if(ids.has(id))throw new Error('Identità canonica duplicata: assegnare ID espliciti distinti.');
  ids.add(id);
  return {id,ts:canon.updated_at||new Date(0).toISOString(),state:STATES.has(x.state)?x.state:'IPOTESI',
   claim:x.label+': '+x.detail,evidence:'Dichiarazione del canone; non è una verifica indipendente.',
   falsifier:'Richiede evidenza più recente o prova contraria.',source:'/r3-evoluzione.json',
   priority:canonicalPriority(x,canon),hash:null,virtual:true};
 });
}
function collateAll(canon){const local=load();const entries=[...canonicalEvents(canon),...local];const links=[],dups=[],conflicts=[];for(let i=0;i<entries.length;i++)for(let j=i+1;j<entries.length;j++){const r=relation(entries[i],entries[j]);if(r.score>=0.30||r.conflict){const link={a:entries[i].id,b:entries[j].id,score:r.score,reason:r.conflict?'polarità opposta su contenuto simile':r.duplicate?'quasi duplicato':'sovrapposizione lessicale/tema'};links.push(link);if(r.duplicate)dups.push(link);if(r.conflict)conflicts.push(link);}}
 const parent=entries.map((_,i)=>i);const find=x=>parent[x]===x?x:(parent[x]=find(parent[x]));const union=(a,b)=>{a=find(a);b=find(b);if(a!==b)parent[b]=a};links.filter(l=>l.score>=0.38&&!l.reason.startsWith('polarità')).forEach(l=>{const a=entries.findIndex(e=>e.id===l.a),b=entries.findIndex(e=>e.id===l.b);if(a>=0&&b>=0)union(a,b)});const groups=new Map();entries.forEach((e,i)=>{const k=find(i);if(!groups.has(k))groups.set(k,[]);groups.get(k).push(e)});const clusters=[...groups.values()].filter(g=>g.length>1).map((g,i)=>({id:'CL-'+String(i+1).padStart(2,'0'),members:g.map(e=>e.id),priorities:[...new Set(g.map(e=>e.priority).filter(Boolean))],states:[...new Set(g.map(e=>e.state))],claims:g.map(e=>e.claim)}));return {schema:'R3_COLLATE_ALL_V1',generated_at:new Date().toISOString(),counts:{entries:entries.length,local:local.length,canonical:entries.length-local.length,links:links.length,duplicates:dups.length,conflicts:conflicts.length,clusters:clusters.length},entries,links:links.sort((a,b)=>b.score-a.score),duplicates:dups,conflicts,clusters};}

// R3_COLLABORATE -------------------------------------------------------------
function collaborate(collated,canon){const byId=new Map(collated.entries.map(e=>[e.id,e]));const proposals=[];collated.clusters.forEach(c=>{const members=c.members.map(id=>byId.get(id)).filter(Boolean);const facts=members.filter(e=>e.state==='FATTO');const hypotheses=members.filter(e=>e.state==='IPOTESI');const falsifiers=[...new Set(members.map(e=>e.falsifier).filter(Boolean))];const sources=[...new Set(members.map(e=>e.source).filter(Boolean))];const priority=c.priorities[0]||'NON_ASSEGNATA';let claim;if(facts.length>=2)claim=`Le evidenze del cluster ${c.id} convergono su ${priority}; verificare se la convergenza regge su un caso nuovo.`;else if(facts.length&&hypotheses.length)claim=`${priority}: esiste almeno un fatto collegato a un'ipotesi; il prossimo passo è testare l'ipotesi senza promuoverla automaticamente.`;else claim=`${priority}: più entrate descrivono lo stesso tema; serve una prova discriminante prima del consolidamento.`;proposals.push({cluster:c.id,priority,state:'INFERENZA',claim,evidence:`${members.length} entrate collegate; ${facts.length} FATTO; ${hypotheses.length} IPOTESI; fonti: ${sources.length}.`,test:falsifiers[0]||'Definire una prova indipendente che distingua le spiegazioni concorrenti.',source_ids:c.members});});
 collated.conflicts.forEach((x,i)=>{proposals.push({cluster:'CONFLICT-'+(i+1),priority:(byId.get(x.a)||{}).priority||'NON_ASSEGNATA',state:'INFERENZA',claim:'Conflitto candidato: due entrate lessicalmente vicine differiscono per negazione o polarità.',evidence:`${x.a} ↔ ${x.b}; similarità ${x.score}.`,test:'Rileggere provenienza e data; conservare entrambe finché una prova non risolve il conflitto.',source_ids:[x.a,x.b]});});
 const priorityOrder=(canon.priorities||[]).map(x=>x.id);proposals.sort((a,b)=>{const ia=priorityOrder.indexOf(a.priority),ib=priorityOrder.indexOf(b.priority);return (ia<0?999:ia)-(ib<0?999:ib)});return {schema:'R3_COLLABORATE_V1',generated_at:new Date().toISOString(),source_schema:collated.schema,proposals,rule:'Le proposte sono INFERENZE: non modificano il canone e richiedono test.'};}
function saveReport(report){localStorage.setItem(REPORT,JSON.stringify(report));}
function exportReport(report){const blob=new Blob([JSON.stringify(report,null,2)],{type:'application/json'});const a=document.createElement('a');a.href=URL.createObjectURL(blob);a.download='R3_COLLABORATION_'+new Date().toISOString().replace(/[:.]/g,'-')+'.json';a.click();setTimeout(()=>URL.revokeObjectURL(a.href),1000);}
function ensureCollabUI(){if(document.getElementById('r3-collab-panel'))return;const anchor=document.getElementById('r3-ledger-list')||document.querySelector('.priority-list');if(!anchor)return;const s=document.createElement('section');s.id='r3-collab-panel';s.innerHTML=`<p class="kicker">R3_COLLATE_ALL → R3_COLLABORATE</p><h2>Le memorie lavorano tra loro.</h2><p class="intro">Il motore collega entrate simili, segnala duplicati e conflitti, costruisce cluster e produce inferenze candidate. Nessuna inferenza viene promossa automaticamente a FATTO.</p><div class="toolbar"><button class="button" id="r3-collate-run" type="button">Esegui collaborazione</button><button class="button secondary" id="r3-collate-export" type="button">Esporta rapporto</button></div><div id="r3-collate-status" class="statusline">Pronto.</div><div id="r3-collate-results" class="evidence" style="margin-top:1rem"></div>`;anchor.parentNode.insertBefore(s,anchor.nextSibling);}
function renderCollab(report){const status=document.getElementById('r3-collate-status'),box=document.getElementById('r3-collate-results');if(status)status.textContent=`Analizzate ${report.collate.counts.entries} entrate · ${report.collate.counts.links} relazioni · ${report.collate.counts.duplicates} duplicati · ${report.collate.counts.conflicts} conflitti · ${report.collaborate.proposals.length} inferenze candidate.`;if(!box)return;box.innerHTML='';report.collaborate.proposals.slice(0,12).forEach(p=>{const a=document.createElement('article');a.innerHTML=`<span class="tag inferenza">INFERENZA</span><h3>${esc(p.priority)} · ${esc(p.cluster)}</h3><p>${esc(p.claim)}</p><p><strong>Evidenza:</strong> ${esc(p.evidence)}</p><p><strong>Prova richiesta:</strong> ${esc(p.test)}</p>`;box.appendChild(a)});if(!report.collaborate.proposals.length)box.innerHTML='<p class="muted">Nessun cluster sufficiente: servono più entrate collegate.</p>';}
function executeCollaboration(canon=activeCanon){
 const collate=collateAll(canon),coop=collaborate(collate,canon);
 const status=canon===activeCanon?canonStatus:{state:'supplied',error:null};
 const warnings=[];
 if(!['loaded','supplied'].includes(status.state))warnings.push(status.error||'Canone non disponibile.');
 const unmapped=collate.entries.filter(e=>e.virtual&&!e.priority).map(e=>e.id);
 if(unmapped.length)warnings.push('Alcune evidenze canoniche non hanno una priorità esplicita valida.');
 const report={schema:'R3_MEMORY_COOP_V1',engine_version:VERSION,generated_at:new Date().toISOString(),
  incomplete:!['loaded','supplied'].includes(status.state),warnings,
  sources:{canonical:{...status,unmapped_ids:unmapped},local:{scope:'this-browser-origin',count:collate.counts.local}},
  collate,collaborate:coop};
 latest=report;
 try{saveReport(report)}catch{report.warnings.push('Rapporto non salvato: spazio locale insufficiente o storage non disponibile.')}
 renderCollab(report);
 const line=document.getElementById('r3-collate-status');
 if(line&&report.incomplete)line.textContent='ANALISI PARZIALE — canone non caricato. '+line.textContent;
 return report;
}
function showError(error){
 latest=null;
 const message=error?.message||'Operazione non completata.';
 const status=document.getElementById('r3-collate-status');
 if(status)status.textContent='ATTENZIONE — '+message;
 const results=document.getElementById('r3-collate-results');if(results)results.innerHTML='';
}
async function refresh(){
 const v=await verify(),integrity=document.getElementById('r3-integrity');
 if(integrity)integrity.textContent=v.ok?`Catena locale integra · ${v.count} eventi`:`ATTENZIONE · catena non valida (${v.reason})`;
 if(!v.ok)throw new Error('Ledger non valido: analisi sospesa; esportare i dati prima di un ripristino.');
 render();
 const next=nextAction(activeCanon),box=document.getElementById('r3-next-action');
 if(box&&next)box.innerHTML=`<strong>${esc(next.id)} · ${esc(next.name)}</strong><span>${esc(next.why)}</span>`;
 return executeCollaboration(activeCanon);
}
async function reloadCanon(){
 try{
  const response=await fetch('/r3-evoluzione.json',{cache:'no-store'});
  if(!response.ok)throw new Error('Canone non caricato: HTTP '+response.status+'.');
  const candidate=await response.json();
  if(!candidate||!Array.isArray(candidate.priorities)||!Array.isArray(candidate.current_evidence)||
   candidate.priorities.some(p=>!p||typeof p.id!=='string')||
   candidate.current_evidence.some(e=>!e||typeof e.label!=='string'||typeof e.detail!=='string'))
   throw new Error('Struttura del canone non valida.');
  canonicalEvents(candidate); // Reject ambiguous identifiers before accepting the source.
  activeCanon=candidate;canonStatus={state:'loaded',error:null};
 }catch{
  activeCanon={priorities:[],current_evidence:[]};
  canonStatus={state:'unavailable',error:'Canone non caricato: verificare accesso, rete e formato. Analisi limitata al ledger locale.'};
 }
}
async function init(){
 ensureCollabUI();
 const form=document.getElementById('r3-memory-form');
 if(form)form.addEventListener('submit',async ev=>{
  ev.preventDefault();let saved=false;
  try{
   const fd=new FormData(form);
   await append({state:fd.get('state'),claim:fd.get('claim'),evidence:fd.get('evidence'),falsifier:fd.get('falsifier'),source:fd.get('source'),priority:fd.get('priority')});
   saved=true;form.reset();form.elements.state.value='FATTO';form.elements.priority.value='R3-019';await refresh();
  }catch(e){showError(e);alert((saved?'Memoria salvata, ma aggiornamento del rapporto fallito: ':'Memoria non salvata: ')+e.message)}
 });
 const ex=document.getElementById('r3-export');
 if(ex)ex.addEventListener('click',()=>{try{download()}catch{const raw=localStorage.getItem(KEY);const a=document.createElement('a');a.href=URL.createObjectURL(new Blob([raw??''],{type:'text/plain'}));a.download='R3_MEMORY_RAW_RECOVERY.txt';a.click();setTimeout(()=>URL.revokeObjectURL(a.href),1000)}});
 const imp=document.getElementById('r3-import');
 if(imp)imp.addEventListener('change',async()=>{
  if(!imp.files[0])return;let count=null;
  try{count=await importFile(imp.files[0]);await refresh();alert('Import completato: '+count+' eventi')}
  catch(e){showError(e);alert((count===null?'Import rifiutato senza modifiche: ':'Import salvato, aggiornamento del rapporto fallito: ')+e.message)}
  finally{imp.value=''}
 });
 const run=document.getElementById('r3-collate-run');
 if(run)run.addEventListener('click',async()=>{try{await reloadCanon();await refresh()}catch(e){showError(e)}});
 const exportButton=document.getElementById('r3-collate-export');
 if(exportButton)exportButton.addEventListener('click',async()=>{try{exportReport(await refresh())}catch(e){showError(e)}});
 if(globalThis.addEventListener)globalThis.addEventListener('storage',async e=>{
  if(e.key===KEY||e.key===null){try{await refresh()}catch(error){showError(error)}}
 });
 await reloadCanon();
 try{await refresh()}catch(e){showError(e)}
 if(!globalThis.navigator?.locks?.request){
  const status=document.getElementById('r3-collate-status');
  if(status)status.textContent+=' · SOLA LETTURA: Web Locks non disponibile.';
 }
}
window.R3Memory={version:VERSION,load,append,verify,collateAll,collaborate,executeCollaboration,importFile};
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',init);else init();
})();
