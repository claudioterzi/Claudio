# CI runtime contracts

The `CI & Security Scans` workflow runs every Python suite as a blocking job on
Python 3.11 and 3.12. Components use separate environments because the site and
RRREMERGEN both contain an `api` namespace; the bot also needs its own pytest
root. No suite is dropped from discovery.

## Reproduce in fresh virtual environments

From the repository root, install the appropriate dependency set:

```sh
# Site, R3 and their site-to-bot integration test
python -m pip install -r requirements.txt -r r3/requirements.txt \
  -r integrations/raffaello-bot/requirements.txt -r requirements-test.txt
python -m pip check
R3_BOT_CHECKOUT="$PWD/integrations/raffaello-bot" python -m coverage run -m pytest -q \
  --ignore=rrremergen --ignore=integrations/raffaello-bot

# RRREMERGEN: use a separate virtual environment
python -m pip install -r rrremergen/requirements.txt -r requirements-test.txt
python -m pip check
python -m coverage run -m pytest -q rrremergen

# Telegram bot: use another separate virtual environment
python -m pip install -r integrations/raffaello-bot/requirements.txt -r requirements-test.txt
python -m pip check
(cd integrations/raffaello-bot && python -m coverage run -m pytest -q)

# Frontend streaming and checked-in production asset contracts (Node 22)
node --test rrremergen/frontend/*.test.mjs
```

Core CI fetches full Git history so the pinned historical-fixture reproducibility
check runs rather than skipping on a shallow checkout. `tests/test_ci_test_gates.py`
injects a failing interpreter into each workflow test command to verify that its
failure reaches the job exit status. Failed runs still export available coverage.
Coverage reports describe executed code; they are not a complete production-code
coverage threshold.

Lint, typing and dependency/static-security scans remain explicitly advisory,
with reports uploaded even on failure. The IONOS deployment-security tests remain
blocking. Dependency audits cover the root, RRREMERGEN and bot manifests separately;
an advisory finding must not be interpreted as a clean security assessment merely
because the test jobs pass.

## Compatibility notes

- Bot `/ask`, `/network/v1/event` and `/network/v1/nodes` require a configured,
  nonempty `NETWORK_SECRET` and a matching request header. An unconfigured
  deployment returns HTTP 401 on these routes. `/health` stays public. No
  credentials or live settings are supplied by this change.
- Standalone R3 sync creates its log directory on first start. The integrity
  command exits unsuccessfully if its database does not exist; absence is not a
  successful integrity verification.
- The JSON decoder-error guard is tested by deterministic `RecursionError`
  injection and by a bounded real nested input. CPython versions differ in native
  decoder depth, so valid accepted input is verified without modifying its bytes.
- RRREMERGEN's dedicated frontend build keeps assets under `/rrremergen/`; the
  standalone root build and development commands are unchanged.

These checks validate local contracts and fresh installs. They do not verify live
LLM providers, Telegram delivery, database connectivity or production deployment.

## Dependency review snapshot, 2026-10-17

The impossible RRREMERGEN Pydantic/Mistral/httpx pins are replaced by tested,
compatible major-bounded requirements. Maintained dotenv, aiohttp, pymongo and
multipart releases replace vulnerable older pins. The bot retains PTB 21.7 and
updates dotenv within its existing major version.

Unused `python-jose` and `passlib` declarations were removed from RRREMERGEN only
following repository-wide source, dynamic-import, template and dependency-graph
review. This also removes transitive `ecdsa` and `rsa` from a fresh install;
`cryptography` remains through google-auth. No running authentication code was
removed. Generated apps are exported source and must have their own dependencies
reviewed before execution.

Fresh Python 3.11 and 3.12 installs each passed all 11 pipeline tests and `pip check`.
Their 73-distribution runtime closures had zero reported audit findings and zero
collection skips on this date; the bot's fresh 18-distribution closure likewise had
zero findings. These are dated scan results, not a permanent security guarantee.
The prior RRREMERGEN closure had 108 raw advisory rows representing 57 distinct
CVEs. Upgrading without removing the unused auth libraries left two unfixed issues:
[python-jose algorithm confusion](https://github.com/advisories/GHSA-3qf3-8w2g-rqmx)
and [python-ecdsa timing leakage](https://github.com/tlsfuzzer/python-ecdsa/security/advisories/GHSA-wj6h-64fc-37mp).
No advisory IDs are excluded from scanning.

Removing a requirement does not uninstall orphan packages from an existing
virtual environment. Use a fresh build/environment to obtain the verified closure.
Legacy infrastructure helpers still have unrelated undeclared boto3 imports; this
repair does not activate or certify those provisioning paths.
