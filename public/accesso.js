/* Raffaello access gateway — Claudio Terzi · C.Terzi
   UX split only. Private confidentiality must ultimately rely on server-side auth/private infrastructure. */
(function(){
'use strict';
var OWNER_HASH='8d81f19b997ea6e0e4032eb9b33d8cbeb488aa4dd98ac932610bc31d923183ff';
var PUBLIC_HASH_KEY='raffaello.public.code.hash.v1';
var PUBLIC_ID_KEY='raffaello.public.id.v1';
var PRIVATE_SESSION_KEY='raffaello.private.session.v1';
var MODE_KEY='raffaello.access.mode.v1';
var form=document.getElementById('access-form');
var input=document.getElementById('access-code');
var status=document.getElementById('access-status');
var newCode=document.getElementById('new-code');
var forget=document.getElementById('forget-code');
function norm(v){return (v||'').trim().toLowerCase()}
function hex(buf){return Array.from(new Uint8Array(buf)).map(function(b){return b.toString(16).padStart(2,'0')}).join('')}
function hash(v){
  var data=new TextEncoder().encode(norm(v));
  return crypto.subtle.digest('SHA-256',data).then(hex);
}
function setStatus(msg,kind){status.textContent=msg;status.className='status '+(kind||'')}
function enterPublic(h){
  try{
    localStorage.setItem(PUBLIC_HASH_KEY,h);
    localStorage.setItem(PUBLIC_ID_KEY,'R-'+h.slice(0,10).toUpperCase());
    localStorage.setItem(MODE_KEY,'public');
    sessionStorage.removeItem(PRIVATE_SESSION_KEY);
  }catch(e){}
  location.replace('/raffaello.html');
}
function enterPrivate(){
  try{
    sessionStorage.setItem(PRIVATE_SESSION_KEY,'1');
    localStorage.setItem(MODE_KEY,'private');
  }catch(e){}
  location.replace('/privato.html');
}
form.addEventListener('submit',function(e){
  e.preventDefault();
  var code=norm(input.value);
  if(code.length<4){setStatus('Scegli un codice di almeno 4 caratteri.','bad');return}
  if(!crypto||!crypto.subtle){setStatus('Questo browser non supporta la verifica sicura del codice.','bad');return}
  setStatus('Verifico…','');
  hash(code).then(function(h){
    if(h===OWNER_HASH){enterPrivate();return}
    var saved='';
    try{saved=localStorage.getItem(PUBLIC_HASH_KEY)||''}catch(e){}
    if(saved&&saved!==h){
      setStatus('Su questo dispositivo esiste già un altro codice pubblico. Usa “Scegli un nuovo codice pubblico” per sostituirlo.','bad');
      return;
    }
    enterPublic(h);
  }).catch(function(){setStatus('Non riesco a verificare il codice. Riprova.','bad')});
});
newCode.addEventListener('click',function(){
  try{localStorage.removeItem(PUBLIC_HASH_KEY);localStorage.removeItem(PUBLIC_ID_KEY);localStorage.removeItem(MODE_KEY)}catch(e){}
  input.value='';input.focus();setStatus('Ora puoi scegliere un nuovo codice pubblico.','good');
});
forget.addEventListener('click',function(){
  try{localStorage.removeItem(PUBLIC_HASH_KEY);localStorage.removeItem(PUBLIC_ID_KEY);localStorage.removeItem(MODE_KEY);sessionStorage.removeItem(PRIVATE_SESSION_KEY)}catch(e){}
  input.value='';input.focus();setStatus('Accesso locale cancellato da questo dispositivo.','good');
});
try{
  var existing=localStorage.getItem(PUBLIC_ID_KEY);
  if(existing)setStatus('Questo dispositivo ha già un accesso pubblico '+existing+'. Inserisci lo stesso codice per continuare.','');
}catch(e){}
})();
