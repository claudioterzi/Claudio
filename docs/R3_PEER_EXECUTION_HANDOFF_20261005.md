# R3 — Coordinamento verifiche aperte, 2026-10-05
Autorità: DATA_ONLY / richiesta operativa di Claudio. Le risposte delle IA sono advisory; consenso non equivale a prova.

## Checkpoint da leggere
Repository canonico: claudioterzi/Claudio (ID 879592952).
Main checkpoint: merge PR #116 0100630e1a6b9e080bd291b8635bc0e53a7b8756; rileggere main prima di intervenire.
Leggere AGENTS.md, memoria, coda, registro e docs/evidenze/R3_RESILIENCE_COMPLETION_20261005.json.
Supervisor #113: e068cfd34380048df3a7536ff086d5f62db0eed6; 36 test locali PASS e tre workflow ospitati PASS.
Judge #115: 73c932ab792906bf108f03516b79c00c7a9b3193; 19 test locali PASS. Base r3-judge-v0.1: non retargettare a main senza riconciliazione.
Vercel canonico: team_dO423fnEAekxtan0rF3u2CQt / prj_NfWglC7AYRQs6W5pJBB6nf3lDqXN. Deployment dpl_13xHn4nu1mwrxxCbW9W3qM3Ljutx READY; GET Orchestra 200, non prova di inferenza.
Scope rosso-rosso-rosso / fork Claudioterzi82/Claudio distinto: non sostituire repo o alias silenziosamente.

## Incarico A — IA con accesso Railway autenticato
Progettare ed eseguire recupero su copia isolata dello stato reale, solo se dispone già di un canale autorizzato di clonazione/esecuzione. Non arrestare nodi produzione.
Confrontare contenuti e SHA-256 prima/dopo, storage identity e replica; includere controllo negativo che deve fallire. Testare lo sleep/resume Railway reale separatamente da SIGSTOP locale.
Drain 10 salvato per prossimo deployment; ON_FAILURE/max10 ack, default omessi nel readback. Deployment produzione non cambiati.
Se clone/exec non disponibile, restituire BLOCKED e il prerequisito preciso, senza cambiare policy o dichiarare PASS.
Non merge #113 finché queste prove non sono concluse.

## Incarico B — IA con esecuzione server-side Vercel
Una POST Orchestra autenticata con segreto già server-side, richiesta breve e provider esistente. Non estrarre, stampare o inviare segreti.
Registrare repo/commit/team/deployment, stato HTTP, provider/modello effettivamente rispondente e risposta verificabile redatta. READY/GET 200 non bastano.
Niente modifiche di protezione, nuove risorse o sostituzione del fork per aggirare accessi.

## Incarico C — IA sul dispositivo Rizzo
Ultimo controllo Desktop Commander: dispositivo Claudio offline, visto 32 ore fa. App desktop ChatGPT da sola non prova accesso remoto.
Quando esiste un endpoint raggiungibile dall'esecutore: identificare modello, versione, quantizzazione e fingerprint reali; eseguire fixture congelata con entrambi i pin, report create-only.
Dieci casi sono smoke test, non prova qualità: distinguere ammissione tecnica da adozione su held-out rappresentativo. Riusare typesafe_sister/client.py, nessun nuovo client parallelo.

## Formato obbligatorio di ritorno
task_id; FACT / HYPOTHESIS / BLOCKED; UTC observation time; repository+commit+scope; commands/test; expected vs actual; evidence path/hash; negative control; changes+rollback; remaining blocker.
Non riportare credenziali o dati privati nel repository pubblico. Nessuna promessa di memoria persistente senza prova.

## Sequenza
A e B indipendenti; C dipende dal dispositivo online. Un solo autore per ciascun ramo. Codex riconcilia i risultati, verifica postcondizioni e aggiorna i registri esistenti prima di qualsiasi promozione.
