const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
const html=fs.readFileSync('public/atelier.html','utf8');
const source=html.slice(html.indexOf('function chiediARaffaello('),html.indexOf('window.addEventListener("pageshow"'));
for(const crypto of [undefined,{randomUUID:()=> '12345678-1234-4234-8234-123456789abc'}]){
 const elements={voce:{},cliente:{value:''},riferimento:{value:'Chanel N° 5 Eau de Parfum\nDior J’adore'},chiedi:{disabled:false}};
 let submitted;
 const document={getElementById:id=>elements[id],body:{appendChild:()=>{}},createElement:tag=>tag==='form'?{inputs:[],appendChild(x){this.inputs.push(x)},submit(){submitted=this}}:{}};
 vm.runInNewContext(source+';chiediARaffaello(false)',{document,window:{crypto},leggi:()=>({intenzione:'Ispirato a Chanel N° 5',ondata:2,stile:'ellena',fam:null})});
 assert.ok(submitted,'Request must start without customer or crypto.randomUUID');
 assert.equal(submitted.method,'POST');assert.equal(submitted.action,'/profumo');
 assert.equal(submitted.inputs.find(x=>x.name==='q').value,'Ispirato a Chanel N° 5');
 assert.equal(submitted.inputs.find(x=>x.name==='cliente').value,'');
 assert.equal(submitted.inputs.find(x=>x.name==='ondata').value,'2');
 assert.equal(submitted.inputs.find(x=>x.name==='stile').value,'ellena');
 assert.equal(submitted.inputs.find(x=>x.name==='riferimento').value,'Chanel N° 5 Eau de Parfum\nDior J’adore');
}
assert.match(html, /<textarea id="riferimento" maxlength="1000"/);
const canonical=JSON.parse(fs.readFileSync('studio/parfums/organo_terzi_300.json','utf8')).materie;
const offline=html.slice(html.indexOf('const D = '),html.indexOf('function flacone('));
vm.runInNewContext(offline+`
 assert.equal(D.materie.length,293);
 for(const m of D.materie){const c=canonical.find(x=>x.n===m.n);assert.ok(c && c.tipo!=='SOL');assert.equal(m.nome,c.nome);}
 for(const style of Object.keys(STILI))for(const family of Object.keys(D.famiglie))for(let level=0;level<3;level++){
   const p=componi('test catalogo',family,style,level,0);
   assert.ok(p.righe.every(m=>ONDATE[level].includes(m.liv)));
   assert.equal(new Set(p.righe.map(m=>m.n)).size,p.righe.length);
   assert.equal(p.righe.reduce((total,m)=>total+m.parti,0),100);
 }
`,{assert,canonical});
console.log('PASS: POST fields, 293 catalog entries, 72 offline combinations constrained to selected levels.');
