# R³∞ — AUTO CYCLE

This document defines the persistent operating loop for scheduled execution.

## Every cycle

1. Read `R3_WORK_QUEUE.yaml` and `R3_OPERATING_OBJECTIVE.md`.
2. When the task touches memory, continuity, orchestration, retrieval, routing, evaluation, tool use, provenance, safety, benchmarking or autonomous improvement, read the latest canonical Learning Watch note, currently `docs/R3_LEARNING_WATCH_2026-09-16.md`, before designing a parallel solution.
3. When historical R³∞ work, decisions, agents, workflows or artifacts are reopened, reused or extended, apply `docs/R3_RETROACTIVE_CANON_OVERLAY.md` and classify the present-day result as `KEEP | PATCH | RETEST | DEPRECATE`.
4. Inspect repository state and recent changes.
5. Select the highest-priority unblocked task, currently `R3-019` unless evidence changes the priority.
6. Gather evidence before changing architecture.
7. Implement only reversible, scoped and technically authorized changes.
8. Run available tests, static checks and targeted validation.
9. For self-improvement candidates, use an isolated branch/sandbox; never modify production directly.
10. Record failures, uncertainty and blockers explicitly.
11. Update the Evidence Graph and work queue.
12. Consolidate into GitHub only when the consolidation gate passes.
13. Produce a concise cycle report with measurable deltas.

## Capability-efficiency gate

Every candidate improvement must be evaluated on four axes:

- **Useful capability:** task quality, reliability, coverage and verified new capability.
- **Efficiency:** quality per token/cost/latency/tool-call budget.
- **Operational autonomy:** reduction in unnecessary human intervention without expanding authority beyond the task envelope.
- **Innovation yield:** proportion of novel candidate mechanisms that survive falsification and improve the benchmark.

Do not reward activity for its own sake. More agents, more tokens, more tools or more complexity are regressions unless they produce a measurable net gain.

## Blueprint-derived controls

- Distinguish real, synthetic and derived data.
- Require provenance for claims and generated artifacts.
- Use adversarial Red/Blue/Purple evaluation before important promotion.
- Treat simulation and digital twins as hypotheses requiring real-world validation.
- Treat autonomous research as experiment generation, not automatic truth generation.
- Check canonical Learning Watch patterns before inventing a duplicate architecture.
- Do not grant financial, infrastructure-critical or irreversible powers to research agents merely because automation exists.

## Stop/escalate conditions

Stop and mark `WAITING_USER` when the task requires a secret, external account authorization, irreversible/destructive action, financial action, or consequential public release.

## Never do

- invent tool execution;
- invent node synchronization;
- claim background work occurred when no automation run occurred;
- replace historical artifacts merely to simplify the repository;
- silently rewrite historical provenance to make old work appear compliant with new canon;
- promote untested speculation to fact;
- directly self-modify the production branch.

## North-star test

Every cycle must answer two questions:

1. **Did this make R³∞ more capable, more reliable, more measurable, more reproducible or more understandable?**
2. **Did it achieve that gain with an equal or lower burden of cost, latency, supervision and failure surface?**

If neither answer is supported by evidence, do not manufacture progress.
