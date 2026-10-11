# R³-029 Pointer-First A/B — Public Durable Receipt

Date: 2026-10-08
Owner: Claudio Terzi
Classification: PUBLIC-SAFE TECHNICAL RECEIPT
Source status: reconstructed from the verified R³ Evolution Cycle checkpoint; this is **not claimed to be byte-identical** to the earlier local JSON receipt.

## Canon / provenance

- Canonical repository at time of reconstruction: `claudioterzi/Claudio`
- Canon main before this receipt: `c4cdf1037a9c590e7136e3687fa177e3f543fadb`
- Historical candidate source: PR #91
- Historical PR head: `35c75f5d7bec16b97ad70295633045d227ae51e4`
- Historical merge-base: `bec964c99bdbb958217e49efff6115335053d907`
- Recovered candidate branch (local, not pushed/deployed): `candidate/r3-029-pointer-ab-20261008`
- Tested technical tip: `3a6199592e90473467ddf335db6d2edaf6f89304`
- Earlier local receipt commit: `3d148f98402f3f0b33a98d55ee5afa86edf872a1`
- Earlier local receipt SHA-256: `7a9c2a7a0748bf082d9d8efc325b1b625a8004b59b5f0900301188c43d9cd0a1`

## What was found

The historical pointer-first candidate had two structural regressions:

1. `AGENTS.md` and `R3_AI_BOOTSTRAP.md` were absent from the manifest root authority set.
2. A selection `limit` smaller than the number of required root sources could silently truncate root authority.

A first CLI A/B attempt also failed with `ModuleNotFoundError` despite import-level tests passing. The isolated candidate added a direct CLI regression test and corrected the invocation path.

## Frozen structural A/B

- cases: 6
- iterations per case: 50
- full-context coverage: 6 / 6
- pointer-first coverage: 6 / 6
- missing contexts: 0
- authority errors: 0
- human interventions observed in this structural harness: 0
- average exact-byte reduction: **0.614197**
- average lexical-proxy reduction: **0.621579**

Per-case exact-byte reduction:

- startup: 0.753015
- continuity: 0.233065
- evolution: 0.562456
- architecture: 0.717590
- retroactive: 0.737931
- learning: 0.681126

## Frozen inputs

- manifest version: `2026-10-08.1`
- manifest SHA-256: `58a2baa907a0ec01955a5423afd4ffb429d56956aaf17b813f92c6a36b02c44e`
- dataset SHA-256: `36f29510fa3194c5c8aa34ced152131a070d74b5de65d38af08a0149881b8f5f`

## Verification

- targeted tests: **12 / 12 PASS**
- `py_compile`: PASS
- diff check: PASS
- Git object verification: PASS

## Decision

**STRUCTURAL_AB_PASS / KEEP_ISOLATED / HOLD**

This receipt does **not** claim:
- live model task success,
- exact provider token savings,
- improved answer quality,
- persistent memory,
- production deployment,
- provider inference,
- authority expansion.

## Next falsifiable gate

Run the same six paired cases with one deliberately authorized, frozen provider/model configuration:

- full context vs pointer-first,
- exact provider token accounting,
- independent success scoring,
- missing-context tracking,
- human-intervention tracking.

Adopt only if live task success is equal-or-better, authority/provenance regressions remain zero, no unexplained context misses appear, provider-measured tokens are lower, and human intervention does not materially increase.

## Durability note

This public-safe receipt exists so the evidence pointer does not depend on a temporary sandbox or one local workspace. Private archives, secrets and unpublished personal material are intentionally excluded.

## Append-only correction — 2026-10-08

A later note headed **PUBLIC LIVE GATE FAILED** was explicitly a *simulation without real provider inference*. It does not overturn this structural result, prove a real live failure, or authorize deletion of the isolated candidate. Independent GitHub read confirmed PR #91 remains open/draft, not merged. For the inconsistencies, deterministic audit and corrected evidence classification see [R³-029 simulated-live claim correction](R3_029_SIMULATED_LIVE_GATE_CORRECTION_20261008.md). **Current gate remains STRUCTURAL_AB_PASS / KEEP_ISOLATED / HOLD; live provider evaluation NOT_RUN.** The historical commit-pinned version of this receipt remains accessible unchanged.
