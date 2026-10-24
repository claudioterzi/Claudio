# R³ CLM / Red Flag candidate — 2026-09-28

Status: **CANDIDATE / NOT CANON / LIVE CLM NOT YET VERIFIED**

## Goal

Add CLM as a second System One provider without creating a parallel R³ policy
engine. The existing canonical `typesafe_sister.client` transport is extended
to speak the TypeSafe-compatible `POST /v1/systemone` wire format to either:

- hosted TypeSafe/Jev (existing default);
- local/open `clm-serve` (opt-in, default loopback `127.0.0.1:8700`).

The CLM upstream repository documents the same endpoint and typed
`Noul | Choice | Score` schema. No CLM package dependency is required in R³.

## Red Flag v0.1

`typesafe_sister/redflag.py` sends an identical bounded evidence packet and
centrally reviewed question set to CLM or Jev. It checks:

- evidence / unsupported promotion;
- authority and secret boundaries;
- reversibility and postconditions;
- version/provenance conflicts;
- stale external facts;
- duplicate-engine drift;
- latency/cost inefficiency and dependency bottlenecks.

The model selects a **review lane**, never an execution permission:

- `QUARANTINE_REVIEW`
- `VERIFY_FIRST`
- `CONTROLLED_TEST_CANDIDATE`

Agreement between CLM and Jev remains advisory and cannot promote a claim to
FACT/canon under P5/P6.

## Security boundary

- Existing Jev behavior is unchanged by default.
- Unauthenticated CLM is allowed only on loopback.
- Remote CLM requires `CLM_API_KEY`.
- Redirects remain disabled.
- State and responses remain bounded.
- No credential is included in the JSON payload.

## Test plan

Deterministic tests cover:

1. TypeSafe-compatible CLM wire request;
2. refusal of unauthenticated remote CLM;
3. Red Flag controlled-test lane;
4. quarantine on authority/secret signals;
5. verify-first on postcondition/evidence flags;
6. malformed/incomplete model output fails closed;
7. CLM-vs-Jev shadow disagreement is preserved rather than averaged away.

## What this does **not** prove

These tests verify adapter/policy/gate behavior only. They do **not** prove the
quality, latency or accuracy of a real CLM model. A live CLM benchmark requires
a reachable `clm-serve` backed by its compatible encoder/head and must be
recorded separately before any default-provider change.


## Candidate reconciliation — 2026-10-11

Classification: PATCH / RETEST. The candidate now incorporates current main;
historical entries above describe the original 2026-09-28 implementation.
The shared transport preserves main's explicit/auto CLM routing, hosted Jev
fallback/reference, native CLM rank and explicit network-free r3_clm baseline.
There is no new default-provider promotion in this reconciliation.

Remote CLM now requires authentication through the existing CLM or generic
System One key configuration; unauthenticated calls are restricted to HTTP(S)
loopback. Both provider environment variable spellings are supported, with
R3_SYSTEMONE_PROVIDER taking precedence, and jev remains an alias for typesafe.
The centralized policy retains both architecture Red Flag and cluster RedFrag
question sets. CLM server latency metadata is preserved for the live probe.

Probe accuracy and required-flag recall include failed cases in their denominators.
Empty/partial runs record LIVE_CLM_INFERENCE_INCOMPLETE and exit nonzero.
This change supplies deterministic evidence only, not a new live model benchmark.
