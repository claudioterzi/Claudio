'use strict';
const assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm'),crypto=require('node:crypto'),path=require('node:path');
const root=path.resolve(process.argv[2]||path.join(__dirname,'..'));
const GOLDEN_CORPUS_SHA256='e57149489a66d5c8f57497d47c5cbd7fd527a6f0a53b7b9bae48b8ede6ca6421';
const sha256=value=>crypto.createHash('sha256').update(value).digest('hex');
const read=f=>fs.readFileSync(path.join(root,'public',f),'utf8');
const inline=f=>[...read(f).matchAll(/<script(?:\s[^>]*)?>([\s\S]*?)<\/script>/g)].map(m=>m[1]).filter(s=>s.trim()).at(-1);
const outcomes=[];
async function test(name,fn){try{await fn();outcomes.push({name,status:'PASS'})}catch(e){outcomes.push({name,status:'FAIL',error:e.stack})}}
class El{
 constructor(doc,tag='div',id=''){
  Object.assign(this,{doc,tagName:tag.toUpperCase(),children:[],parentNode:null,attrs:{},listeners:{},className:'',style:{},value:'',checked:false,hidden:false,disabled:false,_text:'',_html:''});
  this.classList={add:(...xs)=>this.classes(xs,true),remove:(...xs)=>this.classes(xs,false),contains:x=>this.className.split(/\s+/).includes(x),toggle:(x,on)=>this.classes([x],on===undefined?!this.classList.contains(x):on)};
  this.id=id;
 }
 set id(x){this._id=x;if(x)this.doc.ids.set(x,this)}get id(){return this._id}
 classes(xs,on){const set=new Set(this.className.split(/\s+/).filter(Boolean));xs.forEach(x=>on?set.add(x):set.delete(x));this.className=[...set].join(' ')}
 appendChild(el){this.children.push(el);el.parentNode=this;return el}append(...els){els.forEach(el=>this.appendChild(el))}
 contains(el){return el===this||this.children.some(c=>c.contains(el))}
 set textContent(x){this._text=String(x);this.children=[];this._html=''}get textContent(){return this._text+this.children.map(c=>c.textContent).join('')}
 set innerHTML(x){if(this.contains(this.doc.activeElement))this.doc.activeElement=this.doc.body;this.children=[];this._text='';this._html=String(x);const m=this._html.match(/<(h[12])[^>]*>([\s\S]*?)<\/\1>/i);if(m){const h=this.doc.createElement(m[1]);h.textContent=m[2].replace(/<[^>]+>/g,'');this.appendChild(h)}}get innerHTML(){return this._html}
 descendants(){return this.children.flatMap(c=>[c,...c.descendants()])}
 querySelectorAll(selector){const parts=selector.split(',').map(x=>x.trim().toUpperCase());return this.descendants().filter(e=>parts.some(x=>x.startsWith('.')?e.classList.contains(x.slice(1).toLowerCase()):e.tagName===x))}
 querySelector(s){return this.querySelectorAll(s)[0]||null}
 setAttribute(k,v){this.attrs[k]=String(v)}getAttribute(k){return this.attrs[k]??null}removeAttribute(k){delete this.attrs[k]}
 addEventListener(k,f){(this.listeners[k]??=[]).push(f)}removeEventListener(k,f){this.listeners[k]=(this.listeners[k]||[]).filter(x=>x!==f)}
 fire(k,e={}){e.preventDefault??=()=>{};e.target??=this;(this.listeners[k]||[]).slice().forEach(f=>f(e))}
 focus(){this.doc.activeElement=this}scrollIntoView(o){this.lastScroll=o}setPointerCapture(){}click(){throw Error('Download forbidden in this test')}
}
class Doc{
 constructor(){this.ids=new Map();this.listeners={};this.body=new El(this,'body');this.activeElement=this.body;this.hidden=false}
 createElement(tag){return new El(this,tag)}node(id,tag='div',text=''){const e=new El(this,tag,id);e.textContent=text;this.body.appendChild(e);return e}
 getElementById(id){const e=this.ids.get(id);if(!e)throw Error('Missing mock DOM '+id);return e}
 querySelector(s){return this.body.querySelector(s)}querySelectorAll(s){return this.body.querySelectorAll(s)}
 addEventListener(k,f){(this.listeners[k]??=[]).push(f)}fire(k,e={}){(this.listeners[k]||[]).forEach(f=>f(e))}
}
function fixture(url='https://local.test/page.html'){
 const doc=new Doc(),events={},raf=new Map(),timers=new Map();let next=1,clock=0;
 const loc={_href:url,get href(){return this._href},set href(x){this._href=String(x)},get hash(){return new URL(this._href).hash},get search(){return new URL(this._href).search}};
 const scope={document:doc,location:loc,URL,URLSearchParams,AbortController,DOMException,console,TextEncoder,Uint8ClampedArray,Blob,Map,Set,performance:{now:()=>clock},
 requestAnimationFrame:f=>{const id=next++;raf.set(id,f);return id},cancelAnimationFrame:id=>raf.delete(id),matchMedia:()=>({matches:false}),
 addEventListener:(k,f)=>(events[k]??=[]).push(f),removeEventListener:(k,f)=>events[k]=(events[k]||[]).filter(x=>x!==f),
 crypto:{randomUUID:()=>'mock-'+next++},atob:s=>Buffer.from(s,'base64').toString('binary'),btoa:s=>Buffer.from(s,'binary').toString('base64'),setTimeout:(fn,delay)=>{const id=next++;timers.set(id,{fn,delay});return id},clearTimeout:id=>timers.delete(id),
 Path2D:class{moveTo(){}arc(){}},Image:class{},history:{pushes:0,replaces:0,pushState(_s,_t,u){this.pushes++;loc.href=u.href},replaceState(_s,_t,u){this.replaces++;loc.href=u.href}}};
 scope.window=scope;vm.createContext(scope);
 return{doc,scope,run:s=>vm.runInContext(s,scope),event:(k,e={})=>{e.preventDefault??=()=>{};(events[k]||[]).slice().forEach(f=>f(e))},tick:t=>{clock=t;const frames=[...raf.values()];raf.clear();frames.forEach(f=>f(t))},get queued(){return raf.size},get timers(){return timers},timeout(){assert.equal(timers.size,1);const [id,item]=[...timers][0];timers.delete(id);item.fn()}};
}
function opera(url){
 const f=fixture(url||'https://local.test/opera.html');['cerca','voci','search-count','clear-search','doc-status','pagina','doc-link'].forEach(id=>f.doc.node(id,id==='cerca'?'input':'div'));
 f.fetches=0;f.fail=false;f.requests=[];f.scope.fetch=async(url,init)=>{f.fetches++;f.requests.push({url,init});if(f.fail)throw Error('mock offline');assert.match(url,/^opera\/document-\d{3}-[a-f0-9]{16}\.html$/);return{ok:true,text:async()=>read(url)}};return f;
}
function music(data){
 const f=fixture('https://local.test/musica.html');['search','filter','anchors','count','track-list','playlist-grid','playlist-badge','stat-songs','stat-texts','stat-check'].forEach(id=>f.doc.node(id));
 ['stat-songs','stat-texts','stat-check'].forEach(id=>f.doc.getElementById(id).textContent='—');f.doc.getElementById('filter').value='all';
 if(data!==undefined)f.scope.TERZI_MUSICA=data;f.run(inline('musica.html'));return f;
}
function viva(){
 const f=fixture('https://local.test/opera-viva.html');['art','title','status','source','workname','gap','angle','gap-value','angle-value','metric','eye','view','eye-value','play','preset','photo','front','rear','png','project','signature'].forEach(id=>f.doc.node(id,id==='art'?'canvas':'input'));
 Object.entries({title:'Raffaello · Studio 01',source:'portrait',gap:'50',angle:'.6446',eye:'0',view:'both',preset:'balanced'}).forEach(([id,v])=>f.doc.getElementById(id).value=v);
 function ctx(){return{strokes:0,data:new Uint8ClampedArray(480000),save(){},restore(){},setTransform(){},fillRect(){},beginPath(){},rect(){},clip(){},translate(){},scale(){},rotate(){},fill(){},stroke(){this.strokes++},createImageData(w,h){return{data:new Uint8ClampedArray(w*h*4)}},putImageData(im){this.data=im.data},getImageData(){return{data:this.data}},drawImage(){}}}
 const preview=ctx();f.doc.getElementById('art').getContext=()=>preview;const create=f.doc.createElement.bind(f.doc);f.doc.createElement=tag=>{const el=create(tag);if(tag==='canvas'){const c=ctx();el.getContext=()=>c}return el};
 f.run(read('opera-viva-core.js'));f.run(read('opera-viva-data.js'));let builds=0;const points=f.scope.OperaViva.points;f.scope.OperaViva.points=(...a)=>{builds++;return points(...a)};f.run(read('opera-viva.js'));f.preview=preview;Object.defineProperty(f,'builds',{get:()=>builds});return f;
}
function book(){
 const f=fixture('https://local.test/opuscolo.html');['nav','carte-grid','prev-page','next-page','page-status'].forEach(id=>f.doc.node(id,id.includes('page')?'button':'div'));
 for(let i=1;i<=8;i++){const p=f.doc.node('p'+i);p.className='a6';const h=f.doc.createElement(i===1?'h1':'h2');h.textContent='Titolo '+i;p.appendChild(h)}
 f.run(inline('opuscolo.html'));return f;
}
function sanctuary(bot='',aframe=true){
 const f=fixture('https://local.test/santuario-vr.html'+bot);['line','sub','exit-web','hold-web','hold-progress','destination','scene-status','fiamma','uscita','candela'].forEach(id=>f.doc.node(id,id==='hold-web'||id==='exit-web'?'button':'div'));
 f.doc.node('scene','a-scene').is=()=>false;f.components={};if(aframe)f.scope.AFRAME={registerComponent:(n,c)=>f.components[n]=c};f.run(inline('santuario-vr.html'));return f;
}
(async()=>{
 await test('MM12 golden corpus, exact101 documents, metadata and HTML budget',()=>{
 const corpus=read('opera-corpus.json'),docs=JSON.parse(corpus),manifest=JSON.parse(read('opera/manifest.json'));
 assert.equal(sha256(corpus),GOLDEN_CORPUS_SHA256);assert.equal(docs.length,101);assert.equal(manifest.source_corpus_sha256,GOLDEN_CORPUS_SHA256);assert.equal(manifest.documents.length,101);assert.equal(manifest.schema,'OPERA-LAZY/1');
 const index=JSON.parse(read('opera.html').match(/const DOCS = (\[.*?\]);\s*const FIRST_DOC/s)[1]);assert.deepEqual(index,manifest.documents);
 let bytes=0;const paths=new Set();
 docs.forEach((doc,i)=>{const meta=manifest.documents[i];for(const key of ['gruppo','titolo','file'])assert.equal(meta[key],doc[key]);assert.match(meta.src,/^opera\/document-\d{3}-[a-f0-9]{16}\.html$/);assert(!paths.has(meta.src));paths.add(meta.src);const html=read(meta.src);assert.equal(html,doc.html,'Exact content '+doc.file);assert.equal(sha256(html),meta.sha256);assert.equal(Buffer.byteLength(html),meta.bytes);bytes+=meta.bytes});
 assert.equal(bytes,manifest.html_total_bytes);assert.ok(Buffer.byteLength(read('opera.html'))<80000,'Initial HTML <80KB');
 const first=JSON.parse(read('opera.html').match(/const FIRST_DOC = (\{.*?\});\s*let corrente/s)[1]);assert.equal(first.html,docs[0].html);assert.equal(first.file,docs[0].file);
 });
 await test('MM03/MM05/MM12 stable index, focus, permalink and isolated lazy fetch/cache',async()=>{
 const f=opera();await f.run(inline('opera.html'));assert.equal(f.fetches,0);const buttons=f.doc.getElementById('voci').querySelectorAll('button');assert.equal(buttons.length,101);
 buttons[1].focus();await f.scope.apri(1,{focus:true,history:'push'});assert.equal(f.fetches,1);assert.equal(f.doc.getElementById('voci').querySelectorAll('button')[1],buttons[1]);assert.match(f.scope.location.hash,/^#doc=/);assert.equal(f.scope.history.pushes,1);assert.equal(f.doc.activeElement.tagName,'H2');assert.equal(buttons[1].getAttribute('aria-current'),'page');
 assert.equal(f.requests[0].url,JSON.parse(read('opera/manifest.json')).documents[1].src);assert.equal(f.requests[0].init.credentials,'omit');assert.equal(f.requests[0].init.cache,'force-cache');assert(f.requests[0].init.signal instanceof AbortSignal);assert.equal(f.timers.size,0);
 await f.scope.apri(2,{focus:true,history:'push'});assert.equal(f.fetches,2);await f.scope.apri(1);assert.equal(f.fetches,2);assert.equal(f.doc.getElementById('pagina').children[1].innerHTML,JSON.parse(read('opera-corpus.json'))[1].html);
 });
 await test('MM05/MM11/MM13 restore URL/filter, empty feedback and reduced motion',async()=>{
 const docs=JSON.parse(read('opera-corpus.json')),f=opera('https://local.test/opera.html#doc='+encodeURIComponent(docs[4].file)+'&q=no-such-title');f.scope.matchMedia=()=>({matches:true});await f.run(inline('opera.html'));
 assert.equal(f.doc.getElementById('cerca').value,'no-such-title');assert.match(f.doc.getElementById('search-count').textContent,/Nessun documento/);f.doc.getElementById('clear-search').onclick();assert.equal(f.doc.activeElement.id,'cerca');
 await f.scope.apri(5,{focus:true,history:'push'});assert.equal(f.doc.getElementById('pagina').lastScroll.behavior,'auto');
 f.scope.location.href='https://local.test/opera.html#doc='+encodeURIComponent(docs[4].file);await f.scope.ripristinaURL();assert.ok(f.doc.getElementById('doc-link').href.includes(encodeURIComponent(docs[4].file)));
 });
 await test('Opera failed fetch retains document; retry succeeds',async()=>{
 const f=opera();await f.run(inline('opera.html'));const page=f.doc.getElementById('pagina'),first=page.children[1];f.fail=true;await f.scope.apri(6,{focus:true,history:'push'});
 assert.equal(page.children[1],first);assert.match(f.doc.getElementById('doc-status').textContent,/non è stato caricato/);assert.equal(page.getAttribute('aria-busy'),'false');f.fail=false;await f.scope.apri(6,{focus:true,history:'push'});assert.equal(f.fetches,2);assert.notEqual(page.children[1],first);
 });
 await test('MM04/MM09 persistent label and public return destinations',()=>{
 assert.match(read('opera.html'),/<label for="cerca">Cerca un documento<\/label>/);assert.ok(!read('musica.html').includes('href="scritti.html"'));assert.ok(!read('opera-viva.html').includes('href="creazioni.html"'));assert.match(read('musica.html'),/href="raffaello.html"/);assert.match(read('opera-viva.html'),/href="raffaello.html"/);
 });
 await test('MM16 missing data error versus valid empty zero',()=>{
 const bad=music();assert.equal(bad.doc.getElementById('stat-songs').textContent,'—');assert.equal(bad.doc.getElementById('search').disabled,true);assert.match(bad.doc.getElementById('count').textContent,/non è stato caricato/);
 const empty=music({songs:[],raffPlaylist:{songs:[]},count:101});assert.equal(empty.doc.getElementById('stat-songs').textContent,'0');assert.equal(empty.doc.getElementById('stat-texts').textContent,'0');assert.equal(empty.doc.getElementById('anchors').disabled,false);
 });
 await test('MM16 real101 data counters derived; filter retained',()=>{
 const source=read('musica-data.js'),data=JSON.parse(source.slice(source.indexOf('=')+1).trim().replace(/;$/,''));data.count=999;const f=music(data);
 assert.equal(f.doc.getElementById('stat-songs').textContent,'101');assert.equal(f.doc.getElementById('stat-texts').textContent,'85');assert.equal(f.doc.getElementById('stat-check').textContent,'16');f.doc.getElementById('filter').value='raffaello';f.doc.getElementById('filter').fire('change');assert.match(f.doc.getElementById('count').textContent,/4 di 101/);
 });
 await test('MM06 rear preview omits signature; front and coreSVG agree',()=>{
 const f=viva();f.preview.strokes=0;f.doc.getElementById('view').value='rear';f.doc.getElementById('view').onchange();assert.equal(f.preview.strokes,0);f.doc.getElementById('view').value='front';f.doc.getElementById('view').onchange();assert.equal(f.preview.strokes,1);
 const api=f.scope.OperaViva,pts=api.points(()=>.4,50),state={title:'X',id:'t',gap:50,angle:.6};assert.ok(!api.svg('rear',pts,state).includes(api.SIGN));assert.ok(api.svg('front',pts,state).includes(api.SIGN));
 });
 await test('MM15 angle coalesced without point rebuild; gap rebuilds',()=>{
 const f=viva(),initial=f.builds;for(const a of ['.7','.8','.9']){f.doc.getElementById('angle').value=a;f.doc.getElementById('angle').oninput()}
 assert.equal(f.builds,initial);assert.equal(f.queued,1);f.tick(16);assert.equal(f.builds,initial);f.doc.getElementById('gap').value='60';f.doc.getElementById('gap').oninput();assert.equal(f.builds,initial+1);
 });
 await test('MM17 custom title retained, default follows source, reduced motion stops simulation',()=>{
 const f=viva();f.doc.getElementById('title').value='Titolo originale';f.doc.getElementById('title').oninput();f.doc.getElementById('source').value='wave';f.doc.getElementById('source').onchange();assert.equal(f.doc.getElementById('title').value,'Titolo originale');
 const fresh=viva();fresh.doc.getElementById('source').value='wave';fresh.doc.getElementById('source').onchange();assert.equal(fresh.doc.getElementById('title').value,'Onde · Studio cinetico');fresh.scope.matchMedia=()=>({matches:true});fresh.doc.getElementById('play').onclick();assert.equal(fresh.queued,0);assert.match(fresh.doc.getElementById('status').textContent,/Movimento ridotto/);
 });
 await test('MM01/MM02 responsive A6, print excludes controls,74 cards',()=>{
 const html=read('opuscolo.html');assert.match(html,/\.a6\s*\{[^}]*max-width:\s*100%/);assert.match(html,/@page\s*\{\s*size:\s*A6 portrait/);assert.match(html,/nav, \.controls, #page-status\s*\{\s*display:\s*none !important/);assert.match(html,/\.carte-grid\s*\{\s*grid-template-columns:\s*repeat\(3/);
 const f=book();assert.equal((f.doc.getElementById('carte-grid').innerHTML.match(/class="carta-item"/g)||[]).length,74);
 });
 await test('MM14 current page, disabled bounds and heading focus',()=>{
 const f=book();assert.equal(f.doc.getElementById('prev-page').disabled,true);assert.equal(f.doc.getElementById('nav1').getAttribute('aria-current'),'page');f.scope.goTo(8,true);assert.equal(f.doc.getElementById('next-page').disabled,true);assert.equal(f.doc.getElementById('nav8').getAttribute('aria-current'),'page');assert.equal(f.doc.getElementById('nav1').getAttribute('aria-current'),null);assert.equal(f.doc.activeElement.textContent,'Titolo 8');assert.match(f.doc.getElementById('page-status').textContent,/Pagina 8 di 8/);f.scope.goTo(99);assert.equal(f.doc.getElementById('nav8').getAttribute('aria-current'),'page');
 });
 await test('MM08 keyboard release resets; continuous12s completes and focuses exit',()=>{
 const f=sanctuary(),b=f.doc.getElementById('hold-web');b.fire('keydown',{key:' ',repeat:false});f.tick(5000);assert.equal(f.doc.getElementById('hold-progress').getAttribute('aria-valuenow'),'5');f.event('keyup',{key:' '});assert.equal(f.doc.getElementById('hold-progress').getAttribute('aria-valuenow'),'0');f.tick(20000);assert.notEqual(f.doc.getElementById('fiamma').getAttribute('visible'),'true');
 b.fire('keydown',{key:'Enter',repeat:false});f.tick(31999);assert.notEqual(f.doc.getElementById('fiamma').getAttribute('visible'),'true');f.tick(32000);assert.equal(f.doc.getElementById('fiamma').getAttribute('visible'),'true');assert.equal(f.doc.activeElement.id,'exit-web');assert.equal(b.disabled,true);
 });
 await test('MM07 controller rayleave and blur cancel; listeners cleaned',()=>{
 const f=sanctuary(),candle=f.doc.getElementById('candela'),controller=f.doc.node('controller');controller.components={raycaster:{intersectedEls:[candle]}};
 const component=f.components['quest-hold-bridge'],instance={el:controller,data:{target:candle}};component.init.call(instance);controller.fire('triggerdown');f.tick(6000);controller.components.raycaster.intersectedEls=[];component.tick.call(instance);assert.equal(f.doc.getElementById('hold-progress').getAttribute('aria-valuenow'),'0');assert.equal(f.queued,0);
 controller.components.raycaster.intersectedEls=[candle];controller.fire('triggerdown');f.tick(7000);f.event('blur');assert.equal(f.queued,0);f.tick(30000);assert.notEqual(f.doc.getElementById('fiamma').getAttribute('visible'),'true');component.remove.call(instance);assert.equal(controller.listeners.triggerdown.length,0);
 });
 await test('MM08/MM10 AFrame failure retains DOM hold; bot override ignored; exit gated',()=>{
 const f=sanctuary('?bot=AnotherBot',false);assert.match(f.doc.getElementById('scene-status').textContent,/pulsante/);assert.match(f.doc.getElementById('destination').textContent,/@ProtocolloRossoBot/);const before=f.scope.location.href;f.doc.getElementById('exit-web').fire('click');assert.equal(f.scope.location.href,before);
 f.doc.getElementById('hold-web').fire('pointerdown',{button:0,pointerId:1});f.tick(12000);f.doc.getElementById('exit-web').fire('click');assert.equal(f.scope.location.href,'https://t.me/ProtocolloRossoBot?start=vr');
 });
 await test('Opera newest uncached document wins out-of-order responses',async()=>{
 const f=opera();await f.run(inline('opera.html'));const pending=[],docs=JSON.parse(read('opera/manifest.json')).documents;
 f.scope.fetch=(url,init)=>new Promise(resolve=>pending.push({url,init,resolve}));
 const slow=f.scope.apri(7,{focus:true,history:'push'}),latest=f.scope.apri(8,{focus:true,history:'push'});assert.equal(pending.length,2);
 pending[1].resolve({ok:true,text:async()=>read(docs[8].src)});await latest;assert.equal(f.doc.getElementById('voci').querySelectorAll('button')[8].getAttribute('aria-current'),'page');assert.equal(f.scope.history.pushes,1);
 pending[0].resolve({ok:true,text:async()=>read(docs[7].src)});await slow;assert.equal(f.doc.getElementById('voci').querySelectorAll('button')[8].getAttribute('aria-current'),'page');assert.equal(f.scope.history.pushes,1);assert.equal(f.doc.getElementById('pagina').children[1].innerHTML,read(docs[8].src));assert.equal(f.doc.getElementById('pagina').getAttribute('aria-busy'),'false');assert.equal(f.timers.size,0);
 await f.scope.apri(7);assert.equal(pending.length,2,'Completed old response cached without replacing latest selection');
 });
 await test('Opera cached selection supersedes pending request without clearing the current reader',async()=>{
 const f=opera();await f.run(inline('opera.html'));let resolve;f.scope.fetch=()=>new Promise(r=>{resolve=r});const slow=f.scope.apri(7,{focus:true,history:'push'});
 await f.scope.apri(0);resolve({ok:true,text:async()=>read(JSON.parse(read('opera/manifest.json')).documents[7].src)});await slow;
 assert.equal(f.doc.getElementById('voci').querySelectorAll('button')[0].getAttribute('aria-current'),'page');assert.equal(f.doc.getElementById('pagina').getAttribute('aria-busy'),'false');assert.equal(f.scope.history.pushes,0);
 });
 await test('Opera one pending fetch per document; timeout aborts and retry succeeds',async()=>{
 const f=opera();await f.run(inline('opera.html'));let calls=0,signal;
 f.scope.fetch=(url,init)=>{calls++;signal=init.signal;return new Promise((_resolve,reject)=>signal.addEventListener('abort',()=>reject(new DOMException('Mock aborted','AbortError'))))};
 const first=f.scope.apri(9,{focus:true,history:'push'}),second=f.scope.apri(9,{focus:true,history:'push'});assert.equal(calls,1);assert.equal(f.timers.size,1);assert.equal([...f.timers.values()][0].delay,20000);f.timeout();assert(signal.aborted);await Promise.all([first,second]);assert.equal(f.doc.getElementById('pagina').getAttribute('aria-busy'),'false');assert.match(f.doc.getElementById('doc-status').textContent,/non è stato caricato/);assert.equal(f.scope.history.pushes,0);
 f.scope.fetch=async()=>{calls++;return{ok:true,text:async()=>read(JSON.parse(read('opera/manifest.json')).documents[9].src)}};await f.scope.apri(9,{focus:true,history:'push'});assert.equal(calls,2);assert.equal(f.scope.history.pushes,1);assert.equal(f.timers.size,0);
 });
 await test('Opera stale rejection does not overwrite successful latest reader or status',async()=>{
 const f=opera();await f.run(inline('opera.html'));let reject;const normal=f.scope.fetch;f.scope.fetch=(url,init)=>url.includes('document-010-')?new Promise((_resolve,fail)=>reject=fail):normal(url,init);
 const slow=f.scope.apri(10,{focus:true,history:'push'});await f.scope.apri(11,{focus:true,history:'push'});reject(Error('Stale mocked failure'));await slow;
 assert.equal(f.doc.getElementById('voci').querySelectorAll('button')[11].getAttribute('aria-current'),'page');assert.equal(f.doc.getElementById('doc-status').textContent,'');assert.equal(f.doc.getElementById('pagina').getAttribute('aria-busy'),'false');assert.equal(f.scope.history.pushes,1);
 });
 console.log(JSON.stringify({suite:'multimedia-local-mock',tests:outcomes.length,passed:outcomes.filter(x=>x.status==='PASS').length,failed:outcomes.filter(x=>x.status==='FAIL').length,outcomes},null,2));
 if(outcomes.some(x=>x.status==='FAIL'))process.exitCode=1;
})();
