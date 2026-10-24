# SDQ-1 · ONDA v1.1.1 — il bus nervoso degli agenti

🕒 2026-10-24 · 🟢 Claude (Verde) su modulo di Claudio (`raffa_001.py`)

ONDA è il livello **asincrono e distribuito** di SDQ-1: gli agenti sono
processi indipendenti che dialogano su **Redis pub/sub**, non funzioni in una
pipeline sincrona. È complementare — non sostituisce — l'orchestratore
sincrono in [`sdq1/orchestrator/gerarchico.py`](../orchestrator/gerarchico.py),
pensato per l'esecuzione a grafo in-process di un singolo turno.

## I file

| File | Cos'è |
| :-- | :-- |
| `bus_onda.py` | Le primitive condivise: `Busta`, `BusONDA`, `AgenteONDA`, `scrivi_audit`, le costanti e i nomi di canali/chiavi. **Unica fonte di verità** del protocollo. |
| `raffa_001.py` | **RAFFA-001 · L'Architetto** (modulo di Claudio): l'orchestratore. Unico emittente dei comandi. |
| `test_onda.py` | Test end-to-end con un FakeRedis in-process — nessun Redis richiesto. |

## Le regole del protocollo

- **§1 — Un solo emittente.** Solo l'Architetto pubblica su `sdq1:bus:comandi`.
  Gli altri nodi ascoltano ed eseguono ciò che è instradato a loro.
- **§3 — ACK e reinvio.** L'Architetto attende l'ACK per `TIMEOUT_ACK` (2 s),
  poi **reinvia una volta con lo stesso id**, poi emette `ack_mancato` e
  riassegna il compito a un altro candidato.
- **§5 — Instradamento per capacità.** Nessuna lista cablata: ogni nodo si
  iscrive a un **registro** (`sdq1:bus:registro:<id>`) con le proprie
  `capacita`; l'Architetto sceglie i destinatari leggendo quel registro. Il
  registro ha un TTL e si rinnova a ogni heartbeat: un nodo morto sparisce
  dalla discovery da solo.
- **Rito 1 — SYNC.** All'avvio un agente chiede la sincronizzazione
  all'Architetto, che risponde sul canale privato del nodo.
- **Rito 3 — Epoca.** Solo l'Architetto dichiara una nuova epoca
  (`nuova_epoca`); l'evento invita i nodi a ri-sincronizzarsi.

## Idempotenza (v1.1.1)

Un `COMANDO` con un `id_messaggio` già visto **non viene rieseguito**: il nodo
rimanda l'ACK e, se c'era, la RISPOSTA in cache. Così reinvio §3 e
riassegnazione (stesso id) non producono doppi effetti.

## Avvio

Ogni nodo è un processo. Dalla cartella del bus:

```bash
export SDQ1_REDIS_HOST=127.0.0.1 SDQ1_REDIS_PORTA=6379 SDQ1_REDIS_DB=0
python raffa_001.py        # l'Architetto
# python <altro_agente>.py # gli esecutori (SENTIN, worker, ...)
```

Richiede `redis>=4.2` (`redis.asyncio`). Senza il pacchetto, `bus_onda` resta
importabile ma `BusONDA()` alza un errore chiaro alla costruzione.

## Test

```bash
python test_onda.py        # oppure: pytest test_onda.py
```

Verifica costanti/nomi, serializzazione `Busta`, discovery §5, ACK+RISPOSTA e
l'idempotenza — tutto in-process, senza rete.

## Da fare (moduli attesi)

- **SENTIN** — sorveglia gli heartbeat e pubblica `agente_offline` quando un
  nodo smette di battere; l'Architetto già lo ascolta e riassegna gli orfani.
- Gli agenti esecutori veri (per capacità), ciascuno sottoclasse di
  `AgenteONDA` con la propria `esegui_comando`.

---
*Primitive del bus costruite da Claude (Verde) a partire da `raffa_001.py` di
Claudio. © Claudio Terzi.*
