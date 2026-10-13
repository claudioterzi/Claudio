// Real @vercel/node build + compiled-entrypoint check, without Vercel secrets.
// node tests/check_porta_vercel_build.cjs /absolute/path/to/@vercel/node [--baseline]
const assert = require('node:assert/strict');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const { execFileSync, spawnSync } = require('node:child_process');

async function main() {
  const builderPath = path.resolve(process.argv[2]);
  const baseline = process.argv.includes('--baseline');
  const builder = require(builderPath);
  assert.equal(require(path.join(builderPath, 'package.json')).version, '22.0.0');
  const utils = require(require.resolve('@vercel/build-utils', { paths: [builderPath] }));
  const root = path.resolve(__dirname, '..');
  const work = fs.mkdtempSync(path.join(os.tmpdir(), 'porta-build-'));
  const out = fs.mkdtempSync(path.join(os.tmpdir(), 'porta-compiled-'));
  const files = {};
  const names = ['middleware.js', 'porta/porta.mjs', 'porta/core.mjs', 'porta/dati.mjs', 'porta/sentinella.mjs'];
  for (const name of names) {
    const bytes = baseline && name === 'middleware.js'
      ? execFileSync('git', ['show', 'HEAD:middleware.js'], { cwd: root })
      : fs.readFileSync(path.join(root, name));
    const fixture = path.join(work, name);
    fs.mkdirSync(path.dirname(fixture), { recursive: true });
    fs.writeFileSync(fixture, bytes);
    files[name] = new utils.FileFsRef({ fsPath: fixture });
  }
  const built = await builder.build({ files, entrypoint: 'middleware.js', workPath: work,
    config: { middleware: true, projectSettings: { nodeVersion: '24.x' } },
    meta: { isDev: false } });
  const lambda = built.output.middleware || built.output;
  assert.equal(lambda.runtime, 'nodejs24.x');
  assert.equal(lambda.useWebApi, true);
  const compiled = await utils.FileBlob.fromStream({ stream: lambda.files['middleware.js'].toStream() });
  const source = String(compiled.data);
  if (!baseline) {
    assert.match(source, /import\(['"]\.\/porta\/porta\.mjs['"]\)/);
    assert.doesNotMatch(source, /require\(['"]\.\/porta\//);
  }
  for (const [name, file] of Object.entries(lambda.files)) {
    assert.ok(!name.split(/[\\/]/).includes('..'));
    const dest = path.join(out, name);
    fs.mkdirSync(path.dirname(dest), { recursive: true });
    const blob = await utils.FileBlob.fromStream({ stream: file.toStream() });
    fs.writeFileSync(dest, blob.data);
  }
  const child = spawnSync(process.execPath, ['-e', `
    const assert = require('node:assert/strict');
    const Module = require('node:module');
    const load = Module._load;
    Module._load = function(id, ...args) {
      if (id.endsWith('.mjs')) {
        const e = new Error('Hosted loader refuses require(ESM)'); e.code = 'ERR_REQUIRE_ESM'; throw e;
      }
      return load.call(this, id, ...args);
    };
    (async () => {
      const middleware = require('./middleware.js').default;
      const login = await middleware(new Request('https://example.test/porta/entra'));
      assert.equal(login.status, 200);
      assert.ok((await login.text()).includes('<h1>La Porta</h1>'));
      for (const p of ['/libro','/public/libro.html','/api/porta-consiglio','/porta/api/stato']) {
        assert.equal((await middleware(new Request('https://example.test'+p))).status, 401, p);
      }
      const html = await middleware(new Request('https://example.test/', {headers:{accept:'text/html'}}));
      assert.equal(html.status, 303);
      console.log('compiled entrypoint: 6 checks PASS');
    })().catch(e => { console.error(e.code || e.message); process.exitCode=1; });
  `], { cwd: out, env: {}, encoding: 'utf8' });
  if (baseline) {
    assert.notEqual(child.status, 0, 'baseline must reproduce deployed failure');
    assert.match(child.stderr, /ERR_REQUIRE_ESM/);
    console.log('baseline: actual builder reproduced require(ESM) failure');
  } else {
    assert.equal(child.status, 0, child.stderr);
    console.log(child.stdout.trim());
    console.log('actual builder: native import preserved, Node Web API middleware emitted');
  }
  // Keep the bounded temporary build for inspection; no repository or user file deleted.
  console.log(JSON.stringify({ baseline, runtime: lambda.runtime, useWebApi: lambda.useWebApi,
    compiledDirectory: out, routes: built.routes }));
}
main().catch(e => { console.error(e.stack); process.exitCode = 1; });
