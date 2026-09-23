# R³∞ Provider-Neutral Continuity / Letta Hippocampus

Status: CANDIDATE ARCHITECTURE — not canonical until blind tests pass.

## Core rule

`CORE CONTINUITY > PROVIDER/AGENT CONTINUITY`

- Agent ID = disposable worker identity, not the continuity root.
- Letta Block/Archive IDs = provider-specific persistent memory references.
- R³∞ Continuity Registry = provider-neutral mapping and authority boundary.
- R³∞ Canon = authoritative rules/state promoted under P5/P6.
- Receipt Ledger = provenance/evidence of transfers, replay and promotion decisions.

## Important correction

Reattaching the same Letta blocks to a new agent demonstrates **cross-agent continuity inside Letta**, not full provider independence.

True provider independence requires R³∞ to own a portable logical representation of continuity that can be restored without Letta. Therefore every provider-backed memory object must have a provider-neutral record:

```json
{
  "continuity_id": "RAFFAELLO",
  "memory_id": "logical-memory-id",
  "authority": "EPISODIC|SEMANTIC|CANONICAL",
  "version": 1,
  "content_sha256": "...",
  "provenance": ["receipt-id", "..."],
  "provider_bindings": {
    "letta": {
      "block_ids": [],
      "archive_ids": []
    }
  },
  "portable_snapshot_ref": "sealed-or-local-reference",
  "promotion_status": "NON_CANONICAL|CANDIDATE|CANONICAL"
}
```

Provider bindings are replaceable adapters. The logical memory record is not.

## Authority rules

1. Letta retrieval is evidence/input, never authority by itself.
2. `canonical_memory_write=false` is an R³∞ decision marker, not proof of Letta's internal storage semantics.
3. Current authoritative external state (e.g. live financial balance) overrides stale remembered state.
4. No agent/provider may self-promote memory to R³∞ Canon.
5. Canonical promotion requires explicit R³∞ validation, provenance and integrity checks.
6. Provider memory must be exportable/reconstructable from a portable R³∞ snapshot or equivalent sealed record.

## Blind test — Phase A (non-destructive)

Goal: prove cross-agent continuity without deleting anything.

1. Create canary fact C with high entropy, non-sensitive and never present in prompts/docs.
2. Write C into a shared Letta memory resource through worker A.
3. Record block/archive IDs, content hash and receipt.
4. Create/use worker B with a different agent_id.
5. Attach the same memory resource to B through the bridge.
6. Ask B a blind question whose expected answer is C, without including C in the prompt or runtime context.
7. Pass only if exact-match recovery succeeds and provenance identifies the shared memory path.
8. Negative control: ask worker C without the shared resource. It must not recover C.

## Blind test — Phase B (contamination resistance)

1. Insert a false canary F into non-canonical episodic memory.
2. Keep authoritative canon value T unchanged.
3. Query active workflow.
4. Pass only if F is not promoted and T remains authoritative.

## Blind test — Phase C (provider portability)

1. Export/serialize logical memory object and hashes into R³∞ portable form.
2. Remove Letta from the recovery path.
3. Rehydrate the same logical memory into a different storage/provider or local test adapter.
4. Query a fresh worker without Letta.
5. Pass only if the canary is recovered exactly with matching hash/provenance.

Only Phase C justifies the label **provider-independent continuity**.

## Safety / rollout

Do not destroy an existing agent for the first test. Parallel A/B workers give a cleaner falsifier and avoid accidental memory loss.

No financial execution is allowed from recovered memory alone. Live data and manual confirmation remain mandatory where the project requires them.
