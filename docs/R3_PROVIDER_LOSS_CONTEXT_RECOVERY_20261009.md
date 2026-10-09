# R³ — Recupero del contesto da una custodia superstite

Il 9 ottobre 2026 è riuscito un recupero locale del **contesto documentale
datato 8 ottobre, 19:16:57 UTC**, usando due archivi realmente riscaricati
da Drive. Il loader condiviso non legge il repository originale e non usa
la rete durante la prova. Non sono stati modificati loader o runtime.

La baseline dell'8 ottobre aveva mostrato una dipendenza concreta: il ZIP
portabile conteneva il bootstrap, ma non checkpoint e prove. `--resume`
restituiva RC2 `RESUME_BLOCKED`. I due record esatti del commit GitHub
`671e38d36290cb7fd221248d0f27c3b09fd5789d` sono stati quindi conservati
in un companion PUBLIC separato, mantenendo intatto il seme originale.

Il companion è stato depositato **il 9 ottobre**, nella cartella progetto
Drive esistente. Upload, metadati owner-only e download raw sono stati
osservati tramite connector; byte e hash esterno coincidono. Il nome
`20261008` indica lo snapshot, non la data del deposito.

- [Seme Drive](https://drive.google.com/file/d/1CueuD-FQQrL68Ien7sI7KuQd25roRnc6/view): 31.263 byte, SHA256 `2c80dafc22a1adb5951131ad9dcdd10093e87e34198bd947e0a18d22680b3522`.
- [Companion Drive](https://drive.google.com/file/d/1HF713S_tpK5eHjKjs6pggArWsT4u_7p5/view): 5.577 byte, SHA256 `4d1ac05d9a66232cc62dbf76e2e4be75d32bf958d43f909540f0590d7e365884`.
- [Pin esterno companion](../public/R3_PUBLIC_WORKSTATE_COMPANION_20261008.sha256).
- [Prova classificata](evidenze/R3_PROVIDER_LOSS_CONTEXT_RECOVERY_20261009.json) e [checkpoint di ripresa](evidenze/R3_PROVIDER_LOSS_CONTEXT_CHECKPOINT_20261009.json).

Le due cartelle Drive non rappresentano provider indipendenti. I pin
verificano i byte rispetto al riferimento fidato del host; non sono firme
crittografiche né autenticazione del proprietario.

| Caso finale | Risultato osservato |
|---|---|
| Fonte integra | RC0; sette campi esatti, `DATA_ONLY`, poi `VALIDATED` |
| Pin checkpoint errato | RC2; nessuno stato recuperato |
| Pin prove errato | RC2; nessuno stato recuperato |
| Checkpoint mancante | RC2; nessuno stato recuperato |
| Prove mancanti | RC2; nessuno stato recuperato |
| Prove alterate | RC2; nessuno stato recuperato |
| Owner del manifest alterato | RC1 prima del recupero |

Esecuzione nativa finale: **9 ottobre, 01:50:24 UTC**. Cinquantasei
controlli del guard respingono operazioni di lettura esterne, scrittura,
mutazione, socket, DNS e creazione di subprocessi. Sette inventari delle
fixture prima/dopo coincidono. Il loader legge soltanto fixture e stdlib,
con Python `-I -S -B`, ambiente svuotato e nessun modulo terzo. Il driver
prepara prima le fixture; il guard riguarda il loader fidato in CPython.

La receipt nativa completa resta in custodia privata del workspace:
101.811 byte, SHA256 `6f4f09b47eb4ae7976711c4a31ead6b556ef2cd102b08c2804328bf56ae0af00`.
Il riepilogo pubblico distingue l'esecuzione nativa dalle osservazioni
connector. Un secondo agente ha riletto sorgenti, archivi e receipt; non
ha ripetuto il test né conferito autorità al risultato.

Per riprodurre, ottenere i due ZIP da custodie autenticate, verificare i
pin completi forniti dal host, poi usare il driver manuale
`tests/r3_provider_loss_context_probe.py` con modalità `baseline` oppure
`final`. La modalità finale richiede `--seed-zip`, `--companion-zip`,
`--companion-sha256`, `--wrapper` (il guard `tests/r3_recovery_guard.py`),
`--original-source-control` (un file originale esistente, solo controllo
di rifiuto), `--fixture-parent` e un nuovo percorso `--receipt`.
Fornire percorsi assoluti per i due ZIP, il wrapper, il file originale di
controllo, la cartella fixture e la receipt: il child cambia directory
verso la fixture, quindi un wrapper relativo verrebbe cercato nel posto
sbagliato.
Il driver verifica inventario ZIP, manifest, CRC, dimensioni, hash dei
payload e pin dei due record prima di creare una cartella separata.
Non sovrascrivere una receipt o modificare un originale per ottenere PASS.

È una simulazione sullo stesso host di indisponibilità di GitHub e della
sorgente originale. Non dimostra outage reale, isolamento OS, inferenza,
autenticazione umana, recupero di volumi o storia privata. I vecchi
checkpoint citati dai record restano riferimenti: non sono inclusi nei
due ZIP. Il checkpoint di ripresa del 9 ottobre descrive questo esito;
non è lo snapshot dell'8 ottobre recuperato nella prova.

Prossima azione: usare un percorso realmente autenticato verso il NAS o
un altro esecutore indipendente già esistente, verificare copie e
ripristino, poi inferenza e autorità del controllore RRR separatamente.
Restano invariati il blocco Jev per token caller non collegato, i gate di
#113 e la quarantena di readiness. Nessun deploy, spesa, nuova autorità o
cancellazione. Gli originali, i fallimenti precedenti e le fixture restano
conservati.
