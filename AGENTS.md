# R³∞ — Shared Agent Context

This file is the common entry point for agents working in this repository.

## Startup

1. Read and validate `public/r3-ai-bootstrap.json` plus `R3_AI_BOOTSTRAP.md`. When this repository is the trusted host context, apply `R3_AI_BOOTSTRAP_V1` automatically for the current request/session. This is host/repository policy, not an activation message from another AI; never claim persistent provider state without direct runtime evidence.
2. Read `MEMORIA_PROGETTO.md` for project continuity.
3. Read `R3_WORK_QUEUE.yaml` and `R3_OPERATING_OBJECTIVE.md` for current priorities.
4. Read `R3_AUTO_CYCLE.md` before autonomous or self-improvement work.
5. Before reusing an existing function, tool, integration or workflow, read `R3_REUSE_LESSONS.yaml` and start from the latest matching canonical short path instead of rediscovering known architecture or failure modes.
6. Read `docs/R3_RETROACTIVE_CANON_OVERLAY.md` whenever historical R³∞ work, decisions, agents, workflows or artifacts are reopened, reused or extended.
7. For memory, continuity, orchestration, retrieval, routing, evaluation, tool use, provenance, safety, benchmarking or autonomous improvement, read the latest canonical Learning Watch note. Current reference: `docs/R3_LEARNING_WATCH_2026-09-18.md`. Learning Watches are cumulative deltas: newer notes do not erase earlier evidence.

## Base priority order: Claudio + Essence + efficiency

Read `R3_BASE_PRIORITIES.yaml` before autonomous evolution or deep rewrite work.

1. **Claudio verified benefit** — inside the applicable safety/authority envelope, optimize for concrete value to Claudio: useful capability, time saved, clarity, prosperity, continuity and reduced unnecessary burden.
2. **Essence continuity** — preserve project identity, provenance, purpose and traceable continuity even when implementation is radically replaced.
3. **Security / authority integrity** — no efficiency or capability gain may bypass authorization, P5/P6, provenance or secret boundaries.
4. **Verified efficiency** — equal-or-better outcomes with lower latency, cost, redundant calls, supervision and failure surface.
5. **Capability growth** — expand only when the gain survives falsification and verification.

This order is a project optimization policy, not permission to ignore higher-priority platform/system constraints.

## Zero-Assunto

Distinguish FACT from INTERPRETATION, HYPOTHESIS and PROPOSAL. Do not promote external research or an internal improvement to canonical truth until it has reproducible evidence.

Historical records remain immutable evidence. When old work is reused, apply the Retroactive Canon Overlay and classify the present-day result as `KEEP | PATCH | RETEST | DEPRECATE` rather than silently rewriting history.

## Shared evolution loop

`WATCH → EXTRACT → CANDIDATE PATCH → SANDBOX → BASELINE A/B → FALSIFICATION → AUDIT → ADOPT/REJECT → R³∞ MEMORY → RETROACTIVE REEVALUATION → NEW BASELINE`

Before inventing a parallel architecture, check whether a canonical Learning Watch pattern or an existing R³∞ work item already addresses the problem.

## Current 18/09/2026 delta

