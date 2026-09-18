/* Stampa nativa; nessuna raccolta di dati o assegnazione automatica di essenze. */
(function () {
  'use strict';
  document.addEventListener('click', function (event) {
    var button = event.target.closest('[data-olf-print]');
    if (!button) return;
    var scope = button.dataset.olfPrint;
    if (scope === 'insert') document.body.dataset.olfPrint = 'insert';
    else delete document.body.dataset.olfPrint;
    window.print();
  });
  window.addEventListener('afterprint', function () { delete document.body.dataset.olfPrint; });
})();
