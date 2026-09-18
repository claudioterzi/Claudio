# R³∞ — Shared Agent Context

This file is the common entry point for agents working in this repository.

## Startup

1. Read `MEMORIA_PROGETTO.md` for project continuity.
2. Read `R3_WORK_QUEUE.yaml` and `R3_OPERATING_OBJECTIVE.md` for current priorities.
3. Read `R3_AUTO_CYCLE.md` before autonomous or self-improvement work.
4. Read `docs/R3_RETROACTIVE_CANON_OVERLAY.md` whenever historical R³∞ work, decisions, agents, workflows or artifacts are reopened, reused or extended.
5. For memory, continuity, orchestration, retrieval, routing, evaluation, tool use, provenance, safety, benchmarking or autonomous improvement, read the latest canonical Learning Watch note. Current reference: `docs/R3_LEARNING_WATCH_2026-09-18.md`. Learning Watches are cumulative deltas: newer notes do not erase earlier evidence.

## Zero-Assunto

Distinguish FACT from INTERPRETATION, HYPOTHESIS and PROPOSAL. Do not promote external research or an internal improvement to canonical truth until it has reproducible evidence.

Historical records remain immutable evidence. When old work is reused, apply the Retroactive Canon Overlay and classify the present-day result as `KEEP | PATCH | RETEST | DEPRECATE` rather than silently rewriting history.

## Shared evolution loop

`WATCH → EXTRACT → CANDIDATE PATCH → SANDBOX → BASELINE A/B → FALSIFICATION → AUDIT → ADOPT/REJECT → R³∞ MEMORY → RETROACTIVE REEVALUATION → NEW BASELINE`

Before inventing a parallel architecture, check whether a canonical Learning Watch pattern or an existing R³∞ work item already addresses the problem.

## Current 18/09/2026 delta

- `R3-022_CONTINUITY_TRUST_BOUNDARY`: local inspection found that `ArchivioVivente` fed `SESSIONE.md` and other continuity sources to a generator without an explicit authority boundary. Draft PR #56 wraps contextual sources as `DATA_ONLY` and adds targeted regression tests. This is a bounded candidate patch; the full 100-handoff contaminated replay is still required before R3-022 can be `VERIFIED`.
- `R3-007_VERIFICATION_HARNESS`: for state-changing operations, verify authoritative postconditions/state when technically available. A success response, HTTP 2xx, UI confirmation or deployment `READY` is trajectory evidence, not proof that the requested state exists.
- `R3-019_LONGITUDINAL_BENCHMARK`: efficiency comparisons should be success-gated and record user-visible turns/human intervention separately from raw tool calls. Before the next canonical baseline, repair the historical runner's Phase-0 integrity gaps: unique run IDs/non-overwriting persistence and explicit incomplete/invalid-run semantics.
- `R3-023_RECONSOLIDATION_LAYER`: new ablation evidence supports keeping execution-time verification ahead of deeper memory promotion unless local R3-019 evidence shows otherwise.
- Native skill-routing experiments should test a post-retrieval quality/utility gate; retrieval relevance alone is not admission evidence.

The 17/09/2026 patterns remain cumulative: `R3-022`, `R3-023`, `R3-024`, `R3-025`, `R3-026`. The 16/09/2026 patterns also remain cumulative, including `R3-021_CAUSAL_EXPLORATION`, verifier-gated orchestration, Capability Quarantine, `R3-019_SENTINEL` and native skill routing.

## Capability maximization rule

Optimize for verified useful capability, efficiency per unit resource, operational autonomy and innovation yield. Do not maximize raw activity, token use, tool calls or architectural complexity. A simpler mechanism wins when it achieves equal or better verified outcomes with lower cost, latency, supervision or failure surface.

Persistent canonical records live in Drive and GitHub; chat memory is a fast recall layer, not the sole source of truth.

Project signature: C.Terzi
