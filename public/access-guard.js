/* Raffaello access guard — UX separation. Not a substitute for server-side authorization. */
(function(){
'use strict';
var PUBLIC_HASH_KEY='raffaello.public.code.hash.v1';
var PRIVATE_SESSION_KEY='raffaello.private.session.v1';
var privateRoute=/^\/(?:libro-idee|privato|dati|orchestratore|r3-evoluzione|r3-riprendi|home|progetti|creazioni|scritti|codice-gaia|idee|idea-os|idea-document|progetti-indice)(?:\.html)?\/?$/i;
function isPrivate(path){return privateRoute.test(path)||/^\/idee\/IDEA-\d+\/?$/i.test(path)||/^\/custode(?:\/|$)/i.test(path)}
function safeReturn(value){
  if(typeof value!=='string'||!value.startsWith('/')||value.startsWith('//')||/[\\\x00-\x1f\x7f]/.test(value))return '';
  try{
    var url=new URL(value,location.origin);
    if(url.origin!==location.origin||/^\/(?:accesso|soglia)(?:\.html)?\/?$/i.test(url.pathname))return '';
    Array.from(url.searchParams.keys()).forEach(function(key){
      if(/(?:token|password|secret|bypass|initdata|tgwebapp|^code$)/i.test(key)||(/^\/atelier(?:\.html)?\/?$/.test(url.pathname)&&/^(?:q|intenzione)$/.test(key)))url.searchParams.delete(key);
    });
    if(/(?:token|password|secret|bypass|initdata|tgwebapp|key)[^=&]*=|(?:^|[&#])code=/i.test(url.hash))url.hash='';
    return url.pathname+url.search+url.hash;
  }catch(e){return ''}
}
globalThis.R3AccessRoutes={isPrivate:isPrivate,safeReturn:safeReturn};
if(typeof globalThis.dispatchEvent==='function')globalThis.dispatchEvent(new Event('r3-access-routes-ready'));
var p=location.pathname.replace(/\/+$/,'')||'/';
var openRoutes=['/','/accesso','/accesso.html','/soglia','/soglia.html'];
if(openRoutes.indexOf(p)!==-1)return;
var requiresPrivate=isPrivate(p);
var privateOK=false,publicOK=false;
try{
  privateOK=sessionStorage.getItem(PRIVATE_SESSION_KEY)==='1';
  publicOK=Boolean(localStorage.getItem(PUBLIC_HASH_KEY));
}catch(e){}
if((requiresPrivate&&!privateOK)||(!requiresPrivate&&!privateOK&&!publicOK)){
  if(/^\/libro-idee\/?$/.test(location.pathname)){
    var bookMatch=/^#key=([A-Za-z0-9_-]{43})(?:&|$)/.exec(location.hash);
    if(bookMatch){try{sessionStorage.setItem('r3.book.pending.key.v1',bookMatch[1])}catch(_){}}
  }
  var destination=safeReturn(location.pathname+(location.search||'')+(location.hash||''))||'/';
  location.replace('/accesso?reason='+(requiresPrivate?'private':'public')+'&return='+encodeURIComponent(destination));
}
})();
