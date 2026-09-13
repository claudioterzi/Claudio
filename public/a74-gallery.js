(()=>{
const N=["La Scintilla","L'Orizzonte","Il Richiamo","La Scelta","Il Passo","La Ricerca","La Soglia","L'Ignoto","La Vigilia","Il Varco","L'Incontro","L'Eco","La Fiducia","Lo Scambio","L'Alleanza","Il Desiderio","L'Attrazione","La Promessa","L'Unione","Il Noi","Il Dubbio","La Crepa","Il Conflitto","La Ferita","Il Peso","Il Tradimento","La Caduta","La Perdita","Il Distacco","Il Fondo","Il Silenzio","L'Attesa","L'Ombra","La Verità","Il Crollo","Il Fuoco","La Muta","La Rinascita","La Direzione","Il Nuovo Giorno","L'Impulso","L'Azione","La Disciplina","La Volontà","La Costruzione","La Conquista","L'Influenza","La Responsabilità","L'Eredità","Il Trono","Il Miraggio","L'Intuizione","La Domanda","La Comprensione","La Memoria","Il Simbolo","La Connessione","La Mappa","La Rivelazione","La Visione","Il Cerchio","L'Equilibrio","L'Ordine","Il Caos","La Danza","Il Tempo","La Presenza","L'Accettazione","Il Compimento","Il Mondo","L'Osservatore","La Possibilità","L'Emergenza","L'Infinito"];
const img=(i,p)=>`/images/alpha74/${String(i+1).padStart(2,'0')}/${p}-640.webp`;
function mount(){
  if(document.querySelector('.alpha-atlas'))return;
  const anchor=document.querySelector('.alpha-proofline')||document.querySelector('.wrap>header');if(!anchor)return;
  const box=document.createElement('section');box.className='alpha-atlas';box.innerHTML=`<div class="alpha-atlas-head"><div><div class="tag">ATLANTE VISIVO · ALPHA 74</div><h2>Scorri il mazzo</h2><p>Muovi le carte con il dito. Ogni immagine appartiene al Canone Alpha 74.</p></div><div class="alpha-atlas-actions"><button type="button" data-atlas-prev aria-label="Carta precedente">‹</button><button type="button" data-atlas-polarity>Luce</button><button type="button" data-atlas-next aria-label="Carta successiva">›</button></div></div><div class="alpha-atlas-track" tabindex="0" aria-label="74 carte Alpha scorrevoli"></div><div class="alpha-atlas-count"><span>01</span> / 74</div>`;
  anchor.after(box);
  const track=box.querySelector('.alpha-atlas-track');let polarity='luce';
  N.forEach((name,i)=>{const card=document.createElement('article');card.className='alpha-gallery-card';card.dataset.i=String(i);card.innerHTML=`<div class="alpha-gallery-image"><img src="${img(i,polarity)}" alt="${String(i+1).padStart(2,'0')} ${name}" loading="${i<4?'eager':'lazy'}" decoding="async"></div><div class="alpha-gallery-meta"><span>${String(i+1).padStart(2,'0')}</span><strong>${name}</strong></div>`;track.appendChild(card)});
  const cards=[...track.children],count=box.querySelector('.alpha-atlas-count span');
  function center(i){cards[Math.max(0,Math.min(cards.length-1,i))].scrollIntoView({behavior:'smooth',inline:'center',block:'nearest'})}
  let active=0;
  const observer=new IntersectionObserver(entries=>{for(const e of entries){if(e.isIntersecting&&e.intersectionRatio>.65){cards.forEach(c=>c.classList.remove('active'));e.target.classList.add('active');active=+e.target.dataset.i;count.textContent=String(active+1).padStart(2,'0')}}},{root:track,threshold:[.65,.8]});cards.forEach(c=>observer.observe(c));cards[0].classList.add('active');
  box.querySelector('[data-atlas-prev]').onclick=()=>center(active-1);box.querySelector('[data-atlas-next]').onclick=()=>center(active+1);
  box.querySelector('[data-atlas-polarity]').onclick=e=>{polarity=polarity==='luce'?'ombra':'luce';e.currentTarget.textContent=polarity==='luce'?'Luce':'Ombra';cards.forEach((c,i)=>{c.querySelector('img').src=img(i,polarity)})};
  track.addEventListener('keydown',e=>{if(e.key==='ArrowRight'){e.preventDefault();center(active+1)}if(e.key==='ArrowLeft'){e.preventDefault();center(active-1)}});
}
document.readyState==='loading'?document.addEventListener('DOMContentLoaded',mount):mount();
})();