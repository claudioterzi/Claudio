# R3-CLM / RedFrag candidate — 2026-09-28

Status: **CANDIDATE / SANDBOXED**  
Authority: **ADVISORY ONLY**  
Protocol: Rosso Rosso Rosso / Zero-Assunto / P5-P6

## What this is

R3-CLM v0.1 is an internal, provider-neutral contrastive System-One candidate behind the existing typesafe_sister contract. It is **not** a copy of the Stanford/NVIDIA CLM-v0.1 weights and does not claim equivalent capability. The first baseline deliberately uses a deterministic sparse hashing encoder so the full R3 architecture can be exercised now with zero network calls, zero new cloud resources and complete reproducibility.

The architectural contract is:

    state -> closed candidate set -> contrastive scores -> typed answer -> deterministic R3 gate -> action plan

The encoder can later be swapped for Qwen/CLM-compatible embeddings or another verified local encoder without changing project callers.

## Single canonical System-One path

The existing typesafe_sister.client.system_one remains the sole entry point.

- R3_SYSTEM_ONE_BACKEND=typesafe — current default, Jev/TypeSafe.
- R3_SYSTEM_ONE_BACKEND=r3_clm — explicit local R3-CLM candidate.
- R3_SYSTEM_ONE_BACKEND=shadow — Jev remains primary; R3-CLM runs locally and disagreement is attached as observation only.

There is no automatic Jev to local fallback after a configured Jev failure. Shadow mode cannot convert an upstream failure into an invented success.

## RedFrag pilot\n\nThe candidate now includes a real in-memory manifest pipeline that fingerprints supplied records, clusters logical records, applies the evidence-gated RedFrag plan, and emits active payload/pointer/quarantine maps with physical_deletions=0 and source_mutations=0.

Semantic classes:

CORE | ACTIVE | EVIDENCE | REFERENCE | DUPLICATE | STALE | CONFLICT | NOISE

Closed reversible actions:

KEEP_ACTIVE | KEEP_POINTER | LINK_TO_CANON | KEEP_DISTINCT_POINTERS | QUARANTINE_REVIEW

There is intentionally no DELETE, OVERWRITE, silent merge or canon-promotion action.

Direct evidence outranks model advice:
- exact duplicate + full provenance + canonical pointer -> LINK_TO_CANON;
- exact duplicate without recoverable provenance -> QUARANTINE_REVIEW;
- material divergence -> KEEP_DISTINCT_POINTERS;
- canonical invariant/evidence/active requirement -> KEEP_ACTIVE;
- superseded material with complete provenance -> KEEP_POINTER;
- ambiguous remainder -> contrastive model advice, still advisory.

## Evidence produced in this candidate

Local deterministic unit suite: **14/14 PASS** after adding the read-only SOURCE -> FINGERPRINT -> CLUSTER -> PLAN -> CONTEXT MAP pipeline.

RedFrag replay fixture: three 28/09 checkpoint clusters plus two negative controls, repeated 100 times per case:

- final RedFrag decisions: **5/5**;
- model-only semantic-class agreement: **5/5**;
- model-only action agreement: **4/5**;
- one model/action dissent is preserved and overridden by the deterministic evidence gate;
- network calls: **0**;
- physical deletions: **0**.

Exact machine-run evidence is in docs/evidenze/R3_CLM_REDFRAG_BENCH_2026-09-28.json.

These are small curated regression cases, not a generalization claim. The candidate must not be promoted on these numbers alone.

## R3 evolution path

1. Shadow RedFrag: replay real FILE -> FRAGMENT -> PROJECT -> ROLE -> CANON flows with Jev and R3-CLM side by side.
2. Disagreement ledger: persist input hash, both distributions, deterministic outcome and later verified result; use pointers/hashes instead of private raw payloads when sufficient.
3. Hard-negative learning: verified mistakes and Jev/R3 disagreements become contrastive negatives; only verified outcomes enter the training/prototype set.
4. Cache stable actions: pre-encode stable semantic classes/actions for low-latency routing.
5. Encoder swap A/B: compare this deterministic baseline against a Qwen/CLM-compatible encoder on suitable GPU infrastructure without changing the typed contract.
6. R3-019 gate: held-out cases, repetitions/variance, semantic-loss tests, provenance recall, false-compression rate and rollback success before default promotion.
7. Capillary reuse: after verification, reuse the same internal System-One backend for Rizzo routing, GitHub/Drive rapid analyzers, Reflex and sister routing; never create project-local copies.

## Promotion gate

Keep typesafe as default until a held-out R3-019 comparison demonstrates equal-or-better verified outcomes and acceptable semantic-loss/provenance performance. Faster local answers alone are not enough.
