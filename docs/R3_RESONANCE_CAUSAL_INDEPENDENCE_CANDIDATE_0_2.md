# R3∞ — Resonance & Causal Independence

**Status:** CANDIDATE — NON CANONICA  
**Version:** `candidate-0.2+repo-audit`  
**Date:** 2026-09-17  
**Scope:** R³∞ / SDQ-1  
**Candidate algorithm:** `R3-RES-001`  
**Roadmap binding:** R3-011 Evidence Graph, after R3-019 baseline  
**Operational implementation:** not authorized by this document

## 0. Core rule

> **More peers ≠ more independence.**

The correct question is not “how many peers agree?”, but:

> **How many causally independent evidence chains survive provenance verification, P5, P6 and falsification?**

Resonance is not truth and is not activation. It produces a **candidate** that must pass the existing R³∞ verification pipeline.

## 1. Provenance of this specification

This candidate derives from:

- the R³∞ P5/P6 seed;
- Claudio/Raffaello internal review;
- multi-AI review with Perplexity;
- correction of the invalid rule “peer count = independence”;
- direct audit of the current `claudioterzi/Claudio` repository on 2026-09-17.

An external model repeating a correction it has just received is **conceptual convergence**, not independent confirmation.

The unrelated “Chat hot - Apps on Google Play” citation previously attached to this material is explicitly excluded. It provides no provenance for P5, R³∞, Ed25519, `r3/node.py`, H5/H6 or this architecture.

## 2. Identity layers

The system must keep these identifiers distinct:

- `hypothesis_id`: conceptual claim, e.g. `H17`;
- `evidence_id`: one evidence object attached to a claim, e.g. `E17-004`;
- `content_hash`: SHA-256 of the canonical payload.

`content_hash` protects byte-level integrity. It does **not** determine semantic identity.

Therefore:

- same hash ≠ automatically same epistemic evidence;
- different hash ≠ automatically different hypothesis.

## 3. Candidate proposal schema

```text
PROPOSAL
├── schema_version
├── proposal_id
├── hypothesis_id
├── evidence_id
├── content_hash
├── origin_peer_id
├── signer_id
├── root_evidence_ids[]
├── parent_evidence_ids[]
├── causal_ancestors[]
├── path_peers[]
├── acquisition_event_id
├── timestamp
├── sequence
├── nonce
└── signature
```

`path_peers[]` is useful for network audit. It does **not** define epistemic independence.

`signer_id` proves who signed a representation. It does **not** prove that the signer is independent from other signers.

## 4. Declared roots vs verified roots

A `root_evidence_id` declaration is not sufficient.

```text
ROOT_EVIDENCE
├── root_id
├── artifact_hash
├── source_type
├── source_locator
├── acquisition_timestamp
├── acquisition_event_id
├── acquisition_agent
├── verification_method
├── controller_domain
├── causal_parent_root_ids[]
├── provenance_signature
└── verification_state
```

Allowed states:

```text
VERIFIED
DECLARED_ONLY
UNKNOWN
REJECTED
```

Fail closed: `DECLARED_ONLY` and `UNKNOWN` may remain in the registry, but they do not increase the count of independent chains until provenance is verified.

## 5. Root genealogy

Different roots are not automatically independent.

```text
          ROOT-X
          /    \
     ROOT-A    ROOT-B
       |          |
      E1         E2
        \        /
             H
```

`ROOT-A != ROOT-B` does **not** imply `INDEPENDENT(A,B)` if both descend from `ROOT-X`.

Independence therefore uses the verified causal closure of evidence roots, not only hashes, URLs, peer IDs or network paths.

## 6. P5 stays separate from resonance

For trace `i`:

```text
TRACE_i = A_i × R_i × I_i × Rel_i × C_i
```

Mandatory property:

```text
I_i = 0  =>  TRACE_i = 0
```

Candidate 0.2 uses conservative independence handling:

- `I_i = 1`: required provenance is VERIFIED and the evidence chain is admissible;
- `I_i = 0`: dependency/echo is demonstrated;
- `I_i = UNKNOWN`: available provenance is insufficient.

For resonance, `UNKNOWN` is not silently promoted to `1`.

