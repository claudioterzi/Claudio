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

- 49 test del bot: vecchi registri, migrazione additiva, identità, letture immutabili,
  codici monouso, sessioni, lock, errori, analisi esplicita, token assenti dai log
  e costruzione dei veri handler all'avvio senza aprire un ricevitore Telegram.
- 19 test Python del sito, incluso un collaudo fra i due repository con HTTP/SQLite/
  Flask reali. Solo il provider AI e il trasporto verso gli host pubblici sono
  sostituiti. Nessuna conversazione Telegram live è stata inviata o letta.
- Due harness DOM: selezione e trasferimento del contesto, pulsanti manuali,
  isolamento delle risposte tardive, miniature/dettaglio; copertura delle 592
  combinazioni Alpha e delle 296 immagini esistenti.
- Il browser non può raggiungere il server locale in questo ambiente. Questi
  harness verificano il comportamento del JavaScript, non il rendering iPhone.

## Attivazione: configurazione salvata e passaggi mancanti

Il 12 settembre 2026 sono stati salvati su Vercel Production `RAFFAELLO_BOT_URL`
e un nuovo `RAFFAELLO_BRIDGE_SECRET`. Su Render sono stati salvati lo stesso
segreto, `RAFFAELLO_SITE_URL` e una nuova credenziale dedicata
`RAFFAELLO_VERCEL_BYPASS_SECRET`. Gli altri segreti non sono stati letti o
modificati. I provider AI restano quelli già usati dal sito. La protezione Vercel
rimane attiva; l'accesso diretto anonimo alla route status restituisce un redirect.

Manca `RAFFAELLO_ALLOWED_USERS`: /start nella chat privata con il bot mostra
all'utente non ancora abilitato il proprio ID numerico. Occorre ricevere quello
di Claudio e inserirlo nella lista autorizzata. Questo passaggio non può usare
l'ID del bot, un nome utente del browser o un'autorizzazione aperta a tutti.
Prima di affidare nuove letture all'archivio va risolta la persistenza descritta
sotto. L'analisi completa Telegram → sito → risposta e la riapertura web
devono ancora essere collaudate con l'account abilitato.

I nuovi registri sono additivi. Il bot non cancella più un webhook all'avvio e
richiede `NETWORK_SECRET` per `/ask` e `/network/v1/*`. I peer esistenti devono
ricevere la stessa configurazione prima del passaggio. Procedura e script di
backup in [RAFFAELLO_2.md del bot](../integrations/raffaello-bot/docs/RAFFAELLO_2.md).

## Verifica del servizio Render

Il pannello autenticato conferma `protocollo-rosso-bot`, regione Frankfurt,
ora collegato al repository `claudioterzi/Claudio`, branch `main`. La root directory
è vuota, build `pip install -r integrations/raffaello-bot/requirements.txt`,
avvio `cd integrations/raffaello-bot && exec python -m bot.main`. Non semplificare
i comandi senza impostare anche la root directory. Il filtro Included Paths
`integrations/raffaello-bot/**` è salvato: le modifiche al solo sito non devono
riavviare il bot.

Il primo deploy del nuovo runtime è fallito perché la lista dei vecchi handler
include anche CommandHandler, che non hanno `fallbacks`. La PR 36 applica
l'inserimento del fallback /nuovo ai soli ConversationHandler e aggiunge una
regressione d'avvio. Il deploy successivo è risultato Live. La health ha risposto
HTTP 200 con versione `2.0.0`, `bridge_configured: true` e commit
`06f8795f971b6d091478ac8fe379916c7681a4ef`.
Anche il deploy successivo al salvataggio della credenziale Vercel,
`dep-dairnutg1s2s738gqctg`, è risultato Live nel pannello Render.

Vercel Production sullo stesso commit è READY, deployment
`dpl_Ch32WrznjqvG4p7rJQ21D1JruDUa`. La route `/api/raffaello/status`, verificata
tramite accesso Vercel autenticato, risponde HTTP 200 con `configured: true`.
Queste verifiche provano avvio e presenza della configurazione, non la consegna
di un messaggio Telegram né la risposta del provider AI.

Il piano è Free, senza disco persistente né accesso shell. I percorsi configurati
sono `protocollo.db` e `protocollo.persistence`, entrambi relativi.

Durante questa verifica Claudio ha autorizzato esplicitamente a eliminare i vecchi
registri e ripartire da zero. Il backup dei vecchi dati non blocca più il passaggio;
questa autorizzazione non equivale a una cancellazione già eseguita. Non autorizza
un abbonamento aggiuntivo o la perdita programmata delle nuove letture. Render Free
perde i file locali a riavvio, redeploy e sospensione per inattività; il piano
minimo a pagamento mostrato dal pannello è 7 USD/mese, più eventuale disco.
La sospensione dopo 15 minuti senza traffico in ingresso ferma inoltre il polling:
un messaggio Telegram non risveglia da solo un servizio che riceve tramite polling.
Non sono stati acquistati servizi né configurati ping artificiali per mantenerlo
acceso. Questo piano è adatto al collaudo, non alla continuità promessa per il diario.

Corretta anche la registrazione delle richieste Telegram: INFO/DEBUG dei trasporti
sono disabilitati e il formatter oscura i token anche nelle eccezioni. Nessuna
chiave reale è stata aggiunta al codice o alla documentazione.

La verifica diretta `getMe`, con il token fornito da Claudio e corrispondente a
quello del servizio Render, identifica il bot `@ProtocolloRossoBot` (ID
`8900249704`, nome visibile «Protocollo Rosso»). `getWebhookInfo` conferma assenza
di webhook e zero aggiornamenti in attesa al momento del controllo. Queste
richieste non hanno inviato messaggi né modificato il ricevitore Telegram.
I due collegamenti della pagina `/dialogo-raffaello` ora usano questo username
verificato: il nome indicato in precedenza portava a un altro bot. Il token non è
salvato nel repository. Il nuovo runtime si avvia; l'abilitazione personale e il
collaudo completo restano da completare.

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
Per i limiti del piano corrente: [Render Free](https://render.com/docs/free).
