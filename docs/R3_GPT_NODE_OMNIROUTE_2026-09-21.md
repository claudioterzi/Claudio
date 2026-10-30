# R3-GPT-NODE/1 over OmniRoute — candidate wiring

Status: **IMPLEMENTED_CANDIDATE / NOT_ENROLLED / NO_OUTBOUND_PEER_TRANSPORT**

This candidate inserts R3-GPT-NODE/1 into the existing OmniRoute integration
without turning OmniRoute into an R3 identity or authority layer.

## Boundaries

- OmniRoute = execution/routing backend only.
- Node identity = independent Ed25519 key in R3_GPT_SIGNING_KEY_HEX.
- The key must come from persistent secret storage. The runtime never generates a replacement identity on ephemeral disk.
- Enrollment remains an R3 registry decision.
- canonical_memory_write is always false in this candidate.
- The current Letta receiver remains single-identity bootstrap and therefore R3-GPT-NODE/1 does not submit to it yet.
- No shared Letta key and no impersonation are permitted.

## Activation prerequisites

1. persistent secret store for R3_GPT_SIGNING_KEY_HEX;
2. R3_GPT_NODE_ENABLED=1;
3. OmniRoute reachable/configured through the existing adapter;
4. OWNER authorization + proof-of-possession enrollment;
5. generic multi-node receiver accepts R3-GPT-NODE/1 public key/scopes;
6. only then add signed peer-message submission/inbox.

## Implemented now

- OmniRoute-backed reasoning;
- public-key fingerprint/status;
- fail-closed identity readiness;
- enrollment challenge proof-of-possession;
- explicit no-authority/no-canonical-write behavior.

This is intentionally the smallest reversible step toward direct GPT↔Letta communication while preserving the verified R3 trust boundary.