(()=>{
const COPY={
it:{title:'Le 74 carte originali',intro:'Trascina la carta per ruotarla. Tocca per passare Luce/Ombra. Trascina ai lati per scegliere un’altra carta.',tour:'▶ Presentazione AI',stop:'■ Ferma presentazione',loading:'Voce in preparazione…',unavailable:'Voce non disponibile',drag:'↔ Trascina · ruota',tap:'⤾ Tocca · Luce/Ombra',swipe:'⇆ Ai lati · cambia carta',left:'‹ scorri il mazzo',right:'scorri il mazzo ›',axes:{nord:'↑ Nord',est:'→ Est',sud:'↓ Sud',ovest:'← Ovest'},flip:'⤾ Luce / Ombra',labels:{cards:'Carte originali',dirs:'Direzioni',pol:'Polarità',states:'Stati elementari',spread:'Carte nella stesa',space:'Spazio a 7 carte'},segments:[
'Questo è Alpha 74, il Canone originale ideato e disegnato da Claudio Terzi.',
'Settantaquattro carte originali, ognuna con una propria identità simbolica.',
'Ogni carta può essere osservata in quattro direzioni. Cominciamo dal Nord.',
'Ruotando verso Est cambia il punto di osservazione del simbolo.',
'Poi Sud.',
'E infine Ovest. Quattro direzioni reali per ogni carta.',
'Ogni direzione possiede due polarità. Questa è la Luce: ciò che emerge, si apre o diventa disponibile.',
'E questa è l’Ombra: ciò che si ritrae, si complica, si nasconde o chiede di essere compreso.',
'Settantaquattro carte, per quattro direzioni, per due polarità, producono cinquecentonovantadue stati elementari.',
'La stesa può contenere da una a sette carte, e l’ordine delle carte fa parte della configurazione.',
'Con sette carte, la formula è P di settantaquattro su sette, moltiplicato per otto alla settima.',
'Il risultato è diciannove quintilioni, venti quadrilioni, novecentotredici trilioni, settecentonovantanove miliardi, quattrocentocinquantasette milioni, seicentosessantanovemila, centoventi configurazioni ordinate possibili. Non settantaquattro risposte: un linguaggio.'
]},
en:{title:'The 74 original cards',intro:'Drag the card to rotate it. Tap for Light/Shadow. Swipe at the sides to choose another card.',tour:'▶ AI presentation',stop:'■ Stop presentation',loading:'Preparing voice…',unavailable:'Voice unavailable',drag:'↔ Drag · rotate',tap:'⤾ Tap · Light/Shadow',swipe:'⇆ Sides · change card',left:'‹ browse deck',right:'browse deck ›',axes:{nord:'↑ North',est:'→ East',sud:'↓ South',ovest:'← West'},flip:'⤾ Light / Shadow',labels:{cards:'Original cards',dirs:'Directions',pol:'Polarities',states:'Elementary states',spread:'Cards in spread',space:'7-card space'},segments:[
'This is Alpha 74, the original Canon conceived and designed by Claudio Terzi.',
'Seventy-four original cards, each with its own symbolic identity.',
'Every card can be observed in four directions. We begin with North.',
'Rotating to East changes the point of view of the symbol.',
'Then South.',
'And finally West. Four real directions for every card.',
'Each direction has two polarities. This is Light: what emerges, opens, or becomes available.',
'And this is Shadow: what withdraws, becomes complex, hides, or asks to be understood.',
'Seventy-four cards times four directions times two polarities produce five hundred and ninety-two elementary states.',
'A spread can contain from one to seven cards, and card order is part of the configuration.',
'With seven cards, the formula is P of seventy-four over seven, multiplied by eight to the seventh power.',
'The result is nineteen quintillion, twenty quadrillion, nine hundred thirteen trillion, seven hundred ninety-nine billion, four hundred fifty-seven million, six hundred sixty-nine thousand, one hundred twenty ordered configurations. Not seventy-four answers: a language.'
]},
fr:{title:'Les 74 cartes originales',intro:'Faites glisser la carte pour la tourner. Touchez pour Lumière/Ombre. Glissez sur les côtés pour changer de carte.',tour:'▶ Présentation IA',stop:'■ Arrêter',loading:'Préparation de la voix…',unavailable:'Voix indisponible',drag:'↔ Glisser · tourner',tap:'⤾ Toucher · Lumière/Ombre',swipe:'⇆ Côtés · changer de carte',left:'‹ parcourir le jeu',right:'parcourir le jeu ›',axes:{nord:'↑ Nord',est:'→ Est',sud:'↓ Sud',ovest:'← Ouest'},flip:'⤾ Lumière / Ombre',labels:{cards:'Cartes originales',dirs:'Directions',pol:'Polarités',states:'États élémentaires',spread:'Cartes du tirage',space:'Espace à 7 cartes'},segments:[
'Voici Alpha 74, le Canon original conçu et dessiné par Claudio Terzi.',
'Soixante-quatorze cartes originales, chacune avec sa propre identité symbolique.',
'Chaque carte peut être observée dans quatre directions. Nous commençons par le Nord.',
'En tournant vers l’Est, le point de vue du symbole change.',
'Puis le Sud.',
'Et enfin l’Ouest. Quatre directions réelles pour chaque carte.',
'Chaque direction possède deux polarités. Voici la Lumière: ce qui émerge, s’ouvre ou devient disponible.',
'Et voici l’Ombre: ce qui se retire, se complexifie, se cache ou demande à être compris.',
'Soixante-quatorze cartes, multipliées par quatre directions et deux polarités, produisent cinq cent quatre-vingt-douze états élémentaires.',
'Un tirage peut contenir de une à sept cartes, et leur ordre fait partie de la configuration.',
'Avec sept cartes, la formule est P de soixante-quatorze sur sept, multiplié par huit puissance sept.',
'Le résultat est dix-neuf quintillions, vingt quadrillions, neuf cent treize trillions, sept cent quatre-vingt-dix-neuf milliards, quatre cent cinquante-sept millions, six cent soixante-neuf mille, cent vingt configurations ordonnées possibles. Pas soixante-quatorze réponses: un langage.'
]},
es:{title:'Las 74 cartas originales',intro:'Arrastra la carta para rotarla. Toca para Luz/Sombra. Desliza por los lados para cambiar de carta.',tour:'▶ Presentación IA',stop:'■ Detener',loading:'Preparando la voz…',unavailable:'Voz no disponible',drag:'↔ Arrastra · rota',tap:'⤾ Toca · Luz/Sombra',swipe:'⇆ Lados · cambia carta',left:'‹ recorre el mazo',right:'recorre el mazo ›',axes:{nord:'↑ Norte',est:'→ Este',sud:'↓ Sur',ovest:'← Oeste'},flip:'⤾ Luz / Sombra',labels:{cards:'Cartas originales',dirs:'Direcciones',pol:'Polaridades',states:'Estados elementales',spread:'Cartas de la tirada',space:'Espacio con 7 cartas'},segments:[
'Este es Alpha 74, el Canon original ideado y dibujado por Claudio Terzi.',
'Setenta y cuatro cartas originales, cada una con su propia identidad simbólica.',
'Cada carta puede observarse en cuatro direcciones. Empezamos por el Norte.',
'Al girar hacia el Este cambia el punto de vista del símbolo.',
'Después, Sur.',
'Y por último, Oeste. Cuatro direcciones reales para cada carta.',
'Cada dirección posee dos polaridades. Esta es la Luz: lo que emerge, se abre o se vuelve disponible.',
'Y esta es la Sombra: lo que se retrae, se complica, se oculta o pide ser comprendido.',
'Setenta y cuatro cartas por cuatro direcciones por dos polaridades producen quinientos noventa y dos estados elementales.',
'Una tirada puede contener de una a siete cartas, y su orden forma parte de la configuración.',
'Con siete cartas, la fórmula es P de setenta y cuatro sobre siete, multiplicado por ocho a la séptima.',
'El resultado es diecinueve quintillones, veinte cuatrillones, novecientos trece trillones, setecientos noventa y nueve mil millones, cuatrocientos cincuenta y siete millones, seiscientos sesenta y nueve mil, ciento veinte configuraciones ordenadas posibles. No setenta y cuatro respuestas: un lenguaje.'
]}}
;
const AXES=['nord','ovest','sud','est'];
function lang(){const v=document.getElementById('language')?.value||document.documentElement.lang||'it';const c=String(v).toLowerCase().split('-')[0];return COPY[c]?c:'it'}
function mount(){
 const box=document.querySelector('.alpha-atlas');if(!box)return setTimeout(mount,120);if(box.dataset.v2)return;box.dataset.v2='1';box.classList.add('alpha-v2');
 const track=box.querySelector('.alpha-atlas-track'),tourOld=box.querySelector('[data-atlas-tour]');if(!track||!tourOld)return;
 const tour=tourOld.cloneNode(true);tourOld.replaceWith(tour);
 const consoleBox=box.querySelector('.alpha-card-console');
 if(consoleBox&&!box.querySelector('.alpha-gesture-guide')){const g=document.createElement('div');g.className='alpha-gesture-guide';consoleBox.after(g);const side=document.createElement('div');side.className='alpha-side-swipe';side.innerHTML='<span data-side-left></span><span data-side-right></span>';track.after(side)}
 if(!box.querySelector('.alpha-edu-board')){const board=document.createElement('section');board.className='alpha-edu-board';board.innerHTML='<div class="alpha-tour-progress"><span></span></div><div class="alpha-edu-caption"></div><div class="alpha-edu-ledger"></div>';const side=box.querySelector('.alpha-side-swipe');(side||track).after(board)}
 const caption=box.querySelector('.alpha-edu-caption'),ledger=box.querySelector('.alpha-edu-ledger'),progress=box.querySelector('.alpha-tour-progress span');
 let audio=new Audio(),voiceUrl='',abort=null,ready=false,playing=false,lastScene=-1,currentLang='',sceneCuts=[];audio.preload='auto';audio.playsInline=true;
 function activeCard(){return box.querySelector('.alpha-gallery-card.active')}
 function setAxis(a){const b=box.querySelector(`[data-axis="${a}"]`);if(b)b.click()}
 function setFlip(want){const card=activeCard();if(!card)return;const has=card.classList.contains('is-flipped');if(has!==want)box.querySelector('[data-atlas-flip]')?.click()}
 function stopTour(){playing=false;audio.pause();try{audio.currentTime=0}catch(e){}tour.textContent=ready?COPY[lang()].tour:COPY[lang()].loading;tour.dataset.state=ready?'ready':'loading';box.classList.remove('touring');progress.style.width='0';lastScene=-1}
 function typeLine(key,label,value,formula=false){if(ledger.querySelector(`[data-key="${key}"]`))return;const row=document.createElement('div');row.className='alpha-edu-line'+(formula?' formula':'');row.dataset.key=key;row.innerHTML=`<small>${label}</small><strong></strong>`;ledger.append(row);const out=row.querySelector('strong');let i=0;const tick=()=>{out.textContent=value.slice(0,i++);if(i<=value.length)setTimeout(tick,22)};tick()}
 function applyScene(i){if(i===lastScene)return;lastScene=i;const c=COPY[lang()],s=c.segments[i]||'';caption.textContent=s;
  if(i===0){ledger.innerHTML='';setAxis('nord');setFlip(false)}
  if(i===1)typeLine('74',c.labels.cards,'74');
  if(i===2){typeLine('4',c.labels.dirs,'4 · ↑ N  → E  ↓ S  ← O');setAxis('nord')}
  if(i===3)setAxis('est');if(i===4)setAxis('sud');if(i===5)setAxis('ovest');
  if(i===6){typeLine('2',c.labels.pol,'2 · Luce / Ombra');setFlip(false)}
  if(i===7)setFlip(true);
  if(i===8)typeLine('592',c.labels.states,'74 × 4 × 2 = 592',true);
  if(i===9)typeLine('1-7',c.labels.spread,'1 → 7');
  if(i===10)typeLine('formula',c.labels.space,'P(74,7) × 8⁷',true);
  if(i===11)typeLine('max',c.labels.space,'19.020.913.799.457.669.120',true);
 }
 function computeCuts(c){const lens=c.segments.map(s=>s.length+18),total=lens.reduce((a,b)=>a+b,0);let acc=0;sceneCuts=lens.map(n=>{const r=acc/total;acc+=n;return r})}
 function sync(){if(!playing||!Number.isFinite(audio.duration)||!audio.duration)return;const r=Math.min(1,audio.currentTime/audio.duration);progress.style.width=(r*100).toFixed(1)+'%';let idx=0;for(let i=0;i<sceneCuts.length;i++)if(r>=sceneCuts[i])idx=i;applyScene(idx)}
 audio.addEventListener('timeupdate',sync);audio.addEventListener('ended',()=>{progress.style.width='100%';playing=false;tour.textContent=COPY[lang()].tour;tour.dataset.state='ready';box.classList.remove('touring')});
 async function prepareVoice(force=false){const l=lang(),c=COPY[l];currentLang=l;computeCuts(c);if(abort)abort.abort();abort=new AbortController();ready=false;tour.textContent=c.loading;tour.dataset.state='loading';if(voiceUrl){URL.revokeObjectURL(voiceUrl);voiceUrl=''};try{const res=await fetch('/api/tarocchi/alpha-voce',{method:'POST',headers:{'Content-Type':'application/json',Accept:'audio/mpeg'},cache:'no-store',signal:abort.signal,body:JSON.stringify({testo:c.segments.join(' '),lingua:l})});if(!res.ok)throw new Error('tts');const blob=await res.blob();voiceUrl=URL.createObjectURL(blob);audio.src=voiceUrl;audio.load();ready=true;tour.textContent=c.tour;tour.dataset.state='ready'}catch(e){if(e.name==='AbortError')return;tour.textContent=c.unavailable;tour.dataset.state='error'}}
 function updateLanguage(){const c=COPY[lang()];box.querySelector('.alpha-atlas-head h2').textContent=c.title;box.querySelector('.alpha-atlas-head p').textContent=c.intro;const g=box.querySelector('.alpha-gesture-guide');if(g)g.innerHTML=`<span><b>↔</b>${c.drag.replace('↔ ','')}</span><span><b>⤾</b>${c.tap.replace('⤾ ','')}</span><span><b>⇆</b>${c.swipe.replace('⇆ ','')}</span>`;const left=box.querySelector('[data-side-left]'),right=box.querySelector('[data-side-right]');if(left)left.textContent=c.left;if(right)right.textContent=c.right;box.querySelectorAll('[data-axis]').forEach(b=>{b.innerHTML=`<span class="axis-symbol">${c.axes[b.dataset.axis].split(' ')[0]}</span><span>${c.axes[b.dataset.axis].slice(2)}</span>`});const f=box.querySelector('[data-atlas-flip]');if(f)f.textContent=c.flip;caption.textContent=c.intro;stopTour();prepareVoice(true)}
 tour.onclick=async()=>{const c=COPY[lang()];if(playing){stopTour();return}if(!ready){tour.textContent=c.loading;prepareVoice(true);return}playing=true;lastScene=-1;ledger.innerHTML='';progress.style.width='0';tour.textContent=c.stop;tour.dataset.state='playing';box.classList.add('touring');applyScene(0);try{await audio.play()}catch(e){playing=false;tour.textContent='▶ '+(lang()==='it'?'Tocca per ascoltare':c.tour.replace(/^▶ /,''));box.classList.remove('touring')}};
 // Tactile card: drag on the card rotates one quarter-turn; tap flips Light/Shadow.
 let startX=0,startY=0,dragging=false,moved=false,stage=null;
 track.addEventListener('pointerdown',e=>{const s=e.target.closest('.alpha-gallery-card.active .alpha-gallery-stage');if(!s)return;if(playing)stopTour();stage=s;startX=e.clientX;startY=e.clientY;dragging=true;moved=false;s.classList.add('is-dragging');try{s.setPointerCapture(e.pointerId)}catch(_){} });
 track.addEventListener('pointermove',e=>{if(!dragging||!stage)return;const dx=e.clientX-startX,dy=e.clientY-startY;if(Math.abs(dx)>6||Math.abs(dy)>6)moved=true;if(Math.abs(dx)>Math.abs(dy)){e.preventDefault();const card=activeCard();if(card)card.style.setProperty('--drag-turn',Math.max(-38,Math.min(38,dx*.22))+'deg')}});
 function endGesture(e){if(!dragging||!stage)return;const dx=e.clientX-startX,dy=e.clientY-startY,card=activeCard();if(card)card.style.setProperty('--drag-turn','0deg');stage.classList.remove('is-dragging');dragging=false;stage=null;if(Math.abs(dx)<10&&Math.abs(dy)<10&&!moved){box.querySelector('[data-atlas-flip]')?.click();return}if(Math.abs(dx)>34&&Math.abs(dx)>Math.abs(dy)){const cur=box.querySelector('[data-axis].active')?.dataset.axis||'nord',i=AXES.indexOf(cur),next=dx>0?AXES[(i+1)%4]:AXES[(i+3)%4];setAxis(next)}}
 track.addEventListener('pointerup',endGesture);track.addEventListener('pointercancel',endGesture);
 let scrollTimer;track.addEventListener('scroll',()=>{clearTimeout(scrollTimer);scrollTimer=setTimeout(()=>{setAxis('nord');setFlip(false)},160)},{passive:true});
 document.getElementById('language')?.addEventListener('change',()=>setTimeout(updateLanguage,0));
 updateLanguage();
 addEventListener('beforeunload',()=>{if(abort)abort.abort();if(voiceUrl)URL.revokeObjectURL(voiceUrl)},{once:true});
}
document.readyState==='loading'?document.addEventListener('DOMContentLoaded',mount):mount();
})();