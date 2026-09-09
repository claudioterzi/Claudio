'use strict';
const form=document.getElementById('decode-form'),input=document.getElementById('code'),statusNode=document.getElementById('status'),result=document.getElementById('result');
async function digest(text){const hash=await crypto.subtle.digest('SHA-256',new TextEncoder().encode(text));return Array.from(new Uint8Array(hash),b=>b.toString(16).padStart(2,'0')).join('');}
let requestId=0;
form.addEventListener('submit',async e=>{
 e.preventDefault();const id=++requestId;result.replaceChildren();statusNode.textContent='Verifico il codice…';
 try{
  const code=input.value.trim();if(code.length>10000)throw Error('Codice troppo lungo.');
  const [version,revision,payload,checksum,...extra]=code.split('.');
  if(extra.length||version!=='TRZ1'||!/^\w{16}$/.test(revision)||!/^\d+:\d+:[TCFS]:[01](-\d+:\d+:[TCFS]:[01])*$/.test(payload))throw Error('Formato del codice non valido.');
  if((await digest([version,revision,payload].join('.'))).slice(0,12)!==checksum)throw Error('Codice incompleto o modificato: controlla la copia.');
  const response=await fetch('formule/organo-'+revision+'.json');if(!response.ok)throw Error('Versione del catalogo non disponibile.');
  const raw=await response.text();if((await digest(raw)).slice(0,16)!==revision)throw Error('Il catalogo non corrisponde al codice.');
  const materials=new Map(JSON.parse(raw).materie.map(m=>[m.n,m]));
  const rows=payload.split('-').map(s=>{const [n,q,l,m]=s.split(':');return {material:materials.get(Number(n)),q:Number(q),l,m};});
  if(rows.some(r=>!r.material||!Number.isSafeInteger(r.q)||r.q<=0)||rows.reduce((s,r)=>s+r.q,0)!==1000)throw Error('Essenze o totale non validi.');
  const grams=Number(document.getElementById('quantity').value);if(!Number.isFinite(grams)||grams<=0||grams>100000)throw Error('Quantità non valida.');
  if(id!==requestId)return;
  const table=document.createElement('table');const head=document.createElement('tr');
  for(const title of ['Essenza','Nota','Parti','Grammi','Indicazione originale']){const th=document.createElement('th');th.textContent=title;head.append(th);}const thead=document.createElement('thead');thead.append(head);table.append(thead);const tbody=document.createElement('tbody');
  for(const r of rows){const tr=document.createElement('tr');for(const value of [r.material.n+' · '+r.material.nome,{T:'Testa',C:'Cuore',F:'Fondo',S:'Scia'}[r.l],(r.q/10).toLocaleString('it-IT'),(grams*r.q/1000).toLocaleString('it-IT',{maximumFractionDigits:4}),r.m==='1'?'Microdose: 1% (catalogo)':'—']){const td=document.createElement('td');td.textContent=value;tr.append(td);}tbody.append(tr);}table.append(tbody);result.append(table);statusNode.textContent='Formula ricostruita · '+rows.length+' voci · totale 100 parti. Quantità arrotondate a 4 decimali.';
 }catch(error){if(id===requestId){result.replaceChildren();statusNode.textContent=error.message;}}
});
if(location.hash.length>1){try{input.value=decodeURIComponent(location.hash.slice(1));form.requestSubmit();}catch(_){statusNode.textContent='Codice nel collegamento non valido.';}}
