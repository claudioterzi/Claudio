/* Behavioral fixtures only: no real browser, network, credentials or user storage. */
const assert=require('node:assert/strict'),test=require('node:test'),fs=require('node:fs'),vm=require('node:vm');
const source=name=>fs.readFileSync('public/'+name,'utf8');
const tick=()=>new Promise(resolve=>setImmediate(resolve));
class Element{
 constructor(tag='div',doc=null){this.tagName=tag.toUpperCase();this.nodeType=1;this.ownerDocument=doc;this.children=[];this.handlers={};this.attrs={};this.value='';this._text='';this.disabled=false;this.hidden=false;const values=new Set();this.classList={add:v=>values.add(v),remove:v=>values.delete(v),contains:v=>values.has(v),toggle:(v,on)=>{on=on===undefined?!values.has(v):on;on?values.add(v):values.delete(v);return on}};}
 set textContent(v){this._text=String(v);this.children=[];}get textContent(){return this._text+this.children.map(x=>x.textContent).join('');}
 append(...items){for(const x of items){x.parentElement=x.parentNode=this;this.children.push(x)}}
 replaceChildren(...items){this._text='';this.children=[];this.append(...items)}
 addEventListener(k,f){this.handlers[k]=f}setAttribute(k,v){this.attrs[k]=String(v)}focus(){this.focused=true}remove(){if(this.parentNode)this.parentNode.children=this.parentNode.children.filter(x=>x!==this)}
 replaceWith(node){const parent=this.parentNode,index=parent.children.indexOf(this),items=node.nodeType===11?node.children:[node];parent.children.splice(index,1,...items);for(const x of items)x.parentElement=x.parentNode=parent;}
 closest(selector){const tags=selector.toUpperCase().split(',');for(let p=this;p;p=p.parentElement)if(tags.includes(p.tagName))return p;return null}
 querySelectorAll(){const nodes=[];function walk(e){for(const x of e.children){if(x.tagName==='MARK'&&Object.hasOwn(x.attrs,'data-r3-search'))nodes.push(x);if(x.children)walk(x)}}walk(this);return nodes}
 normalize(){for(const x of this.children)if(x.normalize)x.normalize();for(let i=1;i<this.children.length;){const a=this.children[i-1],b=this.children[i];if(a.nodeType===3&&b.nodeType===3){a.nodeValue+=b.nodeValue;this.children.splice(i,1)}else i++}}
}
class Text{constructor(value,doc){this.nodeType=3;this.nodeValue=value;this.ownerDocument=doc}get textContent(){return this.nodeValue}replaceWith(node){Element.prototype.replaceWith.call(this,node)}}
function storage(initial={}){const values=new Map(Object.entries(initial));return{getItem:k=>values.get(k)||null,setItem:(k,v)=>values.set(k,String(v)),removeItem:k=>values.delete(k),values}}
function timerHarness(){let id=0;const tasks=new Map();return{tasks,setTimeout:(fn,delay)=>{tasks.set(++id,{fn,delay});return id},clearTimeout:i=>tasks.delete(i),setInterval:()=>0}}
const snapshot={schema:'r3-public-status-v1',source:'repository-derived',generated_at:'2026-10-13T13:33:58Z',commit:'fixture-1',heartbeat:{last_daily:'2026-10-13',source_file:'output/daily_2026-10-13.txt'},contacts:{last_date:'2026-06-12',verified_human:7},benchmarks:{last_file:'test_2026-06-14.json'}};
function agora(connected=true){
 const elements=new Map(),get=id=>{if(!elements.has(id))elements.set(id,new Element());return elements.get(id)},timers=timerHarness(),calls=[],pending=[],scripts=[];
 const buttons=Array.from({length:7},()=>new Element('button'));get('consilioInput').value='Domanda da conservare';get('consilioWrap').classList.add('visible');
 const doc={getElementById:get,createElement:tag=>new Element(tag),querySelectorAll:()=>[...buttons,get('consiglio-send')],addEventListener(){},visibilityState:'visible',head:{append:s=>scripts.push(s)}};
 const window={IDEA_OS_PORTFOLIO:{meta:{snapshot:'2026-09-17'},ideas:[{id:'IDEA-003',title:'Progetto verificabile',status:'PROJECT CREATED',dossier:{url:'https://example.test'}}]},Telegram:connected?{WebApp:{initData:'FIXTURE_ONLY',expand(){},setHeaderColor(){},setBackgroundColor(){},BackButton:{onClick(){}}}}:null};
 class FixedDate extends Date{static now(){return Date.parse('2026-10-14T16:00:00Z')}}
 const ctx=vm.createContext({window,document:doc,AbortController,Date:FixedDate,...timers,fetch:(url,options)=>{calls.push({url,...options});if(url==='/r3-status.json')return Promise.resolve({ok:true,json:async()=>snapshot});return new Promise((resolve,reject)=>{pending.push({resolve,reject});options.signal.addEventListener('abort',()=>{const error=new Error('Fixture timeout');error.name='AbortError';reject(error)})})}});
 vm.runInContext(source('agora.js'),ctx);return{window,get,timers,calls,pending,buttons,scripts,ctx};
}
test('Consiglio retains text and stays open while pending and after server failure',async()=>{
 const x=agora();await tick();const work=x.window.inviaConsiglio();
 assert.equal(x.get('consilioInput').value,'Domanda da conservare');assert(x.get('consilioWrap').classList.contains('visible'));assert(x.get('consilioInput').readOnly);assert(x.buttons.every(x=>x.disabled));
 await x.window.inviaConsiglio();assert.equal(x.calls.filter(x=>x.method==='POST').length,1);
 x.pending[0].resolve({ok:false,status:500,json:async()=>({errore:'Errore simulato'})});await work;
 assert.equal(x.get('consilioInput').value,'Domanda da conservare');assert(x.get('consilioWrap').classList.contains('visible'));assert(!x.get('consilioInput').readOnly);assert.match(x.get('command-status').textContent,/non confermato/);
});
test('Consiglio clears only after a successful server acknowledgement',async()=>{
 const x=agora();await tick();const work=x.window.inviaConsiglio();x.pending[0].resolve({ok:true,json:async()=>({ok:true})});await work;
 assert.equal(x.get('consilioInput').value,'');assert(!x.get('consilioWrap').classList.contains('visible'));assert.equal(x.get('btnConsiglio').attrs['aria-expanded'],'false');assert.match(x.get('command-status').textContent,/ricevuto dal server/);
});
test('Agorà does not erase a question on HTTP 200 without an application receipt',async()=>{
 for(const data of [{},null,{ok:false}]){const x=agora();await tick();const work=x.window.inviaConsiglio();x.pending[0].resolve({ok:true,status:200,json:async()=>data});await work;assert.equal(x.get('consilioInput').value,'Domanda da conservare');assert(x.get('consilioWrap').classList.contains('visible'));assert.match(x.get('command-status').textContent,/non confermato/);assert(!x.get('consilioInput').readOnly)}
});
test('Agorà preserves new text changed during a pending confirmed request',async()=>{
 const x=agora();await tick();const work=x.window.inviaConsiglio();x.get('consilioInput').value='Una nuova domanda';x.pending[0].resolve({ok:true,status:200,json:async()=>({ok:true})});await work;assert.equal(x.get('consilioInput').value,'Una nuova domanda');assert(x.get('consilioWrap').classList.contains('visible'));
});
test('Network errors and uncertain timeouts preserve the question',async()=>{
 for(const mode of ['network','timeout']){const x=agora();await tick();const work=x.window.inviaConsiglio();if(mode==='network')x.pending[0].reject(new Error('Rete simulata'));else [...x.timers.tasks.values()].find(x=>x.delay===45000).fn();await work;assert.equal(x.get('consilioInput').value,'Domanda da conservare');if(mode==='timeout')assert.match(x.get('command-status').textContent,/potrebbe essere arrivato/)}
});
test('Outside Telegram commands are explicit and do not POST or erase text',async()=>{
 const x=agora(false);await tick();await x.window.inviaConsiglio();assert.equal(x.calls.filter(x=>x.method==='POST').length,0);assert.equal(x.get('consilioInput').value,'Domanda da conservare');assert.match(x.get('command-status').textContent,/non è stato inviato/);
});
test('Rapid command activations are locked until the first acknowledgement',async()=>{
 const x=agora();await tick();const first=x.window.sendCmd('/briefing'),second=await x.window.sendCmd('/briefing');assert.equal(second.pending,true);assert.equal(x.calls.filter(x=>x.method==='POST').length,1);x.pending[0].resolve({ok:true,json:async()=>({})});await first;assert(x.buttons.every(x=>!x.disabled));
});
test('Agorà exposes dated snapshot provenance and project snapshot instead of live-agent claims',async()=>{
 const x=agora();await tick();assert.equal(x.get('logList').children.length,3);assert.match(x.get('activity-status').textContent,/repository.*2026/);assert.match(x.get('activity-status').textContent,/più vecchi di 24 ore/);assert.match(x.get('project-status').textContent,/singoli progetti non sono documentate/);assert.match(x.get('project-list').textContent,/IDEA-003/);assert.equal(x.calls[0].cache,'no-store');
 const html=source('home.html');assert(!html.includes('Sistema</b> online'));assert(!html.includes('class="log-time">oggi'));assert(!html.includes('>Attivo</div>'));assert(html.includes('for="consilioInput"'));
});
function guard(route,privateOK=false,publicOK=false){const redirects=[];const ctx=vm.createContext({URL,Event,location:{origin:'https://example.test',pathname:route,search:'?id=IDEA-003',hash:'#sezione',replace:v=>redirects.push(v)},sessionStorage:storage(privateOK?{'raffaello.private.session.v1':'1'}:{}),localStorage:storage(publicOK?{'raffaello.public.code.hash.v1':'fixture'}:{})});vm.runInContext(source('access-guard.js'),ctx);return{ctx,redirects}}
test('Every private page alias requires the private session and preserves a safe return path',()=>{
 for(const page of ['home','privato','dati','orchestratore','r3-evoluzione','r3-riprendi','progetti','creazioni','scritti','codice-gaia','idee','idea-os','idea-document','progetti-indice'])for(const suffix of ['','.html']){const path='/'+page+suffix,x=guard(path,false,true);assert.equal(x.redirects.length,1);const dest=new URL(x.redirects[0],'https://example.test');assert.equal(dest.pathname,'/accesso');assert.equal(dest.searchParams.get('reason'),'private');assert.equal(dest.searchParams.get('return'),path+'?id=IDEA-003#sezione');assert.equal(guard(path,true).redirects.length,0)}
 assert.equal(guard('/idee/IDEA-003').redirects.length,1);assert.equal(guard('/custode/').redirects.length,1);
});
test('Return URLs reject foreign origins, login loops and credentials or inference triggers',()=>{
 const routes=guard('/accesso').ctx.R3AccessRoutes;
 for(const hash of ['#tgWebAppData=FIXTURE','#token=FIXTURE','#x=1&secret=FIXTURE','#initData=FIXTURE'])assert.equal(routes.safeReturn('/home'+hash),'/home');
 for(const value of ['https://evil.test','//evil.test','/\\evil.test','/accesso?return=/home','/soglia','/home\n'])assert.equal(routes.safeReturn(value),'');
 assert.equal(routes.safeReturn('/home?token=fixture&x-vercel-protection-bypass=fixture&ok=1#x'),'/home?ok=1#x');assert.equal(routes.safeReturn('/atelier.html?q=non-inviare&intenzione=non-inviare&scena=locale'),'/atelier.html?scena=locale');assert.equal(routes.isPrivate('/progetti-indice.html'),true);
});
function accessGateway(owner=false,blockedStorage=false){
 const elements=new Map(),get=id=>{if(!elements.has(id))elements.set(id,new Element());return elements.get(id)},local=storage(),session=storage(),redirects=[];
 const gateway=source('accesso.js'),ownerHash=gateway.match(/var OWNER_HASH='([a-f0-9]+)'/)[1];
 const digest=owner?ownerHash:(ownerHash==='a'.repeat(64)?'b'.repeat(64):'a'.repeat(64));
 if(blockedStorage)session.setItem=()=>{throw new Error('Fixture blocked storage')};
 const ctx=vm.createContext({URL,URLSearchParams,TextEncoder,Uint8Array,document:{getElementById:get},location:{origin:'https://example.test',pathname:'/accesso',search:'?return='+encodeURIComponent('/home#consiglio'),hash:'',replace:to=>redirects.push(to)},localStorage:local,sessionStorage:session,crypto:{subtle:{digest:async()=>Uint8Array.from(Buffer.from(digest,'hex')).buffer}}});
 vm.runInContext(source('access-guard.js'),ctx);vm.runInContext(gateway,ctx);get('access-code').value='FIXTURE_ONLY';return{get,local,session,redirects};
}
test('Owner gateway returns to the requested page only after local session storage succeeds',async()=>{
 for(const blocked of [false,true]){const x=accessGateway(true,blocked);x.get('access-form').handlers.submit({preventDefault(){}});await tick();if(blocked){assert.equal(x.redirects.length,0);assert.match(x.get('access-status').textContent,/non riesce/)}else{assert.equal(x.session.getItem('raffaello.private.session.v1'),'1');assert.deepEqual(x.redirects,['/home#consiglio'])}}
});
test('A public code cannot navigate into a private return destination',async()=>{
 const x=accessGateway(false);x.get('access-form').handlers.submit({preventDefault(){}});await tick();assert.equal(x.redirects.length,0);assert.equal(x.session.getItem('raffaello.private.session.v1'),null);assert.equal(x.local.getItem('raffaello.public.code.hash.v1'),null);assert.match(x.get('access-status').textContent,/codice proprietario/);
});
function sync(response){const local=storage({'r3.sync.device_token.v1':'FIXTURE_ONLY','r3.sync.device_meta.v1':'{}'}),elements=new Map(),get=id=>{if(!elements.has(id))elements.set(id,new Element());return elements.get(id)},window={};const ctx=vm.createContext({window,document:{readyState:'loading',addEventListener(){},getElementById:get},localStorage:local,fetch:response,setTimeout(){},clearTimeout(){},setInterval(){}});vm.runInContext(source('r3-sync.js'),ctx);return{window,local,get}}
test('Failed or malformed revocation retains local authorization and allows retry',async()=>{
 for(const response of [async()=>{throw new Error('Fixture offline')},async()=>({ok:false,status:503,json:async()=>({error:'Fixture503'})}),async()=>({ok:true,status:200,json:async()=>({})})]){const x=sync(response),result=await x.window.R3Sync.revoke();assert.equal(result.status,'error');assert.equal(x.local.getItem('r3.sync.device_token.v1'),'FIXTURE_ONLY');assert.match(x.get('r3-server-sync-status').textContent,/non confermata/);assert(!x.get('r3-sync-revoke').disabled)}
});
test('Only acknowledged revocation clears local authorization',async()=>{
 const x=sync(async()=>({ok:true,status:200,json:async()=>({ok:true,revoked:'fixture-device'})}));assert.equal((await x.window.R3Sync.revoke()).status,'revoked');assert.equal(x.local.getItem('r3.sync.device_token.v1'),null);assert.match(x.get('r3-server-sync-status').textContent,/confermata dal server/);
});
test('An already invalid device is described as unauthorized rather than newly revoked',async()=>{
 const x=sync(async()=>({ok:false,status:401,json:async()=>({error:'Unauthorized fixture'})}));assert.equal((await x.window.R3Sync.revoke()).status,'not_authorized');assert.equal(x.local.getItem('r3.sync.device_token.v1'),null);assert.match(x.get('r3-server-sync-status').textContent,/non riconosce/);
});
test('Text highlighting preserves attributes, link identity and handlers, then cleanly clears',()=>{
 const search=require('../public/terzo-livello-search.js');const doc={createElement:t=>new Element(t,doc),createTextNode:v=>new Text(v,doc),createDocumentFragment:()=>{const f=new Element('fragment',doc);f.nodeType=11;return f},createTreeWalker:root=>{const text=[];function walk(n){if(n.nodeType===3)text.push(n);else n.children.forEach(walk)}walk(root);let i=0;return{nextNode:()=>text[i++]||null}}};
 const section=doc.createElement('section'),anchor=doc.createElement('a');anchor.setAttribute('href','/parola.html');anchor.setAttribute('class','parola');let clicks=0;anchor.handlers.click=()=>clicks++;anchor.append(doc.createTextNode('Pagina p prova ['));section.append(anchor);
 assert.equal(search.highlight(section,'class'),0);assert.equal(anchor.attrs.class,'parola');assert(search.highlight(section,'p')>0);assert.equal(anchor.attrs.href,'/parola.html');assert.equal(section.children[0],anchor);anchor.handlers.click();assert.equal(clicks,1);search.clear(section);assert.equal(section.textContent,'Pagina p prova [');assert.equal(section.querySelectorAll().length,0);assert.equal(search.highlight(section,'['),1);search.clear(section);assert.equal(section.textContent,'Pagina p prova [');
});
test('IDEA loading stops after five seconds with explicit error and manual retry',()=>{
 let now=0,reloads=0;const timers=timerHarness(),window={location:{reload:()=>reloads++}},ctx=vm.createContext({window,Date:{now:()=>now},...timers});vm.runInContext(source('idea-loader.js'),ctx);const status=new Element(),retry=new Element('button');let ready=0;window.R3IdeaLoader.wait(()=>ready++,status,retry);
 for(let i=0;i<51&&timers.tasks.size;i++){const [id,task]=timers.tasks.entries().next().value;timers.tasks.delete(id);now+=task.delay;task.fn()}assert.equal(ready,0);assert.equal(timers.tasks.size,0);assert.equal(retry.hidden,false);assert.match(status.textContent,/non è stato caricato/);retry.onclick();assert.equal(reloads,1);
});
test('IDEA successful delayed loading boots exactly once and hides retry',()=>{
 let now=0;const timers=timerHarness(),window={location:{reload(){}}},ctx=vm.createContext({window,Date:{now:()=>now},...timers});vm.runInContext(source('idea-loader.js'),ctx);const status=new Element(),retry=new Element();let ready=0;window.R3IdeaLoader.wait(()=>ready++,status,retry);window.IDEA_OS_PORTFOLIO={meta:{},ideas:[]};const [id,task]=timers.tasks.entries().next().value;timers.tasks.delete(id);now=100;task.fn();assert.equal(ready,1);assert.equal(status.textContent,'');assert(retry.hidden);assert.equal(timers.tasks.size,0);
});
test('Visible core labels are associated and sync panels have unique status IDs',()=>{
 assert(source('progetti-indice.html').includes('aria-label="Cerca idee e progetti"'));for(const field of ['state','priority','claim','evidence','falsifier','source']){const html=source('r3-evoluzione.html');assert(html.includes('for="r3-memory-'+field+'"'));assert(html.includes('id="r3-memory-'+field+'"'))}assert(source('r3-sync.js').includes('for="r3-sync-password"'));assert(source('r3-secure-sync.js').includes('for="r3-sync-pass"'));assert(!source('r3-sync.js').includes('id="r3-sync-status"'));
});
test('Agorà metadata/accent and command-button colors satisfy small-text contrast',()=>{
 const luminance=hex=>{const rgb=hex.match(/\w\w/g).map(v=>parseInt(v,16)/255).map(v=>v<=.04045?v/12.92:((v+.055)/1.055)**2.4);return .2126*rgb[0]+.7152*rgb[1]+.0722*rgb[2]},contrast=(a,b)=>{const x=luminance(a),y=luminance(b);return(Math.max(x,y)+.05)/(Math.min(x,y)+.05)};
 const html=source('home.html'),palette=name=>html.match(new RegExp('--'+name+':\\s*#([a-f0-9]{6})'))[1];
 for(const color of ['text-dim','text-sub','red'])for(const bg of ['surface','card'])assert(contrast(palette(color),palette(bg))>=4.5);assert(contrast('ffffff',palette('red-button'))>=4.5);
});
