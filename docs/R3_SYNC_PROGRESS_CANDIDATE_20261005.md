# Sync progress candidate — CT-LGAI-001

Status: CANDIDATE / LOCAL_VERIFIED / NOT_DEPLOYED. No production configuration changed.

The existing supervisor now reads an ephemeral progress record written by the actual sync work path. No background heartbeat thread, network monitor, persistent volume file or new service is added. A private temporary directory and fresh run ID isolate each invocation. The shared monotonic clock is sampled by the supervisor; timestamps supplied by the worker are not trusted.

Successful HTTP steps and integrity iteration advance the sequence. Every cycle records success or failure; empty successful cycles count as success. RRR, document, hash and receipt failures now propagate as explicit false results instead of being hidden by normal function returns. All configured peers must succeed for a cycle to succeed. No peers is a failed replication cycle.

Defaults: R3_SYNC_PROGRESS_TIMEOUT=180 seconds without progress; R3_SYNC_STARTUP_TIMEOUT=120 seconds plus R3_SYNC_START_DELAY; R3_SYNC_MAX_FAILURES=3 consecutive failed cycles. Normal idle time allows R3_SYNC_INTERVAL plus the progress timeout. Budgets must be finite and positive. Tune against real document sizes, slow disk and peer latency before adoption. A persistent remote fault or signed-state conflict can exhaust platform retries; progress monitoring is detection, not repair or crash-loop protection.

Local validation: 25 tests pass (5 original process tests, 9 new progress tests including real hung/failing worker processes, 11 existing local signed replication and persistence/readiness tests). Initial expanded run had four missing-harness import failures in the isolated assembly; copying the unchanged scripts/r3_restart_proof.py dependency resolved them. Loopback HTTP tests use temporary state, not live Railway volumes.

Still required before adoption: PID-1 descendant reaping, actual sleep/resume verification, drain at least 10 seconds for 5-second internal grace, hosted checks, exact live source/readiness and authenticated state-preserving controlled recovery. No model admission or production fault was triggered. #113 remains a draft; its merge touches r3/** and can redeploy both nodes.

Rollback: retain the prior startup command and source revision. Preserve all historical baseline evidence. This implementation is a post-review candidate, not a preregistered adoption experiment.
