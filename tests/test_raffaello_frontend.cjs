/* Behavioral DOM harness; not a browser rendering test. */
const assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm');
const art=require('../public/alpha74-art.js');
class Element{
 constructor(){this.children=[];this.handlers={};this.value='';this.textContent='';this.hidden=false;this.disabled=false;this.attrs={};this.style={setProperty:(k,v)=>this.attrs[k]=v};}
 addEventListener(k,f){this.handlers[k]=f;}setAttribute(k,v){this.attrs[k]=v;}
 append(...items){this.children.push(...items);}replaceChildren(){this.children=[];}focus(){}showModal(){this.open=true;}close(){this.open=false;}
}
const elements=new Map(),$=id=>{if(!elements.has(id))elements.set(id,new Element());return elements.get(id);};
const rid='a'.repeat(32),did='b'.repeat(32),calls=[];let spoken=0,resolveAnswer;
const location={search:'?lettura='+rid,pathname:'/dialogo-raffaello'};
const data={id:rid,snapshot:{domanda:'Una lettura',carte:[{id:1,carta:'Carta canonica',asse:'est',polarita:'ombra',posizione_label:'Presente',significato_canonico:'Significato'}],lettura:{messaggio:'Testo iniziale'},cronologia:[]},cronologia:[]};
const window={speechSynthesis:{cancel(){},speak(){spoken++;}},addEventListener(){}};
const ctx=vm.createContext({window,location,history:{replaceState(){}},URLSearchParams,AbortController,setTimeout,clearTimeout,
 crypto:{randomUUID:()=> 'web-question-1'},sessionStorage:{getItem(){return null;},removeItem(){}},
 SpeechSynthesisUtterance:class{constructor(text){this.text=text;}},speechSynthesis:window.speechSynthesis,
 document:{getElementById:$,createElement:()=>new Element(),createTextNode:text=>({textContent:text}),addEventListener(){}},Alpha74Art:art,
 fetch:async(url,options)=>{
   calls.push({url,...options});let value;
   if(url.endsWith('/status'))value={configured:true};
   else if(url.endsWith('/session'))value={cronologia:[]};
   else if(url.endsWith('/readings/'+rid))value=data;
   else if(url.endsWith('/readings'))value={letture:[{id:rid,domanda:'Una lettura',carte:['Carta canonica']}]};
   else if(url.endsWith('/drafts'))value={id:did};
   else if(url.endsWith('/analyze'))return new Promise(resolve=>{resolveAnswer=()=>resolve({ok:true,json:async()=>({risposta:'La risposta',richiesta_id:did})});});
   else throw new Error('Unexpected URL '+url);
   return {ok:true,json:async()=>value};
 }});
vm.runInContext(fs.readFileSync('public/raffaello-bridge.js','utf8'),ctx);
ctx.RaffaelloBridge=window.RaffaelloBridge;
vm.runInContext(fs.readFileSync('public/dialogo-raffaello.js','utf8'),ctx);
const tick=()=>new Promise(resolve=>setImmediate(resolve));
(async()=>{
 await tick();
 assert.equal($('reading').hidden,false);assert.equal($('reading-title').textContent,'Una lettura');
 const button=$('cards').children[0].children[0],img=button.children[0];
 assert.equal(img.src,'/images/alpha74/01/ombra-160.webp');assert.equal(img.attrs['--turn'],'-90deg');
 assert.equal($('large-card').src,undefined);assert.equal(spoken,0);
 button.handlers.click();assert.equal($('large-card').src,'/images/alpha74/01/ombra-640.webp');
 assert.equal(calls.filter(c=>c.method==='POST').length,0);
 $('question').value='Una domanda libera';
 const work=$('question-form').handlers.submit({preventDefault(){}});await tick();
 assert.equal($('analyze').disabled,true);assert.equal(spoken,0);
 const draft=calls.find(c=>c.url.endsWith('/drafts'));
 assert.equal(JSON.parse(draft.body).lettura_id,rid);assert.equal(draft.headers['X-Raffaello'],'1');
 resolveAnswer();await work;assert.equal($('thread').children.length,1);assert.equal(spoken,0);
 $('listen').handlers.click();assert.equal(spoken,1);
 // Navigation while a request is running must not attach it to a different context.
 $('question').value='Una seconda domanda';const second=$('question-form').handlers.submit({preventDefault(){}});await tick();
 $('general').handlers.click();await tick();resolveAnswer();await second;
 assert.equal($('thread').children.length,0);assert.equal($('reading').hidden,true);
 console.log('Raffaello DOM flow: manual analysis, private request, lazy card detail, manual audio, stale-result isolation passed. Browser rendering not covered.');
})().catch(error=>{console.error(error);process.exitCode=1;});
