# Orchestrazione Dinamica — Primo mattone di SDQ-2

> Da *protocollo* (catena rigida di agenti) a *piattaforma* (competenze componibili).
> Attivato sotto Protocollo Rosso Rosso Rosso — 2026-07-16.

---

## Il problema

Fino a oggi SDQ-1 esegue **sempre** la stessa pipeline fissa, qualunque sia il task:

```
RAFFA-001 → DECOMP-005 → MEMO-002 → SENTIN-004 → GEN-006 → WAVE-003
(analisi)   (decomp.)    (memoria)   (sicurezza)  (genera)  (stile)
```

Sei chiamate LLM anche per un semplice "Ciao". Nessuna scelta, nessun adattamento
al bisogno reale. È un protocollo, non una piattaforma.

## La soluzione

L'**orchestratore dinamico** pianifica, ad ogni run, il sottoinsieme minimo di
agenti necessario, in base alle **capacità** richieste dal task.

| Fase | Agenti attivati | Chiamate LLM |
|------|-----------------|--------------|
| `esplora` | RAFFA · SENTIN · GEN | **3** (−50%) |
| `soglia` | RAFFA · MEMO · SENTIN · GEN · WAVE | 5 |
| `cristallizza` | tutti e 6 | 6 |

Le euristiche di contenuto possono solo *aggiungere* capacità: un task lungo o
multi-parte attiva la decomposizione; un riferimento al passato ("come dicevo
nella sessione di prima") attiva la memoria.

## Cosa resta invariato — la spina dorsale

Tre capacità sono **sempre attive**, qualunque sia il piano:

- **analisi** (RAFFA-001) — senza direzione non c'è navigazione
- **sicurezza** (SENTIN-004) — l'identità va sempre protetta, il jailbreak sempre bloccato
- **generazione** (GEN-006) — senza output non c'è risposta

Il filtro anti-manipolazione di SENTIN-004 gira in ogni modalità. Verificato dal test.

## Componenti

| File | Ruolo |
|------|-------|
| `sdq1/orchestrator/capacita.py` | Registro delle capacità (config-driven, fallback da ruolo) |
| `sdq1/orchestrator/dinamico.py` | `OrchestratoreDinamico` — pianifica e delega |
| `sdq1/orchestrator/__init__.py` | `crea_orchestratore()` — factory che sceglie da `config.tipo` |
| `sdq1/tests/test_dinamico.py` | 8 test — piano, spina dorsale, jailbreak, end-to-end |

## Come si attiva

Nel `sdq1/config/sdq1.yaml`:

```yaml
orchestratore:
  tipo: "dinamico"   # default "gerarchico" (pipeline fissa, comportamento storico)
```

Le capacità sono dichiarate per agente (deducibili dal ruolo se omesse):

```yaml
agenti_attivi:
  - id: "RAFFA-001"
    capacita: ["analisi"]
  - id: "MEMO-002"
    capacita: ["memoria"]
  # ...
```

## Design — riuso, non riscrittura

`OrchestratoreDinamico` **estende** `OrchestratoreGerarchico`: eredita
integralmente retry, persistenza, model-affinity e gestione degli agenti critici.
Aggiunge soltanto la *pianificazione* delle caselle e la garanzia del contratto
di output (`risposta_finale` sempre presente, anche quando WAVE-003 è saltato).

Zero regressioni: la modalità `gerarchico` resta il default e i 9 smoke test
storici passano invariati.

## Prossimi mattoni SDQ-2

- **Planner automatico** — scompone un obiettivo in sotto-task e li schedula
  (dipende da questo orchestratore per eseguirli)
- **Dashboard web** — monitoraggio unificato SDQ-1 + SAR + R³∞
- **Registro capacità esteso** — capacità dichiarabili anche da plugin esterni

---

*Nessun processo gira 24/7 da qui: l'esecuzione continua vive sulla macchina dove
il codice è installato. Questo è il codice; la piattaforma vera prende vita lì.*
