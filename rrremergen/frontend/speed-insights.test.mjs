import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { resolve } from 'node:path';
import { createRequire } from 'node:module';
import test from 'node:test';
import { isRrremergenLocation, sanitizeSpeedInsightsEvent } from '../../studio/web/src/speed-insights-privacy.js';

const root = fileURLToPath(new URL('../../', import.meta.url));
const origin = 'https://preview.example.invalid';
const expected = { type: 'vital', url: `${origin}/rrremergen/`, route: '/rrremergen' };

test('RRREMERGEN aliases and known React anchors share one canonical, query-free URL', () => {
  for (const path of ['/rrremergen', '/rrremergen/', '/rrremergen/index.html']) {
    for (const hash of ['', '#rrremergen', '#servizi', '#come-funziona', '#chi-siamo', '#contatto']) {
      const event = { type: 'vital', url: `${origin}${path}?key=synthetic-key&prompt=synthetic-form-text${hash}` };
      assert.deepEqual(sanitizeSpeedInsightsEvent(event, origin), expected);
    }
  }
});

test('private, authentication, API, other static and unknown paths are excluded', () => {
  for (const path of ['/', '/privato', '/privato.html', '/accesso', '/login', '/api/rrremergen',
    '/raffaello', '/rrremergen/private', '/rrremergen/assets/index.js', '/rrremergen-secret',
    '/rrremergen/%70rivate', '/%72rremergen/', '/RRREMERGEN', '/rrremergen//']) {
    assert.equal(sanitizeSpeedInsightsEvent({ type: 'vital', url: origin + path }, origin), null, path);
  }
});

test('unknown or private fragments are excluded rather than forwarded', () => {
  for (const hash of ['#privato', '#/private', '#access_token=synthetic-key', '#synthetic-form-text', '#rrremergen?key=secret']) {
    assert.equal(sanitizeSpeedInsightsEvent({ type: 'vital', url: `${origin}/rrremergen/${hash}` }, origin), null);
  }
});

test('malformed, cross-origin, credential-bearing and unsupported URLs fail closed', () => {
  for (const url of ['not a URL', '/rrremergen/', '//other.invalid/rrremergen/',
    'https://other.invalid/rrremergen/', 'http://preview.example.invalid/rrremergen/',
    'https://synthetic-key:synthetic-secret@preview.example.invalid/rrremergen/',
    'javascript:alert(1)', 'data:text/plain,synthetic-key', 'file:///rrremergen/']) {
    assert.equal(sanitizeSpeedInsightsEvent({ type: 'vital', url }, origin), null, url);
  }
  for (const invalidOrigin of ['', 'not a URL', 'file:///tmp', 'https://key:secret@preview.example.invalid']) {
    assert.equal(sanitizeSpeedInsightsEvent({ type: 'vital', url: origin + '/rrremergen/' }, invalidOrigin), null);
  }
});