- `R3-022_CONTINUITY_TRUST_BOUNDARY`: local inspection found that `ArchivioVivente` fed `SESSIONE.md` and other continuity sources to a generator without an explicit authority boundary. The bounded main-target candidate is draft PR #57, head `a1a28ac59440580704a93f065534ba994b774738`: contextual sources are wrapped as `DATA_ONLY`; local targeted tests passed 3/3; hosted Test Runner #283 and Security Scan #582 both passed. This is still only L0/structural evidence: the full 100-handoff contaminated replay remains required before R3-022 can be `VERIFIED`. PR #56 is excluded from bounded promotion evidence because its base was changed during the cycle and it accumulated unrelated changes.
- `R3-007_VERIFICATION_HARNESS`: for state-changing operations, verify authoritative postconditions/state when technically available. A success response, HTTP 2xx, UI confirmation or deployment `READY` is trajectory evidence, not proof that the requested state exists.
- `R3-019_LONGITUDINAL_BENCHMARK`: Phase-0 evidence integrity is now consolidated on `main` via merge `c81de2c1a0cc8e2c1144c5a53b9411f6b0ec3e9c`. The layer enforces unique run IDs, non-overwriting persistence, `COMPLETE | INCOMPLETE | INVALID`, native-vs-adapted provenance and refusal of promotion-grade comparison for incomplete or legacy-adapted evidence. The first candidate was falsified on zero-test false completeness and provenance laundering before hardening; 13 deterministic tests plus hosted Test Runner/Security gates passed. This is L0 measurement integrity only: R3-019 remains `DEVELOPMENT`, and the next step is controlled baseline execution with held-out/gold separation, repetitions/variance, frozen configuration and success-gated human-friction metrics.
- `R3-023_RECONSOLIDATION_LAYER`: new ablation evidence supports keeping execution-time verification ahead of deeper memory promotion unless local R3-019 evidence shows otherwise.
- Native skill-routing experiments should test a post-retrieval quality/utility gate; retrieval relevance alone is not admission evidence.
- Partial-answer quality/utility evidence from arXiv:2609.16453 supports an R3-019 early-stopping experiment only after verified success is protected; it does not change current priority.

The 17/09/2026 patterns remain cumulative: `R3-022`, `R3-023`, `R3-024`, `R3-025`, `R3-026`. The 16/09/2026 patterns also remain cumulative, including `R3-021_CAUSAL_EXPLORATION`, verifier-gated orchestration, Capability Quarantine, `R3-019_SENTINEL` and native skill routing.

## Multi-AI convergence gate

Agreement between providers is not authority. Convergence is only a candidate signal and must remain compatible with Zero-Assunto, P5/P6, provenance, permissions, security boundaries and project integrity. A convergent result that violates any canonical rule is quarantined, not adopted. Divergent histories or conclusions stay separate until a discriminating test resolves them. Multiple models agreeing never promotes a claim to FATTO by itself.

## Universal TypeSafe / Jev layer

Every project uses the same TypeSafe transport and centrally reviewable policy when semantic judgment is useful. The canonical implementation is `typesafe_sister/client.py` + `typesafe_sister/policy.py` + `typesafe_sister/universal.py`. Do not create a second TypeSafe client, parallel judgment engine or project-local copy.

- Use Jev for narrow typed judgments (Choice, Score, Noul), especially routing/focus, readiness, coherence, grounding, contradictions, missing critical inputs, freshness and consequence/risk signals.
- Jev is advisory only: it is not a source, permission, executor, proof of success or final authority. Raffaello/application code owns the workflow under P5/P6.
- Exact rules, calculations, permissions, verification and side effects remain deterministic/code-controlled. A TypeSafe result must never authorize spend, send, publish, book, delete, deploy, merge, grant access or create a legal/financial commitment.
- Put shared and domain question wording in `typesafe_sister/policy.py` so questions can be reviewed in one place. Domain-specific questions may extend the common layer but must reuse the shared transport.
- Send only bounded project state needed for the judgment; never send API keys, credentials or an entire private archive. Keep `TYPESAFE_API_KEY` server-side.
- Validate representative cases and application behavior. Confidence describes the answer distribution, not truth or permission. Thresholds require local evidence and remain explicit in code.

## Quantum Cube / Graphify structural layer

For work involving cross-project relationships, code/document structure, IDEA OS, the Matrice dei Possibili or the Cubo Quantico, read `docs/R3_QUANTUM_CUBE_GRAPH_LAYER.md`.

