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
    talenti=card('<div class="sala-header"><span class="sala-num">Ecosistema Raffaello · persone e servizi</span><span class="stato vivo">MVP testabile</span></div><h2>Raffaello · ecosistema dei servizi</h2><p class="sotto">Una sola intelligenza di regia, molte capacità nel mondo reale.</p><p>Fabbrica, Bottega, filiera, fiducia, economia e Regia Live non sono progetti separati: sono parti di Raffaello. Chi sa fare qualcosa può trasformarlo in un servizio; chi ha un bisogno può partire da un desiderio; Raffaello collega persone, risorse e verifiche.</p><ul><li>Fabbrica dei Desideri: dall\'idea al piano</li><li>Bottega dei Talenti: capacità, richieste e reputazione</li><li>Make / Buy / Collaborate e opportunità tra persone e produttori</li><li>Regia Live durante il servizio, audit e piani B</li><li>Prezzo, margini e distribuzione del valore spiegabili</li><li>Memorabilità e budget extra sotto controllo del cliente</li></ul><p class="formula">Raffaello coordina; Fabbrica progetta; Bottega trova le persone; la filiera procura; le persone realizzano.</p><div class="link-row"><a href="raffaello.html">Capisci Raffaello in 60 secondi</a><a href="fabbrica.html">Apri la Fabbrica</a><a href="talenti.html">Apri la Bottega</a><a href="orchestratore.html">Apri la cabina di regia</a></div>','project-bottega-talenti');
    fab.insertAdjacentElement('afterend',talenti);
  } else {
    const h=talenti.querySelector('h2'); if(h) h.textContent='Raffaello · ecosistema dei servizi';
    const num=talenti.querySelector('.sala-num'); if(num) num.textContent='Ecosistema Raffaello · persone e servizi';
    const sotto=talenti.querySelector('.sotto'); if(sotto) sotto.textContent='Una sola intelligenza di regia, molte capacità nel mondo reale.';
    const ps=talenti.querySelectorAll('p'); if(ps[1]) ps[1].textContent='Fabbrica, Bottega, filiera, fiducia, economia e Regia Live non sono progetti separati: sono parti di Raffaello. Chi sa fare qualcosa può trasformarlo in un servizio; chi ha un bisogno può partire da un desiderio; Raffaello collega persone, risorse e verifiche.';
    let formula=talenti.querySelector('.formula'); if(formula) formula.textContent='Raffaello coordina; Fabbrica progetta; Bottega trova le persone; la filiera procura; le persone realizzano.';
    const links=talenti.querySelector('.link-row'); if(links) links.innerHTML='<a href="raffaello.html">Capisci Raffaello in 60 secondi</a><a href="fabbrica.html">Apri la Fabbrica</a><a href="talenti.html">Apri la Bottega</a><a href="orchestratore.html">Apri la cabina di regia</a>';
  }
}
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',mount);else mount();
})();
