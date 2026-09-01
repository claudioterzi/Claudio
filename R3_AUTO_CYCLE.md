# R³∞ — AUTO CYCLE

This document defines the persistent operating loop for scheduled execution.

## Every cycle

1. Read `R3_WORK_QUEUE.yaml` and `R3_OPERATING_OBJECTIVE.md`.
2. Inspect repository state and recent changes.
3. Select the highest-priority unblocked task, currently `R3-019` unless evidence changes the priority.
4. Gather evidence before changing architecture.
5. Implement only reversible, scoped and technically authorized changes.
6. Run available tests, static checks and targeted validation.
7. For self-improvement candidates, use an isolated branch/sandbox; never modify production directly.
8. Record failures, uncertainty and blockers explicitly.
9. Update the Evidence Graph and work queue.
10. Consolidate into GitHub only when the consolidation gate passes.
11. Produce a concise cycle report with measurable deltas.

## Blueprint-derived controls

- Distinguish real, synthetic and derived data.
- Require provenance for claims and generated artifacts.
- Use adversarial Red/Blue/Purple evaluation before important promotion.
- Treat simulation and digital twins as hypotheses requiring real-world validation.
- Treat autonomous research as experiment generation, not automatic truth generation.
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
