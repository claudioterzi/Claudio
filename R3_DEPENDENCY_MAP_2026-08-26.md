# R³∞ DEPENDENCY MAP — 2026-08-26

## Stato

**FATTO:** mappa strutturale di primo livello costruita sul branch `main` del repository `claudioterzi/Claudio`.

**FATTO:** il repository principale è `claudioterzi/Claudio`, branch `main`. La struttura contiene i livelli di continuità/governance, SDQ-1, R³∞, epistemologia, applicazioni, studio creativo e distribuzione già descritti nell'audit di fondazione.

**FATTO:** l'ultimo commit osservato prima di questa mappa è `7a001486fc9330cb2ac5df063b3d36a001433338` (`R³∞: add persistent work queue and consolidation contract`). Il check GitHub `Vercel` su quel commit risulta `success`.

**LIMITE:** questa è una mappa architetturale verificata per struttura e punti di integrazione principali; non è ancora un grafo completo di ogni import Python del repository. Il completamento dell'import graph richiede un ambiente di esecuzione/checkout del repository.

---

## 1. Grafo sistema → sottosistema

```text
REPOSITORY / MAIN
│
├── CONTINUITÀ / GOVERNANCE
│   ├── MEMORIA_PROGETTO.md
│   ├── COSTELLAZIONE.md
│   ├── CLAUDE.md
│   ├── SESSIONE.md / AVVIO.md / ORIENTAMENTO.md
│   ├── SECURITY.md / security_protocol.json
│   └── R3_WORK_QUEUE.yaml
│
├── SDQ-1
│   └── sdq1/
│       ├── agents/          → agenti e registry
│       ├── llm/             → client, router, provider, specializzazioni
│       ├── memory/          → memoria / VSS
│       ├── orchestrator/    → coordinamento
│       ├── sar/             → auto-riflessione / valutazione
│       ├── persistence/     → persistenza e snapshot
│       ├── monitoring/      → battito / watchdog / diagnostica
│       ├── futures/         → scenari / simulazione
│       ├── voli/            → componenti voli
│       └── tests/           → verifica locale
│
├── R³∞ STORAGE / NETWORK
│   └── r3/
│       ├── node.py          → API nodo, SHA-256, SQLite, Ed25519
│       ├── sync.py          → pull/push tra peer + integrity check
│       ├── docker-compose.yml / Dockerfile
│       └── archivio/        → archivio persistente
│
├── EPISTEMOLOGIA
│   ├── registro_ipotesi.py/json
│   ├── PROGETTO_BENCHMARK.md
│   └── output/
│
├── APPLICAZIONI
│   ├── flight_hunter/       → ricerca voli multi-fonte
│   ├── viaggi/              → pianificazione viaggi
│   ├── custode/             → servizio Custode
│   ├── intruder_engine/     → sicurezza / analisi intrusioni
│   └── lgai_core/           → nucleo LGAI / Raffaello
│
├── STUDIO / PARFUMS
│   └── studio/parfums/
│       ├── generatori
│       ├── cataloghi
│       ├── Organo Terzi
│       └── Valigia-Organo
│
├── TAROCCHI QUANTICI
│   ├── tarocchi/
│   ├── tarocchi_quantici_alpha.json
│   └── tarocchi_web.py
│
└── DISTRIBUZIONE
    ├── api/
    ├── public/
    ├── .github/workflows/
    └── vercel.json
```

---

## 2. Flusso operativo principale

```text
UTENTE
  ↓
INTERFACCE / API
  ├── tarocchi_web.py
  ├── api/
  └── Telegram / Vercel (secondo configurazione documentata)
  ↓
ORCHESTRAZIONE SDQ-1
  ├── router LLM
  ├── agenti specialisti
  ├── planner / orchestrator
  └── policy / guardian
  ↓
MEMORIA + CONOSCENZA
  ├── memory / VSS
  ├── persistence
  ├── MEMORIA_PROGETTO.md
  └── registro_ipotesi
  ↓
VERIFICA
  ├── SAR
  ├── adversarial / contraddittore
  ├── test
  └── benchmark
  ↓
RISULTATO
  ├── output applicativo
  ├── aggiornamento epistemico
  └── eventuale consolidamento documentato
```

---

## 3. R³∞ come infrastruttura di persistenza

`r3/node.py` espone il nodo HTTP e mantiene documenti content-addressed: l'ID è calcolato come SHA-256 del contenuto; usa SQLite per metadati/audit e Ed25519 per la firma dei documenti.

`r3/sync.py` dipende dall'API del nodo (`/sync/hashes`, `/documents/{id}`, `/sync/receive`) e usa HTTPX. Verifica l'hash dei dati ricevuti prima di reinserirli. La sincronizzazione reale tra host distinti rimane **NON VERIFICATA** dalla sola presenza del codice.

