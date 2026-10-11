/* DOM integration regression: rendering a dinner must settle and remain usable.
   npm install --prefix tests && node tests/test_fabbrica_frontend.cjs */
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const { JSDOM, VirtualConsole } = require('jsdom');
const root = path.resolve(__dirname, '..');
const source = name => fs.readFileSync(path.join(root, 'public', name), 'utf8');
const tick = () => new Promise(resolve => setTimeout(resolve, 35));

async function scenario({ travel = false, unavailable = false } = {}) {
  const errors = [];
  const output = new VirtualConsole();
  output.on('jsdomError', error => errors.push(error.message));
  const dom = new JSDOM(source('fabbrica.html'), {
    url: 'https://example.test/fabbrica.html', runScripts: 'outside-only', virtualConsole: output
  });
  const { window: w } = dom;
  const $ = id => w.document.getElementById(id);
  w.HTMLElement.prototype.scrollIntoView = function () {};
  // Bound a faulty observer so the regression fails instead of hanging CI forever.
  const NativeObserver = w.MutationObserver;
  let callbacks = 0;
  w.MutationObserver = class extends NativeObserver {
    constructor(fn) { super((mutations, observer) => {
      if (++callbacks > 40) {
        observer.disconnect(); errors.push('Runaway mutation observer'); return;
      }
      fn(mutations, observer);
    }); }
  };
  w.eval(source('fabbrica-examples.js'));
  const plan = JSON.parse(JSON.stringify(w.FABBRICA_LEVELS[1]));
  plan.title = travel ? 'Un viaggio tra amici' : 'Una cena tra amici';
  plan.summary = travel ? 'Prepariamo un viaggio in gruppo.' : 'Cena e musica a Bruxelles.';
  plan.questions = ['Quale data?', 'Quale budget?'];
  for (const scene of plan.scenes) for (const action of scene.actions) action.status = 'proposed';
  const calls = [];
  let generations = 0;
  const record = { id: 'a'.repeat(32), version: 1, status: 'complete',
    root_id: 'a'.repeat(32), dialogue: {answers: [], notes: '', revisions: []},
    expires_at: '2026-10-20T00:00:00Z', plan,
    assessment: unavailable ? { status: 'unavailable' } : {
      status: 'evaluated', label: travel ? 'Viaggio' : 'Cena', signals: { travel: travel ? .99 : .01 }
    }
  };
  w.fetch = async (url, options = {}) => {
    calls.push({ url, options });
    if (url.endsWith('/status')) return { ok: true, json: async () => ({ ai_available: true }) };
    const body = JSON.parse(options.body || '{}');
    if (url.endsWith('/question-help')) return {ok: true, json: async () => ({status: 'suggested',
      explanation: '<img src=x onerror=alert(1)> Una proposta da scegliere.',
      suggestions: [{label: 'Sera tranquilla', answer: 'Preferisco venerdì sera dopo le 20.'}]})};
    if (options.method === 'POST') {
      generations++;
      record.brief = body;
      if (body.parent_id) {
        record.id = String.fromCharCode(96 + generations).repeat(32);
        const choices = new Map(record.dialogue.answers.map(a => [a.question, a]));
        for (const answer of body.dialogue?.answers || []) {
          if (answer.answer) choices.set(answer.question, answer); else choices.delete(answer.question);
        }
        record.dialogue = {answers: Array.from(choices.values()), notes: body.dialogue?.notes || '', revisions: []};
        record.plan.questions = ['Quale atmosfera?'];
      }
    }
    return { ok: true, json: async () => JSON.parse(JSON.stringify(record)) };
  };
  w.eval(source('fabbrica.js'));
  w.eval(process.env.FABBRICA_TRAVEL_SCRIPT
    ? fs.readFileSync(process.env.FABBRICA_TRAVEL_SCRIPT, 'utf8') : source('fabbrica-viaggi.js'));
  w.eval(source('fabbrica-dialogo.js'));
  await tick();
  assert.equal($('dream-budget').options.length, 5, 'budget must work before repair scripts');
  w.document.querySelector('[data-example="cena"]').click();
  if (travel) $('dream-text').value = 'Un viaggio tra amici con pernottamento e voli da confrontare.';
  $('dream-city').value = 'Bruxelles';
  $('generate-button').click();
  await tick();
  assert.deepEqual(errors, [], 'render must settle without a mutation loop');
  assert.equal($('copione').hidden, false);
  assert.equal($('generate-button').disabled, false);
  assert.equal(w.document.querySelectorAll('#fabbrica-plan-travel').length, travel ? 1 : 0);
  assert.ok($('plan-assessment').textContent.includes(unavailable ? 'non è disponibile' : 'TypeSafe ha analizzato'));
  for (let i = 0; i < 10; i++) w.document.dispatchEvent(new w.CustomEvent('fabbrica:plan-rendered'));
  await tick();
  assert.equal(w.document.querySelectorAll('#fabbrica-plan-travel').length, travel ? 1 : 0);
  if (travel) {
    const link = $('fabbrica-plan-travel').querySelector('a');
    assert.equal(link.getAttribute('href'), '/viaggi.html?source=fabbrica');
    link.addEventListener('click', event => event.preventDefault());
    link.click();
    assert.equal(JSON.parse(w.localStorage.getItem('claudio.travel.intent.v1')).destination, 'Bruxelles');
  }
  for (let wait = 0; !$('fabbrica-answer-0') && wait < 20; wait++) await tick();
  assert.ok($('fabbrica-answer-0'), 'dialogue questions must mount');
  $('fabbrica-answer-0').value = 'Sto valutando venerdì.';
  $('fabbrica-answer-0').dispatchEvent(new w.Event('input'));
  w.document.querySelector('[data-action="help"]').click();
  await tick();
  assert.equal($('fabbrica-answer-0').value, 'Sto valutando venerdì.', 'AI proposals do not overwrite user choices');
  assert.equal(w.document.querySelector('.fabbrica-question-help img'), null, 'AI help is rendered as text, never HTML');
  assert.equal(calls.filter(c => c.options.method === 'POST' && c.url.endsWith('/plans')).length, 1);
  w.document.querySelector('[data-action="use-suggestion"]').click();
  assert.equal($('fabbrica-answer-0').value, 'Preferisco venerdì sera dopo le 20.');
  $('fabbrica-answer-0').value = 'Una preferenza dettagliata. '.repeat(30);
  $('fabbrica-answer-0').dispatchEvent(new w.Event('input'));
  $('fabbrica-answer-0-type').value = 'VINCOLO';
  $('fabbrica-answer-0-type').dispatchEvent(new w.Event('change'));
  // Subsequent typing must preserve the user's explicit priority.
  $('fabbrica-answer-0').dispatchEvent(new w.Event('input'));
  assert.equal($('fabbrica-answer-0-type').value, 'VINCOLO');
  w.document.querySelector('[data-action="refine-all"]').click();
  await tick();
  const posts = calls.filter(c => c.options.method === 'POST' && c.url.endsWith('/plans'));
  assert.equal(posts.length, 2, 'long dialogue should reach revision endpoint');
  const revised = JSON.parse(posts[1].options.body);
  assert.equal(revised.parent_id, 'a'.repeat(32));
  assert.ok(revised.dialogue.answers[0].answer.length > 700);
  assert.equal(revised.dialogue.answers[0].type, 'VINCOLO');
  assert.equal($('fabbrica-answer-0').value, '', 'a new question must not inherit the first answer by array position');
  assert.equal($('fabbrica-answer-1').value, revised.dialogue.answers[0].answer, 'accepted choices remain editable on the next plan');
  assert.equal($('fabbrica-answer-1-type').value, 'VINCOLO');
  // A service failure leaves the typed answer usable, and a single answer can
  // refine the plan without submitting unrelated draft fields.
  const actualFetch = w.fetch;
  w.fetch = async (url, options) => url.endsWith('/question-help')
    ? {ok: false, status: 503, json: async () => ({error: 'Aiuto temporaneamente non disponibile.'})}
    : actualFetch(url, options);
  $('fabbrica-answer-0').value = 'Atmosfera tranquilla, senza sorprese.';
  $('fabbrica-answer-0').dispatchEvent(new w.Event('input'));
  w.document.querySelector('[data-action="help"]').click();
  await tick();
  assert.equal($('fabbrica-answer-0').value, 'Atmosfera tranquilla, senza sorprese.');
  assert.ok(w.document.querySelector('.fabbrica-risposta [role="status"]').textContent.includes('non disponibile'));
  w.fetch = actualFetch;
  w.document.querySelector('[data-action="refine-one"]').click();
  await tick();
  const single = JSON.parse(calls.filter(c => c.options.method === 'POST' && c.url.endsWith('/plans')).at(-1).options.body);
  assert.equal(single.dialogue.answers.length, 1);
  assert.ok(record.dialogue.answers.some(a => a.type === 'VINCOLO'), 'earlier choices survive a one-question revision');
  assert.deepEqual(errors, []);
  if (travel) {
    const flight = new JSDOM('<input id="r-dest">', {url:'https://example.test/viaggi.html?source=fabbrica',runScripts:'outside-only'});
    flight.window.localStorage.setItem('claudio.travel.intent.v1', w.localStorage.getItem('claudio.travel.intent.v1'));
    flight.window.eval(source('viaggi-pro.js'));
    await tick();
    assert.equal(flight.window.document.getElementById('r-dest').value, 'Bruxelles', 'Flight Desk must read the private handoff');
    flight.window.close();
  }
  $('new-plan').click();
  assert.equal($('fabbrica-dialogo-progressivo'), null, 'new dreams must not keep the previous dialogue');
  dom.window.close();
}
(async () => {
  for (const options of [{}, { travel: true }, { unavailable: true }]) await scenario(options);
  console.log('PASS: dinner/travel, AI help and explicit choice, per-question revision, retained constraints, failure recovery, no stale answers and private handoff');
})().catch(error => { console.error(error); process.exitCode = 1; });
