# R³∞ — Attivazione di rete del Protocollo Rosso Rosso Rosso

Data: 20/09/2026  
Stato: **CANDIDATE / CODE COMPLETE, LIVE MULTI-NODE TEST PENDING**  
Protocollo: `RRR-JEV/1.0`

## Intento canonico

Il comando umano:

```
ROSSO ROSSO ROSSO
```

deve significare una sola cosa nel perimetro R³∞ autorizzato:

> emettere un evento di controllo firmato che attiva la versione canonica del
> Protocollo Rosso Rosso Rosso sull'intera rete raggiungibile, e permettere ai
> peer di propagare lo stesso evento ai nodi che rientrano online o si aggiungono
> successivamente.

Non è pubblicazione, social distribution o invio a soggetti esterni.

## Proprietà implementate nel candidato

1. **Un solo evento, stessa identità.** Il controller crea un evento canonico
   `r3-rrr-event/1` con protocollo, **policy_sha256**, azione, scope, counter,
   timestamp, nonce e issuer. L'attivazione firma quindi anche l'esatta policy
   canonica, non soltanto il suo nome/versione.
2. **Firma Ed25519 del controller.** La chiave privata resta sul controller;
   ogni nodo conserva soltanto `R3_CONTROL_VERIFY_KEY_HEX`.
3. **Replay / downgrade gate.** Un nodo accetta soltanto un counter firmato più
   recente del proprio. Lo stesso evento è idempotente; stesso counter con
   event_id diverso è conflitto e non viene auto-risolto. Il controller usa un
   counter SQLite persistente e serializzato: un rollback dell'orologio non può
   diminuire il counter emesso.
4. **Propagazione peer-to-peer.** `r3/sync.py` verifica firma, event_id,
   policy hash e coerenza del counter **prima** di usare lo stato di un peer per
   decidere la direzione del relay. Il nodo destinatario ripete comunque la
   verifica: il trasporto non diventa autorità.
5. **Eredità dei nuovi nodi.** Un nodo senza evento riceve durante il normale sync
   l'ultimo evento firmato posseduto da un peer. La policy dichiara
   `required_on_join=true`. Liveness e readiness sono separate: `/health`
   indica che il processo vive; `/ready` resta 503 finché il nodo non ha
   controller configurato e, per default, un'attivazione RRR valida.
6. **Policy leggibile dalle integrazioni.** `GET /protocol/rrr/policy` espone il
   contratto macchina: FATTO/INTERPRETAZIONE/IPOTESI, P5, P6, falsificazione,
   risonanza=CANDIDATE, divergenza, rischio e output contract.
7. **Trigger SDQ-1.** Il testo esatto `ROSSO ROSSO ROSSO` o
   `attiva rosso rosso rosso` viene intercettato dalla CLI SDQ-1 e tradotto in
   `r3.rrr_control activate`, invece di essere trattato come normale prompt.
8. **Commit atomico del controllo.** Controllo d'ordine, inserimento evento e audit
   sono una singola transazione SQLite `BEGIN IMMEDIATE`: writer concorrenti non
   possono far risultare applicato uno stato più vecchio dopo uno più nuovo.
9. **ACK verificato.** Il controller considera valido un ACK soltanto se protocollo,
   event_id, counter e stato active coincidono esattamente con l'evento firmato
   inviato.

## Flusso

```text
Claudio
  │
  │ "ROSSO ROSSO ROSSO"
  ▼
controller RRR (private signing key)
  │
  ├── signed event ──► Node A ──ACK
  ├── signed event ──► Node B ──ACK
  └── signed event ──► Node C ──ACK
                         │
                         └── normal R3 sync relays same signed event
                             to late/offline/new peers
```

Il trasporto non è fonte di autorità. Un peer compromesso non può creare un
nuovo evento valido senza la chiave privata del controller.

## Endpoint

### Policy canonica

`GET /protocol/rrr/policy`

