# RedFrag benchmark v1 — fixture reale congelato

Data: 2026-09-29
Stato: **FROZEN** — pronto per l'A/B con CLM vero su GPU. Nessun provider CLM eseguito.
Branch: `candidate/redfrag-benchmark-v1-20260929` (base `main` `8050f1c`)

## Fixture

- File: `tests/redfrag_benchmark_v1.json`
- SHA-256 congelato: `0cff14f3cfb64650d955ffedd227a875978e6682ccd653b1f78b112685bd127f`
  (verificato da `tests/test_redfrag_benchmark_v1.py`; cambiarlo richiede una v2)
- 30 casi, 5 per classe: DUPLICATE, CONFLICT, CORE, EVIDENCE, STALE, ACTIVE.
- Fonti tutte reali: 27 dal repo a commit fissati (`8050f1c`, branch `27391cf`, `cc610bc`),
  3 da Drive dove aggiungono un failure mode che il repo non ha (file con lo stesso nome in un
  altro repository; indice superato che nel testo si dichiara ancora "CANONICO").
  Per Drive: byte scaricati il 29/09, dimensione uguale ai metadati, SHA-256 registrato.
- Ogni caso registra provenienza, hash, gold (classe + azione), perché il gold è deterministico,
  e quale falsifier lo renderebbe ambiguo.
- Ricostruibile: `python scripts/redfrag_build_fixture_v1.py --check`.

Casi difficili inclusi: duplicato con provenienza incompleta (D05), stesso tema con contenuto
divergente (X01, X02), storico superato da tenere come puntatore (S05), evidenza negativa (E02, E03),
canone attivo simile a materiale stale (K05 ↔ S03, A01 ↔ S04), candidato da non promuovere
(A02, A05), stale che si dichiara canonico (S02), conflitto tra due sezioni di canone (X05),
duplicato di output d'errore (D03).

## Cosa vede il modello

Il benchmark passa al modello solo `cluster` (nome, estratti reali, hash, provenienza e i flag
del gate). Mai gold, motivazioni o falsifier. Due viste:

- `flags` — lo stato che RedFrag invia oggi in produzione, con i flag deterministici.
- `blind` — senza flag né evidenza derivata: il modello deve capire classe e azione dal contenuto.

La decisione finale usa sempre il gate completo. Il test verifica che il gold esca identico con
tre modelli fittizi diversi: la decisione finale non dipende dal modello, quindi l'A/B misura
solo la qualità del consiglio del modello.

## Falsifier trovato durante la costruzione

Il benchmark del 28/09 passava al modello l'intero caso, **incluse `expected_class` ed
`expected_action`**. Il modello locale leggeva la risposta dentro l'input. Rieseguito sugli stessi
5 casi senza etichette: accordo classe 1.0 → 0.4, accordo azione 0.8 → 0.2
(`docs/evidenze/R3_REDFRAG_BENCH_LEGACY5_NOLEAK_2026-09-29.json`). I numeri del 28/09 non vanno
più citati.

## Baseline `r3_clm` (locale, zero rete) sul fixture congelato — 20 ripetizioni per caso

| Vista | Decisione finale | Classe (solo modello) | Azione (solo modello) | Dissenso | Fallimenti | Latenza p50 / p95 / p99 ms |
|---|---|---|---|---|---|---|
| flags | 1.00 | 0.167 | 0.033 | 1.00 | 0 | 33.6 / 54.5 / 65.2 |
| blind | 1.00 | 0.133 | 0.100 | 1.00 | 0 | 31.7 / 51.2 / 53.4 |

Riferimento per il caso: 8 classi → 0.125 a caso; 5 azioni → 0.20 a caso.
Il baseline locale è al livello del caso: tutto il lavoro lo fa il gate deterministico.
Evidenze: `docs/evidenze/R3_REDFRAG_BENCH_V1_R3CLM_FLAGS_2026-09-29.json`,
`docs/evidenze/R3_REDFRAG_BENCH_V1_R3CLM_BLIND_2026-09-29.json`.

Jev/TypeSafe non è stato eseguito: questa sessione non ha `TYPESAFE_API_KEY` (resta solo sul
servizio Railway e non va copiata). Si può eseguire dove la chiave vive con
`python scripts/r3_clm_redfrag_benchmark.py --provider typesafe --view {flags,blind}`.

## Prossimo passo: una sessione GPU controllata

`CLM_BASE_URL=http://<gpu>:8700 python scripts/r3_clm_redfrag_benchmark.py --provider clm --view flags`
e poi `--view blind`, stesso fixture (hash sopra). Registrare anche se il risultato è negativo.
La metrica decisiva è l'accuratezza del solo modello in vista `blind`; la decisione finale resta 1.00
per costruzione.

Firma progetto: C.Terzi
