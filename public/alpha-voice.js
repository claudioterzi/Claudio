(function(root){
  'use strict';
  const DEFAULT_LANG={it:'it-IT',en:'en-US',fr:'fr-FR',es:'es-ES'};
  let activeAudio=null,activeUrl='',activeSource=null,audioContext=null,token=0;
  function notify(cb,state){if(typeof cb==='function')cb(state)}
  function voiceFor(language){
    const code=String(language||'it').toLowerCase().split('-',1)[0];
    const voices=('speechSynthesis' in root?root.speechSynthesis.getVoices():[]).filter(v=>String(v.lang||'').toLowerCase().startsWith(code));
    return voices.sort((a,b)=>/natural|enhanced|premium|neural|google|microsoft/i.test(b.name)-/natural|enhanced|premium|neural|google|microsoft/i.test(a.name))[0]||null;
  }
  function unlockAudio(){
    const C=root.AudioContext||root.webkitAudioContext;if(!C)return null;
    try{
      if(!audioContext||audioContext.state==='closed')audioContext=new C();
      if(audioContext.state==='suspended')audioContext.resume().catch(()=>{});
      /* iOS Safari: a real zero-length playback inside the tap unlocks later WebAudio starts. */
      const buf=audioContext.createBuffer(1,1,22050),src=audioContext.createBufferSource(),gain=audioContext.createGain();
      gain.gain.value=0;src.buffer=buf;src.connect(gain);gain.connect(audioContext.destination);src.start(0);
      src.onended=()=>{try{src.disconnect();gain.disconnect()}catch(e){}};
      return audioContext;
    }catch(e){return null}
  }
  function stop(){
    token++;
    if(activeSource){try{activeSource.stop(0)}catch(e){}activeSource=null}
    if(activeAudio){try{activeAudio.pause();activeAudio.currentTime=0}catch(e){}activeAudio.onended=null;activeAudio.onerror=null;activeAudio=null}
    if(activeUrl){URL.revokeObjectURL(activeUrl);activeUrl=''}
    if('speechSynthesis' in root)root.speechSynthesis.cancel();
  }
  async function fetchAudio(text,language){
    const response=await fetch('/api/tarocchi/alpha-voce',{method:'POST',headers:{'Content-Type':'application/json',Accept:'audio/mpeg'},cache:'no-store',body:JSON.stringify({testo:text,lingua:language||'it'})});
    if(!response.ok)throw new Error('tts '+response.status);
    return response.blob();
  }
  async function decode(blob,ctx){
    const bytes=await blob.arrayBuffer();
    return ctx.decodeAudioData(bytes.slice(0));
  }
  function playBuffer(buffer,current,ctx,cb,announce=true){
    return new Promise(resolve=>{
      if(current!==token){resolve(false);return}
      try{
        const src=ctx.createBufferSource();src.buffer=buffer;src.connect(ctx.destination);activeSource=src;
        src.onended=()=>{if(activeSource===src)activeSource=null;try{src.disconnect()}catch(e){}resolve(current===token)};
        if(announce)notify(cb,'playing');src.start(0);
      }catch(e){resolve(false)}
    });
  }
  async function playElement(blob,cb,current){
    const url=URL.createObjectURL(blob),audio=new Audio();audio.preload='auto';audio.playsInline=true;audio.src=url;activeAudio=audio;activeUrl=url;
    audio.onended=()=>{if(current===token)notify(cb,'ended');if(activeAudio===audio){activeAudio=null;URL.revokeObjectURL(url);activeUrl=''}};
    audio.onerror=()=>{if(activeAudio===audio){activeAudio=null;URL.revokeObjectURL(url);activeUrl=''}};
    try{notify(cb,'playing');await audio.play();return true}catch(e){if(activeAudio===audio){activeAudio=null;URL.revokeObjectURL(url);activeUrl=''}return false}
  }
  function chunks(text){const s=text.match(/[^.!?…]+[.!?…]+|[^.!?…]+$/g)||[text],out=[];let cur='';for(const part of s){const n=(cur+' '+part.trim()).trim();if(n.length>240&&cur){out.push(cur);cur=part.trim()}else cur=n}if(cur)out.push(cur);return out}
  function localSpeech(text,language,cb,current){
    if(!('speechSynthesis' in root)){notify(cb,'unavailable');return false}
    const synth=root.speechSynthesis,code=String(language||'it').toLowerCase().split('-',1)[0],voice=voiceFor(language),list=chunks(text);if(!list.length){notify(cb,'unavailable');return false}notify(cb,'fallback');
    list.forEach((part,i)=>{const u=new SpeechSynthesisUtterance(part);u.lang=voice?.lang||DEFAULT_LANG[code]||DEFAULT_LANG.it;if(voice)u.voice=voice;u.rate=.96;u.pitch=.98;u.volume=1;if(i===list.length-1){u.onend=()=>{if(current===token)notify(cb,'ended')};u.onerror=()=>{if(current===token)notify(cb,'ended')}}synth.speak(u)});return true
  }
  function localSequence(list,options,current){
    if(!('speechSynthesis' in root)){notify(options.onState,'unavailable');return false}
    const synth=root.speechSynthesis,language=options.language||'it',code=String(language).toLowerCase().split('-',1)[0],voice=voiceFor(language);let i=0;notify(options.onState,'fallback');
    const next=()=>{if(current!==token)return;if(i>=list.length){notify(options.onState,'ended');return}const text=list[i];if(typeof options.onSegment==='function')options.onSegment(i,text);const u=new SpeechSynthesisUtterance(text);u.lang=voice?.lang||DEFAULT_LANG[code]||DEFAULT_LANG.it;if(voice)u.voice=voice;u.rate=.96;u.pitch=.98;u.volume=1;u.onend=()=>{i++;next()};u.onerror=()=>{i++;next()};synth.speak(u)};next();return true
  }
  async function speak(value,options){
    const text=String(value||'').replace(/\s+/g,' ').trim(),opts=options||{};if(!text)return false;
    stop();const current=token,ctx=unlockAudio();notify(opts.onState,'loading');
    try{
      const blob=await fetchAudio(text,opts.language||'it');if(current!==token)return false;
      if(ctx){if(ctx.state==='suspended')await ctx.resume();const buffer=await decode(blob,ctx);if(current!==token)return false;const ok=await playBuffer(buffer,current,ctx,opts.onState,true);if(ok&&current===token)notify(opts.onState,'ended');if(ok)return true}
      if(current!==token)return false;if(await playElement(blob,opts.onState,current))return true;
    }catch(e){}
    if(current!==token)return false;return localSpeech(text,opts.language,opts.onState,current)
  }
  async function speakSequence(values,options){
    const opts=options||{},list=(Array.isArray(values)?values:[]).map(v=>String(v||'').replace(/\s+/g,' ').trim()).filter(Boolean);if(!list.length)return false;
    stop();const current=token,ctx=unlockAudio();notify(opts.onState,'loading');
    if(!ctx)return localSequence(list,opts,current);
    try{
      if(ctx.state==='suspended')await ctx.resume();
      let pending=fetchAudio(list[0],opts.language||'it');
      for(let i=0;i<list.length;i++){
        const blob=await pending;if(current!==token)return false;
        if(i+1<list.length)pending=fetchAudio(list[i+1],opts.language||'it');
        const buffer=await decode(blob,ctx);if(current!==token)return false;
        if(typeof opts.onSegment==='function')opts.onSegment(i,list[i]);
        const ok=await playBuffer(buffer,current,ctx,opts.onState,i===0);if(!ok||current!==token)return false;
      }
      notify(opts.onState,'ended');return true;
    }catch(e){if(current!==token)return false;return localSequence(list,opts,current)}
  }
  root.AlphaVoice=Object.freeze({speak,speakSequence,stop,unlock:unlockAudio});
})(typeof globalThis!=='undefined'?globalThis:this);
