# R3 — Persistenza nodi e prova di restart (Issue #86)

Stato: **APERTO** finché non esistono volumi Railway su `/data` per entrambi i nodi
e due prove di restart remoto PASS per nodo.

## Contratto

- `/health` = solo liveness. Non prova continuità.
- `/ready` = 200 solo se: token configurato, chiave del controller RRR configurata,
  `R3_DATA_DIR` è un mount (volume), RRR attivo. Fallisce chiuso.
- Lo stato da preservare vive tutto sotto `R3_DATA_DIR`:
  `signing.key`, `storage_id`, `r3.db` (documents, audit_log, protocol_events), `docs/`.
- `R3_SIGNING_KEY_HEX` **non** sostituisce la persistenza: fissa l'identità ma non
  conserva `r3.db`, eventi di protocollo e documenti. Il test
  `test_env_signing_key_alone_does_not_pass_restart_proof` lo dimostra.

## Target infrastrutturale (per ciascun nodo)

| Servizio | Volume | `R3_DATA_DIR` |
|---|---|---|
| `r3-external-node-a` | nuovo volume montato su `/data` | `/data` |
| `r3-external-node-v2` | nuovo volume montato su `/data` | `/data` |

Riferimento di forma: `r3-external-property-runner` ha già un volume su `/data`.
Un volume per nodo, mai condiviso: due nodi sullo stesso volume non sono ridondanza.

Nota: i nodi hanno `sleepApplication=true`. Senza volume, ogni risveglio dal sonno
equivale a un restart con perdita di stato. Con il volume il sonno diventa innocuo,
ed è comunque un evento di restart che la prova sotto copre.

Il materiale di verifica del controller RRR (`R3_CONTROL_VERIFY_KEY_HEX`, chiave
pubblica) va impostato tramite il percorso di controllo autorizzato esistente.
Finché manca, `/ready` resta 503 con `rrr_controller_key_not_configured`: è corretto.

## Endpoint di prova

`GET /state/fingerprint` (Bearer) restituisce, senza segreti:
`verify_key`, `storage_id`, `storage_id_created_this_boot`, `process_boot_id`,
ultimo evento RRR (`rrr_event_id`, `rrr_counter`, `rrr_action`),
`protocol_event_count`, `document_hashes`, `document_set_sha256`,
`documents_missing_or_corrupt` (verifica hash su disco), `durable_state_detected`.

`storage_id` è un id casuale scritto una sola volta in `R3_DATA_DIR`; non è
impostabile da env, quindi cambia solo se lo storage è andato perso.

## Procedura di prova remota (per nodo)

```bash
export R3_API_TOKEN=...            # token del nodo, mai committato
N=https://r3-external-node-a-production.up.railway.app

# 0. baseline con documento preregistrato
python scripts/r3_restart_proof.py capture --base-url $N \
  --seed-file r3/continuity_registry_seed.json --out proof/node-a.0.json

# 1. restart Railway (restart-service), attendere /health=200
python scripts/r3_restart_proof.py verify --base-url $N \
  --baseline proof/node-a.0.json --previous proof/node-a.0.json --out proof/node-a.1.json

# 2. secondo restart
python scripts/r3_restart_proof.py verify --base-url $N \
  --baseline proof/node-a.0.json --previous proof/node-a.1.json --out proof/node-a.2.json
```

Accettazione: entrambi i `verify` escono con codice 0 (`"result": "PASS"`) per
**ogni** nodo. Aggiungere `--require-ready` quando il controller RRR è configurato e
attivo, per chiudere anche la condizione `/ready=200`.

## Prova dai log, senza accesso di rete autenticato

Ogni avvio scrive una riga `R3_BOOT_FINGERPRINT {...}` nei log (nessun segreto:
verify key, `storage_id`, `storage_id_created_this_boot`, `process_boot_id`,
stato RRR, `document_count`, `document_set_sha256`, esito dei seed).

Documento preregistrato: `r3/seeds/issue86_restart_proof_seed_v1.txt` (immutabile),
SHA-256 `181935e360299343c1154ba719f3bc8675834ab2f8cf77ac746ee9b013a37f5c`.
Si attiva con `R3_PREREGISTERED_SEED_PATHS=r3/seeds/issue86_restart_proof_seed_v1.txt`.
Ingestione idempotente: al primo avvio `ingested`, poi sempre `present`.

Accettazione dai log, per nodo: tre righe consecutive (boot 0 + due restart) con
stessi `verify_key`, `storage_id`, `document_set_sha256`, stato RRR;
`process_boot_id` diverso ogni volta; `storage_id_created_this_boot: false` e
seed `present` nei due restart.

## Falsificatore

La persistenza **non** è risolta se, dopo un restart, si osserva anche una sola di:

- `storage_id` diverso, oppure `storage_id_created_this_boot: true`;
- `verify_key` diverso;
- ultimo evento RRR o `protocol_event_count` cambiati senza un nuovo evento del controller;
- `document_set_sha256` diverso o `documents_missing_or_corrupt` non vuoto;
- `durable_state_detected: false`;
- `process_boot_id` invariato (nessun restart reale: la prova non prova nulla).

## Limite noto del controllo di mount

`os.path.ismount` prova solo che `/data` non è il layer effimero del container.
Non prova la durabilità di ogni backend (un tmpfs passerebbe) né copre store non
filesystem. Se in futuro la persistenza passa a un driver non filesystem, serve una
sonda di readiness specifica del driver; la prova di restart resta l'evidenza
d'accettazione in ogni caso.

## Fuori ambito

Trasporto Letta (httpx, blocchi, `/letta/cooperate`) e quota Railway Agent sono
problemi separati da #86. Letta può tenere memoria lato provider; lo storage R3
durevole e le ricevute restano la radice di continuità indipendente.
