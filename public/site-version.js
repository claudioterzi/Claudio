/* Version notice for previews + route-specific feature loader. */
(function () {
  'use strict';

  function loadOnce(src, datasetKey) {
    if (document.querySelector('script[data-' + datasetKey + ']')) return;
    var script = document.createElement('script');
    script.src = src;
    script.async = false;
    script.setAttribute('data-' + datasetKey, '1');
    document.head.appendChild(script);
  }

  function loadRouteFeatures() {
    if (/^\/r3-evoluzione(?:\.html)?\/?$/.test(location.pathname)) {
      loadOnce('/r3-secure-sync.js', 'r3-secure-sync');
    }
    if (/^\/viaggi(?:\.html)?\/?$/.test(location.pathname)) {
      loadOnce('/viaggi-pro.js', 'viaggi-pro');
    }
    if (/^\/fabbrica(?:\.html)?\/?$/.test(location.pathname)) {
      loadOnce('/fabbrica-viaggi.js', 'fabbrica-viaggi');
      loadOnce('/fabbrica-dialogo.js', 'fabbrica-dialogo');
      loadOnce('/fabbrica-talenti.js', 'fabbrica-talenti');
    }
    if (/^\/talenti(?:\.html)?\/?$/.test(location.pathname)) {
      loadOnce('/talenti-pro.js', 'talenti-pro');
      loadOnce('/talenti-ecosistema.js', 'talenti-ecosistema');
    }
    if (/^\/orchestratore(?:\.html)?\/?$/.test(location.pathname)) {
      loadOnce('/orchestratore-proof.js', 'orchestratore-proof');
      loadOnce('/orchestratore-audit.js', 'orchestratore-audit');
    }
    if (/^\/(?:creazioni|progetti)(?:\.html)?\/?$/.test(location.pathname)) {
      loadOnce('/creazioni-extra.js', 'creazioni-extra');
    }
  }

  loadRouteFeatures();

  if (!/^claudio-[a-z0-9-]+-claudio-terzi-s-projects\.vercel\.app$/.test(location.hostname)) return;
  function showVersionLink() {
    if (document.getElementById('site-version-notice')) return;
    var notice = document.createElement('aside');
    notice.id = 'site-version-notice';
    notice.setAttribute('aria-label', 'Versione del sito');
    notice.style.cssText = 'padding:12px 20px;background:#fff4d7;color:#242014;font:16px/1.5 system-ui;text-align:center;position:relative;z-index:1000';
    notice.appendChild(document.createTextNode('Stai consultando una versione del sito. '));
    var link = document.createElement('a');
    link.textContent = 'Apri il sito ufficiale aggiornato';
    link.href = 'https://claudio-ebon.vercel.app' + location.pathname + location.search + location.hash;
    link.style.cssText = 'color:#302000;text-decoration:underline;font-weight:700';
    notice.appendChild(link);
    document.body.insertBefore(notice, document.body.firstChild);
    var style = document.createElement('style');
    style.textContent = '@media print{#site-version-notice{display:none!important}}';
    document.head.appendChild(style);
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', showVersionLink);
  else showVersionLink();
})();