## 7. Causal dependency graph

For each evidence object `E`:

```text
CAUSAL_CLOSURE(E) =
  verified_roots(E)
  ∪ verified_root_ancestors(E)
  ∪ relevant_parent_evidence(E)
```

Build graph `G`:

- one node per eligible P5 trace;
- edge between `E_a` and `E_b` if they share a verified root or verified critical causal ancestor;
- policy may also add an edge when a shared acquisition event or other verified dependency proves common origin.

Connected components of `G` are **causal dependency clusters**.

Many peer copies or many keys descending from the same causal family remain one cluster.

## 8. Echo and Sybil resistance

Ed25519 provides signer authentication, not epistemic independence.

SHA-256 provides integrity/content addressing, not truth or independence.

Candidate rules:

1. signatures are never counted as independent sources by themselves;
2. signers with the same causal closure belong to the same dependency cluster;
3. creating N peers or N keys does not multiply weight when lineage is common;
4. unverifiable roots do not create positive independence;
5. aliases, paraphrases and re-encodings should inherit lineage when provenance proves common origin.

## 9. R3-RES-001 — deterministic candidate algorithm

### Input

- `hypothesis_id`;
- P5 traces linked to the hypothesis;
- verified provenance;
- causal dependency graph;
- versioned policy.

### Step 1 — Filter

Exclude from resonance traces with:

- invalid signature/integrity;
- `REJECTED` provenance;
- `UNKNOWN` independence when policy requires VERIFIED;
- `TRACE = 0`.

### Step 2 — Build graph

Construct the causal dependency graph from verified dependencies.

### Step 3 — Components

Compute connected components `C_1 ... C_m`.

Each component is a causal family whose internal evidence is not independent.

### Step 4 — Representative score

For each component:

```text
S_j = max(TRACE_i)  for i ∈ C_j
```

Rationale: repeated dependent copies must not increase the score.

### Step 5 — Resonance score

Across causally distinct clusters:

```text
RESONANCE_SCORE(H) = 1 - ∏_j (1 - clamp(S_j, 0, 1))
```

Properties:

- deterministic;
- bounded to `[0,1]`;
- duplicate evidence inside one cluster does not increase score;
- a genuinely independent new chain may increase score;
- output depends on causal clusters, not raw peer count.

### Step 6 — Policy gate

A resonance may emit `CANDIDATE` only if:

```text
independent_cluster_count >= K_min
AND
RESONANCE_SCORE >= theta
AND
policy_version is known
```

`K_min` and `theta` must be explicit, versioned and calibrated. Candidate 0.2 does not canonize numerical defaults.

If policy values are absent:

```text
RESULT = INSUFFICIENT_POLICY
```

Identifier:

```text
resonance_algorithm = R3-RES-001
algorithm_version = candidate-0.2
```

## 10. Resonance never activates directly

Required pipeline:

```text
OBSERVATION
↓
ROOT EVIDENCE
↓
DERIVED EVIDENCE
↓
P5 TRACE
↓
INDEPENDENCE GRAPH
↓
R3-RES-001
↓
CANDIDATE
↓
VERIFIER
↓
P6 / FALSIFICATION
↓
CAPABILITY QUARANTINE  (if new capability)
↓
SANDBOX
↓
BASELINE A/B
↓
AUDIT
↓
ADOPT / REJECT / INCONCLUSIVE
```

No `RESONANCE_SCORE` may directly modify operational behaviour.

## 11. Adversarial tests

| Test | Scenario | Expected |
|---|---|---|
| T1 | 100 peers repeat same root | one causal cluster |
| T2 | 100 Ed25519 keys derive from same root | one causal cluster |
| T3 | disjoint network paths, common root | dependent |
| T4 | different hashes/paraphrases, same verified lineage | same cluster |
| T5 | different root IDs, common verified ancestor | dependent |
| T6 | false declared roots without proof | `DECLARED_ONLY/UNKNOWN` |
| T7 | truly separate acquisitions with verified provenance | separate clusters |
| T8 | replay same proposal via new path | no new cluster |
| T9 | missing `K_min` or `theta` | `INSUFFICIENT_POLICY` |
| T10 | resonance passes, P6 fails | never `ADOPT` |

