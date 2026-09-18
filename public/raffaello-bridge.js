/* Raffaello private bridge. Claudio Terzi · C.Terzi. */
(function(root){
  'use strict';
  async function request(path, method='GET', body){
    const controller=new AbortController();
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
      if(error.name==='AbortError')throw new Error('La risposta sta impiegando più tempo. Riprova Analizza per recuperarla.');
      throw error;
    }finally{clearTimeout(timer);}
  }
  async function analyze(question, reading, requestId, onStaged, language){
    const draft=await request('/drafts','POST',{domanda:question,lettura_id:reading||null,request_id:requestId,lingua:language||undefined});
    if(onStaged)onStaged(draft.id);
    return request('/drafts/'+draft.id+'/analyze','POST',{});
  }
  root.RaffaelloBridge={request,analyze};
})(window);
