/* Stampe personali Terzi · © 2026 Claudio Terzi. */
(function () {
  'use strict';
  const LABELS={recipe:'Ricetta e dosi',label:'Etichetta',inspiration:'Ispirazione e dedica'};
  const CSS=`*{box-sizing:border-box}body{margin:0;background:#f1eee8;color:#191919;font:15px/1.55 Georgia,serif}
  .print-toolbar{display:flex;gap:10px;flex-wrap:wrap;position:sticky;top:0;background:#17202a;padding:16px;z-index:1}
  .print-toolbar button{font:15px system-ui;padding:12px;border:1px solid #ad996a;background:#17202a;color:#fff;cursor:pointer}
  .print-paper{width:min(100%,210mm);margin:24px auto;background:white;padding:18mm;overflow-wrap:anywhere;color-scheme:light}
  .print-paper :is(h1,h2,h3,p,td,th,small,.eyebrow,.caption,.intention){color:#191919}.print-paper .formula{margin:0;padding:0;border:0}
  .print-paper h1{font-size:28pt;line-height:1.15;font-weight:400;margin:12px 0}.print-paper h2{font-size:16pt}.print-paper h3{font-size:12pt}
  .print-paper p,.print-paper li{font-size:11pt}.print-paper a{color:#222}.print-paper img{display:block;width:100%;max-height:80mm;object-fit:contain}
  .print-paper table{width:100%;border-collapse:collapse;font-size:9pt;table-layout:auto}.print-paper th,.print-paper td{border-bottom:1px solid #bbb;padding:6px;text-align:left}
  .print-paper small{display:block;font-size:8pt}.print-paper tr{break-inside:avoid}.print-paper code{font-size:8pt;overflow-wrap:anywhere}
  .print-paper .print-footer{margin-top:24px;border-top:1px solid #bbb;padding-top:12px;font-size:8pt}
  .print-paper .print-brand{letter-spacing:.18em;font-size:10pt}.print-paper .print-dedication{font-style:italic}.print-paper .table-wrap{overflow:visible}
  .print-paper.label{width:75mm;max-width:100%;padding:8mm;text-align:center;border:1px solid #999}.print-paper.label h1{font-size:20pt}.print-paper.label p{font-size:9pt}
  @media(max-width:600px){.print-paper{padding:20px;margin:12px auto}.print-paper table{font-size:8pt}.print-paper th,.print-paper td{padding:4px}}
  @media print{@page{margin:12mm}body{background:white!important;color:black!important}body>*{display:none!important}body>#terzi-print-root{display:block!important;position:static!important;overflow:visible!important;background:white!important;color:black!important}
  #terzi-print-root .print-toolbar{display:none!important}.print-paper{width:100%;margin:0;padding:0;box-shadow:none}.print-paper.label{width:75mm;padding:8mm}.print-paper a{text-decoration:none}body{overflow:visible!important}}`;
  const el=(tag,text)=>{const n=document.createElement(tag);if(text)n.textContent=text;return n;};
  function cleanClone(source) {
    if(!source)return null;const copy=source.cloneNode(true);
    copy.querySelectorAll('button,script,iframe,.lab-actions,.lab-controls,.actions').forEach(n=>n.remove());
    copy.querySelectorAll('[id]').forEach(n=>n.removeAttribute('id'));copy.removeAttribute('id');
    copy.querySelectorAll('input').forEach(n=>{const original=source.querySelector('[aria-label="'+CSSescape(n.getAttribute('aria-label')||'')+'"]');n.replaceWith(el('span',original?.value||n.value||'Non dichiarata'));});
    copy.querySelectorAll('img').forEach(n=>{n.src=new URL(n.getAttribute('src'),location.href).href;n.removeAttribute('srcset');});
    copy.querySelectorAll('a').forEach(n=>n.href=new URL(n.getAttribute('href'),location.href).href);
    copy.querySelectorAll('details').forEach(n=>n.open=true);return copy;
  }
  const CSSescape=value=>value.replace(/\\/g,'\\\\').replace(/"/g,'\\"');
  function open(kind) {
    if(!LABELS[kind])return;
    const node=document.getElementById('perfume-data');if(!node)return;
    const data=JSON.parse(node.textContent),p=data.record.perfume;
    document.getElementById('terzi-print-root')?.remove();
    const previousFocus=document.activeElement,root=el('div');root.id='terzi-print-root';root.setAttribute('role','dialog');root.setAttribute('aria-modal','true');root.setAttribute('aria-label','Anteprima · '+LABELS[kind]);
    const style=el('style');style.textContent=CSS;root.append(style);
    const toolbar=el('div');toolbar.className='print-toolbar';
    const go=el('button','Stampa / Salva PDF'),download=el('button','Scarica versione stampabile'),close=el('button','Chiudi anteprima');
    [go,download,close].forEach(b=>{b.type='button';toolbar.append(b);});root.append(toolbar);
    const paper=el('article');paper.className='print-paper '+kind;
    const brand=el('p','TERZI PARFUMS');brand.className='print-brand';paper.append(brand,el('h1',p.nome));
    if(data.customer)paper.append(el('p','Creato per '+data.customer));
    if(data.dedication){const d=el('p',kind==='label'?'Una creazione dedicata a te.':data.dedication);d.className='print-dedication';paper.append(d);}
    if(kind==='recipe') {
      paper.append(el('h2',LABELS[kind]));const formula=cleanClone(document.querySelector('.formula'));if(formula)paper.append(formula);
      const lab=document.getElementById('perfume-lab');if(lab){paper.append(el('h2','Lotti di progetto'));for(const source of [lab.querySelector('.lab-state'),lab.querySelector('table'),lab.querySelector('.table-wrap')?.nextElementSibling]){const copy=cleanClone(source);if(copy)paper.append(copy);}}
      if(p.formula_code){paper.append(el('p','Codice per ricostruire la formula'),el('code',p.formula_code));}
    } else if(kind==='inspiration') {
      paper.append(el('h2',LABELS[kind]));const intention=cleanClone(document.querySelector('.intention'));if(intention)paper.append(intention);
      for(const label of ['Dalla foto al profumo','La fotografia di Claudio','Gusti del cliente','Ricerca del riferimento']){const copy=cleanClone(document.querySelector('[aria-label="'+label+'"]'));if(copy)paper.append(copy);}
      paper.append(el('h2','Il carattere'),el('p',p.concept||''));
      if(p.ragionamento)paper.append(el('h2','La composizione'),el('p',p.ragionamento));
    } else {paper.append(el('p',p.fam||''));paper.append(el('p',data.serial||'CREAZIONE · BOZZA'));}
    const footer=el('p','Concept e direzione creativa: Claudio Terzi · © 2026 Claudio Terzi. '+(kind==='label'?'Etichetta di progetto.':'Formula di progetto: preparazioni, forniture e sicurezza da validare prima della produzione.'));
    footer.className='print-footer';paper.append(footer);root.append(paper);document.body.append(root);document.body.classList.add('terzi-print-open');
    close.onclick=()=>{root.remove();document.body.classList.remove('terzi-print-open');previousFocus?.focus();};
    root.addEventListener('keydown',event=>{if(event.key==='Escape'){event.preventDefault();close.click();}if(event.key==='Tab'){const nodes=Array.from(root.querySelectorAll('button,a[href]'));const i=nodes.indexOf(document.activeElement);if(event.shiftKey&&i===0){event.preventDefault();nodes.at(-1)?.focus();}else if(!event.shiftKey&&i===nodes.length-1){event.preventDefault();nodes[0]?.focus();}}});
    go.onclick=()=>window.print();
    download.onclick=async()=>{
      download.disabled=true;
      try {const copy=paper.cloneNode(true);for(const img of copy.querySelectorAll('img')){try{const response=await fetch(img.src);if(response.ok){const blob=await response.blob();img.src=await new Promise((resolve,reject)=>{const reader=new FileReader();reader.onload=()=>resolve(reader.result);reader.onerror=reject;reader.readAsDataURL(blob);});}}catch{}}
        const doc=document.implementation.createHTMLDocument(p.nome+' · '+LABELS[kind]);doc.documentElement.lang='it';const meta=doc.createElement('meta');meta.name='viewport';meta.content='width=device-width,initial-scale=1';doc.head.append(meta);const s=doc.createElement('style');s.textContent=CSS;doc.head.append(s);const wrapper=doc.createElement('main');wrapper.id='terzi-print-root';wrapper.append(copy);doc.body.append(wrapper);
        const url=URL.createObjectURL(new Blob(['<!doctype html>\n'+doc.documentElement.outerHTML],{type:'text/html;charset=utf-8'}));const a=el('a');a.href=url;a.download='terzi-'+kind+'-'+(p.nome||'creazione').normalize('NFKD').replace(/[^a-z0-9]+/gi,'-').slice(0,60)+'.html';document.body.append(a);a.click();a.remove();setTimeout(()=>URL.revokeObjectURL(url),60000);
      } finally {download.disabled=false;}
    };go.focus();
  }
  window.TerziPrint={open};
})();
