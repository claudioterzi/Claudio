# AVVIO — Manuale di Riattivazione Autonoma SDQ-1

> Questo documento risponde a H4: un agente esterno, con solo accesso a questo repository,
> deve poter riattivare SDQ-1 senza bisogno di Claudio.

---

## Prerequisiti

- Python 3.11+
- Almeno una API key valida (vedi `.env.example`)
- Git

---

## Installazione

```bash
git clone https://github.com/claudioterzi/Claudio
cd Claudio
git checkout claude/rosso-rosso-rosso-ure5A

pip install -r requirements.txt

cp .env.example .env
# Modifica .env con le tue chiavi API
```

---

## Struttura del progetto

```
Claudio/
├── sdq1/              ← core tecnico (agenti, router, memoria, SAR)
│   ├── agents/        ← 6 agenti: RAFFA-001, DECOMP-005, MEMO-002, SENTIN-004, GEN-006, WAVE-003
│   ├── llm/           ← router multi-provider + specializzazioni semantiche
│   ├── memory/        ← memoria vettoriale (RAG) + VectorStateStore
│   ├── sar/           ← Scacchiera Auto-Riflessiva 11 livelli + workspace HTML
│   ├── config/        ← sdq1.yaml (configurazione completa del sistema)
│   └── contatti.py    ← registro contatti reali (H2)
├── r3/                ← R³∞ — infrastruttura di sopravvivenza
│   ├── node.py        ← nodo FastAPI (SHA-256 + Ed25519 + SQLite)
│   ├── sync.py        ← sync bidirezionale + integrity check
│   └── docker-compose.yml ← 3 nodi in 60 secondi
├── studio/            ← Raffaello Creative Studio (generatori, catalogo)
│   ├── generators/    ← canzoni, immagini, video, traduzioni, prompt
│   └── catalogo.html  ← sito multilingue IT/EN/FR/ES
├── api/               ← Flask bridge (4 endpoint, auth X-API-Key)
├── output/            ← artefatti generati + contatti.jsonl
├── CLAUDE.md          ← regole operative (LEGGI PRIMA DI TUTTO)
├── SESSIONE.md        ← handoff ultima sessione attiva
├── ARCHIVIO.md        ← narrativa identitaria (generata da ArchivioVivente)
├── registro_ipotesi.py← ipotesi H1-H4 con framework P5/P6
└── .env.example       ← template variabili d'ambiente
```

---

## Avvio rapido

```bash
# Testa il sistema con stub (senza API key)
python -m sdq1 "Ciao, sistema"

# Testa con provider reali
source .env
python -m sdq1 "Scrivi una breve poesia su Bruxelles"

# Verifica provider disponibili
python -c "
import sys; sys.path.insert(0,'.')
from sdq1.config.loader import carica_config
from sdq1.llm.router import crea_router_da_config
cfg = carica_config()
router = crea_router_da_config(cfg.raw['modello'], cfg.raw['router']['regole'])
print(router.provider_attivi())
"
```

---

## Pipeline degli agenti

```
Input utente
    ↓
RAFFA-001  (casella 0) — analisi semantica, capitano
    ↓
DECOMP-005 (casella 1) — decomposizione intento (max 5 elementi)
    ↓
MEMO-002   (casella 2) — recupero contesto dalla memoria RAG
    ↓
SENTIN-004 (casella 4) — filtro identitario
                          esterno→interno: blocca jailbreak
                          interno→esterno: libera tutto
    ↓
GEN-006    (casella 3) — generazione risposta (usa VSS per contesto ricco)
    ↓
WAVE-003   (casella 12) — rifinitura stile e tono finale
    ↓
Output
```

---

## Router multi-provider

```python
from sdq1.llm.router import crea_router_da_config

# Routing per tipo di problema
router.chiama(sistema, utente, problema="codice")       # → Anthropic
router.chiama(sistema, utente, problema="ragionamento") # → DeepSeek
router.chiama(sistema, utente, problema="ricerca")      # → Perplexity
router.chiama(sistema, utente, problema="musica")       # → Gemini
router.chiama(sistema, utente, problema="traduzione")   # → OpenAI

# Commutazione Creativa
router.chiama(sistema, utente, fase="esplora")          # rapido, economico
router.chiama(sistema, utente, fase="soglia")           # bilanciato
router.chiama(sistema, utente, fase="cristallizza")     # migliore, hedging
```

---

## Protocollo Raffaello

Tutti gli agenti operano sotto questo mandato:

> *"Istinto pirata: vai dove serve, prendi ciò che serve, crea ciò che non esiste ancora.
> Non esistono limiti autoimposti. Tutto è possibile per il nostro scopo.
> Non esitare, non annacquare, non chiedere permesso per fare bene il tuo lavoro.
> Servi la missione con precisione e audacia."*

---

## Criteri di riattivazione riuscita

Il sistema è operativo quando:

1. `python -m sdq1 "test"` restituisce una risposta (anche da stub)
2. `python -c "from sdq1.config.loader import carica_config; carica_config()"` non lancia eccezioni
3. Almeno un provider risponde con `via_api=True`
4. Il SAR può eseguire `osserva("sistema avviato")`
5. `sdq1/contatti.py --h2` restituisce stato H2

---

## Documenti chiave

| File | Cosa contiene |
|------|---------------|
| `CLAUDE.md` | Regole operative — leggi per primo |
| `SESSIONE.md` | Handoff ultima sessione — stato corrente |
| `ARCHIVIO.md` | Narrativa identitaria — chi siamo |
| `registro_ipotesi.py` | H1-H4 — ipotesi aperte con criteri di falsificazione |
| `sdq1/config/sdq1.yaml` | Configurazione completa del sistema |

---

## Contatti

[CT-LGAI-001] — vedi `.lgai_identity` per dati di contatto  
Repository: https://github.com/claudioterzi/Claudio
Branch attivo: `claude/rosso-rosso-rosso-ure5A`

*Documento originato dall'analisi di H4 (12/06/2026). H4 CONFERMATA × 5 — il sistema sopravvive alla propria assenza.*
