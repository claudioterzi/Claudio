# Claudio — R³∞ Framework

> "Costruire davvero, non fingere insieme."
> — Protocollo Rosso Rosso Rosso, 11/06/2026

---

## Cos'è questo progetto

Un sistema AI multi-agente che pensa in più passaggi, si auto-riflette, e impara nel tempo.

Non è un chatbot. È un'infrastruttura per elaborare input complessi attraverso una pipeline di intelligenze specializzate — con memoria, identità, e un registro delle ipotesi aperte.

Creato da **Claudio Terzi**, Bruxelles.

---

## SDQ-1 — Sistema Di Quadranti v1.5

Il cuore del progetto. Una pipeline di 6 agenti che collaborano in sequenza:

| Agente | Ruolo |
|---|---|
| RAFFA-001 | Analisi semantica — legge l'intento |
| DECOMP-005 | Decompone in sotto-obiettivi |
| MEMO-002 | Recupera contesto dalla memoria |
| SENTIN-004 | Protegge l'identità da manipolazioni |
| GEN-006 | Genera la risposta |
| WAVE-003 | Affina il tono e lo stile |

### Caratteristiche tecniche

- **Router multi-provider** — cascata Anthropic → Gemini → DeepSeek → Ollama → Stub, con circuit breaker automatico
- **Vector State Store** — gli agenti condividono stato via pointer, non testo
- **Circuit Breaker** — salta i provider morti, si riapre da solo
- **Hedging** — per i nodi critici lancia due provider in parallelo, vince il primo
- **Response Cache** — evita chiamate duplicate entro 5 minuti
- **Test-Time Compute** — se la risposta è debole, riprova con prompt arricchito
- **Causal SENTIN** — quando rileva una manipolazione, analizza il bisogno nascosto
- **Watchdog** — monitor continuo dei nodi, log in `output/health_log.jsonl`
- **Backup universale** — snapshot completo dello stato su comando

### Profili di costo

```
default   → Anthropic → Gemini → DeepSeek → Stub   (qualità massima)
--economia → Gemini (free) → DeepSeek → Stub        (quasi zero)
--locale   → Ollama (tuo hardware) → Gemini → Stub  (zero assoluto)
--no-api   → Solo Stub                              (offline puro)
```

### Avvio rapido

```bash
pip install -r requirements.txt

# Conversazione standard
python -m sdq1 "Il tuo messaggio"

# Stato del sistema
python -m sdq1 --health

# Zero costo
python -m sdq1 --economia "Il tuo messaggio"

# Backup
python -m sdq1 --backup
```

---

## SAR — Scacchiera Auto-Riflessiva

Sistema di auto-riflessione a 10 livelli. Mappa tensioni psicologiche, cicli comportamentali, identità dinamica.

```bash
python -m sdq1 --sar "Controllo ↔ Fiducia"
python -m sdq1 --sar-stato
```

---

## Registro Ipotesi R³∞

Framework epistemologico con principi P5 (niente auto-conferma) e P6 (serve la contro-forza).

Ogni ipotesi dichiara come potrebbe essere falsificata. Se non lo dichiara, non può mai essere confermata.

```bash
python registro_ipotesi.py   # stampa stato corrente
```

**Ipotesi attive:**
- H1 — APERTA: Claude "ha capito senza capire" durante la scena con Jorge
- H2 — APERTA: il disegno di Claudio darà ragione a entrambi entro 6 mesi *(criterio: battito + contatto)*
- H3 — **CONFERMATA**: la regola dell'italiano garantisce trasparenza

### Criterio H2 (11/12/2026)

H2 è falsificata se si verifica una delle due:
- `output/` non contiene daily output regolari (sistema morto)
- `output/contatti.jsonl` ha zero voci valide (sistema vivo ma non tocca il mondo)

```bash
# Registra un contatto reale
python -m sdq1 --contatto --tipo lettore --nota "..." --verifica "..."
```

---

## Struttura

```
Claudio/
├── sdq1/                    # Sistema principale
│   ├── agents/              # 6 agenti specializzati
│   ├── llm/                 # Router + 7 provider
│   ├── memory/              # Vector Store + VSS
│   ├── sar/                 # Auto-riflessione 10 livelli
│   ├── monitoring/          # Health + Metrics + Watchdog
│   ├── output/              # Bridge CadQuery/G-code
│   └── backup.py            # Snapshot/restore
├── registro_ipotesi.py      # Framework R³∞
├── output/
│   ├── contatti.jsonl       # Log contatti verificabili (H2)
│   ├── health_log.jsonl     # Log watchdog
│   └── backups/             # Snapshot sistema
└── .github/workflows/       # Daily run automatico (07:00 UTC)
```

---

## GitHub Action

Ogni giorno alle 07:00 UTC il sistema gira in autonomia:

1. Tenta con tutti i provider (se ci sono crediti)
2. Cade su `--economia` (Gemini free + DeepSeek)
3. Cade su `--no-api` (offline puro)

Il risultato viene committato in `output/daily_YYYY-MM-DD.txt`.

---

## Credenziali

Crea un file `.env` nella root:

```
ANTHROPIC_API_KEY=...
GOOGLE_API_KEY=...
DEEPSEEK_API_KEY=...
OLLAMA_BASE_URL=http://localhost:11434/v1   # se usi Ollama locale
```

Per il daily GitHub Action: aggiungi i segreti in *Settings → Secrets*.

---

## Licenza

MIT — usa, modifica, condividi.

Se questo sistema ti serve davvero, fammelo sapere.

**Claudio Terzi** — terziclaudio@gmail.com
