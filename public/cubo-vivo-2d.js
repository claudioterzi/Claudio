(function(){
  'use strict';

  const data=window.CUBO_VIVO_2D;
  if(!data||!Array.isArray(data.scenes)||!data.scenes.length)return;

  const root=document.getElementById('experience');
  const titleEl=document.getElementById('scene-title');
  const kickerEl=document.getElementById('scene-kicker');
  const copyEl=document.getElementById('scene-copy');
  const senseEl=document.getElementById('scene-sense');
  const numberEl=document.getElementById('scene-number');
  const timeEl=document.getElementById('scene-time');
  const locationEl=document.getElementById('scene-location');
  const timeline=document.getElementById('timeline');
  const prev=document.getElementById('prev');
  const next=document.getElementById('next');
  const play=document.getElementById('play');
  const playIcon=document.getElementById('play-icon');
  const playLabel=document.getElementById('play-label');
  const modeButtons=[...document.querySelectorAll('.mode-button')];
  const prodToggle=document.getElementById('production-toggle');
  const prodClose=document.getElementById('production-close');
  const prodPanel=document.getElementById('production-panel');
  const prodSource=document.getElementById('prod-source');
  const prodPipeline=document.getElementById('prod-pipeline');
  const prodStatus=document.getElementById('prod-status');
  const prodSceneId=document.getElementById('prod-scene-id');
  const prodPrompt=document.getElementById('prod-prompt');

  let index=0;
  let mode='osserva';
  let timer=null;
  let touchStartX=null;

  data.scenes.forEach((scene,i)=>{
    const button=document.createElement('button');
    button.type='button';
    button.setAttribute('aria-label',`Vai alla scena ${i+1}: ${scene.title}`);
    button.innerHTML=`<span>${String(i+1).padStart(2,'0')} · ${escapeHtml(scene.title)}</span>`;
    button.addEventListener('click',()=>show(i,true));
    timeline.appendChild(button);
  });

  const timelineButtons=[...timeline.querySelectorAll('button')];

  function escapeHtml(value){
    return String(value).replace(/[&<>"']/g,char=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[char]));
  }

  function show(nextIndex,userInitiated=false){
    index=(nextIndex+data.scenes.length)%data.scenes.length;
    const scene=data.scenes[index];
    root.dataset.scene=scene.id;
    titleEl.textContent=scene.title;
    kickerEl.textContent=scene.kicker;
    copyEl.textContent=scene.copy[mode]||scene.copy.osserva;
    senseEl.textContent=scene.sense;
    numberEl.textContent=`${String(index+1).padStart(2,'0')} / ${String(data.scenes.length).padStart(2,'0')}`;
    timeEl.textContent=scene.time;
    locationEl.textContent=scene.location;
    prodSource.textContent=`${data.meta.sourceRepository} · ${data.meta.sourceBlobSha.slice(0,10)}…`;
    prodPipeline.textContent=`${data.meta.openMontageCandidatePipeline} · candidate`;
    prodStatus.textContent=data.meta.status;
    prodSceneId.textContent=scene.id;
    prodPrompt.textContent=scene.visualDirection;
    timelineButtons.forEach((button,i)=>{
      button.classList.toggle('active',i===index);
      button.classList.toggle('done',i<index);
      button.setAttribute('aria-current',i===index?'step':'false');
    });
    history.replaceState(null,'',`#${scene.id}`);
    if(userInitiated&&timer)restartTimer();
  }

  function setMode(nextMode){
    if(!['osserva','vivi','ricorda'].includes(nextMode))return;
    mode=nextMode;
    root.dataset.mode=mode;
    modeButtons.forEach(button=>button.classList.toggle('active',button.dataset.mode===mode));
    show(index,false);
  }

  function setPlaying(active){
    if(active){
      if(timer)return;
      play.setAttribute('aria-pressed','true');
      playIcon.textContent='Ⅱ';
      playLabel.textContent='Pausa';
      timer=setInterval(()=>show(index+1,false),8000);
    }else{
      clearInterval(timer);
      timer=null;
      play.setAttribute('aria-pressed','false');
      playIcon.textContent='▶';
      playLabel.textContent='Vivi la sequenza';
    }
  }

  function restartTimer(){
    if(!timer)return;
    clearInterval(timer);
    timer=setInterval(()=>show(index+1,false),8000);
  }

  function toggleProduction(open){
    const shouldOpen=typeof open==='boolean'?open:prodPanel.hidden;
    prodPanel.hidden=!shouldOpen;
    prodToggle.setAttribute('aria-expanded',String(shouldOpen));
  }

  prev.addEventListener('click',()=>show(index-1,true));
  next.addEventListener('click',()=>show(index+1,true));
  play.addEventListener('click',()=>setPlaying(!timer));
  modeButtons.forEach(button=>button.addEventListener('click',()=>setMode(button.dataset.mode)));
  prodToggle.addEventListener('click',()=>toggleProduction());
  prodClose.addEventListener('click',()=>toggleProduction(false));

  document.addEventListener('keydown',event=>{
    if(event.key==='ArrowRight')show(index+1,true);
    if(event.key==='ArrowLeft')show(index-1,true);
    if(event.key===' '&&event.target===document.body){event.preventDefault();setPlaying(!timer)}
    if(event.key==='Escape')toggleProduction(false);
  });

  root.addEventListener('touchstart',event=>{touchStartX=event.changedTouches[0].clientX},{passive:true});
  root.addEventListener('touchend',event=>{
    if(touchStartX===null)return;
    const delta=event.changedTouches[0].clientX-touchStartX;
    touchStartX=null;
    if(Math.abs(delta)<55)return;
    show(index+(delta<0?1:-1),true);
  },{passive:true});

  if(!window.matchMedia('(prefers-reduced-motion: reduce)').matches){
    root.addEventListener('pointermove',event=>{
      const x=(event.clientX/window.innerWidth-.5)*2;
      const y=(event.clientY/window.innerHeight-.5)*2;
      root.style.setProperty('--px',x.toFixed(3));
      root.style.setProperty('--py',y.toFixed(3));
    },{passive:true});
  }

  const hash=decodeURIComponent(location.hash.replace(/^#/,''));
  const hashIndex=data.scenes.findIndex(scene=>scene.id===hash);
  if(hashIndex>=0)index=hashIndex;
  show(index,false);
})();