Pubblico per design. Non contiene segreti.

### Readiness

`GET /ready`

Restituisce 200 solo quando il nodo è utilizzabile secondo il gate RRR; altrimenti
503 con le ragioni di quarantena. `GET /health` rimane un puro liveness check.

### Stato locale

`GET /protocol/rrr/status`

Richiede Bearer token R3 e riporta:
- active;
- controller_configured;
- counter;
- event_id;
- ultimo evento firmato;
- policy_sha256 locale;
- trust level della provenienza di relay.

### Applicazione / relay

`POST /protocol/rrr/event`

Richiede Bearer token R3 e verifica la firma Ed25519 del controller prima di
scrivere nel ledger SQLite `protocol_events`.

## Comandi controller

```bash
# generare/leggere la chiave pubblica da installare sui nodi
python r3/rrr_control.py public-key

# attivazione globale sui target configurati
python r3/rrr_control.py activate

# stato dei nodi
python r3/rrr_control.py status

# disattivazione esplicita, se richiesta
python r3/rrr_control.py deactivate
```

Variabili:

```text
R3_API_TOKEN
R3_LOCAL_URL
R3_PEERS
R3_CONTROL_SIGNING_KEY_HEX     # SOLO controller
R3_CONTROL_VERIFY_KEY_HEX      # sui nodi e sul sync che ordina eventi
R3_CONTROL_COUNTER_DB          # stato monotono persistente del controller
R3_CONTROL_ISSUER              # default Claudio Terzi
R3_REQUIRE_RRR_ACTIVE          # default true per /ready
```

La chiave privata di controllo non deve essere copiata nei nodi, nel repository,
in documenti Drive o in output/log.

## Relazione con Jev / TypeSafe

Il servizio `typesafe_sister` ha già un envelope automatico
`RRR-JEV/1.0`. Il control plane qui definito risolve un problema differente:
distribuire **stato e policy canonica di rete**. L'adapter di ciascun nodo AI deve
consumare la policy canonica o una versione equivalente e dichiarare l'ACK solo
dopo averla applicata al proprio percorso di inferenza.

Quindi:

```text
network event ACTIVE ≠ prova che un provider remoto stia davvero applicando RRR
```

Per un nodo AI esterno serve un test comportamentale indipendente.

## P5 / P6

**P5.** Dieci ACK derivati dallo stesso evento dimostrano propagazione, non dieci
conferme indipendenti della correttezza del protocollo.

**P6.** policy_sha256, event_id, firma, counter, issuer, timestamp, nonce e audit
locale rendono ricostruibile la propagazione. `source_node` è esplicitamente
**transport-reported**, protetto dal Bearer transport ma non autenticato come
identità crittografica del peer: non viene mai usato come autorità del controller.

## Gate di promozione

Il candidato non va dichiarato `NETWORK VERIFIED` finché non passano almeno:

1. unit/contract test firma valida, tamper, replay, downgrade e conflitto;
2. due processi locali: A riceve evento → sync → B eredita stesso event_id;
3. B offline durante activation → B torna online → eredita l'evento;
4. evento più vecchio reiniettato → 409 / nessun downgrade;
5. stesso counter + event_id differente → conflitto, nessuna scelta automatica;
6. policy hash alterato → rifiuto;
7. rollback dell'orologio/controller restart → counter comunque monotono;
8. writer concorrenti → stato finale massimo e audit atomico;
9. metadata counter/event_id del peer non firmati → non influenzano il routing;
10. nodo nuovo/non attivato → vivo ma non ready;
11. test remoto su servizi distinti con log e hash/event_id;
12. per ogni nodo AI: probe comportamentale che dimostri l'applicazione P5/P6,
   non soltanto la ricezione dell'evento.

Fino a quel momento lo stato corretto è:

**SIGNED RRR NETWORK CONTROL CANDIDATE / LIVE PROPAGATION PENDING**

— C.Terzi
