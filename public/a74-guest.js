(()=>{
  function isGuest(){
    return location.pathname.replace(/\/+$/,'')==='/alpha74-prova' || new URLSearchParams(location.search).get('guest')==='1';
  }
  function apply(){
    if(!isGuest())return;
    document.documentElement.classList.add('a74-guest');
    document.title='Alpha 74 · Prova privata';
    const kill=()=>{
      document.querySelectorAll('.nav-costellazione,#telegram-continuity').forEach(el=>el.remove());
      document.querySelectorAll('a[href]').forEach(a=>{
        try{
          const u=new URL(a.href,location.href);
          if(u.origin===location.origin && u.pathname!==location.pathname && u.hash==='') a.remove();
        }catch(_){}
      });
    };
    kill();
    const obs=new MutationObserver(kill);
    obs.observe(document.documentElement,{childList:true,subtree:true});
    addEventListener('beforeunload',()=>obs.disconnect(),{once:true});
  }
  const style=document.createElement('style');
  style.textContent=`
    .a74-guest .nav-costellazione{display:none!important}
    .a74-guest #telegram-continuity{display:none!important}
    .a74-guest body{padding-top:0!important}
    .a74-guest .a74-language-top{top:max(.55rem,env(safe-area-inset-top))!important}
  `;
  document.head.appendChild(style);
  document.readyState==='loading'?document.addEventListener('DOMContentLoaded',apply):apply();
})();