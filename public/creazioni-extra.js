/* Project catalog additions — Claudio Terzi · C.Terzi */
(function(){
'use strict';
function card(html,id){const d=document.createElement('div');d.className='sala';d.id=id;d.innerHTML=html;return d}
function mount(){
  const cards=Array.from(document.querySelectorAll('.sala'));
  const fab=cards.find(c=>c.querySelector('h2')?.textContent.trim()==='Fabbrica dei Desideri');
  if(!fab)return;
  let talenti=document.getElementById('project-bottega-talenti');
  if(!talenti){
    talenti=card('<div class="sala-header"><span class="sala-num">App verticale della Fabbrica</span><span class="stato vivo">MVP testabile</span></div><h2>Bottega dei Talenti</h2><p class="sotto">Una piccola società di servizi assistita da IA, costruita attorno alle capacità reali delle persone.</p><p>Chi sa fare qualcosa può trasformarlo in un servizio; chi ha un bisogno può pubblicare una richiesta. Il sistema raccoglie feedback multidimensionali, osserva costanza e domanda, suggerisce un valore economico spiegabile e collega i bisogni complessi alla Fabbrica dei Desideri.</p><ul><li>Profilo del talento e capacità settimanale</li><li>Richieste clienti e matching locale</li><li>Qualità, presentazione, puntualità, pulizia e cura valutate separatamente</li><li>Foto opzionali come supporto, mai requisito per la reputazione</li><li>Prezzo suggerito con limiti e motivazione, non aumento automatico opaco</li><li>Bridge interno Bottega ↔ Fabbrica per delineare il servizio mano a mano</li></ul><p class="formula">Talento + prove ripetute + domanda reale = valore del servizio che può crescere senza confondere il valore della persona.</p><div class="link-row"><a href="talenti.html">Apri la Bottega dei Talenti</a><a href="fabbrica.html">Apri la Fabbrica dei Desideri</a></div>','project-bottega-talenti');
    fab.insertAdjacentElement('afterend',talenti);
  }
  if(!document.getElementById('project-raffaello-orchestratore')){
    const orch=card('<div class="sala-header"><span class="sala-num">Motore trasversale</span><span class="stato vivo">MVP testabile</span></div><h2>Raffaello Orchestratore</h2><p class="sotto">Il coordinatore che vede insieme micro e macro.</p><p>Aggrega bisogni di più talenti, confronta capacità dei produttori, qualità, prezzo, impatto locale e rischio. Fa emergere collaborazioni che il singolo non vedrebbe e mantiene piani B quando la capacità o la fiducia non bastano.</p><ul><li>Domanda aggregata e capacità reale</li><li>Make / Buy / Collaborate</li><li>Acquisti collettivi e filiere locali</li><li>Impatto micro per il professionista e macro per la rete</li><li>Decisioni spiegabili con pesi modificabili</li><li>Fiducia progressiva e piano B</li></ul><p class="formula">Raffaello non sceglie al posto delle persone: rende visibili le conseguenze e propone la cooperazione migliore sostenuta dai dati.</p><div class="link-row"><a href="orchestratore.html">Apri Raffaello Orchestratore</a><a href="talenti.html">Apri Bottega</a><a href="spesa.html">Apri Dispensa</a></div>','project-raffaello-orchestratore');
    talenti.insertAdjacentElement('afterend',orch);
  }
}
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',mount);else mount();
})();
