/* Fabbrica dei Desideri — concept Claudio Terzi / C.Terzi. */
(() => {
  'use strict';
  const $ = id => document.getElementById(id);
  const examples = {
    palco: 'Vorrei cantare dal vivo una canzone, una volta. Non l’ho mai fatto e mi piacerebbe cominciare in un piccolo locale, con un musicista e due persone fidate.',
    cena: 'Vorrei passare una sera speciale su una terrazza con quattro amici, una cena semplice, fiori e qualcuno che suoni una canzone per noi.',
    profumo: 'Vorrei creare un profumo che mi assomigli, in un laboratorio con una persona che mi insegni a riconoscere le materie prime.',
    musica: 'Vorrei ricominciare a suonare la chitarra insieme a qualcuno, senza dover essere già bravo, e organizzare una prima prova tranquilla.'
  };
  let record = null;
  let busy = false;
  let serviceReady = false;
  let initPromise;

  function node(tag, text, className) {
    const element = document.createElement(tag);
    if (text !== undefined) element.textContent = text;
    if (className) element.className = className;
    return element;
  }
  function message(id, text, error = false) {
    $(id).textContent = text;
    $(id).classList.toggle('error', error);
  }
  function lock(value) {
    busy = value;
    $('generate-button').disabled = value;
    $('refine-button').disabled = value;
    $('demo-button').disabled = value;
    $('new-plan').disabled = value;
    document.querySelectorAll('.microaction input, #delete-plan').forEach(el => { el.disabled = value; });
  }
  async function api(path, options = {}) {
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 55000);
    try {
      const response = await fetch('/api/fabbrica/' + path, {
        ...options, credentials: 'same-origin', signal: controller.signal,
        headers: { 'Content-Type': 'application/json', 'X-Fabbrica': '1', ...(options.headers || {}) }
      });
      const data = await response.json().catch(() => ({}));
      if (!response.ok) {
        const error = new Error(data.error || 'Il servizio non risponde. Riprova tra poco.');
        error.code = response.status;
        error.planId = data.id;
        throw error;
      }
      return data;
    } catch (error) {
      if (error.name === 'AbortError') throw new Error('La risposta sta impiegando più tempo. Riapri la pagina prima di riprovare: il copione potrebbe essere già stato salvato.');
      throw error;
    } finally { clearTimeout(timeout); }
  }
  function getBrief() {
    return {
      dream: $('dream-text').value.trim(), city: $('dream-city').value.trim(),
      budget: $('dream-budget').value, timing: $('dream-time').value.trim(),
      delegation: $('dream-delegation').value.trim(), intensity: Number($('regia-level').value)
    };
  }
  function fillBrief(brief) {
    $('dream-text').value = brief.dream || '';
    $('dream-city').value = brief.city || '';
    $('dream-budget').value = brief.budget || 'Da definire';
    $('dream-time').value = brief.timing || '';
    $('dream-delegation').value = brief.delegation || '';
    $('regia-level').value = brief.intensity || 2; updateLevel();
  }
  function allActions() { return record.plan.scenes.flatMap(scene => scene.actions); }
  function ready(action, actions) {
    return action.depends_on.every(id => actions.find(a => a.id === id)?.status === 'reported_done');
  }
  function prettyDate(value) {
    const date = new Date(value);
    return Number.isNaN(date.getTime()) ? '' : date.toLocaleDateString('it-IT');
  }
  function render(scroll = true) {
    const plan = record.plan;
    const demo = record.demo === true;
    const actions = allActions();
    const done = actions.filter(a => a.status === 'reported_done').length;
    $('plan-title').textContent = plan.title;
    $('plan-type').textContent = demo ? 'ESEMPIO INTERATTIVO · NESSUNA AZIONE REALE' : 'IL TUO COPIONE · RAFFAELLO IA';
    $('plan-summary').textContent = plan.summary;
    $('plan-meta').replaceChildren(...[
      record.brief.city || 'Luogo da scegliere', record.brief.budget || 'Budget da definire',
      record.brief.timing || 'Data da definire',
      demo ? 'Prova locale, non salvata' : 'Conservato fino al ' + prettyDate(record.expires_at)
    ].map(text => node('span', text, 'meta-pill')));
    $('plan-conditions').replaceChildren(...plan.conditions.map((condition, index) => {
      const row = node('div', undefined, 'condition');
      const content = node('div');
      content.append(node('strong', condition.text), node('p', condition.detail), node('small', 'Da verificare'));
      row.append(node('span', String(index + 1).padStart(2, '0')), content);
      return row;
    }));
    $('plan-scenes').replaceChildren(...plan.scenes.map((scene, index) => {
      const article = node('article', undefined, 'scene');
      const header = node('div', undefined, 'scene-heading');
      header.append(node('span', 'SCENA ' + String(index + 1).padStart(2, '0')), node('h4', scene.title));
      article.append(header, node('p', scene.goal));
      for (const action of scene.actions) {
        const complete = action.status === 'reported_done';
        const available = ready(action, actions);
        const item = node('div', undefined, 'microaction' + (complete ? ' done' : ''));
        const label = node('label');
        const checkbox = node('input');
        checkbox.type = 'checkbox'; checkbox.id = 'action-' + action.id; checkbox.checked = complete;
        checkbox.disabled = busy || (!available && !complete);
        checkbox.addEventListener('change', () => updateAction(action.id, checkbox.checked));
        label.append(checkbox, node('span', action.title));
        item.append(label, node('p', action.role + ' · ' + action.when));
        const missing = action.depends_on.filter(id => actions.find(a => a.id === id)?.status !== 'reported_done');
        item.append(node('p', complete ? 'Completamento dichiarato ' + (demo ? 'nell’esempio' : 'da te') : missing.length ? 'In attesa di: ' + missing.map(id => actions.find(a => a.id === id).title).join('; ') : 'Pronta da verificare e svolgere'));
        const tools = node('div', undefined, 'action-tools');
        if (action.search_query) {
          const link = node('a', 'Avvia una ricerca');
          link.href = 'https://www.google.com/search?q=' + encodeURIComponent(action.search_query);
          link.target = '_blank'; link.rel = 'noopener noreferrer';
          tools.append(link);
        }
        if (action.draft) {
          const button = node('button', 'Apri la bozza di contatto');
          button.type = 'button'; button.setAttribute('aria-expanded', 'false');
          const draft = node('div', action.draft + '\n\nBozza da controllare. Nessun messaggio è stato inviato.', 'draft-text');
          draft.hidden = true;
          button.addEventListener('click', () => {
            draft.hidden = !draft.hidden; button.setAttribute('aria-expanded', String(!draft.hidden));
          });
          tools.append(button); item.append(tools, draft);
        } else if (tools.childNodes.length) item.append(tools);
        article.append(item);
      }
      return article;
    }));
    $('progress-label').textContent = `${done} di ${actions.length} microazioni ${demo ? 'simulate' : 'dichiarate complete'}`;
    $('plan-progress').max = actions.length; $('plan-progress').value = done;
    const next = actions.find(a => a.status !== 'reported_done' && ready(a, actions));
    const nextBox = node('div', undefined, 'director-next');
    nextBox.append(node('strong', next ? 'Il prossimo passo utile' : 'Il copione è stato percorso'), node('span', next ? next.title : 'Hai dichiarato concluse le microazioni. L’esito dell’esperienza resta da valutare insieme alle persone coinvolte.'));
    $('director-next').replaceChildren(nextBox);
    $('plan-questions').replaceChildren(...plan.questions.map(question => node('li', question)));
    $('plan-alternative').textContent = plan.alternative;
    $('refine-form').hidden = demo;
    let deleteButton = $('delete-plan');
    if (!deleteButton) {
      deleteButton = node('button', 'Elimina questo copione', 'text-button danger');
      deleteButton.id = 'delete-plan'; deleteButton.type = 'button';
      deleteButton.addEventListener('click', deletePlan);
      document.querySelector('.director-panel').append(deleteButton);
    }
    deleteButton.hidden = demo;
    $('copione').hidden = false;
    if (!demo) history.replaceState(null, '', '#copione/' + record.id);
    if (scroll) { $('copione').scrollIntoView({ behavior: 'smooth', block: 'start' }); $('plan-title').focus({ preventScroll: true }); }
  }
  async function updateAction(id, complete) {
    if (busy) return;
    lock(true);
    try {
      if (record.demo) {
        const actions = allActions(); const action = actions.find(a => a.id === id);
        if (complete && !ready(action, actions)) return;
        action.status = complete ? 'reported_done' : 'proposed';
        for (const item of actions) if (!ready(item, actions)) item.status = 'proposed';
      } else {
        record = await api('plans/' + record.id, { method: 'PATCH', body: JSON.stringify({ action_id: id, complete, version: record.version }) });
      }
      message('refine-status', record.demo ? '' : 'Avanzamento salvato.');
    } catch (error) {
      message('refine-status', error.message, true);
      if (error.code === 409) {
        try { record = await api('plans/' + record.id); } catch (_) { /* Preserve current copy for download. */ }
      }
    } finally {
      lock(false); render(false); $('action-' + id)?.focus({ preventScroll: true });
    }
  }
  async function submit(event, refine = false) {
    event.preventDefault(); if (busy) return;
    const statusId = refine ? 'refine-status' : 'form-status';
    lock(true); message(statusId, 'Raffaello sta studiando le condizioni e scrivendo il copione…');
    try {
      await initPromise;
      if (!serviceReady) {
        const status = await api('status'); serviceReady = status.ai_available;
        if (!serviceReady) throw new Error('La progettazione IA non è disponibile adesso. Puoi esplorare il copione di esempio.');
      }
      const body = refine ? { ...record.brief, parent_id: record.id, revision: $('refine-text').value.trim() } : getBrief();
      record = await api('plans', { method: 'POST', body: JSON.stringify(body) });
      message(statusId, refine ? 'Nuova versione salvata. Le microazioni richiedono nuove conferme.' : 'Copione salvato. Puoi riaprirlo da questo browser o scaricarne una copia.');
      $('refine-text').value = ''; render();
    } catch (error) { message(statusId, error.message, true); }
    finally { lock(false); if (record) render(false); }
  }
  async function deletePlan() {
    if (!record || record.demo || busy) return;
    if (!window.confirm('Eliminare questo copione e le sue conferme? Le altre versioni restano separate.')) return;
    lock(true);
    try {
      await api('plans/' + record.id, { method: 'DELETE' });
      record = null; $('copione').hidden = true; history.replaceState(null, '', '#racconta');
      message('form-status', 'Copione eliminato.'); $('racconta').scrollIntoView();
    } catch (error) { message('refine-status', error.message, true); }
    finally { lock(false); }
  }
  function level() { return Number($('regia-level').value); }
  function updateLevel() {
    const selected = window.FABBRICA_LEVELS[level() - 1];
    $('level-value').value = String(level()).padStart(2, '0');
    $('level-label').textContent = selected.name;
    $('regia-level').setAttribute('aria-valuetext', level() + ' di 5: ' + selected.name);
    $('level-title').textContent = selected.title;
    $('level-summary').textContent = selected.summary;
    const count = selected.scenes.reduce((sum, scene) => sum + scene.actions.length, 0);
    $('level-facts').replaceChildren(...[selected.people, count + ' microazioni', selected.scope].map(text => node('span', text)));
    $('level-preview').replaceChildren(...selected.scenes.map(scene => node('li', scene.title)));
    document.querySelectorAll('[data-level]').forEach(button => button.setAttribute('aria-pressed', String(Number(button.dataset.level) === level())));
    $('regia-level').style.setProperty('--fill', ((level() - 1) * 25) + '%');
    $('selected-regia').textContent = 'Intensità scelta: ' + selected.name + ' (' + level() + '/5)';
  }
  function demo() {
    if (busy) return;
    const selected = JSON.parse(JSON.stringify(window.FABBRICA_LEVELS[level() - 1]));
    record = { demo:true, id:'esempio-regia-' + level(),
      brief:{dream:examples.palco, city:'Luoghi da scegliere', budget:'Da definire', timing:'Una data da concordare', intensity:level()}, plan:selected };
    history.replaceState(null, '', '#copione'); render();
  }
  const occasions = {
    gruppo: {intensity:4, dream:'Siamo otto persone e vorremmo fare un viaggio memorabile insieme, partendo da città diverse. Aiutaci a coordinare gli spostamenti, scegliere quante camere servono e costruire le attività con un budget totale condiviso. Prima chiedici partenze, date, preferenze di condivisione e limiti.'},
    matrimonio: {intensity:4, dream:'Vorremmo organizzare il nostro matrimonio, con una giornata che ci somigli. Aiutaci a scegliere le priorità, coordinare invitati e fornitori e distribuire le decisioni nel tempo, rispettando il budget.'},
    festa: {intensity:3, dream:'Vorrei organizzare un addio al celibato o al nubilato per una persona cara. Cerco un’esperienza condivisa, divertente e adatta ai suoi gusti, con sorprese gradite e senza metterla in imbarazzo.'},
    viaggio: {intensity:3, dream:'Vorremmo fare un viaggio insieme, ma partiamo da città diverse e abbiamo tempi e budget differenti. Aiutaci a trovare un progetto comune, un itinerario possibile e alternative se qualcosa cambia.'},
    personale: {intensity:2, dream:examples.palco}
  };
  document.querySelectorAll('[data-occasion]').forEach(button => button.addEventListener('click', () => {
    const selected = occasions[button.dataset.occasion];
    $('dream-text').value = selected.dream; $('regia-level').value = selected.intensity;
    updateLevel(); $('racconta').scrollIntoView({behavior:'smooth'}); $('dream-text').focus({preventScroll:true});
  }));
  $('regia-level').addEventListener('input', updateLevel);
  document.querySelectorAll('[data-level]').forEach(button => button.addEventListener('click', () => { $('regia-level').value = button.dataset.level; updateLevel(); }));
  $('level-demo').addEventListener('click', demo);
  updateLevel();
  $('dream-form').addEventListener('submit', event => submit(event));
  $('refine-form').addEventListener('submit', event => submit(event, true));
  $('demo-button').addEventListener('click', demo);
  document.querySelectorAll('[data-example]').forEach(button => button.addEventListener('click', () => {
    $('dream-text').value = examples[button.dataset.example]; $('dream-text').focus();
  }));
  $('new-plan').addEventListener('click', () => {
    if (busy) return;
    record = null; $('copione').hidden = true; history.replaceState(null, '', '#racconta');
    message('form-status', 'Il copione precedente resta conservato al suo indirizzo per 30 giorni.');
    $('dream-form').reset(); $('racconta').scrollIntoView(); $('dream-text').focus();
  });
  $('download-plan').addEventListener('click', () => {
    if (!record) return;
    const exported = { ...record, author: 'Claudio Terzi', signature: 'C.Terzi', exported_at: new Date().toISOString(), note: 'Le microazioni completate sono dichiarazioni dell’utente. Nessun contatto o acquisto automatico.' };
    const blob = new Blob([JSON.stringify(exported, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob); const link = node('a');
    link.href = url; link.download = 'Fabbrica-Copione-' + record.id + '.json';
    document.body.append(link); link.click(); link.remove(); setTimeout(() => URL.revokeObjectURL(url), 1000);
  });
  initPromise = (async () => {
    try {
      const status = await api('status'); serviceReady = status.ai_available;
      $('service-mode').textContent = serviceReady ? 'Progettazione IA pronta' : 'Esplora l’esempio';
      const requested = location.hash.match(/^#copione\/([a-f0-9]{32})$/)?.[1];
      const id = requested || status.latest_id;
      if (id) {
        try {
          const saved = await api('plans/' + id);
          if (saved.status === 'complete') { record = saved; fillBrief(record.brief); render(Boolean(requested)); }
          else message('form-status', saved.status === 'pending' ? 'Il tuo ultimo copione è ancora in preparazione. Riapri fra poco.' : 'L’ultimo tentativo non ha prodotto un copione valido. Puoi riprovare.');
        } catch (error) { if (requested) message('form-status', error.message, true); }
      }
    } catch (_) { $('service-mode').textContent = 'Esplora l’esempio'; }
  })();
})();
