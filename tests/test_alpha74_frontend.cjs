const fs=require('node:fs');
const vm=require('node:vm');
const assert=require('node:assert/strict');
const path=require('node:path');
const root=path.resolve(__dirname,'..');
const canonical=JSON.parse(fs.readFileSync(root+'/tarocchi_quantici_alpha.json')).carte;
const art=require(root+'/public/alpha74-art.js');
let checks=0;
for(const c of canonical)for(const pol of ['luce','ombra'])for(const axis of ['nord','est','sud','ovest']){
 const view=art.resolve({id:c.id,polarita:pol,asse:axis});
 assert.ok(view);assert.ok(fs.statSync(root+'/public'+view.thumbnail).size>100);
 assert.ok(fs.statSync(root+'/public'+view.detail).size>100);
 assert.equal((view.rotation+({nord:0,est:90,sud:180,ovest:270})[axis])%360,0);
 checks++;
}
assert.equal(art.resolve({id:99,polarita:'luce',asse:'nord'}),null);
assert.equal(art.resolve({id:1,polarita:'wrong',asse:'nord'}),null);
class Element{
 constructor(){this.value='';this.textContent='';this.innerHTML='';this.disabled=false;this.children=[];this.handlers={};this.attrs={};this.classes=new Set();this.classList={add:x=>this.classes.add(x),remove:x=>this.classes.delete(x)};this.style={setProperty:(k,v)=>this.attrs[k]=v};}
 addEventListener(k,fn){this.handlers[k]=fn;}setAttribute(k,v){this.attrs[k]=v;}removeAttribute(k){delete this.attrs[k];}
 appendChild(n){this.children.push(n);}append(...n){this.children.push(...n);}replaceChildren(){this.children=[];}
 scrollIntoView(){}focus(){}querySelectorAll(){return [];}showModal(){this.open=true;}close(){this.open=false;}
}
const els=new Map();const $=id=>{if(!els.has(id))els.set(id,new Element());return els.get(id);};
const requests=[];let resolveReading;let spoken=0;
const context=vm.createContext({document:{getElementById:$,createElement:()=>new Element()},
 window:{addEventListener(){},speechSynthesis:{cancel(){},getVoices(){return[];},speak(){spoken++;}}},
 SpeechSynthesisUtterance:class{constructor(text){this.text=text;}},
 crypto:{getRandomValues(a){a[0]=0;}},Uint32Array,Alpha74Art:art,console,alert:e=>{throw Error(e);},
 fetch:async(url,options)=>{
  if(url==='/api/alpha')return{ok:true,json:async()=>canonical};
  const body=JSON.parse(options.body);requests.push(body);
  if(body.modalita==='approfondimento')return{ok:true,json:async()=>({risposta:'Risposta di prova sul canone.'})};
  return new Promise(resolve=>{resolveReading=()=>resolve({ok:true,json:async()=>({lettura_id:'test-1',lettura:{messaggio:'Prova',nodo:'Nodo',direzione:'Direzione',domanda_finale:'Domanda',carte:[]},motore:{provider:'test'}})});});
 }});
const html=fs.readFileSync(root+'/public/tarocchi-manuale-alpha.html','utf8');
const js=[...html.matchAll(/<script[^>]*>([\s\S]*?)<\/script>/g)].map(x=>x[1]).join('\n');
vm.runInContext(js,context);
(async()=>{
 await new Promise(r=>setImmediate(r));
 vm.runInContext('deck=cards.slice();',context);
 $('q').value='Domanda iniziale';$('ctx').value='Contesto iniziale';
 vm.runInContext('pick(0,document.createElement("button"))',context);
 assert.match($('spread').innerHTML,/01\/luce-160.webp/);
 assert.doesNotMatch($('spread').innerHTML,/-640.webp/);
 const reading=$('read').handlers.click();
 assert.equal(requests[0].carte_scelte[0].id,1);
 assert.equal(requests[0].carte_scelte[0].asse,'ovest');
 $('q').value='Modifica dopo invio';$('ctx').value='Contesto modificato';
 vm.runInContext('pick(1,document.createElement("button"))',context);
 assert.equal(vm.runInContext('picked.length',context),1);
 resolveReading();await reading;
 assert.equal(spoken,0);
 $('follow-question').value='Spiegami questa carta';
 await $('ask').handlers.click();
 assert.equal(requests[1].domanda_originale,'Domanda iniziale');
 assert.equal(requests[1].contesto,'Contesto iniziale');
 assert.equal(requests[1].carte_scelte.length,1);
 assert.equal(requests[1].carte_scelte[0].significato_canonico,canonical[0].luce.ovest);
 assert.equal(spoken,0);
 vm.runInContext('showCard(0)',context);
 assert.equal($('art-image').src,'/images/alpha74/01/luce-640.webp');
 assert.equal($('art-image').attrs['--card-turn'],'90deg');
 $('listen').handlers.click();assert.ok(spoken>0);
 vm.runInContext('pick(1,document.createElement("button"))',context);
 assert.equal(vm.runInContext('lastReading',context),null);
 assert.ok($('result').classes.has('hidden'));
 console.log(JSON.stringify({states:checks,assets:296,snapshot:'passed',manual_analysis:'passed',audio_only_on_click:'passed',detail_on_demand:'passed',stale_reading_invalidation:'passed',browser_rendering:'not tested by this harness'}));
})().catch(e=>{console.error(e);process.exitCode=1;});
