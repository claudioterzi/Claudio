# R3 service resilience candidate — 2026-10-05

Classification: PATCH / CANDIDATE_LOCAL_VERIFIED / NOT_DEPLOYED.

## Concrete change
The current node-A command backgrounds r3.sync and execs uvicorn. If sync exits,
the HTTP process may remain healthy while replication stops. `python -m
r3.supervise_node` supervises both processes; any unexpected exit, including exit
zero, stops its sibling and exits nonzero. Platform ON_FAILURE restarts can then
recover the complete service. SIGTERM/SIGINT stops both process groups and reaps
the children. No model, permission or canonical memory change.

## Validation
Five process-only tests passed: kill node, kill sync, clean child exit, service
SIGTERM, invalid commands. No HTTP, provider, production database or notification
calls in these tests. This proves bounded process behavior, not production
recovery, faster replication, latency improvement or backup restoration.
Candidate registration occurred after implementation; it is NOT a preregistered
experiment and cannot satisfy a promotion-grade baseline gate.

## Deployment gate and rollback
Before adoption: rerun hosted tests/security checks, inspect the exact source
revision and live readiness, preserve node-A fingerprints, then deploy the
supervisor to node A only. Use an explicit ON_FAILURE policy and bounded retry
count; do not silently alter sleep settings or infrastructure budgets. Verify
health, storage_id, document set and a fresh bidirectional replication receipt.
Then deliberately stop only the sync child in a controlled runtime and verify
that platform recovery preserves data and restarts both children. Rollback: the
original start command `sh -c "R3_LOCAL_URL=http://127.0.0.1:$PORT python -m r3.sync
--loop & exec uvicorn r3.node:app --host 0.0.0.0 --port $PORT"`, and original
source revision. Never invoke test_shutdown on production just to exercise this.

## Other services: next concrete gates
- Node V2: preserve as intentional replica; cross-region backup/restore must use
  the existing R3_UNIVERSAL_BACKUP contract. Same-region replication is not an
  independent backup. Do not provision or migrate volumes without restore proof.
- MCP/Letta receiver: preserve current traffic. Measure and pin the hash of code
  loaded from environment before consolidation into source. Keep signed-envelope
  authorization and canonical_memory_write=false until a separate write gate.
- external-test: authenticate notification actions and avoid exposing topic in
  health only after matching the actual deployed source. Do not wake this
  service while diagnostic/startup flags are unknown. No autonomous crypto
  monitoring or trading capability is implied by its name.
- typesafe-sister: preserve shared provider transport; verify actual Jev use and
  local-state storage before wakeup/consolidation. Keep model judgments advisory.
- All: retain rollback records, verify actual persisted postconditions, measure
  useful work per cost before increasing polling/agents/compute.

No live service configuration was changed by this candidate.
