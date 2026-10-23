#!/usr/bin/env node
'use strict';

// Publication preflight: builds local artifacts but never deploys.
// Install the official builder in a temporary prefix, then expose its modules:
// cp scripts/vercel-python-toolchain/package*.json /tmp/vercel-python-check/
// npm ci --prefix /tmp/vercel-python-check --ignore-scripts --no-audit --no-fund
// NODE_PATH=/tmp/vercel-python-check/node_modules \
//   node scripts/verify_vercel_python_builds.cjs /path/to/checkout
// Use Python 3.12 and uv 0.13.5 to match the observed hosted preview builder.

const assert = require('node:assert/strict');
const crypto = require('node:crypto');
const { execFileSync } = require('node:child_process');
const fs = require('node:fs/promises');
const os = require('node:os');
const path = require('node:path');
const { build } = require('@vercel/python');
const { glob } = require('@vercel/build-utils');

const EXCLUDED = new Set([
  '.git', '.vercel', '.now', '.venv', 'venv', 'node_modules',
  '__pycache__', '.pytest_cache', '.mypy_cache', '.ruff_cache',
]);

async function describeFile(file) {
  if (file.fsPath) {
    const data = await fs.readFile(file.fsPath);
    return { size: data.length, sha256: crypto.createHash('sha256').update(data).digest('hex') };
  }
  assert.equal(file.type, 'FileBlob', `Unexpected non-local file type: ${file.type}`);
  const data = Buffer.isBuffer(file.data) ? file.data : Buffer.from(file.data);
  return { size: data.length, sha256: crypto.createHash('sha256').update(data).digest('hex') };
}

async function main() {
  const source = path.resolve(process.argv[2] || process.cwd());
  const configuration = JSON.parse(await fs.readFile(path.join(source, 'vercel.json'), 'utf8'));
  const entries = configuration.builds.filter(item => /^@vercel\/python(?:@|$)/.test(item.use));
  assert.ok(entries.length, 'No configured Python builds');
  assert.equal(require('@vercel/python/package.json').version, '25.0.0');
  assert.equal(require('@vercel/build-utils/package.json').version, '14.21.0');
  const uvVersion = execFileSync('uv', ['--version'], {encoding:'utf8'}).trim();
  assert.match(uvVersion, /^uv 0\.13\.5(?:\s|$)/, 'Use the observed hosted preview uv version');
  const staging = await fs.mkdtemp(path.join(os.tmpdir(), 'vercel-python-preflight-'));
  console.log(`STAGING ${staging}`);
  const snapshot = path.join(staging, 'source');
  const workPath = path.join(staging, 'work');
  await fs.mkdir(workPath);
  await fs.cp(source, snapshot, {
    recursive: true,
    filter: async filename => {
      const relative = path.relative(source, filename);
      if (!relative) return true;
      const parts = relative.split(path.sep);
      if (parts.some(part => EXCLUDED.has(part) || part === '.env' ||
          (part.startsWith('.env.') && part !== '.env.example'))) return false;
      const stat = await fs.lstat(filename);
      assert.ok(!stat.isSymbolicLink(), `Use a checkout without symlinks: ${relative}`);
      return true;
    },
  });
  // Keep immutable source references separate: builder.download writes workPath.
  const files = await glob('**', snapshot);
  const retained = new Map();
  const results = [];

  async function verifyRetained(after) {
    for (const [filename, expected] of retained) {
      let actual;
      try { actual = await describeFile({fsPath: filename}); }
      catch (error) { throw new Error(`Earlier bundle reference disappeared after ${after}: ${filename}`, {cause:error}); }
      assert.deepEqual(actual, expected, `Earlier bundle reference changed after ${after}: ${filename}`);
    }
  }

  for (const item of entries) {
    console.log(`BUILD ${item.src}`);
    const result = await build({
      workPath, files, entrypoint: item.src,
      config: item.config || {}, meta: {},
    });
    await verifyRetained(item.src);
    const output = result.result?.output || result.output;
    assert.equal(output?.type, 'Lambda', `Expected one Lambda for ${item.src}`);
    assert.equal(output.runtime, 'python3.12', `Unexpected Python runtime for ${item.src}`);
    let size = 0;
    for (const file of Object.values(output.files)) {
      const description = await describeFile(file);
      size += description.size;
      if (file.fsPath) retained.set(file.fsPath, description);
    }
    // Stay below the builder's standard 250 MiB bundle target, without opt-ins.
    assert.ok(size < 250 * 1024 * 1024, `${item.src}: bundle exceeds 250 MiB`);
    const summary = {
      entrypoint: item.src, files: Object.keys(output.files).length,
      uncompressedBytes: size, survivingUniqueReferences: retained.size,
      runtimeDependencyInstallation: Boolean(output.files['_uv/_runtime_config.json']),
    };
    results.push(summary);
    console.log(`PASS ${JSON.stringify(summary)}`);
  }
  await verifyRetained('all builds');
  const report = { builder:'@vercel/python@25.0.0', uvVersion, staging, results, verifiedFileReferences:retained.size };
  const reportPath = path.resolve(process.argv[3] || path.join(staging, 'preflight-report.json'));
  await fs.writeFile(reportPath, `${JSON.stringify(report, null, 2)}\n`);
  console.log(`REPORT ${reportPath}`);
  console.log(`ALL_PASS ${JSON.stringify(report)}`);
  console.log('No deployment was performed. Remove the printed staging directory after reviewing it.');
}

main().catch(error => { console.error(error); process.exitCode = 1; });
