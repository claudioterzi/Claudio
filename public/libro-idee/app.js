/* Libro delle Idee R3 — portale statico, senza backend e senza telemetria.
 * © Claudio Terzi, 2026. Dataset documentali derivati: non sostituiscono il Master.
 */
(function () {
  'use strict';

  var registry = window.R3_IDEA_REGISTRY;
  var cube = window.CUBO_OPERE_DATA;
  var $ = function (id) { return document.getElementById(id); };
  var qs = function (s) { return Array.from(document.querySelectorAll(s)); };
  var records = [], edges = [], byKey = new Map(), byCubeId = new Map();
  var active = 'catalogo', selectedKey = '', pageSize = 60, graphifyLoaded = false;
  var selectedRec = null, lastReply = '', filters = {};
  var cubeCamera = { yaw: -.47, pitch: .3, zoom: 1.0 };
  var graphCamera = { zoom: 1, dx: 0, dy: 0 };
  var graphPoints = [], cubePoints = [];
  var cubeCanvas = $('cubeCanvas'), graphCanvas = $('graphCanvas');
  var drawingQueued = false;
  var handlers = [];
  var registryReady = registry && Array.isArray(registry.records) && registry.records.length;
  var cubeReady = cube && Array.isArray(cube.nodes) && Array.isArray(cube.links);

  function node(tag, text, className) {
    var e = document.createElement(tag);
    if (text !== undefined && text !== null) e.textContent = String(text);
    if (className) e.className = className;
    return e;
  }
  function append(parent) {
    for (var i = 1; i < arguments.length; i++) if (arguments[i]) parent.appendChild(arguments[i]);
    return parent;
  }
  function codeHash(s) {
    var h = 2166136261;
    s = String(s || '');
    for (var i = 0; i < s.length; i++) { h ^= s.charCodeAt(i); h = Math.imul(h, 16777619); }
    return h >>> 0;
  }
  function safeURL(s) {
    if (typeof s !== 'string') return '';
    try { var u = new URL(s); return (u.protocol === 'https:' || u.protocol === 'http:') ? u.href : ''; }
    catch (_) { return ''; }
  }
  function clean(s) {
    return String(s || '').normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLowerCase();
  }
  function short(s, limit) {
    s = String(s || '');
    return s.length > limit ? s.slice(0, limit - 1) + '…' : s;
  }
  function ideaPosition(r, i) {
    var h = codeHash(r.id), j = (h % 310) - 155, k = ((h >>> 8) % 350) - 175;
    return { x: 70 + (i % 4) * 12 + j * .43, y: (i % 9 - 4) * 15 + k * .28, z: k };
  }
  function graphPosition(rec) {
    var groups = ['R³ e infrastruttura','Media e creazione','Giochi, XR e mondi','Organizzazione quotidiana','Oggetti e prodotti','Retail e imprese','Impatto e territorio','Servizi professionali','Economia e proprietà intellettuale'];
    var ix = groups.indexOf(rec.domain); if (ix < 0) ix = codeHash(rec.domain) % 10;
    var a = (ix / 10) * Math.PI * 2 - Math.PI / 2;
    var r = 132 + (codeHash(rec.key) % 100) * .53;
    var h = codeHash(rec.key + 'seed');
    return { x: Math.cos(a) * r + ((h % 70) - 35), y: Math.sin(a) * r + (((h >>> 8) % 70) - 35) };
  }
  function addRecord(r) {
    if (byKey.has(r.key)) return;
    r.pos2d = graphPosition(r);
    records.push(r); byKey.set(r.key, r);
  }
  if (registryReady) registry.records.forEach(function (r, i) {
    var p = ideaPosition(r, i);
    addRecord({
      key: 'R3:' + r.id, id: r.id, title: r.name || r.id, type: r.group,
      domain: r.domain || 'Non classificato', state: r.state || 'DOCUMENTATO',
      evidence: r.evidence_tier || 'MASTER_DOCUMENT',
      summary: r.implementation_note || '',
      refs: r.source_refs || [], source: r.source_of_truth || 'Master IDEA OS',
      aliases: r.aliases || [], year: null, date: 'Snapshot 2026-10-14',
      privacy: r.privacy_scope || 'PROJECT', kind: 'idea',
      x: p.x, y: p.y, z: p.z, color: r.group === 'IDEA_OS_MASTER' ? '#bda4fb' : '#8ee0d8',
      rawTextPresent: false
    });
  });
  if (cubeReady) {
    cube.nodes.forEach(function (n, i) {
      var k = 'CUBO:' + n.id;
      byCubeId.set(n.id, k);
      var p = ideaPosition(n, i);
      var pos = { x: typeof n.fx === 'number' ? n.fx : p.x,
                  y: typeof n.fy === 'number' ? n.fy : p.y,
                  z: typeof n.fz === 'number' ? n.fz : p.z };
      addRecord({
        key: k, id: n.id, title: n.title || n.id, type: 'OPERA_CUBO',
        domain: n.category || 'Cubo Quantico', state: 'TITOLO_CENSITO',
        evidence: 'CUBO_INDEX', summary: n.summary || '', refs: n.url ? [{ kind: 'CUBO_LINK', label: 'Fonte del Cubo', url: n.url }] : [],
        source: 'Cubo Quantico delle Opere · registro derivato', aliases: [],
        year: typeof n.year === 'number' ? n.year : null, date: n.date || (n.year || ''),
        privacy: 'PROJECT', kind: n.kind || 'work', x: pos.x, y: pos.y, z: pos.z,
        color: n.color || '#f9bfa1', rawTextPresent: false
      });
    });
  }
  if (registryReady) (registry.relationships || []).forEach(function (e) {
    var a = 'R3:' + e.source, b = 'R3:' + e.target;
    if (byKey.has(a) && byKey.has(b)) edges.push({
      a: a, b: b, label: e.relationship || 'collegamento', evidence: e.status || 'DESIGN_LINK_OR_SOURCE_BASED',
      possible: /POSSIBLE|INFERRED|HYPOTHESIS/.test(String(e.status || '')),
      source: 'R³ UNIVERSUM · relazioni documentali'
    });
  });
  if (cubeReady) cube.links.forEach(function (e) {
    var endpoint = function (v) { return v && typeof v === 'object' ? v.id : v; };
    var a = byCubeId.get(endpoint(e.source)), b = byCubeId.get(endpoint(e.target));
    if (a && b) edges.push({
      a: a, b: b, label: e.type || e.relation || 'correlazione', evidence: e.evidence || e.confidence || 'DECLARED',
      possible: /POSSIBLE|INFERRED|AMBIGUOUS/.test(String(e.evidence || e.confidence || '')),
      source: e.sourceSystem || 'Cubo Quantico'
    });
  });

  // R3_CUBO_BOOK_JOURNEY_V1: one record, two views; no source writes or inferred identity.
  var journeyReady = false, journeyRestoring = false, journeyDepth = 0;
  var journeyNotice = '';
  var journeyViews = ['catalogo','cubo','grafo','cronologia','fonti','voce'];
  var journeyFilterIds = ['searchInput','typeFilter','domainFilter','statusFilter'];
  function journeySnapshot() {
    var values = {};
    journeyFilterIds.forEach(function(id){ values[id] = $(id).value; });
    return {schema:'R3_CUBO_BOOK_JOURNEY_V1',view:active,key:selectedKey,depth:journeyDepth,
      filters:values,pageSize:pageSize,cubeCamera:Object.assign({},cubeCamera),
      graphCamera:Object.assign({},graphCamera),scrollY:window.scrollY || 0};
  }
  function journeyURL() {
    var fragment = location.hash.slice(1);
    var params = new URLSearchParams(journeyViews.includes(fragment) ? '' : fragment);
    params.set('view',active);
    if(selectedKey) params.set('node',selectedKey); else params.delete('node');
    // Preserve any existing unlock fragment in place; never copy it into history state or links.
    return location.pathname + location.search + '#' + params.toString();
  }
  function journeyStore(push) {
    if(!journeyReady || journeyRestoring) return;
    if(push) journeyDepth++;
    var state = Object.assign({},history.state || {});
    state.r3BookJourney = journeySnapshot();
    try { history[push ? 'pushState' : 'replaceState'](state,'',journeyURL()); }
    catch(_) { if(push) journeyDepth--; journeyNotice='Cronologia del browser non disponibile; la selezione resta locale.'; }
    renderJourney();
  }
  function journeyRemember() { journeyStore(false); }
  function renderJourney() {
    if(!$('r3Journey')) return;
    $('journeyBack').disabled = journeyDepth <= 0;
    $('journeyToBook').disabled = !selectedRec;
    $('journeyToCube').disabled = !selectedRec;
    $('journeyToBook').setAttribute('aria-pressed',String(active==='catalogo'));
    $('journeyToCube').setAttribute('aria-pressed',String(active==='cubo'));
    $('journeySelection').textContent = selectedRec ? selectedRec.id+' · '+selectedRec.title : 'Seleziona una scheda nel Libro o un nodo nel Cubo.';
    $('journeyStatus').textContent = journeyNotice || (selectedRec ? 'Stessa scheda, stesso testo, stesse fonti. Nessun originale modificato.' : 'Libro ↔ Cubo · percorso nei due sensi');
    $('r3Journey').setAttribute('data-selected-key',selectedKey);
    $('r3Journey').setAttribute('data-active-view',active);
    var previous=$('r3Journey').querySelector('[data-cubo-book-link]');if(previous)previous.remove();
    var cross=journeyExternalLink(selectedKey);if(cross)$('r3Journey').appendChild(cross);
  }
  function revealJourneyRecord(rec) {
    if(!currentMatches(rec)) {
      journeyFilterIds.forEach(function(id){ $(id).value=''; });
      journeyNotice='Filtri sospesi per mostrare la scheda; «Passo precedente» ripristina il contesto.';
    }
    var index=results().findIndex(function(item){return item.key===rec.key;});
    if(index>=pageSize) pageSize=Math.ceil((index+1)/60)*60;
  }
  function journeyCloseDetail(next) {
    var A=window.Approfondimento, dialog=document.querySelector('dialog.approf[open]');
    if(!A || !A.isOpen())return false;
    if(dialog && typeof dialog.close==='function'){
      dialog.addEventListener('close',next,{once:true});A.close();return true;
    }
    A.close();return false;
  }
  function journeyExternalLink(key) {
    if(!/^\/libro-idee(?:\/|$)/.test(location.pathname) || typeof key!=='string' || !key.startsWith('CUBO:'))return null;
    var a=node('a','↗ Cubo completo','button small');
    a.href='/cubo-quantico#'+encodeURIComponent(key.slice(5));a.rel='noreferrer';a.referrerPolicy='no-referrer';
    a.setAttribute('data-cubo-book-link','to-cube');return a;
  }
  function journeyNavigate(key,view) {
    if(journeyCloseDetail(function(){journeyNavigate(key,view);}))return true;
    var rec=byKey.get(key);
    if(!rec || !journeyViews.includes(view)) {
      journeyNotice='Nodo non presente nello snapshot caricato: nessuna associazione inventata.';
      renderJourney();return false;
    }
    var changed=key!==selectedKey || view!==active;
    journeyRemember();journeyRestoring=true;journeyNotice='';
    try {
      select(key,true);showView(view);revealJourneyRecord(rec);
      if(view==='cubo') cubeCamera.focus={x:rec.x,y:rec.y,z:rec.z};
      renderCatalog();scheduleDrawing();
    } finally { journeyRestoring=false; }
    journeyStore(changed);
    var focusTarget=view==='cubo'?cubeCanvas:$('detailContent');
    if(focusTarget!==cubeCanvas)focusTarget.setAttribute('tabindex','-1');
    focusTarget.focus({preventScroll:true});
    return true;
  }
  function journeyRestore(snapshot) {
    if(journeyCloseDetail(function(){journeyRestore(snapshot);journeyStore(false);}))return true;
    if(!snapshot || snapshot.schema!=='R3_CUBO_BOOK_JOURNEY_V1' || !journeyViews.includes(snapshot.view)) return false;
    journeyRestoring=true;journeyNotice='';
    try {
      journeyDepth=Number.isInteger(snapshot.depth)&&snapshot.depth>=0?snapshot.depth:0;
      journeyFilterIds.forEach(function(id){
        var value=snapshot.filters && snapshot.filters[id];
        $(id).value=typeof value==='string'?value.slice(0,500):'';
      });
      pageSize=Number.isFinite(snapshot.pageSize)?Math.max(60,Math.min(records.length,snapshot.pageSize)):60;
      if(snapshot.cubeCamera) {
        var cam=snapshot.cubeCamera;
        if(['yaw','pitch','zoom'].every(function(k){return Number.isFinite(cam[k]);})) {
          cubeCamera={yaw:cam.yaw,pitch:Math.max(-1.1,Math.min(1.1,cam.pitch)),zoom:Math.max(.32,Math.min(3.4,cam.zoom))};
          if(cam.focus && ['x','y','z'].every(function(k){return Number.isFinite(cam.focus[k]);})) cubeCamera.focus={x:cam.focus.x,y:cam.focus.y,z:cam.focus.z};
        }
      }
      if(snapshot.graphCamera && ['zoom','dx','dy'].every(function(k){return Number.isFinite(snapshot.graphCamera[k]);})) graphCamera=Object.assign({},snapshot.graphCamera);
      if(snapshot.key && byKey.has(snapshot.key)) select(snapshot.key,true);
      else {
        if('speechSynthesis' in window)window.speechSynthesis.cancel();
        selectedKey='';selectedRec=null;$('detailContent').removeAttribute('data-record-key');
        $('detailContent').replaceChildren(node('p','Seleziona una scheda per aprirne testo e fonti.'));
        if(snapshot.key) journeyNotice='Nodo non presente nello snapshot caricato: nessuna associazione inventata.';
      }
      showView(snapshot.view);
      if(snapshot.view==='cubo' && !snapshot.cubeCamera && selectedRec)cubeCamera.focus={x:selectedRec.x,y:selectedRec.y,z:selectedRec.z};
      renderCatalog();scheduleDrawing();
      var scroll=Number.isFinite(snapshot.scrollY)?Math.max(0,Math.min(10000000,snapshot.scrollY)):0;
      requestAnimationFrame(function(){window.scrollTo({top:scroll,behavior:'auto'});});
    } finally { journeyRestoring=false; }
    renderJourney();return true;
  }
  function journeyReadRoute() {
    var raw=location.hash.slice(1),params=new URLSearchParams(raw);
    var view=journeyViews.includes(raw)?raw:params.get('view');
    var key=params.get('node') || '';
    return {view:journeyViews.includes(view)?view:'catalogo',key:key};
  }
  function initJourney() {
    var style=node('style');
    style.textContent='.r3-journey{display:flex;align-items:center;flex-wrap:wrap;gap:10px;padding:16px;margin:0 0 22px;border:1px solid #675982;border-radius:16px;background:#151527}.r3-journey .button{min-height:44px}.r3-journey .button:disabled{opacity:.45;cursor:default}.r3-journey-info{flex:1 1 230px;min-width:0}.r3-journey-info strong{display:block;overflow-wrap:anywhere}.r3-journey-info p{margin:6px 0 0;font-size:12px;line-height:1.5;color:#bdc3d5}.r3-journey .button[aria-pressed=true]{border-color:#bda4fb}.journey-detail-actions{display:flex;gap:8px;flex-wrap:wrap;margin:16px 0}.journey-detail-actions button{min-height:44px}@media(max-width:600px){.r3-journey-info{flex-basis:100%}.r3-journey .button{flex:1 1 120px}}';
    document.head.appendChild(style);
    var bar=node('nav',null,'r3-journey');bar.id='r3Journey';bar.setAttribute('aria-label','Percorso Cubo e Libro delle Idee');
    var info=node('div',null,'r3-journey-info'),label=node('strong'),status=node('p');
    label.id='journeySelection';status.id='journeyStatus';status.setAttribute('role','status');status.setAttribute('aria-live','polite');append(info,label,status);
    var back=node('button','← Passo precedente','button ghost');back.id='journeyBack';back.type='button';
    var book=node('button','▦ Apri nel Libro','button');book.id='journeyToBook';book.type='button';
    var spatial=node('button','◇ Mostra nel Cubo','button');spatial.id='journeyToCube';spatial.type='button';
    append(bar,info,back,book,spatial);document.querySelector('.toolbar').insertAdjacentElement('afterend',bar);
    back.addEventListener('click',function(){if(journeyDepth>0)history.back();});
    book.addEventListener('click',function(){journeyNavigate(selectedKey,'catalogo');});
    spatial.addEventListener('click',function(){journeyNavigate(selectedKey,'cubo');});
    window.addEventListener('popstate',function(event){
      var snap=event.state && event.state.r3BookJourney;
      if(!journeyRestore(snap)){var route=journeyReadRoute();journeyRestore({schema:'R3_CUBO_BOOK_JOURNEY_V1',view:route.view,key:route.key,depth:0});journeyStore(false);}
    });
    window.addEventListener('hashchange',function(){
      var route=journeyReadRoute();
      if(route.view===active && route.key===selectedKey)return;
      journeyRestore({schema:'R3_CUBO_BOOK_JOURNEY_V1',view:route.view,key:route.key,depth:0});journeyStore(false);
    });
    var route=journeyReadRoute(),stored=history.state && history.state.r3BookJourney;
    journeyReady=true;
    if(stored && stored.view===route.view && stored.key===route.key)journeyRestore(stored);
    else journeyRestore({schema:'R3_CUBO_BOOK_JOURNEY_V1',view:route.view,key:route.key,depth:0});
    journeyStore(false);
  }

  function currentMatches(rec) {
    var q = clean($('searchInput').value.trim());
    var type = $('typeFilter').value, domain = $('domainFilter').value, status = $('statusFilter').value;
    if (type && rec.type !== type) return false;
    if (domain && rec.domain !== domain) return false;
    if (status && rec.state !== status) return false;
    if (q) {
      var blob = clean([rec.title,rec.id,rec.domain,rec.summary,rec.source,rec.state].concat(rec.aliases).join(' '));
      var terms = q.split(/\s+/).filter(Boolean);
      if (!terms.every(function (t) { return blob.includes(t); })) return false;
    }
    return true;
  }
  function results() { return records.filter(currentMatches); }
  function refreshFilters() {
    [['domainFilter','domain'],['statusFilter','state']].forEach(function (pair) {
      var sel = $(pair[0]), val = sel.value, prefix = pair[0] === 'domainFilter' ? 'Tutti i domini' : 'Tutti gli stati';
      var firstOption = node('option', prefix); firstOption.value = ''; sel.replaceChildren(firstOption);
      Array.from(new Set(records.map(function (r) { return r[pair[1]]; }))).sort().forEach(function (v) {
        var opt = node('option', short(v, 55)); opt.value = v; sel.appendChild(opt);
      });
      if (Array.from(sel.options).some(function (o) { return o.value === val; })) sel.value = val;
    });
  }
  function updateStats() {
    $('statIdeas').textContent = records.filter(function (r) { return r.type === 'IDEA_OS_MASTER'; }).length;
    $('statModules').textContent = records.filter(function (r) { return r.type === 'COLLEGAMENTI_E_MODULI'; }).length;
    $('statWorks').textContent = records.filter(function (r) { return r.type === 'OPERA_CUBO' && r.kind === 'work'; }).length;
    $('statEdges').textContent = edges.length;
    $('statGraphify').textContent = graphifyLoaded ? records.filter(function (r) { return r.type === 'GRAPHIFY'; }).length : '—';
  }
  function recordCard(rec) {
    var card = node('button',null,'idea-card');
    card.type = 'button';
    card.setAttribute('data-record-key',rec.key);
    if (rec.key === selectedKey) card.classList.add('selected');
    card.setAttribute('aria-label', 'Apri ' + rec.title);
    var top = node('div',null,'card-top');
    append(top,node('span',rec.type === 'OPERA_CUBO' ? 'CUBO / OPERA' : rec.type === 'GRAPHIFY' ? 'GRAPHIFY / METADATI' : rec.id,'id'),node('span','↗','arrow'));
    var mid = node('div');
    append(mid,node('h3',short(rec.title,120)),node('span',rec.domain,'cat'));
    var bottom = node('div',null,'card-bottom');
    append(bottom,node('span',short(rec.state.replaceAll('_',' '),25),'state'),node('span',rec.year || 'Archivio','cat'));
    append(card,top,mid,bottom);
    card.addEventListener('click',function(){ select(rec.key); deepen(rec.key); });
    return card;
  }
  function renderCatalog() {
    var found = results();
    $('catalogSummary').textContent = found.length + ' schede trovate. I titoli indicizzati non equivalgono a testi integrali recuperati.';
    var grid = $('catalogGrid'); grid.replaceChildren();
    var frag = document.createDocumentFragment();
    found.slice(0,pageSize).forEach(function (r) { frag.appendChild(recordCard(r)); });
    grid.appendChild(frag);
    $('showMore').hidden = found.length <= pageSize;
    $('showMore').textContent = 'Mostra altre schede (' + Math.max(0,found.length - pageSize) + ') ↓';
  }
  function detailSection(title, content) {
    var block = node('section',null,'detail-block');
    block.appendChild(node('h4',title));
    if (content instanceof Node) block.appendChild(content);
    else block.appendChild(node('p',content || 'Non verificato'));
    return block;
  }
  // Open the node's full story as its own screen; links inside rebuild it in place.
  function deepen(key) {
    var rec = byKey.get(key), A = window.Approfondimento;
    if (!rec || !A || A.isOpen()) return;
    A.openElement($('detailContent'), {titolo: rec.title, sopratitolo: 'Libro delle idee · ' + rec.id});
  }
  function select(key, silent) {
    var rec = byKey.get(key);
    if (!rec) return;
    var journeyChanged=selectedKey!==key;
    if(journeyChanged){journeyRemember();if('speechSynthesis' in window)window.speechSynthesis.cancel();}
    selectedKey = key; selectedRec = rec;
    var area = $('detailContent'); area.replaceChildren();
    append(area,node('span',rec.id,'detail-id'),node('h3',rec.title,'detail-title'));
    var pills = node('div',null,'detail-meta');
    append(pills,node('span',rec.domain,'detail-pill'),node('span',rec.state.replaceAll('_',' '),'detail-pill'));
    if (rec.year) pills.appendChild(node('span',String(rec.year),'detail-pill'));
    area.appendChild(pills);
    area.setAttribute('data-record-key',key);
    var journeyActions=node('div',null,'journey-detail-actions');
    var detailBook=node('button','▦ Apri nel Libro','button small');detailBook.id='detailToBook';detailBook.type='button';
    var detailCube=node('button','◇ Mostra nel Cubo','button small');detailCube.id='detailToCube';detailCube.type='button';
    detailBook.setAttribute('aria-label','Apri nel Libro: '+rec.id);
    detailCube.setAttribute('aria-label','Mostra nel Cubo: '+rec.id);
    detailBook.addEventListener('click',function(){journeyNavigate(key,'catalogo');});
    detailCube.addEventListener('click',function(){journeyNavigate(key,'cubo');});
    append(journeyActions,detailBook,detailCube,journeyExternalLink(key));area.appendChild(journeyActions);
    area.appendChild(detailSection('Cosa sappiamo', rec.summary || 'Questo titolo è censito, ma il contenuto integrale non è presente in questa copia dell’archivio.'));
    area.appendChild(detailSection('Origine', rec.source));
    area.appendChild(detailSection('Qualità della prova', rec.evidence + (rec.type === 'GRAPHIFY' ? ' · classificazione dai metadati, da verificare sul testo' : '')));
    if (rec.refs && rec.refs.length) {
      var list = node('ul');
      rec.refs.slice(0,14).forEach(function (ref) {
        var li = node('li');
        var u = safeURL(ref.url), label = ref.label || ref.path || ref.kind || 'Documento';
        if (u) {
          var a = node('a',label + ' ↗'); a.href = u; a.target = '_blank'; a.rel = 'noopener noreferrer';
          li.appendChild(a);
        } else li.textContent = label + ' (riferimento documentale; apertura non disponibile)';
        list.appendChild(li);
      });
      area.appendChild(detailSection('Fonti e riferimenti',list));
    }
    var linked = edges.filter(function (e) { return e.a === key || e.b === key; }).slice(0,18);
    if (linked.length) {
      var rel = node('ul');
      linked.forEach(function(e) {
        var other = byKey.get(e.a === key ? e.b : e.a);
        if (!other) return;
        var li = node('li');
        var b = node('button',short(other.title,74)); b.type = 'button'; b.className = 'mini-btn';
        b.addEventListener('click',function(){journeyNavigate(other.key,active);});
        append(li,b,node('span',' · ' + e.label + ' [' + e.evidence + ']'));
        rel.appendChild(li);
      });
      area.appendChild(detailSection('Collegamenti nel grafo',rel));
    }
    area.appendChild(detailSection('Integrità', 'Scheda derivata e consultiva. Testo integrale non importato. Nessuna modifica automatica alla fonte; la data dello snapshot non è la data di nascita dell’idea.'));
    if (!silent && active === 'catalogo') renderCatalog();
    scheduleDrawing();
    journeyStore(journeyChanged);
    renderJourney();
  }
  function showView(view) {
    if (!['catalogo','cubo','grafo','cronologia','fonti','voce'].includes(view)) return;
    var journeyViewChanged=active!==view;
    if(journeyViewChanged)journeyRemember();
    active = view;
    qs('[data-panel]').forEach(function (p) { p.classList.toggle('active',p.dataset.panel===view); });
    qs('[data-view]').forEach(function (b) {
      var yes=b.dataset.view===view; b.classList.toggle('active',yes);b.setAttribute('aria-pressed',String(yes));
    });
    if (view === 'cronologia') renderTimeline();
    if (view === 'fonti') renderSources();
    if (view === 'cubo' || view === 'grafo') scheduleDrawing();
    journeyStore(journeyViewChanged);
    renderJourney();
  }
  function filteredVisual(view) {
    var candidates=results();
    if (view === 'grafo') {
      candidates.sort(function(a,b) {
        var pa=a.type==='IDEA_OS_MASTER' ? 0 : a.type==='COLLEGAMENTI_E_MODULI' ? 1 : a.type==='OPERA_CUBO' ? 2 : 3;
        var pb=b.type==='IDEA_OS_MASTER' ? 0 : b.type==='COLLEGAMENTI_E_MODULI' ? 1 : b.type==='OPERA_CUBO' ? 2 : 3;
        return pa-pb;
      });
    } else {
      candidates.sort(function(a,b) {
        var pa=a.type==='OPERA_CUBO' ? 0 : a.type==='IDEA_OS_MASTER' ? 1 : a.type==='COLLEGAMENTI_E_MODULI' ? 2 : 3;
        var pb=b.type==='OPERA_CUBO' ? 0 : b.type==='IDEA_OS_MASTER' ? 1 : b.type==='COLLEGAMENTI_E_MODULI' ? 2 : 3;
        return pa-pb;
      });
    }
    var max = view === 'grafo' ? 260 : 330;
    if (selectedKey) {
      var selected = candidates.findIndex(function(x){return x.key===selectedKey;});
      if (selected>=max) candidates.splice(0,0,candidates.splice(selected,1)[0]);
    }
    return candidates.slice(0,max);
  }

  // Cubo 3D: proiezione matematica leggera sul Canvas 2D, senza WebGL, Three.js o loop continui.
  function project(n,w,h) {
    var y=cubeCamera.yaw, p=cubeCamera.pitch;
    var origin=cubeCamera.focus || {x:0,y:0,z:0};
    var nx=n.x-origin.x,ny=n.y-origin.y,nz=n.z-origin.z;
    var xx=nx*Math.cos(y)-nz*Math.sin(y);
    var zz=nx*Math.sin(y)+nz*Math.cos(y);
    var yy=ny*Math.cos(p)-zz*Math.sin(p);
    var depth=ny*Math.sin(p)+zz*Math.cos(p);
    var f=510/(560+depth)*cubeCamera.zoom;
    return {x:w/2+xx*f,y:h/2-yy*f,scale:f,depth:depth};
  }
  function resizeCanvas(canvas) {
    var box = canvas.getBoundingClientRect();
    if (box.width < 20 || box.height < 20) return null;
    var dpr=Math.min(window.devicePixelRatio||1,2);
    var targetW=Math.round(box.width*dpr),targetH=Math.round(box.height*dpr);
    if(canvas.width!==targetW||canvas.height!==targetH){canvas.width=targetW;canvas.height=targetH;}
    var ctx=canvas.getContext('2d'); if(!ctx)return null;
    ctx.setTransform(dpr,0,0,dpr,0,0);
    return {ctx:ctx,w:box.width,h:box.height};
  }
  function backdrop(ctx,w,h) {
    ctx.clearRect(0,0,w,h);
    ctx.fillStyle='rgba(197,196,239,.18)';
    for(var i=0;i<34;i++){var x=(codeHash('star'+i)%1000)/1000*w,y=(codeHash('other'+i)%1000)/1000*h;ctx.fillRect(x,y,1.3,1.3);}
  }
  function drawCube() {
    var sz=resizeCanvas(cubeCanvas); if(!sz)return;
    var ctx=sz.ctx,w=sz.w,h=sz.h; backdrop(ctx,w,h);
    var corners=[];
    [-1,1].forEach(function(a){[-1,1].forEach(function(b){[-1,1].forEach(function(c){corners.push({x:a*188,y:b*153,z:c*188});});});});
    ctx.lineWidth=1;ctx.strokeStyle='rgba(143,169,222,.16)';
    for(var i=0;i<corners.length;i++)for(var j=i+1;j<corners.length;j++){
      var d=(corners[i].x!==corners[j].x?1:0)+(corners[i].y!==corners[j].y?1:0)+(corners[i].z!==corners[j].z?1:0);
      if(d!==1)continue;
      var a=project(corners[i],w,h),b=project(corners[j],w,h);
      ctx.beginPath();ctx.moveTo(a.x,a.y);ctx.lineTo(b.x,b.y);ctx.stroke();
    }
    var nodes=filteredVisual('cubo'), set=new Set(nodes.map(function(r){return r.key;}));
    var projected=new Map(); nodes.forEach(function(r){projected.set(r.key,project(r,w,h));});
    if ($('cubeEdges').checked) {
      ctx.lineWidth=.65;ctx.strokeStyle='rgba(179,178,220,.15)';
      edges.forEach(function(e) {
        if(!set.has(e.a)||!set.has(e.b))return;
        var a=projected.get(e.a),b=projected.get(e.b);
        ctx.beginPath();ctx.moveTo(a.x,a.y);ctx.lineTo(b.x,b.y);ctx.stroke();
      });
    }
    cubePoints=[];
    nodes.sort(function(a,b){return projected.get(a.key).depth-projected.get(b.key).depth;}).forEach(function(r){
      var p=projected.get(r.key),selected=r.key===selectedKey;
      var radius=(selected?5.5:r.kind==='category'||r.kind==='hub'?3.7:2.5)*Math.max(.7,Math.min(1.5,p.scale));
      ctx.beginPath();ctx.arc(p.x,p.y,radius,0,Math.PI*2);
      ctx.fillStyle=selected?'#ffffff':r.color;ctx.fill();
      if(selected){ctx.strokeStyle='#e9c9ff';ctx.lineWidth=2;ctx.stroke();ctx.font='12px Segoe UI';ctx.fillStyle='#fff';ctx.fillText(short(r.title,49),p.x+11,p.y-9);}
      cubePoints.push({key:r.key,x:p.x,y:p.y,radius:Math.max(10,radius+5),depth:p.depth});
    });
    ctx.fillStyle='#b2bbd1';ctx.font='12px Segoe UI';
    ctx.fillText('CUBO · ' + nodes.length + ' nodi visibili / ' + results().length + ' risultati',14,25);
  }
  function drawGraph() {
    var sz=resizeCanvas(graphCanvas); if(!sz)return;
    var ctx=sz.ctx,w=sz.w,h=sz.h; backdrop(ctx,w,h);
    var nodes=filteredVisual('grafo'), set=new Set(nodes.map(function(r){return r.key;}));
    function point(r) {
      var s=Math.min(w/540,h/540)*graphCamera.zoom;
      return {x:w/2+r.pos2d.x*s+graphCamera.dx,y:h/2+r.pos2d.y*s+graphCamera.dy};
    }
    var projected=new Map();nodes.forEach(function(r){projected.set(r.key,point(r));});
    var obs=$('observedToggle').checked,pos=$('possibleToggle').checked,drawn=0;
    edges.forEach(function(e){
      if(!set.has(e.a)||!set.has(e.b))return;
      if(e.possible ? !pos : !obs)return;
      var a=projected.get(e.a),b=projected.get(e.b);
      ctx.beginPath();ctx.moveTo(a.x,a.y);ctx.lineTo(b.x,b.y);
      ctx.strokeStyle=e.possible?'rgba(240,181,126,.48)':'rgba(170,194,249,.37)';
      ctx.lineWidth=e.possible?1:1.35;
      if(e.possible)ctx.setLineDash([4,5]);else ctx.setLineDash([]);
      ctx.stroke();drawn++;
    });
    ctx.setLineDash([]);
    graphPoints=[];
    nodes.forEach(function(r){
      var p=projected.get(r.key),selected=r.key===selectedKey;
      var radius=selected?7:r.type==='IDEA_OS_MASTER'?5.2:3.1;
      ctx.beginPath();ctx.arc(p.x,p.y,radius,0,Math.PI*2);ctx.fillStyle=selected?'#fff':r.color;ctx.fill();
      if(selected || (nodes.length<=90&&r.type==='IDEA_OS_MASTER')){
        ctx.font=(selected?'bold ':'')+'10px Segoe UI';ctx.fillStyle=selected?'#fff':'#a5b0cd';
        ctx.fillText(short(r.title,selected?37:17),p.x+8,p.y-8);
      }
      graphPoints.push({key:r.key,x:p.x,y:p.y,radius:Math.max(10,radius+5)});
    });
    ctx.font='12px Segoe UI';ctx.fillStyle='#b2bbd1';
    ctx.fillText('GRAFO · ' + nodes.length + ' nodi · ' + drawn + ' legami visibili',14,25);
  }
  function scheduleDrawing() {
    if(drawingQueued)return;
    drawingQueued=true;
    requestAnimationFrame(function(){drawingQueued=false;if(active==='cubo')drawCube();if(active==='grafo')drawGraph();});
  }
  function bindCanvas(canvas,view) {
    var start, moved=false;
    canvas.addEventListener('pointerdown',function(e){
      start={x:e.clientX,y:e.clientY,yaw:cubeCamera.yaw,pitch:cubeCamera.pitch,dx:graphCamera.dx,dy:graphCamera.dy};
      moved=false;canvas.setPointerCapture(e.pointerId);
    });
    canvas.addEventListener('pointermove',function(e){
      if(!start)return;
      var dx=e.clientX-start.x,dy=e.clientY-start.y;
      if(Math.abs(dx)+Math.abs(dy)>5)moved=true;
      if(!moved)return;
      if(view==='cubo'){
        cubeCamera.yaw=start.yaw+dx*.007;cubeCamera.pitch=Math.max(-1.1,Math.min(1.1,start.pitch+dy*.005));
      }else{graphCamera.dx=start.dx+dx;graphCamera.dy=start.dy+dy;}
      scheduleDrawing();
    });
    canvas.addEventListener('pointerup',function(e){
      if(!start)return;
      if(!moved){
        var rect=canvas.getBoundingClientRect(),x=e.clientX-rect.left,y=e.clientY-rect.top;
        var pts=view==='cubo'?cubePoints:graphPoints;
        var hit=null,min=Infinity;
        pts.forEach(function(p){var d=Math.hypot(x-p.x,y-p.y);if(d<p.radius&&d<min){hit=p;min=d;}});
        if(hit){select(hit.key,true);deepen(hit.key);}
      }
      start=null;
    });
    canvas.addEventListener('pointercancel',function(){start=null;});
    canvas.addEventListener('wheel',function(e){
      e.preventDefault();var cam=view==='cubo'?cubeCamera:graphCamera;
      cam.zoom=Math.max(.32,Math.min(3.4,cam.zoom*(e.deltaY>0?.91:1.1)));scheduleDrawing();
    },{passive:false});
    canvas.addEventListener('keydown',function(e){
      if(view==='cubo'){
        if(e.key==='ArrowLeft')cubeCamera.yaw-=.14;
        else if(e.key==='ArrowRight')cubeCamera.yaw+=.14;
        else if(e.key==='ArrowUp')cubeCamera.pitch=Math.max(-1.1,cubeCamera.pitch-.12);
        else if(e.key==='ArrowDown')cubeCamera.pitch=Math.min(1.1,cubeCamera.pitch+.12);
        else return;
      }else{
        if(e.key==='ArrowLeft')graphCamera.dx-=20;
        else if(e.key==='ArrowRight')graphCamera.dx+=20;
        else if(e.key==='ArrowUp')graphCamera.dy-=20;
        else if(e.key==='ArrowDown')graphCamera.dy+=20;
        else return;
      }
      e.preventDefault();scheduleDrawing();
    });
  }
  bindCanvas(cubeCanvas,'cubo');bindCanvas(graphCanvas,'grafo');

  function renderTimeline() {
    var container=$('timeline');container.replaceChildren();
    var works=records.filter(function(r){return r.type==='OPERA_CUBO'&&r.kind==='work'&&r.year;});
    var years=Array.from(new Set(works.map(function(r){return r.year;}))).sort();
    if(!years.length){container.appendChild(node('p','Nessun anno nel dataset del Cubo.'));return;}
    var max=Math.max.apply(null,years.map(function(y){return works.filter(function(r){return r.year===y;}).length;}));
    years.forEach(function(y){
      var subset=works.filter(function(r){return r.year===y;});
      var block=node('div',null,'time-card'),title=node('div',null,'time-year');
      append(title,node('span',String(y)),node('span',subset.length+' titoli censiti','time-count'));
      var track=node('div',null,'time-track'),fill=node('span',null,'time-fill');fill.style.width=Math.round(subset.length/max*100)+'%';track.appendChild(fill);
      append(block,title,track,node('p',subset.slice(0,9).map(function(r){return r.title;}).join(' · ')+(subset.length>9?' · …':''),'time-list'));
      container.appendChild(block);
    });
  }
  function renderSources() {
    var panel=$('sourcesPanel');panel.replaceChildren();
    function card(title,description,link,label){
      var b=node('article',null,'source-card');append(b,node('h3',title),node('p',description));
      if(safeURL(link)){var a=node('a',label||'Apri fonte ↗');a.href=link;a.target='_blank';a.rel='noopener noreferrer';b.appendChild(a);}
      panel.appendChild(b);
    }
    card('01 / IDEA OS · Master privato', '38 IDEA-ID riportate da uno snapshot derivato del 14 ottobre 2026. Il Master su Google Drive resta la fonte titolare. Questa copia non è sincronizzata in tempo reale.');
    card('02 / R³ UNIVERSUM', '26 moduli collegati e 21 relazioni del registro derivato. Una relazione di architettura descritta non dimostra una connessione software attiva.');
    card('03 / Cubo Quantico', 'Dati dalle copie del repository: opere, famiglie, Identità e Genesi. Le coordinate X/Y/Z sono convenzioni di navigazione. Il titolo censito non prova la presenza o lettura del testo integrale.');
    card('04 / Graphify', graphifyLoaded ? 'Layer Graphify caricato. Il dataset originale dichiara 1.010 documenti censiti dai metadati e 0 testi letti. Le connessioni inferite restano esplicitamente distinte.' : 'Layer Graphify non caricato. Attivalo soltanto quando ti serve, nella sezione Grafo: il browser legge un file locale, senza analisi IA.');
    card('05 / Continuità e protezione', 'Questo portale è statico e consultivo. Non modifica originali, non scandisce le cartelle NAS, non apre porte di rete e non attiva microfoni in background. L’archivio originale, inclusi documenti privati, rimane separato.');
    card('06 / Funzioni future', 'Collegamento autenticato e approvato ai dossier originali, versionamento append-only, motore IA locale per domande naturali, ascolto vocale con consenso e sincronizzazione incrementale. Non sono attivi nella versione attuale.');
  }
  function exportBook() {
    var subset=results().filter(function(r){return r.type==='IDEA_OS_MASTER'||r.type==='COLLEGAMENTI_E_MODULI';});
    function escapeHTML(s){return String(s||'').replace(/[&<>"']/g,function(c){return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c];});}
    var body=subset.map(function(r){
      return '<article><h2>'+escapeHTML(r.id)+' — '+escapeHTML(r.title)+'</h2><p class="meta">'+escapeHTML(r.domain)+' · '+escapeHTML(r.state)+'</p><p>'+escapeHTML(r.summary||'Nessun testo integrale in questo indice.')+'</p><small>Origine: '+escapeHTML(r.source)+'</small></article>';
    }).join('');
    var contents='<!doctype html><html lang="it"><meta charset="utf-8"><title>Il Libro delle Idee — estratto</title><style>body{font:15px/1.6 Georgia,serif;max-width:820px;margin:auto;padding:36px;color:#20202b}h1{font-size:40px}article{page-break-inside:avoid;border-top:1px solid #bbb;padding:20px 0}h2{font-size:20px}.meta,small{color:#606477}@media print{body{padding:0}}</style><h1>Il Libro delle Idee</h1><p>Claudio Terzi · Esportazione documentale · '+escapeHTML(new Date().toLocaleDateString('it-IT'))+'</p><p><strong>ATTENZIONE:</strong> indice derivato di '+subset.length+' schede, non testo integrale delle idee. Nessuna fonte originale modificata.</p>'+body+'</html>';
    var blob=new Blob([contents],{type:'text/html;charset=utf-8'}),url=URL.createObjectURL(blob),a=node('a');
    a.href=url;a.download='Libro_delle_Idee_INDICE_'+new Date().toISOString().slice(0,10)+'.html';
    document.body.appendChild(a);a.click();a.remove();
    setTimeout(function(){URL.revokeObjectURL(url);},2000);
  }
  function loadGraphify() {
    if(graphifyLoaded)return;
    var btn=$('graphifyBtn'),status=$('graphifyStatus');
    btn.disabled=true;status.textContent='Carico il layer locale dai metadati…';
    var script=document.createElement('script');script.src='graphify-data.js';
    script.onerror=function(){btn.disabled=false;status.textContent='Il layer non è disponibile. Cubo e idee restano consultabili.';script.remove();};
    script.onload=function(){
      var extra=window.R3_GRAPHIFY_DATA;
      if(!extra||!Array.isArray(extra.nodes)||!Array.isArray(extra.links)){status.textContent='Layer non valido; nessuna modifica.';btn.disabled=false;return;}
      extra.nodes.forEach(function(n,i){
        var p=ideaPosition(n,i);
        addRecord({
          key:'GFY:'+n.id,id:n.id,title:n.title||n.id,type:'GRAPHIFY',domain:n.category||'Graphify',
          state:'METADATI_NON_LETTI',evidence:n.classificationBasis||'TITLE_ONLY',
          summary:'Documento individuato da Graphify. Classificazione strutturale da titolo e metadati; contenuto non letto.',
          refs:n.url?[{kind:'GOOGLE_DRIVE',label:n.sourceFile||n.title,url:n.url}]:[],
          source:n.sourceSystem||'Graphify RUN-001',aliases:[],year:typeof n.year==='number'?n.year:null,
          date:'Snapshot Graphify 2026-09',privacy:'PROJECT',kind:'graph',
          x:typeof n.fx==='number'?n.fx:p.x,y:typeof n.fy==='number'?n.fy:p.y,z:typeof n.fz==='number'?n.fz:p.z,
          color:n.color||'#8caabf',rawTextPresent:false
        });
      });
      extra.links.forEach(function(e){
        var endpoint=function(v){return typeof v==='object'&&v?v.id:v;};
        var a='GFY:'+endpoint(e.source),b='GFY:'+endpoint(e.target);
        if(!byKey.has(a)||!byKey.has(b))return;
        var ev=e.evidence||e.confidence||'AMBIGUOUS';
        edges.push({a:a,b:b,label:e.type||'relazione',evidence:ev,
          possible:/INFERRED|AMBIGUOUS|POSSIBLE/.test(ev),source:e.sourceSystem||'Graphify'});
      });
      graphifyLoaded=true;btn.textContent='✓ Layer Graphify caricato';
      status.textContent=extra.nodes.length+' documenti censiti e '+extra.links.length+' legami strutturali; 0 testi integrali letti.';
      refreshFilters();updateStats();renderCatalog();renderSources();scheduleDrawing();
    };
    document.head.appendChild(script);
  }

  function speak(text) {
    text=String(text||'').trim();
    if(!('speechSynthesis' in window)){ $('voiceStatus').textContent='Questo browser non dispone di lettura vocale.';return; }
    window.speechSynthesis.cancel();
    if(!text)return;
    var utterance=new SpeechSynthesisUtterance(text.slice(0,3600));
    utterance.lang='it-IT';utterance.rate=.96;utterance.pitch=1;
    utterance.onstart=function(){ $('voiceStatus').textContent='Sto leggendo la risposta…'; };
    utterance.onend=function(){ $('voiceStatus').textContent='Lettura terminata. Microfono spento.'; };
    utterance.onerror=function(){ $('voiceStatus').textContent='Lettura vocale non disponibile su questo dispositivo.'; };
    window.speechSynthesis.speak(utterance);
  }
  function reply(text,asVoice) {
    lastReply=String(text);$('voiceReply').textContent=lastReply;
    if(asVoice)speak(lastReply);
  }
  function detailSpeech() {
    if(!selectedRec){speak('Seleziona una scheda nel catalogo o nel Cubo.');return;}
    speak(selectedRec.title+'. '+(selectedRec.summary||'Titolo censito; testo integrale non presente.')+' Origine: '+selectedRec.source+'. Stato: '+selectedRec.state+'.');
  }
  function ask(q,asVoice) {
    var original=String(q||'').trim();
    if(!original){reply('Dimmi un nome o una domanda, per esempio: cerca SYNESIS.',asVoice);return;}
    var normalized=clean(original).replace(/[?!.,]/g,' ').replace(/\s+/g,' ').trim();
    if(/^(stop|ferma|silenzio|basta)\b/.test(normalized)){
      if('speechSynthesis' in window)window.speechSynthesis.cancel();
      reply('Ho fermato la lettura. Il microfono è spento.',false);return;
    }
    if(/(?:quante idee|numero di idee|quanti progetti)/.test(normalized)){
      reply('Nel registro derivato risultano 38 idee ufficiali e 26 moduli collegati. Sono schede documentali, non tutti progetti realizzati.',asVoice);return;
    }
    if(/(?:quanti documenti|graphify quanti)/.test(normalized)){
      reply('Il catalogo Graphify originale censiva 1.010 documenti mediante metadati, con zero testi integrali letti. Il layer opzionale non è una verifica semantica.',asVoice);return;
    }
    if(/(?:leggi|raccontami|spiegami).*(?:scheda|questa idea|questa invenzione)/.test(normalized)){
      reply(selectedRec ? selectedRec.title+'. '+(selectedRec.summary||'Il testo integrale non è stato recuperato.')+' Fonte: '+selectedRec.source : 'Seleziona prima una scheda.',asVoice);return;
    }
    if(/(?:apri|vai al|mostra|entra nel).*(?:cubo|3d)/.test(normalized)){
      showView('cubo');reply('Ho aperto il Cubo Quantico. Trascina per ruotarlo, seleziona un nodo per scoprirne le fonti.',asVoice);return;
    }
    if(/(?:apri|vai al|mostra|entra nel).*(?:grafo|connessioni|rete)/.test(normalized)){
      showView('grafo');reply('Ho aperto il Grafo. Le relazioni inferite sono separate dalle connessioni documentali.',asVoice);return;
    }
    var topic=normalized.replace(/^(?:raffaello\s+)?(?:per favore\s+)?(?:cerca|mostra|trova|quali (?:sono )?(?:le )?idee (?:legate|relative|su|riguardanti|di)|dimmi (?:di|su)|parlami (?:di|del|della)|voglio vedere|aprimi)\s+/,'');
    topic=topic.replace(/^(?:tutte |le |i |gli |su |il |la |lo |del |della |di )+/,'').trim();
    if(topic.length<2)topic=normalized;
    $('searchInput').value=topic;
    pageSize=60;showView('catalogo');renderCatalog();
    var found=results();
    if(found.length===1)select(found[0].key,true);
    reply(found.length ? 'Ho trovato '+found.length+' schede per '+topic+'. '+found.slice(0,3).map(function(r){return r.title;}).join('; ')+'. Puoi aprirle nel catalogo.' : 'Non trovo '+topic+' nello snapshot disponibile. Questo non significa che l’idea non esista nelle vecchie chat: l’archivio non è ancora completo.',asVoice);
  }
  var Recognition=window.SpeechRecognition||window.webkitSpeechRecognition;
  var recognition=null;
  function listen() {
    if(!Recognition){$('voiceStatus').textContent='Riconoscimento vocale non disponibile in questo browser o contesto. Puoi scrivere la richiesta e usare «Leggi la risposta».';showView('voce');return;}
    if(recognition){try{recognition.abort();}catch(_){} recognition=null;}
    showView('voce');
    try {
      var r=new Recognition();recognition=r;r.lang='it-IT';r.continuous=false;r.interimResults=false;r.maxAlternatives=1;
      $('voiceStatus').textContent='Ascolto attivo per una sola richiesta…';
      r.onresult=function(e){var t=e.results[0][0].transcript;$('askInput').value=t;$('voiceStatus').textContent='Riconosciuto: '+t;ask(t,true);};
      r.onerror=function(e){$('voiceStatus').textContent='Microfono o riconoscimento non disponibile ('+e.error+'). Puoi scrivere la richiesta.';};
      r.onend=function(){recognition=null;if($('voiceStatus').textContent.startsWith('Ascolto'))$('voiceStatus').textContent='Ascolto terminato. Microfono spento.';};
      r.start();
    }catch(_){recognition=null;$('voiceStatus').textContent='Non posso attivare il microfono in questo contesto. Usa la casella di testo.';}
  }

  function onSearchChanged(){pageSize=60;renderCatalog();scheduleDrawing();journeyStore(false);}
  ['searchInput','typeFilter','domainFilter','statusFilter'].forEach(function(id){
    $(id).addEventListener(id==='searchInput'?'input':'change',onSearchChanged);
  });
  $('showMore').addEventListener('click',function(){pageSize+=60;renderCatalog();});
  qs('[data-view]').forEach(function(b){b.addEventListener('click',function(){showView(b.dataset.view);});});
  $('goCube').addEventListener('click',function(){if(selectedRec)journeyNavigate(selectedKey,'cubo');else showView('cubo');});
  $('goGraph').addEventListener('click',function(){showView('grafo');});
  $('exportBook').addEventListener('click',exportBook);
  $('cubeReset').addEventListener('click',function(){cubeCamera={yaw:-.47,pitch:.3,zoom:1};scheduleDrawing();});
  $('graphReset').addEventListener('click',function(){graphCamera={zoom:1,dx:0,dy:0};scheduleDrawing();});
  ['cubeEdges','observedToggle','possibleToggle'].forEach(function(id){$(id).addEventListener('change',scheduleDrawing);});
  $('graphifyBtn').addEventListener('click',loadGraphify);
  $('listenBtn').addEventListener('click',listen);
  $('talkBtn').addEventListener('click',listen);
  $('readAnswerBtn').addEventListener('click',function(){speak(lastReply||$('voiceReply').textContent);});
  $('readDetail').addEventListener('click',detailSpeech);
  $('stopSpeechBtn').addEventListener('click',function(){if(recognition){recognition.abort();recognition=null;}if('speechSynthesis' in window)speechSynthesis.cancel();$('voiceStatus').textContent='Microfono e voce fermati.';});
  $('askBtn').addEventListener('click',function(){ask($('askInput').value,false);});
  $('askInput').addEventListener('keydown',function(e){if(e.key==='Enter')ask(e.target.value,false);});
  window.addEventListener('resize',scheduleDrawing);

  refreshFilters();updateStats();renderCatalog();
  if (!registryReady || !cubeReady) {
    $('catalogSummary').textContent='Attenzione: un dataset locale non è stato caricato. Verifica i file accanto a index.html.';
  }
  document.querySelector('.brand').addEventListener('click',function(ev){ev.preventDefault();if(selectedRec)journeyNavigate(selectedKey,'catalogo');else showView('catalogo');});
  initJourney();
})();
