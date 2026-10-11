/* Raffaello Data Hub V3 · Claudio Terzi · C.Terzi */
(function(){
'use strict';
const SESSION='raffaello.private.session.v1', INDEX='claudio.raffaello.datahub.index.v3', enc=new TextEncoder();
const SOURCES=[
['/r3-evoluzione.json','Canone R³∞','R³∞','CREME','json','current_evidence'],
['/formule/codici-400.json','Codici canonici dei 400 profumi','Profumi','CREME','json',''],
['/esperienze-olfattive.json','Esperienze olfattive','Profumi','CREME','json','entries'],
['/api/alpha','Canone Alpha','Creazioni','CREME','json',''],
['/api/mazzo','Mazzo Tarocchi R³∞','Creazioni','CREME','json',''],
['/musica-data.js','Archivio Musica','Creazioni','CREME','music','songs'],
['/organo-evoluzione.json','Organo · evoluzione','Profumi','ATTIVO','json','proposals'],
['/formule/organo-13aff1815ecef350.json','Organo formule','Profumi','ATTIVO','json',''],
['/api/viaggi/destinazioni','Catalogo destinazioni Viaggi','Viaggi','ATTIVO','json','destinazioni'],
['/atmosfere-disponibili.json','Atmosfere disponibili','Esperienza','SUPPORTO','json','']
];
const ARCHIVE=[
['/opera-viva-data.js','Opera Viva · asset visuale pesante','Creazioni','HEAVY_ASSET_NOT_AUTO_LOADED','Censito ma non caricato: contiene un grande blocco visuale.'],
['server:terzi:formula:*','Archivio formule personali','Profumi','PROTECTED','Record cliente/formula: accesso autenticato separato.'],
['server:terzi:fabbrica:v1:*','Copioni Fabbrica conservati','Fabbrica','SESSION_BOUND','Archivio di sessione: non enumerato dal browser.'],
['studio/parfums/organo_terzi_300.json','Organo Terzi 300 · sorgente','Profumi','SERVER_SIDE','Catalogo interno del compositore.'],
['studio/parfums/Organo_Terzi_300.xlsx','Organo Terzi 300 · foglio','Profumi','SOURCE_FILE','Sorgente di lavoro.'],
['studio/parfums/parfums_400.json','Archivio 400 profumi','Profumi','SERVER_SIDE','Dataset di generazione.'],
['studio/parfums/flaconi_400.json','Archivio flaconi 400','Profumi','SERVER_SIDE','Dataset visuale.'],
['studio/parfums/foto_400.json','Mappa foto 400','Profumi','SERVER_SIDE','Dataset di supporto.'],
['/atelier/archivio','Archivio privato Atelier','Profumi','AUTHENTICATED','Protetto da autenticazione/CSRF.'],
['/api/fabbrica/status','Stato Fabbrica','Fabbrica','STATEFUL_NOT_CALLED','GET stateful: escluso dall’indice.'],
['/api/atelier','Compositore Atelier','Profumi','AI_NOT_CALLED','Può avviare modelli IA: escluso dal refresh.'],
['/api/telegram/debug','Stato Telegram','Sistema','CONFIG_NOT_IMPORTED','Stato operativo, non conoscenza canonica.']
].map(x=>({path:x[0],label:x[1],area:x[2],state:x[3],reason:x[4],tier:'ARCHIVIO'}));
const EDGES=[
['r3.memory.ledger.v1','/r3-evoluzione.json','Memoria locale → canone R³∞'],
['/formule/codici-400.json','/formule/organo-13aff1815ecef350.json','Codici formule → organo'],
['/esperienze-olfattive.json','/formule/codici-400.json','Esperienze → formule canoniche'],
['/api/alpha','/api/mazzo','Alpha → mazzo operativo'],
['/api/mazzo','/r3-evoluzione.json','Tarocchi → canone R³∞'],
['claudio.travel.intent.v1','/api/viaggi/destinazioni','Intento viaggio → catalogo destinazioni']
];
const facetKeys=new Set(['title','nome','name','famiglia','family','paese','city','place','status','tags']);
let latest=null, parsed=new Map();
function ok(){try{return sessionStorage.getItem(SESSION)==='1'}catch{return false}}
function sensitive(k){const s=String(k||'').toLowerCase();return k===INDEX||/(^|[._-])(password|passwd|secret|token|auth|credential|session)([._-]|$)/i.test(s)||s.startsWith('raffaello.private.')||s.startsWith('raffaello.access.')||s.startsWith('raffaello.public.code.')||s.startsWith('raffaello.public.id.')}
function classify(k){k=String(k).toLowerCase();if(k.includes('r3'))return'R³∞';if(k.includes('parfum')||k.includes('organo')||k.includes('formula')||k.includes('olfatt'))return'Profumi';if(k.includes('flight')||k.includes('travel')||k.includes('viaggi'))return'Viaggi';if(k.includes('fabbrica'))return'Fabbrica';if(k.includes('talenti'))return'Bottega';if(k.includes('musica')||k.includes('opera')||k.includes('taroc')||k.includes('alpha'))return'Creazioni';return'Sistema'}
function path(v,p){return String(p||'').split('.').filter(Boolean).reduce((a,k)=>a==null?undefined:a[k],v)}
function count(v,p){const x=p?path(v,p):v;if(Array.isArray(x))return x.length;if(x&&typeof x==='object'){for(const k of ['entries','songs','destinazioni','items','records','proposals'])if(Array.isArray(x[k]))return x[k].length;return Object.keys(x).length}return x==null?0:1}
function stamp(v,d=0){if(!v||typeof v!=='object'||d>2)return null;for(const k of ['updated_at','created_at','checked_at','at','ts']){const x=v[k];if(typeof x==='string'&&!Number.isNaN(Date.parse(x)))return new Date(x).toISOString()}for(const x of Object.values(v).slice(0,40)){const t=stamp(x,d+1);if(t)return t}return null}
function facets(v,out={},d=0){if(!v||d>2)return out;if(Array.isArray(v)){v.slice(0,100).forEach(x=>facets(x,out,d+1));return out}if(typeof v!=='object')return out;for(const [k,val] of Object.entries(v)){const lk=k.toLowerCase();if(facetKeys.has(lk)){for(const z of (Array.isArray(val)?val:[val]))if(typeof z==='string'||typeof z==='number'){const t=String(z).trim().toLowerCase();if(t&&t.length<120){if(!out[lk])out[lk]=new Set();out[lk].add(t)}}}if(val&&typeof val==='object')facets(val,out,d+1)}return out}
function parse(text,kind){if(kind==='json')return JSON.parse(text);if(kind==='music'){const marker='window.TERZI_MUSICA =';const i=text.indexOf(marker);if(i<0)throw Error('formato Musica non riconosciuto');let p=text.slice(i+marker.length).trim();if(p.endsWith(';'))p=p.slice(0,-1);return JSON.parse(p)}return text}
function highlights(key,v){const a=[];if(key==='/r3-evoluzione.json'){if(v.version)a.push('versione '+v.version);if(v.status)a.push(v.status)}if(key==='/musica-data.js'){if(v.count!=null)a.push(v.count+' brani');if(v.textsVerified!=null)a.push(v.textsVerified+' testi verificati')}if(key==='/organo-evoluzione.json')a.push((v.proposals||[]).length+' proposte da testare');return a}
function local(){const out=[],errors=[];let keys=[];try{keys=Object.keys(localStorage)}catch(e){return{out,errors:['localStorage: '+e.message]}}for(const key of keys.sort()){if(sensitive(key))continue;try{const raw=localStorage.getItem(key);if(raw==null)continue;let v;try{v=JSON.parse(raw)}catch{v=raw}parsed.set(key,v);out.push({key,label:key,area:classify(key),tier:'LOCALE',source:'localStorage',type:typeof v==='string'?'text':'json',bytes:enc.encode(raw).length,items:count(v),timestamp:stamp(v),facets:facets(v),state:'PRESENTE',highlights:[]})}catch(e){errors.push(key+': '+e.message)}}return{out,errors}}
async function remote(){return Promise.all(SOURCES.map(async s=>{const [key,label,area,tier,kind,countPath]=s;try{const r=await fetch(key,{cache:'no-store',credentials:'same-origin'});if(!r.ok)throw Error('HTTP '+r.status);const text=await r.text(),v=parse(text,kind);parsed.set(key,v);return{key,label,area,tier,source:key.startsWith('/api/')?'server-api':'static',type:'json',bytes:enc.encode(text).length,items:count(v,countPath),timestamp:stamp(v),facets:facets(v),state:'PRESENTE',highlights:highlights(key,v)}}catch(e){return{key,label,area,tier,source:key.startsWith('/api/')?'server-api':'static',type:'unknown',bytes:0,items:0,timestamp:null,facets:{},state:'ERRORE',error:e.message,highlights:[]}}}))}
function has(nodes,k){return nodes.some(n=>n.key===k)}
function relations(nodes){const facts=EDGES.filter(e=>has(nodes,e[0])&&has(nodes,e[1])).map(e=>({from:e[0],to:e[1],label:e[2],state:'FATTO',basis:'collegamento esplicito della mappa'}));const seen=new Set(facts.map(r=>[r.from,r.to].sort().join('|'))),inf=[];const c=nodes.filter(n=>n.state==='PRESENTE'&&n.type==='json');for(let i=0;i<c.length;i++)for(let j=i+1;j<c.length;j++){const fields=[];for(const f of facetKeys){const A=c[i].facets?.[f],B=c[j].facets?.[f];if(A&&B&&[...A].some(x=>B.has(x)))fields.push(f)}if(!fields.length)continue;const p=[c[i].key,c[j].key].sort().join('|');if(seen.has(p))continue;seen.add(p);inf.push({from:c[i].key,to:c[j].key,label:'Relazione candidata: '+fields.join(', '),state:'INFERENZA',basis:'campi condivisi; da verificare'})}return facts.concat(inf.slice(0,40))}
function compact(n){const {facets,...x}=n;return x}
async function refresh(){if(!ok())throw Error('Sessione proprietario richiesta.');parsed=new Map();const L=local(),R=await remote(),nodes=R.concat(L.out),rels=relations(nodes);latest={schema:'RAFFAELLO_DATA_HUB_V3',generated_at:new Date().toISOString(),policy:{surface:'CREME_DE_LA_CREME',cold_archive:'iCloud scelto come archivio esterno; non sincronizzato da questa pagina',heavy_assets:'censiti ma non caricati'},datasets:nodes.map(compact),relations:rels,structural:ARCHIVE,errors:L.errors.concat(R.filter(x=>x.error).map(x=>x.key+': '+x.error))};try{localStorage.setItem(INDEX,JSON.stringify(latest))}catch{}return JSON.parse(JSON.stringify(latest))}
function read(k){if(!ok())throw Error('Sessione proprietario richiesta.');if(sensitive(k))throw Error('Sorgente esclusa per sicurezza.');if(parsed.has(k))return parsed.get(k);const raw=localStorage.getItem(k);if(raw==null)return null;try{return JSON.parse(raw)}catch{return raw}}
function exportIndex(){if(!latest)throw Error('Aggiorna prima il Data Hub.');const a=document.createElement('a'),u=URL.createObjectURL(new Blob([JSON.stringify(latest,null,2)],{type:'application/json'}));a.href=u;a.download='RAFFAELLO_DATA_HUB_V3_'+new Date().toISOString().slice(0,10)+'.json';a.click();setTimeout(()=>URL.revokeObjectURL(u),500)}
window.RaffaelloDataHub={refresh,read,snapshot:()=>latest?JSON.parse(JSON.stringify(latest)):null,export:exportIndex,version:'3.0'};
})();