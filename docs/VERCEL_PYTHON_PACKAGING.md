# Vercel Python multi-function packaging contract

## Failure reproduced

The production build at merge `d3de6110c092fd5a71033894648904dd4e7a5167`
resolved its dependencies but failed while uploading a function artifact:
`ENOENT .../SQLAlchemy-2.0.0.dist-info/LICENSE`.

A clean local reproduction with the observed official builder
`@vercel/python@25.0.0`, `@vercel/build-utils@14.21.0`, Python 3.12 and
`uv 0.10.11` reproduced that missing reference without a deployment cache:

1. A nested Python entrypoint installs SQLAlchemy and returns a `FileFsRef`
   pointing to its license in the builder's shared virtual environment.
2. A later root entrypoint resolves a different requirements manifest.
3. The builder's exact `uv sync` removes the now-unneeded distribution.
4. The earlier function still references the deleted file and cannot be packaged.

The license exists in the original clean installation. A package-version bump,
cache retry or ignoring the missing license does not repair the shared-environment
contract. The same mechanism is present in the inspected preceding builder version.

## Compatible repair

`requirements.txt` is the canonical **shared runtime superset** for all ten Python
functions in `vercel.json`. `rrremergen/requirements.txt` remains a byte-identical
copy, preserving existing component installation commands. Update the canonical
file, then synchronize and run the tests:

```sh
cp requirements.txt rrremergen/requirements.txt
python -m pytest -q tests/test_runtime_requirements.py
```

Direct entries are deliberate: the observed builder's manifest-discovery path
omits the callback needed to resolve `-r`/`-c` includes. A wrapper file was tested
and rejected by that builder, so it is not used here.

All previously declared site/composer dependencies are retained. Shared SDK bounds
are their existing intersections: Anthropic `>=0.39,<1`, OpenAI `>=1.50,<2`, and
httpx `>=0.28.1,<1`. Uvicorn moves from the composer's old `0.24.0` pin to
`>=0.29,<1` to coexist with the existing R3 requirement. Root SDK resolutions may
therefore differ from earlier unconstrained installs; real-SDK mock-transport
regressions exercise supported requests, parsed responses, errors and empty output
without sending any provider traffic. No routes, authentication, cloud/local/demo
selection or live environment variables change.

## Blocking packaging preflight

The `Vercel Python packaging contract` CI job installs the exact observed official
builder into a temporary directory, then builds every configured Python entrypoint
sequentially from a complete checkout. It requires no Vercel credentials and never
calls deploy, promote or rollback.

For a local run (Node 24 and Python 3.12):

```sh
python -m pip install uv==0.10.11
npm install --prefix /tmp/vercel-python-check --ignore-scripts --no-audit --no-fund \
  @vercel/python@25.0.0 @vercel/build-utils@14.21.0
NODE_PATH=/tmp/vercel-python-check/node_modules \
  node scripts/verify_vercel_python_builds.cjs "$PWD" "${TMPDIR:-/tmp}/vercel-python-preflight.json"
```

The script stages source separately from mutable builder output, excludes local
secret/environment and VCS files, and verifies **all earlier filesystem references
and SHA-256 digests after each subsequent build**. Every function must stay below
a conservative 250 MiB uncompressed guard, beneath the current documented 500 MB
Python limit; no larger-bundle opt-in is used. The JSON artifact records each function's files, bytes and surviving reference
count. It also records whether the builder selects runtime dependency installation;
a packaging pass does not verify that later cold-start path. A changed or missing
reference causes a nonzero exit. Ordinary Python tests
also reject divergent manifests, unsupported nearer dependency formats, duplicate
package entries and swallowed preflight failures.

Use a temporary filesystem with enough room for a complete checkout, installed
packages and build staging. The printed staging directory can be removed after
reviewing the report. No source or deployed files are removed by the preflight.

Passing local/CI packaging and dated dependency audits establish the tested build
contract, not live LLM availability, external service health or a successful
production deployment. A fresh production build still needs to reach READY and
have its public routes verified before publication can be declared successful.

## Verification snapshot (17 October 2026)

The complete repository archive was checked against all 2,114 canonical Git blobs.
The exact-builder run packaged all ten Python functions and verified 6,191 surviving
filesystem references after later builds. The largest packaged output was about
236 MB; the others were about 180 MB. Every build used the builder's automatic
runtime dependency installation, so live cold-start behavior remains a separate
verification gate. The negative two-manifest fixture reproduced the missing license;
the identical-manifest control preserved every reference.

The shared runtime resolved to 84 distributions and its dated audit reported no
known vulnerabilities or skipped packages. Real-SDK contract checks include chat,
error and image serialization with network sockets blocked; they do not claim live
model availability. Full test and hosted-build results are recorded in the repair PR.

## Exact-builder tooling advisories

The isolated npm preflight tools are not part of the deployed Python dependency
closure. Auditing the exact observed production builder on 17 October 2026 reported
ten distinct denial-of-service advisories (seven HIGH, three MODERATE) in
js-yaml, minimatch and smol-toml. npm
reports five affected package entries (four HIGH, one MODERATE), including propagated
entries for the Vercel builder and its analysis package. This is not a zero-finding
build-tool audit and is not hidden by the clean Python runtime audit.

The exact-version regression job retains these known tooling risks explicitly:
its token has only contents-read scope, checkout does not persist credentials, no
secrets are supplied, execution is limited to 15 minutes, and its nonblocking npm
audit JSON is always uploaded. Parser/matcher DoS against crafted repository input
remains a risk within that bounded runner. The build/file-integrity check itself is
blocking. No audit IDs are ignored and no automatic forced upgrade/downgrade or
unverified transitive overrides are applied. A future vendor-version update must
repeat the failing and passing packaging controls before replacing this reproducer.

The reviewed build reaches smol-toml for generated manifests and locks; its
malformed-input hang is therefore not classified as unreachable. Workspace glob
matching and YAML parsing were not exercised by this configuration. These are
build-time availability findings, not reports of code execution or data theft.
