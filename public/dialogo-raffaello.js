/* Shared reading and dialogue, manual AI and speech. Claudio Terzi · C.Terzi. */
(function(){
  'use strict';
  const $=id=>document.getElementById(id), api=RaffaelloBridge.request;
  const params=new URLSearchParams(location.search);
  let readingId=null, currentReading=null, turns=[], pending=null, generation=0, speaking=false;
  const say=text=>{$('status').textContent=text;};
  const escapeId=value=>/^[a-f0-9]{32}$/.test(value||'')?value:null;
  function stop(){if(window.speechSynthesis)window.speechSynthesis.cancel();speaking=false;$('listen').textContent='Ascolta';$('listen').setAttribute('aria-pressed','false');}
  function showTurns(items){
    stop();turns=items;$('thread').replaceChildren();
    for(const turn of items){
      const article=document.createElement('article');article.className='turn';
      const question=document.createElement('p');question.className='question';question.textContent=turn.domanda;
      const answer=document.createElement('p');answer.className='answer';answer.textContent=turn.risposta;
      article.append(question,answer);$('thread').append(article);
    }
  }
  function setBusy(active){
    $('analyze').disabled=active;$('analyze').textContent=active?'Raffaello risponde…':'Analizza';
    $('question').disabled=active;
  }
  async function loadReading(id){
    const version=++generation;
    const item=await api('/readings/'+id);if(version!==generation)return;
    stop();pending=null;readingId=id;currentReading=item.snapshot;
    $('reading').hidden=false;$('reading-title').textContent=item.snapshot.domanda||'La tua lettura';
    $('interpretation').textContent=['messaggio','nodo','direzione','domanda_finale'].map(key=>item.snapshot.lettura[key]).filter(Boolean).join('\n\n');
    $('cards').replaceChildren();
    for(const card of item.snapshot.carte){
      const art=Alpha74Art.resolve(card);if(!art)continue;
      const figure=document.createElement('div');figure.className='card';
      const button=document.createElement('button');button.type='button';button.setAttribute('aria-label','Apri '+card.carta);
      const img=document.createElement('img');img.src=art.thumbnail;img.width=160;img.height=160;img.alt=card.carta+' · '+card.polarita;img.loading='lazy';img.style.setProperty('--turn',art.rotation+'deg');
      button.append(img);button.addEventListener('click',()=>{
        $('large-card').src=art.detail;$('large-card').alt=img.alt;$('large-card').style.setProperty('--turn',art.rotation+'deg');
        $('card-title').textContent=card.carta;$('card-meaning').textContent=card.significato_canonico;$('card-dialog').showModal();
      });
      const label=document.createElement('p'),name=document.createElement('strong');name.textContent=card.carta;
      label.append(name,document.createTextNode(card.posizione_label+' · '+card.asse+' · '+card.polarita));figure.append(button,label);$('cards').append(figure);
    }
    $('context-label').textContent='Sulle carte di questa lettura';$('thread-title').textContent='Continuiamo da qui.';
    $('continue-telegram').href='https://t.me/ProtocolloRossoBot?start=r3_'+id;$('continue-telegram').hidden=false;
    showTurns([...(item.snapshot.cronologia||[]),...item.cronologia]);
    history.replaceState(null,'','?lettura='+id);say('Lettura e dialogo aggiornati.');
  }
  async function general(){
    const version=++generation;const state=await api('/session');if(version!==generation)return;
    readingId=null;currentReading=null;pending=null;$('reading').hidden=true;$('continue-telegram').hidden=true;
    $('context-label').textContent='Dialogo libero';$('thread-title').textContent='Cosa vuoi esplorare?';showTurns(state.cronologia||[]);
    history.replaceState(null,'',location.pathname);say('Scrivi liberamente, poi premi Analizza.');
  }
  async function list(){
    const data=await api('/readings');$('readings').replaceChildren();
    for(const item of data.letture){const button=document.createElement('button');button.type='button';button.textContent=item.domanda||item.carte.join(' · ');button.addEventListener('click',()=>loadReading(item.id).catch(fail));$('readings').append(button);}
    if(!data.letture.length){const empty=document.createElement('p');empty.textContent='Le letture che colleghi da Alpha 74 compariranno qui.';$('readings').append(empty);}
  }
  function fail(error){say(error.message||'Collegamento non disponibile.');if(error.status===401){$('pairing').hidden=false;$('workspace').hidden=true;}}
  async function importPending(){
    const raw=sessionStorage.getItem('r3-reading-transfer');if(!raw)return false;
    const snapshot=JSON.parse(raw);const saved=await api('/readings','POST',snapshot);
    sessionStorage.removeItem('r3-reading-transfer');await loadReading(saved.id);await list();return true;
  }
  async function open(){
    try{
      const status=await api('/status');
      if(!status.configured){say('Il collegamento con Telegram è in preparazione. Puoi continuare a usare Alpha 74.');return;}
      await api('/session');$('pairing').hidden=true;$('workspace').hidden=false;
      await list();if(await importPending())return;
      const rid=escapeId(params.get('lettura')),did=escapeId(params.get('richiesta'));
      if(did){
        const task=await api('/drafts/'+did);
        if(task.reading_id)await loadReading(task.reading_id);else await general();
        if(task.answer&&!turns.some(t=>t.id===did))showTurns([...turns,{id:did,domanda:task.question,risposta:task.answer.risposta}]);
        else if(!task.answer)say('Questa domanda non ha ancora una risposta. Premi Analizza nella chat Telegram.');
      }else if(rid)await loadReading(rid);else await general();
      if(params.get('ascolto')==='1'){$('listen').focus();say('Premi Ascolta per avviare la voce.');}
    }catch(error){fail(error);}
  }
  $('pair-form').addEventListener('submit',async event=>{
    event.preventDefault();const button=event.submitter;button.disabled=true;
    try{await api('/link','POST',{code:$('pair-code').value});$('pair-code').value='';await open();}catch(error){fail(error);}finally{button.disabled=false;}
  });
  $('question-form').addEventListener('submit',async event=>{
    event.preventDefault();if($('analyze').disabled)return;
    const question=$('question').value.trim();if(!question)return;
    const version=generation,active=readingId;
    if(!pending||pending.question!==question||pending.reading!==active)pending={question,reading:active,id:crypto.randomUUID()};
    setBusy(true);say('Raffaello sta analizzando la tua domanda…');
    try{
      const result=await RaffaelloBridge.analyze(question,active,pending.id);
      if(version!==generation)return;
      showTurns([...turns,{id:result.richiesta_id,domanda:question,risposta:result.risposta}]);pending=null;$('question').value='';say('Risposta salvata nel tuo dialogo.');
    }catch(error){fail(error);}finally{setBusy(false);}
  });
  $('listen').addEventListener('click',()=>{
    if(speaking){stop();return;}
    if(!window.speechSynthesis){say('Questo browser non supporta l’ascolto. Apri la pagina in Safari o Chrome.');return;}
    const text=[currentReading?['messaggio','nodo','direzione','domanda_finale'].map(key=>currentReading.lettura[key]).filter(Boolean).join('\n'): '',...turns.map(t=>t.domanda+'\n'+t.risposta)].filter(Boolean).join('\n\n');
    if(!text){say('Apri una lettura o analizza una domanda per ascoltarla.');return;}
    const queue=text.match(/[\s\S]{1,240}(?:\s|$)|[\s\S]{1,240}/g)||[];
    speaking=true;$('listen').textContent='Ferma ascolto';$('listen').setAttribute('aria-pressed','true');
    function next(){if(!speaking)return;const chunk=queue.shift();if(!chunk){stop();return;}const utterance=new SpeechSynthesisUtterance(chunk);utterance.lang='it-IT';utterance.rate=.95;utterance.onend=next;utterance.onerror=()=>{stop();say('Ascolto interrotto. Premi Ascolta per riprovare.');};speechSynthesis.speak(utterance);}next();
  });
  $('general').addEventListener('click',()=>general().catch(fail));
  $('refresh').addEventListener('click',()=>{(readingId?loadReading(readingId):general()).then(list).catch(fail);});
  $('disconnect').addEventListener('click',async()=>{try{await api('/session','DELETE');stop();$('workspace').hidden=true;$('pairing').hidden=false;$('thread').replaceChildren();currentReading=null;turns=[];say('Sito scollegato. I registri e le letture restano conservati.');}catch(error){fail(error);}});
  $('close-card').addEventListener('click',()=>$('card-dialog').close());
  window.addEventListener('pagehide',stop);document.addEventListener('visibilitychange',()=>{if(document.hidden)stop();});
  open();
})();
