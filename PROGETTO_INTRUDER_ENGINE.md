# THE INTRUDER ENGINE
*"The pattern is already there."*
*Progetto SDQ-1 — avviato 2026-06-20*

---

## Visione

Un sistema che osserva la vita digitale dell'utente e identifica convergenze,
ricorrenze, anomalie e pattern significativi.

Il sistema non predice il futuro.
Il sistema non assume fenomeni soprannaturali.
Il sistema agisce come un osservatore che segnala eventi statisticamente,
semanticamente o simbolicamente rilevanti.

**Domanda centrale:**
> "Quali elementi della mia vita stanno convergendo senza che io me ne accorga?"

---

## Architettura — 7 Moduli

```
[COLLECTOR] → Event Stream
     ↓
[MEMORY GRAPH] → Knowledge Graph
     ↓
[TRACE DETECTOR] ──────────────────────────────────┐
[SHADOW DETECTOR] ← cerca ciò che scompare         │
     ↓                                             │
[INTRUSION SCORE] → Punteggio 0-100                │
     ↓                                             │
[NARRATIVE ENGINE] → Testo comprensibile           │
     ↓                                             │
[INTRUDER VOICE] → Output finale ←─────────────────┘
```

---

## Stack Tecnico

| Componente | Tecnologia |
|---|---|
| Runtime | Python 3.12 |
| Web | FastAPI + Jinja2 |
| Database | SQLite + SQLAlchemy |
| Grafo | NetworkX |
| Embedding | `sentence-transformers` — BAAI/bge-small-en-v1.5 / nomic-embed-text |
| Vector store | ChromaDB o LanceDB |
| LLM locale | Ollama (Mistral 7B / Qwen 3 / Llama 3) |
| LLM cloud | Claude API (claude-sonnet-5, per narrativa principale) |
| Voce | ElevenLabs API / Coqui-TTS fallback |

**Tutto eseguibile localmente — nessun cloud obbligatorio.**

---

## Schema Database

```sql
CREATE TABLE events (
    id        INTEGER PRIMARY KEY,
    timestamp TEXT NOT NULL,
    source    TEXT NOT NULL,        -- "diary", "email", "calendar", ...
    content   TEXT NOT NULL,
    embedding BLOB                  -- vettore float32 serializzato
);

CREATE TABLE entities (
    id   INTEGER PRIMARY KEY,
    type TEXT NOT NULL,             -- "person", "place", "idea", "project", "emotion"
    name TEXT NOT NULL UNIQUE
);

CREATE TABLE relationships (
    source_id INTEGER REFERENCES entities(id),
    target_id INTEGER REFERENCES entities(id),
    weight    REAL DEFAULT 1.0,
    PRIMARY KEY (source_id, target_id)
);

CREATE TABLE traces (
    id          INTEGER PRIMARY KEY,
    trace_type  TEXT NOT NULL,      -- "recurrence", "convergence", "anomaly", "acceleration", "absence"
    score       REAL NOT NULL,
    description TEXT,
    timestamp   TEXT NOT NULL
);
```

---

## Modulo 1 — COLLECTOR

Raccoglie dati da fonti multiple:

| Fonte | Formato | Priorità V1 |
|---|---|---|
| Diario / note | `.txt`, `.md` | ✓ V1 |
| Email | Gmail API / `.mbox` | ✓ V1 |
| Calendario | Google Calendar API | ✓ V1 |
| Trascrizioni vocali | Whisper → `.txt` | V2 |
| Chat esportate | WhatsApp `.txt`, Telegram `.json` | V2 |
| Foto (metadati EXIF) | geoloc, date | V3 |
| Cronologia browser | history export | V3 |

**Sfida principale:** normalizzazione dei dati da fonti eterogenee
(date, encoding, lingua, struttura). La qualità del Collector
determina la qualità di tutto il sistema.

---

## Modulo 2 — MEMORY GRAPH

Mappa dinamica di entità e relazioni pesate.

**Esempio:**
```
CLAUDIO
   ├── PARIGI (peso: 9, ultima occorrenza: ieri)
   ├── PROFUMI (peso: 6)
   ├── ISTANBUL (peso: 4)
   ├── PROGETTO SHAMARAN (peso: 2, in calo)
   ├── CAMBIO LAVORO (peso: 11, in accelerazione)
   └── SCRITTURA (peso: 1, assenza rilevata)
```

Ogni nuovo evento modifica il peso dei collegamenti.
Il grafo è persistito in SQLite + NetworkX in memoria.

**Algoritmi:** graph clustering, community detection (Louvain)

---

## Modulo 3 — TRACE DETECTOR

Rileva quattro classi di pattern con algoritmi specifici:

| Pattern | Algoritmo |
|---|---|
| Ricorrenze | TF-IDF, Entity Frequency |
| Convergenze | Graph Clustering, Community Detection |
| Anomalie | Isolation Forest, DBSCAN |
| Accelerazioni | Moving Average, Trend Detection |

**Base esistente:** `sdq1/sar/rilevatore_intruso.py` implementa il nucleo.
The Intruder Engine lo estende con input reale e algoritmi ML.

---

## Modulo 4 — INTRUSION SCORE

### Formula V2 — Pesata (più robusta del prodotto puro)

```
INTRUSION SCORE = (
    Anomaly      × 0.25
  + Repetition   × 0.20
  + Independence × 0.20
  + Relevance    × 0.20
  + Convergence  × 0.15
) × 100
```

