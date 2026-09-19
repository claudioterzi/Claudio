(function(){
  'use strict';

  const DATA=window.CUBO_OPERE_DATA;
  const graphEl=document.getElementById('graph');
  const detailEl=document.getElementById('detail');
  const searchEl=document.getElementById('search');
  const categoryEl=document.getElementById('category');
  const yearEl=document.getElementById('year');
  const connectionsEl=document.getElementById('connections');
  const resetEl=document.getElementById('reset');
  const warningEl=document.getElementById('webgl-warning');
  const legendEl=document.getElementById('legend');
  const catalogGroupsEl=document.getElementById('catalog-groups');
  const catalogCountEl=document.getElementById('catalog-count');

  const allNodes=DATA.nodes, allLinks=DATA.links;
  const nodeById=new Map(allNodes.map(n=>[n.id,n]));
  const workNodes=allNodes.filter(n=>n.kind==='work');
  const categories=[...new Set(workNodes.map(n=>n.category))];

  document.getElementById('metric-works').textContent=workNodes.length;
  document.getElementById('metric-categories').textContent=categories.length;
  document.getElementById('metric-links').textContent=allLinks.length;

  categories.forEach(cat=>{const o=document.createElement('option');o.value=cat;o.textContent=cat;categoryEl.appendChild(o)});
  const colorByCategory={};workNodes.forEach(n=>colorByCategory[n.category]=n.color);
  categories.forEach(cat=>{const item=document.createElement('button');item.type='button';item.className='legend-item';item.innerHTML='<span class="legend-dot" style="color:'+colorByCategory[cat]+';background:'+colorByCategory[cat]+'"></span><span>'+escapeHtml(cat)+'</span>';item.addEventListener('click',()=>{categoryEl.value=categoryEl.value===cat?'':cat;applyFilter()});legendEl.appendChild(item)});

  let selectedId=null,graph=null;
  function escapeHtml(v){return String(v).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]))}
  function normalize(v){return String(v||'').toLocaleLowerCase('it').normalize('NFD').replace(/[\u0300-\u036f]/g,'')}
  function linkEnds(l){return[typeof l.source==='object'?l.source.id:l.source,typeof l.target==='object'?l.target.id:l.target]}
  function relationLabel(t){return({family:'famiglia',contains:'appartenenza',genealogy:'genealogia',canon:'canone',version:'versione',symbolic:'legame simbolico',method:'metodo',derives:'derivazione',echo:'eco',source:'fonte',theme:'tema',style:'stile',historical:'asse storico',threshold:'soglia fondativa'})[t]||'relazione'}

  function visibleSet(){
    const q=normalize(searchEl.value.trim()),cat=categoryEl.value,year=yearEl.value?Number(yearEl.value):null;
    const works=workNodes.filter(n=>{if(cat&&n.category!==cat)return false;if(year&&n.year!==year)return false;if(q&&!(normalize(n.title).includes(q)||normalize(n.category).includes(q)||normalize(n.summary).includes(q)))return false;return true});
    const ids=new Set(works.map(n=>n.id));
    if(!cat&&!year&&!q){allNodes.forEach(n=>ids.add(n.id));return ids}
    works.forEach(n=>allLinks.forEach(l=>{const[s,t]=linkEnds(l);if(s===n.id)ids.add(t);if(t===n.id)ids.add(s)}));ids.add('corpus-claudio-terzi');return ids
  }

  function applyFilter(){const ids=visibleSet();if(graph){graph.nodeVisibility(n=>ids.has(n.id)).linkVisibility(l=>{if(!connectionsEl.checked)return false;const[s,t]=linkEnds(l);return ids.has(s)&&ids.has(t)})}renderCatalog(ids)}

  function renderCatalog(ids){
    catalogGroupsEl.innerHTML='';const visibleWorks=workNodes.filter(n=>ids.has(n.id));catalogCountEl.textContent=visibleWorks.length+' titoli visibili';
    categories.forEach(cat=>{const rows=visibleWorks.filter(n=>n.category===cat).sort((a,b)=>a.year-b.year||b.importance-a.importance||a.title.localeCompare(b.title,'it'));if(!rows.length)return;const sec=document.createElement('section');sec.className='catalog-group';const h=document.createElement('h3');h.textContent=cat+' · '+rows.length;sec.appendChild(h);const grid=document.createElement('div');grid.className='title-grid';rows.forEach(n=>{const a=document.createElement('a');a.className='title-link';a.style.setProperty('--node-color',n.color);a.href=n.url;a.target='_blank';a.rel='noopener';a.textContent=n.title;a.title=(n.date?n.date+' · ':'')+'Apri lo scritto';a.addEventListener('mouseenter',()=>focusNode(n,false));grid.appendChild(a)});sec.appendChild(grid);catalogGroupsEl.appendChild(sec)})
  }

  function relatedNodes(node){const rows=[];allLinks.forEach(l=>{const[s,t]=linkEnds(l);if(s===node.id&&nodeById.has(t))rows.push({node:nodeById.get(t),type:l.type});else if(t===node.id&&nodeById.has(s))rows.push({node:nodeById.get(s),type:l.type})});return rows.filter(r=>r.node.id!=='corpus-claudio-terzi').sort((a,b)=>b.node.importance-a.node.importance)}

  function renderDetail(node){
    const related=relatedNodes(node);
    const generic=node.kind==='work'?'Questo titolo occupa una posizione determinata dal suo momento nella genealogia, dalla centralità nel corpus e dalla quantità di relazioni con gli altri testi.':'Nodo di orientamento: raccoglie una costellazione del corpus e permette di leggerne la struttura.';
    const description=node.summary||generic;
    const dateLine=node.date?`<p class="detail-kicker">${escapeHtml(node.date)}</p>`:'';
    const attribution=node.kind==='work'?`<div class="detail-attribution"><strong>Attribuzione:</strong> ${escapeHtml(node.credit||'Claudio Terzi · C.Terzi')}<br><strong>Diritti:</strong> ${escapeHtml(node.rightsNotice||'© Claudio Terzi · archivio e contributi dichiarati')}<br><span>${escapeHtml(node.attributionStatus||'Corpus Claudio Terzi')}</span></div>`:'';
    detailEl.innerHTML=`<p class="detail-kicker">${escapeHtml(node.kind==='work'?node.category:'Nodo di orientamento')}</p><h2>${escapeHtml(node.title)}</h2>${dateLine}${attribution}<p>${escapeHtml(description)}</p><div class="meta"><div class="chip"><strong>${escapeHtml(node.year)}</strong><span>tempo</span></div><div class="chip"><strong>${escapeHtml(node.importance)}/10</strong><span>importanza</span></div><div class="chip"><strong>${escapeHtml(node.density)}/10</strong><span>densità</span></div></div>${node.kind==='work'?`<a class="open-doc" href="${escapeHtml(node.url)}" target="_blank" rel="noopener">Apri lo scritto ↗</a>`:''}<div class="related"><h3>Connessioni · ${related.length}</h3>${related.slice(0,18).map(r=>`<a href="#${escapeHtml(r.node.id)}" data-focus="${escapeHtml(r.node.id)}"><span>${escapeHtml(r.node.title)}</span> · <small>${escapeHtml(relationLabel(r.type))}</small></a>`).join('')}</div>`;
    detailEl.querySelectorAll('[data-focus]').forEach(a=>a.addEventListener('click',e=>{e.preventDefault();const n=nodeById.get(a.dataset.focus);if(n)focusNode(n,true)}))
  }

  function focusNode(node,moveCamera=true){
    selectedId=node.id;renderDetail(node);location.hash=node.id;
    if(graph){graph.nodeVal(n=>n.id===selectedId?(n.kind==='hub'?14:9):(n.kind==='category'?7:n.kind==='hub'?11:2.5+n.importance*.42)).nodeOpacity(n=>n.id===selectedId?1:.9).linkWidth(l=>{const[s,t]=linkEnds(l);return(s===selectedId||t===selectedId)?2.6:(l.type==='threshold'?1.35:.35)}).linkOpacity(.58).linkColor(l=>{const[s,t]=linkEnds(l);if(s===selectedId||t===selectedId)return'#f0d98e';if(l.type==='threshold')return'#e7a76f';return'#536073'});if(moveCamera){const distance=115,len=Math.hypot(node.fx||1,node.fy||1,node.fz||1)||1,ratio=1+distance/len;graph.cameraPosition({x:(node.fx||0)*ratio,y:(node.fy||0)*ratio,z:(node.fz||0)*ratio},{x:node.fx||0,y:node.fy||0,z:node.fz||0},900)}}
  }

  function makeNodeObject(node){const group=new THREE.Group(),radius=node.kind==='hub'?7.6:node.kind==='category'?5.2:2.4+node.importance*.22,geometry=new THREE.SphereGeometry(radius,node.kind==='work'?14:22,node.kind==='work'?10:16),material=new THREE.MeshPhongMaterial({color:node.color,emissive:node.color,emissiveIntensity:node.kind==='work'?.28:.48,shininess:80,transparent:true,opacity:node.kind==='work'?.91:.97});group.add(new THREE.Mesh(geometry,material));if(node.kind!=='work'||node.importance>=9){const ringGeo=new THREE.RingGeometry(radius*1.45,radius*1.55,48),ringMat=new THREE.MeshBasicMaterial({color:node.color,transparent:true,opacity:.32,side:THREE.DoubleSide}),ring=new THREE.Mesh(ringGeo,ringMat);ring.rotation.x=Math.PI/2;group.add(ring)}return group}

  function addCubeAndStars(){if(!graph||!window.THREE)return;const scene=graph.scene(),box=new THREE.BoxGeometry(360,260,280),edges=new THREE.EdgesGeometry(box),lines=new THREE.LineSegments(edges,new THREE.LineBasicMaterial({color:0x4d5565,transparent:true,opacity:.35}));scene.add(lines);const starCount=window.innerWidth<700?350:900,positions=new Float32Array(starCount*3);for(let i=0;i<starCount;i++){positions[i*3]=(Math.random()-.5)*1100;positions[i*3+1]=(Math.random()-.5)*780;positions[i*3+2]=(Math.random()-.5)*900}const starGeo=new THREE.BufferGeometry();starGeo.setAttribute('position',new THREE.BufferAttribute(positions,3));scene.add(new THREE.Points(starGeo,new THREE.PointsMaterial({color:0xd9deea,size:1.1,transparent:true,opacity:.32,sizeAttenuation:true})));scene.add(new THREE.AmbientLight(0x8a91a5,1.1));const light=new THREE.PointLight(0xffdfa0,50,800);light.position.set(80,160,220);scene.add(light)}

  function initGraph(){
    if(!window.ForceGraph3D||!window.THREE){warningEl.hidden=false;renderCatalog(visibleSet());return}
    try{
      graph=ForceGraph3D({controlType:'orbit',rendererConfig:{antialias:true,alpha:true}})(graphEl).graphData({nodes:allNodes,links:allLinks}).backgroundColor('rgba(0,0,0,0)').showNavInfo(false).nodeThreeObject(makeNodeObject).nodeLabel(n=>`<div style="max-width:260px;padding:5px 7px"><b>${escapeHtml(n.title)}</b><br><span style="opacity:.75">${escapeHtml(n.category)} · ${escapeHtml(n.date||n.year)}</span></div>`).nodeVal(n=>n.kind==='hub'?11:n.kind==='category'?7:2.5+n.importance*.42).nodeColor(n=>n.color).linkColor(l=>l.type==='threshold'?'#e7a76f':l.type==='genealogy'?'#d7b65b':l.type==='version'?'#b88fd2':'#536073').linkOpacity(.38).linkWidth(l=>l.type==='threshold'?1.35:l.type==='genealogy'?1.25:.35).linkDirectionalParticles(l=>['genealogy','derives','source','threshold'].includes(l.type)?2:0).linkDirectionalParticleWidth(1.6).linkDirectionalParticleSpeed(.004).onNodeClick(n=>focusNode(n,true)).onNodeHover(n=>{graphEl.style.cursor=n?'pointer':'grab'}).cooldownTicks(0).warmupTicks(0);
      allNodes.forEach(n=>{n.x=n.fx;n.y=n.fy;n.z=n.fz});
      const resize=()=>{const r=graphEl.getBoundingClientRect();graph.width(r.width).height(r.height||650)};resize();window.addEventListener('resize',resize,{passive:true});addCubeAndStars();graph.cameraPosition({x:430,y:275,z:430},{x:0,y:15,z:0},0);const controls=graph.controls();if(controls){controls.enableDamping=true;controls.dampingFactor=.08;controls.minDistance=70;controls.maxDistance=900}applyFilter()
    }catch(err){console.error('Cubo Quantico:',err);warningEl.hidden=false;renderCatalog(visibleSet())}
  }

  [searchEl,categoryEl,yearEl].forEach(el=>el.addEventListener(el===searchEl?'input':'change',applyFilter));connectionsEl.addEventListener('change',applyFilter);resetEl.addEventListener('click',()=>{selectedId=null;searchEl.value='';categoryEl.value='';yearEl.value='';connectionsEl.checked=true;history.replaceState(null,'',location.pathname);applyFilter();if(graph)graph.cameraPosition({x:430,y:275,z:430},{x:0,y:15,z:0},900);detailEl.innerHTML=`<p class="detail-kicker">Vista generale</p><h2>Cubo Quantico delle Opere</h2><p>Ogni punto è un titolo. X attraversa il tempo, Y misura la centralità dell’opera, Z la sua densità di relazioni. Le linee mostrano famiglie, genealogie, versioni, echi e soglie fondative.</p><div class="metrics"><div><strong>${workNodes.length}</strong><span>titoli</span></div><div><strong>${categories.length}</strong><span>costellazioni</span></div><div><strong>${allLinks.length}</strong><span>relazioni</span></div></div>`});

  const initialHash=decodeURIComponent(location.hash.replace(/^#/,''));if(initialHash&&nodeById.has(initialHash))setTimeout(()=>focusNode(nodeById.get(initialHash),true),700);
  renderCatalog(visibleSet());initGraph();
})();
