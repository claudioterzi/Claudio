# R³∞ — Kit di Distribuzione

Testi pronti per ogni piattaforma. Copia, incolla, pubblica.

---

## 🐦 Thread X/Twitter (8 tweet)

**Tweet 1 — hook**
```
Ogni documento che crei vive in un posto solo.

Un disco che muore, un'azienda che chiude, una decisione politica —
e sparisce per sempre.

Ho costruito R³∞: il sistema minimo per garantire che non succeda.
🧵
```

**Tweet 2 — problema**
```
Il problema non è il backup.

Il problema è la verifica.

Come sai che la tua copia è integra?
Come sai che non è stata corrotta silenziosamente nel tempo?

R³∞ lo sa. Ogni ora. Automaticamente.
```

**Tweet 3 — come funziona**
```
R³∞: 3 nodi indipendenti, sync bidirezionale ogni 5 minuti.

Ogni documento ha ID = SHA-256 del suo contenuto.
Non puoi avere un documento con quell'ID che non sia esattamente quel contenuto.

La verifica dell'integrità è implicita nel sistema stesso.
```

**Tweet 4 — tech**
```
Stack:
· Python + FastAPI
· SQLite (zero dipendenze esterne)
· Ed25519 (firma di ogni documento)
· Docker (opzionale)

Un singolo file: node.py
Un secondo file: sync.py

Niente di più.
```

**Tweet 5 — avvio**
```
3 nodi in produzione in 60 secondi:

git clone github.com/claudioterzi/Claudio
docker compose -f r3/docker-compose.yml up -d

Upload:
curl -X POST http://localhost:8001/documents \
  -H "Authorization: Bearer token" \
  -F "file=@documento.txt"
```

**Tweet 6 — filosofia**
```
R³∞ non include blockchain, P2P, GUI, steganografia, token.

Perché?

La complessità senza fondamenta è fragilità mascherata da sofisticazione.

Prima il cuore funziona. Poi il corpo.
```

**Tweet 7 — use case**
```
Per chi è utile:

· Giornalisti in paesi a rischio
· Ricercatori con documenti critici
· Chiunque voglia che il proprio lavoro sopravviva

"La conoscenza che sopravvive a chi la crea è l'unica vera conoscenza."
```

**Tweet 8 — call to action**
```
R³∞ è open source, licenza libera.

→ github.com/claudioterzi/Claudio (branch: claude/rosso-rosso-rosso-ure5A)
→ Cartella r3/

Prova. Forka. Migliora.

La conoscenza appartiene a tutti. 🔴
```

---

## 💼 LinkedIn (post lungo)

```
Ho costruito qualcosa di piccolo che risponde a una domanda grande.

La domanda: qual è il sistema MINIMO per garantire che un documento sopravviva?

Non sopravviva "di solito". Sopravviva anche quando:
- Un server muore
- Un'azienda fallisce
- Una giurisdizione prende una decisione sbagliata
- Un disco si corrompe silenziosamente nel tempo

La risposta che ho trovato si chiama R³∞.

---

COME FUNZIONA

Tre nodi indipendenti (possono essere su tre macchine diverse, in tre paesi diversi).
Ogni documento ha ID = SHA-256 del suo contenuto.
Sync bidirezionale automatico ogni 5 minuti.
Verifica dell'integrità ogni ora: ricalcola SHA-256 di ogni file, confronta col DB.
Se trova una discrepanza: ripristino automatico dal nodo più vicino integro.

---

COSA NON C'È (deliberatamente)

No blockchain. No token. No GUI. No cloud vendor. No single point of failure.

La complessità aggiunta prima che il cuore funzioni è solo fragilità mascherata.

---

STACK

Python 3.10+ · FastAPI · SQLite · Ed25519 (PyNaCl) · Docker

Due file: node.py (il nodo) e sync.py (lo script di sincronizzazione).
Zero dipendenze esterne per il core.

---

AVVIO IN 60 SECONDI

git clone github.com/claudioterzi/Claudio
docker compose -f r3/docker-compose.yml up -d

Tre nodi attivi. Pronti per l'uso.

---

È open source. Licenza libera (R³∞ Knowledge Resilience License v1.0):
usa, forka, deploya, migliora — mantieni la ridondanza a 3 nodi.

→ github.com/claudioterzi/Claudio

"La conoscenza che sopravvive a chi la crea è l'unica vera conoscenza."

#OpenSource #Python #KnowledgeManagement #Resilienza #DocumentManagement
```

