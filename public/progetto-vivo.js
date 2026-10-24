(function(){
  'use strict';
  const registry=window.R3_PROJECTS;
  if(!registry||!Array.isArray(registry.projects))return;

  const slug=decodeURIComponent(location.pathname.replace(/^\/progetto\/?/,'').replace(/\/$/,''));
  const project=registry.projects.find(p=>p.slug===slug);
  const byId=id=>document.getElementById(id);
  const esc=v=>String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));

  if(!project){
    document.title='Progetto non trovato — R³∞';
    byId('detail-title').textContent='Progetto non trovato';
    byId('detail-summary').textContent='Questo indirizzo non corrisponde ancora a un progetto registrato.';
    byId('detail-live').href='/progetti';
    byId('detail-live').innerHTML='Torna ai progetti <span>→</span>';
    return;
  }

  document.title=`${project.title} — Progetto Vivo`;
  byId('detail-eyebrow').textContent=project.eyebrow;
  byId('detail-title').textContent=project.title;
  byId('detail-status').textContent=project.status;
  byId('detail-summary').textContent=project.summary;
  byId('detail-live').href=project.liveUrl||'#';
  if(project.liveUrl===`/progetto/${project.slug}`){
    byId('detail-live').style.display='none';
  }
  byId('detail-source').textContent=project.source||'—';
  byId('detail-next').textContent=project.next||'Nessun passo successivo registrato.';
  byId('detail-updated').textContent=`Registro progetti · aggiornato ${registry.meta.updated} · versione ${registry.meta.version}`;

  const capabilities=byId('detail-capabilities');
  capabilities.innerHTML=(project.capabilities||[]).map(item=>`<span class="cap-item">${esc(item)}</span>`).join('')||'<span class="cap-item">Nessuna capacità registrata</span>';

  const discoveries=project.discoveries||[];
  byId('repo-total').textContent=`${discoveries.length} ${discoveries.length===1?'candidata':'candidate'}`;
  const repoList=byId('repo-list');
  if(!discoveries.length){
    repoList.innerHTML='<div class="repo-empty">Nessuna repo esterna in valutazione per questo progetto. Quando ne troviamo una utile, compare qui prima di qualsiasi adozione.</div>';
  }else{
    repoList.innerHTML=discoveries.map(repo=>{
      const url=`https://github.com/${encodeURI(repo.repo)}`;
      return `<article class="repo-card"><div><h3><a href="${url}" target="_blank" rel="noopener">${esc(repo.repo)} ↗</a></h3><p>${esc(repo.use)}</p></div><span class="repo-state">${esc(repo.status)}</span></article>`;
    }).join('');
  }
})();
