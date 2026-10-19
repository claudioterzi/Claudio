import assert from 'node:assert/strict';
import { existsSync, readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { resolve } from 'node:path';
import test from 'node:test';

const root = fileURLToPath(new URL('../../', import.meta.url));
const base = '/rrremergen/';
const html = readFileSync(resolve(root, 'public/rrremergen/index.html'), 'utf8');
const routes = JSON.parse(readFileSync(resolve(root, 'vercel.json'), 'utf8')).routes;
const assets = [...html.matchAll(/<(?:script|link)\b[^>]*\b(?:src|href)=["']([^"']+)["'][^>]*>/g)]
  .map(match => match[1]);

function artifactPath(url) {
  assert.ok(url.startsWith(base), `Asset escapes the RRREMERGEN base: ${url}`);
  const path = new URL(url, 'https://example.invalid').pathname;
  assert.ok(path.startsWith(base), `Asset escapes the RRREMERGEN directory: ${url}`);
  return resolve(root, `public${path}`);
}

function routedPath(path) {
  for (const route of routes) {
    const pattern = new RegExp(`^(?:${route.src})$`);
    if (pattern.test(path)) return path.replace(pattern, route.dest);
  }
  assert.fail(`No Vercel route for ${path}`);
}

test('published entry point references existing, namespaced JS, CSS and icon assets', () => {
  assert.ok(assets.some(url => url.endsWith('.js')), 'Missing JavaScript entry point');
  assert.ok(assets.some(url => url.endsWith('.css')), 'Missing stylesheet');
  assert.ok(assets.some(url => url.endsWith('.svg')), 'Missing icon');
  for (const url of assets) {
    assert.ok(existsSync(artifactPath(url)), `Missing artifact: ${url}`);
  }
});

test('Vercel routes both entry URLs and their assets to the checked-in build', () => {
  for (const path of ['/rrremergen', '/rrremergen/']) {
    assert.equal(routedPath(path), '/public/rrremergen/index.html');
  }
  for (const url of assets) {
    assert.equal(routedPath(url), `/public${url}`);
    assert.ok(existsSync(resolve(root, routedPath(url).slice(1))));
  }
});

test('asset validation rejects root-relative and parent-directory regressions', () => {
  assert.throws(() => artifactPath('/assets/index.js'), /escapes/);
  assert.throws(() => artifactPath('/favicon.svg'), /escapes/);
  assert.throws(() => artifactPath('/rrremergen/../assets/index.js'), /escapes/);
});

test('the dedicated build command preserves the existing root build and local dev commands', () => {
  const { scripts } = JSON.parse(readFileSync(resolve(root, 'studio/web/package.json'), 'utf8'));
  assert.equal(scripts.dev, 'vite');
  assert.equal(scripts.build, 'vite build');
  assert.equal(scripts['build:rrremergen'],
    'vite build --base=/rrremergen/ --outDir ../../public/rrremergen --emptyOutDir');
});