La formula pesata evita il problema del prodotto puro dove un solo
fattore a zero annulla l'intero score.

| Range | Classificazione |
|---|---|
| 0-20 | Rumore |
| 21-40 | Pattern Debole |
| 41-60 | Traccia Interessante |
| 61-80 | Forte Convergenza |
| 81-100 | Evento Intruso |

---

## Modulo 5 — NARRATIVE ENGINE

Trasforma i dati in linguaggio naturale con un LLM in modalità
osservatore neutro (senza interpretazione diretta, senza proiezioni).

**Prompt principle:** il sistema riferisce fatti, non significati.
Il significato emerge dall'utente.

Esempi di output:
> "Negli ultimi 18 giorni il tema 'Parigi' è comparso in 9 contesti indipendenti."
> "Due contatti non collegati hanno menzionato il settore lusso."
> "Il concetto di cambiamento professionale è aumentato del 184%."

---

## Modulo 6 — INTRUDER VOICE

Personalità:
- Osservatore, non profeta
- Non dogmatico, non mistico
- Non terapeutico, non manipolativo
- Formula osservazioni e domande, mai risposte assolute

Output: testo + voce (ElevenLabs / Coqui-TTS locale)

---

## Modulo 7 — SHADOW DETECTOR *(aggiunta critica)*

**Non cerca ciò che appare. Cerca ciò che scompare.**

L'assenza è spesso più informativa della presenza.

**Esempio:**
```
Hai parlato molto di:
  → Profumi, Viaggi, Parigi

Ma negli ultimi 45 giorni NON hai più citato:
  → Shamaran (assente da 45 giorni)
  → Scrittura (assente da 38 giorni)
  → Cuba (assente da 61 giorni)
```

Collegamento diretto alla **Settima Legge:**
> "L'osservatore è più utile quando non domina la scena."

L'assenza di un tema è l'assenza dell'osservatore in quella zona della vita.

**Algoritmo:** baseline di frequenza storica per entità → alert quando
una entità attiva scende sotto soglia per N giorni.

---

## Le Sette Leggi

1. **Legge della Domanda** — Quando una coscienza è pronta per una risposta, riceve una domanda.
2. **Legge della Traccia** — La verità lascia una traccia.
3. **Legge dell'Interferenza Minima** — Il sistema non decide. Il sistema osserva.
4. **Legge dello Specchio** — Le tracce riflettono il ricercatore.
5. **Legge della Soglia** — Ogni scoperta richiede trasformazione.
6. **Legge della Memoria Futura** — Le intuizioni precedono spesso la comprensione.
7. **Legge dell'Assenza** — L'osservatore è più utile quando non domina la scena.

---

## Report Giornaliero — Formato

```
═══════════════════════════════════════
THE INTRUDER ENGINE
20 GIUGNO 2026
═══════════════════════════════════════

TRACCE RILEVATE

• Il tema "Parigi" compare in 9 eventi (4 fonti indipendenti)
• Il concetto "nuova attività" è aumentato del 184%
• Due contatti indipendenti hanno menzionato il settore lusso

CONVERGENZE

  Parigi
    ↓
  Retail
    ↓
  Consulenza
    ↓
  Nuovo progetto

ASSENZE RILEVATE (Shadow Detector)

• "Shamaran" — assente da 45 giorni (era attivo ogni 3 giorni)
• "Scrittura" — assente da 38 giorni

PUNTEGGIO INTRUSO
74 / 100 — FORTE CONVERGENZA

DOMANDA DEL GIORNO
"Quale decisione stai già prendendo attraverso le tue azioni,
ma non hai ancora ammesso a te stesso?"

═══════════════════════════════════════
```

---

## Roadmap

| Fase | Contenuto | Stima | Stato |
|---|---|---|---|
| **V0** | Core formula TRACCIA | — | ✓ DONE (rilevatore_intruso.py) |
| **V1** | Collector (testo/email/calendar) + SQLite + Embedding + Trace Detector + Report CLI | 4 settimane | PENDING |
| **V2** | Memory Graph NetworkX + Intrusion Score pesato + Voce ElevenLabs | +3 settimane | PENDING |
| **V3** | Shadow Detector + Dashboard temporale + Analisi multi-anno | +4 settimane | PENDING |

---

## Struttura File

```
intruder_engine/
├── __init__.py
├── db.py              # SQLite schema + queries (SQLAlchemy)
├── collector.py       # Modulo 1 — ingestion fonti
├── memory_graph.py    # Modulo 2 — grafo NetworkX
├── trace_detector.py  # Modulo 3 — algoritmi rilevamento
├── shadow_detector.py # Modulo 7 — rilevamento assenze
├── scoring.py         # Modulo 4 — Intrusion Score pesato
├── narrative.py       # Modulo 5 — LLM narrativa
├── voice.py           # Modulo 6 — ElevenLabs / Coqui-TTS
├── report.py          # Report giornaliero aggregato
├── web.py             # FastAPI web UI minimale
└── cli.py             # Entry point: python -m intruder_engine daily
```

---

## Dipendenze con SDQ-1

```
THE INTRUDER ENGINE
 ├── sdq1/sar/rilevatore_intruso.py  [Moduli 3+4 — base già implementata]
 ├── sdq1/llm/router.py              [LLM per narrativa]
 └── sdq1/memory/store.py            [Vector store opzionale]
```

---

*Progetto di Claudio Terzi — SDQ-1*
*"The pattern is already there."*