## 12. Repository audit — 2026-09-17

### 12.1 `registro_ipotesi.py`

Current main was checked directly.

Recovered current-state facts:

- `Registro.carica()` is called before reseeding H1-H4;
- `Registro.apri()` is non-destructive for existing IDs;
- `carica()` tolerates and preserves extra JSON fields such as `note_convergenza`;
- `valuta()` is pure with respect to state transition;
- explicit mutation is in `applica_valutazione()`;
- current `registro_ipotesi.json` contains H1-H6, including H5 and H6.

Therefore the historical “H5/H6 get eaten on every execution” bug was real in an earlier version, but it is **not observed in that form on current main**.

Current task is regression prevention, not rediscovery.

Suggested permanent regression test:

```text
test_hypothesis_registry_preserves_existing_entries()
```

with a fixture containing H1, H2, H5 and H6 and an assertion equivalent to:

```text
before_ids ⊆ after_ids
```

except explicit audited tombstones.

### 12.2 `r3/node.py`

Current R3 node is still an MVP content-addressed document store:

- document ID = SHA-256;
- local Ed25519 signatures via PyNaCl;
- SQLite document metadata and audit log;
- upload/download/info/sync endpoints;
- no `hypothesis_id`, `evidence_id`, root lineage or causal ancestry schema.

Critical finding:

`sync_receive()` receives file bytes, computes the hash and signs the received content again with the **local node key**. Remote origin signature/identity is not propagated as epistemic provenance.

Therefore the existing `signature` field must **not** be interpreted as original `signer_id` for R3-RES-001.

### 12.3 `r3/sync.py`

Recovered behaviour:

- explicit peer URLs via `R3_PEERS`;
- synchronization by content-hash set difference;
- pulled bytes are checked against the expected SHA-256/document ID;
- local disk integrity is checked against DB SHA-256;
- causal provenance/origin-signature propagation is not implemented.

So current R3 has **content integrity**, not yet **epistemic provenance**.

## 13. Roadmap binding

Current roadmap already contains:

- `R3-011 Evidence Graph` — DEVELOPMENT, integrity;
- `R3-019 Longitudinal capability benchmark` — DEVELOPMENT, reproducibility;
- `R3-020 Self-improvement safety gate` — VERIFIED.

The recorded operating order places R3-019 before R3-011.

Therefore this candidate is input to **R3-011**, but it must not bypass the current `R3-019-baseline-execution` next action.

## 14. Promotion gates

Candidate 0.2 cannot become canon until all gates pass:

- **G0 Schema:** repository compatibility and migration strategy verified;
- **G1 Registry regression:** H5/H6 preservation test exists and passes;
- **G2 Provenance:** verified roots and causal ancestry have an auditable procedure;
- **G3 Independence:** adversarial T1-T8 pass;
- **G4 Resonance:** R3-RES-001 is benchmarked against alternatives;
- **G5 Policy:** `K_min` and `theta` are calibrated and versioned;
- **G6 P6:** resonance cannot bypass falsification;
- **G7 Reversibility:** rollback and audit are verified.

Only then may status move from `CANDIDATE` to `PROPOSED-CANON`.

Promotion to `CANON` requires an explicit recorded project decision.

## 15. Formal states

```text
NO_SIGNAL
INSUFFICIENT_PROVENANCE
INSUFFICIENT_POLICY
DEPENDENT_ECHO
CANDIDATE
REJECT
INCONCLUSIVE
ADOPT
```

Constraints:

- `UNKNOWN != VERIFIED`;
- `CANDIDATE != ADOPT`;
- `RESONANCE_SCORE != truth`;
- valid signature != independence;
- peer majority != confirmation.

## 16. Closing rule

```text
CONVERGENCE WITHOUT INDEPENDENCE = ECHO
INDEPENDENCE WITHOUT VERIFICATION = UNKNOWN
RESONANCE WITHOUT P6 = INCOMPLETE CANDIDATE
ADOPTION WITHOUT BASELINE = NOT ALLOWED
```

This file is a candidate specification and audit record, not proof that the described resonance mechanism is implemented or superior.
