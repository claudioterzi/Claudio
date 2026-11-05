const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const {JSDOM} = require('jsdom');
const {validSnapshot} = require('../public/r3-status.js');
const root = path.resolve(__dirname, '..');
const fixture = JSON.parse(fs.readFileSync(path.join(root, 'public/r3-status.json'), 'utf8'));
assert.equal(validSnapshot(fixture), true);
for (const value of [null, {}, {...fixture, generated_at: 'invalid'}, {...fixture, r3: []},
  {...fixture, hypotheses: {...fixture.hypotheses, total: '6'}},
  {...fixture, contacts: {...fixture.contacts, records: -1}}]) {
  assert.equal(validSnapshot(value), false);
}
const tick = () => new Promise(resolve => setImmediate(resolve));
(async () => {
  const dom = new JSDOM(fs.readFileSync(path.join(root, 'public/r3-status.html'), 'utf8'),
    {url: 'https://example.invalid', runScripts: 'outside-only'});
  const w = dom.window;
  const button = w.document.getElementById('refresh-status');
  const calls = [];
  w.AbortController = AbortController;
  let timeout;
  w.setTimeout = callback => { timeout = callback; return 1; };
  w.clearTimeout = () => {};
  w.fetch = (url, options) => new Promise((resolve, reject) => {
    calls.push({url, options, resolve, reject});
    options.signal.addEventListener('abort', () => reject(Object.assign(new Error('Timeout'), {name: 'AbortError'})));
  });
  const reply = value => ({ok: true, json: async () => value});
  w.eval(fs.readFileSync(path.join(root, 'public/r3-status.js'), 'utf8'));
  button.click();
  assert.equal(calls.length, 1, 'duplicate refresh is blocked');
  assert.equal(button.getAttribute('aria-busy'), 'true');
  calls[0].resolve(reply({...fixture, r3: {...fixture.r3, verified_external_nodes: 2}}));
  await tick();
  assert.equal(button.disabled, false);
  assert.equal(w.document.getElementById('nodes').textContent, '2');
  assert.match(w.document.getElementById('node-badge').className, /good/);
  button.click();
  calls[1].resolve(reply({...fixture, hypotheses: {...fixture.hypotheses, total: 'invalid'}}));
  await tick();
  assert.equal(w.document.getElementById('nodes').textContent, '2', 'last good values retained');
  assert.match(w.document.getElementById('node-badge').className, /warn/);
  assert.match(w.document.getElementById('status-read').textContent, /Snapshot non valido/);
  button.click(); timeout(); await tick();
  assert.equal(calls[2].options.signal.aborted, true);
  assert.equal(button.disabled, false, 'timeout unlocks manual retry');
  assert.equal(button.getAttribute('aria-busy'), 'false');
  assert.match(w.document.getElementById('status-read').textContent, /15 secondi/);
  button.click(); calls[3].resolve(reply(fixture)); await tick();
  assert.equal(w.document.getElementById('nodes').textContent, String(fixture.r3.verified_external_nodes));
  assert.doesNotMatch(w.document.getElementById('daily-badge').textContent, /LETTURA NON RIUSCITA/);
  dom.window.close();
  console.log('PASS: snapshot validation, duplicate suppression, retained data, stale badges, timeout and retry');
})().catch(error => {console.error(error); process.exitCode = 1;});
