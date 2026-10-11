# RedFrag su System One — baseline R3-CLM, pronto per CLM vero

Data: 2026-09-29
Stato: **MERGED / BASELINE VERIFIED / REAL CLM A/B DEFERRED** — PR #103, merge `8050f1c02c512cddfd822c467eab8a7953be4517`
Autorità: **ADVISORY ONLY** — il gate deterministico sulle evidenze decide, il modello consiglia.

## Cosa cambia rispetto al branch del 28/09

Il branch `candidate/r3-clm-redfrag-20260928` aveva la pipeline RedFrag ma un suo router
(`R3_SYSTEM_ONE_BACKEND`), in conflitto con il router provider-neutral poi entrato su `main`
(PR #98, `R3_SYSTEMONE_PROVIDER`). Qui RedFrag è portata sul router di `main`: un solo
percorso System One, nessun motore parallelo.

- `typesafe_sister/client.py`: nuovo provider esplicito `r3_clm` (locale, zero rete).
  Non viene mai scelto da `auto`. Non ha `rank` nativo.
- `typesafe_sister/redfrag.py`: chiama `client.system_one(provider=R3_REDFRAG_PROVIDER)`.
  Default `r3_clm`; `clm` usa il server CLM a `CLM_BASE_URL`; `typesafe` usa Jev.
- `typesafe_sister/redfrag_pipeline.py`, `r3_clm.py`, policy RedFrag: invariati rispetto al 28/09.
- Shadow mode del 28/09 non portata: l'A/B si fa con lo script di benchmark per provider.

## Evidenza

- Test System One / RedFrag: 37 su 37 OK (1 skip preesistente), incluso il test che la stessa
  pipeline con `R3_REDFRAG_PROVIDER=clm` chiama `POST {CLM_BASE_URL}/v1/systemone` con le
  stesse domande e lo stesso gate.
- Baseline locale `r3_clm`, 5 casi × 100 ripetizioni: decisioni finali 5/5, accordo classe
  del solo modello 1.0, accordo azione 0.8 (dissenso su N02 corretto dal gate), p50 ≈ 20 ms,
  zero chiamate di rete, zero cancellazioni.
  File: `docs/evidenze/R3_REDFRAG_R3CLM_BASELINE_2026-09-29.json`.

Cinque casi scelti a mano: è una regressione, non una prova di generalizzazione.

## Gate prima della GPU

Decisione 29/09: non accendere ancora una GPU sul fixture da 5 casi. Prima congelare un set di almeno 24 casi reali (target preferito circa 30), bilanciato tra `DUPLICATE`, `CONFLICT`, `CORE`, `EVIDENCE`, `STALE`, `ACTIVE` e failure mode osservati nel progetto. Ogni caso deve avere provenance, gold deterministico, expected action e falsifier/ambiguità. Il fixture va congelato prima di vedere il risultato del provider CLM reale.

Lo stesso fixture congelato deve essere eseguito con `r3_clm`, TypeSafe/Jev quando disponibile e poi CLM-v0.1 reale. Le metriche minime: final decision accuracy, model-only class/action accuracy, dissent rate, latency p50/p95/p99, failures/abstentions. Nessun wording tuning dopo aver osservato i risultati di un provider.

## Passo 3 — A/B con CLM vero

1. Server CLM temporaneo su GPU (Qwen3-8B encoder + `clm-serve`), acceso solo per il run.
   Decisione di costo di Claudio. Su CPU (GitHub Actions, 28/09) il run non è mai arrivato in fondo.
2. `CLM_BASE_URL=... python scripts/r3_clm_redfrag_benchmark.py --provider clm`
3. Confronto con la baseline sugli stessi casi: accuratezza finale, accordo del solo modello,
   latenza, errori. Poi spegnere il server.
4. Promozione di CLM su RedFrag solo se equal-or-better sul fixture congelato esteso. `r3_clm` resta un baseline R³ interno e non va descritto come CLM-v0.1.

Firma progetto: C.Terzi
