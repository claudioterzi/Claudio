/* Raffaello Data Hub — indice locale e grafo dati privato.
   Claudio Terzi · C.Terzi
   Legge le sorgenti esistenti senza riscriverle. Nessuna sincronizzazione server implicita. */
(function(){
'use strict';
if(window.RaffaelloDataHub)return;

const INDEX_KEY='claudio.raffaello.datahub.index.v1';
const PRIVATE_SESSION_KEY='raffaello.private.session.v1';
const enc=new TextEncoder();
let latest=null;
let parsedByKey=new Map();

const STATIC_SOURCES=[
  {path:'/atmosfere-disponibili.json',label:'Atmosfere disponibili',area:'Esperienza'},
  {path:'/esperienze-olfattive.json',label:'Esperienze olfattive',area:'Profumi'},
  {path:'/organo-evoluzione.json',label:'Organo · evoluzione',area:'Profumi'},
  {path:'/r3-evoluzione.json',label:'Canone R³∞',area:'R³∞'}
];
const STRUCTURAL_SOURCES=[
  {path:'/formule/',label:'Archivio formule',area:'Profumi',state:'PRESENT_IN_REPO_NOT_ENUMERATED'}
];
const EXPLICIT_EDGES=[
  ['claudio.fabbrica.talent.intent.v1','claudio.talenti.requests.v1','Fabbrica ↔ richieste della Bottega'],
  ['claudio.fabbrica.talent.intent.v1','claudio.talenti.profile.v1','Fabbrica ↔ profilo talento'],
  ['claudio.talenti.supply-intent.v1','claudio.talenti.requests.v1','Servizio → preparazione filiera'],
  ['claudio.travel.intent.v1','claudio.flight.hunter.verified.v1','Intento viaggio → prezzi verificati'],
  ['claudio.orchestrator.live-proof.v1','claudio.orchestrator.audit.v1','Claim/prova → audit'],
  ['claudio.orchestrator.economy.v1','claudio.orchestrator.value-waterfall.v1','Economia rete → distribuzione valore'],
  ['claudio.orchestrator.live-service.v1','claudio.orchestrator.live-opportunities.v1','Regia live → opportunità'],
  ['claudio.orchestrator.live-opportunities.v1','claudio.orchestrator.memorability.v1','Opportunità → memorabilità'],
  ['claudio.orchestrator.memorability.v1','claudio.orchestrator.extra-budget.v1','Memorabilità → budget extra'],
  ['r3.memory.ledger.v1','r3.memory.meta.v1','Ledger → metadati memoria'],
  ['r3.memory.ledger.v1','r3.memory.collate.latest.v1','Ledger → collazione'],
  ['r3.memory.ledger.v1','/r3-evoluzione.json','Memoria locale → canone R³∞']
];
const FACET_FIELDS=new Set(['service','area','place','city','title','priority','status','producer','mode','from','to','date','ret']);

function privateOK(){try{return sessionStorage.getItem(PRIVATE_SESSION_KEY)==='1'}catch{return false}}
function sensitiveKey(k){
  const s=String(k||'').toLowerCase();
  return k===INDEX_KEY || /(^|[._-])(password|passwd|secret|token|auth|credential|session)([._-]|$)/i.test(s) ||
    s.startsWith('raffaello.public.code.') || s.startsWith('raffaello.public.id.') ||
    s.startsWith('raffaello.private.') || s.startsWith('raffaello.access.');
}
function classify(key){
  const k=String(key).toLowerCase();
  if(k.startsWith('r3.')||k.includes('r3'))return 'R³∞';
  if(k.includes('fabbrica'))return 'Fabbrica';
  if(k.includes('talenti'))return 'Bottega';
  if(k.includes('flight')||k.includes('travel')||k.includes('viaggi'))return 'Viaggi';
  if(k.includes('orchestrator')){
    if(k.includes('audit')||k.includes('proof'))return 'Fiducia';
    if(k.includes('economy')||k.includes('value'))return 'Economia';
    return 'Regia';
  }
  if(k.includes('parfum')||k.includes('perfume')||k.includes('organo')||k.includes('olfatt')||k.includes('formula'))return 'Profumi';
  if(k.includes('opera')||k.includes('musica')||k.includes('taroc')||k.includes('alpha'))return 'Creazioni';
  return 'Sistema';
}
function parseRaw(raw){try{return {ok:true,value:JSON.parse(raw),type:'json'}}catch{return {ok:true,value:raw,type:'text'}}}
function itemCount(v){if(Array.isArray(v))return v.length;if(v&&typeof v==='object')return Object.keys(v).length;return v==null?0:1}
function findTimestamp(v){
  if(!v||typeof v!=='object')return null;
  for(const k of ['updated_at','created_at','exported_at','at','ts']){
    const x=v[k]; if(typeof x==='string'&&!Number.isNaN(Date.parse(x)))return x;
  }
  if(Array.isArray(v)){
    const times=v.slice(-50).map(findTimestamp).filter(Boolean).map(x=>Date.parse(x)).filter(Number.isFinite);
    if(times.length)return new Date(Math.max(...times)).toISOString();
  }
  return null;
}
function collectFacets(v,out,depth){
  if(depth>2||v==null)return out;
  if(Array.isArray(v)){v.slice(0,50).forEach(x=>collectFacets(x,out,depth+1));return out}
  if(typeof v!=='object')return out;
  Object.entries(v).forEach(([k,val])=>{
    const lk=k.toLowerCase();
    if(FACET_FIELDS.has(lk)&&(typeof val==='string'||typeof val==='number')){
      const text=String(val).trim().toLowerCase();
      if(text&&text.length<=160){if(!out[lk])out[lk]=new Set();out[lk].add(text)}
    }
    if(depth<2&&val&&typeof val==='object')collectFacets(val,out,depth+1);
  });
  return out;
}
function localDatasets(){
  parsedByKey=new Map();
  const nodes=[];
  let keys=[];
  try{keys=Object.keys(localStorage)}catch(e){return {nodes,errors:['localStorage non accessibile: '+e.message]}}
  const errors=[];
  keys.sort().forEach(key=>{
    if(sensitiveKey(key))return;
    let raw='';try{raw=localStorage.getItem(key)}catch(e){errors.push(key+': '+e.message);return}
    if(raw==null)return;
    const p=parseRaw(raw); parsedByKey.set(key,p.value);
    nodes.push({
      id:'storage:'+key,source:'localStorage',key,label:key,area:classify(key),type:p.type,
      bytes:enc.encode(raw).length,items:itemCount(p.value),timestamp:findTimestamp(p.value),
      facets:collectFacets(p.value,{},0),state:'PRESENTE'
    });
  });
  return {nodes,errors};
}
async function staticDatasets(){
  if(!/^\/dati(?:\.html)?\/?$/.test(location.pathname))return [];
  return Promise.all(STATIC_SOURCES.map(async s=>{
    try{
      const r=await fetch(s.path,{cache:'no-store'});if(!r.ok)throw new Error('HTTP '+r.status);
      const text=await r.text();let value;try{value=JSON.parse(text)}catch{value=text}
      return {id:'static:'+s.path,source:'static',key:s.path,label:s.label,area:s.area,type:typeof value==='string'?'text':'json',bytes:enc.encode(text).length,items:itemCount(value),timestamp:findTimestamp(value),facets:collectFacets(value,{},0),state:'PRESENTE'};
    }catch(e){return {id:'static:'+s.path,source:'static',key:s.path,label:s.label,area:s.area,type:'unknown',bytes:0,items:0,timestamp:null,facets:{},state:'ERRORE',error:e.message}}
  }));
}
function hasNode(nodes,key){return nodes.some(n=>n.key===key)}
function explicitRelations(nodes){
  const rel=[];
  EXPLICIT_EDGES.forEach(([a,b,label])=>{
    if(hasNode(nodes,a)&&hasNode(nodes,b))rel.push({from:a,to:b,label,state:'FATTO',basis:'collegamento esplicito già definito nel sistema'});
  });
  return rel;
}
function sharedFacet(a,b){
  const common=[];
  for(const field of FACET_FIELDS){
    const A=a.facets?.[field],B=b.facets?.[field];if(!A||!B)continue;
    let hit=false;A.forEach(v=>{if(B.has(v))hit=true});if(hit)common.push(field);
  }
  return common;
}
function inferredRelations(nodes,existing){
  const seen=new Set(existing.map(r=>[r.from,r.to].sort().join('|'))),rel=[];
  const candidates=nodes.filter(n=>n.source==='localStorage');
  for(let i=0;i<candidates.length;i++)for(let j=i+1;j<candidates.length;j++){
    const a=candidates[i],b=candidates[j];if(a.area===b.area&&a.key===b.key)continue;
    const fields=sharedFacet(a,b);if(!fields.length)continue;
    const pair=[a.key,b.key].sort().join('|');if(seen.has(pair))continue;
    seen.add(pair);rel.push({from:a.key,to:b.key,label:'Possibile relazione per campi condivisi: '+fields.join(', '),state:'INFERENZA',basis:'euristica locale; da confermare'});
  }
  return rel.slice(0,80);
}
function compactNode(n){return {id:n.id,source:n.source,key:n.key,label:n.label,area:n.area,type:n.type,bytes:n.bytes,items:n.items,timestamp:n.timestamp,state:n.state,error:n.error||null}}
function saveIndex(snapshot){
  try{localStorage.setItem(INDEX_KEY,JSON.stringify({schema:snapshot.schema,generated_at:snapshot.generated_at,datasets:snapshot.datasets.map(compactNode),relations:snapshot.relations,structural:snapshot.structural,errors:snapshot.errors}))}catch(e){snapshot.errors.push('Indice non salvato: '+e.message)}
}
async function refresh(){
  if(!privateOK())throw new Error('Data Hub disponibile solo nella sessione proprietario.');
  const local=localDatasets();const statics=await staticDatasets();const nodes=[...local.nodes,...statics];
  const explicit=explicitRelations(nodes),inferred=inferredRelations(nodes,explicit);
  latest={schema:'RAFFAELLO_DATA_HUB_V1',generated_at:new Date().toISOString(),scope:'browser-locale + sorgenti statiche note',datasets:nodes.map(compactNode),relations:[...explicit,...inferred],structural:STRUCTURAL_SOURCES,errors:[...local.errors,...statics.filter(x=>x.error).map(x=>x.key+': '+x.error)]};
  saveIndex(latest);
  window.dispatchEvent(new CustomEvent('raffaello:datahub:refreshed',{detail:latest}));
  return latest;
}
function snapshot(){return latest?JSON.parse(JSON.stringify(latest)):null}
function read(key){
  if(!privateOK())throw new Error('Sessione proprietario richiesta.');
  if(sensitiveKey(key))throw new Error('Sorgente esclusa dal Data Hub per sicurezza.');
  if(parsedByKey.has(key))return parsedByKey.get(key);
  const raw=localStorage.getItem(key);if(raw==null)return null;const p=parseRaw(raw);parsedByKey.set(key,p.value);return p.value;
}
function exportSnapshot(){
  if(!latest)throw new Error('Aggiorna prima il Data Hub.');
  const blob=new Blob([JSON.stringify(latest,null,2)],{type:'application/json'});const a=document.createElement('a');a.href=URL.createObjectURL(blob);a.download='RAFFAELLO_DATA_HUB_'+new Date().toISOString().slice(0,10)+'.json';a.click();setTimeout(()=>URL.revokeObjectURL(a.href),1000);
}
window.RaffaelloDataHub={refresh,snapshot,read,export:exportSnapshot,version:'1.0.0'};

/* Sulle pagine private ordinarie aggiorna solo l'indice locale; /dati carica anche i JSON statici. */
if(privateOK())refresh().catch(()=>{});
})();
