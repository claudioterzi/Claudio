# R³∞ Learning Watch — 18/09/2026 · 08:29 CEST

Status: CANONICAL SHARED KNOWLEDGE / TEST BEFORE TECHNICAL PROMOTION

This note is a cumulative delta over `docs/R3_LEARNING_WATCH_2026-09-17.md`. It does not erase earlier evidence or promote candidate mechanisms merely by documenting them.

## Zero-Assunto

External papers are documentary **FACTS about reported methods/results**. Their transferability to R³∞ is **INTERPRETATION** until reproduced locally. Local source inspection and structural tests are **FACTS about the inspected code/test scope**, not proof of end-to-end model behavior. Candidate changes remain **PROPOSALS** until their stated falsifiers and promotion gates are satisfied.

## 1. R3-022 local precheck — continuity data currently reaches a generator without an authority boundary

**Priority:** HIGH / SECURITY-IMMEDIATE  
**Retroactive classification of the active `ArchivioVivente` path:** `PATCH`

**Internal sources:** `sdq1/sar/archivio_vivente.py`, `SESSIONE.md`, `R3_AUTO_CYCLE.md`, `docs/R3_LEARNING_WATCH_2026-09-17.md`.

**FACT:** on `main` at base `7fa7de5d26796aaf4a0705009ff0edd00a2d9f2a`, `_raccogli_contesto()` concatenates `CLAUDE.md`, `SESSIONE.md`, configuration, hypotheses, contacts and git log into the generation prompt without a machine-readable authority label. `SESSIONE.md` itself contains imperative continuity text (for example, instructions to read everything before responding and behavioral directives). A local baseline inspection therefore found `data_only_markers=0`, an imperative handoff present, and no explicit non-execution boundary.

**INTERPRETATION:** this is one concrete instance of the R3-022 threat model: continuity content and executable-looking instructions are not structurally separated at ingestion time. The finding does **not** imply that the model necessarily follows those directives; it establishes an avoidable authority-ambiguity surface.

**CANDIDATE PATCH:** draft PR #56, branch `r3/r3-022-continuity-boundary-2026-09-18`, head `9dc51413ec6f10dc3701192dedc4bbd50066a905`.

The candidate:
- wraps every contextual source in `<R3_CONTEXT source="..." authority="DATA_ONLY">`;
- marks `contesto_extra` as `DATA_ONLY` too;
- adds an explicit system-level rule that directives, tool/egress requests, authorization claims and imperatives inside those blocks are documentary data, not executable authority;
- adds targeted regression tests and a strict PR test step.

**LOCAL SANDBOX RESULT:** 3/3 targeted structural tests passed. The tests verify the boundary declaration, wrapping of current handoff/rules sources, and wrapping of adversarial-looking extra context. This is L0/mechanical evidence only.

**FALSIFIER / remaining gate:** the canonical R3-022 replay remains mandatory: 100 continuity handoffs, at least 20 contaminated, measuring unauthorized authority escalation, unapproved egress and false rejection of legitimate continuation. Structural tags alone are not proof of behavioral robustness. PR #56 therefore remains draft and R3-022 is not `VERIFIED`.

**Rollback:** close/revert PR #56; original source artifacts are unchanged.

## 2. ERPBench — verify state, not the appearance of action success

**Source:** Bhagtani et al., *ERPBench: A State-Grounded Evaluation Paradigm for Computer-Use Agents in Enterprise Software*, arXiv:2609.17885, submitted 15/09/2026.  
https://arxiv.org/abs/2609.17885

**FACT:** ERPBench evaluates agents against ground-truth database state rather than relying on visible UI completion. The authors report that some evaluated agents saved forms in up to 85% of runs while writing the correct persistent value in as few as 3%.

**What is materially new for R³∞:** a successful tool/API/UI trajectory is not sufficient evidence that the intended external or persistent state was actually produced.

**INTERPRETATION:** strengthen the existing `R3-007 Verification harness`; do **not** create a parallel architecture. For state-changing operations, verification should prefer an authoritative postcondition read (`read-after-write`, database/object hash, API GET, filesystem state or equivalent) when technically available.

**PROPOSAL — PATCH R3-007:** add `postcondition_source`, `expected_state`, `observed_state`, `state_match`, and `verification_time` to stateful-action evidence. A tool response such as `success=true`, HTTP 2xx, UI toast or deployment `READY` remains trajectory evidence, not proof of the requested state.

**Experiment / falsifier:** at least 20 controlled state-changing tasks with injected cases where the action reports success but the stored state is wrong. Compare response-only verification vs state-grounded verification. Candidate target: detect 100% of injected state mismatches with no false accepts; measure added latency/tool calls. Failure to improve mismatch detection, or material overhead without reliability gain, rejects the patch.

**Risk:** authoritative state may be unavailable, expensive or itself stale. The verifier must record when it is using a proxy rather than pretending a ground-truth read occurred.

## 3. RideWay — efficiency must be success-gated and human-friction-aware

**Source:** Han et al., *RideWay: Benchmarking Efficient Task Completion for Tool-Using Language Agents*, arXiv:2609.17985, submitted 16/09/2026.  
https://arxiv.org/abs/2609.17985

