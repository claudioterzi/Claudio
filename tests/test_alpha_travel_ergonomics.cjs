const fs=require('fs'),path=require('path'),vm=require('vm'),assert=require('assert');
const root=path.resolve(__dirname,'..'),out=[];
const source=name=>fs.readFileSync(path.join(root,'public',name),'utf8');
async function test(name,fn){try{await fn();out.push({name,pass:true})}catch(error){out.push({name,pass:false,error:error.stack});process.exitCode=1}}
function node(){return {value:'',textContent:'',innerHTML:'',hidden:false,disabled:false,dataset:{},children:[],listeners:{},classList:{add(){},remove(){},toggle(){},contains(){return true}},addEventListener(type,fn){this.listeners[type]=fn},append(...items){this.children.push(...items)},appendChild(item){this.children.push(item)},replaceChildren(...items){this.children=items},setAttribute(){},focus(){},scrollIntoView(){}}}
function sandbox(extra={}){const ctx={console,URL,URLSearchParams,AbortController,DOMException,TextEncoder,setTimeout,clearTimeout,matchMedia:()=>({matches:false}),...extra};ctx.window=ctx;vm.createContext(ctx);return ctx}
function range(text,start,end){const a=text.indexOf(start);assert(a>=0,start);const b=text.indexOf(end,a);assert(b>a,end);return text.slice(a,b)}
(async()=>{
await test('Syntax: owned scripts and every inline page script',()=>{
 for(const name of ['alpha-request.js','alpha-voice.js','a74-gallery.js','a74-gallery-manual-fix.js','a74-presentation-i18n.js','alpha74-art.js','viaggi-pro.js'])new vm.Script(source(name),{filename:name});
 for(const name of ['alpha.html','alpha74-test.html','tarocchi-alpha.html','tarocchi-manuale-alpha.html','tarocchi-raffaello.html','viaggi.html','parti.html','flight_hunter.html','oracolo.html'])for(const [,body]of source(name).matchAll(/<script\b[^>]*>([\s\S]*?)<\/script>/gi))new vm.Script(body,{filename:name});
});
await test('Audio mount and language change issue no TTS request',()=>{
 let fetches=0,speech=0;const intro=node(),narration=node(),language=node();language.value='it';
 const original=node();original.dataset.manual='1';original.cloneNode=()=>button;original.replaceWith=()=>{};const button=node();
 const box=node();box.querySelector=selector=>selector==='[data-atlas-tour]'?original:selector.includes('head')?intro:narration;
 const ctx=sandbox({document:{readyState:'complete',querySelector:()=>box,getElementById:()=>language},fetch:()=>{fetches++;throw Error('network forbidden')},AlphaVoice:{stop(){},speak(){speech++}},addEventListener(){}});
 vm.runInContext(source('a74-presentation-i18n.js'),ctx);assert.equal(fetches,0);assert.equal(speech,0);
 language.value='es';language.listeners.change();assert.equal(fetches,0);assert.equal(speech,0);assert(narration.textContent.includes('Alpha 74'));
 button.onclick();assert.equal(speech,1);
});
await test('Manual gallery fix mount is text only',()=>{
 let calls=0;const button=node(),paragraph=node(),box=node();box.querySelector=s=>s==='[data-atlas-tour]'?button:paragraph;
 const ctx=sandbox({document:{readyState:'complete',querySelector:()=>box,getElementById:()=>({value:'it'})},AlphaVoice:{stop(){},speak(){calls++}},fetch(){throw Error('network forbidden')}});
 vm.runInContext(source('a74-gallery-manual-fix.js'),ctx);assert.equal(calls,0);button.onclick();assert.equal(calls,1);
});
await test('Guest voice is blocked and duplicate module retains singleton',async()=>{
 let calls=0;const ctx=sandbox({AlphaGuestMode:true,fetch(){calls++;throw Error('network forbidden')}});vm.runInContext(source('alpha-voice.js'),ctx);
 const voice=ctx.AlphaVoice;assert.equal(await voice.speak('Test'),false);assert.equal(await voice.speakSequence(['Test']),false);assert.equal(calls,0);
 vm.runInContext(source('alpha-voice.js'),ctx);assert.strictEqual(ctx.AlphaVoice,voice);
});
await test('Stopping sequence aborts prefetch without an unhandled rejection',async()=>{
 const requests=[];let activeSource;
 class Context{constructor(){this.state='running';this.destination={}}createBuffer(){return{}}createGain(){return{gain:{},connect(){},disconnect(){}}}createBufferSource(){const item={connect(){},disconnect(){},start(){},stop(){this.onended?.()}};activeSource=item;return item}decodeAudioData(){return Promise.resolve({})}}
 const errors=[],onUnhandled=error=>errors.push(error);process.on('unhandledRejection',onUnhandled);
 try{
  const ctx=sandbox({AudioContext:Context,fetch:(url,init)=>new Promise((resolve,reject)=>{requests.push({resolve,signal:init.signal});init.signal.addEventListener('abort',()=>reject(new DOMException('aborted','AbortError')))})});vm.runInContext(source('alpha-voice.js'),ctx);
  const result=ctx.AlphaVoice.speakSequence(['one','two']);requests[0].resolve({ok:true,blob:async()=>({arrayBuffer:async()=>new ArrayBuffer(1)})});
  await new Promise(resolve=>setImmediate(resolve));assert.equal(requests.length,2);ctx.AlphaVoice.stop();assert(requests[1].signal.aborted);assert.equal(await result,false);
  await new Promise(resolve=>setImmediate(resolve));assert.equal(errors.length,0);
 }finally{process.off('unhandledRejection',onUnhandled)}
});
await test('Requests supersede stale replies, preserve latest reply',async()=>{
 const requests=[];const ctx=sandbox({fetch:(url,init)=>new Promise(resolve=>requests.push({resolve,signal:init.signal}))});vm.runInContext(source('alpha-request.js'),ctx);
 const first=ctx.AlphaRequest.json('/test',{}, {key:'same'}).catch(e=>e);const second=ctx.AlphaRequest.json('/test',{}, {key:'same'});
 assert(requests[0].signal.aborted);requests[1].resolve({ok:true,json:async()=>({fresh:true})});assert.equal((await second).fresh,true);
 requests[0].resolve({ok:true,json:async()=>({fresh:false})});assert.equal((await first).kind,'superseded');
});
await test('Request timeout, explicit cancellation, authentication and malformed JSON',async()=>{
 const timers=new Map();let next=0;const requests=[];const ctx=sandbox({setTimeout:fn=>{timers.set(++next,fn);return next},clearTimeout:id=>timers.delete(id),fetch:(url,init)=>new Promise((resolve,reject)=>{requests.push({resolve,signal:init.signal});init.signal.addEventListener('abort',()=>reject(new DOMException('aborted','AbortError')))})});vm.runInContext(source('alpha-request.js'),ctx);
 const timeout=ctx.AlphaRequest.json('/timeout').catch(e=>e);[...timers.values()][0]();assert.equal((await timeout).kind,'timeout');assert.equal(timers.size,0);
 const cancelled=ctx.AlphaRequest.json('/cancel',{}, {key:'cancel'}).catch(e=>e);ctx.AlphaRequest.cancel('cancel');assert.equal((await cancelled).kind,'cancelled');
 const auth=ctx.AlphaRequest.json('/auth').catch(e=>e);requests.at(-1).resolve({ok:false,status:401,json:async()=>{throw Error('html')}});assert.equal((await auth).kind,'auth');
 const invalid=ctx.AlphaRequest.json('/bad').catch(e=>e);requests.at(-1).resolve({ok:true,status:200,json:async()=>{throw Error('html')}});assert.equal((await invalid).kind,'invalid');
});
await test('Alpha apostrophe card uses native button and listener',()=>{
 const holder=node(),select=node();const ctx=sandbox({document:{getElementById:id=>id==='carte-lista'?holder:select,createElement:()=>node()},CARTE:[{nome:"L'Orizzonte",simbolo:'X',ciclo:'Origine'}],cicloAttivo:'Origine',aggiornaPrev(){},scrollTo(){}});
 vm.runInContext(range(source('alpha.html'),'function aggiornaCarte()','function esc(s)'),ctx);ctx.aggiornaCarte();assert.equal(holder.children[0].type,'button');assert.equal(holder.children[0].children[1].textContent,"L'Orizzonte");holder.children[0].listeners.click();assert.equal(select.value,"L'Orizzonte");
});
await test('Flight prefill replaces defaults while preserving a field edited by user',()=>{
 const nodes={};for(const id of ['r-origine','r-dest','r-mese','o-origine','o-mese'])nodes[id]=node();nodes['r-origine'].value='Milano';nodes['r-dest'].value='Tirana';nodes['r-mese'].value='2026-11';
 const ctx=sandbox({location:{search:'?source=fabbrica&from=Bruxelles&to=Roma&month=2027-01'},load:()=>null,INTENT_KEY:'test',editedFields:new Set(['r-dest']),$:id=>nodes[id],monthOf:value=>value.slice(0,7)});vm.runInContext(range(source('viaggi-pro.js'),'function prefillFromIntent()','function renderPanel()'),ctx);ctx.prefillFromIntent();assert.equal(nodes['r-origine'].value,'Bruxelles');assert.equal(nodes['r-dest'].value,'Tirana');assert.equal(nodes['r-mese'].value,'2027-01');
});
await test('Viaggi keeps latest result even when transport returns stale response',async()=>{
 const nodes={};for(const id of ['form','search-submit','search-cancel','risultati','origine','budget','giorni','solo-budget'])nodes[id]=node();const pending=[],shown=[];
 const ctx=sandbox({document:{getElementById:id=>nodes[id]},AlphaRequest:{json:()=>new Promise(resolve=>pending.push(resolve)),cancel(){},isSuperseded:()=>false},selMese:{value:''},tipiScelti:new Set(),esc:String,mostra:data=>shown.push(data.id)});
 vm.runInContext(range(source('viaggi.html'),'let searchVersion=0;','function mostra(dati)'),ctx);
 const a=nodes.form.listeners.submit({preventDefault(){}}),b=nodes.form.listeners.submit({preventDefault(){}});pending[1]({id:'new'});await b;pending[0]({id:'old'});await a;
 assert.deepEqual(shown,['new']);assert.equal(nodes['search-submit'].disabled,false);assert.equal(nodes['search-cancel'].hidden,true);
});
await test('Parti renders results when optional storage get/set throws',async()=>{
 const cancel=node(),out=node(),inp=node();let rendered=0;const ctx=sandbox({document:{getElementById:()=>cancel},AlphaRequest:{json:async()=>({origine:'Milano',voli:[{id:1}]}),cancel(){},isSuperseded:()=>false},out,inp,daBox:node(),filtriBox:node(),localStorage:{getItem(){throw Error('storage blocked')},setItem(){throw Error('storage blocked')}},disegnaFiltri(){},render(){rendered++},esc:String});
 vm.runInContext('let ultimiVoli=[],etichettaDa="",filtro=null;'+range(source('parti.html'),'let searchVersion=0;','function disegnaFiltri()'),ctx);await ctx.carica({origine:'Roma'},'Roma');assert.equal(rendered,1);assert.equal(inp.value,'Roma');assert.equal(cancel.hidden,true);
 vm.runInContext(range(source('parti.html'),"let iniziale='Milano';",'</script>'),ctx);await new Promise(resolve=>setImmediate(resolve));assert.equal(rendered,1);assert.equal(inp.value,'Milano');assert(ctx.daBox.textContent.includes('Premi Trova'));
});
await test('Manual spread undo/reset cancels pending work, clears old reading and restores deck',()=>{
 const nodes={};const get=id=>nodes[id]||(nodes[id]=node());let aborts=0,cancelled=[];const ctx=sandbox({$:get,AlphaRequest:{cancel:key=>cancelled.push(key)},stopSpeech(){},renderDeck(){},renderSpread(){},shuffle:x=>[...x],t:key=>key==='nextCard'?'{position}':key,I18N:{it:{position:{presente:'Presente',futuro:'Futuro'}}},language:'it',ORDER:[['passato'],['presente'],['futuro']]});
 vm.runInContext('let picked=[{id:1},{id:2}],pickedIndices=[0,1],cards=[{id:1},{id:2},{id:3}],deck=[],readVersion=0,followVersion=0,readingPending=true,lastReading={},readingContext={},followHistory=[{}],shareController=null,followController={abort(){aborts++}};'+range(source('tarocchi-manuale-alpha.html'),'function clearReading()','function pick(index,button)')+'\nthis.state=()=>({picked,pickedIndices,readingPending,lastReading,readingContext,followHistory,deck});',Object.assign(ctx,{aborts}));
 ctx.resetSpread(true);assert.equal(ctx.state().picked.length,1);assert.equal(ctx.state().pickedIndices.length,1);assert.equal(ctx.state().lastReading,null);assert.equal(ctx.state().readingPending,false);assert(cancelled.includes('manual-reading'));assert(cancelled.includes('manual-follow'));assert.equal(get('spread-undo').disabled,false);
 ctx.resetSpread();assert.equal(ctx.state().picked.length,0);assert.equal(ctx.state().deck.length,3);assert.equal(get('read').disabled,true);assert.equal(get('spread-undo').disabled,true);
});
await test('Reset during sharing prevents old 401 transfer and navigation',async()=>{
 let reject,transfers=0;const nodes={};const get=id=>nodes[id]||(nodes[id]=node());const ctx=sandbox({$:get,RaffaelloBridge:{request:()=>new Promise((resolve,fail)=>reject=fail)},selectedLanguage:()=> 'it',location:{href:''},sessionStorage:{setItem(){transfers++}}});
 vm.runInContext('let lastReading={lettura_id:"old",lettura:{}},readingContext={carte:[],domanda:"old",contesto:""},followHistory=[],shareController=null;'+range(source('tarocchi-manuale-alpha.html'),'async function shareWithTelegram()',"$('telegram-share').addEventListener"),ctx);
 const share=ctx.shareWithTelegram();vm.runInContext('lastReading=null;shareController.abort();',ctx);reject(Object.assign(new Error('Unauthorized'),{status:401}));await share;
 assert.equal(transfers,0);assert.equal(ctx.location.href,'');assert.equal(get('telegram-share').disabled,false);
});
await test('Guest demo counter stays bounded in session if storage is unavailable',()=>{
 const ctx=sandbox({localStorage:{getItem(){throw Error('blocked')},setItem(){throw Error('blocked')}},max:3,key:'synthetic-test'});
 vm.runInContext(range(source('alpha74-test.html'),'let pending=false','function decorate()'),ctx);assert.equal(ctx.used(),0);ctx.save(1);assert.equal(ctx.used(),1);ctx.save(4);assert.equal(ctx.used(),3);
});
console.log(JSON.stringify({passed:out.filter(x=>x.pass).length,total:out.length,results:out},null,2));
})();
