/* IDEA OS — aggiunge l'accesso ai dossier HTML interattivi senza duplicare il renderer del portfolio. */
(function(){
'use strict';
function addLinks(){
  document.querySelectorAll('.idea[data-id]').forEach(function(card){
    var id=card.getAttribute('data-id');
    var actions=card.querySelector('.actions');
    if(!id||!actions||actions.querySelector('[data-interactive-dossier]'))return;
    var a=document.createElement('a');
    a.href='/idee/'+encodeURIComponent(id);
    a.textContent='Apri documento interattivo →';
    a.setAttribute('data-interactive-dossier','1');
    a.className='primary';
    actions.insertBefore(a,actions.firstChild);
  });
}
var target=null,observer=null;
function boot(){
  target=document.getElementById('ideas');
  if(!target){setTimeout(boot,60);return}
  addLinks();
  observer=new MutationObserver(addLinks);
  observer.observe(target,{childList:true,subtree:true});
}
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',boot);else boot();
})();
