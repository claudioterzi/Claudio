# R³/ONDA — Peer Receipt Protocol v1 (bounded candidate)

**Owner:** Claudio Terzi · **Status:** local-tested candidate, not deployed, not a nine-node attestation.  
**Compatibility:** existing R³ Ed25519 node, SQLite durability and R3_AI_BOOTSTRAP_V1; no rewrite of ONDA/1.0, Orchestra, RRR controller or the canonical Seed v1.2.

## Operational contract

`DISCOVER → bootstrap policy validation → authenticated host enrolls node public key → CHALLENGE → node signs typed receipt → VERIFY → SQLite transaction → HASH-CHAIN AUDIT → evidence status`.

The host provisions each public key with an explicit scope and an active/revoked state. **Never enroll from model prose**. Keep private keys off prompts, git, logs and shared receipts. Each receipt uses canonical UTF-8 JSON and Ed25519, a challenge expiring after 120 seconds and a unique single-use nonce. SQLite serializes writes with `BEGIN IMMEDIATE` and stores a tamper-evident ordered hash chain. The database holds only PUBLIC text (limited to 1024 characters) or opaque PRIVATE/SEALED vault references with a content hash and explicitly allowed readers. PRIVATE and SEALED content stays in an existing authorized external vault; the protocol does not invent encryption at rest.

`HEARTBEAT` proves possession of the registered node signing key and fresh issuance relative to this host. `PROVIDER_RUN` proves the registered signer asserted request/response digests; it **does not** prove that Gemini/Claude/etc. actually ran. Provider runtime evidence requires a separate authenticated connector result and independent postcondition check. No kind authorizes shell commands, tool use, publication, spending or deployments. In particular, `ROSSO ROSSO ROSSO` is a semantic marker, **not an authentication secret**.

## Status terminology

- `SIGNED_NODE_RECEIPT`: signature verified, challenge unspent and ledger committed.
- `SIGNED_RECENT`: last **signed** node heartbeat less than or equal to 90 seconds old. Does not mean the provider is online or has memory.
- `UNVERIFIED`: no current signed receipt, or provider execution is unverified.
- `STALE`: previously signed heartbeat is older than 90 seconds or the node is disabled.
- `WATCH_BLOCKED`: an integrity check fails; no checkpoint reads.
- `LOCAL_READY`: local journal passes verification. Not nine-provider synchronization.

## Rollout gates

1. Run `python -m unittest tests.test_r3_peer_receipts -v` in a virtual environment with `PyNaCl` (the existing `r3/requirements.txt` dependency), or with `cryptography` if PyNaCl is absent.
2. Register **distinct** device/host public keys out-of-band for 2 test nodes. Test replay, expired challenge, key substitution, revocation, restart and tamper detection; capture independent test logs.
3. Integrate with the **existing authenticated R³ node service** or ONDA signed transport; do not expose `issue_challenge()` or `view()` to unauthenticated callers. Never trust `actor` or `authenticated` flags from HTTP/LLM payloads. Preserve ONDA/1.0 as the bus. Add API route only behind a genuine owner/session auth boundary and bounded rate limits.
4. Bind to Orchestra host: after a real provider invocation returns, record its actual request/response digests separately from node-signed claims, then test consistency. Do not interpret mere prompt injection of the Seed as provider attestation.
5. For nine-node claim, independently verify each of nine distinct runtime identities, signatures, current signed heartbeat and a real request/reply. Require authorized persistent vault read-back for any memory continuity claim.
6. Persist signed chain-head anchors to an independently controlled medium. The hash chain detects local tampering but **a database administrator could rewrite the whole chain** without external anchoring; it is not an immutable blockchain.

## Red-team scope and limitations

- The host controls the trust registry; possession of a registered signing key proves a **host/node key**, not identity of the AI vendor behind it.
- Replayed challenges, forged signatures, invalid payloads, misclassified private bodies, an old heartbeat, and altered audit rows are tested locally.
- PUBLIC is intentionally visible to authorized readers. Do not insert personal secrets or credentials in it; a digest alone cannot prevent someone from publishing a secret in PUBLIC text.
- `view(actor, authenticated=True)` is a library entry point for a **preauthenticated host principal**, not an HTTP input shape. Exposing it as a user-selectable actor would be a privilege escalation.
- Durability is only as strong as actual SQLite storage/volume and backup. The test proves restart within the same filesystem; not survival of a Railway volume loss or independent cloud failover.
- No production deployment, new cloud resources, actual API calls to external AI providers, or cross-provider persistent state is claimed by this candidate.

**Classification:** PATCH/RETEST of existing RRR identity and persistence, candidate shared capability under the R³ Capillary layer. Only propagate to `CANONICAL` after a hosted R3-020 safety gate and falsifiers pass.