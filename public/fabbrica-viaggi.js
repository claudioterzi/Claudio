/* Fabbrica -> Viaggi bridge — Claudio Terzi · C.Terzi */
(() => {
  'use strict';
  const INTENT_KEY = 'claudio.travel.intent.v1';
  const $ = id => document.getElementById(id);
  function save(value) {
    try { localStorage.setItem(INTENT_KEY, JSON.stringify(value)); return true; }
    catch { return false; }
  }
  function destination() { return $('dream-city')?.value?.trim() || ''; }
  function purpose() {
    return $('dream-text')?.value?.trim() || $('plan-title')?.textContent?.trim() || 'Viaggio necessario a un desiderio';
  }
  function intent() {
    return { source: 'fabbrica', purpose: purpose(), destination: destination(),
      people: 'da definire', created_at: new Date().toISOString() };
  }
  // Private wishes stay in the existing same-origin handoff store, not in URLs.
  function bindLink(link) {
    link.href = '/viaggi.html?source=fabbrica';
    link.addEventListener('click', () => save(intent()));
  }
  function addStudioLink() {
    const form = $('dream-form');
    if (!form || $('fabbrica-travel-link')) return;
    const box = document.createElement('div');
    box.id = 'fabbrica-travel-link'; box.className = 'fabbrica-travel-bridge';
    box.innerHTML = '<strong>Questo desiderio richiede uno spostamento?</strong><span>Prepara tratta, persone e confronto voli nel Flight Desk.</span><a>Prepara il viaggio ↗</a>';
    bindLink(box.querySelector('a')); form.appendChild(box);
  }
  function addPlanLink() {
    const panel = document.querySelector('.director-panel');
    const plan = $('copione');
    if (!panel || !plan || plan.hidden) return;
    // A city alone is not a journey. Without TypeSafe, inspect only explicit
    // travel words in the user's brief, never generated boilerplate.
    const suggested = plan.dataset.travelSuggested;
    const travel = suggested === 'yes' || (suggested !== 'no' &&
      /\b(viagg\w*|vol[oi]|aere[oi]|aeroport\w*|trasfert\w*|pernott\w*|hotel|vacanz\w*)\b/i.test(purpose()));
    let box = $('fabbrica-plan-travel');
    if (!travel) { box?.remove(); return; }
    if (box) return;
    box = document.createElement('div');
    box.id = 'fabbrica-plan-travel'; box.className = 'fabbrica-travel-bridge plan';
    box.innerHTML = '<strong>Uno spostamento da preparare</strong><span>Puoi confrontare i voli nel Flight Desk. Nessun acquisto viene effettuato.</span><a>Prepara il viaggio ↗</a>';
    bindLink(box.querySelector('a')); panel.prepend(box);
  }
  function mount() {
    addStudioLink();
    const style = document.createElement('style');
    style.textContent = '.fabbrica-travel-bridge{display:grid;gap:.35rem;margin-top:1rem;padding:1rem;border:1px solid #b6a05e;border-radius:14px;background:#fff8df;color:#252014}.fabbrica-travel-bridge span{font-size:.9rem;color:#625a48}.fabbrica-travel-bridge a{justify-self:start;font-weight:700;color:#173ee8;text-decoration:none}.fabbrica-travel-bridge.plan{background:#f7f2df;margin:0 0 1rem}';
    document.head.appendChild(style);
    // The old subtree observer rewrote its own subtree indefinitely after a
    // generated plan. An explicit render event has a single owner instead.
    document.addEventListener('fabbrica:plan-rendered', addPlanLink);
    ['dream-text', 'dream-city'].forEach(id => $(id)?.addEventListener('input', () => {
      const plan = $('copione');
      if (plan) plan.dataset.travelSuggested = 'unknown';
      addPlanLink();
    }));
    addPlanLink();
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', mount);
  else mount();
})();
