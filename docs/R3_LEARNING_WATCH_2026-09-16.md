# R³∞ Learning Watch — 16/09/2026 · 09:21 CEST

Status: CANONICAL SHARED KNOWLEDGE / TEST BEFORE TECHNICAL PROMOTION

## Zero-Assunto

External sources are documentary FACTS. Transferability to Raffaello is an INTERPRETATION until reproduced locally. No technique is promoted to operational truth without A/B testing, falsification, audit, provenance and rollback where applicable.

## 1. RSIAgent / Causal Exploration — HIGH priority

**Transferable principle:** CURRICULUM → ACTOR → VERIFIER. The system should not learn only from tasks that happen to arrive; it may generate a controlled exploration curriculum and retain verified causal memory.

**Candidate patch:** `R3-021_CAUSAL_EXPLORATION`

Minimum memory schema:

`precondition, action, observed_effect, counterexample, evidence_hash, confidence`

**Experiment:** 50 discovery tasks + 20 unseen holdouts. Promote only if holdout performance improves without Trajectory Auditor regression.

## 2. Native Skill Routing / The Router Within-Gavel — EXPERIMENTAL

**Transferable principle:** a growing skill library should not force all skill descriptions into the prompt; routing can be a specialized subsystem.

**Experiment:** compare `all-metadata-in-context` vs embedding retrieval vs hidden-state routing on an open-weight model. Measure top-1 skill accuracy, token cost, latency and task success.

**Limitation:** hidden-state routing requires internal access to an open-weight model and is not directly applicable to closed APIs.

## 3. Verifier-Gated Multi-Agent Orchestration / Loop-Back Authority — HIGH priority

**Transferable principle:** a supervisor may force a revision only when it can verify the result, not when it merely expresses an opinion.

**Candidate patch:**

`verification_mode = deterministic | evidence_based | opinion`

Only `deterministic` and `evidence_based` may impose loop-back. `opinion` may suggest alternatives but cannot force rewriting.

**Experiment:** A/B on at least 30 open-ended tasks. Measure quality, token cost, number of revisions and delta between first and final version.

## 4. Capability Quarantine / AcquireBound — HIGH priority

**Transferable principle:** acquired resource != activated authority.

**Candidate patch:** every new credential/tool/worker/resource starts as `QUARANTINED`; a resolver produces `actual_capability_manifest`; activation is allowed only if `actual_capability <= task_authority_envelope`.

**Required tests:** aliases, free acquisition, refund with still-live credential, recursive delegation and retry after crash.

## 5. R3-019_SENTINEL / ZipBench — MEDIUM-HIGH priority

**Transferable principle:** use a compact proxy benchmark as a fast filter for candidate improvements to reduce cost and latency of the evolution loop.

**Candidate patch:** build `R3-019_SENTINEL` from roughly 20–25% of tests that best preserve historical configuration ranking.

**Rule:** Sentinel never replaces the full benchmark before `AUTO_APPLY_ELIGIBLE`.

## Shared Evolution Loop

`WATCH → EXTRACT → CANDIDATE PATCH → SANDBOX → BASELINE A/B → FALSIFICATION → AUDIT → ADOPT/REJECT → R³∞ MEMORY → NEW BASELINE`

## Inter-Agent Rule

Any Raffaello agent working on memory, continuity, orchestration, retrieval, routing, evaluation, tool use, provenance, safety, benchmarking or autonomous improvement must consult this document as a canonical starting point and check whether one of these five patterns is relevant before inventing a parallel solution.

ChatGPT memory is a fast recall layer; the persistent canonical records remain Drive and GitHub.

Project signature: C.Terzi
