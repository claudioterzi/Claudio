/* Ogni luogo ha una voce visiva. Concept e direzione: Claudio Terzi, 2026. */
(function () {
  'use strict';
  if (window.TerziAtmosfere) return;
  window.TerziAtmosfere = true;
  const base = new URL('.', document.currentScript.src);
  const scenes = {
    index: ['La soglia', 'Il momento prima di una domanda.', 'Una soglia di pietra, il buio e una luce calda oltre la porta.'],
    home: ['La possibilità', 'Le idee prendono posto nel mondo.', 'Un tavolo creativo sopra una città al crepuscolo.'],
    atelier: ['La trasformazione', 'Qualcosa che senti diventa una creazione.', 'Vetro ambrato, legno vissuto e luce calda in un atelier di profumeria.'],
    parfums: ['Il desiderio', 'Una presenza che rimane.', 'Un flacone prezioso, ambra luminosa e ombre profonde.'],
    libro: ['La memoria', 'Le pagine custodiscono ciò che ritorna.', 'Un libro aperto, una biblioteca silenziosa e polvere nella luce del tramonto.'],
    organo: ['La materia', 'Ogni essenza apre una possibilità.', 'Essenze ambrate e materie botaniche su un banco scuro.'],
    formula: ['La precisione', 'Dare una misura all’intuizione.', 'Pipette, una bilancia e vetro in un laboratorio al crepuscolo.'],
    spesa: ['La cura', 'Preparare bene è già creare.', 'Una preparazione botanica fatta con cura su un piano scuro.'],
    valigia: ['La libertà', 'Portare con sé ciò che conta.', 'Una valigia di cuoio e piccole essenze accanto a una finestra bagnata.'],
    viaggi: ['L’attesa', 'La partenza comincia prima del viaggio.', 'Una stazione al crepuscolo, binari bagnati e un treno illuminato vicino al porto.'],
    flight_hunter: ['Lo slancio', 'Il mondo torna vicino.', 'Un aereo oltre il vetro, pista bagnata e cielo al tramonto.'],
    oracolo: ['L’orizzonte', 'Lasciare spazio a ciò che ancora non sai.', 'Un faro solitario nell’ora blu, con una luce calda verso il mare.'],
    parti: ['La decisione', 'Una strada diventa la tua.', 'Due vie si dividono al crepuscolo, nell’attesa di una scelta.'],
    creazioni: ['Il gesto', 'La materia conserva il segno di chi crea.', 'Attrezzi da scultore, polvere e una pietra ancora incompiuta.'],
    opera: ['La tensione', 'Il calore che trasforma la resistenza.', 'Acciaio, scintille di saldatura e riflessi di un cantiere al tramonto.'],
    opuscolo: ['La trasmissione', 'Un pensiero passa da una mano all’altra.', 'Una stamperia, carta e luce calda sulle superfici lavorate.'],
    alpha: ['L’intuizione', 'Ascoltare prima di dare un nome.', 'Carte coperte, una candela e un tavolo di legno nell’ombra.']
  };
  const path = location.pathname.replace(base.pathname, '').replace(/\/$/, '').replace(/\.html$/, '');
  const aliases = {'': 'index', profumo: 'atelier', flight: 'flight_hunter', 'atelier/archivio': 'libro', 'atelier/riapri': 'libro', 'atelier/esempio': 'opera'};
  const key = aliases[path] || path;
  const available = ["alpha", "atelier", "creazioni", "flight_hunter", "formula", "home", "index", "libro", "opera", "opuscolo", "oracolo", "organo", "parfums", "parti", "spesa", "valigia", "viaggi"];
  const scene = available.includes(key) ? scenes[key] : null;
  if (!scene) return;
  const css = document.createElement('link'); css.rel = 'stylesheet'; css.href = new URL('atmosfere.css', base); document.head.appendChild(css);
  function mount() {
    document.body.dataset.atmosfera = key;
    const background = document.createElement('div'); background.className = 'terzi-atmosfera'; background.setAttribute('aria-hidden', 'true');
    const picture = document.createElement('picture');
    const small = document.createElement('source'); small.media = '(max-width: 700px)'; small.srcset = new URL('images/atmosfere/' + key + '-mobile.webp', base);
    const img = document.createElement('img'); img.src = new URL('images/atmosfere/' + key + '.webp', base); img.alt = ''; img.decoding = 'async'; img.fetchPriority = 'high';
    picture.append(small, img); background.append(picture); document.body.prepend(background);
    const note = document.createElement('div'); note.className = 'terzi-atmosfera-nota';
    const title = document.createElement('span'); title.textContent = scene[0];
    const phrase = document.createElement('p'); phrase.textContent = scene[1]; note.append(title, phrase);
    const anchor = document.querySelector('.container > header, .container > .header, .libro > .copertina, .studio > .identity, .container > h1');
    if (anchor) anchor.prepend(note);
    else {
      const main = document.querySelector('.container, main, .libro');
      if (main) main.prepend(note); else document.body.insertBefore(note, background.nextSibling);
    }
    const launch = document.createElement('button'); launch.type = 'button'; launch.className = 'terzi-raffaello'; launch.textContent = 'Raffaello'; launch.setAttribute('aria-haspopup', 'dialog');
    const dialog = document.createElement('dialog'); dialog.className = 'terzi-raffaello-dialog'; dialog.setAttribute('aria-labelledby', 'terzi-raffaello-title');
    const close = document.createElement('button'); close.type = 'button'; close.className = 'terzi-raffaello-close'; close.textContent = 'Chiudi';
    const name = document.createElement('h2'); name.id = 'terzi-raffaello-title'; name.textContent = 'Raffaello · L’Atelier di Claudio';
    const voice = document.createElement('p'); voice.textContent = 'Qui l’atmosfera è ' + scene[0].toLowerCase() + '. ' + scene[1];
    const invitation = document.createElement('p'); invitation.textContent = 'Portala nell’Atelier: posso interpretare un racconto, una foto e i profumi che ami, poi comporre con le essenze dell’Organo Terzi.';
    const action = document.createElement('a'); action.className = 'terzi-raffaello-action'; action.href = new URL('atelier.html', base); action.textContent = 'Crea un profumo da questa atmosfera';
    action.addEventListener('click', () => { try { sessionStorage.setItem('terzi-atmosfera-intenzione', 'Vorrei un profumo ispirato a questa atmosfera: ' + scene[2]); } catch (_) {} });
    const details = document.createElement('p'); details.className = 'terzi-raffaello-credit'; details.textContent = 'Assistente AI dell’Atelier · Concept e direzione: Claudio Terzi';
    dialog.append(close, name, voice, invitation, action, details); document.body.append(launch, dialog);
    launch.addEventListener('click', () => dialog.showModal()); close.addEventListener('click', () => dialog.close());
    dialog.addEventListener('click', event => { if (event.target === dialog) { const r = dialog.getBoundingClientRect(); if (event.clientX < r.left || event.clientX > r.right || event.clientY < r.top || event.clientY > r.bottom) dialog.close(); } });
    if (key === 'atelier' && path !== 'profumo') {
      try { const draft = sessionStorage.getItem('terzi-atmosfera-intenzione'); const input = document.getElementById('intenzione'); if (draft && input && !input.value) { input.value = draft; sessionStorage.removeItem('terzi-atmosfera-intenzione'); } } catch (_) {}
    }
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', mount); else mount();
})();
