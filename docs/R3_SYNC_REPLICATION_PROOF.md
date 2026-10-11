# R3 — Prova di replica A↔B in produzione

Domanda: la replica tra `r3-external-node-a` e `r3-external-node-v2` funziona
davvero ogni 5 minuti, o esiste solo `r3/sync.py --loop`?

Stato al 2026-10-01 prima di questa modifica: **nessun processo eseguiva il sync**
su Railway (nessuna chiamata `/sync` nei log di node-a dal 24/09). Persistenza
(Issue #86) e replica sono due proprietà distinte.

## Come gira

Il loop gira come processo affiancato nel servizio `r3-external-node-a`
(il piano Railway attuale non permette servizi aggiuntivi):

```
sh -c "R3_LOCAL_URL=http://127.0.0.1:$PORT python -m r3.sync --loop & exec uvicorn r3.node:app --host 0.0.0.0 --port $PORT"
```

Variabili su node-a:

| Variabile | Valore |
|---|---|
| `R3_PEERS` | URL pubblico di node-v2 |
| `R3_PEER_TOKEN` | riferimento Railway al `R3_API_TOKEN` di node-v2 (mai in chiaro nel repo) |
| `R3_SYNC_INTERVAL` | `300` |
| `R3_SYNC_CANARY` | `true` |
| `R3_SYNC_CANARY_EVERY` | `1` durante la prova; poi es. `12` (una ricevuta all'ora) |
| `R3_SYNC_START_DELAY` | `30` |

Un solo loop su A basta per i due versi: a ogni ciclo tira da B ciò che manca ad A
e spinge su B ciò che manca a B.

## La prova: canarino + ricevuta

A ogni ciclo con canarino:

1. scrive un documento unico (timestamp) **solo su A** e un altro **solo su B**;
2. controlla che ciascuno sia assente sull'altro nodo prima del sync;
3. esegue il sync normale;
4. scarica ciascun canarino dal nodo **opposto** e ne verifica lo SHA-256;
5. confronta gli insiemi di hash completi di A e B;
6. scrive una riga `R3_SYNC_RECEIPT {...}` nei log, con `pass: true|false`.

La verifica si fa leggendo i log Railway: niente token, niente accesso di rete.

## Accettazione

- per una finestra di almeno 1 ora: una ricevuta ogni ~5 minuti (scarto massimo 10);
- ogni ricevuta con `pass: true`, entrambi i canarini arrivati, `sets_equal: true`;
- dopo un restart di node-v2 (volume persistente), le ricevute successive tornano `pass: true`.

## Falsificatore

La replica **non** funziona se si osserva anche una sola di:

- nessuna `R3_SYNC_RECEIPT` per più di 10 minuti (loop morto o nodo addormentato);
- `local_to_peer_arrived` o `peer_to_local_arrived` = `false`;
- `sets_equal: false` per due ricevute consecutive;
- `pass: false` con `error` non transitorio.

`/health=200` su entrambi i nodi **non** prova nulla sulla replica.

## Limiti dichiarati

- Stesso provider (Railway), stessa regione: è replica tra servizi, non backup indipendente.
- I canarini sono documenti permanenti: crescita limitata con `R3_SYNC_CANARY_EVERY`.
- Le prove di restart future vanno lette sul seed preregistrato, non sull'intero
  insieme di documenti, che ora cresce con i canarini e con la replica.
- Il loop dentro node-a è un compromesso dovuto al limite del piano: se node-a è
  giù, la replica si ferma (lo rivela l'assenza di ricevute).
