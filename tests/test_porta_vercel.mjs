import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import test from 'node:test';

const cfg = JSON.parse(readFileSync(new URL('../vercel.json', import.meta.url)));

test('legacy builds explicitly compile the Porta as middleware', () => {
  const entries = cfg.builds.filter(b => b.src === 'middleware.js');
  assert.equal(entries.length, 1);
  assert.match(entries[0].use, /^@vercel\/node(?:@|$)/);
  assert.equal(entries[0].config.middleware, true);
  assert.equal(cfg.proxy, undefined, 'proxy and legacy builds cannot coexist');
});

test('actual middleware entrypoint refuses direct pages, files and APIs', async () => {
  // Child process keeps all real credentials out of the fixture.
  const { spawnSync } = await import('node:child_process');
  const child = spawnSync(process.execPath, ['--input-type=module', '-e', `
    import assert from 'node:assert/strict';
    import middleware, { config } from './middleware.js';
    assert.equal(config.runtime, 'nodejs');
    const login = await middleware(new Request('https://example.test/porta/entra'));
    assert.equal(login.status, 200);
    assert.ok((await login.text()).includes('<h1>La Porta</h1>'));
    for (const p of ['/libro','/public/libro.html','/api/porta-consiglio','/api/orchestra','/porta/api/stato']) {
      const r = await middleware(new Request('https://example.test'+p));
      assert.equal(r.status, 401, p);
      assert.equal(r.headers.get('x-middleware-next'), null, p);
    }
    const r = await middleware(new Request('https://example.test/libro', {headers:{accept:'text/html'}}));
    assert.equal(r.status, 303);
    assert.equal(r.headers.get('location'), '/porta/entra?torna=%2Flibro');
  `], { cwd: new URL('..', import.meta.url), env: {}, encoding: 'utf8' });
  assert.equal(child.status, 0, child.stderr);
});
