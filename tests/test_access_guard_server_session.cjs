// One login: a server-verified owner session opens private pages; otherwise /accesso.
const test = require('node:test');
const assert = require('node:assert');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const source = fs.readFileSync(path.join(__dirname, '..', 'public', 'access-guard.js'), 'utf8');
const storage = (init = {}) => { const m = new Map(Object.entries(init)); return { getItem: k => m.has(k) ? m.get(k) : null, setItem: (k, v) => m.set(k, String(v)), removeItem: k => m.delete(k) }; };

function run(route, sessionReply) {
  const events = { redirects: [], reloads: 0, fetched: [] };
  const style = { visibility: '' };
  const session = storage();
  const ctx = vm.createContext({
    URL, Event, Promise,
    location: { origin: 'https://example.test', pathname: route, search: '', hash: '#key=' + 'A'.repeat(43),
      replace: v => events.redirects.push(v), reload: () => { events.reloads++; } },
    document: { documentElement: { style } },
    sessionStorage: session, localStorage: storage(),
    fetch: (url, opts) => { events.fetched.push([url, opts]); return sessionReply(); },
  });
  vm.runInContext(source, ctx);
  return { events, style, session };
}
const settle = () => new Promise(r => setImmediate(r));

test('server owner session opens a private page without asking again', async () => {
  const r = run('/libro-idee/', () => Promise.resolve({ ok: true, json: () => Promise.resolve({ autorizzato: true }) }));
  assert.strictEqual(r.style.visibility, 'hidden');
  await settle(); await settle();
  assert.deepStrictEqual(r.events.redirects, []);
  assert.strictEqual(r.events.reloads, 1);
  assert.strictEqual(r.session.getItem('raffaello.private.session.v1'), '1');
  assert.strictEqual(r.events.fetched[0][0], '/api/agora/session');
});

test('no server session still goes to /accesso and keeps the book key aside', async () => {
  const r = run('/libro-idee/', () => Promise.resolve({ ok: true, json: () => Promise.resolve({ autorizzato: false }) }));
  await settle(); await settle();
  assert.strictEqual(r.events.redirects.length, 1);
  assert.match(r.events.redirects[0], /^\/accesso\?reason=private/);
  assert.strictEqual(r.session.getItem('r3.book.pending.key.v1'), 'A'.repeat(43));
  assert.strictEqual(r.events.reloads, 0);
});

test('network failure falls back to /accesso', async () => {
  const r = run('/privato', () => Promise.reject(new Error('offline')));
  await settle(); await settle();
  assert.strictEqual(r.events.redirects.length, 1);
});