---

## 🟠 Hacker News — Show HN

**Titolo:**
```
Show HN: R³∞ – Minimal 3-node document redundancy with SHA-256 content addressing
```

**Testo:**
```
R³∞ is the smallest system I could build that guarantees a document survives
the loss of any single node, with automatic integrity verification and recovery.

Core design decisions:

- Document ID = SHA-256(content). Integrity verification is implicit — you
  can't have an ID mismatch without knowing something changed.
- Each node signs documents with a persistent Ed25519 key (PyNaCl).
- Sync is a simple pull/push delta: GET /sync/hashes from peer, compare,
  transfer what's missing in either direction.
- Integrity check runs hourly: recomputes SHA-256 of every file, triggers
  peer pull on mismatch.
- SQLite + filesystem. Zero external dependencies for the core.

The system is two files: node.py (FastAPI REST node) and sync.py
(bidirectional sync script, run as cron or --loop).

Stack: Python 3.10+, FastAPI, SQLite, PyNaCl, Docker (optional).

Three nodes in 60 seconds:
  docker compose -f r3/docker-compose.yml up -d

Deliberately excluded: blockchain, P2P mesh, GUI, steganography,
auto-deploy to cloud providers. Complexity before the core works is
just fragility dressed as sophistication.

MVP success criteria:
1. Upload to A → present on B and Archive within 10 minutes
2. After 7 days, all docs have valid hashes on all nodes
3. Kill A → B becomes effective primary within 15 minutes
4. A offline 1h, restarted → re-syncs without data loss
5. File corrupted on A → detected and restored from B within 1 hour

GitHub: github.com/claudioterzi/Claudio (r3/ directory)

Happy to discuss the design decisions — especially around sync conflict
resolution (currently last-write-wins with audit log) and the tradeoffs
of content-addressing vs. mutable document IDs.
```

---

## 📱 Reddit — r/selfhosted, r/opensource

**Titolo:**
```
[Project] R³∞ – 3-node document redundancy in ~500 lines of Python. SHA-256 content-addressed, Ed25519-signed, automatic repair.
```

**Testo:**
```
Built a minimal document redundancy system after getting tired of "it's backed up"
meaning "there's one other copy somewhere I haven't checked in months."

R³∞ runs three independent nodes. Every document gets ID = SHA-256(content).
Hourly integrity checks recompute hashes and trigger auto-repair from peers.

Two files: node.py (FastAPI node) + sync.py (bidirectional sync script).
SQLite + filesystem. No external dependencies for the core.

Docker quickstart:
  docker compose -f r3/docker-compose.yml up -d
  # → 3 nodes on ports 8001, 8002, 8003

Open source. Looking for feedback on:
- Sync conflict resolution strategy (currently last-write-wins)
- Whether content-addressing is the right default or should there be mutable IDs
- Security model (static Bearer token per deployment)

github.com/claudioterzi/Claudio → r3/ directory
```

---

## 📬 Invio email a giornalisti tech / blogger

**Oggetto:**
```
R³∞: sistema open source di ridondanza documentale — 500 righe di Python, 3 nodi, zero dipendenze cloud
```

**Corpo:**
```
Ciao,

ho costruito R³∞, un sistema minimale di ridondanza della conoscenza.
La premessa è semplice: ogni documento critico esiste in un solo posto,
e quel posto può sparire.

R³∞ risponde con tre nodi indipendenti, sync automatico ogni 5 minuti,
e verifica dell'integrità ogni ora con riparazione automatica.

Tecnicità rilevanti:
- ID documento = SHA-256 del contenuto (verifica implicita, deduplicazione gratuita)
- Firma Ed25519 per ogni documento
- SQLite + filesystem: zero dipendenze esterne
- Due file Python (~500 righe): node.py (FastAPI) + sync.py (sync bidirezionale)
- Docker compose per 3 nodi in 60 secondi

Open source, licenza libera.
→ github.com/claudioterzi/Claudio (cartella r3/)

Sono disponibile per una demo o per rispondere a domande tecniche.

Claudio Terzi
terziclaudio@gmail.com
```

---

## 🗓️ Piano di lancio (3 giorni)

| Giorno | Azione |
|--------|--------|
| **Giorno 1** | Push README definitivo su GitHub · Show HN · Thread X |
| **Giorno 2** | Post LinkedIn · Reddit r/selfhosted + r/opensource |
| **Giorno 3** | Email 5 blogger tech/IT · Product Hunt (se vuoi) |
