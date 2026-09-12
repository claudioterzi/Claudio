/* Raffaello · Estrazione manuale guidata
   L'utente sceglie solo il dorso. Raffaello gestisce ordine, posizione, stato e rovescio.
   Claudio Terzi · C.Terzi */
(function(){
'use strict';
if(window.RaffaelloManualTarot)return;

const ORDER=[
  {pos:'passato',label:'Passato',state:'collassato'},
  {pos:'presente',label:'Presente',state:'entangled'},
  {pos:'futuro',label:'Futuro',state:'sovrapposto'},
  {pos:'ostacolo',label:'Ostacolo',state:'entangled'},
  {pos:'potenziale',label:'Potenziale',state:'sovrapposto'},
  {pos:'consiglio',label:'Consiglio',state:'collassato'},
  {pos:'esito',label:'Esito',state:'sovrapposto'}
];
const REVERSED_RATE=0.20; // "ogni tanto": circa una carta su cinque
let deck=[];
let picked=[];
let mounted=false;

function rnd(){
  try{const a=new Uint32Array(1);crypto.getRandomValues(a);return a[0]/4294967296}catch(e){return Math.random()}
}
function shuffle(xs){
  const a=xs.slice();
  for(let i=a.length-1;i>0;i--){const j=Math.floor(rnd()*(i+1));[a[i],a[j]]=[a[j],a[i]]}
  return a;
}
function slug(nome){return String(nome||'').normalize('NFD').replace(/[\u0300-\u036f]/g,'').toLowerCase().replace(/\s+/g,'_').replace(/'/g,'').replace(/[^a-z0-9_]/g,'')}
function cardImage(c){return `/cards/${String(c.indice).padStart(2,'0')}_${slug(c.nome)}.svg`}
function escapeHtml(s){return String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]))}

function prepareSlot(slot,index){
  if(!slot||index>=ORDER.length)return;
  const id=slot.id.replace('slot-','');const cfg=ORDER[index];
  const c=document.getElementById(`carta-${id}`),p=document.getElementById(`pos-${id}`),s=document.getElementById(`stato-${id}`),r=document.getElementById(`rov-${id}`);
  if(p)p.value=cfg.pos;if(s)s.value=cfg.state;
  [c,p,s,r].forEach(x=>{if(x)x.disabled=true});
  const remove=slot.querySelector('.slot-remove');if(remove)remove.style.display='none';
  slot.dataset.manual='1';slot.dataset.order=String(index+1);
  let placeholder=slot.querySelector('.manual-slot-placeholder');
  if(!placeholder){placeholder=document.createElement('div');placeholder.className='manual-slot-placeholder';slot.insertBefore(placeholder,slot.firstChild.nextSibling)}
  if(!c?.value)placeholder.innerHTML=`<strong>${index+1}. ${escapeHtml(cfg.label)}</strong><span>In attesa della tua scelta dal mazzo coperto.</span>`;
}
function prepareVisibleSlots(){[...document.querySelectorAll('.slot')].forEach((slot,i)=>prepareSlot(slot,i))}

function nextEmptySlot(){
  let slots=[...document.querySelectorAll('.slot')];
  let empty=slots.find(s=>{const id=s.id.replace('slot-','');return !document.getElementById(`carta-${id}`)?.value});
  if(!empty && slots.length<ORDER.length && typeof aggiungiSlot==='function'){
    aggiungiSlot();slots=[...document.querySelectorAll('.slot')];empty=slots[slots.length-1];prepareSlot(empty,slots.length-1);
  }
  return empty||null;
}
function configureSlot(slot,index,card,reversed){
  const id=slot.id.replace('slot-','');const cfg=ORDER[index];
  const c=document.getElementById(`carta-${id}`),p=document.getElementById(`pos-${id}`),s=document.getElementById(`stato-${id}`),r=document.getElementById(`rov-${id}`);
  if(!c||!p||!s||!r)return false;
  c.value=card.nome;p.value=cfg.pos;s.value=cfg.state;r.checked=reversed;
  [c,p,s,r].forEach(x=>x.disabled=true);
  const preview=slot.querySelector('.voce-preview');if(preview)preview.textContent=card.voce||'';
  const placeholder=slot.querySelector('.manual-slot-placeholder');if(placeholder)placeholder.remove();
  let visual=slot.querySelector('.manual-picked-preview');if(!visual){visual=document.createElement('div');visual.className='manual-picked-preview';slot.insertBefore(visual,slot.firstChild.nextSibling)}
  visual.innerHTML=`<img src="${cardImage(card)}" alt="${escapeHtml(card.nome)}" class="${reversed?'is-reversed':''}"><div><strong>${index+1}. ${escapeHtml(cfg.label)} · ${escapeHtml(card.nome)}</strong><span>${reversed?'Rovesciata':'Diritta'} · ${escapeHtml(card.voce||'')}</span></div>`;
  return true;
}
function pick(button){
  if(picked.length>=ORDER.length)return;
  const deckIndex=Number(button.dataset.deckIndex);const card=deck[deckIndex];if(!card||button.disabled)return;
  const slot=nextEmptySlot();if(!slot)return;
  const reversed=rnd()<REVERSED_RATE;
  const orderIndex=picked.length;
  if(!configureSlot(slot,orderIndex,card,reversed))return;
  picked.push({card:card.nome,reversed,position:ORDER[orderIndex].pos});
  button.disabled=true;button.classList.add('chosen');
  button.innerHTML='<span class="manual-chosen-mark">✓</span>';
  updateGuide();
}
function updateGuide(){
  const guide=document.getElementById('manual-tarot-guide');if(!guide)return;
  if(picked.length>=ORDER.length){guide.innerHTML='<strong>Stesa completa.</strong> Le 7 posizioni sono state riempite. Ora leggila.';return}
  const next=ORDER[picked.length];guide.innerHTML=`Hai scelto <strong>${picked.length}</strong> ${picked.length===1?'carta':'carte'}. La prossima verrà messa in <strong>${next.label}</strong>. Puoi fermarti quando senti che la stesa è sufficiente.`;
}
function renderDeck(){
  const grid=document.getElementById('manual-deck-grid');if(!grid)return;grid.innerHTML='';
  deck.forEach((card,i)=>{const b=document.createElement('button');b.type='button';b.className='manual-card-back';b.dataset.deckIndex=String(i);b.setAttribute('aria-label','Scegli questa carta coperta');b.innerHTML='<img src="/cards/retro.svg" alt="Carta coperta">';b.addEventListener('click',()=>pick(b));grid.appendChild(b)});
}
function reset(){location.reload()}
function hideOldFaceGallery(){
  const gallery=document.getElementById('galleria');if(gallery){gallery.classList.add('hidden');gallery.style.display='none';const head=gallery.previousElementSibling;if(head)head.style.display='none'}
}
function mount(){
  if(mounted||typeof MAZZO==='undefined'||!Array.isArray(MAZZO)||!MAZZO.length||!document.getElementById('slots'))return false;
  mounted=true;deck=shuffle(MAZZO);hideOldFaceGallery();prepareVisibleSlots();
  const slots=document.getElementById('slots');const title=slots.previousElementSibling;
  const section=document.createElement('section');section.id='manual-tarot-picker';section.innerHTML=`
    <div class="manual-head"><div><p class="manual-kicker">ESTRAZIONE MANUALE · RAFFAELLO</p><h2>Scegli soltanto il dorso.</h2><p id="manual-tarot-guide"></p></div><button type="button" id="manual-reset">Ricomincia</button></div>
    <div id="manual-deck-grid" class="manual-deck-grid" aria-label="Mazzo coperto"></div>
    <p class="manual-note">Il mazzo viene mescolato prima della prima scelta. Tu scegli la carta coperta; Raffaello la colloca nella posizione successiva e decide, in modo occasionale, se entra rovesciata.</p>`;
  if(title)title.parentNode.insertBefore(section,title);else slots.parentNode.insertBefore(section,slots);
  const style=document.createElement('style');style.textContent=`
    #manual-tarot-picker{margin:1.5rem 0 2rem;padding:1rem;background:#111116;border:1px solid #3b3322;border-radius:14px}
    .manual-head{display:flex;justify-content:space-between;gap:1rem;align-items:flex-start}.manual-kicker{font-size:.68rem;letter-spacing:.15em;color:#a88d45;margin:0 0 .25rem}.manual-head h2{font-weight:400;color:#d0b15b;margin:.1rem 0 .4rem}.manual-head p{color:#9a9388;line-height:1.5;font-size:.86rem}.manual-head button{border:1px solid #554727;background:transparent;color:#c9a84c;border-radius:999px;padding:.45rem .75rem;cursor:pointer;white-space:nowrap}.manual-deck-grid{display:grid;grid-template-columns:repeat(13,minmax(0,1fr));gap:.38rem;margin-top:1rem}.manual-card-back{appearance:none;border:1px solid #3b3427;border-radius:5px;background:#0b0b0e;padding:0;cursor:pointer;aspect-ratio:120/206;overflow:hidden;position:relative;transition:transform .16s,border-color .16s,opacity .16s}.manual-card-back:hover:not(:disabled){transform:translateY(-4px);border-color:#b99a4b}.manual-card-back img{width:100%;height:100%;object-fit:cover;display:block}.manual-card-back.chosen{border-color:#8f7739;opacity:.22;cursor:default}.manual-chosen-mark{position:absolute;inset:0;display:grid;place-items:center;color:#d6bc72;font:700 1.3rem system-ui}.manual-picked-preview .is-reversed{transform:rotate(180deg)}.manual-note{margin:.8rem 0 0;color:#716b63;font-size:.72rem;line-height:1.5}.manual-slot-placeholder{display:grid;gap:.2rem;margin:.25rem 0 .75rem;padding:.7rem;background:#0d0d11;border:1px dashed #34313a;border-radius:8px}.manual-slot-placeholder strong{color:#b99a4b}.manual-slot-placeholder span{color:#777168;font-size:.8rem}.manual-picked-preview{display:grid;grid-template-columns:72px 1fr;gap:.8rem;align-items:center;margin:.25rem 0 .85rem;padding:.65rem;background:#0d0d11;border:1px solid #2c2a30;border-radius:8px}.manual-picked-preview img{width:72px;height:124px;object-fit:cover;border-radius:5px}.manual-picked-preview strong,.manual-picked-preview span{display:block}.manual-picked-preview strong{color:#d0b15b;margin-bottom:.35rem}.manual-picked-preview span{color:#918a80;font-size:.82rem;line-height:1.4}.slot[data-manual="1"] .slot-row{display:none!important}#btn-add{display:none!important}
    @media(max-width:760px){.manual-deck-grid{grid-template-columns:repeat(8,minmax(0,1fr));gap:.3rem}}@media(max-width:480px){.manual-deck-grid{grid-template-columns:repeat(6,minmax(0,1fr));gap:.28rem}.manual-head{display:block}.manual-head button{margin-top:.65rem}.manual-picked-preview{grid-template-columns:58px 1fr}.manual-picked-preview img{width:58px;height:100px}}
  `;document.head.appendChild(style);
  document.getElementById('manual-reset').addEventListener('click',reset);renderDeck();updateGuide();
  return true;
}
function boot(){let tries=0;const timer=setInterval(()=>{tries++;if(mount()||tries>100)clearInterval(timer)},80)}
window.RaffaelloManualTarot={version:'1.1.0',order:ORDER,reversedRate:REVERSED_RATE};
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',boot);else boot();
})();
