# RedFrag su System One — baseline R3-CLM, pronto per CLM vero

Data: 2026-09-29
Stato: **CANDIDATE** — branch `candidate/redfrag-systemone-20260929`, basato su `main` `f45b3be`
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

## Passo 3 — A/B con CLM vero

1. Server CLM temporaneo su GPU (Qwen3-8B encoder + `clm-serve`), acceso solo per il run.
   Decisione di costo di Claudio. Su CPU (GitHub Actions, 28/09) il run non è mai arrivato in fondo.
2. `CLM_BASE_URL=... python scripts/r3_clm_redfrag_benchmark.py --provider clm`
3. Confronto con la baseline sugli stessi casi: accuratezza finale, accordo del solo modello,
   latenza, errori. Poi spegnere il server.
4. Promozione di CLM su RedFrag solo se equal-or-better, e solo dopo un set di casi più ampio.

Firma progetto: C.Terzi
