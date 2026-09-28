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
