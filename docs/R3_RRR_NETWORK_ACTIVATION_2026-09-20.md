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
   `r3-rrr-event/1` con protocollo, azione, scope, counter, timestamp, nonce e
   issuer.
2. **Firma Ed25519 del controller.** La chiave privata resta sul controller;
   ogni nodo conserva soltanto `R3_CONTROL_VERIFY_KEY_HEX`.
3. **Replay / downgrade gate.** Un nodo accetta soltanto un counter firmato più
   recente del proprio. Lo stesso evento è idempotente; stesso counter con
   event_id diverso è conflitto e non viene auto-risolto.
4. **Propagazione peer-to-peer.** `r3/sync.py` confronta anche lo stato RRR e
   inoltra l'evento più recente. Il nodo ricevente ricontrolla sempre la firma.
5. **Eredità dei nuovi nodi.** Un nodo senza evento riceve durante il normale sync
   l'ultimo evento firmato posseduto da un peer. La policy dichiara
   `required_on_join=true`.
6. **Policy leggibile dalle integrazioni.** `GET /protocol/rrr/policy` espone il
   contratto macchina: FATTO/INTERPRETAZIONE/IPOTESI, P5, P6, falsificazione,
   risonanza=CANDIDATE, divergenza, rischio e output contract.
7. **Trigger SDQ-1.** Il testo esatto `ROSSO ROSSO ROSSO` o
   `attiva rosso rosso rosso` viene intercettato dalla CLI SDQ-1 e tradotto in
   `r3.rrr_control activate`, invece di essere trattato come normale prompt.

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

### Stato locale

`GET /protocol/rrr/status`

Richiede Bearer token R3 e riporta:
- active;
- controller_configured;
- counter;
- event_id;
- ultimo evento firmato.

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
R3_CONTROL_VERIFY_KEY_HEX      # sui nodi
R3_CONTROL_ISSUER              # default Claudio Terzi
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

**P6.** event_id, firma, counter, issuer, timestamp, nonce, source_node e audit
locale rendono ricostruibile la propagazione.

## Gate di promozione

Il candidato non va dichiarato `NETWORK VERIFIED` finché non passano almeno:

1. unit/contract test firma valida, tamper, replay, downgrade e conflitto;
2. due processi locali: A riceve evento → sync → B eredita stesso event_id;
3. B offline durante activation → B torna online → eredita l'evento;
4. evento più vecchio reiniettato → 409 / nessun downgrade;
5. stesso counter + event_id differente → conflitto, nessuna scelta automatica;
6. test remoto su servizi distinti con log e hash/event_id;
7. per ogni nodo AI: probe comportamentale che dimostri l'applicazione P5/P6,
   non soltanto la ricezione dell'evento.

Fino a quel momento lo stato corretto è:

**SIGNED RRR NETWORK CONTROL CANDIDATE / LIVE PROPAGATION PENDING**

— C.Terzi
