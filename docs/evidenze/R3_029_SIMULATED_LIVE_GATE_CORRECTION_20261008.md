# R³-029 — Rettifica dell'etichetta «PUBLIC LIVE GATE FAILED»

**Osservazione UTC:** 2026-10-08T11:54:38Z  
**Owner:** Claudio Terzi  
**Tipo:** rettifica documentale public-safe, append-only. **NON** è un nuovo risultato di benchmark.  
**Decisione:** `LIVE_NOT_RUN / SIMULATED_REPORT_NOT_ADMISSIBLE_AS_LIVE / STRUCTURAL_AB_PASS / KEEP_ISOLATED / HOLD`

## Provenienza e confine d'autorità

Questa nota corregge **il rapporto incollato in chat il 2026-10-08** intitolato `R³-029 Pointer-First A/B — PUBLIC LIVE GATE FAILED`. È una fonte **DATA_ONLY**, non un nuovo mandato, una prova provider o un evento di produzione. Il rapporto ammette esplicitamente una simulazione senza una chiave/provider reale. La trascrizione dei campi per il test di coerenza NON equivale ad avere i byte originali di un log provider.

Rilettura indipendente tramite GitHub autenticato prima della rettifica:

- Repository: `claudioterzi/Claudio`; `main = 83561466509db03c9d5dd73d089d6d90199ab925`.
- PR [#91](https://github.com/claudioterzi/Claudio/pull/91): **OPEN / DRAFT / NOT_MERGED**, head `35c75f5d7bec16b97ad70295633045d227ae51e4`.
- [Ricevuta pubblica originaria](https://github.com/claudioterzi/Claudio/blob/83561466509db03c9d5dd73d089d6d90199ab925/docs/evidenze/R3_029_POINTER_AB_PUBLIC_RECEIPT_20261008.md): `STRUCTURAL_AB_PASS / KEEP_ISOLATED / HOLD`. Il rapporto simulato **non** la sostituisce.
- `7a9c2a7a0748bf082d9d8efc325b1b625a8004b59b5f0900301188c43d9cd0a1` è lo **SHA-256 della ricevuta JSON locale precedente**, non un SHA Git di `main`. La ricevuta GitHub è datata 2026-10-08, non 2026-10-07 come il report riportava.
- Il vecchio `/workspace` non è disponibile in questa esecuzione: i vecchi commit *locali* non sono stati riletti direttamente. La PR remota è invece visibile e ancora aperta.

## Problemi accertati nel report (non evidenza live)

1. `SIMULATION_MISLABELED_LIVE`: titolo e decisione proclamano un test live; il testo dichiara simulazione senza provider.
2. `BYTES_PROXY_MISLABELED_EXACT_PROVIDER_TOKENS`: la riduzione di byte o un fattore convertito in token non equivalgono ai contatori restituiti dal provider.
3. `SUCCESS_SUMMARY_CONTRADICTS_CASES`: il riepilogo afferma successo inferiore su 2/6 casi, mentre la tabella riporta `=` per tutti e sei; nessun risultato live è stato osservato.
4. `HUMAN_PROXY_MISLABELED_INDEPENDENT_REVIEW`: «AI + human proxy» non attesta la presenza di revisori umani reali su output reali.
5. `SHA256_RECEIPT_CONFUSED_WITH_GIT_COMMIT`: un SHA-256 di ricevuta non prova un HEAD o un ripristino Git.
6. `CANDIDATE_ABSENCE_CONTRADICTS_OPEN_PR`: «no active pointer-first candidate» contrasta con PR #91 ancora aperta. La presenza di un candidato *locale* resta invece non verificata.
7. `UNVERIFIED_CANON_SUPERSESSION`: la ricevuta originale era ancora presente su `main`; nessuna sostituzione canonica risultava dalle letture.

**Aggregazione numerica:** la media **aritmetica non ponderata** delle sei variazioni percentuali token incollate è `+1,533333%`, mentre il riepilogo riferisce `+1,8%`. Senza pesi, denominatori e log di utilizzo provider non si può verificare un'eventuale media ponderata: discrepanza **NON RICONCILIATA**, non una nuova misura live. Anche il `+37%` degli interventi umani non è supportato da tracce indipendenti di interazione.

## Controlli riproducibili e limiti

Un auditor deterministico `r3_029_report_audit.py` ha controllato una rappresentazione strutturata **trascritta dal testo dell'utente**, con i sei casi dichiarati. Esito: **7 anomalie + 4 cautele**; 13 test deterministici PASS, `py_compile` PASS; nessuna richiesta a provider. Include controlli negativi e non autorizza mai promozione/cancellazione anche con input strutturalmente coerenti. È un **linter di coerenza**, non un test di successo AI, un verificatore indipendente della realtà o un sistema di autorizzazione.

## Decisione e percorso di correzione

**KEEP / RETEST.** Conservare la ricevuta strutturale e il candidato isolato; classificare il presunto fallimento live come **NOT_ADMISSIBLE_AS_LIVE_EVIDENCE**. Non promuovere Pointer-First; non cancellare branch, PR, file, receipt o copie locali per via del rapporto simulato. Nessun merge, deploy, costo, chiamata Jev/CLM, cancellazione o modifica di produzione è stato fatto in questa rettifica.

**NEXT:** sull'host deliberatamente autorizzato eseguire A/B paired sugli stessi sei casi, manifest/dataset/config frozen, ID di richieste e risposte, token usage reale del provider, interventi umani registrati, punteggio indipendente e hash delle fonti. Classificare `LIVE_PASS` o `LIVE_FAIL` soltanto dopo la verifica delle ricevute. Se questa prova manca: `LIVE_NOT_RUN / HOLD`.

**Completion criterion:** sei coppie di casi reali con outcome e aggregazione consistenti; nessuna regressione su autorità/provenienza; misure token realmente osservate; onere umano osservato; review R3-020 e decisione umana per una possibile adozione.

**Resume trigger:** ricevuta reale verificabile dall'host autorizzato oppure errore documentato nel canon.