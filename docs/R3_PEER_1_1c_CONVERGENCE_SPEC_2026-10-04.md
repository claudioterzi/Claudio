# R3-PEER/1.1c — CONVERGENCE SPEC

Status: PROPOSAL (non CANON). Diventa CANON solo dopo property test su due implementazioni indipendenti.
Base: R3-PEER/1.0, review Claude/DeepSeek/Qwen, commit 81dce982dfbd1d4b5f646b1418efbc24c8be4bf0.
Data: 2026-10-04.

## 1. FINDINGS & DECISION MATRIX

| # | Origine | Problema | Decisione | Motivo |
|---|---|---|---|---|
| 1 | Claude / DeepSeek / Qwen | Store separati vs atomicità | Single-DB default. Multi-store supportato con outbox, non gode di atomicità CAS senza 2PC | Atomicità |
| 2 | Claude | AUTO test SHA-256 non prova il modello | AUTO come test di endpoint; MODEL_ATTESTED richiede artefatto firmato separato | Test deve esercitare la proprietà |
| 3 | Claude | channel_id aggira replay scope | Channel Registry autoritativo | Sender non crea canali |
| 4 | Claude | Checkpoint rifirmabile | Signing key fuori dominio DB | Tamper-evidence reale |
| 5 | DeepSeek | Canonicalizzazione byte non definita | JCS RFC 8785 normativo. Protobuf NON conforme in 1.1c | Due implementatori non possono scegliere |
| 6 | DeepSeek | Lifecycle LINK-ONLY → ACCEPT | Promozione solo via nuova decisione SUPERSEDES con evidenza nuova | Non automatica, non retroattiva |
| 7 | DeepSeek | Retention assente | Segmenti firmati, chiusi a intervalli, archiviabili | Head online, storia verificabile |
| 8 | DeepSeek | Verifier/provider trust-domain | Verifier fuori dominio provider obbligatorio in 1.1c | Co-locazione rende correlazione tautologica |
| 9 | Qwen | Attestation senza funzione di decisione | policy_profile_id + regole deterministiche | Determinismo richiesto |
| 10 | Qwen | prev_memory_hash circolare | observed_source_memory_head (sender) + canonical_memory_head_before/after (receiver) | Sender osserva, receiver determina |
| 11 | Qwen | msg_id vs nonce | msg_id = UUIDv7, nonce = random 128/256 bit. Due unique constraints scoped | Semantica distinta |
| 12 | Qwen | Revocation non formalizzata | REVOCATION con effective_from, SUPERSEDES, MARKS_AT_RISK | Storia immutabile, giudizio rivalutabile |

## 2. DISCARDED FINDINGS

| # | Proposta | Origine | Motivo del rigetto |
|---|---|---|---|
| D1 | confidence_weight: 0.93 come campo envelope | esterno | Non calibrato, non falsificabile |
| D2 | Trust ladder NODE→TRANSPORT→PROVIDER→MODEL | esterno | Proprietà ortogonali, la scala è una forzatura |
| D3 | AUTO_VERIFIED come stato finale | proposta precedente | Rinomina in PROVIDER_ENDPOINT_CORRELATED |
| D4 | Payload mode (REF) come proxy LINK-ONLY | Qwen (corretto) | Trasporto ≠ decisione epistemica |
| D5 | Accordo tra IA come evidenza indipendente | prassi esterna | Vietato dal canone R³ |
| D6 | Firme Ed25519 come prova identità modello | prassi esterna | Autentica il nodo, non il modello |
| D7 | String matching su constraint violation | Meta | Fragile, non portabile |
| D8 | Fallback silenzioso PG → in-memory | Meta | Viola la regola "test che passa non è prova" |
| D9 | Eliminazione chiavi revocate | Meta | Rompe history preserved |
| D10 | Kirkpatrick principle come riferimento tecnico | documento precedente | Non riconosciuto; il principio sta in piedi da sé |

## 3. OPEN FINDINGS

| # | Punto | Stato | Chi può chiuderlo |
|---|---|---|---|
| O1 | claimed / verified a livello schema | APERTO | Verifier |
| O2 | Policy del consumatore a valle | APERTO | Specifica futura |
| O3 | Anchor esterno checkpoint se signing key compromessa | APERTO | Modello minaccia |
| O4 | Witness indipendente prev_message_hash | APERTO | Architettura |
| O5 | Broadcast replay semantics | APERTO | Specifica |
| O6 | Versioning semantico model ID | APERTO | Federazione provider |
| O7 | MODEL_ATTESTED senza provider mainstream con attestazione nonce | INERTE per scelta | Federazione provider |
| O8 | Modello di minaccia | APERTO | Red-team |

Regola: un OPEN FINDING non blocca 1.1c, ma nessuno può dichiararlo risolto senza evidenza esportata.

## 4. ENVELOPE

