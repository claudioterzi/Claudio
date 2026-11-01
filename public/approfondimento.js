/* Approfondimento — una schermata comune che si apre su ciò che tocchi.
   Tarocchi, Agorà, archivio dei copioni e Libro delle idee la usano allo stesso modo.
   <dialog> nativo: Esc, focus e lettori di schermo gestiti dal browser. © Claudio Terzi 2026. */
(function(root){
  'use strict';
  if (root.Approfondimento) return;
  const doc = root.document;
  let dialog, body, titleEl, kickerEl, restore = null, lastFocus = null;

  function style(){
    const s = doc.createElement('style');
    s.textContent = `
.approf{border:0;padding:0;margin:auto;width:min(760px,100%);max-width:100%;max-height:min(92vh,100%);max-height:min(92svh,100%);border-radius:20px;
  background:var(--approf-bg,#12151c);color:var(--approf-ink,#f1ece0);box-shadow:0 30px 90px rgba(0,0,0,.45);overflow:hidden}
.approf::backdrop{background:rgba(5,7,10,.72);backdrop-filter:blur(3px)}
.approf-frame{display:flex;flex-direction:column;max-height:inherit}
.approf-head{display:flex;align-items:flex-start;gap:12px;padding:18px 20px 12px;border-bottom:1px solid var(--approf-line,rgba(255,255,255,.12))}
.approf-head>div{flex:1;min-width:0}
.approf-kicker{font:700 .72rem/1.3 system-ui,sans-serif;letter-spacing:.14em;text-transform:uppercase;color:var(--approf-accent,#d7b86d)}
.approf-title{font:500 clamp(1.4rem,4.5vw,2rem)/1.15 Georgia,serif;margin:.3rem 0 0;overflow-wrap:anywhere}
.approf-close{flex:none;min-width:44px;min-height:44px;border-radius:50%;border:1px solid var(--approf-line,rgba(255,255,255,.2));
  background:transparent;color:inherit;font-size:1.2rem;cursor:pointer}
.approf-close:focus-visible{outline:3px solid var(--approf-accent,#d7b86d);outline-offset:3px}
.approf-body{overflow:auto;padding:16px 20px 26px;-webkit-overflow-scrolling:touch;overscroll-behavior:contain}
.approf-section{margin:0 0 18px}
.approf-section h3{font:700 .78rem/1.3 system-ui,sans-serif;letter-spacing:.1em;text-transform:uppercase;margin:0 0 6px;color:var(--approf-accent,#d7b86d)}
.approf-section p,.approf-section div.text{margin:0;line-height:1.7;white-space:pre-wrap;overflow-wrap:anywhere}
.approf-media{display:block;max-width:220px;width:100%;margin:0 auto 16px;border-radius:12px}
.approf-list{margin:0;padding-left:1.15rem;line-height:1.65}
.approf-list li{margin:.25rem 0}
.approf-links{display:flex;flex-wrap:wrap;gap:8px}
.approf-links button{min-height:40px;border-radius:999px;border:1px solid var(--approf-line,rgba(255,255,255,.2));background:transparent;
  color:inherit;padding:6px 14px;font:inherit;cursor:pointer}
@media(max-width:640px){.approf{width:100vw;max-width:100vw;max-height:100%;height:100%;border-radius:0;margin:0}
  .approf-frame{height:100%}.approf-body{flex:1}}
@media(prefers-reduced-motion:no-preference){.approf[open]{animation:approf-in .18s ease-out}
  @keyframes approf-in{from{opacity:0;transform:translateY(10px)}to{opacity:1;transform:none}}}`;
    doc.head.appendChild(s);
  }

  function build(){
    if (dialog) return;
    style();
    dialog = doc.createElement('dialog');
    dialog.className = 'approf';
    dialog.setAttribute('aria-labelledby', 'approf-title');
    dialog.innerHTML = '<div class="approf-frame"><header class="approf-head"><div><div class="approf-kicker" id="approf-kicker"></div>'
      + '<h2 class="approf-title" id="approf-title"></h2></div><button type="button" class="approf-close" aria-label="Chiudi l’approfondimento">✕</button></header>'
      + '<div class="approf-body"></div></div>';
    doc.body.appendChild(dialog);
    body = dialog.querySelector('.approf-body');
    titleEl = dialog.querySelector('#approf-title');
    kickerEl = dialog.querySelector('#approf-kicker');
    dialog.querySelector('.approf-close').addEventListener('click', close);
    dialog.addEventListener('click', e => { if (e.target === dialog) close(); });
    dialog.addEventListener('close', cleanup);
  }

  function text(tag, value, cls){ const n = doc.createElement(tag); if (cls) n.className = cls; n.textContent = value == null ? '' : String(value); return n; }

  function section(s){
    const box = doc.createElement('section'); box.className = 'approf-section';
    if (s.titolo) box.appendChild(text('h3', s.titolo));
    if (s.nodo) box.appendChild(s.nodo);
    else if (Array.isArray(s.elenco)) {
      const ul = doc.createElement('ul'); ul.className = 'approf-list';
      s.elenco.filter(v => v != null && String(v).trim()).forEach(v => ul.appendChild(text('li', v)));
      box.appendChild(ul);
    } else if (Array.isArray(s.collegamenti)) {
      const wrap = doc.createElement('div'); wrap.className = 'approf-links';
      s.collegamenti.forEach(l => { const b = text('button', l.etichetta); b.type = 'button'; b.addEventListener('click', () => { if (dialog.open && typeof dialog.close === 'function') { dialog.addEventListener('close', () => l.apri(), { once: true }); close(); } else l.apri(); }); wrap.appendChild(b); });
      box.appendChild(wrap);
    } else box.appendChild(text('div', s.testo, 'text'));
    return box;
  }

  function show(title, kicker){
    titleEl.textContent = title || '';
    kickerEl.textContent = kicker || '';
    kickerEl.hidden = !kicker;
    lastFocus = doc.activeElement;
    if (typeof dialog.showModal === 'function') { if (!dialog.open) dialog.showModal(); }
    else dialog.setAttribute('open', '');
    body.scrollTop = 0;
    dialog.querySelector('.approf-close').focus();
  }

  /** open({titolo, sopratitolo, immagine, sezioni:[{titolo, testo|elenco|collegamenti|nodo}]}) */
  function open(opts){
    build(); cleanup(true);
    body.replaceChildren();
    if (opts.immagine) { const img = doc.createElement('img'); img.className = 'approf-media'; img.src = opts.immagine; img.alt = opts.titolo || ''; if (opts.rotazione) img.style.transform = 'rotate(' + Number(opts.rotazione) + 'deg)'; body.appendChild(img); }
    (opts.sezioni || []).filter(s => s && (s.nodo || s.elenco?.length || s.collegamenti?.length || (s.testo != null && String(s.testo).trim()))).forEach(s => body.appendChild(section(s)));
    show(opts.titolo, opts.sopratitolo);
  }

  /** Move an existing element (with its listeners) into the screen; it goes back on close. */
  function openElement(el, opts = {}){
    build(); cleanup(true);
    body.replaceChildren();
    restore = { el, parent: el.parentNode, next: el.nextSibling };
    body.appendChild(el);
    show(opts.titolo, opts.sopratitolo);
  }

  function cleanup(keepOpen){
    if (restore && restore.parent) restore.parent.insertBefore(restore.el, restore.next);
    restore = null;
    if (keepOpen !== true && lastFocus && typeof lastFocus.focus === 'function') { try { lastFocus.focus(); } catch (_) {} }
  }
  function close(){ if (!dialog) return; if (typeof dialog.close === 'function' && dialog.open) dialog.close(); else { dialog.removeAttribute('open'); cleanup(); } }
  function isOpen(){ return Boolean(dialog && dialog.open); }

  root.Approfondimento = Object.freeze({ open, openElement, close, isOpen });
})(typeof window === 'undefined' ? globalThis : window);
