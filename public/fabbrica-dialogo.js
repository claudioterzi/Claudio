/* Fabbrica dei Desideri — dialogo progressivo. Claudio Terzi · C.Terzi */
(() => {
  'use strict';
  const KEY = 'claudio.fabbrica.preferences.v3';
  const TYPES = {
    VINCOLO: 'Un limite da rispettare.', PREFERENZA: 'Una preferenza negoziabile.',
    DESIDERIO: 'Ciò che vuoi vivere.', DA_DECIDERE: 'Una scelta ancora aperta.',
    CONFERMATO: 'Una scelta già presa da preservare.'
  };
  const $ = id => document.getElementById(id);
  const key = text => text.trim().toLowerCase().replace(/\s+/g, ' ');
  const read = name => { try { return JSON.parse(localStorage.getItem(name) || '{}'); } catch (_) { return {}; } };
  const node = (tag, text, cls) => {
    const element = document.createElement(tag);
    if (text !== undefined) element.textContent = text;
    if (cls) element.className = cls;
    return element;
  };
  let context = null, state = read(KEY), cards = [], notes, box, pending = false, signature = '';
  if (!state.plans || typeof state.plans !== 'object') state = {plans: {}};
  function save() { try { localStorage.setItem(KEY, JSON.stringify(state)); } catch (_) { /* Server keeps applied choices. */ } }
  function draft() {
    const root = context.rootId;
    if (!state.plans[root]) {
      const legacy = read('claudio.fabbrica.preferences.v2');
      const old = legacy.plans?.[context.id]?.answers || {};
      state.plans[root] = {answers: Object.values(old).filter(a => a && typeof a.question === 'string'), notes: legacy.notes || ''};
    }
    return state.plans[root];
  }
  function entry(card) { return {question: card.question, answer: card.input.value.trim(), type: card.select.value}; }
  function collect(selected = cards) { return {answers: selected.map(entry), notes: notes?.value.trim() || ''}; }
  function persist(card) {
    const local = draft(), answer = entry(card);
    local.answers = (local.answers || []).filter(a => key(a.question) !== key(card.question));
    local.answers.push(answer); save(); updateSummary();
  }
  function updateSummary() {
    if (!box) return;
    const summary = box.querySelector('.fabbrica-summary');
    const counts = Object.fromEntries(Object.keys(TYPES).map(type => [type, 0]));
    for (const card of cards) if (card.input.value.trim()) counts[card.select.value]++;
    summary.replaceChildren(...Object.entries(counts).filter(([,count]) => count).map(([type,count]) =>
      node('span', `${type.replaceAll('_', ' ')}: ${count}`, 'fabbrica-chip')));
  }
  function lock(value) {
    pending = value;
    box?.querySelectorAll('button').forEach(button => { button.disabled = value || Boolean(context?.demo); });
  }
  function style() {
    if ($('fabbrica-dialogo-style')) return;
    const css = node('style'); css.id = 'fabbrica-dialogo-style';
    css.textContent = `
.fabbrica-dialogo{margin:1rem 0;padding:1rem;border:1px solid #d7c991;border-radius:14px;background:#fffaf0;color:#2c271b}.fabbrica-dialogo h4{margin:.1rem 0 .5rem}.fabbrica-dialogo p{margin:.3rem 0 .8rem}.fabbrica-dialogo-grid{display:grid;gap:.9rem}.fabbrica-risposta{display:grid;gap:.45rem;padding:.85rem;border:1px solid #e2d8b1;border-radius:12px;background:#fff}.fabbrica-risposta>label{font-weight:700}.fabbrica-dialogo textarea{box-sizing:border-box;width:100%;min-height:74px;resize:vertical;padding:.7rem;border:1px solid #c6b982;border-radius:10px;background:#fff;color:#17150f;font:inherit}.fabbrica-answer-meta{display:flex;gap:.55rem;align-items:center;flex-wrap:wrap}.fabbrica-answer-meta select{min-height:42px;padding:.45rem;border:1px solid #b6a76b;border-radius:10px;background:#fff;color:#17150f}.fabbrica-dialogo small{color:#6a624f}.fabbrica-summary,.fabbrica-dialogo-actions{display:flex;gap:.5rem;flex-wrap:wrap;align-items:center;margin:.7rem 0}.fabbrica-chip{border-radius:999px;padding:.28rem .55rem;border:1px solid #cbbb82;background:#f8f0d1;font-size:.78rem}.fabbrica-dialogo button{min-height:42px;padding:.55rem .8rem;border-radius:999px;border:1px solid #8c7937;background:#17150f;color:#fff;cursor:pointer;font:inherit}.fabbrica-dialogo button.secondary{background:transparent;color:#17150f}.fabbrica-dialogo button:disabled{opacity:.55;cursor:wait}.fabbrica-question-help{padding:.75rem;border-radius:10px;background:#f7f3e7}.fabbrica-question-help[hidden]{display:none}.fabbrica-ai-option{padding:.6rem 0;border-top:1px solid #e2d8b1}.fabbrica-ai-option p{white-space:pre-wrap}.fabbrica-dialogo details{margin:.6rem 0}.fabbrica-dialogo summary{cursor:pointer;font-weight:600}.fabbrica-dialogo [role=status]{font-size:.9rem;white-space:pre-wrap}.fabbrica-dialogo .error{color:#a52323}.fabbrica-profile{margin:.9rem 0;padding-top:.7rem;border-top:1px dashed #cbbb82}
`;
    document.head.append(css);
  }
  async function refine(selected = cards) {
    if (pending || context.demo) return;
    const message = box.querySelector('.fabbrica-dialogue-status');
    const changes = collect(selected);
    const hasExisting = selected.some(card => context.dialogue.answers.some(a => key(a.question) === key(card.question)));
    if (!changes.answers.some(a => a.answer) && !hasExisting && !changes.notes) {
      message.textContent = 'Scrivi almeno una risposta oppure chiedi un aiuto a Raffaello.'; return;
    }
    message.textContent = 'Raffaello sta affinando il sogno con le tue scelte…';
    const root = context.rootId;
    const result = await window.FABBRICA_DIALOGUE.refine(changes);
    if (result) {
      // Remove only the submitted drafts, preserving unfinished answers to other questions.
      const saved = state.plans[root];
      if (saved) saved.answers = saved.answers.filter(a => !changes.answers.some(sent => key(sent.question) === key(a.question) && sent.answer === a.answer && sent.type === a.type));
      save();
    } else if (message.isConnected) message.textContent = 'Il copione non è stato aggiornato. Le risposte restano qui; trovi il motivo sotto “Rivedi la regia”.';
  }
  function makeCard(question, index, previous = false) {
    const wrap = node('div', undefined, 'fabbrica-risposta');
    const label = node('label', question); label.htmlFor = 'fabbrica-answer-' + index;
    const input = node('textarea'); input.id = label.htmlFor; input.maxLength = 900;
    input.placeholder = 'La tua risposta, anche parziale…';
    const accepted = context.dialogue.answers.find(a => key(a.question) === key(question));
    const local = draft().answers?.find(a => key(a.question) === key(question));
    const value = local || accepted;
    input.value = value?.answer || '';
    const select = node('select'); select.id = input.id + '-type'; select.setAttribute('aria-label', 'Peso della risposta');
    for (const type of Object.keys(TYPES)) { const option = node('option', type.replaceAll('_', ' ')); option.value = type; select.append(option); }
    select.value = TYPES[value?.type] ? value.type : 'DA_DECIDERE';
    const hint = node('small', TYPES[select.value]);
    const meta = node('div', undefined, 'fabbrica-answer-meta'); meta.append(select, hint);
    const status = node('p'); status.setAttribute('role', 'status');
    const instruction = node('textarea'); instruction.maxLength = 600;
    instruction.placeholder = 'Es. spiegami la domanda, oppure proponi una soluzione più economica…';
    instruction.id = input.id + '-help';
    const helpLabel = node('label', 'Che aiuto vuoi? (facoltativo)'); helpLabel.htmlFor = instruction.id;
    const helpOptions = node('details'); helpOptions.append(node('summary', 'Personalizza il consiglio'), helpLabel, instruction);
    const help = node('div', undefined, 'fabbrica-question-help'); help.hidden = true;
    const ask = node('button', 'Aiutami a rispondere', 'secondary'); ask.type = 'button'; ask.dataset.action = 'help';
    const apply = node('button', 'Affina con questa risposta'); apply.type = 'button'; apply.dataset.action = 'refine-one';
    const actions = node('div', undefined, 'fabbrica-dialogo-actions'); actions.append(ask, apply);
    const card = {question, input, select, wrap};
    let chosenType = Boolean(value?.type && value.type !== 'DA_DECIDERE');
    const clearHelp = () => { help.hidden = true; help.replaceChildren(); };
    input.addEventListener('input', () => {
      if (!chosenType) select.value = input.value.trim() ? 'PREFERENZA' : 'DA_DECIDERE';
      hint.textContent = TYPES[select.value]; clearHelp(); persist(card);
    });
    select.addEventListener('change', () => { chosenType = true; hint.textContent = TYPES[select.value]; clearHelp(); persist(card); });
    instruction.addEventListener('input', clearHelp);
    apply.addEventListener('click', () => { persist(card); refine([card]); });
    ask.addEventListener('click', async () => {
      if (pending || context.demo) return;
      const original = input.value, request = instruction.value, version = context.id;
      const sent = collect(); clearHelp(); status.className = ''; status.textContent = 'Raffaello sta preparando alcune possibilità…';
      try {
        const result = await window.FABBRICA_DIALOGUE.suggest(question, original.trim(), request.trim(), sent);
        if (!wrap.isConnected || context.id !== version) return;
        if (input.value !== original || instruction.value !== request || JSON.stringify(collect()) !== JSON.stringify(sent)) {
          status.textContent = 'Hai cambiato una risposta mentre pensavo. Chiedimi un nuovo consiglio per tenerne conto.'; return;
        }
        help.append(node('strong', 'Proposte di Raffaello · scegli e modifica'), node('p', result.explanation));
        for (const suggestion of result.suggestions) {
          const option = node('div', undefined, 'fabbrica-ai-option');
          const use = node('button', 'Usa: ' + suggestion.label, 'secondary'); use.type = 'button'; use.dataset.action = 'use-suggestion';
          use.addEventListener('click', () => {
            input.value = suggestion.answer;
            if (!chosenType) select.value = 'PREFERENZA';
            hint.textContent = TYPES[select.value]; persist(card); clearHelp(); input.focus();
            status.textContent = 'Proposta inserita nella tua risposta. Puoi modificarla e poi affinare il sogno.';
          });
          option.append(node('strong', suggestion.label), node('p', suggestion.answer), use); help.append(option);
        }
        help.hidden = false; status.textContent = 'Il copione cambia solo quando usi la risposta per affinare.';
      } catch (error) { if (wrap.isConnected) { status.textContent = error.message; status.className = 'error'; } }
    });
    if (previous) wrap.append(node('small', 'Già integrata nel copione · puoi modificarla'));
    wrap.append(label, input, meta, helpOptions, actions, status, help); cards.push(card); return wrap;
  }
  function mount(next) {
    if (!next || !Array.isArray(next.questions)) return;
    const oldId = context?.id;
    context = next;
    context.dialogue = {answers: [], notes: '', revisions: [], ...context.dialogue};
    const nextSignature = JSON.stringify([context.id, context.demo, context.questions, context.dialogue]);
    if (signature === nextSignature && box?.isConnected) return;
    signature = nextSignature;
    $('fabbrica-dialogo-progressivo')?.remove(); cards = [];
    style(); box = node('section', undefined, 'fabbrica-dialogo'); box.id = 'fabbrica-dialogo-progressivo'; box.setAttribute('aria-label', 'Dialogo progressivo');
    box.append(node('h4', 'Delineiamolo mano a mano'), node('p', context.demo
      ? 'Questo è un esempio. Crea il tuo copione per dialogare con Raffaello.'
      : 'Rispondi a una domanda per volta. Se vuoi, Raffaello ti aiuta a trovare una risposta: scegli tu cosa usare.'));
    box.append(node('div', undefined, 'fabbrica-summary'));
    const grid = node('div', undefined, 'fabbrica-dialogo-grid');
    context.questions.forEach((question, i) => grid.append(makeCard(question, i)));
    if (!context.questions.length) grid.append(node('p', 'I dettagli essenziali sono delineati. Puoi modificare le scelte già integrate o aggiungere un nuovo dettaglio.'));
    box.append(grid);
    const previous = context.dialogue.answers.filter(a => !context.questions.some(q => key(q) === key(a.question)));
    if (previous.length) {
      const details = node('details'); details.append(node('summary', 'Scelte già integrate (' + previous.length + ')'));
      previous.forEach((answer, i) => details.append(makeCard(answer.question, context.questions.length + i, true)));
      box.append(details);
    }
    const profile = node('details', undefined, 'fabbrica-profile');
    profile.append(node('summary', 'Preferenze per questo sogno'));
    notes = node('textarea'); notes.maxLength = 1800; notes.setAttribute('aria-label', 'Preferenze per questo sogno');
    notes.placeholder = 'Preferenze o limiti che vuoi mantenere in tutte le revisioni di questo sogno…';
    notes.value = Object.hasOwn(draft(), 'notes') ? draft().notes : context.dialogue.notes;
    // On a newly loaded server record, accepted notes are authoritative unless locally edited.
    if (!draft().notesEdited) notes.value = context.dialogue.notes || draft().notes || '';
    notes.addEventListener('input', () => { draft().notes = notes.value; draft().notesEdited = true; save(); });
    profile.append(notes); box.append(profile);
    const all = node('button', 'Affina con tutte le risposte'); all.type = 'button'; all.dataset.action = 'refine-all';
    all.addEventListener('click', () => { cards.forEach(persist); refine(); });
    const status = node('p', '', 'fabbrica-dialogue-status'); status.setAttribute('role', 'status');
    box.append(all, status, node('small', 'Le scelte applicate restano nel copione. Le risposte ancora in bozza restano in questo browser.'));
    $('refine-form').before(box); updateSummary(); lock(pending);
    if (oldId && oldId !== context.id && !context.demo) status.textContent = 'Sogno aggiornato. Le scelte precedenti restano integrate.';
  }
  document.addEventListener('fabbrica:plan-rendered', event => mount(event.detail));
  document.addEventListener('fabbrica:busy', event => lock(Boolean(event.detail)));
  document.addEventListener('fabbrica:collect-dialogue', event => { if (context && !context.demo) event.detail.dialogue = collect(); });
  document.addEventListener('fabbrica:plan-cleared', () => {
    context = null; signature = ''; box?.remove(); box = null; cards = [];
  });
  mount(window.FABBRICA_DIALOGUE?.snapshot());
})();
