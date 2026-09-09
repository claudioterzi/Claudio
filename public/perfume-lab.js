/* Laboratorio Terzi — concept e direzione Claudio Terzi, © 2026. */
(function (root) {
  'use strict';
  const VOLUMES = [50, 100, 200];
  const PRICES = [220, 340, 590];
  function calculate(recipe, concentration, density, basis = 'ml') {
    if (!Array.isArray(recipe) || !recipe.length || recipe.some(r => !Array.isArray(r) || !Number.isFinite(r[2]) || r[2] <= 0)) throw Error('Formula incompleta.');
    if (Math.abs(recipe.reduce((s, r) => s + r[2], 0) - 100) > 1e-7 || new Set(recipe.map(r => r[1])).size !== recipe.length) throw Error('La formula deve contenere 100 parti e materie distinte.');
    if (!Number.isFinite(concentration) || concentration <= 0 || concentration > 100) throw Error('Indica una concentrazione maggiore di zero e fino al 100%.');
    if (!['ml', 'g'].includes(basis)) throw Error('Unità non valida.');
    if (basis === 'ml' && (!Number.isFinite(density) || density <= 0 || density > 5)) throw Error('Inserisci la densità misurata del prodotto finito, in g/ml.');
    return VOLUMES.map(volume => {
      const total = volume * (basis === 'g' ? 1 : density), blend = total * concentration / 100;
      return {quantity: volume, unit: basis, total, blend, support: total - blend,
        ingredients: recipe.map(r => ({n: r[1], name: r[0], grams: blend * r[2] / 100}))};
    });
  }
  function mount(host, perfume) {
    if (!host || !perfume || !perfume.ricetta) return;
    host.replaceChildren(); host.className = 'perfume-lab';
    const recipe = perfume.ricetta;
    const el = (tag, text, cls) => {const n = document.createElement(tag); if (text) n.textContent = text; if (cls) n.className = cls; return n;};
    host.append(el('p', 'IL LABORATORIO DI RAFFAELLO', 'eyebrow'), el('h2', 'La formula, nelle tue mani.'),
      el('p', 'Prepara i lotti da 50, 100 e 200 ml. Le pesate sono in grammi: i millilitri si ricavano dalla densità del prodotto finito.'));
    const controls = el('div', '', 'lab-controls'); host.append(controls);
    function field(label, control) {const box = el('label', label); box.append(control); controls.append(box); return control;}
    const basis = el('select'); for (const [v, text] of [['ml','Lotti da 50, 100 e 200 ml'],['g','Prove da 50, 100 e 200 g']]) {const o = el('option', text); o.value = v; basis.append(o);} field('Formato del lotto', basis);
    const concentration = el('input'); concentration.type = 'number'; concentration.min = '.01'; concentration.max = '100'; concentration.step = '.01'; concentration.value = '20'; field('Miscela delle preparazioni nel finito · % in massa', concentration);
    const density = el('input'); density.type = 'number'; density.min = '.001'; density.max = '5'; density.step = '.001'; density.placeholder = 'Densità misurata · g/ml'; field('Densità del prodotto finito', density);
    const support = el('select'); const empty = el('option', 'Scegli il supporto del lotto'); empty.value = ''; support.append(empty);
    const supports = perfume.organo?.supporti || [{n:44,nome:'Alcol etilico profumeria 96%'},{n:45,nome:'Dipropilenglicole (DPG)'},{n:46,nome:'Isopropil miristato (IPM)'},{n:124,nome:'Benzil benzoato'},{n:125,nome:'Trietil citrato (TEC)'},{n:285,nome:'Glucam P-20'},{n:286,nome:'Hercolyn D'}];
    for (const m of supports) {const o = el('option', m.nome); o.value = m.n + ' · ' + m.nome; support.append(o);} field('Supporto tal quale, da verificare per questa formula', support);
    host.append(el('p', 'Il 20% iniziale è un’ipotesi di progetto, modificabile: indica la miscela delle preparazioni, non la percentuale di sostanze pure. Per stimare la densità misura la massa netta di un volume noto del finito, alla temperatura di lavoro, e dividi grammi per millilitri.', 'caption'));
    host.append(el('p', 'Dichiara per ogni materia la preparazione che pesi, per esempio “tal quale” o “1% in etanolo”. Il nome o il flag di microdose non bastano a certificare una diluizione. Cambiare preparazione cambia il profumo.', 'caption'));
    const state = el('p', '', 'lab-state'); state.setAttribute('role', 'status'); host.append(state);
    const tableWrap = el('div', '', 'table-wrap'); const table = el('table'); tableWrap.append(table); host.append(tableWrap);
    const header = el('tr'); for (const label of ['Materia e parti','Preparazione pesata','50 ml','100 ml','200 ml']) header.append(el('th', label)); const thead = el('thead'); thead.append(header); table.append(thead);
    const tbody = el('tbody'); table.append(tbody); const preparations = [], cells = [];
    recipe.forEach((r, i) => {const tr = el('tr'); const name = el('td', 'N° '+r[1]+' · '+r[0]); name.append(el('small', r[2].toLocaleString('it-IT')+' parti')); tr.append(name);
      const td = el('td'), input = el('input'); input.type = 'text'; input.maxLength = 120; input.placeholder = 'Da dichiarare'; input.setAttribute('aria-label', 'Preparazione di '+r[0]); input.addEventListener('input', render); td.append(input); preparations.push(input); tr.append(td);
      cells[i] = VOLUMES.map(() => {const c = el('td','—'); tr.append(c); return c;}); tbody.append(tr);});
    const supportRow = el('tr'); supportRow.append(el('td','Supporto aggiuntivo'),el('td','Tal quale')); const supportCells = VOLUMES.map(() => {const c=el('td','—');supportRow.append(c);return c;}); tbody.append(supportRow);
    const totalRow = el('tr'); totalRow.append(el('th','Massa totale del lotto'),el('td')); const totalCells = VOLUMES.map(() => {const c=el('th','—');totalRow.append(c);return c;}); tbody.append(totalRow);
    const detail = el('p','', 'caption');host.append(detail);
    const actions = el('div','', 'lab-actions actions');host.append(actions);
    const exportButton = el('button','Scarica la scheda laboratorio','action');exportButton.type='button';actions.append(exportButton);
    const printButton = el('button','Stampa la scheda','action');printButton.type='button';actions.append(printButton);
    const priceHeading = el('h3','Il valore della tua creazione');host.append(priceHeading);
    const prices = el('div','', 'lab-prices'); VOLUMES.forEach((v,i) => {const card=el('div');card.append(el('span',v+' ml'),el('strong',PRICES[i].toLocaleString('it-IT',{style:'currency',currency:'EUR',maximumFractionDigits:0})));prices.append(card);});host.append(prices);
    host.append(el('p','Listino di progetto Terzi Parfums · prezzi fissi per formato. Il preventivo finale deve confermare materie, confezione, lavorazione e imposte; la scheda non attiva un acquisto.', 'caption'));
    host.append(el('h3','Dal progetto al lotto'));
    const steps=el('ol'); for(const text of ['Registra fornitore, lotto e preparazione effettiva di ogni materia. Verifica solubilità e documentazione tecnica della fornitura.','Prepara prima un piccolo campione in massa. Pesa le preparazioni dichiarate e il supporto con una bilancia di risoluzione adeguata; registra le pesate reali.','Valuta su mouillette, registra le modifiche e verifica stabilità e compatibilità con il flacone. La scheda non stabilisce tempi universali di macerazione.','Prima di applicare sulla pelle o vendere, verifica la formula completa nel prodotto finito, comprese le contribuzioni degli oli essenziali, e completa la valutazione di sicurezza applicabile.']) steps.append(el('li',text));host.append(steps);
    const source=el('a','Come verificare i limiti IFRA nel prodotto finito');source.href='https://ifrafragrance.org/using-the-standards';source.target='_blank';source.rel='noopener noreferrer';host.append(source);
    let current = null;
    function render() {
      density.disabled = basis.value === 'g';
      Array.from(header.children).slice(2).forEach((c,i)=>c.textContent=VOLUMES[i]+' '+basis.value);
      const c = Number(concentration.value), d = density.value.trim() ? Number(density.value) : null;
      try {current=calculate(recipe,c,d,basis.value);}
      catch(error){current=null; state.textContent=error.message+' Puoi lavorare in grammi senza conversione di volume.';}
      recipe.forEach((r,i)=>cells[i].forEach((cell,j)=>{cell.textContent=current ? current[j].ingredients[i].grams.toLocaleString('it-IT',{minimumFractionDigits:4,maximumFractionDigits:4})+' g' : '—';}));
      supportCells.forEach((cell,j)=>cell.textContent=current?current[j].support.toLocaleString('it-IT',{minimumFractionDigits:4,maximumFractionDigits:4})+' g':'—');
      totalCells.forEach((cell,j)=>cell.textContent=current?current[j].total.toLocaleString('it-IT',{maximumFractionDigits:4})+' g':'—');
      const missing=preparations.filter(n=>!n.value.trim()).length;
      if(current) state.textContent=missing ? 'Calcolo di progetto · '+missing+' preparazioni da dichiarare.' : ((!support.value&&c<100) ? 'Scegli il supporto prima di definire il lotto.' : 'Calcolo completo · formula da validare tecnicamente prima della produzione.');
      detail.textContent='Base: '+c+'% in massa di miscela; '+(basis.value==='g'?'lotti in grammi':d===null?'densità non dichiarata':'densità '+d+' g/ml')+'. Supporto: '+(support.value||'da scegliere')+'. Le pesate sono delle preparazioni indicate, non delle materie pure. Arrotondamento visuale a 0,0001 g; conserva le pesate reali.';
      exportButton.disabled=!current; printButton.disabled=!current;
    }
    for(const control of [basis,concentration,density,support])control.addEventListener('input',render);
    exportButton.onclick=()=>{if(!current)return;const documentData={schema_version:1,type:'terzi_laboratory_draft',created_at:new Date().toISOString(),name:perfume.nome||'Formula da codice',formula_code:perfume.formula_code,concentration_of_preparations_percent_mass:Number(concentration.value),density_g_ml:basis.value==='ml'?Number(density.value):null,support:support.value||null,preparations:recipe.map((r,i)=>({n:r[1],name:r[0],parts:r[2],preparation:preparations[i].value.trim()||null})),batches:current,prices_eur:VOLUMES.map((v,i)=>({ml:v,eur:PRICES[i]})),production_validated:false,attribution:'Concept e direzione: Claudio Terzi · © 2026'};const url=URL.createObjectURL(new Blob([JSON.stringify(documentData,null,2)],{type:'application/json'}));const a=el('a');a.href=url;a.download='terzi-scheda-laboratorio.json';document.body.append(a);a.click();a.remove();setTimeout(()=>URL.revokeObjectURL(url),60000);};
    printButton.onclick=()=>{if(window.TerziPrint&&document.getElementById('perfume-data')){window.TerziPrint.open('recipe');return;}document.body.classList.add('lab-print');window.addEventListener('afterprint',()=>document.body.classList.remove('lab-print'),{once:true});window.print();};
    render();
  }
  root.TerziLab={calculate,mount};
  if(typeof module!=='undefined'&&module.exports)module.exports={calculate};
  if(typeof document!=='undefined') {const start=()=>{const data=document.getElementById('perfume-data'),host=document.getElementById('perfume-lab');if(data&&host)mount(host,JSON.parse(data.textContent).record.perfume);};if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',start);else start();}
})(typeof window!=='undefined'?window:globalThis);
