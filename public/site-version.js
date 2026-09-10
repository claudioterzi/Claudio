/* A version-specific preview must clearly point to the stable public site. */
(function () {
  'use strict';
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
    link.href = 'https://claudio-ebon.vercel.app' + location.pathname;
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
