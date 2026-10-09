# TERZI/0.1 — Token-Efficient Relevance & Zero-loss Inference

Origin: **Claudio Terzi [CT-LGAI-001]**.

TERZI is a candidate context-purification and typed-decision layer built **around** Rizzo Flow and Jev/TypeSafe. It does not fork or rebrand Rizzo Flow. It adds a new product layer whose job is to reduce irrelevant context before expensive reasoning while preserving provenance and failing open when reduction is not trustworthy.

## Name

**TERZI = Token-Efficient Relevance & Zero-loss Inference.**

"Zero-loss" is an admission goal, not a promise. A compressed capsule is accepted only when the configured verification gate says that no material decision evidence was lost. Otherwise TERZI returns the fuller context.

## Core idea

Most agent contexts mix:

- evidence that directly changes a decision;
- provenance that is needed to trust that evidence;
- contradictory evidence;
- duplicated passages;
- operational metadata;
- conversational history that no longer matters to the current decision.

Rizzo Flow already makes cheap typed decisions over evidence, but it deliberately does **no truncation** when an input exceeds context. TERZI adds a conservative evidence-selection layer before Rizzo/Jev.

TERZI compresses by **selection, not paraphrase**:

1. split the input into addressable chunks;
2. hash every chunk;
3. remove only exact duplicates deterministically;
4. ask a local Rizzo judge which chunks might materially affect the target decisions;
5. ask Jev to audit only the chunks proposed for omission or marked uncertain;
6. build a capsule from the **original verbatim chunks**;
7. optionally run a decision-equivalence check between full and compact context;
8. fail open to fuller context whenever the gate is not satisfied.

No model-generated summary is treated as a replacement for source evidence.

## Why Jev is used for token reduction

Jev is not asked to "summarize this document". It receives a bounded set of candidate chunks plus the exact closed decisions that downstream code must make and answers a closed question:

> Would removing this chunk create a material risk of changing any target answer, hiding contradictory evidence, or removing provenance required to judge?

This uses Jev as a **relevance auditor** rather than a text generator. The expensive judge sees only omission candidates after the local Rizzo pass, so hosted token use can fall sharply on large histories.

## Architecture

```text
RAW CONTEXT
   |
   v
[Canonical chunker + hashes]
   |
   +--> exact duplicate removal
   |
   v
[Rizzo local relevance pass]
   |    |  +--> clearly needed ----------+
   |                                |
   +--> uncertain / drop candidates |
                    |               |
                    v               |
             [Jev omission audit]   |
                    |               |
                    +---------------+
                            |
                            v
                  [VERBATIM CAPSULE]
                            |
              +-------------+-------------+
              |                           |
              v                           v
       [Rizzo decisions]          [optional Jev/full
                                   equivalence audit]
              |                           |
              +-------------+-------------+
                            |
                            v
                    ACCEPT / FAIL OPEN
```

## Invariants

1. **Verbatim evidence.** Kept chunks are not rewritten by TERZI.
2. **Reversible compression.** Every capsule records the source hash and kept/omitted chunk hashes.
3. **No silent truncation.** Missing context is explicit.
4. **Conservative omission.** Uncertainty keeps evidence unless a configured second gate clears the omission.
5. **Contradictions are sticky.** A chunk that may contradict a candidate conclusion is treated as relevant.
6. **Provenance is sticky.** Source/date/authorship metadata needed to interpret evidence is treated as relevant.
7. **One evidence origin is one evidence origin.** Multiple model judgments over the same source do not become independent evidence.
8. **Model score != probability of truth.** Thresholds are operational routing thresholds and must be calibrated on labelled domain data.
9. **Fail open.** If the distiller errors, the backend is unavailable, or an equivalence check fails, use fuller context.
10. **No authority escalation.** TERZI cannot authorize publishing, spending, deployment, deletion, contracts or other external mutation.

## Two-stage token economy

### Stage A — Rizzo local

Rizzo sees each bounded chunk batch with the target decision schema and returns a typed `noul` relevance score. Local inference is used for the high-volume first pass.

Default policy is intentionally conservative:

- high relevance -> KEEP;
- middle band -> REVIEW;
- very low relevance -> DROP_CANDIDATE.

Thresholds are configuration, not truth claims.

### Stage B — Jev audit

Only REVIEW and DROP_CANDIDATE chunks are sent to Jev. Jev can restore a chunk to KEEP. Production should normally require agreement of both judges before omitting non-duplicate evidence.

This is the main economic innovation: **Jev spends tokens on the boundary, not on the whole history.**

## Context Capsule

A capsule contains:

- protocol/version;
- source SHA-256;
- target-question SHA-256;
- kept chunk ids, hashes and verbatim text;
- omitted chunk ids and hashes;
- deterministic duplicate map;
- judge model ids;
- decision thresholds;
- character/byte and optional tokenizer-exact token counts;
- reduction ratio;
- verification status.

The capsule itself is safe to cache by `(source_hash, target_questions_hash, policy_version, judge_fingerprints)`.

## Decision-equivalence gate

For high-value workflows or benchmark samples, run the same typed questions on:

A. original context;
B. TERZI capsule.

Admission requires the configured decision signature to match. Any material mismatch is a **compression failure** and restores the fuller context.

A domain benchmark should measure:

- exact decision agreement;
- false omission rate;
- contradiction retention;
- provenance retention;
- reduction ratio;
- wall-clock latency;
- local compute;
- hosted input tokens;
- total cost.

Reduction ratio by itself is never a success metric.

## TERZI purity metric

Candidate metric:

```
purity = decision_relevant_bytes / capsule_bytes
```

This requires labelled evidence and cannot be inferred from model confidence alone.

Operational metrics should remain separate:

- `compression_ratio`
- `decision_agreement`
- `false_omission_rate`
- `hosted_tokens_saved`
- `latency_delta`

## Product modes

### SAFE
Rizzo pass + Jev audit + full-vs-capsule equivalence on every request.

### BALANCED
Rizzo pass + Jev audit for omission candidates; equivalence on sampled/high-risk requests.

### LOCAL
Rizzo only; uncertain evidence is kept. No claim of Jev validation.

### BENCHMARK
No external actions. Saves full provenance, logits/scores where available, hashes, timings and exact decisions.

## Relationship to Rizzo Flow

Rizzo Flow remains an independent Apache-2.0 project. TERZI talks to its published HTTP interface and does not copy its source. If TERZI later incorporates Rizzo code, preserve Apache-2.0 attribution and NOTICE obligations.

Upstream reference reviewed for this design:
- repository: `Rizzo-AI-Academy/rizzo-flow`
- upstream commit reviewed: `b9ba007ee4d2928bbab5b1d8bfe9009c3696b6de`
- Rizzo prompt behavior reviewed: prompt v3, shared state prefix, no truncation on context overflow.

## Relationship to Jev

The existing R³ `typesafe_sister.client.system_one` remains the hosted Jev/TypeSafe route when configured. TERZI does not assume that Jev is always available. Missing Jev means LOCAL/conservative behavior, not fabricated validation.

## First admission benchmark

Before ACTIVE status:

1. collect at least 50 representative contexts from one domain;
2. label which chunks are materially required for the target decisions;
3. freeze target questions before evaluation;
4. compare FULL vs TERZI decisions;
5. require zero critical false omissions in the admission set;
6. report decision agreement and token savings separately;
7. include missing-evidence and contradiction cases;
8. repeat with chunk order perturbations;
9. bind results to Rizzo/Jev model ids and fingerprints where available;
10. store the report create-only.

Until that benchmark exists, TERZI is **CANDIDATE**.
