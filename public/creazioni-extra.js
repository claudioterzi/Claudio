/* Project catalog additions — Claudio Terzi · C.Terzi */
(function(){
'use strict';
function card(html,id){const d=document.createElement('div');d.className='sala';d.id=id;d.innerHTML=html;return d}
function mount(){
  const cards=Array.from(document.querySelectorAll('.sala'));
  const fab=cards.find(c=>c.querySelector('h2')?.textContent.trim()==='Fabbrica dei Desideri');
  if(!fab)return;
  document.getElementById('project-raffaello-orchestratore')?.remove();
  let talenti=document.getElementById('project-bottega-talenti');
  if(!talenti){
    talenti=card('<div class="sala-header"><span class="sala-num">Ecosistema Raffaello · persone e servizi</span><span class="stato vivo">MVP testabile</span></div><h2>Bottega dei Talenti</h2><p class="sotto">Le persone sono le mani di Raffaello nel mondo reale.</p><p>Chi sa fare qualcosa può trasformarlo in un servizio; chi ha un bisogno può pubblicare una richiesta. Raffaello è il motore trasversale: collega Fabbrica, Bottega, filiera, fiducia, economia e regia live senza diventare un progetto separato.</p><ul><li>Profilo del talento, capacità e disponibilità</li><li>Richieste clienti e matching locale</li><li>Qualità, reputazione e fiducia per singola capacità</li><li>Make / Buy / Collaborate e opportunità tra persone e produttori</li><li>Regia live durante il servizio, audit e piani B</li><li>Prezzo, margini e distribuzione del valore spiegabili</li></ul><p class="formula">Raffaello coordina; Fabbrica progetta; Bottega trova le persone; la filiera procura; le persone realizzano.</p><div class="link-row"><a href="fabbrica.html">Apri la Fabbrica</a><a href="talenti.html">Apri la Bottega</a><a href="orchestratore.html">Apri la cabina di regia di Raffaello</a></div>','project-bottega-talenti');
    fab.insertAdjacentElement('afterend',talenti);
  } else {
    const num=talenti.querySelector('.sala-num'); if(num) num.textContent='Ecosistema Raffaello · persone e servizi';
    const sotto=talenti.querySelector('.sotto'); if(sotto) sotto.textContent='Le persone sono le mani di Raffaello nel mondo reale.';
    const p=talenti.querySelectorAll('p')[1]; if(p) p.textContent='Chi sa fare qualcosa può trasformarlo in un servizio; chi ha un bisogno può pubblicare una richiesta. Raffaello è il motore trasversale: collega Fabbrica, Bottega, filiera, fiducia, economia e regia live senza diventare un progetto separato.';
    let formula=talenti.querySelector('.formula'); if(formula) formula.textContent='Raffaello coordina; Fabbrica progetta; Bottega trova le persone; la filiera procura; le persone realizzano.';
    const links=talenti.querySelector('.link-row'); if(links) links.innerHTML='<a href="fabbrica.html">Apri la Fabbrica</a><a href="talenti.html">Apri la Bottega</a><a href="orchestratore.html">Apri la cabina di regia di Raffaello</a>';
  }
}
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',mount);else mount();
})();
