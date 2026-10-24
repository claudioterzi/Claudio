/* Bounded loading state for the existing, versioned IDEA OS projection. */
(function (root) {
  'use strict';
  function wait(ready, status, retry) {
    const started = Date.now(); let timer, finished = false;
    retry.hidden = true; status.textContent = 'Carico il portafoglio documentato…';
    function poll() {
      if (finished) return;
      const data = root.IDEA_OS_PORTFOLIO;
      if (data && Array.isArray(data.ideas) && data.meta) {
        finished = true; status.textContent = '';
        try { ready(data); } catch (error) { status.textContent = 'Il portafoglio non è leggibile. Riprova a caricare la pagina.'; retry.hidden = false; }
        return;
      }
      if (Date.now() - started >= 5000) {
        finished = true; status.textContent = 'Il portafoglio non è stato caricato. Controlla la connessione e riprova.'; retry.hidden = false; return;
      }
      timer = setTimeout(poll, 100);
    }
    retry.onclick = () => root.location.reload(); poll();
    return () => { finished = true; clearTimeout(timer); };
  }
  root.R3IdeaLoader = {wait};
})(window);
