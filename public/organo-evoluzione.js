(async function () {
  'use strict';
  const host=document.getElementById('organo-evoluzione');if(!host)return;
  const el=(tag,text,cls)=>{const n=document.createElement(tag);if(text)n.textContent=text;if(cls)n.className=cls;return n;};
  try {
    const response=await fetch('/organo-evoluzione.json');if(!response.ok)throw Error();const data=await response.json();
    host.append(el('p','L’ORGANO VIVO · REVISIONE '+data.revision,'evolution-kicker'),el('h2','Nuove possibilità, radici riconoscibili.'),el('p','Raffaello propone, confronta e documenta. Una nuova materia entra nelle composizioni quando la sua disponibilità e la preparazione sono confermate. Una materia sospesa resta nella storia delle formule.'));
    const grid=el('div','','evolution-grid');host.append(grid);
    for(const p of data.proposals){const card=el('article');card.append(el('span',p.status==='admitted'?'Ammessa nell’organo':'Proposta · disponibilità da confermare','evolution-tag'),el('h3',p.name),el('p',p.type,'evolution-type'),el('p',p.profile),el('p',p.why));const d=el('details'),summary=el('summary','Come valutarla');d.append(summary,el('p',p.test));card.append(d);
      for(const source of p.sources||[]){try{const u=new URL(source.url);if(u.protocol!=='https:')continue;const a=el('a',source.title+' ↗');a.href=u.href;a.target='_blank';a.rel='noopener noreferrer';card.append(a);}catch(_){}}
      grid.append(card);
    }
    if(data.overrides.length){const list=el('ul');for(const s of data.overrides)list.append(el('li','N° '+s.n+' · '+(s.status==='suspended'?'sospesa':'attiva')+' · '+s.reason));host.append(el('h3','Stato delle materie'),list);}
    host.append(el('p','Le tre proposte non sono acquisti già effettuati. Per attivarle servono identificazione del prodotto, fornitore, preparazione effettiva e documentazione tecnica. Ogni modifica mantiene numeri e cataloghi storici per ricostruire i codici precedenti.','evolution-note'));
  }catch(_){host.append(el('p','Il registro di evoluzione non è disponibile adesso. Il catalogo storico rimane consultabile.'));}
})();
