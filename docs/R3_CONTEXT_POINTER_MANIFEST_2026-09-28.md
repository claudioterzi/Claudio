# R³∞ Context Pointer Manifest — Candidate 2026-09-28

Status: **CANDIDATE / REVERSIBLE / NO PRODUCTION MUTATION**

## Problem

R³∞ has accumulated a large set of canonical and operational documents. Loading
full copies of the same material into every reasoning step increases token cost,
latency and the probability of stale duplicated context.

The goal is not to compress or rewrite history. The goal is to keep history in
its authoritative source and pass a small, deterministic index first.

## Candidate

This branch adds:

- `public/r3-context-pointer-manifest.json`
- `scripts/r3_context_pointer_manifest.py`
- `tests/test_r3_context_pointer_manifest.py`

The selector emits only:

- stable pointer id;
- repository-relative source path;
- short role;
- load mode.

Source bodies are never embedded in the pointer packet.

## Loading policy

1. Load the small `root` pointer set for orientation.
2. Match task tags.
3. Add only relevant `on_demand` pointers.
4. Retrieve the pointed source only when its content is actually required.
5. Preserve source authority, provenance and verification rules.

This is a routing optimization, not a memory rewrite.

## Safety / authority

- Jev remains advisory only.
- The pointer manifest does not authorize external actions.
- A pointer is not evidence by itself; the pointed source remains authoritative.
- Repository escape paths and missing targets fail validation.
- Inline source bodies are rejected.
- Selection is bounded by an explicit limit.

## Falsification criteria

Reject or revise this candidate if any controlled comparison shows:

- worse task success at equal evidence quality;
- missing required authority/provenance context;
- materially higher human correction rate;
- stale or broken pointers;
- no meaningful token/latency reduction.

## Next verification

Run a controlled A/B on representative R³ tasks:

A. current startup/context loading;
B. pointer-first loading with on-demand expansion.

Measure:

- input tokens;
- latency;
- task success;
- missing-context events;
- human interventions;
- provenance/authority errors.

Promotion to default behavior requires equal-or-better verified task success with
lower context cost and no authority regression.
