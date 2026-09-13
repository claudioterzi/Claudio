(function(root){
  'use strict';
  const DEFAULT_LANG={it:'it-IT',en:'en-US',fr:'fr-FR',es:'es-ES'};
  let activeAudio=null;
  let activeUrl='';
  let token=0;
  let providerAvailable;

  function notify(callback,state){if(typeof callback==='function')callback(state);}

  function stop(){
    token+=1;
    if(activeAudio){
      activeAudio.pause();
      activeAudio.currentTime=0;
      activeAudio.onended=null;
      activeAudio.onerror=null;
      activeAudio=null;
    }
    if(activeUrl){URL.revokeObjectURL(activeUrl);activeUrl='';}
    if('speechSynthesis' in root)root.speechSynthesis.cancel();
  }

  function chunks(text){
    const sentences=text.match(/[^.!?…]+[.!?…]+|[^.!?…]+$/g)||[text];
    const result=[];
    let current='';
    sentences.forEach(sentence=>{
      const next=(current+' '+sentence.trim()).trim();
      if(next.length>240&&current){result.push(current);current=sentence.trim();}
      else current=next;
    });
    if(current)result.push(current);
    return result;
  }

  function localSpeech(text,language,callback,current){
    if(!('speechSynthesis' in root)){notify(callback,'unavailable');return false;}
    const synth=root.speechSynthesis;
    const code=String(language||'it').toLowerCase().split('-',1)[0];
    const voices=synth.getVoices();
    const voice=voices
      .filter(item=>String(item.lang||'').toLowerCase().startsWith(code))
      .sort((a,b)=>{
        const score=name=>/natural|enhanced|premium|neural|google|microsoft/i.test(name)?1:0;
        return score(b.name)-score(a.name);
      })[0]||null;
    const list=chunks(text);
    if(!list.length){notify(callback,'unavailable');return false;}
    notify(callback,'fallback');
    list.forEach((part,index)=>{
      const utterance=new SpeechSynthesisUtterance(part);
      utterance.lang=voice?.lang||DEFAULT_LANG[code]||DEFAULT_LANG.it;
      if(voice)utterance.voice=voice;
      utterance.rate=.96;
      utterance.pitch=.98;
      utterance.volume=1;
      if(index===list.length-1){
        utterance.onend=()=>{if(current===token)notify(callback,'ended');};
        utterance.onerror=()=>{if(current===token)notify(callback,'ended');};
      }
      synth.speak(utterance);
    });
    return true;
  }

  async function externalAvailable(){
    if(providerAvailable!==undefined)return providerAvailable;
    try{
      const response=await fetch('/api/tarocchi/alpha-voce',{headers:{Accept:'application/json'},cache:'no-store'});
      const data=await response.json().catch(()=>({}));
      providerAvailable=Boolean(response.ok&&data.disponibile);
    }catch(error){providerAvailable=false;}
    return providerAvailable;
  }

  async function speak(value,options){
    const text=String(value||'').replace(/\s+/g,' ').trim();
    const opts=options||{};
    if(!text)return false;
    stop();
    const current=token;
    notify(opts.onState,'loading');
    if(await externalAvailable()){
      try{
        const response=await fetch('/api/tarocchi/alpha-voce',{
          method:'POST',
          headers:{'Content-Type':'application/json',Accept:'audio/mpeg'},
          body:JSON.stringify({testo:text,lingua:opts.language||'it'})
        });
        if(!response.ok)throw new Error('external voice unavailable');
        const blob=await response.blob();
        if(current!==token)return false;
        const url=URL.createObjectURL(blob);
        const audio=new Audio(url);
        activeAudio=audio;
        activeUrl=url;
        audio.onended=()=>{
          if(current===token)notify(opts.onState,'ended');
          if(activeAudio===audio){activeAudio=null;URL.revokeObjectURL(url);activeUrl='';}
        };
        audio.onerror=()=>{
          if(activeAudio===audio){activeAudio=null;URL.revokeObjectURL(url);activeUrl='';}
          if(current===token)localSpeech(text,opts.language,opts.onState,current);
        };
        notify(opts.onState,'playing');
        await audio.play();
        return true;
      }catch(error){
        if(current!==token)return false;
        providerAvailable=false;
      }
    }
    if(current!==token)return false;
    return localSpeech(text,opts.language,opts.onState,current);
  }

  root.AlphaVoice=Object.freeze({speak,stop});
})(typeof globalThis!=='undefined'?globalThis:this);
