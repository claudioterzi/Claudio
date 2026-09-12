/* Fabbrica — repair malformed budget select without changing legacy page structure. */
(function(){
  'use strict';
  function mount(){
    var select=document.getElementById('dream-budget');
    if(!select)return;
    var expected=[
      ['Da definire','Da definire insieme'],
      ['Fino a 100 €','Fino a 100 €'],
      ['100–300 €','100–300 €'],
      ['300–700 €','300–700 €'],
      ['Oltre 700 €','Oltre 700 €']
    ];
    var valid=select.options.length===expected.length&&expected.every(function(x,i){return select.options[i]&&select.options[i].textContent.trim()===x[1]});
    if(valid)return;
    var previous=select.value;
    select.replaceChildren.apply(select,expected.map(function(x){var o=document.createElement('option');o.value=x[0];o.textContent=x[1];return o;}));
    if(Array.from(select.options).some(function(o){return o.value===previous;}))select.value=previous;
    else select.value='Da definire';
  }
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',mount);else mount();
})();
