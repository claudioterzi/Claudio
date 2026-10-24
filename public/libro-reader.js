/* Reader for the preserved Terzi integral edition. Static files only. */
(function(){
  'use strict';
  const $=id=>document.getElementById(id),search=$('book-search'),results=$('book-results'),more=$('book-more'),status=$('book-status'),content=$('book-content');
  let index=null,indexRequest=null,shown=20,loadVersion=0,activeChapter=null;
  const cache=new Map();
  const mobile=matchMedia('(max-width:760px)'),indexPanel=$('book-index-toggle');
  indexPanel.open=!mobile.matches;
  const normalize=value=>String(value).normalize('NFD').replace(/[\u0300-\u036f]/g,'').toLocaleLowerCase('it');
  async function getIndex(){
    if(index)return index;
    if(!indexRequest)indexRequest=fetch('libro/indice.json').then(response=>{if(!response.ok)throw Error('Indice non disponibile');return response.json()}).then(data=>{index=data;return data}).catch(error=>{indexRequest=null;throw error});
    return indexRequest;
  }
  function renderResults(){
    if(!index)return;
    const query=normalize(search.value.trim()),number=/^\d+$/.test(query)?Number(query):null;
    const matching=index.perfumes.filter(item=>!query||(number!==null?item.n===number:normalize(item.title+' '+item.family+' '+item.summary).includes(query)));
    results.replaceChildren();
    matching.slice(0,shown).forEach(item=>{const li=document.createElement('li'),link=document.createElement('a'),detail=document.createElement('span');link.href='#'+item.id;link.textContent=String(item.n).padStart(3,'0')+' · '+item.title;detail.textContent=item.family;li.append(link,detail);results.append(li)});
    $('book-results-count').textContent=matching.length+' profumi trovati · '+Math.min(shown,matching.length)+' mostrati';
    more.hidden=shown>=matching.length;
  }
  function focusAnchor(anchor){
    const target=document.getElementById(anchor)||content;
    target.setAttribute('tabindex','-1');target.scrollIntoView({block:'start',behavior:'auto'});target.focus({preventScroll:true});
  }
  function tableRegions(){
    content.querySelectorAll('table').forEach(table=>{const region=document.createElement('div');region.className='book-table-scroll';region.tabIndex=0;region.setAttribute('role','region');region.setAttribute('aria-label','Tabella del capitolo: scorrimento orizzontale');table.replaceWith(region);region.append(table)});
  }
  function chapterNavigation(chapter){
    const position=index.chapters.indexOf(chapter);
    for(const [id,offset] of [['book-prev',-1],['book-next',1]]){const link=$(id),next=index.chapters[position+offset];link.hidden=!next;if(next){link.href='#'+next.id;link.textContent=(offset<0?'← ':'')+next.title+(offset>0?' →':'')}}
  }
  async function openHash(moveFocus){
    const version=++loadVersion;
    $('book-retry').hidden=true;content.setAttribute('aria-busy','true');
    try{
      await getIndex();renderResults();
      let anchor=decodeURIComponent(location.hash.slice(1))||'introduzione';
      const chapter=index.chapters.find(item=>item.id===anchor||item.anchors.includes(anchor))||(anchor==='book-content'?index.chapters[0]:null);
      if(!chapter)throw Error('Questo riferimento non è nel libro. Scegli un capitolo dall’indice.');
      status.textContent='Carico '+chapter.title+'…';
      if(activeChapter!==chapter.id){
        let fragment=cache.get(chapter.id);
        if(!fragment){const response=await fetch(chapter.url);if(!response.ok)throw Error('Capitolo non disponibile. Puoi riprovare o aprire la versione integrale.');fragment=await response.text();cache.set(chapter.id,fragment)}
        if(version!==loadVersion)return;
        content.innerHTML=fragment;
        const heading=content.querySelector('h2');if(heading&&!heading.id)heading.id=chapter.id;
        activeChapter=chapter.id;tableRegions();chapterNavigation(chapter);
      }
      if(version!==loadVersion)return;
      status.textContent=chapter.title+' · capitolo aperto';
      if(moveFocus){if(mobile.matches)indexPanel.open=false;focusAnchor(anchor)}
    }catch(error){if(version===loadVersion){status.textContent=error.message||'Caricamento non riuscito.';$('book-retry').hidden=false}}
    finally{if(version===loadVersion)content.removeAttribute('aria-busy')}
  }
  search.addEventListener('input',()=>{shown=20;renderResults()});
  more.addEventListener('click',()=>{shown+=20;renderResults()});
  $('book-index-open').addEventListener('click',()=>{indexPanel.open=true;indexPanel.scrollIntoView({block:'start',behavior:'auto'});search.focus({preventScroll:true})});
  results.addEventListener('click',event=>{const link=event.target.closest('a');if(link&&link.hash===location.hash){event.preventDefault();openHash(true)}});
  $('book-retry').addEventListener('click',()=>openHash(true));
  window.addEventListener('hashchange',()=>openHash(true));
  status.textContent='Carico l’indice del libro…';
  openHash(Boolean(location.hash));
})();
