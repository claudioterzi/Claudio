(()=>{
  const MAX=3,KEY='alpha74.guest.completed.v1';
  const COPY={
    it:{label:'TEST PRIVATO',left:n=>n===1?'1 lettura di prova disponibile':`${n} letture di prova disponibili`,blocked:'Hai completato le 3 letture TEST.',note:'Questa è una versione di prova privata, non la versione pubblica ufficiale.'},
    en:{label:'PRIVATE TEST',left:n=>n===1?'1 test reading available':`${n} test readings available`,blocked:'You have completed the 3 TEST readings.',note:'This is a private test version, not the official public release.'},
    fr:{label:'TEST PRIVÉ',left:n=>n===1?'1 lecture test disponible':`${n} lectures test disponibles`,blocked:'Vous avez terminé les 3 lectures TEST.',note:'Ceci est une version de test privée, pas la version publique officielle.'},
    es:{label:'TEST PRIVADO',left:n=>n===1?'1 lectura de prueba disponible':`${n} lecturas de prueba disponibles`,blocked:'Has completado las 3 lecturas TEST.',note:'Esta es una versión de prueba privada, no la versión pública oficial.'}
  };
  let memory=0,pending=false,pendingTimer=0,countedForPending=false;
  function isGuest(){return location.pathname.replace(/\/+$/,'')==='/alpha74-prova'}
  function lang(){const v=document.getElementById('language')?.value||'it';return COPY[v]?v:'it'}
  function getUsed(){try{return Math.max(0,Math.min(MAX,Number(localStorage.getItem(KEY))||0))}catch(_){return memory}}
  function setUsed(v){v=Math.max(0,Math.min(MAX,v));memory=v;try{localStorage.setItem(KEY,String(v))}catch(_){}}
  function noIndex(){
    let m=document.querySelector('meta[name="robots"]');if(!m){m=document.createElement('meta');m.name='robots';document.head.appendChild(m)}m.content='noindex,nofollow,noarchive,nosnippet,noimageindex';
    let g=document.querySelector('meta[name="googlebot"]');if(!g){g=document.createElement('meta');g.name='googlebot';document.head.appendChild(g)}g.content='noindex,nofollow,noarchive,nosnippet,noimageindex';
  }
  function killLinks(){
    document.querySelectorAll('.nav-costellazione,#telegram-continuity').forEach(el=>el.remove());
    document.querySelectorAll('a[href]').forEach(a=>{try{const u=new URL(a.href,location.href);if(u.origin===location.origin&&u.pathname!==location.pathname&&u.hash==='')a.remove()}catch(_){}})
  }
  function banner(){
    let box=document.querySelector('.a74-guest-limit');
    if(!box){box=document.createElement('section');box.className='a74-guest-limit';box.setAttribute('role','status');box.setAttribute('aria-live','polite');const top=document.querySelector('.a74-language-top'),wrap=document.querySelector('main.wrap');if(top?.parentNode)top.after(box);else wrap?.prepend(box)}
    const used=getUsed(),left=Math.max(0,MAX-used),c=COPY[lang()];
    box.innerHTML=`<strong>${c.label}</strong><span>${used>=MAX?c.blocked:c.left(left)}</span><small>${c.note}</small>`;
    box.classList.toggle('is-blocked',used>=MAX);
  }
  function enforce(){
    const blocked=getUsed()>=MAX;
    document.querySelectorAll('#deck .back').forEach(b=>{if(blocked)b.disabled=true});
    const read=document.getElementById('read');if(read&&blocked)read.disabled=true;
    banner();
  }
  function completeOne(){if(!pending||countedForPending)return;countedForPending=true;pending=false;clearTimeout(pendingTimer);setUsed(getUsed()+1);enforce()}
  function watchResult(){const result=document.getElementById('result');if(!result)return setTimeout(watchResult,120);const check=()=>{if(pending&&!result.classList.contains('hidden'))completeOne()};new MutationObserver(check).observe(result,{attributes:true,attributeFilter:['class']});check()}
  function interceptRead(){document.addEventListener('click',e=>{const btn=e.target.closest?.('#read');if(!btn)return;if(getUsed()>=MAX){e.preventDefault();e.stopImmediatePropagation();enforce();return}pending=true;countedForPending=false;clearTimeout(pendingTimer);pendingTimer=setTimeout(()=>{pending=false},70000)},true)}
  function apply(){
    if(!isGuest())return;
    noIndex();document.documentElement.classList.add('a74-guest');document.title='Alpha 74 · TEST PRIVATO';
    killLinks();new MutationObserver(()=>{killLinks();enforce()}).observe(document.documentElement,{childList:true,subtree:true});
    document.getElementById('language')?.addEventListener('change',banner);
    interceptRead();watchResult();enforce();
  }
  const style=document.createElement('style');style.textContent=`
    .a74-guest .nav-costellazione{display:none!important}.a74-guest #telegram-continuity{display:none!important}.a74-guest body{padding-top:0!important}.a74-guest .a74-language-top{top:max(.55rem,env(safe-area-inset-top))!important}
    .a74-guest body::before{content:'TEST';position:fixed;right:10px;bottom:10px;z-index:9999;padding:.35rem .55rem;border:1px solid #d9bd7066;border-radius:999px;background:#0b0a0ee8;color:#e5cb7c;font:700 .68rem/1 system-ui;letter-spacing:.12em;pointer-events:none}
    .a74-guest-limit{display:flex;align-items:center;gap:.65rem;flex-wrap:wrap;margin:-.35rem 0 1rem;padding:.7rem .85rem;border:1px solid #d9bd7038;border-radius:13px;background:#111016;color:#cfc6b5;font-size:.86rem}.a74-guest-limit strong{color:#e5cb7c;letter-spacing:.06em;text-transform:uppercase;font-size:.72rem}.a74-guest-limit small{width:100%;color:#8f877b;line-height:1.45}.a74-guest-limit.is-blocked{border-color:#9b754a66;background:#17120f}
  `;document.head.appendChild(style);
  document.readyState==='loading'?document.addEventListener('DOMContentLoaded',apply):apply();
})();