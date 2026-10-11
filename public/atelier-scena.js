// Una descrizione scelta dal lettore diventa intenzione; nessuna generazione automatica.
(() => {
  'use strict';
  const scene = new URLSearchParams(window.location.search).get('scena');
  const input = document.getElementById('intenzione');
  if (scene && input) {
    input.value = scene.slice(0, input.maxLength > 0 ? input.maxLength : 3000);
    input.dispatchEvent(new Event('input', { bubbles: true }));
  }
})();
