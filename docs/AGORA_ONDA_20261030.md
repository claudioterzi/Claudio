# Agorà → ONDA sul PC

Data: 30 ottobre 2026. Classificazione: PATCH del collegamento, RETEST della precedente attivazione dichiarata dal Consiglio.

## Problema e comportamento

Il comando `/consiglio Attiva onda` produceva una delibera; non chiamava il servizio Windows. La delibera e i risultati storici rimangono integralmente conservati.

Agorà propone ora un'azione esplicita **Attiva ONDA sul PC**, anche recuperando una vecchia delibera con quel comando esatto. I comandi rapidi sono `/onda attiva` e `/onda stato`. Richiedono la stessa autenticazione del proprietario già usata da Agorà. Le raccomandazioni dei modelli non diventano comandi.

La richiesta utilizza le ricevute esistenti `agora:v1:request:<id>` e la loro cronologia. Un indice Redis di richieste pendenti collega l'archivio al Dell. L'adapter `scripts/agora_onda_pc.py` esegue un solo passaggio nel task Windows `ONDA_Guardiano_riavvio` già presente, senza un nuovo servizio o una nuova pianificazione. Il task controlla ogni cinque minuti; una richiesta scade dopo dieci minuti. A PC scollegato non viene attestata l'attivazione.

L'adapter può soltanto osservare il servizio o avviare il task esistente `R3_ONDA_servizio`. Una ONDA già sana mantiene il suo processo. Il risultato completo richiede uno stato recente, un PID che corrisponda a `python -m onda.servizio` e gli agenti NARR-003/NARR-013 operativi. Il file viene riletto dopo il controllo del processo. Questa prova riguarda stato e processo; heartbeat firmati e inferenza sono verifiche distinte.

## Integrità e recupero

- La connessione all'archivio usa TLS e la credenziale già configurata per il sito, protetta sul Dell da DPAPI dell'utente corrente. Non è presente nel repository.
- Le azioni sono un insieme chiuso. Nessuna stringa remota è eseguita come comando shell.
- Lease per richiesta, scrittura condizionale, rilettura e indicatore persistente di dispatch impediscono la riesecuzione automatica dopo un esito incerto. Non viene promessa esecuzione distribuita exactly-once.
- Un errore di registrazione nel web non sovrascrive una ricevuta già salvata dal worker. Reinvio dello stesso ID e recupero riparano l'indice senza rinnovare la scadenza.
- Il controllo ONDA non invia Telegram. Le altre funzioni conservano la loro copia facoltativa.
- Il browser ritenta il recupero dopo errori transitori e scarta risposte relative a una selezione precedente.

## Validazione

Suite interessate: `tests/test_agora_onda.py`, `tests/test_agora_onda_web.py`, `tests/test_agora_web.py`, `tests/test_agora.py`; controllo sintassi di `public/agora.js`.

Il 30 ottobre sono stati osservati direttamente il servizio esistente e due heartbeat firmati; una richiesta generativa è stata completata in 37,922 secondi con risposta corretta alla verifica 17 × 23 = 391. Sul Dell il round-trip DPAPI e l'accesso TLS alla richiesta originale nell'archivio Agorà sono stati verificati. Le ricevute operative locali documentano separatamente installazione e prova del collegamento.

## Ripristino circoscritto

Rimuovere soltanto il blocco delimitato `AGORA_ONDA_ADAPTER_V1` dal guardiano Windows, usando la copia e le impronte conservate nella cartella di stato `R3-diario/agora-onda`. Il resto del guardiano e il task ONDA restano operativi. Il codice del sito è ripristinabile con il revert del commit di questa modifica, senza eliminare registri, richieste storiche o credenziali. Preservare le modifiche concorrenti e verificare gli hash prima del ripristino.
