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


## Refinements after external review

The external review is directionally aligned, but the following corrections are canonical constraints for the experiment:

1. **Do not call the architecture definitive before evidence.** Until Phases A/B/C pass with preserved evidence, status remains `CANDIDATE`.
2. **R³∞ Canon is not TypeSafe/Jev.** TypeSafe/Jev is advisory under repository policy; it cannot be the authority that decides truth, permissions, spend, promotion or canonical state. Canonical authority resides in versioned R³∞ state/artifacts plus deterministic validation, P5/P6, provenance and explicit promotion rules.
3. **Do not snapshot every write by default.** Prefer an append-only event/receipt log plus checkpointed signed portable snapshots. Per-write snapshots are allowed only if measurements justify their latency/storage cost.
4. **A Railway-local database is not sufficient for sovereignty.** The portable continuity representation must have at least one recovery path independent of the active runtime/provider. A bridge database may be a working store, but not the only copy.
5. **"Migration in seconds / no downtime / total sovereignty" are hypotheses until measured.** Record recovery time objective (RTO), recovery point objective (RPO), export completeness and hash/provenance preservation before making those claims.
6. **CI split:** deterministic schema/hash/promotion tests may run on every build; live Letta/provider integration tests should run in an isolated integration job (scheduled/manual or gated) to avoid nondeterminism, quota coupling and false CI failures.

## Persistence pattern

Recommended write path:

```
EVENT -> Receipt Ledger (append-only)
      -> provider adapter write (e.g. Letta)
      -> continuity registry update
      -> checkpoint policy decides whether to emit signed portable snapshot
```

A checkpoint must include the logical continuity IDs, versions, content hashes, provenance references and provider bindings needed to reconstruct state without trusting the provider's private internal representation.

## Promotion boundary

```
Retrieved memory -> NON_CANONICAL evidence
                  -> deterministic validation + provenance checks
                  -> CANDIDATE
                  -> explicit R³∞ promotion gate
                  -> CANONICAL
```

No semantic model, Letta agent, TypeSafe/Jev result, or provider receipt may skip this path.
