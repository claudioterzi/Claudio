/* R3∞ automatic cross-device persistence — Claudio Terzi · C.Terzi */
(function(){
'use strict';
var API='/api/r3-sync';
var TOKEN='r3.sync.device_token.v1';
var DEVICE='r3.sync.device_meta.v1';
var busy=false,queued=false,timer=null;

function getToken(){try{return localStorage.getItem(TOKEN)||''}catch(e){return ''}}
function setToken(value,device){try{localStorage.setItem(TOKEN,value);localStorage.setItem(DEVICE,JSON.stringify(device||{}))}catch(e){}}
function clearToken(){try{localStorage.removeItem(TOKEN);localStorage.removeItem(DEVICE)}catch(e){}}
function panel(){
  var existing=document.getElementById('r3-sync-panel');
  if(existing)return existing;
  var anchor=document.getElementById('r3-ledger-list')||document.getElementById('r3-memory-form');
  if(!anchor)return null;
  var box=document.createElement('section');
  box.id='r3-sync-panel';
  box.innerHTML='<p class="kicker">R3_SYNC_SERVER</p><h2>Persistenza cross-device.</h2>'+
    '<p class="muted">Redis persistente + autenticazione per dispositivo. Le catene divergenti non vengono fuse alla cieca.</p>'+
    '<div class="toolbar"><button class="button" id="r3-sync-now" type="button">Sincronizza ora</button>'+
    '<button class="button secondary" id="r3-sync-enroll" type="button">Attiva questo dispositivo</button>'+
    '<button class="button secondary" id="r3-sync-revoke" type="button">Disconnetti dispositivo</button></div>'+
    '<form id="r3-sync-auth" hidden style="margin-top:1rem"><div class="field"><label>Password proprietaria server</label>'+
    '<input id="r3-sync-password" type="password" autocomplete="current-password" maxlength="1024"></div>'+
    '<button class="button" type="submit">Autorizza e sincronizza</button></form>'+
    '<div id="r3-sync-status" class="statusline">Controllo stato…</div>';
  anchor.parentNode.insertBefore(box,anchor.nextSibling);
  return box;
}
function status(message){var el=document.getElementById('r3-sync-status');if(el)el.textContent=message}
function authHeaders(){var t=getToken();return t?{'Authorization':'Bearer '+t}:{}}
async function call(path,options){
  options=options||{};
  var headers=Object.assign({'Accept':'application/json'},authHeaders(),options.headers||{});
  if(options.body&&!headers['Content-Type'])headers['Content-Type']='application/json';
  var response=await fetch(API+(path||''),Object.assign({cache:'no-store',credentials:'same-origin'},options,{headers:headers}));
  var data={};
  try{data=await response.json()}catch(e){}
  return {response:response,data:data};
}
async function enroll(password){
  var body=JSON.stringify({password:password,device_name:(navigator.platform||'browser')+' · '+(new Date()).toISOString().slice(0,10)});
  var result=await call('/enroll',{method:'POST',body:body,headers:{'Content-Type':'application/json'}});
  if(!result.response.ok)throw new Error(result.data.error||('HTTP '+result.response.status));
  setToken(result.data.token,result.data.device);
  status('Dispositivo autorizzato · avvio sincronizzazione…');
  return syncOnce(true);
}
async function revoke(){
  if(!getToken()){clearToken();renderAuth();return}
  try{await call('/revoke',{method:'POST'})}catch(e){}
  clearToken();renderAuth();status('Dispositivo disconnesso. Il ledger locale resta intatto.');
}
function renderAuth(){
  var enabled=!!getToken();
  var enrollButton=document.getElementById('r3-sync-enroll');
  var revokeButton=document.getElementById('r3-sync-revoke');
  var nowButton=document.getElementById('r3-sync-now');
  if(enrollButton)enrollButton.hidden=enabled;
  if(revokeButton)revokeButton.hidden=!enabled;
  if(nowButton)nowButton.disabled=!enabled;
  var form=document.getElementById('r3-sync-auth');
  if(form&&!enabled)form.hidden=true;
  if(!enabled)status('Sync server pronta: autorizza questo dispositivo una volta.');
}
function sameHead(events,head){return (events.length?events[events.length-1].hash:null)===head}
async function syncOnce(force){
  if(!getToken()){renderAuth();return {status:'not_enrolled'}}
  if(!window.R3Memory){status('Motore memoria non ancora pronto.');return {status:'not_ready'}}
  if(busy){queued=true;return {status:'queued'}}
  busy=true;
  try{
    var verified=await window.R3Memory.verify();
    if(!verified.ok)throw new Error('catena locale non valida: '+verified.reason);
    for(var attempt=0;attempt<3;attempt++){
      var remote=await call('',{method:'GET'});
      if(remote.response.status===401){clearToken();renderAuth();throw new Error('autorizzazione dispositivo scaduta o revocata')}
      if(!remote.response.ok)throw new Error(remote.data.error||('GET HTTP '+remote.response.status));
      var merge=await window.R3Memory.syncRemote(remote.data.events||[]);
      if(merge.status==='diverged'){
        status('CONFLITTO BLOCCATO · due catene divergenti conservate; nessuna fusione automatica.');
        return merge;
      }
      var local=window.R3Memory.load();
      if(local.length===(remote.data.events||[]).length&&sameHead(local,remote.data.head)){
        status('Sincronizzato · '+local.length+' eventi · revisione server '+remote.data.revision);
        return {status:'synced',count:local.length,revision:remote.data.revision};
      }
      var pushed=await call('',{
        method:'PUT',
        body:JSON.stringify({base_revision:remote.data.revision,base_head:remote.data.head,events:local}),
        headers:{'Content-Type':'application/json'}
      });
      if(pushed.response.status===409)continue;
      if(!pushed.response.ok)throw new Error(pushed.data.error||('PUT HTTP '+pushed.response.status));
      status('Sincronizzato · '+local.length+' eventi · revisione server '+pushed.data.revision);
      return {status:'pushed',count:local.length,revision:pushed.data.revision};
    }
    throw new Error('concorrenza elevata: nuovo tentativo automatico programmato');
  }catch(e){
    status('Sync sospesa · '+(e&&e.message?e.message:'errore'));
    return {status:'error',error:String(e&&e.message||e)};
  }finally{
    busy=false;
    if(queued){queued=false;schedule(250)}
  }
}
function schedule(delay){if(timer)clearTimeout(timer);timer=setTimeout(function(){syncOnce(false)},delay||800)}
function bind(){
  panel();renderAuth();
  var now=document.getElementById('r3-sync-now');
  if(now)now.addEventListener('click',function(){syncOnce(true)});
  var enrollButton=document.getElementById('r3-sync-enroll');
  if(enrollButton)enrollButton.addEventListener('click',function(){
    var form=document.getElementById('r3-sync-auth');if(form)form.hidden=false;
    var input=document.getElementById('r3-sync-password');if(input)input.focus();
  });
  var form=document.getElementById('r3-sync-auth');
  if(form)form.addEventListener('submit',async function(ev){
    ev.preventDefault();
    var input=document.getElementById('r3-sync-password');
    var password=input?input.value:'';
    if(input)input.value='';
    try{await enroll(password);form.hidden=true;renderAuth()}catch(e){status('Autorizzazione non riuscita · '+e.message)}
  });
  var revokeButton=document.getElementById('r3-sync-revoke');
  if(revokeButton)revokeButton.addEventListener('click',revoke);
  if(globalThis.addEventListener){
    globalThis.addEventListener('r3:ledger-updated',function(){schedule(300)});
    globalThis.addEventListener('online',function(){schedule(200)});
    globalThis.addEventListener('storage',function(e){if(e.key==='r3.memory.ledger.v1')schedule(250)});
  }
  if(document.addEventListener)document.addEventListener('visibilitychange',function(){if(document.visibilityState==='visible')schedule(200)});
  if(getToken())schedule(600);
  setInterval(function(){if(getToken()&&document.visibilityState!=='hidden')syncOnce(false)},30000);
}
window.R3Sync={version:'1.0.0',syncOnce:syncOnce,enroll:enroll,revoke:revoke};
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',bind);else bind();
})();