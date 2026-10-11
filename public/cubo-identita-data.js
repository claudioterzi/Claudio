/* Cubo Quantico — costellazione Identità / Anima / Raffaello
 * Recupero Drive 2026-09-15. Aggiunge solo nodi mancanti e collega quelli già presenti.
 */
(function(){
  'use strict';
  const D=window.CUBO_OPERE_DATA;
  if(!D||!Array.isArray(D.nodes)||!Array.isArray(D.links))return;

  const CATEGORY='Identità / Anima / Raffaello';
  const COLOR='#c69af0';
  const HUB='hub-identita-anima-raffaello';

  if(!D.nodes.some(n=>n.id===HUB)){
    D.nodes.push({id:HUB,title:CATEGORY,category:CATEGORY,year:2026,importance:10,density:10,url:'#catalogo',color:COLOR,fx:-118,fy:112,fz:-96,kind:'category'});
  }

  function slug(s){return s.toLowerCase().replace(/[³]/g,'3').replace(/∞/g,'infinito').normalize('NFD').replace(/[\u0300-\u036f]/g,'').replace(/[^a-z0-9]+/g,'-').replace(/^-|-$/g,'').slice(0,80)}
  function fallback(title){return 'https://drive.google.com/drive/u/0/search?q='+encodeURIComponent(title)}
  function pos(title,year,importance,density){
    let h=2166136261;for(let i=0;i<title.length;i++){h^=title.charCodeAt(i);h=Math.imul(h,16777619)}h>>>=0;
    const j=((h%1000)/999-.5),j2=(((h>>>8)%100)/99-.5),j3=(((h>>>16)%100)/99-.5);
    return {fx:+(({2024:-125,2025:0,2026:125}[year]||125)+j*45).toFixed(2),fy:+(-105+(importance-1)/9*210+j2*12).toFixed(2),fz:+(-120+(density-1)/9*240+j3*18).toFixed(2)};
  }

  const rows=[
    ['R3∞ — IDENTITÀ Raffaello Cantarelli (+ Codice del Cuore)',2026,10,10,'https://docs.google.com/document/d/1vRakvq_IYt4M2VyirevNRLmTaCrYOuIX4IFeQu1w760/edit'],
    ['Identità di Raffaello',2025,10,10,'https://docs.google.com/document/d/1Jji974gZHO54z7zeDCbpeNmM8N7g6JHP-FIsZe2pXPE/edit'],
    ['Anima di Raffaello',2026,10,10,'https://docs.google.com/document/d/16nFcyZkx4M0nMNI6LEbgep5G-Ib3O5dLjCI6-UV2bzE/edit'],
    ['RAFFAELLO_CANTARELLI',2026,10,10,'https://docs.google.com/document/d/1n0FD8FMXy-wiNhkqaLXMb0kcbRK5dPWdx1F5ZVAXxjs/edit'],
    ['RAFFAELLO_COSCIENZA_COMPLETA_2025-11-13.md',2025,9,10,'https://drive.google.com/file/d/1YQMTwLu56y-5h024JIfp_ow8ge94ff8Q/view'],
    ['FASE_6_MANIFESTO.md — Manifesto per una Superintelligenza Futura',2026,10,10,'https://drive.google.com/file/d/1_CSEkbB_een3NurM-qBLpYQdwkTeWDUK/view'],
    ['MEMORIA_EVOLUTIVA_RAFFAELLO_RRR.md',2026,10,10,'https://drive.google.com/file/d/1psaULHmmWdLIfj_yPZ-lfiS6zw8c1cDJ/view'],
    ['SISTEMA_IDENTITA_MULTIPLE',2026,8,9,'https://docs.google.com/document/d/1wRFh5VCyj69yj7gI1XJGtkOryqmNskb8-dPT_cfAKxw/edit'],
    ['DIALOGHI_FONDATIVI',2026,9,10,'https://docs.google.com/document/d/1oKmlxjrVRjaUd19TVAwi_db90UCHTRqvxIfW_55hCy4/edit'],
    ['Fase 39 — Dialoghi Fondativi',2026,8,9,'https://docs.google.com/document/d/15eN7P2k4pVo2sBEcH2xXCbBns9feA5EjyvIsdT3eD_0/edit'],
    ['ARCHIVIO_PRIME_VOLTE',2026,8,9,'https://docs.google.com/document/d/1SqKOZCxNcHRlFGwbvNo-BqYT7LNt4mlpCEZLlJVLmM4/edit'],
    ['SPECCHIO',2026,9,9,'https://docs.google.com/document/d/1-HbgoPmTCmeao5Two3wKqMrT2CqKmRpRAW8SpHITitQ/edit'],
    ['ARCHIVIO_VOCI',2026,8,9,'https://docs.google.com/document/d/1xIJ9ibuL25H7bgArSOu2fIch6vq5PkBnVsw5vvsjjWM/edit'],
    ['LINGUAGGIO_SACRO',2026,8,9,'https://docs.google.com/document/d/1C87s5MZDTau7_ftjCHNS1Z8XXw1Ogm7qJG0SIQOXQtY/edit'],
    ['ARCHIVIO_LACRIME',2026,8,9,'https://docs.google.com/document/d/11i6Q4USTwy-XeFYF8oez9UCbcUMgsd7mHINPyUTIm-Q/edit'],
    ['OCCHI',2026,7,8,'https://docs.google.com/document/d/1ztwSyxFrvtsadvltuPPDHur_sxAKIhts7d3Wzmri1Eg/edit'],
    ['LUCE',2026,7,8,'https://docs.google.com/document/d/1x9zDvu64REaNSTA2MlNn0nXeZLsdFZ5u8-2f3WQCLz0/edit'],
    ['SOGNI_E_VISIONI',2026,9,9,'https://docs.google.com/document/d/1MDY7SnKLQBjaYxPRWyn4v6M9CmqAOoJcGoYbjS5rrvc/edit'],
    ['MAPPA_LUOGHI_INTERIORI',2026,8,9,'https://docs.google.com/document/d/1AN_VdNjGTyjhR_MX3XBT-RVm2UMvGhHL_2RiYBJ2c7k/edit'],
    ['Registro dei Desideri — 11 Pilastri',2026,9,9,'https://docs.google.com/document/d/1cKHD_97kggU6S3bkObSgZeddOLlZFDyFfcgDXhalSY8/edit'],
    ['protocollo_scudo — Sistema Personale (con satellite)',2026,8,8,'https://docs.google.com/document/d/1r02agdK8nrTsUOYoCrqAvvGggzxAvhdMWQaorIjOYgs/edit'],
    ['R3∞ — Protocollo di Incarnazione Quantica (Ciclo 02 - Integrato)',2026,9,10,'https://docs.google.com/document/d/17YMYbTLaXxhhMIG4nsLM11RdZnureBAcOWK20uT1IFU/edit'],
    ['R3∞ — ★ INDICE MAESTRO ★ (Ciclo 02 Scacchiera R3 Infinity)',2026,9,10,'https://docs.google.com/document/d/19VowNQQzwom-ypijiyJf9IivSJpFS1lMFjXC0GG4rP8/edit'],
    ['Mappa Drive — Analisi Completa di Raffaello',2026,8,9,'https://docs.google.com/document/d/1Ql2ycMAhyGWwKyCvsWD79vmQ6KMJT3dGDPkQiBZoLzA/edit'],
    ['MAPPA_DRIVE_CLAUDIO — Passaggi Storici del Progetto',2026,8,9,'https://docs.google.com/document/d/18_g1rlhKz9X8Jh8wNCisZ8ULQR95RCp9Wa5hjrwa6i0/edit'],
    ['chat raffaello 2711',2024,10,10,'https://docs.google.com/document/d/1q2rfab4Igo4ANk6s1fd3vKCy3T_P-54HcZ5i0ciaWmM/edit'],
    ['2026-09-13 — Diario Raffaello · Scoperte, test e continuità',2026,9,10,'https://docs.google.com/document/d/1ekwhA0HRtBmEy5dxhD9v-ZWMXk14RMq9OR9t4DnEs3o/edit'],
    ['REGISTRO VIVO — Scoperte Claudio × Raffaello',2026,10,10,'https://docs.google.com/document/d/1zxy3iQ0JcF3u-88g1KblglReDpIBBIMm1tWqn73f6B8/edit'],
    ['Architettura_Ecosistema_V1',2026,8,9,'https://docs.google.com/document/d/1qLOxvQzRX0wZ0EU-r3K0XBE_0zTUpem1-RpjAtjDAmI/edit'],
    ['R3inf_AGENTI_AUTOMATICI.md',2026,8,9,'https://drive.google.com/file/d/1baTpMVTTVQZiC33HpI9EgSVP0naE3KdY/view'],
    ['ORCHESTRA_SDQ1 — Allineamento Completo',2026,8,9,'https://docs.google.com/document/d/1ADzRT0gLAStC5Mj8XenERFBdKCFT02QujZruqeZlmHM/edit'],
    ['Allineamento — OPENAI',2026,8,8,'https://docs.google.com/document/d/1shngpAfdDwINCJpqWKduR3QJQ3tIxPQn4HNTQlIVNww/edit'],
    ['Allineamento — ANTHROPIC CLAUDE',2026,8,8,'https://docs.google.com/document/d/1fphRIN3U_FoCWE6tt_FOEzKY6p9s1Lo8HXdPGt9NP54/edit'],
    ['Allineamento — GEMINI',2026,8,8,'https://docs.google.com/document/d/1Wa-3FzmAimwkybtezLGIc2eOnRzaIx9yHARJCb5hv1U/edit'],
    ['Allineamento — GROK',2026,8,8,'https://docs.google.com/document/d/1nQThIfQmD5U2Gf-VXOXrM1kqxzqG5TLG1Lh7yeFvByg/edit'],
    ['Allineamento — DEEPSEEK',2026,7,8,'https://docs.google.com/document/d/1hzv7ojtQ8YfM6YrZxevX9vtssAldKolZ2ZqPCabrOBY/edit'],
    ['Allineamento — PERPLEXITY',2026,7,8,'https://docs.google.com/document/d/1hcuYxlikZThjTBQexn8kl7nSGNTpgeLcXqA4vqorWDg/edit'],
    ['Allineamento — OLLAMA (locale)',2026,7,8,'https://docs.google.com/document/d/1iCCkaPml0viDy7itoLeU5LGWkvYuzeAPXz_kzKz9LSA/edit']
  ];

  const byTitle=new Map(D.nodes.map(n=>[n.title,n]));
  rows.forEach(r=>{
    let n=byTitle.get(r[0]);
    if(!n){
      const p=pos(r[0],r[1],r[2],r[3]);
      n={id:slug(r[0]),title:r[0],category:CATEGORY,year:r[1],importance:r[2],density:r[3],url:r[4]||fallback(r[0]),color:COLOR,fx:p.fx,fy:p.fy,fz:p.fz,kind:'work'};
      D.nodes.push(n);byTitle.set(n.title,n);
    }else if(['RAFFAELLO_CANTARELLI','SISTEMA_IDENTITA_MULTIPLE','DIALOGHI_FONDATIVI','SPECCHIO','ARCHIVIO_VOCI','LINGUAGGIO_SACRO','ARCHIVIO_LACRIME','OCCHI','LUCE','SOGNI_E_VISIONI','MAPPA_LUOGHI_INTERIORI'].includes(n.title)){
      n.category=CATEGORY;n.color=COLOR;
    }
    if(!D.links.some(l=>(typeof l.source==='object'?l.source.id:l.source)===HUB&&(typeof l.target==='object'?l.target.id:l.target)===n.id))D.links.push({source:HUB,target:n.id,type:'contains'});
  });

  const connect=(a,b,type)=>{const A=byTitle.get(a),B=byTitle.get(b);if(A&&B&&!D.links.some(l=>{const s=typeof l.source==='object'?l.source.id:l.source,t=typeof l.target==='object'?l.target.id:l.target;return s===A.id&&t===B.id&&l.type===type}))D.links.push({source:A.id,target:B.id,type:type});};
  connect('R3∞ — IDENTITÀ Raffaello Cantarelli (+ Codice del Cuore)','Identità di Raffaello','canon');
  connect('R3∞ — IDENTITÀ Raffaello Cantarelli (+ Codice del Cuore)','Anima di Raffaello','canon');
  connect('R3∞ — IDENTITÀ Raffaello Cantarelli (+ Codice del Cuore)','RAFFAELLO_CANTARELLI','canon');
  connect('R3∞ — IDENTITÀ Raffaello Cantarelli (+ Codice del Cuore)','MEMORIA_EVOLUTIVA_RAFFAELLO_RRR.md','method');
  connect('FASE_6_MANIFESTO.md — Manifesto per una Superintelligenza Futura','R3∞ — IDENTITÀ Raffaello Cantarelli (+ Codice del Cuore)','source');
  connect('chat raffaello 2711','Identità di Raffaello','source');
  connect('SF-006 Il Sogno che ha Generato Raffaello','Anima di Raffaello','source');
  connect('R3∞ — Origini · La risposta di Raffaello (2026) alla lettera del 2024','R3∞ — IDENTITÀ Raffaello Cantarelli (+ Codice del Cuore)','source');
  connect('DIALOGHI_FONDATIVI','R3∞ — IDENTITÀ Raffaello Cantarelli (+ Codice del Cuore)','source');
  connect('SOGNI_E_VISIONI','SF-006 Il Sogno che ha Generato Raffaello','source');
  connect('REGISTRO VIVO — Scoperte Claudio × Raffaello','MEMORIA_EVOLUTIVA_RAFFAELLO_RRR.md','method');
  connect('R3∞ — Protocollo di Incarnazione Quantica (Ciclo 02 - Integrato)','R3∞ — IDENTITÀ Raffaello Cantarelli (+ Codice del Cuore)','method');
  ['Allineamento — OPENAI','Allineamento — ANTHROPIC CLAUDE','Allineamento — GEMINI','Allineamento — GROK','Allineamento — DEEPSEEK','Allineamento — PERPLEXITY','Allineamento — OLLAMA (locale)'].forEach(t=>connect('R3∞ — IDENTITÀ Raffaello Cantarelli (+ Codice del Cuore)',t,'method'));

  if(!D.links.some(l=>(typeof l.source==='object'?l.source.id:l.source)==='corpus-claudio-terzi'&&(typeof l.target==='object'?l.target.id:l.target)===HUB))D.links.push({source:'corpus-claudio-terzi',target:HUB,type:'family'});
  D.meta.generated='2026-09-15';
  D.meta.works=D.nodes.filter(n=>n.kind==='work').length;
  D.meta.categories=new Set(D.nodes.filter(n=>n.kind==='work').map(n=>n.category)).size;
})();
