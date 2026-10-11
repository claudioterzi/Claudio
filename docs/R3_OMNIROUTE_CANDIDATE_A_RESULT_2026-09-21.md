# R³∞ — OmniRoute Candidate A Result · 2026-09-21

Owner: Claudio Terzi  
Signature: C.Terzi  
Classification: PUBLIC-SAFE  
Status: VERIFIED_ISOLATED / NOT_PRODUCTION_DEPLOYED

## Decision

**ADOPT Candidate A as the preferred OmniRoute integration path: upstream 3.8.51 native model exposure filtering + operator denylist.**

This decision applies to the R³∞ integration strategy. It does **not** claim that OmniRoute 3.8.51 is deployed in production, nor that its current upstream Docker build is production-ready in our environment.

## Baseline truth

The runtime that produced the original live `model:auto` HTTP 502 was OmniRoute 3.8.50 / Docker latest digest:

`diegosouzapw/omniroute@sha256:085c57adf499a8aaa9f35ccde95c0df9c11bd9ecd18d6c9edbf3b68b8079ba9d`

F0 inventory proved that this runtime has:
- `virtualFactory.ts`: present;
- `modelExposureFilter.ts/js`: absent;
- `modelLockoutFilter.ts/js`: absent;
- no `filterModelExposureCandidates` wiring in `virtualFactory.ts`.

The npm `omniroute@3.8.50` package and its published tarball independently showed the same absence.

## Upstream 3.8.51 truth

Verified source:
- upstream: `diegosouzapw/OmniRoute`
- ref: `release/v3.8.51`
- tested source SHA: `7a921299c5b4c28dcf837f56a1c312b61414a646`

3.8.51 includes:
- `open-sse/services/autoCombo/modelExposureFilter.ts`;
- `open-sse/services/autoCombo/modelLockoutFilter.ts`;
- exposure filtering wired directly into the `auto/*` candidate-pool build;
- `modelVisibilityAllowlist` / `modelVisibilityDenylist` settings;
- existing per-model connection lockout/resilience logic.

Therefore the R³ rule is **reuse the upstream filtering/lockout architecture before adding any custom parallel router or breaker.**

## Deterministic Candidate A test

Canonical successful workflow:
- GitHub Actions run: `35561949401`
- conclusion: `success`
- artifact: `10622417386`
- artifact digest: `sha256:c9aa33c116a64937620216d52179222ffabfc2c1c1d248d68908763252ddb46d`

The harness used an isolated OmniRoute 3.8.51 dev runtime and a deterministic local OpenAI-compatible provider exposing exactly five models:

- healthy: `r3-good-model`
- deliberately bad: `anthropic/claude-opus-5`
- deliberately bad: `big-pickle`
- deliberately bad: `felo-chat`
- deliberately bad: `felo-search`

The mock upstream returned deterministic 401 / 403 / 400 failures for the four bad models and HTTP 200 for the healthy model.

No production runtime was changed and no user provider secret was used.

## P1 — exposure / candidate eligibility

Native denylist:

```json
{
  "modelVisibilityDenylist": [
    "anthropic/claude-opus-5",
    "big-pickle",
    "felo-chat",
    "felo-search"
  ]
}
```

Observed postcondition:

```json
{
  "blocked_catalog": 0,
  "blocked_pool": 0,
  "good_catalog": 1,
  "good_pool": 1,
  "pass": true
}
```

Result: **PASS**.

The bad models were absent from both the post-filter catalog and the actual `auto` candidate pool, while the healthy model remained available.

## P2 — runtime execution

Observed postcondition:

```json
{
  "http_status": 200,
  "latency_ms": 108,
  "nonempty_response": true,
  "resolved_model": "r3-good-model",
  "error_summary": "",
  "pass": true
}
```

Result: **PASS**.

Final harness verdict: **`ADOPT_A`**.

## Important causal limitation

The same 3.8.51 deterministic runtime also completed through the healthy model before the denylist while five bad candidates were present.

Therefore this experiment verifies:

1. 3.8.51 can remain operational with bad candidates present in this controlled scenario;
2. the native denylist removes the targeted bad candidates from the real auto pool;
3. the good candidate survives the filter;
4. `model:auto` still completes after filtering.

It does **not** isolate how much of the improvement relative to the original 3.8.50 live 502 comes from:
- the 3.8.51 upgrade itself,
- improved dispatch/resilience behavior,
- the exposure denylist,
- or their combination.

Do not claim denylist-only causality without a controlled 3.8.50/3.8.51 equivalent external-provider comparison.

## Falsifier correction

An earlier Candidate A run incorrectly reported `blocked_catalog=16` because the evaluator searched the substring `opus-5` and counted distinct models such as `dva/claude-opus-5-high`.

That was an evaluator false positive, not an OmniRoute exposure failure.

The harness was corrected to match the exact semantic IDs:

`(^|/)anthropic/claude-opus-5$ | (^|/)big-pickle$ | (^|/)felo-chat$ | (^|/)felo-search$`

The corrected run is the canonical evidence.

Rule learned: **model-policy falsifiers must compare canonical semantic IDs, not broad substrings.**

## Separate upstream build blocker

A different 3.8.51 workflow attempted a full Docker build from `release/v3.8.51`.

It failed before runtime in the Next/Turbopack build with repeated Node builtin resolution errors such as:
- `Can't resolve 'fs'`
- `fs/promises`
- `net`
- `tls`
- `http2`
- `readline`

This is a **BUILD/UPSTREAM ARTIFACT blocker**, not a Candidate A functional falsifier.

Consequently:

- native 3.8.51 filtering path: VERIFIED in isolated dev runtime;
- current source Docker build in our GitHub runner: NOT READY;
- production deployment: NOT DONE;
- PR #79: remains candidate/draft;
- Candidate B custom router/breaker: NOT ACTIVATED.

## Architecture decision

Preferred order remains:

`UPSTREAM NATIVE FIX > EXACT UPSTREAM BACKPORT > CUSTOM R³ PATCH`

Do not introduce:
- a second breaker state store;
- a second auto-router;
- a Kilo authority layer;
- static global `known_bad` state when upstream model-level facilities exist.

## Next gate before production

Production promotion requires:
1. a deployable/published 3.8.51-equivalent runtime or resolution of the upstream Docker build blocker;
2. the same postcondition checks on the target runtime;
3. authoritative runtime health after deployment;
4. preservation of R³ fallback if OmniRoute is unavailable;
5. no secret leakage;
6. PR #79 branch-protection/status requirements satisfied.

— C.Terzi
