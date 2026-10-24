# R3-011 hosted review package

Status: `DRAFT_REVIEW_ONLY / R3-020 HOLD`

Proposed title: **R3-011: recover Evidence Graph with source-safe R3-007 provenance**

## Exact candidate

- Base: `main@e01b98a0d9a3a1d135b172088949dd1a5bd79dff`
- Local branch: `candidate/r3-011-r3-007-replay-20261009`
- Reviewed technical head: `fad754be87bb10fa5a68da8534d458593ab2300b`
- Historical source: draft PR #78, recovered without its old workflow or ancestry
- Publication state at preparation time: not pushed, not merged, not deployed

## What the candidate changes

1. Recovers the existing R3-011 Evidence Graph contract on current `main`.
2. Fails closed on weak evidence admission:
   - source-less authoritative state;
   - proxy mismatch promoted as fact;
   - non-factual evidence used as promotion support.
3. Preserves exact `postcondition_source` provenance from validated R3-007 observations.
4. Keeps absent optional source fields out of schema-v1 serialization so legacy non-authoritative graph hashes remain stable.
5. Preserves failed-observation provenance without making the failed observation factual or promotion-eligible.

## Measured deltas

- Unsafe Evidence Graph admissions: `3 → 0`.
- Exact authoritative sources exported: `0/2 → 2/2`.
- Legacy document-only graph hash: restored to and preserved at `e1b20336f3288dfe247803c7bd8b7856cc6d06213074a03c11aa0835bf108757`.
- Pre-existing R3-007 fixture sources preserved: `2/3 → 3/3`.
- Failed `missing_object` case remains `IPOTESI / OTHER` with `promotion_support=0`.
- Relevant tests: `56/56 PASS`; R3-011 tests: `23/23 PASS`.

## Hosted review checklist

- [ ] Confirm PR base is current `main` and the diff remains limited to R3-011 code, tests, capillary metadata and public-safe receipts.
- [ ] Run `python -m unittest tests.test_evidence_graph tests.test_evolution_kernel tests.test_benchmark_integrity tests.test_benchmark_controlled tests.test_evidence_review`.
- [ ] Run `python -m py_compile sdq1/evidence_graph.py tests/test_evidence_graph.py`.
- [ ] Run repository security/secret scanning on the exact head.
- [ ] Verify no serialized consumer rejects the optional `postcondition_source` field when present.
- [ ] Verify the legacy document-only fixture still hashes to `e1b20336…108757`.
- [ ] Verify `AUTHORITATIVE_STATE` without a source is refused.
- [ ] Verify proxy/error evidence with a preserved source remains non-factual and cannot support promotion.
- [ ] Obtain domain review that source labels are provenance metadata, not proof of real authority or durability.
- [ ] Keep the PR draft and R3-020 `HOLD` until hosted checks and consumer review are recorded.

## Evidence chain

- `docs/evidenze/R3_011_EVIDENCE_ADMISSION_20261008T215704Z.json`
- `docs/evidenze/R3_011_SOURCE_PROVENANCE_20261008T225420Z.json`
- `docs/evidenze/R3_011_HASH_COMPATIBILITY_20261009T000326Z.json`
- `docs/evidenze/R3_011_R3_007_REPLAY_20261009T005355Z.json`

## Non-goals

- No automatic adoption, merge or deployment.
- No claim that a source string proves authority.
- No claim of durable or cross-run persistence.
- No provider inference, production change or new verifier engine.

## Rollback

Close the draft review and delete the candidate branch if rejected. `main` and production remain unchanged.
