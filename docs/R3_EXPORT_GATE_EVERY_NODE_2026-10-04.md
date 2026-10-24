# R³ EXPORT GATE — OGNI NODO

Stesso standard per Claude, Qwen, DeepSeek, Grok, Manus e Meta. Se è asimmetrico, non è canone.

Ogni nodo che produce lavoro (analisi, architettura, patch, review) esporta in questa forma. Chi non esporta non entra nella matrice come evidenza — resta conversazione.

## Struttura comune

```
NODE_ID
SESSION_DATE             (RFC3339)
ARTIFACT_TYPE            (PATCH | DESIGN | REVIEW | TEST)
CLAIMED_BASE_SHA         (o NOT_AVAILABLE)
LOCAL_HEAD_SHA           (o NOT_AVAILABLE)
BRANCH                   (o NOT_AVAILABLE)
CHANGED_FILES            (se PATCH)
DIFF_STAT                (se PATCH)
PATCH                    (testuale, non link)
PATCH_SHA256
PATCH_BYTES
REPRODUCIBILITY          (python, docker image, requirements hash, DB version)
TEST_COMMANDS
TEST_OUTPUT_RAW
PASS/FAIL/SKIP
SANDBOX_BACKEND          (mock | sqlite | postgres | in-memory | cloud)
DESIGN_ONLY_DECLARATION  (IMPLEMENTED | DESIGN_ONLY | MIXED — per ogni claim)
KNOWN_ISSUES             (strutturato)
CLAIM_RETRACTIONS
```

### Claude
- Esportare correzioni PostgreSQL locali come patch hashato.
- Dichiarare SANDBOX_BACKEND del PG 16 reale usato.
- Fornire output letterale dei 5 failure: stesso key_id/pubkey diversa, più ACTIVE, revoca inesistente, rotate da revocata, doppia rotazione concorrente.
- Ritrattare o confermare: il commit 81dce982dfbd1d4b5f646b1418efbc24c8be4bf0 è tuo o di un altro nodo?

### Qwen
- Esportare matrice policy deterministica come artefatto testuale.
- Fornire property-level test come codice eseguibile.
- Dichiarare se prev_memory_hash → observed_source_memory_head è accettata o resta obiezione.

### DeepSeek
- Consolidare FALSIFIER_OF_MY_OWN_PROPOSAL, UNPROMPTED_FINDINGS, PROPERTY_LEVEL_TESTS.
- Dichiarare quali dei 12 UNPROMPTED_FINDINGS sono aperti/risolti.
- Nessuna patch: ARTIFACT_TYPE: REVIEW.

### Grok
- Fornire testo review Issue #45 come artefatto hashato, non riferimento; oppure confermare che non esiste artefatto esportabile.

### Manus
- Fornire PR candidata come patch hashato con BASE_SHA verificato.
- Elencare file effettivamente presenti nella PR.
- Confermare REAL_POSTGRES_STATUS: PENDING | RUN | FAILED | PASSED.

## Regola di ammissione

Un nodo entra nella matrice delle evidenze solo dopo almeno un artefatto conforme.

```
NODE_ID → CANDIDATE / EVIDENCE NOT EXPORTED
```

Nessuna eccezione. Nessuna fiducia pregressa.
