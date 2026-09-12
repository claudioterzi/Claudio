/* Raffaello access guard — UX separation. Not a substitute for server-side authorization. */
(function(){
'use strict';
var PUBLIC_HASH_KEY='raffaello.public.code.hash.v1';
var PRIVATE_SESSION_KEY='raffaello.private.session.v1';
var p=location.pathname.replace(/\/+$/,'')||'/';
var openRoutes=['/','/accesso','/accesso.html','/soglia','/soglia.html'];
if(openRoutes.indexOf(p)!==-1)return;
var privateRoutes=[
  '/privato','/privato.html','/orchestratore','/orchestratore.html','/r3-evoluzione','/r3-evoluzione.html',
  '/home','/home.html','/progetti','/creazioni.html','/scritti','/scritti.html','/codice-gaia','/codice-gaia.html'
];
var isPrivate=privateRoutes.indexOf(p)!==-1;
var privateOK=false,publicOK=false;
try{
  privateOK=sessionStorage.getItem(PRIVATE_SESSION_KEY)==='1';
  publicOK=Boolean(localStorage.getItem(PUBLIC_HASH_KEY));
}catch(e){}
if(isPrivate&&!privateOK){location.replace('/');return}
if(!isPrivate&&!privateOK&&!publicOK){location.replace('/');return}
})();
