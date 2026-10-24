/* Text-only initialization; no TTS until an explicit click. */
(function(){
  let attempts=0;
  function mount(){
    const box=document.querySelector('.alpha-atlas');
    if(!box){if(attempts++<100)setTimeout(mount,150);return}
    const button=box.querySelector('[data-atlas-tour]');
    if(!button||button.dataset.manual)return;
    button.dataset.manual='1';
    const intro=box.querySelector('.alpha-atlas-head p');
    if(intro)intro.textContent="Scorri tu con il dito. Nessuna carta avanza da sola: ruota la carta nei quattro lati e girala Luce/Ombra.";
    let playing=false;
    button.onclick=()=>{
      if(window.AlphaGuestMode)return;
      if(playing){window.AlphaVoice?.stop();playing=false;button.textContent='▶ Presentazione AI';return}
      const text=box.querySelector('.alpha-atlas-narration p')?.textContent||'';
      if(!text||!window.AlphaVoice)return;
      playing=true;button.textContent='■ Ferma presentazione';
      window.AlphaVoice.speak(text,{language:document.getElementById('language')?.value||'it',onState:state=>{
        if(state==='ended'||state==='unavailable'){playing=false;button.textContent='▶ Presentazione AI'}
      }});
    };
    if(window.AlphaGuestMode){button.disabled=true;button.textContent='Presentazione testuale'}
  }
  document.readyState==='loading'?document.addEventListener('DOMContentLoaded',mount):mount();
})();
