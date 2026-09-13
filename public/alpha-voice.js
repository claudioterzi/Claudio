(function(root){
  'use strict';
  const DEFAULT_LANG={it:'it-IT',en:'en-US',fr:'fr-FR',es:'es-ES'};
  let activeAudio=null,activeUrl='',activeSource=null,audioContext=null,token=0;
  function notify(cb,state){if(typeof cb==='function')cb(state)}
  function unlockAudio(){
    const C=root.AudioContext||root.webkitAudioContext;if(!C)return null;
    try{if(!audioContext||audioContext.state==='closed')audioContext=new C();if(audioContext.state==='suspended')audioContext.resume().catch(()=>{});return audioContext}catch(e){return null}
  }
  function stop(){
    token++;
    if(activeSource){try{activeSource.onended=null;activeSource.stop(0);activeSource.disconnect()}catch(e){}activeSource=null}
    if(activeAudio){try{activeAudio.pause();activeAudio.currentTime=0}catch(e){}activeAudio.onended=null;activeAudio.onerror=null;activeAudio=null}
    if(activeUrl){URL.revokeObjectURL(activeUrl);activeUrl=''}
    if('speechSynthesis' in root)root.speechSynthesis.cancel();
  }
  function chunks(text){const s=text.match(/[^.!?…]+[.!?…]+|[^.!?…]+$/g)||[text],out=[];let cur='';for(const part of s){const n=(cur+' '+part.trim()).trim();if(n.length>240&&cur){out.push(cur);cur=part.trim()}else cur=n}if(cur)out.push(cur);return out}
  function localSpeech(text,language,cb,current){
    if(!('speechSynthesis' in root)){notify(cb,'unavailable');return false}
    const synth=root.speechSynthesis,code=String(language||'it').toLowerCase().split('-',1)[0];
    const voice=synth.getVoices().filter(v=>String(v.lang||'').toLowerCase().startsWith(code)).sort((a,b)=>/natural|enhanced|premium|neural|google|microsoft/i.test(b.name)-/natural|enhanced|premium|neural|google|microsoft/i.test(a.name))[0]||null;
    const list=chunks(text);if(!list.length){notify(cb,'unavailable');return false}notify(cb,'fallback');
    list.forEach((part,i)=>{const u=new SpeechSynthesisUtterance(part);u.lang=voice?.lang||DEFAULT_LANG[code]||DEFAULT_LANG.it;if(voice)u.voice=voice;u.rate=.96;u.pitch=.98;u.volume=1;if(i===list.length-1){u.onend=()=>{if(current===token)notify(cb,'ended')};u.onerror=()=>{if(current===token)notify(cb,'ended')}}synth.speak(u)});return true
  }
  async function playWeb(blob,cb,current,ctx){
    if(!ctx)return false;
    try{if(ctx.state==='suspended')await ctx.resume();const bytes=await blob.arrayBuffer();if(current!==token)return false;const buf=await ctx.decodeAudioData(bytes.slice(0));if(current!==token)return false;const src=ctx.createBufferSource();src.buffer=buf;src.connect(ctx.destination);activeSource=src;src.onended=()=>{if(activeSource===src)activeSource=null;try{src.disconnect()}catch(e){}if(current===token)notify(cb,'ended')};notify(cb,'playing');src.start(0);return true}catch(e){activeSource=null;return false}
  }
  async function playElement(blob,cb,current){
    const url=URL.createObjectURL(blob),audio=new Audio();audio.preload='auto';audio.playsInline=true;audio.src=url;activeAudio=audio;activeUrl=url;
    audio.onended=()=>{if(current===token)notify(cb,'ended');if(activeAudio===audio){activeAudio=null;URL.revokeObjectURL(url);activeUrl=''}};
    audio.onerror=()=>{if(activeAudio===audio){activeAudio=null;URL.revokeObjectURL(url);activeUrl=''}};
    try{notify(cb,'playing');await audio.play();return true}catch(e){if(activeAudio===audio){activeAudio=null;URL.revokeObjectURL(url);activeUrl=''}return false}
  }
  async function speak(value,options){
    const text=String(value||'').replace(/\s+/g,' ').trim(),opts=options||{};if(!text)return false;
    stop();const current=token,ctx=unlockAudio();notify(opts.onState,'loading');
    try{
      const response=await fetch('/api/tarocchi/alpha-voce',{method:'POST',headers:{'Content-Type':'application/json',Accept:'audio/mpeg'},cache:'no-store',body:JSON.stringify({testo:text,lingua:opts.language||'it'})});
      if(!response.ok)throw new Error('tts '+response.status);
      const blob=await response.blob();if(current!==token)return false;
      if(await playWeb(blob,opts.onState,current,ctx))return true;
      if(current!==token)return false;
      if(await playElement(blob,opts.onState,current))return true;
    }catch(e){}
    if(current!==token)return false;
    return localSpeech(text,opts.language,opts.onState,current);
  }
  root.AlphaVoice=Object.freeze({speak,stop});
})(typeof globalThis!=='undefined'?globalThis:this);
