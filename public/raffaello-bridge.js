/* Raffaello private bridge. Claudio Terzi · C.Terzi. */
(function(root){
  'use strict';
  async function request(path, method='GET', body, options={}){
    const controller=new AbortController();
    const forwardAbort=()=>controller.abort();
    if(options.signal){if(options.signal.aborted)controller.abort();else options.signal.addEventListener('abort',forwardAbort,{once:true});}
    const timer=setTimeout(()=>controller.abort(),90000);
    try{
      const response=await fetch('/api/raffaello'+path,{
        method,credentials:'same-origin',signal:controller.signal,
        headers:{'Content-Type':'application/json','X-Raffaello':'1'},
        ...(body===undefined?{}:{body:JSON.stringify(body)})
      });
      const data=await response.json();
      if(!response.ok){const error=new Error(data.errore||'Operazione non riuscita.');error.status=response.status;throw error;}
      return data;
    }catch(error){
      if(error.name==='AbortError'&&options.signal&&options.signal.aborted)throw error;
      if(error.name==='AbortError'){const timeout=new Error('La risposta sta impiegando più tempo. Riprova Analizza per recuperarla.');timeout.name='TimeoutError';throw timeout;}
      throw error;
    }finally{clearTimeout(timer);if(options.signal)options.signal.removeEventListener('abort',forwardAbort);}
  }
  async function analyze(question, reading, requestId, onStaged, language, options={}){
    const draft=await request('/drafts','POST',{domanda:question,lettura_id:reading||null,request_id:requestId,lingua:language||undefined},options);
    if(onStaged)onStaged(draft.id);
    if(options.signal&&options.signal.aborted)throw new DOMException('Attesa annullata.','AbortError');
    return request('/drafts/'+draft.id+'/analyze','POST',{},options);
  }
  root.RaffaelloBridge={request,analyze};
})(window);
