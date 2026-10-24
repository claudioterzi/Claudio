const fs=require('node:fs'),path=require('node:path'),vm=require('node:vm'),assert=require('node:assert/strict'),crypto=require('node:crypto');
const root=path.resolve(__dirname,'..');
const read=name=>fs.readFileSync(path.join(root,name),'utf8');
const pro=read('public/talenti-pro.js');
const seed={service:'Fotografo',description:'Ritratti in studio',base:190,capacity:2,area:'Bruxelles',updated_at:'2026-09-01T10:00:00Z'};
const storage=new Map([['claudio.talenti.profile.v1',JSON.stringify(seed)]]);let writes=0,priceEvents=0;
const fields=Object.fromEntries(['talent','description','base','capacity','profile-status'].map(id=>[id,{value:id==='base'?'45':id==='capacity'?'3':'Esempio predefinito',dispatchEvent(){priceEvents++}}]));
const context={document:{getElementById:id=>fields[id]},localStorage:{getItem:key=>storage.get(key),setItem(key,value){writes++;storage.set(key,value)}},Event:class{},Date};
vm.createContext(context);vm.runInContext(pro.slice(0,pro.indexOf('function tokens('))+'globalThis.api={profile,restoreProfile,syncProfile};})();',context);
context.api.restoreProfile();
assert.equal(fields.talent.value,seed.service);assert.equal(fields.description.value,seed.description);assert.equal(fields.base.value,'190');assert.equal(fields.capacity.value,'2');assert.equal(writes,0,'Opening/restoring must not persist DOM defaults');assert.deepEqual(JSON.parse(storage.get('claudio.talenti.profile.v1')),seed);assert.equal(priceEvents,1);
fields.talent.value='';fields.base.value='3000';fields.capacity.value='31';context.api.syncProfile();
const edited=JSON.parse(storage.get('claudio.talenti.profile.v1'));assert.equal(edited.service,'','Explicitly clearing a field must be allowed');assert.equal(edited.base,2000);assert.equal(edited.capacity,30);assert.equal(edited.area,seed.area);assert.equal(writes,1);
storage.set('claudio.talenti.profile.v1','null');assert.doesNotThrow(()=>context.api.restoreProfile());assert.equal(writes,1,'Corrupt data fallback must not overwrite storage at open');

const spesa=read('public/spesa.html'),usedSource=spesa.match(/function consumo\(m\)[^\n]+/)[0];
for(const [value,wanted] of [[20,10],[-5,0],[4.5,4.5],['oops',0],[Infinity,0]]){
  const sandbox={st:()=>({u:value})};vm.createContext(sandbox);vm.runInContext(usedSource+'globalThis.used=consumo({n:2,ml:10});',sandbox);assert.equal(sandbox.used,wanted);assert.ok(10-sandbox.used>=0);
}

const atelier=read('public/atelier.html'),prefill=atelier.slice(atelier.indexOf('// Un collegamento precompila'),atelier.lastIndexOf('</script>'));
const atelierFields={intenzione:{value:''},famiglia:{value:''},voce:{textContent:''}};let requests=0;
vm.runInNewContext(prefill,{location:{search:'?q=Ritratto%20di%20primavera&famiglia=Agrumata'},URLSearchParams,document:{getElementById:id=>atelierFields[id]},chiediARaffaello(){requests++},setTimeout(){throw Error('No delayed submission allowed on URL arrival')}});
assert.equal(atelierFields.intenzione.value,'Ritratto di primavera');assert.equal(atelierFields.famiglia.value,'Agrumata');assert.equal(requests,0);assert.match(atelierFields.voce.textContent,/premi Chiedi/);

const manifest=JSON.parse(read('public/libro/provenienza.json')),index=JSON.parse(read('public/libro/indice.json'));
const integral=fs.readFileSync(path.join(root,'public/libro-integrale.html'));
const sha=data=>crypto.createHash('sha256').update(data).digest('hex');
assert.equal(sha(integral),manifest.source_sha256);assert.equal(integral.length,manifest.source_bytes);
assert.equal(index.perfumes.length,400);assert.deepEqual(index.perfumes.map(item=>item.n),Array.from({length:400},(_,i)=>i+1));
const original=Array.from(integral.toString('utf8').replace(/\r\n/g,'\n'));let previousEnd=null;
for(const chapter of manifest.chapters){
  if(previousEnd!==null)assert.equal(chapter.source_start_character,previousEnd,'Chapters must preserve continuous source coverage');
  const raw=original.slice(chapter.source_start_character,chapter.source_end_character).join('');
  assert.equal(sha(Buffer.from(raw)),chapter.raw_fragment_sha256);
  const derived=fs.readFileSync(path.join(root,chapter.file));assert.equal(sha(derived),chapter.derived_fragment_sha256);assert.equal(derived.toString('utf8'),raw.replace(/<(\/?)h2\b/g,'<$1h3').replace(/<(\/?)h1\b/g,'<$1h2'));
  previousEnd=chapter.source_end_character;
}
assert.ok(fs.statSync(path.join(root,'public/libro.html')).size<10000,'Default HTML should be a compact index, not all 400 sheets');
const codeLinks=text=>Array.from(text.matchAll(/href="formula\.html#(TRZ1\.[^"]+)"/g),match=>match[1]);
const chaptersText=manifest.chapters.map(chapter=>read(chapter.file)).join('');
assert.equal(codeLinks(integral.toString('utf8')).length,400);assert.deepEqual(codeLinks(chaptersText),codeLinks(integral.toString('utf8')),'All 400 original formula links remain byte-accurate and in order');
console.log('PASS: profile restoration without writes, explicit edits and bounds, five stock counterexamples, query without submission, integral hash and 12 contiguous chapter derivations / 400 perfumes.');
