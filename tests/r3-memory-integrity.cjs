'use strict';
// Audit offline del sorgente reale, senza servizi esterni né memorie dell'utente.
// Eseguire: node tests/r3-memory-integrity.cjs [percorso/r3-memory.js]
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const {webcrypto, createHash} = require('node:crypto');
const sourcePath = process.argv[2] || path.join(__dirname, '../public/r3-memory.js');
const bytes = fs.readFileSync(sourcePath);
const blobSHA = createHash('sha1').update(`blob ${bytes.length}\0`).update(bytes).digest('hex');
// Record the actual source hash; do not change production code to pass tests.
const KEY='r3.memory.ledger.v1', REPORT='r3.memory.collate.latest.v1';
const blankCanon={priorities:[],current_evidence:[]};
const input=(claim,overrides={})=>({state:'FATTO',claim,evidence:'',falsifier:'',source:'audit-sintetico',priority:'R3-019',...overrides});
function sharedState(initial={}){
 const store=new Map(Object.entries(initial)), queues=new Map();
 const locks={request(name,options,callback){
  if(typeof options==='function')callback=options;
  const result=(queues.get(name)||Promise.resolve()).then(()=>callback({name,mode:'exclusive'}));
  queues.set(name,result.catch(()=>{}));return result;
 }};
 return {store,locks};
}
function env(canon=blankCanon, initial={}, fetchError=false, options={}){
  const shared=options.shared||sharedState(initial);
  const store=shared.store, hooks={}, elements={}, downloads=[], alerts=[];
  for(const id of ['r3-memory-form','r3-integrity','r3-import','r3-export','r3-collate-run','r3-collate-export','r3-collab-panel','r3-collate-status']){
    elements[id]={handlers:{},addEventListener(name,fn){this.handlers[name]=fn;},files:[],value:'',textContent:''};
  }
  elements['r3-memory-form'].elements={state:{value:'FATTO'},priority:{value:'R3-019'}};
  elements['r3-memory-form'].reset=function(){};
  const context={TextEncoder,crypto:webcrypto,Blob,console,Date,Math,JSON,Uint8Array,
    navigator:options.noLocks?{}:{locks:shared.locks},
    localStorage:{getItem:k=>store.get(k)??null,setItem:(k,v)=>{if(k===options.failKey)throw new Error('QuotaExceededError');store.set(k,String(v));},removeItem:k=>store.delete(k)},
    document:{readyState:'loading',getElementById:id=>elements[id]||null,querySelector:()=>null,
      addEventListener:(type,fn)=>hooks[type]=fn,
      createElement:()=>({click(){},appendChild(){},innerHTML:'',className:''})},
    fetch:async()=>{if(fetchError)throw new Error('Canone non raggiungibile');return {ok:!options.status||options.status<400,status:options.status||200,json:async()=>JSON.parse(JSON.stringify(canon))};},
    FormData:class{constructor(f){this.values=f.testValues;}get(k){return this.values[k];}},
    URL:{createObjectURL:blob=>{downloads.push(blob);return 'blob:audit';},revokeObjectURL(){}},
    alert:x=>alerts.push(String(x)),setTimeout:()=>0};
  context.window=context;vm.createContext(context);vm.runInContext(bytes.toString(),context);
  return {api:context.R3Memory,store,elements,downloads,alerts,init:()=>hooks.DOMContentLoaded(),context,options};
}
const results=[];
async function check(id, requirement, fn){
  try{const observed=await fn();results.push({id,requirement,...observed});}
  catch(e){results.push({id,requirement,passed:false,test_error:e.stack});}
}
(async()=>{
await check('T01','Aggiunte sequenziali conservate con catena SHA-256 valida',async()=>{
 const e=env();await e.api.append(input('Evento iniziale'));await e.api.append(input('Secondo evento'));
 const v=await e.api.verify();return {passed:v.ok&&v.count===2,verification:v};
});
await check('T02','Collazione conserva tutte le entrate e non modifica il ledger',async()=>{
 const e=env();await e.api.append(input('Memoria condivisa del server verificata'));await e.api.append(input('Memoria condivisa del server verificata'));
 const before=e.store.get(KEY),r=e.api.collateAll(blankCanon);
 return {passed:r.counts.entries===2&&r.counts.duplicates===1&&before===e.store.get(KEY),counts:r.counts};
});
await check('T03','Collaborazione produce solo INFERENZA con fonti e prova, senza promozione',async()=>{
 const e=env();await e.api.append(input('Memoria condivisa del server verificata',{falsifier:'Nuovo test indipendente fallisce'}));await e.api.append(input('Memoria condivisa del server verificata',{state:'IPOTESI'}));
 const before=e.store.get(KEY),c=e.api.collateAll(blankCanon),r=e.api.collaborate(c,blankCanon);
 return {passed:r.proposals.length>0&&r.proposals.every(p=>p.state==='INFERENZA'&&p.source_ids.length>=2&&p.test)&&before===e.store.get(KEY),proposals:r.proposals};
});
await check('T04','Il server è attivo / Il server non è attivo segnalati come conflitto candidato',async()=>{
 const e=env();await e.api.append(input('Il server è attivo'));await e.api.append(input('Il server non è attivo'));
 const r=e.api.collateAll(blankCanon);return {passed:r.counts.conflicts===1,claims:r.entries.map(x=>x.claim),counts:r.counts,links:r.links};
});
await check('T05','Import rifiutato lascia invariata la memoria precedente',async()=>{
 const e=env();await e.init();await e.api.append(input('Ricordo originale valido'));const before=e.store.get(KEY);
 const altered=JSON.parse(before)[0];altered.claim='Testo alterato ma hash originale';
 e.elements['r3-import'].files=[{text:async()=>JSON.stringify({events:[altered]})}];
 await e.elements['r3-import'].handlers.change();const v=await e.api.verify();
 return {passed:before===e.store.get(KEY)&&v.ok,import_alerts:e.alerts,memory_unchanged:before===e.store.get(KEY),verification:v,stored_claim:e.api.load()[0].claim};
});
await check('T06','Rapporto esportato aggiornato dopo aggiunta tramite form',async()=>{
 const e=env();await e.init();e.elements['r3-memory-form'].testValues=input('Nuova memoria tramite form');
 await e.elements['r3-memory-form'].handlers.submit({preventDefault(){}});
 const live=JSON.parse(e.store.get(REPORT));await e.elements['r3-collate-export'].handlers.click();const exported=JSON.parse(await e.downloads.at(-1).text());
 return {passed:live.collate.counts.local===1&&exported.collate.counts.local===1,current_local:live.collate.counts.local,exported_local:exported.collate.counts.local};
});
await check('T07','Due aggiunte concorrenti non perdono eventi',async()=>{
 const e=env();await Promise.all([e.api.append(input('Primo evento concorrente')),e.api.append(input('Secondo evento concorrente'))]);
 return {passed:e.api.load().length===2,expected_count:2,actual_count:e.api.load().length,verification:await e.api.verify()};
});
await check('T08','Assegnazione priorità canoniche indipendente dall’ordine delle righe',async()=>{
 // Fixture minimale tratta dalle priorità e dalle etichette effettivamente presenti nel canone.
 const canon={priorities:[{id:'R3-019'},{id:'R3-011'},{id:'R3-012'},{id:'R3-013'},{id:'R3-016'}],current_evidence:[
  {label:'Memoria locale append-only',state:'FATTO',detail:''},{label:'R3_COLLATE_ALL',state:'FATTO',detail:''},
  {label:'R3_COLLABORATE',state:'FATTO',detail:''},{label:'Persistenza cross-device',state:'IPOTESI',detail:''},
  {label:'Meta-Scacchiera',state:'FATTO',detail:''}]};
 const r=env().api.collateAll(canon);const mapped=r.entries.find(x=>x.claim.startsWith('Meta-Scacchiera:'));
 return {passed:mapped.priority==='R3-012',expected_priority:'R3-012',observed_priority:mapped.priority,fixture:'minimal canonical labels and priority order, not full canonical document'};
});
await check('T09','Avvio della dashboard produce automaticamente un rapporto',async()=>{
 const e=env();await e.init();return {passed:!!e.store.get(REPORT),report_schema:JSON.parse(e.store.get(REPORT)).schema};
});
await check('T10','Errore nel caricamento del canone segnalato nel rapporto',async()=>{
 const e=env(blankCanon,{},true);await e.init();const report=JSON.parse(e.store.get(REPORT));
 const warned=report.incomplete===true&&report.sources.canonical.state==='unavailable'&&report.warnings.length>0;
 return {passed:warned,canonical_count:report.collate.counts.canonical,report_has_failure_indicator:warned,ui_status:e.elements['r3-collate-status'].textContent};
});

await check('T11','Import di una estensione valida preserva byte e hash dei record precedenti',async()=>{
 const a=env(),b=env();await a.api.append(input('Radice valida'));const prefix=a.store.get(KEY);
 await b.api.importFile({text:async()=>JSON.stringify({schema:'R3_MEMORY_LEDGER_V1',events:a.api.load()})});
 await b.api.append(input('Estensione valida'));
 await a.api.importFile({text:async()=>JSON.stringify({events:b.api.load()})});
 return {passed:(await a.api.verify()).ok&&a.api.load().length===2&&JSON.stringify(a.api.load().slice(0,1))===prefix};
});
await check('T12','Import di catena indipendente è rifiutato senza perdita',async()=>{
 const a=env(),b=env();await a.api.append(input('Radice A'));await b.api.append(input('Radice B'));const before=a.store.get(KEY);let rejected=false;
 try{await a.api.importFile({text:async()=>JSON.stringify({events:b.api.load()})})}catch{rejected=true}
 return {passed:rejected&&a.store.get(KEY)===before&&(await a.api.verify()).ok};
});
await check('T13','Import di un ramo divergente è rifiutato senza riscrivere cronologia',async()=>{
 const a=env(),b=env();await a.api.append(input('Radice comune'));
 await b.api.importFile({text:async()=>JSON.stringify({events:a.api.load()})});
 await a.api.append(input('Ramo A'));await b.api.append(input('Ramo B'));const before=a.store.get(KEY);let rejected=false;
 try{await a.api.importFile({text:async()=>JSON.stringify({events:b.api.load()})})}catch{rejected=true}
 return {passed:rejected&&a.store.get(KEY)===before};
});
await check('T14','Import ripetuto o prefisso più vecchio è idempotente',async()=>{
 const e=env();await e.api.append(input('Radice'));const older=e.api.load();await e.api.append(input('Nuovo evento'));
 const before=e.store.get(KEY);await e.api.importFile({text:async()=>JSON.stringify({events:e.api.load()})});
 await e.api.importFile({text:async()=>JSON.stringify({events:older})});return {passed:e.store.get(KEY)===before};
});
await check('T15','Cinquanta scritture da due contesti condivisi conservano tutto',async()=>{
 const shared=sharedState(),a=env(blankCanon,{},false,{shared}),b=env(blankCanon,{},false,{shared});
 await Promise.all(Array.from({length:50},(_,i)=>(i%2?a:b).api.append(input('Evento concorrente '+i))));
 const v=await a.api.verify();return {passed:v.ok&&v.count===50,count:v.count,unique_claims:new Set(a.api.load().map(e=>e.claim)).size};
});
await check('T16','JSON locale danneggiato non viene trattato come memoria vuota',async()=>{
 const e=env(blankCanon,{[KEY]:'{broken'});let rejected=false;
 try{await e.api.append(input('Non sovrascrivere'))}catch{rejected=true}
 return {passed:rejected&&e.store.get(KEY)==='{broken'&&!(await e.api.verify()).ok};
});
await check('T17','Quota esaurita conserva la memoria precedente',async()=>{
 const e=env();await e.api.append(input('Prima'));const before=e.store.get(KEY);e.options.failKey=KEY;let rejected=false;
 try{await e.api.append(input('Non salvabile'))}catch{rejected=true}
 return {passed:rejected&&before===e.store.get(KEY)&&(await e.api.verify()).ok};
});
await check('T18','Errore sui metadati non maschera una scrittura del ledger riuscita',async()=>{
 const e=env();e.options.failKey='r3.memory.meta.v1';await e.api.append(input('Dato salvato'));
 return {passed:e.api.load().length===1&&(await e.api.verify()).ok};
});
await check('T19','Senza Web Locks le scritture sono rifiutate e il ledger resta intatto',async()=>{
 const e=env(blankCanon,{},false,{noLocks:true});let rejected=false;
 try{await e.api.append(input('Non perdere dati'))}catch{rejected=true}
 return {passed:rejected&&!e.store.has(KEY)};
});
await check('T20','Stato sconosciuto non è accettato come FATTO',async()=>{
 const e=env();let rejected=false;
 try{await e.api.append(input('Stato errato',{state:'VERITA'}))}catch{rejected=true}
 return {passed:rejected&&!e.store.has(KEY)};
});
await check('T21','Priorità e identità canoniche stabili riordinando le liste',async()=>{
 const c={priorities:[{id:'R3-012',name:'Meta-Scacchiera'},{id:'R3-011'}],current_evidence:[
 {label:'Meta-Scacchiera',detail:'Prototipo',state:'FATTO'},{label:'R3_COLLATE_ALL',detail:'Prototipo',state:'FATTO'}]};
 const e=env(),a=e.api.collateAll(c).entries;
 c.priorities.reverse();c.current_evidence.reverse();const b=e.api.collateAll(c).entries;
 return {passed:a.every(x=>b.some(y=>x.id===y.id&&x.priority===y.priority&&x.claim===y.claim))};
});
await check('T22','Priorità sconosciuta e stato assente non diventano fatti o priorità arbitrarie',async()=>{
 const c={priorities:[{id:'R3-019'}],current_evidence:[{label:'Nuova voce',detail:'Da verificare',priority:'R3-999'}]};
 const x=env().api.collateAll(c).entries[0];return {passed:x.priority===null&&x.state==='IPOTESI'};
});
await check('T23','Conflitto non viene classificato anche come quasi duplicato',async()=>{
 const e=env();await e.api.append(input('Il server è attivo'));await e.api.append(input('Il server non è attivo'));
 const c=e.api.collateAll(blankCanon);return {passed:c.counts.conflicts===1&&c.counts.duplicates===0};
});
await check('T24','Sottostringhe invalido/valido e impossibile/possibile non si annullano',async()=>{
 const outcomes=[];
 for(const pair of [['Il collegamento è valido','Il collegamento è invalido'],['Il caricamento del registro è possibile','Il caricamento del registro è impossibile']]){
 const e=env();for(const claim of pair)await e.api.append(input(claim));outcomes.push(e.api.collateAll(blankCanon).counts.conflicts===1)}
 return {passed:outcomes.every(Boolean),cases:outcomes};
});
await check('T25','Rapporto esportato aggiornato anche dopo importazione',async()=>{
 const e=env(),other=env();await e.init();await other.api.append(input('Importato'));
 e.elements['r3-import'].files=[{text:async()=>JSON.stringify({events:other.api.load()})}];await e.elements['r3-import'].handlers.change();
 await e.elements['r3-collate-export'].handlers.click();const exported=JSON.parse(await e.downloads.at(-1).text());
 return {passed:exported.collate.counts.local===1&&(await e.api.verify()).ok};
});
await check('T26','Errore HTTP e schema canone errato producono analisi parziale esplicita',async()=>{
 const a=env(blankCanon,{},false,{status:403}),b=env({unexpected:true});await a.init();await b.init();
 return {passed:[a,b].every(e=>JSON.parse(e.store.get(REPORT)).incomplete===true)};
});
await check('T27','Canone caricato e vuoto non è confuso con canone indisponibile',async()=>{
 const e=env();await e.init();const r=JSON.parse(e.store.get(REPORT));return {passed:r.incomplete===false&&r.sources.canonical.state==='loaded'};
});
await check('T28','Validazione locale fallita sospende il rapporto automatico',async()=>{
 const e=env(blankCanon,{[KEY]:'[]'});await e.api.append(input('Valido'));const altered=e.api.load();altered[0].claim='Alterato';e.store.set(KEY,JSON.stringify(altered));
 await e.init();return {passed:!e.store.has(REPORT)&&e.elements['r3-collate-status'].textContent.includes('sospesa')};
});
await check('T29','Entrata mutata dal chiamante mentre attende non cambia il dato salvato',async()=>{
 const e=env(),data=input('Originale');const pending=e.api.append(data);data.claim='Modificata dopo chiamata';await pending;
 return {passed:e.api.load()[0].claim==='Originale'};
});
await check('T30','Catena V1 storica conservata senza migrazione o ricalcolo degli hash',async()=>{
 const e=env(),record={id:'R3E-old-id',ts:'2026-09-10T10:00:00.000Z',state:'FATTO',claim:'Evento sintetico storico',evidence:'',falsifier:'',source:'fixture',priority:'R3-019',previous_hash:null};
 record.hash=createHash('sha256').update(JSON.stringify(record)).digest('hex'); // hash only pre-hash fields in V1 order
 e.store.set(KEY,JSON.stringify([record]));await e.api.append(input('Evento nuovo'));
 return {passed:(await e.api.verify()).ok&&JSON.stringify(e.api.load()[0])===JSON.stringify(record)};
});
await check('T31','La copula è e un avverbio non cancellano la negazione',async()=>{
 const e=env();await e.api.append(input('Il server è attivo'));await e.api.append(input('Il server non è più attivo'));
 const c=e.api.collateAll(blankCanon);return {passed:c.counts.conflicts===1&&c.counts.duplicates===0};
});
await check('T32','Doppia negazione non genera da sola un conflitto',async()=>{
 const e=env();await e.api.append(input('Il server è attivo'));await e.api.append(input('Il server non non è attivo'));
 return {passed:e.api.collateAll(blankCanon).counts.conflicts===0};
});
const report={schema:'R3_MEMORY_REGRESSION_V1',project_author:'Claudio Terzi',signature:'C.Terzi',source:{path:'public/r3-memory.js',git_blob_sha:blobSHA},environment:{node:process.version,dom:'minimal event/document stubs; not a browser',localStorage:'isolated in-memory Map',locks:'shared simulated cooperative lock manager',fixtures:'synthetic only',network:'none'},scope:'Targeted regression checks, not a benchmark or production end-to-end test',total:results.length,passed:results.filter(x=>x.passed).length,failed:results.filter(x=>!x.passed).length,results};
const out=process.env.R3_TEST_OUTPUT||path.join(process.cwd(),'r3-test-results.json');
fs.writeFileSync(out,JSON.stringify(report,null,2)+'\n');
for(const x of results)console.log(`${x.passed?'PASS':'FAIL'} ${x.id} ${x.requirement}${x.passed?'':' '+JSON.stringify(x)}`);
console.log(`TOTAL ${report.total} PASS ${report.passed} FAIL ${report.failed}`);
if(report.failed)process.exitCode=1;
})().catch(e=>{console.error(e);process.exitCode=1;});
