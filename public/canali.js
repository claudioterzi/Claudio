/* La Soglia: directory of links, without account/session inference or external calls. */
(function () {
  'use strict';
  var bar = document.getElementById('filters');
  var buttons = Array.from(document.querySelectorAll('[data-filter]'));
  var cards = Array.from(document.querySelectorAll('[data-category]'));
  var result = document.getElementById('filter-result');
  if (!bar || !buttons.length || !cards.length || !result) return;
  bar.hidden = false;
  buttons.forEach(function (button) {
    button.addEventListener('click', function () {
      var category = button.getAttribute('data-filter');
      var count = 0;
      cards.forEach(function (card) {
        card.hidden = category !== 'all' && card.getAttribute('data-category') !== category;
        if (!card.hidden) count += 1;
      });
      buttons.forEach(function (item) { item.setAttribute('aria-pressed', String(item === button)); });
      result.textContent = count + (count === 1 ? ' collegamento' : ' collegamenti');
    });
  });
})();
