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
  const record = { id: 'a'.repeat(32), version: 1, status: 'complete',
    expires_at: '2026-10-20T00:00:00Z', plan,
    assessment: unavailable ? { status: 'unavailable' } : {
      status: 'evaluated', label: travel ? 'Viaggio' : 'Cena', signals: { travel: travel ? .99 : .01 }
    }
  };
  w.fetch = async (url, options = {}) => {
    calls.push({ url, options });
    if (url.endsWith('/status')) return { ok: true, json: async () => ({ ai_available: true }) };
    const body = JSON.parse(options.body || '{}');
    if (options.method === 'POST') record.brief = body;
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
  $('fabbrica-answer-0').value = 'Una preferenza dettagliata. '.repeat(30);
  w.document.querySelector('#fabbrica-dialogo-progressivo button').click();
  assert.ok($('refine-text').value.length > 700);
  assert.ok($('refine-text').value.length <= $('refine-text').maxLength);
  $('refine-button').click();
  await tick();
  const posts = calls.filter(c => c.options.method === 'POST');
  assert.equal(posts.length, 2, 'long dialogue should reach revision endpoint');
  assert.equal(JSON.parse(posts[1].options.body).parent_id, record.id);
  assert.deepEqual(errors, []);
  if (travel) {
    const flight = new JSDOM('<input id="r-dest">', {url:'https://example.test/viaggi.html?source=fabbrica',runScripts:'outside-only'});
    flight.window.localStorage.setItem('claudio.travel.intent.v1', w.localStorage.getItem('claudio.travel.intent.v1'));
    flight.window.eval(source('viaggi-pro.js'));
    await tick();
    assert.equal(flight.window.document.getElementById('r-dest').value, 'Bruxelles', 'Flight Desk must read the private handoff');
    flight.window.close();
  }
  dom.window.close();
}
(async () => {
  for (const options of [{}, { travel: true }, { unavailable: true }]) await scenario(options);
  console.log('PASS: dinner, travel, unavailable TypeSafe, responsive render, revision and private handoff');
})().catch(error => { console.error(error); process.exitCode = 1; });
