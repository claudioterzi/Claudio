# Sync progress candidate — CT-LGAI-001

Status: CANDIDATE / LOCAL_VERIFIED / NOT_DEPLOYED. No production configuration changed.

The existing supervisor now reads an ephemeral progress record written by the actual sync work path. No background heartbeat thread, network monitor, persistent volume file or new service is added. A private temporary directory and fresh run ID isolate each invocation. The shared monotonic clock is sampled by the supervisor; timestamps supplied by the worker are not trusted.

Successful HTTP steps and integrity iteration advance the sequence. Every cycle records success or failure; empty successful cycles count as success. RRR, document, hash and receipt failures now propagate as explicit false results instead of being hidden by normal function returns. All configured peers must succeed for a cycle to succeed. No peers is a failed replication cycle.

Defaults: R3_SYNC_PROGRESS_TIMEOUT=180 seconds without progress; R3_SYNC_STARTUP_TIMEOUT=120 seconds plus R3_SYNC_START_DELAY; R3_SYNC_MAX_FAILURES=3 consecutive failed cycles. Normal idle time allows R3_SYNC_INTERVAL plus the progress timeout. Budgets must be finite and positive. Tune against real document sizes, slow disk and peer latency before adoption. A persistent remote fault or signed-state conflict can exhaust platform retries; progress monitoring is detection, not repair or crash-loop protection.

Local validation: 25 tests pass (5 original process tests, 9 new progress tests including real hung/failing worker processes, 11 existing local signed replication and persistence/readiness tests). Initial expanded run had four missing-harness import failures in the isolated assembly; copying the unchanged scripts/r3_restart_proof.py dependency resolved them. Loopback HTTP tests use temporary state, not live Railway volumes.

Still required before adoption: PID-1 descendant reaping, actual sleep/resume verification, drain at least 10 seconds for 5-second internal grace, hosted checks, exact live source/readiness and authenticated state-preserving controlled recovery. No model admission or production fault was triggered. #113 remains a draft; its merge touches r3/** and can redeploy both nodes.

Rollback: retain the prior startup command and source revision. Preserve all historical baseline evidence. This implementation is a post-review candidate, not a preregistered adoption experiment.

## Autonomous completion — 2026-10-05

Status: candidate, 36 local supervisor/progress/replication/persistence tests PASS (17.01s). Additional judge suite 19 PASS; four local Orchestra route/authentication checks PASS with model calls mocked. No inference claim.

Linux subreaper and selective waits preserve Popen leader status. PPid/NSpid mapping handles ancestor-mounted /proc. Earlier checks of /proc/<inner-pid> falsely indicated orphan disappearance and were replaced with real process-existence checks. Shutdown now signals adopted descendants even after setsid, grants TERM grace, then collects/kills/reaps new orphan generations for at most one additional second. Incomplete cleanup fails nonzero; handlers/subreaper settings are restored.

A monitoring-loop pause over one second grants one new timeout budget per unchanged progress sequence. Further pauses cannot indefinitely hide the same stall. Actual SIGSTOP/SIGCONT tests validate local behavior, not Railway-specific sleep semantics.

R3_FAILURE_DELAY_SECONDS defaults to 5 in main, bounded 0..60. After cleanup, a failed service pauses before its nonzero exit; SIGTERM interrupts that cooldown. This limits rapid churn but does not repair permanent faults.

Infrastructure changed in this attempt: drainingSeconds=10 saved and independently read back for both nodes. ON_FAILURE/max10 writes acknowledged; independent serialization omits those default fields, so direct readback is not claimed. Configuration takes effect on the next deployment. Existing deployments/startup commands remain unchanged, nodes online with no reported failures.

Still blocked: authenticated volume clone/recovery, actual Railway sleep/resume; device Claudio offline for Rizzo; no existing Vercel command session or usable sensitive bridge value for an authenticated Orchestra POST. Other Vercel team rosso-rosso-rosso returns 403 to this connector. Railway agent returned usage-limit reached.

Code checkpoint: 6c5854a77268503314d78983aa24e2617d44196b. Rollback infrastructure: reset drainingSeconds to the prior default (null); restart defaults were already reported ON_FAILURE/max10. No runtime source rollout was initiated.

## Sentinella CI coverage patch — 2026-10-07

Classification: PATCH / CANDIDATE / production adoption still blocked.
Inspection of exact head e068cfd34380048df3a7536ff086d5f62db0eed6 found Security
Scan #898, Test Runner #476 and R3 RRR Control #55 successful. Their workflows
did not invoke the five supervisor/progress regression modules. Green general
checks therefore did not establish hosted validation of those regressions.

Reuse the existing R3 RRR Control workflow: add the five modules to its path
filter and a separate, unmasked pytest step with a five-minute timeout. The
R3-020 candidate was registered before implementation in
`docs/evidenze/R3_SUPERVISOR_CI_CANDIDATE_20261007.jsonl`. Local invocation of the
exact added test command passed 24 tests in 12.41s. Path/command inspection and
git diff checks passed. Hosted execution remains to be read back after push.
No runtime code, production startup command, resource or service changed.
Rollback: revert this CI-only patch; retain the production adoption gates above.
