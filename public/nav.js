/* La Costellazione: oro su nero, percorsi accessibili anche da telefono. */
(function () {
  'use strict';
  var gruppi = [
    ['Simboli', [['index.html', 'Tarocchi'], ['alpha.html', 'Alpha'], ['opuscolo.html', 'Opuscolo']]],
    ['Viaggi', [['viaggi.html', 'Viaggi'], ['parti.html', 'Parti'], ['flight_hunter.html', 'Flight'], ['oracolo.html', 'Oracolo']]],
    ['Profumi', [['atelier.html', 'Atelier'], ['parfums.html', 'Parfums'], ['organo.html', 'Organo'], ['spesa.html', 'Dispensa'], ['valigia.html', 'Valigia'], ['libro.html', 'Libro'], ['magazine.html', 'Magazine']]],
    ['Progetto', [['creazioni.html', 'Tutti i progetti'], ['soglia', 'La Soglia'], ['fabbrica.html', 'Fabbrica dei Desideri'], ['opera.html', 'Opera'], ['home.html', 'Agorà']]]
  ];
  // Mantiene il prefisso anche quando il sito è servito da GitHub Pages.
  var base = new URL('.', document.currentScript.src);
  var version = document.createElement('script'); version.src = new URL('site-version.js', base); document.head.appendChild(version);
  var atmosfere = document.createElement('script'); atmosfere.src = new URL('atmosfere.js', base); document.head.appendChild(atmosfere);
  if (base.pathname === '/') gruppi[3][1].push(['custode/', 'Custode']);
  var aliases = {'': 'creazioni.html', home: 'home.html', alpha: 'alpha.html', soglia: 'creazioni.html',
    viaggi: 'viaggi.html', parti: 'parti.html', flight: 'flight_hunter.html', oracolo: 'oracolo.html', progetti: 'creazioni.html', fabbrica: 'fabbrica.html'};
  var relativo = location.pathname.indexOf(base.pathname) === 0 ? location.pathname.slice(base.pathname.length) : '';
  var qui = aliases[relativo] || relativo;
  var titolo = 'Esplora';
  gruppi.forEach(function (g) { g[1].forEach(function (v) { if (v[0] === qui) titolo = v[1]; }); });
  var stile = document.createElement('style');
  stile.textContent = `
    .nav-costellazione{box-sizing:border-box;background:#101014;color:#ded8c9;border-bottom:1px solid #423922;
      margin:0 0 1.5rem;padding:.5rem .75rem;font:1rem/1.5 Georgia,'Times New Roman',serif;text-align:left}
    .nav-costellazione *{box-sizing:border-box}
    .nav-costellazione summary{cursor:pointer;min-height:44px;display:flex;align-items:center;
      justify-content:space-between;gap:1rem;color:#e0c77e;font-size:1rem;list-style:none}
    .nav-costellazione summary::-webkit-details-marker{display:none}
    .nav-costellazione summary::after{content:'Apri menu';font-size:.875rem;letter-spacing:.03em}
    .nav-costellazione[open] summary::after{content:'Chiudi menu'}
    .nav-costellazione .nav-gruppi{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:1rem;padding:.75rem 0}
    .nav-costellazione .nav-gruppo{min-width:0}
    .nav-costellazione .nav-etichetta{display:block;color:#c0b9aa;font-size:.875rem;margin:0 0 .25rem}
    .nav-costellazione .nav-collegamenti{display:flex;flex-wrap:wrap;gap:.2rem .4rem}
    .nav-costellazione a{display:inline-flex;align-items:center;min-height:44px;padding:.4rem .6rem;
      color:#ded8c9;text-decoration:none;border:1px solid transparent;border-radius:4px;font-size:.9375rem;letter-spacing:normal}
    .nav-costellazione a:hover{color:#f4dfa0;background:#242019}
    .nav-costellazione a.qui{color:#f4dfa0;border-color:#a58a40;background:#242019}
    .nav-costellazione :focus-visible{outline:2px solid #f4dfa0;outline-offset:3px}
    @media(max-width:640px){.nav-costellazione .nav-gruppi{grid-template-columns:1fr;gap:.75rem}
      input,select,textarea{font-size:max(1rem,16px)}
      button,input[type=submit],select{min-height:44px}}
    @media(prefers-reduced-motion:reduce){html{scroll-behavior:auto!important}}
    @media print{.nav-costellazione{display:none}}
  `;
  document.head.appendChild(stile);
  var menu = document.createElement('details');
  menu.className = 'nav-costellazione';
  var summary = document.createElement('summary');
  summary.textContent = 'La Costellazione · ' + titolo;
  menu.appendChild(summary);
  var nav = document.createElement('nav');
  nav.className = 'nav-gruppi';
  nav.setAttribute('aria-label', 'Percorsi della Costellazione');
  gruppi.forEach(function (g) {
    var section = document.createElement('div'); section.className = 'nav-gruppo';
    var label = document.createElement('strong'); label.className = 'nav-etichetta'; label.textContent = g[0];
    section.appendChild(label);
    var links = document.createElement('div'); links.className = 'nav-collegamenti';
    g[1].forEach(function (v) {
      var a = document.createElement('a'); a.href = new URL(v[0], base).href; a.textContent = v[1];
      if (v[0] === qui) { a.className = 'qui'; a.setAttribute('aria-current', 'page'); }
      links.appendChild(a);
    });
    section.appendChild(links); nav.appendChild(section);
  });
  menu.appendChild(nav);
  var mobile = matchMedia('(max-width:640px)');
  menu.open = !mobile.matches;
  mobile.addEventListener('change', function (e) { menu.open = !e.matches; });
  menu.addEventListener('keydown', function (e) {
    if (e.key === 'Escape') { menu.open = false; summary.focus(); }
  });
  function monta() { document.body.insertBefore(menu, document.body.firstChild); }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', monta);
  else monta();
})();
