/* Bounded cancellable requests reused by Alpha and travel pages. */
(function(root){
  'use strict';
  const pending=new Map();
  function cancel(key,reason='cancelled'){const item=pending.get(key);if(item){item.reason=reason;item.controller.abort()}}
  function failure(kind){const messages={timeout:'La risposta impiega troppo tempo. Riprova: i parametri sono rimasti qui.',cancelled:'Attesa annullata.',auth:'Accedi di nuovo per continuare.',invalid:'Risposta del servizio non leggibile.'};const error=new Error(messages[kind]||kind);error.kind=kind;return error}
  async function json(url,init={},options={}){
    if(typeof url==='string'&&url==='/api/tarocchi/alpha-leggi'&&init.method==='POST'&&typeof init.body==='string'&&root.Telegram?.WebApp?.initData){
      const body=JSON.parse(init.body);if(body&&!('guest_invite' in body)&&!('guest_mode' in body)&&!('invito' in body))init={...init,body:JSON.stringify({...body,initData:root.Telegram.WebApp.initData})};
    }
    const key=options.key||url;cancel(key,'superseded');
    const item={controller:new AbortController(),reason:''};pending.set(key,item);
    const timer=setTimeout(()=>{item.reason='timeout';item.controller.abort()},Math.max(1000,Math.min(120000,Number(options.timeoutMs)||45000)));
    try{
      const response=await fetch(url,{...init,signal:item.controller.signal});
      let data;
      try{data=await response.json()}catch(error){if(item.controller.signal.aborted)throw error;throw failure([401,403].includes(response.status)?'auth':'invalid')}
      if(!response.ok){const error=[401,403].includes(response.status)?failure('auth'):new Error(String(data?.errore||('HTTP '+response.status)));error.status=response.status;throw error}
      if(item.controller.signal.aborted)throw failure(item.reason||'cancelled');
      return data;
    }catch(error){if(item.controller.signal.aborted)throw failure(item.reason||'cancelled');throw error}
    finally{clearTimeout(timer);if(pending.get(key)===item)pending.delete(key)}
  }
  root.AlphaRequest=Object.freeze({json,cancel,isSuperseded:error=>error?.kind==='superseded'});
  root.addEventListener?.('beforeunload',()=>{for(const key of pending.keys())cancel(key)});
})(typeof window==='undefined'?globalThis:window);