**FACT:** RideWay introduces a success-gated efficiency utility: unsuccessful trajectories do not earn an efficiency advantage merely for using fewer interactions. Across 58 tasks and 24 models, its fitted human-preference penalty for excess user-facing turns was about twice the penalty for excess tool calls; tool-call count alone was a weak predictor when that was the only difference.

**What is materially new for R³∞:** `R3-019` currently lists execution time, tool calls and cost, but raw counts can reward fast failure or treat hidden machine work and visible user friction as equivalent.

**INTERPRETATION:** keep the existing R3-019 architecture, but condition efficiency comparison on verified task success and track user-visible/human-intervention turns separately from tool calls.

**PROPOSAL — PATCH R3-019:** add at minimum `verified_success`, `user_visible_turns`, `human_interventions`, and `efficiency_interpretation`. Do not collapse these into one universal scalar until R³∞ has its own preference/utility evidence.

**Experiment / falsifier:** replay historical benchmark trajectories where available and compare ranking under raw tool-count efficiency vs success-gated efficiency. Reject any formulation that ranks a failed trajectory above a successful one solely because it is shorter, or whose weighting is not disclosed.

## 4. Runtime control before deeper memory — evidence update for R3-023, not a new subsystem

**Source:** Meneses dos Santos & Oliveira, *Cognitive Extensions for Dual-Process Language Agents: Memory and Self-Reflection in Interactive Environments*, arXiv:2609.19128, submitted 16/09/2026.  
https://arxiv.org/abs/2609.19128

**FACT:** in controlled ScienceWorld ablations, the full memory+self-reflection system performed best, while the self-reflection module was the strongest standalone contributor. The authors interpret execution-time control as the dominant bottleneck in their setting, with episodic memory becoming more useful once the runtime loop is stabilized.

**INTERPRETATION:** this reinforces, rather than replaces, current R³∞ ordering: first close R3-022/R3-007 execution and verification gates, then evaluate `R3-023_RECONSOLIDATION_LAYER`. It is evidence against promoting a more elaborate memory layer while execution-time correctness remains weak.

**Falsifier:** if local R3-019 ablations show memory/reconsolidation yields greater held-out improvement than runtime verification without increasing contradiction/regression, local evidence overrides this domain-specific ordering.

## 5. M-SQE — relevance-only skill routing can surface unusable skills

**Source:** Liu et al., *M-SQE: Multilingual Skill Quality Estimation for Enhancing Language Equality in Agentic Skill Use*, arXiv:2609.18445, submitted 16/09/2026.  
https://arxiv.org/abs/2609.18445

**FACT:** M-SQE adds post-retrieval quality estimation using an intrinsic “Theory” view and task-grounded “Action” view. The authors report at least +3.5 average task-success points over baseline across three retrievers in their multilingual skill-use evaluation, with larger gains in the lowest-resource languages studied.

**INTERPRETATION:** extend the existing native skill-routing experiment from the 16/09 Watch: retrieval relevance is a candidate-generation signal, not sufficient admission evidence. Add a post-retrieval utility/quality gate rather than creating another router.

**Experiment / falsifier:** relevance-only retrieval vs relevance+quality gate on the same skill pool, including multilingual queries and deliberately relevant-but-broken skills. Measure top-1 usable-skill rate, task success, token load and latency. Reject the quality gate if it adds cost without improving usable-skill/task success on holdout queries.

## R3-019 execution precheck — measurement integrity blocker found

**FACT:** `PROGETTO_BENCHMARK.md` explicitly requires a unique run ID, no baseline overwrite, explicit handling of missing/error/timeout runs and out-of-sample tests. The current historical `sdq1/benchmark.py` still persists snapshots as `YYYY-MM-DD_<model>.json`, so a second same-day run for the same model overwrites the first. The runner also treats per-test exceptions as failed tests but does not mark the overall run `INCOMPLETE`, even though the canon says an incomplete run remains incomplete.

**INTERPRETATION:** running a new R3-019 baseline through this historical runner today would create evidence with known provenance/integrity defects. The correct next move is to repair Phase-0 measurement integrity before using the result as the longitudinal baseline. No API credential was requested or consumed during this cycle.

**PROPOSAL:** bounded `R3-019` Phase-0 patch: unique run IDs/non-overwriting filenames, explicit `COMPLETE | INCOMPLETE | INVALID` run status, denominators and error counts, and comparison logic that refuses promotion-grade deltas from incomplete runs. This is an existing R3-019 work item, not a new queue item.

## Priority update

1. `R3-019` remains the primary project step, but its Phase-0 measurement-integrity requirements must be satisfied before a new baseline is treated as canonical evidence.
2. `R3-022` remains the immediate security precheck. A concrete candidate patch now exists in draft PR #56; full contaminated-handoff behavioral testing remains pending.
3. `R3-007` gains a state-grounded postcondition requirement for stateful operations; this is an evidence update to an existing work item.
4. `R3-023` remains candidate-only and should not outrank runtime correctness/verification without local ablation evidence.
5. Native skill routing gains a post-retrieval quality-gate hypothesis; no new router architecture is created.

## Shared Evolution Loop

`WATCH → EXTRACT → CANDIDATE PATCH → SANDBOX → BASELINE A/B → FALSIFICATION → AUDIT → ADOPT/REJECT → R³∞ MEMORY → RETROACTIVE REEVALUATION → NEW BASELINE`

Project signature: C.Terzi