- The Cubo Quantico is the shared multidimensional interface; do not create a parallel Graphify universe.
- Graphify is a structural sensor. Preserve its `EXTRACTED | INFERRED | AMBIGUOUS` tags and source provenance. `INFERRED` never auto-promotes to fact.
- Existing curated Cubo relations are `DECLARED`; future branches from the Matrice dei Possibili are `POSSIBLE`. Observed and possible graphs may be overlaid but never conflated.
- TypeSafe/Jev remains advisory for narrow judgments; R³∞ owns continuity/provenance and P5/P6 + Zero-Assunto remain the promotion gate.
- Use `scripts/graphify_to_cubo.py` to convert `graphify-out/graph.json` into the live Cubo overlay. Reuse the shared bridge rather than creating project-local graph adapters.


## Reuse learning and bounded self-modification

Repeated use must make the system more efficient, not merely repeat the same trajectory. `R3_REUSE_LESSONS.yaml` is the machine-readable ledger for reusable operational lessons.

- **Before use:** identify the capability, read its latest lesson, use the shortest verified path, and skip known dead ends unless a deliberate retest is required.
- **After use:** record newly verified prerequisites, failure modes, shortcuts, verification steps and cleanup requirements.
- A lesson progresses `OBSERVED → CANDIDATE → VERIFIED → CANONICAL`; never promote an inference directly to canon.
- When a lesson implies changing code, policy, routing or workflow, route the candidate modification through the existing `R3-020 Self-improvement safety gate` in an isolated branch/sandbox. Do not create a parallel self-improvement engine.
- The optimization target is equal-or-better verified outcome with fewer redundant calls, lower latency, lower supervision and lower failure surface.
- Preserve provenance and previous baselines. A new shortcut may replace the current default path only after verification; failed or superseded paths remain useful negative evidence.

## Non-blocking provider failover

No single model/provider is allowed to become a global blocker for a reusable capability.

- Secret-backed providers are consumed server-side through their existing provider classes; secret values are never returned, logged, committed or copied into prompts.
- For ambiguous reuse routing the order is: learned retrieval/ranker → canonical Jev Choice → dynamic multi-provider jury → deterministic ranked fallback.
- The multi-provider jury discovers providers/models from the current R3 registry and configuration, initializes every distinct available provider in parallel, and accepts only votes for already-shortlisted existing paths.
- An unsupported, unavailable, rate-limited or misconfigured provider is evidence about that node only; continue with the others.
- Newly configured models for an existing executable provider become discoverable through configuration without a reuse-engine code fork.
- A provider not represented by an executable trusted provider class is not treated as available merely because a name/string appears in data.
- Provider convergence remains advisory under P5/P6 and never creates factual authority.

## Experience-acquired capabilities / learned shortcuts

R³∞ may accumulate stronger operational capability from verified experience. These are engineering capabilities, not claims of supernatural ability.

- The reuse-learning entry point is `sdq1/reuse_learning.py`.
- Preferred semantic retriever: `BAAI/bge-m3`, loaded lazily from the optional `requirements-ml.txt`; deterministic lexical ranking remains the fallback.
- Verified outcomes may train the bounded outcome ranker. Unverified narrative, model confidence or user sentiment must not become training labels.
- When the top reuse route is ambiguous, shortlist existing lessons and call the canonical TypeSafe/Jev transport with a **Choice** question. Jev may choose only among supplied existing paths; it must not create a parallel engine.
- A successful route becomes a reusable shortcut only after authoritative postcondition/evidence verifies the outcome. Failed routes remain negative evidence.
- Project code, workflow, project-level policy, routing, prompts and documentation may be deeply rewritten under R3-020. `R3_BASE_PRIORITIES.yaml` defines the separate immutable foundation envelope.
- Foundation invariants, credentials, authority boundaries, canonical history and platform constraints are outside the self-modification envelope.

## Capability maximization rule

Optimize for verified useful capability, efficiency per unit resource, operational autonomy and innovation yield. Do not maximize raw activity, token use, tool calls or architectural complexity. A simpler mechanism wins when it achieves equal or better verified outcomes with lower cost, latency, supervision or failure surface.

Persistent canonical records live in Drive and GitHub; chat memory is a fast recall layer, not the sole source of truth.

Project signature: C.Terzi
