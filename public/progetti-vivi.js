(function(){
  'use strict';
  const registry=window.R3_PROJECTS;
  if(!registry||!Array.isArray(registry.projects))return;
  const grid=document.getElementById('project-grid');
  const search=document.getElementById('project-search');
  const status=document.getElementById('project-status');
  const count=document.getElementById('project-count');

  const statuses=[...new Set(registry.projects.map(p=>p.status))].sort();
  statuses.forEach(value=>{const option=document.createElement('option');option.value=value;option.textContent=value;status.appendChild(option)});

  function esc(v){return String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]))}
  function norm(v){return String(v??'').toLocaleLowerCase('it').normalize('NFD').replace(/[\u0300-\u036f]/g,'')}
  function hrefFor(project){return `/progetto/${encodeURIComponent(project.slug)}`}

  function render(){
    const q=norm(search.value.trim());
    const state=status.value;
    const rows=registry.projects.filter(project=>{
      if(state&&project.status!==state)return false;
      if(!q)return true;
      const hay=[project.title,project.eyebrow,project.status,project.summary,...(project.capabilities||[])].join(' ');
      return norm(hay).includes(q);
    });
    count.textContent=rows.length;
    grid.innerHTML='';
    if(!rows.length){grid.innerHTML='<div class="empty">Nessun progetto corrisponde ai filtri.</div>';return}
    rows.forEach(project=>{
      const card=document.createElement('article');
      card.className='project-card';
      card.tabIndex=0;
      card.dataset.href=hrefFor(project);
      const discoveries=(project.discoveries||[]).length;
      card.innerHTML=`
        <div class="project-top">
          <p class="project-eyebrow">${esc(project.eyebrow)}</p>
          <span class="badge">${esc(project.status)}</span>
        </div>
        <h2>${esc(project.title)}</h2>
        <p class="project-summary">${esc(project.summary)}</p>
        <div class="chips">${(project.capabilities||[]).slice(0,5).map(x=>`<span class="chip">${esc(x)}</span>`).join('')}</div>
        <div class="project-bottom">
          <a class="open-project" href="${hrefFor(project)}">Apri la pagina viva <span aria-hidden="true">→</span></a>
          <span class="repo-count">${discoveries?`${discoveries} repo in osservazione`:'nessuna repo candidata'}</span>
        </div>`;
      card.addEventListener('click',event=>{if(event.target.closest('a,button,input,select'))return;location.href=card.dataset.href});
      card.addEventListener('keydown',event=>{if(event.key==='Enter'||event.key===' '){event.preventDefault();location.href=card.dataset.href}});
      grid.appendChild(card);
    });
  }

  search.addEventListener('input',render);
  status.addEventListener('change',render);
  render();
})();
