# Raffaello · continuità fra sito e Telegram

Claudio Terzi · C.Terzi · 12 settembre 2026

Implementati il dialogo personale e il collegamento con Alpha 74. L'analisi resta
manuale. Il testo libero del bot prepara una domanda; Analizza invoca il motore del
sito con le carte della lettura selezionata e una cronologia limitata.

Il bot conserva l'archivio SQLite e controlla il proprietario. Il sito usa un cookie
HttpOnly/Secure/SameSite=Strict ottenuto con un codice monouso generato nella chat
Telegram autorizzata. Non riceve il token Telegram e non accetta ID di proprietari
come credenziali. Il segreto del ponte resta sui server. Nessuna protezione Vercel
o Soglia esistente viene disabilitata.

`/dialogo-raffaello` riapre la stessa lettura o risposta: le carte hanno miniature
da 160 px e dettaglio da 640 px richiesto al tocco, con la rotazione corretta.
Ascolta usa la voce del browser su richiesta; non crea file audio o nuovi costi TTS.
Il contenuto personale viene recuperato soltanto dopo il collegamento.

In Alpha 74 compare Continua su Telegram solo quando il ponte è configurato.
Il trasferimento include domanda, contesto, carte, interpretazione e precedenti
approfondimenti. Da quel momento i nuovi approfondimenti passano all'archivio
condiviso. I significati canonici vengono ricalcolati sul server del bot dal
medesimo JSON, e il contesto iniziale rimane immutabile.

## Verifica

- 48 test del bot: vecchi registri, migrazione additiva, identità, letture immutabili,
  codici monouso, sessioni, lock, errori, analisi esplicita e token assenti dai log.
- 19 test Python del sito, incluso un collaudo fra i due repository con HTTP/SQLite/
  Flask reali. Solo il provider AI e il trasporto verso gli host pubblici sono
  sostituiti. Nessuna conversazione Telegram live è stata inviata o letta.
- Due harness DOM: selezione e trasferimento del contesto, pulsanti manuali,
  isolamento delle risposte tardive, miniature/dettaglio; copertura delle 592
  combinazioni Alpha e delle 296 immagini esistenti.
- Il browser non può raggiungere il server locale in questo ambiente. Questi
  harness verificano il comportamento del JavaScript, non il rendering iPhone.

## Attivazione

Su Vercel servono `RAFFAELLO_BOT_URL` e `RAFFAELLO_BRIDGE_SECRET`; i provider AI
sono quelli già usati dal sito. Sul servizio Render esistente servono lo stesso
segreto, `RAFFAELLO_ALLOWED_USERS`, l'indirizzo del sito e, se richiesto dalla
protezione Vercel, la credenziale per automazioni conservata solo sul server.

La pubblicazione del sito è compatibile con ponte assente: API personali chiuse e
lettura Alpha precedente operativa. Per attivare il bot occorre verificare nel
pannello Render il repository effettivamente collegato e il disco persistente,
eseguire backup dei dati e passare a un solo ricevitore Telegram. Il connettore GitHub rifiuta con HTTP 403 la scrittura nel repository separato
del bot. Il runtime completo e verificato è quindi conservato in
`integrations/raffaello-bot` in questo repository. Per distribuirlo da qui impostare
la root directory Render su `integrations/raffaello-bot`, installazione
`pip install -r requirements.txt` e avvio `python -m bot.main`.
Il cambio va effettuato sul servizio esistente dopo aver definito la conservazione
dei dati; per la ripartenza senza vecchi registri autorizzata da Claudio, vedere
la verifica del servizio riportata sotto.

I nuovi registri sono additivi. Il bot non cancella più un webhook all'avvio e
richiede `NETWORK_SECRET` per `/ask` e `/network/v1/*`. I peer esistenti devono
ricevere la stessa configurazione prima del passaggio. Procedura e script di
backup in [RAFFAELLO_2.md del bot](../integrations/raffaello-bot/docs/RAFFAELLO_2.md).

## Verifica del servizio Render

Il pannello autenticato conferma `protocollo-rosso-bot`, regione Frankfurt,
repository `Claudioterzi82/protocollo-rosso-bot`, branch `main`, commit live
`6fb9846a18c96f75ce7bce22ca205f1f3123155b`, avvio `python -m bot.main`.
Il piano è Free, senza disco persistente né accesso shell. I percorsi configurati
sono `protocollo.db` e `protocollo.persistence`, entrambi relativi. I log mostrano
polling Telegram con risposte HTTP 200. I nomi delle variabili confermano che il
ponte Raffaello non è ancora configurato.

Durante questa verifica Claudio ha autorizzato esplicitamente a eliminare i vecchi
registri e ripartire da zero. Il backup dei vecchi dati non blocca più il passaggio;
questa autorizzazione non equivale a una cancellazione già eseguita. Non autorizza
un abbonamento aggiuntivo o la perdita programmata delle nuove letture. Render Free
perde i file locali a riavvio, redeploy e sospensione per inattività; il piano
minimo a pagamento mostrato dal pannello è 7 USD/mese, più eventuale disco.

Corretta anche la registrazione delle richieste Telegram: INFO/DEBUG dei trasporti
sono disabilitati e il formatter oscura i token anche nelle eccezioni. Nessuna
chiave reale è stata aggiunta al codice o alla documentazione.

## Limiti dichiarati

Il dialogo non accede autonomamente agli archivi Atelier/Fabbrica, non trascrive
vocali e non invia audio nativo Telegram. Queste funzioni non sono simulate.
La ripetizione di un pulsante riusa il risultato persistito; un crash durante la
chiamata al provider può comportare un nuovo tentativo dopo la scadenza del lock.
La pagina presenta gli ultimi 30 scambi, mentre il database conserva anche i
precedenti. Nessuna cancellazione automatica dei registri personali.

Le API e i parametri di hosting sono verificati sulla documentazione ufficiale
[durata delle funzioni Vercel](https://vercel.com/docs/functions/configuring-functions/duration)
e [credenziale per automazioni](https://vercel.com/docs/deployment-protection/methods-to-bypass-deployment-protection/protection-bypass-automation).