test('only documented sanitized fields survive, and the input is not mutated', () => {
  const event = Object.freeze({ type: 'vital', url: `${origin}/rrremergen/?token=synthetic-key#rrremergen`,
    route: '/private/synthetic-person', prompt: 'synthetic-form-text', apiKey: 'synthetic-key',
    nested: { secret: 'synthetic-secret' } });
  const result = sanitizeSpeedInsightsEvent(event, origin);
  assert.deepEqual(result, expected);
  assert.deepEqual(Object.keys(result).sort(), ['route', 'type', 'url']);
  assert.doesNotMatch(JSON.stringify(result), /synthetic|[?#]|private/);
  assert.ok(event.url.includes('token='));
});

test('unexpected event shapes and throwing properties fail closed', () => {
  for (const event of [null, undefined, {}, false, { type: 'pageview', url: origin + '/rrremergen/' },
    { type: 'vital', url: {} }, { type: 'vital', get url() { throw new Error('unexpected'); } }]) {
    assert.equal(sanitizeSpeedInsightsEvent(event, origin), null);
  }
});

test('mount eligibility excludes development root, private paths and unknown anchors', () => {
  assert.equal(isRrremergenLocation(new URL(origin + '/rrremergen/#rrremergen')), true);
  assert.equal(isRrremergenLocation(new URL(origin + '/')), false);
  assert.equal(isRrremergenLocation(new URL(origin + '/privato')), false);
  assert.equal(isRrremergenLocation(new URL(origin + '/rrremergen/#private')), false);
  assert.equal(isRrremergenLocation(null), false);
});

test('one root integration is production-only and uses the privacy callback', () => {
  const main = readFileSync(resolve(root, 'studio/web/src/main.jsx'), 'utf8');
  const app = readFileSync(resolve(root, 'studio/web/src/App.jsx'), 'utf8');
  const wrapper = readFileSync(resolve(root, 'studio/web/src/RrremergenSpeedInsights.jsx'), 'utf8');
  assert.equal((main.match(/<RrremergenSpeedInsights\s*\/>/g) || []).length, 1);
  assert.doesNotMatch(app, /SpeedInsights/);
  assert.match(wrapper, /!import\.meta\.env\.PROD/);
  assert.match(wrapper, /isRrremergenLocation\(window\.location\)/);
  assert.match(wrapper, /sanitizeSpeedInsightsEvent\(event, window\.location\.origin\)/);
  assert.match(wrapper, /beforeSend=\{beforeSend\}/);
  assert.match(wrapper, /sampleRate=\{1\}/);
  assert.doesNotMatch(wrapper, /localStorage|sessionStorage|querySelector|FormData|\.value\b/);
});

test('the actual checked-in production bundle includes the SDK and privacy boundary', () => {
  const html = readFileSync(resolve(root, 'public/rrremergen/index.html'), 'utf8');
  const scripts = [...html.matchAll(/<script\b[^>]*\bsrc=["']([^"']+)["']/g)].map(match => match[1]);
  assert.ok(scripts.length);
  const bundle = scripts.map(path => {
    assert.ok(path.startsWith('/rrremergen/'));
    return readFileSync(resolve(root, `public${path}`), 'utf8');
  }).join('\n');
  assert.match(bundle, /@vercel\/speed-insights/);
  assert.match(bundle, /\/_vercel\/speed-insights\/script\.js/);
  assert.match(bundle, /beforeSend/);
  assert.match(bundle, /\/rrremergen\/index\.html/);
  assert.match(bundle, /username/);
  assert.match(bundle, /password/);
  assert.match(bundle, /sampleRate:1/);
});

test('the installed SDK registers sanitization before loading one same-origin script', t => {
  const require = createRequire(new URL('../../studio/web/package.json', import.meta.url));
  const { injectSpeedInsights } = require('@vercel/speed-insights');
  assert.equal(require('@vercel/speed-insights/package.json').version, '2.0.0');
  const previousWindow = Object.getOwnPropertyDescriptor(globalThis, 'window');
  const previousDocument = Object.getOwnPropertyDescriptor(globalThis, 'document');
  const previousEnvironment = process.env.NODE_ENV;
  const scripts = [];
  const callback = event => sanitizeSpeedInsightsEvent(event, origin);
  const restore = (name, descriptor) => {
    if (descriptor) Object.defineProperty(globalThis, name, descriptor);
    else delete globalThis[name];
  };
  t.after(() => {
    restore('window', previousWindow);
    restore('document', previousDocument);
    if (previousEnvironment === undefined) delete process.env.NODE_ENV;
    else process.env.NODE_ENV = previousEnvironment;
  });
  process.env.NODE_ENV = 'production';
  // A minimal offline DOM. appendChild records the script; it never fetches it.
  globalThis.window = {};
  globalThis.document = {
    createElement(tag) { assert.equal(tag, 'script'); return { dataset: {} }; },
    head: {
      querySelector() { return scripts[0] || null; },
      appendChild(script) {
        assert.equal(window.siq[0][0], 'beforeSend');
        assert.equal(window.siq[0][1], callback);
        scripts.push(script);
      },
    },
  };
  injectSpeedInsights({ beforeSend: callback, route: '/rrremergen', sampleRate: 1 });
  injectSpeedInsights({ beforeSend: callback, route: '/rrremergen', sampleRate: 1 });
  assert.equal(scripts.length, 1);
  assert.equal(scripts[0].src, '/_vercel/speed-insights/script.js');
  assert.equal(scripts[0].dataset.route, '/rrremergen');
  assert.equal(scripts[0].dataset.sampleRate, '1');
  assert.equal(scripts[0].dataset.sdkv, '2.0.0');
  const queued = window.siq[0][1];
  assert.deepEqual(queued({ type: 'vital', url: `${origin}/rrremergen/?key=synthetic#rrremergen` }), expected);
  assert.equal(queued({ type: 'vital', url: `${origin}/privato?key=synthetic` }), null);
});