```json
{
  "version": "R3-PEER/1.1c",
  "channel_id": "uuid-v7",
  "channel_registry_ref": "opaque:chanref",
  "msg_id": "uuid-v7",
  "sender_node_id": "ed25519:...",
  "sender_key_ref": "opaque:keyref",
  "recipient_node_id": "ed25519:...",
  "nonce": "base64(128..256 bit)",
  "timestamp": "RFC3339",
  "expiry": "RFC3339",
  "operation": "string",
  "policy_profile_id": "string",
  "prev_message_hash": "sha256:...",
  "observed_source_memory_head": "sha256:...|null",
  "source_memory_namespace": "string|null",
  "observed_decision_head": "sha256:...|null",
  "payload_mode": "INLINE|REF",
  "payload": "object|null",
  "payload_ref": "uri|null",
  "payload_hash": "sha256:...",
  "raw_input_hash": "sha256:...",
  "claimed_identity": {
    "node_identity": "ed25519:...",
    "provider_identity": "string|null",
    "provider_account_ref": "opaque:acctref|null",
    "model_requested": "string|null",
    "model_reported": "string|null",
    "transport_identity": "string|null",
    "evidence_origin_claimed": "api_direct|human_relay|log_export|synthetic"
  },
  "causal_origin_ids": ["decision_id"],
  "evidence_parent_ids": ["decision_id"],
  "signature": "ed25519:..."
}
```

## 5. DECISION RECORD

```json
{
  "decision_id": "uuid-v7",
  "ledger_index": 12345,
  "prev_decision_hash": "sha256:...",
  "entry_hash": "sha256:...",
  "policy_profile_id": "string",
  "policy_version": "string",
  "router_version": "string",
  "decision": "ACCEPT|LINK-ONLY|DUPLICATE|REJECT|SUPERSEDES|REVOCATION|MARKS_AT_RISK",
  "reason": "string",
  "input_event_hash": "sha256:...",
  "raw_input_hash": "sha256:...",
  "identity_vector": {
    "node_auth_status": "VERIFIED_ED25519|MISMATCH|UNVERIFIED|MISSING",
    "transport_status": "PROVIDER_ENDPOINT_CORRELATED|UNVERIFIED|MISSING",
    "provider_status": "PROVIDER_REPORTED|PROVIDER_ACCOUNT_UNKNOWN|UNVERIFIED|MISSING",
    "model_status": "MODEL_ATTESTED|PROVIDER_REPORTED_MODEL|NOT_ATTESTED"
  },
  "evidence_origin_verified": "api_direct|human_relay|log_export|synthetic|UNVERIFIED",
  "canonical_memory_head_before": "sha256:...|null",
  "canonical_memory_head_after": "sha256:...|null",
  "memory_namespace": "string|null",
  "memory_write": "NONE|CANONICAL|LINK|SUPERSEDE|MARK_AT_RISK",
  "evidence_parent_ids": ["decision_id"],
  "causal_origin_ids": ["decision_id"],
  "timestamp": "RFC3339"
}
```

## 6. POLICY PROFILE — FORMA

```yaml
profiles:
  MEMORY_ADOPT:
    require:
      node_auth_status: VERIFIED_ED25519
      transport_status: [PROVIDER_ENDPOINT_CORRELATED, UNVERIFIED]
    rules:
      - {if: {model_status: MODEL_ATTESTED}, then: ACCEPT}
      - {if: {provider_status: PROVIDER_REPORTED}, then: LINK-ONLY}
      - {else: REJECT}
  AUDIT_LOG:
    require:
      node_auth_status: VERIFIED_ED25519
    rules:
      - {if: {transport_status: PROVIDER_ENDPOINT_CORRELATED}, then: ACCEPT}
      - {else: LINK-ONLY}
  REVOCATION_INTAKE:
    require:
      node_auth_status: VERIFIED_ED25519
    rules:
      - {if: {operation: KEY_REVOKE}, then: ACCEPT}
      - {else: REJECT}
```

Decisione fuori tabella → REJECT con reason: POLICY_UNDEFINED.

## 7. CANONICAL BYTE ENCODING

Scelta normativa: JCS RFC 8785.

- Obbligatorio per raw_input_hash, payload_hash, input_event_hash, entry_hash.
- Protobuf non conforme a 1.1c. Se una futura versione lo adotterà, sarà una major.
- Implementazioni che divergono sui bytes non sono interoperabili.

## 8. REGOLE OPERATIVE

### Envelope
- channel_id deve esistere in Channel Registry autoritativo.
- Sender dichiara observed_source_memory_head, mai canonical_memory_head.
- msg_id UUIDv7, nonce random. Entrambi unique scoped (channel, sender).
- provider_account_ref opaco (provref:...). Mapping solo in secret store.

### Decision
- identity_vector ortogonale, mai ordinato, mai sommato.
- Decisione deterministica via policy_profile_id + policy_version.
- MODEL_ATTESTED solo con attestazione provider firmata contenente nonce + challenge + request_id.

### Storage
- CanonicalMemory, LinkRegistry, DecisionLedger logicamente distinti, stesso motore transazionale per atomicità CAS.
- LINK-ONLY → LinkRegistry. Mai CanonicalMemory.
- REJECT/DUPLICATE → DecisionLedger only.
- Checkpoint firmati fuori dominio DB.

### Lifecycle
- REVOCATION con effective_from. Storia immutabile, giudizio rivalutabile.
- SUPERSEDES, MARKS_AT_RISK come decisioni derivate.

## 9. STATO DEL DOCUMENTO

```
R3-PEER/1.1c
Status: PROPOSAL
Next: produce due implementazioni indipendenti, test su 1.000 eventi misti
Soglia: disaccordo < 2% su decisioni binarie
Se > 2%: la specifica è sottospecificata, non le implementazioni
Promozione a CANON solo dopo property test verificato
```
