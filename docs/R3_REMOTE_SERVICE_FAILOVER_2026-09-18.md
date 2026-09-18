# R3∞ — Remote separate-service failover/recovery evidence

Timestamp: 2026-09-18 05:43 CEST (UTC+02:00)

## Classification

**REMOTE SEPARATE-SERVICE PROPERTY TEST PASSED / DIFFERENT-PROVIDER + DURABLE-STORAGE PENDING**

This is stronger than the earlier local two-process property test because node A and node B were independently deployed Railway services and the orchestration crossed their public HTTPS service endpoints.

It does **not** prove:
- different cloud providers or ASNs;
- physically distinct underlying hosts;
- durable disk survival across provider/service destruction;
- production-grade inter-peer identity/trust;
- automatic failover routing.

Both tested nodes were Railway services and both used ephemeral application storage for this experiment.

## Topology observed

- Node A: Railway service `r3-external-node-a`
- Node B: Railway service `r3-external-node-v2`
- Orchestrator: independent Railway service `r3-external-property-runner`
- Canonical test object: repository `sdq1_master.json`
- Content SHA-256:
  `ce0d0b351d94c4e5540a190a476e068bbddb5b729b3dabfe34a7a731b8bd96e8`

No secret values are recorded in this document.

## Observed sequence

### Phase 1 — seed and replicate

At 2026-09-18 03:40:38 UTC:
- A accepted `POST /documents` with HTTP 200.
- A served the canonical object.
- B accepted `POST /sync/receive` with HTTP 200.
- B logged:
  `Sync received id=ce0d0b351d94c4e5540a190a476e068bbddb5b729b3dabfe34a7a731b8bd96e8`.
- B served the same object with HTTP 200.

### Phase 2 — actual process loss on A

At 2026-09-18 03:40:38 UTC:
- authenticated test hook `POST /test/shutdown` on A returned HTTP 200;
- A logged `Authenticated external property test requested process shutdown`;
- subsequent A health probes returned HTTP 499 for approximately two minutes;
- therefore A was unavailable to the test orchestrator.

At 2026-09-18 03:40:41 UTC, while A was unavailable:
- B served
  `GET /documents/ce0d0b351d94c4e5540a190a476e068bbddb5b729b3dabfe34a7a731b8bd96e8`
  with HTTP 200;
- the orchestrator recomputed the object hash and recorded:
  - `node_a_unavailable=true`
  - `node_b_served_exact_object=true`
  - B SHA-256 exactly equals the canonical SHA-256.

This establishes the tested failover property: **loss of the A process did not remove access to the already replicated exact object on B.**

### Phase 3 — restart and recovery of A

A was deliberately redeployed.

At 2026-09-18 03:42:34 UTC:
- the new A container started;
- because this test used ephemeral storage, A generated a new local signing key and began with a fresh local data directory.

At 2026-09-18 03:42:37 UTC:
- A accepted `POST /sync/receive` with HTTP 200;
- A logged:
  `Sync received id=ce0d0b351d94c4e5540a190a476e068bbddb5b729b3dabfe34a7a731b8bd96e8`;
- A served the recovered exact object with HTTP 200.

At 2026-09-18 03:42:42 UTC the orchestrator recorded:
- `external_failover_recovery_pass`
- `node_a_restored_from_node_b=true`
- `same_hash_sets=true`
- `different_provider_proof=false`
- provider scope:
  `RAILWAY_SEPARATE_SERVICES_SAME_PROVIDER`.

## Security cleanup

After evidence capture:
- the test shutdown capability on A was disabled;
- A restart policy was returned to ALWAYS;
- temporary test credentials were rotated;
- the runner no longer retains a credential accepted by A/B.

## P5

The result cannot be promoted to “multi-provider resilience” or “distributed immortality”. Railway may place separate services on infrastructure under one provider, and no durable volume was attached.

## P6

The stronger property remains falsifiable:

> With A and B on independently administered providers/ASNs and durable storage enabled, destroy or disconnect A after replication. B must continue serving the exact canonical object. Recreate A from an empty durable store, reconcile from B, and recover equal hash sets and valid provenance without manual insertion of the object.

Failure of any of those conditions rejects the stronger claim.

## Next gate

1. Add durable storage to each tested node.
2. Put A and B on different providers/ASNs.
3. Use a fresh canonical object with preregistered SHA-256.
4. Capture provider/host evidence, health transition, object retrieval, resync and audit trail.
5. Rotate test credentials and disable test-only controls after the run.

Until then, the strongest honest status is:

**REMOTE SEPARATE-SERVICE PROPERTY TEST PASSED / DIFFERENT-PROVIDER + DURABLE-STORAGE PENDING**
