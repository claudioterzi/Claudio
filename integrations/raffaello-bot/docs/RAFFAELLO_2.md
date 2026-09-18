# Raffaello 2 · Rosso Rosso Rosso

Claudio Terzi · C.Terzi · 12 settembre 2026

## Implementazione

Il testo libero prepara una domanda e mostra **Analizza**. Il modello viene
invocato soltanto dal pulsante. La risposta usa il motore del sito, con la lettura
selezionata oppure la cronologia recente del dialogo libero. Nessuna classificazione
per parole come «non funziona» devia più la richiesta verso frasi filosofiche.

**/letture** recupera le letture personali; **/nuovo** apre un nuovo dialogo e
interrompe gli eventuali percorsi guidati precedenti; **/collega** genera un codice
monouso di 64 bit valido 10 minuti; **/scollega** revoca le sessioni web. Il sito
conserva la credenziale in un cookie HttpOnly/Secure/SameSite=Strict: nessun token
personale negli URL. Username e ID ricevuti dal browser non concedono accesso.

Il sito invia la lettura solo dopo **Continua su Telegram**. L'archivio deriva i
significati dalle 74 carte canoniche, rifiuta direzioni/polarità mancanti e mantiene
immutabile il contesto iniziale. Una nuova estrazione resta una nuova lettura.
L'interpretazione importata è contenuto proveniente dal sito, non una prova di fatti.
La copia del canone in `bot/data/alpha74.json` è identica a
`claudioterzi/Claudio:tarocchi_quantici_alpha.json`; il test fra repository verifica
questa uguaglianza. Non contiene immagini.

La pagina `/dialogo-raffaello` presenta la stessa lettura, le domande e le risposte
recenti. Carica le miniature esistenti da 160 px e il dettaglio da 640 px soltanto
al tocco, rispettando l'orientamento. **Ascolta sul sito** apre la lettura/risposta;
la voce del browser parte solo dopo il tocco su **Ascolta**. Nessun file audio
pesante viene memorizzato e nessun servizio vocale a pagamento è aggiunto.

Le tabelle `r3_*` si aggiungono al database esistente. Azioni, esiti, testimoni,
possibilità e altri registri restano nelle loro tabelle. Le generazioni usano ID
stabili, risultato riutilizzabile, lock per proprietario e limite di 30 tentativi
all'ora. Un errore mantiene la domanda riprovabile, senza salvare una falsa risposta.
Il contesto inviato al modello è limitato; la pagina mostra gli ultimi 30 scambi.
I record precedenti restano nel database. Dopo un crash durante una chiamata esterna,
il recupero di un lock scaduto (180 secondi) può ripetere la chiamata al provider:
non si dichiara una garanzia di fatturazione «exactly once».

## Configurazione per attivare il servizio esistente

La pubblicazione del codice non equivale all'attivazione del bot su Render.
Prima del passaggio occorre verificare repository/branch effettivo, identità del
bot con `getMe`, disco persistente e percorso reale dei registri. Non avviare un
secondo ricevitore con lo stesso token. Un webhook esistente ora blocca l'avvio del
polling, invece di essere cancellato automaticamente.

| Ambiente | Variabile | Scopo |
| --- | --- | --- |
| Render | `TELEGRAM_BOT_TOKEN` oppure `BOT_TOKEN` | Token del bot esistente |
| Render | `DATABASE_PATH`, `PERSISTENCE_PATH` | Percorsi dei registri sul disco persistente già verificato |
| Render | `RAFFAELLO_ALLOWED_USERS` | ID numerici Telegram autorizzati, separati da virgole |
| Entrambi | `RAFFAELLO_BRIDGE_SECRET` | Lo stesso segreto casuale, almeno 32 caratteri |
| Render | `RAFFAELLO_SITE_URL` | `https://claudio-ebon.vercel.app` |
| Render, se il sito è protetto | `RAFFAELLO_VERCEL_BYPASS_SECRET` | Credenziale Vercel per l'automazione, conservata soltanto sul server |
| Vercel | `RAFFAELLO_BOT_URL` | URL HTTPS del servizio Render verificato |
| Vercel | `GOOGLE_API_KEY`/`GEMINI_API_KEY` o `ANTHROPIC_API_KEY` | Provider già usati dal sito |
| Render e peer di rete, se usati | `NETWORK_SECRET` | Ora obbligatorio per `/ask` e `/network/v1/*` |

Il ponte rifiuta richieste senza segreto, proprietari non abilitati, sessioni
scadute, payload eccessivi e accessi a letture altrui. Non segue redirect HTTP con
credenziali. La protezione Vercel e la Soglia del sito restano attive.
Per la prima abilitazione, `/start` in una chat privata non autorizzata mostra
l'ID numerico dell'utente che ha scritto. Inserire quell'ID in
`RAFFAELLO_ALLOWED_USERS`: il messaggio non concede accesso, non avvia analisi
e non mostra identificativi di altre persone.
La [credenziale Vercel per automazioni](https://vercel.com/docs/deployment-protection/methods-to-bypass-deployment-protection/protection-bypass-automation)
consente l'accesso del servizio alla funzione protetta; non va messa nel browser.

Eseguire un backup consistente prima della migrazione, usando i percorsi reali:

```sh
python scripts/backup_raffaello.py /percorso/protocollo.db /backup/protocollo-prima-r3.db
```

Copiare anche la persistenza dei ConversationHandler con il processo fermo.
Non puntare `DATABASE_PATH` a un nuovo file vuoto per «risolvere» un errore di
migrazione. In caso di rollback, il codice precedente può aprire lo stesso SQLite:
le nuove tabelle sono additive. Il backup conserva il punto precedente.
Il [filesystem dei servizi Render Free](https://render.com/docs/free#free-web-services)
non garantisce questa persistenza: il piano live non è stato accertato.

## Verifiche riproducibili

```sh
python -m pytest -q
```

Nel checkout del sito, con il bot e le sue dipendenze disponibili:

```sh
R3_BOT_CHECKOUT=/percorso/protocollo-rosso-bot python -m unittest tests.test_raffaello_roundtrip -v
python -m unittest tests.test_raffaello_bridge tests.test_alpha_web tests.test_tarot_alpha_follow_up
node tests/test_alpha74_frontend.cjs
```

Il collaudo fra repository usa SQLite reale, server HTTP del bot e route Flask del
sito: collegamento → importazione → domanda Telegram → risposta → riapertura sul
sito → seconda domanda → stessa cronologia e stesse carte. Solo provider AI e
trasporto verso gli host pubblici sono sostituiti. Non è un collaudo Telegram live.
Sono verificati anche isolamento fra account, codice monouso/scadenza/revoca,
immutabilità, ripetizioni, lock concorrenti, errore del provider, riapertura del
database e conservazione dei vecchi registri.

La health `/raffaello/health` espone versione e `RENDER_GIT_COMMIT` quando presente.
`bridge_configured` indica configurazione presente, non raggiungibilità verificata.
La health non prova ricezione o consegna Telegram.

Atelier e Fabbrica restano accessibili dal sito: il dialogo può sviluppare idee,
ma questa versione non crea automaticamente progetti in quegli archivi. Ingresso
vocale, trascrizione e audio nativo Telegram non sono implementati.
