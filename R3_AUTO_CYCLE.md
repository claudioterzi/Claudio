# R³∞ — AUTO CYCLE

This document defines the persistent operating loop for scheduled execution.

## Every cycle

1. Read `R3_WORK_QUEUE.yaml` and `R3_OPERATING_OBJECTIVE.md`.
2. Inspect repository state and recent changes.
3. Select the highest-priority unblocked task.
4. Gather evidence before changing architecture.
5. Implement only reversible, scoped changes that are technically authorized.
6. Run available tests, static checks and targeted validation.
7. Record failures and blockers explicitly.
8. Update the work queue.
9. Consolidate into GitHub only when the consolidation gate passes.
10. Produce a concise cycle report.

## Stop/escalate conditions

Stop and mark `WAITING_USER` when the task requires a secret, external account authorization, irreversible/destructive action, financial action, or consequential public release.

## Never do

- invent tool execution;
- invent node synchronization;
- claim background work occurred when no automation run occurred;
- replace historical artifacts merely to simplify the repository;
- promote untested speculation to fact.

## North-star test

Every cycle must answer: **Did this make R³∞ more capable, more reliable, more measurable, more reproducible, or more understandable?** If not, do not manufacture progress.
