# TypeSafe / Jev — Layer universale per tutti i progetti

Data: 2026-09-20  
Owner / Vision: Claudio Terzi  
Firma progetto: C.Terzi  
Stato: CANDIDATE PATCH — validazione CI richiesta

## Decisione canonica

TypeSafe/Jev non è un progetto separato e non sostituisce Raffaello. È un layer comune di giudizi strutturati riusabile da tutti i progetti quando serve comprensione semantica rapida.

Architettura:

Raffaello / progetto → stato limitato → TypeSafe System One → Choice / Score / Noul → Raffaello + P5/P6 → decisione / verifica / eventuale azione

Il codice, non Jev, mantiene il controllo del workflow.

## Implementazione condivisa

- typesafe_sister/client.py — unico trasporto server-side verso POST /v1/systemone.
- typesafe_sister/policy.py — unico punto di revisione delle domande condivise e di dominio.
- typesafe_sister/universal.py — evaluator comune per qualunque project_id.
- api/orchestra.py — applica il secondo giudizio a ogni dialogo/progetto che passa dall'Orchestra.
- fabbrica_typesafe.py — conserva le domande specifiche Fabbrica ma usa la policy e il trasporto comuni.

Non creare copie project-local del client, chiavi duplicate o un secondo motore globale.

## Giudizi universali

Una singola richiesta TypeSafe valuta in parallelo:

### Choice
- focus: develop | clarify | verify | review

Il focus è una proposta di instradamento informativo, non un'autorizzazione.

### Score
- readiness — quanto lo stato è pronto per un prossimo passo limitato;
- coherence — compatibilità interna tra obiettivi, vincoli e dipendenze;
- grounding — qualità del legame tra affermazioni, evidenze e provenienza;
- risk — conseguenza/reversibilità del prossimo passo proposto.

I livelli sono descrittivi, non numeri vuoti. Lo score e la confidence vengono conservati separatamente.

### Noul
- contradiction
- missing_critical_input
- unsupported_claim
- freshness_needed
- external_side_effect

I Noul restituiscono probabilità, non permessi.

## P5 / P6

P5: un giudizio Jev non è una prova indipendente di un fatto esterno e non può auto-confermare un altro modello.

P6: quando una conclusione dipende da un fatto verificabile, il sistema deve cercare o richiedere il riscontro appropriato. Il flag freshness_needed serve a segnalare questo bisogno, non a sostituire la verifica.

## Regola sulle azioni

TypeSafe non può autorizzare:
- invii, pubblicazioni o contatti;
- pagamenti, trasferimenti, acquisti o prenotazioni;
- cancellazioni, overwrite o modifiche di permessi;
- deploy, merge o modifiche irreversibili;
- impegni legali o finanziari;
- uso di credenziali o ampliamento di accesso.

Le autorizzazioni restano deterministiche e separate dal giudizio probabilistico.

## Dati e segreti

- TYPESAFE_API_KEY resta server-side.
- Il layer universale accetta al massimo 64 KiB di stato serializzato.
- Passare solo lo stato necessario al giudizio.
- Non inviare archivi privati completi, token, password o API key.
- Gli errori vengono registrati per classe, senza contenuto privato della richiesta.

## Copertura dei progetti

1. Progetti che usano Raffaello/Orchestra: ricevono automaticamente il layer universale.
2. Fabbrica dei Desideri: mantiene i suoi giudizi di dominio sul medesimo transport/policy.
3. Moduli software futuri: importano assess_project_state invece di creare un nuovo client.
4. Progetti editoriali, creativi o di ricerca: il layer si usa per readiness/coherence/grounding, senza trasformare proposte creative in fatti.
5. Progetti legali/finanziari o con effetti esterni: Jev resta advisory; fonti, calcoli, regole e autorizzazioni devono essere verificati separatamente.
6. Tarocchi/oracolo: TypeSafe può valutare coerenza dell'interazione, stato e requisiti UX; non è una prova di verità divinatoria.

## Soglie

La policy universale non incorpora soglie automatiche per autorizzare o bloccare azioni. Le probabilità e le confidence vengono conservate grezze. Eventuali soglie di routing devono essere esplicite, reversibili e validate su casi del progetto.

La Fabbrica conserva temporaneamente la soglia 0.75 soltanto per suggerire micro-domande mancanti; non autorizza azioni.

## Verifica

Test introdotti:
- risposta completa Choice/Score/Noul;
- degradazione pulita se TypeSafe non è configurato;
- rifiuto di risposte incomplete/malformate;
- rifiuto dello stato oltre 64 KiB prima della chiamata API;
- suite Fabbrica esistente per prevenire regressioni dopo la centralizzazione.

Documentazione TypeSafe di riferimento:
- https://docs.typesafe.ai/llms.txt
- https://docs.typesafe.ai/api
- https://docs.typesafe.ai/primitives
- https://docs.typesafe.ai/confidence
- https://github.com/typesafe-ai/skills/blob/main/skills/typesafe-ai/SKILL.md

## Regola permanente

Quando un nuovo progetto nasce o un progetto esistente viene modificato, chiedere prima:
1. c'è un giudizio semantico fragile che TypeSafe può rendere tipizzato?
2. quel giudizio è già coperto dalla policy universale?
3. se serve una domanda di dominio, può essere aggiunta alla policy centrale senza creare un motore parallelo?
4. i fatti esatti, le autorizzazioni e gli effetti esterni restano nel codice/verificatore appropriato?

Se sì, riusare il layer. Se no, non aggiungere TypeSafe soltanto per presenza decorativa.
