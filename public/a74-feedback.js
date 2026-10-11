(()=>{
  const PATH='/alpha74-prova';
  if(location.pathname.replace(/\/+$/,'')!==PATH)return;
  const COPY={
    it:{title:'Prima impressione',intro:'Ci aiuta a capire cosa funziona davvero. Bastano pochi secondi.',name:'Nome o soprannome (facoltativo)',comment:'Cosa ti è piaciuto o cosa cambieresti?',send:'Invia feedback',sending:'Invio…',sent:'Grazie. Feedback ricevuto.',retry:'Non riesco a inviarlo adesso.',qs:['Impatto visivo','Chiarezza del funzionamento','Qualità della lettura','Coerenza tra carte e interpretazione','Quanto vorresti usarlo di nuovo']},
    en:{title:'First impression',intro:'Help us understand what truly works. It only takes a few seconds.',name:'Name or nickname (optional)',comment:'What did you like, or what would you change?',send:'Send feedback',sending:'Sending…',sent:'Thank you. Feedback received.',retry:'Unable to send it right now.',qs:['Visual impact','Clarity of how it works','Quality of the reading','Coherence between cards and interpretation','How much you would use it again']},
    fr:{title:'Première impression',intro:'Aidez-nous à comprendre ce qui fonctionne vraiment. Quelques secondes suffisent.',name:'Nom ou surnom (facultatif)',comment:'Qu’avez-vous aimé ou que changeriez-vous ?',send:'Envoyer',sending:'Envoi…',sent:'Merci. Avis reçu.',retry:'Impossible de l’envoyer maintenant.',qs:['Impact visuel','Clarté du fonctionnement','Qualité de la lecture','Cohérence cartes / interprétation','Envie de le réutiliser']},
    es:{title:'Primera impresión',intro:'Ayúdanos a entender qué funciona de verdad. Solo lleva unos segundos.',name:'Nombre o apodo (opcional)',comment:'¿Qué te gustó o qué cambiarías?',send:'Enviar opinión',sending:'Enviando…',sent:'Gracias. Opinión recibida.',retry:'No puedo enviarlo ahora.',qs:['Impacto visual','Claridad del funcionamiento','Calidad de la lectura','Coherencia cartas / interpretación','Cuánto te gustaría usarlo de nuevo']}
  };
  const KEY='alpha74.feedback.sent.v1';
  const lang=()=>{const v=document.getElementById('language')?.value||'it';return COPY[v]?v:'it'};
  const friend=()=>new URLSearchParams(location.search).get('friend')||'';
  const used=()=>{try{return Math.max(1,Math.min(3,Number(localStorage.getItem('alpha74.guest.completed.v1'))||1))}catch(_){return 1}};
  const already=()=>{try{return sessionStorage.getItem(KEY)==='1'}catch(_){return false}};
  const mark=()=>{try{sessionStorage.setItem(KEY,'1')}catch(_){}};
  function row(label,key){return `<fieldset class="a74-fb-row" data-key="${key}"><legend>${label}</legend><div class="a74-fb-scale">${[1,2,3,4,5].map(n=>`<label><input type="radio" name="fb-${key}" value="${n}"><span>${n}</span></label>`).join('')}</div></fieldset>`}
  function render(){
    const result=document.getElementById('result');if(!result)return setTimeout(render,150);
    if(already()||document.querySelector('.a74-feedback'))return;
    const c=COPY[lang()],box=document.createElement('section');box.className='panel a74-feedback';box.innerHTML=`<div class="tag">${c.title}</div><p class="muted">${c.intro}</p>${row(c.qs[0],'visual')}${row(c.qs[1],'clarity')}${row(c.qs[2],'reading')}${row(c.qs[3],'coherence')}${row(c.qs[4],'return')}<label>${c.name}<input class="a74-fb-input" data-fb-name maxlength="80" autocomplete="name"></label><label>${c.comment}<textarea data-fb-comment rows="3" maxlength="1800"></textarea></label><button type="button" class="primary" data-fb-send>${c.send}</button><span class="a74-fb-status" role="status" aria-live="polite"></span>`;
    result.after(box);
    box.querySelector('[data-fb-send]').addEventListener('click',()=>send(box));
    document.getElementById('language')?.addEventListener('change',()=>{if(!document.querySelector('.a74-feedback'))return;document.querySelector('.a74-feedback').remove();render()},{once:true});
  }
  async function send(box){
    const c=COPY[lang()],ratings={};let complete=true;
    for(const key of ['visual','clarity','reading','coherence','return']){const v=box.querySelector(`input[name="fb-${key}"]:checked`)?.value;if(!v){complete=false;break}ratings[key]=Number(v)}
    const status=box.querySelector('.a74-fb-status'),btn=box.querySelector('[data-fb-send]');if(!complete){status.textContent='1–5';return}
    btn.disabled=true;btn.textContent=c.sending;status.textContent='';
    try{const r=await fetch('/api/tarocchi/alpha-feedback',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({friend:friend(),nickname:box.querySelector('[data-fb-name]').value,language:lang(),reading_number:used(),ratings,comment:box.querySelector('[data-fb-comment]').value})});if(!r.ok)throw new Error();mark();box.querySelectorAll('input,textarea,button').forEach(el=>el.disabled=true);status.textContent=c.sent;btn.textContent=c.send}catch(_){btn.disabled=false;btn.textContent=c.send;status.textContent=c.retry}}
  function watch(){const result=document.getElementById('result');if(!result)return setTimeout(watch,150);const show=()=>{if(!result.classList.contains('hidden'))render()};new MutationObserver(show).observe(result,{attributes:true,attributeFilter:['class']});show()}
  const style=document.createElement('style');style.textContent=`.a74-feedback{border-color:#d9bd7040}.a74-fb-row{border:0;border-top:1px solid #2d2b31;padding:.8rem 0;margin:0}.a74-fb-row legend{color:#d8c68f;padding:0;font-size:.94rem}.a74-fb-scale{display:flex;gap:.45rem;margin-top:.55rem}.a74-fb-scale label{margin:0}.a74-fb-scale input{position:absolute;opacity:0;pointer-events:none}.a74-fb-scale span{display:grid;place-items:center;width:42px;height:42px;border:1px solid #4b4332;border-radius:999px;color:#d8c68f;cursor:pointer}.a74-fb-scale input:checked+span{background:#b99843;color:#0b0b0e;border-color:#d7bd70}.a74-fb-input{width:100%;min-height:44px;background:#0d0d11;border:1px solid #3a3740;border-radius:9px;color:#eee;padding:.7rem;margin:.35rem 0 .9rem}.a74-fb-status{margin-left:.65rem;color:#a49c8f;font-size:.85rem}@media(max-width:520px){.a74-fb-scale{justify-content:space-between}.a74-fb-scale span{width:44px;height:44px}.a74-feedback .primary{width:100%}.a74-fb-status{display:block;margin:.55rem 0 0}}`;document.head.appendChild(style);
  document.readyState==='loading'?document.addEventListener('DOMContentLoaded',watch):watch();
})();