# R3_DURABLE_STATE_GATE/1.0 — Candidate

Status: CANDIDATE_ONLY · NONPRODUCTION · DO_NOT_DEPLOY AUTOMATICALLY

## Problem verified

The current Railway services `r3-external-node-a` and `r3-external-node-v2` run `uvicorn r3.node:app` from `claudioterzi/Claudio` and expose `R3_DATA_DIR`, but their current production configuration has no mounted persistent volume. The current node source stores `r3.db`, `signing.key`, uploaded documents and protocol events below the same data directory. Therefore HTTP 200 liveness does not prove durable identity or durable state across a fresh container/redeploy.

The service named `r3-external-property-runner` does have a separate `/data` volume, but it currently starts a dynamically materialized Letta server rather than `r3/external_property_runner.py`. Its volume is a different service/failure domain and is not evidence of persistence for node-a or node-v2.

The service named `r3-typesafe-sister` currently starts `letta_bridge_v2`; its name is historical and must not be treated as proof of the runtime function.

## Candidate capability now implemented

Branch: `candidate/r3-persistence-gate-20260925`

Added:
- `r3/persistence_contract.py`
- `tests/test_r3_persistence_contract.py`

The contract creates a non-secret 32-byte marker inside the configured data directory and exposes only its SHA-256. A durability claim is deliberately fail-closed and requires, after a fresh container/redeploy, all three externally frozen expectations to match:

1. persistence marker SHA-256;
2. node Ed25519 public verify key;
3. a known content-addressed canary document whose ID/hash remains exact.

A matching marker alone is insufficient. A matching public key alone is insufficient. A matching canary alone is insufficient.

## Test result

Bounded local test execution on the exact candidate files: 8/8 PASS.

Covered:
- marker stable in the same directory;
- fresh directory receives an independent marker;
- truncated/tampered marker fails closed;
- incomplete expectation set never verifies;
- exact marker + verify key + canary match verifies;
- marker mismatch fails;
- verify-key mismatch fails;
- absent/bad canary fails.

This proves only the helper contract. It does not prove Railway persistence, node runtime integration, restore correctness, backup independence, or production readiness.

## Runtime integration gate

Do not change production configuration or credentials automatically.

Next integration must occur only on this candidate/non-auto-deploy surface:

1. import the persistence contract into `r3/node.py`;
2. expose an authenticated persistence evidence surface;
3. add `R3_REQUIRE_DURABLE_STATE` fail-closed readiness behavior;
4. freeze expected marker SHA-256 + expected verify key + known canary document ID before the destructive/redeploy leg;
5. perform controlled fresh-container/redeploy;
6. require exact post-redeploy match for all three values;
7. verify the same canary is represented consistently in both SQLite and the content-addressed file;
8. only then classify durability as VERIFIED for that service.

If any of the three values changes or disappears, classify FAIL_DURABILITY and do not count the service as a durable continuity node.

## CURRENT-TECH / HORIZON

H0 current-tech path: Railway volume or equivalent durable store bound explicitly to the node data directory + evidence-bound pre/post redeploy test.

H1: external durable state/key provider with independent restore evidence and receipt-bound identity.

H2/H3 are not required for this gate. MISSING TECHNOLOGY is not a blocker here; the missing item is deployment binding/evidence, not future technology.

## Claim bound

CANDIDATE_IMPLEMENTED_HELPER / 8_OF_8_LOCAL / NODE_INTEGRATION_NOT_DONE / PRODUCTION_UNCHANGED.

No merge, deploy, credential change, volume mutation, or production restart is authorized by this document.
