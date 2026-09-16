# R³∞ — AUTO CYCLE

This document defines the persistent operating loop for scheduled execution.

## Every cycle

1. Read `R3_WORK_QUEUE.yaml` and `R3_OPERATING_OBJECTIVE.md`.
2. When the task touches memory, continuity, orchestration, retrieval, routing, evaluation, tool use, provenance, safety, benchmarking or autonomous improvement, read the latest canonical Learning Watch note, currently `docs/R3_LEARNING_WATCH_2026-09-16.md`, before designing a parallel solution.
3. Inspect repository state and recent changes.
4. Select the highest-priority unblocked task, currently `R3-019` unless evidence changes the priority.
5. Gather evidence before changing architecture.
6. Implement only reversible, scoped and technically authorized changes.
7. Run available tests, static checks and targeted validation.
8. For self-improvement candidates, use an isolated branch/sandbox; never modify production directly.
9. Record failures, uncertainty and blockers explicitly.
10. Update the Evidence Graph and work queue.
11. Consolidate into GitHub only when the consolidation gate passes.
12. Produce a concise cycle report with measurable deltas.

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
- promote untested speculation to fact;
- directly self-modify the production branch.

## North-star test

Every cycle must answer: **Did this make R³∞ more capable, more reliable, more measurable, more reproducible, or more understandable?** If not, do not manufacture progress.
