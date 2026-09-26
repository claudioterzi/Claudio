# R³∞ — OmniRoute Gateway Integration · 2026-09-21

Status: CANDIDATE / OPTIONAL SHARED SERVICE  
Owner: Claudio Terzi  
Signature: C.Terzi

## Purpose

Use OmniRoute as an optional routing/failover gateway underneath the existing R³∞ / SDQ-1 router.

It is **not**:
- a new authority layer;
- a replacement for R³∞;
- a replacement for TypeSafe/Jev;
- proof that any provider is currently reachable;
- permission to bypass P5/P6, Zero-Assunto, provenance or secret boundaries.

## External capability basis

Current OmniRoute documentation reports:
- an OpenAI-compatible API at `/v1/chat/completions`;
- default local API base `http://localhost:20128/v1`;
- zero-config auto-routing model IDs including `auto`, `auto/fast`, `auto/cheap`, `auto/smart`;
- category/tier routing such as `auto/reasoning:pro`;
- dynamic routing over currently connected provider accounts;
- optional combo strategies including multi-model fusion.

Sources:
- https://github.com/mkolbas/omniroute/blob/main/docs/routing/AUTO-COMBO.md
- https://github.com/pitbaden/omniroute/blob/main/docs/USER_GUIDE.md
- https://github.com/zorojean/omniroute/blob/main/docs/API_REFERENCE.md

These are documentary facts about OmniRoute's reported interface. Local R³∞ capability is verified only by our own tests/runtime evidence.

## R³∞ integration

Canonical adapter:
`sdq1/llm/providers/omniroute_provider.py`

Shared registry:
`sdq1/llm/router.py`

Configuration:
`sdq1/config/sdq1.yaml`

Capillary inheritance:
`R3_CAPILLARY_INHERITANCE.yaml → OMNIROUTE_GATEWAY`

### Profile mapping

- default → `auto`
- realtime → existing Grok/Perplexity first; OmniRoute `auto/smart` as additional failover
- ragionamento → `auto/reasoning:pro`
- veloce → `auto/fast`
- ricerca → Perplexity first; OmniRoute `auto/smart` as additional route
- economia → `auto/cheap`
- esplora → `auto/smart`
- soglia → `auto`
- cristallizza → `auto/reasoning:pro`
- potente → `auto/reasoning:pro`
- locale → **no automatic OmniRoute**; Ollama remains first and cloud routing is not silently introduced

## Security contract

Environment names only:
- `OMNIROUTE_BASE_URL`
- `OMNIROUTE_API_KEY`
- `OMNIROUTE_LOCAL_NO_AUTH`

Rules:
1. remote OmniRoute requires an API key;
2. unauthenticated mode is allowed only when explicitly enabled and the endpoint hostname is loopback;
3. no OmniRoute key is persisted in model memory or repository artifacts;
4. adapter availability is not runtime reachability;
5. OmniRoute output remains model output under P5;
6. consequential state changes still require R3-007 postcondition verification.

## Failover rule

If OmniRoute is absent, misconfigured, unreachable or rate-limited, SDQ-1 continues through the existing provider cascade. No task should fail merely because OmniRoute is unavailable when another verified route exists.

## Fusion

OmniRoute documents a Fusion strategy that fans out to multiple models and synthesizes via a judge. R³∞ does **not** enable Fusion by default in this patch.

Reason:
R³∞ already has HyperRed/Sister independent-review semantics. Any use of Fusion must preserve independent outputs/provenance and must not turn a judge synthesis into authority.

Fusion is therefore a future candidate for bounded comparison, not an automatic replacement for R³∞ multi-AI verification.

## Falsifiers

The candidate is rejected or patched if:
- remote no-key configuration becomes usable;
- local no-auth works without explicit opt-in;
- OmniRoute absence blocks the existing fallback chain;
- local/privacy profile silently routes to cloud;
- requested auto-route model is lost from provenance;
- security/static tests fail.

— C.Terzi
