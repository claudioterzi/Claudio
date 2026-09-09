const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
const html=fs.readFileSync('public/atelier.html','utf8');
const source=html.slice(html.indexOf('function chiediARaffaello('),html.indexOf('window.addEventListener("pageshow"'));
for(const crypto of [undefined,{randomUUID:()=> '12345678-1234-4234-8234-123456789abc'}]){
 const elements={voce:{},cliente:{value:''},chiedi:{disabled:false}};
 let submitted;
 const document={getElementById:id=>elements[id],body:{appendChild:()=>{}},createElement:tag=>tag==='form'?{inputs:[],appendChild(x){this.inputs.push(x)},submit(){submitted=this}}:{}};
 vm.runInNewContext(source+';chiediARaffaello(false)',{document,window:{crypto},leggi:()=>({intenzione:'Ispirato a Chanel N° 5',ondata:2,fam:null})});
 assert.ok(submitted,'Request must start without customer or crypto.randomUUID');
 assert.equal(submitted.method,'POST');assert.equal(submitted.action,'/profumo');
 assert.equal(submitted.inputs.find(x=>x.name==='q').value,'Ispirato a Chanel N° 5');
 assert.equal(submitted.inputs.find(x=>x.name==='cliente').value,'');
}
console.log('PASS: empty customer; unavailable UUID; original intention preserved.');
