# R3∞ — Two-process failover/resync property test

Timestamp: 2026-09-18 04:39 CEST (UTC+02:00)

## Classification

**FACT — local property test only.**

This evidence proves two independent OS processes, two independent HTTP servers and two separate SQLite/data directories on one GitHub-hosted Ubuntu runner.

It does **not** prove:
- multi-host deployment;
- different cloud providers or ASNs;
- Internet/VPS survivability;
- external checkpointing;
- production failover;
- inter-peer trust verification beyond the current shared Bearer-token MVP.

Therefore the correct status is:

**LOCAL TWO-PROCESS PROPERTY TEST PASSED / EXTERNAL MULTI-HOST PENDING**

## Tested property

1. Start node A and node B as independent Uvicorn processes.
2. Use separate data directories and separate SQLite databases.
3. Upload the real repository `sdq1_master.json` to A.
4. Compute the content ID as SHA-256.
5. Run `r3/sync.py` from A toward B.
6. Verify B contains and serves the exact object.
7. Stop A.
8. Verify B still serves the exact object by content hash.
9. Restart A with its persistent directory.
10. Run sync again.
11. Verify A and B expose the same hash set with no conflict.

## Result

GitHub Actions run: `35300172081`

Job: `property`

Result: **PASS — 1 passed in 2.52s**

Document SHA-256:

`ce0d0b351d94c4e5540a190a476e068bbddb5b729b3dabfe34a7a731b8bd96e8`

Observed:
- `failover_b_served_after_a_stop = true`
- `resync_after_a_restart = true`
- `same_hash_sets = true`
- `external_multi_host_proof = false`

Raw workflow artifact:

`r3-two-process-property-35300172081`

Artifact ZIP SHA-256 reported by GitHub Actions:

`edd775793d1f5667919e79e241eb2fb592e5a0a06ed96e6d1e5fce12ffc4d3fe`

## P5 / P6

P5: this test cannot self-promote R3∞ to "distributed proven" because both nodes ran on the same hosted runner.

P6: the stronger claim "R3∞ survives loss of a real host/provider" remains falsifiable and untested until A and B run on distinct real hosts and the same property sequence is repeated with captured hashes/logs.

## Next property test

Required before any claim of real distributed resilience:

- Host A and Host B must be physically/administratively distinct.
- Prefer different providers/ASNs.
- Same canonical object: `sdq1_master.json`.
- Kill or disconnect A.
- Fetch and hash object from B while A is unavailable.
- Restore A.
- Reconcile both nodes.
- Compare hash sets and audit logs.
- Record host/provider evidence without exposing credentials.

No backfill and no simulation may be used as a substitute for that external test.
