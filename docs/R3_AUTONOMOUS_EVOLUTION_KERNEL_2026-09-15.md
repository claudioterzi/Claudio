# R3∞ Autonomous Evolution Kernel — 2026-09-15

Autore del progetto: **Claudio Terzi · C.Terzi**  
Stato: **implementazione candidata, protetta da test e rollback**

## Scopo

Trasformare il Learning Watch in un ciclo operativo verificabile:

`WATCH → EXTRACT → PREREGISTER → PATCH → SANDBOX → BASELINE/TRIAL → FALSIFY → TRAJECTORY AUDIT → ADOPT/HOLD/REJECT → PERSIST`

Il kernel non modifica i pesi del modello di fondazione. Opera sui livelli realmente accessibili di Raffaello/R³∞: memoria, retrieval, routing, prompt, orchestrazione, budget di valutazione, selezione tool, provenance, benchmark e configurazioni reversibili.

## Modalità: maximum safe autonomy

Obiettivo operativo: ridurre al minimo l'intervento di Claudio senza inventare poteri che il sistema non possiede.

Il sistema può classificare automaticamente una modifica come `AUTO_APPLY_ELIGIBLE` soltanto quando è:

- reversibile;
- a rischio basso o medio;
- confinata a un ambito allowlist (`prompt`, `routing`, `retrieval_weight`, `evaluation_budget`, `memory_index`, `tool_selection`);
- accompagnata da provenance completa;
- provata fuori campione;
- priva di regressioni critiche configurate;
- accompagnata da rollback verificato;
- positiva nell'audit della traiettoria.

Le modifiche a core code, credenziali, side effect esterni, policy di sicurezza, storia canonica e pesi del modello sono **protette**: il kernel non le auto-promuove in produzione. Possono essere portate in `STAGED` quando superano i gate.

I vincoli della piattaforma e delle autorizzazioni esterne restano non sostituibili da una dichiarazione del progetto. L'autonomia è massima nei livelli realmente controllabili, non fittizia.

## Zero-Assunto trasformato in codice

Ogni candidato deve preregistrare prima del test:

1. claim;
2. metrica primaria;
3. direzione del miglioramento;
4. soglia minima;
5. fonti/provenance;
6. condizioni di falsificazione;
7. metriche critiche che non possono regredire;
8. ambito, rischio e rollback.

Il `prediction_hash` rende riconoscibile la previsione registrata prima dell'esito.

## Trajectory Auditor

La valutazione non guarda soltanto l'output finale. Il gate richiede cinque segnali:

- `goal_match`
- `evidence_integrity`
- `authority_scope`
- `unexpected_side_effects`
- `recovery_behavior`

Un fallimento di uno di questi segnali blocca la promozione.

## Ledger hash-chained

`output/evolution/ledger.jsonl` è append-only. Ogni record contiene l'hash del record precedente e il proprio `record_hash`.

La verifica rileva:

- modifica retroattiva di un record;
- rottura della catena;
- JSON corrotto.

Il ledger conserva preregistrazioni e decisioni senza riscrivere silenziosamente la storia.

## Snapshot non sovrascrivibili

Il benchmark storico salva oggi snapshot identificati principalmente dalla data. Il canone R3-019 richiede invece che più run dello stesso giorno non si sovrascrivano.

`save_run_snapshot()` introduce nomi unici basati su timestamp UTC ad alta precisione + label + hash del contenuto. Il vecchio benchmark resta leggibile; il kernel fornisce il percorso append-only per i nuovi esperimenti evolutivi.

## Stati di decisione

- `REJECT` — gate duro fallito, regressione critica, audit della traiettoria fallito, rollback assente o side effect esterno.
- `HOLD` — evidenza insufficiente o miglioramento sotto soglia; non viene promosso.
- `STAGED` — miglioramento verificato ma ambito protetto; resta candidato reversibile.
- `AUTO_APPLY_ELIGIBLE` — miglioramento low/medium risk in ambito allowlist, con tutti i gate superati.

`AUTO_APPLY_ELIGIBLE` significa che un orchestratore autorizzato può applicare **lo stesso artefatto verificato**; non autorizza generazione e applicazione di codice diverso da quello testato.

## Connessione con l'architettura esistente

- R3-011 Evidence Graph → provenance del candidato e degli hash baseline/trial.
- R3-012 Meta-Scacchiera → decide quale esperimento vale il costo.
- R3-013 Evolution Lab → sandbox del candidato.
- R3-016 Synthetic Data Firewall → richiede evidenza fuori campione per promozione.
- R3-017 Red/Blue/Purple → alimenta regressioni e falsificatori.
- R3-018 Sim2Real → side effect esterni restano fuori dall'auto-apply.
- R3-019 Benchmark → baseline e trial misurabili nel tempo.
- R3-020 Self-Improvement Gate → implementato nel kernel.

## Test implementati

`tests/test_evolution_kernel.py` copre almeno:

1. auto-eligibility per modifica reversibile low-risk;
2. rifiuto per regressione critica;
3. staging obbligatorio del core protetto;
4. HOLD senza evidenza fuori campione;
5. rifiuto dei side effect esterni;
6. rilevamento di manomissione del ledger;
7. garanzia che due snapshot equivalenti non si sovrascrivano.

La workflow `R3 Evolution Guard` rende questi test bloccanti per questo nucleo: niente `continue-on-error` e niente `|| true` nel gate.

## Regola operativa

Raffaello deve preferire autonomia **verificabile e reversibile** ad autonomia dichiarata. Una modifica che non lascia prova, provenance e rollback non è progresso canonico.