**Conseguenza:**

```text
SDQ-1 / applicazioni
        │
        │ integrazione prevista
        ▼
      R³∞
        │
        ├── storage locale verificabile
        └── sync peer-to-peer (implementato nel codice,
            rete reale ancora da testare)
```

---

## 4. Punti di integrazione ad alta priorità

| Punto | Dipende da | Produce / serve | Stato |
|---|---|---|---|
| `sdq1/llm/router.py` | provider + config | selezione modello | IMPLEMENTATO, audit funzionale da completare |
| `sdq1/memory/` | storage / modelli memoria | contesto persistente | IMPLEMENTATO, unificazione da progettare |
| `sdq1/orchestrator/` | agenti + router + memoria | workflow agentico | IMPLEMENTATO, responsabilità da consolidare |
| `sdq1/sar/` | risultati + criteri | auto-valutazione | IMPLEMENTATO, da integrare con Scacchiera |
| `sdq1/tests/` | componenti SDQ-1 | regressioni | PRESENTE, copertura globale da misurare |
| `r3/node.py` | FastAPI + SQLite + PyNaCl | storage R³∞ | IMPLEMENTATO, deploy multi-host non provato |
| `r3/sync.py` | nodi HTTP + token | replica | IMPLEMENTATO, sync reale non provato |
| `benchmark.py` / benchmark | modelli + scenari | metriche | PRESENTE, baseline R³∞ da costruire |
| `.github/workflows/` | GitHub Actions | CI/deploy | PRESENTE; dettaglio run da verificare per ogni workflow |
| `vercel.json` | Vercel | distribuzione web/API | PRESENTE; ultimo check Vercel osservato: success |

---

## 5. Dipendenze e duplicazioni da investigare

### D1 — Memoria
Possibile sovrapposizione fra memoria SDQ-1, `MEMORIA_PROGETTO.md`, persistence, snapshot/backup e futuro R³∞. Non eliminare nessuno store: prima definire ruoli e flussi.

### D2 — Orchestrazione
Router, orchestrator, agent registry, SAR, guardian e componenti autonomi possono condividere responsabilità decisionali. Serve un contratto: **chi decide / chi genera / chi critica / chi verifica / chi agisce**.

### D3 — Backup vs R³∞
`backup.py`, agenti di backup e R³∞ possono produrre ridondanza funzionale. Distinguere backup operativo, replica e archivio content-addressed.

### D4 — Verifica vs benchmark
Test di correttezza, SAR e benchmark misurano proprietà diverse. Non devono essere fusi in un unico indicatore di "intelligenza".

### D5 — Documentazione di realtà
I documenti storici contengono sia architettura implementata sia roadmap/simulazioni. Ogni audit successivo deve mantenere le etichette **FATTO / INFERENZA / IPOTESI / SIMULAZIONE**.

---

## 6. R³∞ reality status

- **FATTO:** repository principale e struttura R³∞ presenti su GitHub.
- **FATTO:** `R3_WORK_QUEUE.yaml` è persistente e indica `R3-002` come prossima azione.
- **FATTO:** `r3/node.py` e `r3/sync.py` esistono e implementano le primitive descritte.
- **FATTO:** l'ultimo commit osservato ha check Vercel `success`.
- **INFERENZA:** il codice R³∞ è progettato per supportare replica content-addressed e firma, ma questo non dimostra un deployment distribuito funzionante.
- **NON VERIFICATO:** due o più nodi R³∞ realmente online e sincronizzati su host distinti.
- **NON VERIFICATO:** integrazione R³∞ come backend effettivo della memoria SDQ-1.
- **NON VERIFICATO:** benchmark end-to-end del sistema R³∞ rispetto a modelli isolati.

---

## 7. Prossimi passi derivati dalla mappa

1. **R3-003:** audit puntuale di SDQ-1: entry point, router, orchestrator, memory, SAR, persistence, monitoring e test.
2. **R3-004:** definire il contratto unificato della memoria senza migrare o cancellare gli store esistenti.
3. **R3-007:** costruire un harness riproducibile per testare routing, memoria, orchestrazione, tool boundaries e sicurezza.
4. **R3-006:** verificare separatamente i nove nodi storici con evidenza osservabile.
5. Solo dopo questi passaggi: Scacchiera meta-riflessiva e benchmark comparativi.

---

## Provenienza

- Repository: `claudioterzi/Claudio`, branch `main`.
- Foundation audit: `R3_FOUNDATION_AUDIT_2026-08-26.md`.
- Work queue: `R3_WORK_QUEUE.yaml`.
- R³∞ design: `PROGETTO_R3.md`, `r3/README.md`, `r3/node.py`, `r3/sync.py`.
- Snapshot di lavoro osservato: commit `7a001486fc9330cb2ac5df063b3d36a001433338`.
