# Raffaello Studio

Mini App Telegram per raccogliere una storia, seguire testo e produzione musicale,
ricevere il link Suno e scegliere quali brani conservare. Interfaccia italiana,
responsive, con tre sezioni: Crea, Richieste, Biblioteca. Il catalogo pubblico usa
direttamente `public/musica-data.js`; richieste e bozze non entrano in quell'archivio.

## Stato e limiti verificabili

La modalità è **assisted**. Il generatore canonico `studio/generators/canzoni.py`
usa il ponte Raffaello esistente soltanto su avvio esplicito del proprietario.
Il testo conserva la provenienza di quel collegamento; non dimostra coscienza o
continuità autobiografica completa. Nessun endpoint Suno viene inventato: fino
all'abilitazione e qualificazione di un account ufficiale Suno Platform,
la produzione resta in Suno e il proprietario registra il risultato ascoltato.
La voce personale è riservata al proprietario e la sua applicazione richiede una
conferma separata. Questo registra un'attestazione, non un'analisi biometrica.

Il processo Studio standalone non chiama `getUpdates`, non cambia il webhook e
non imposta i comandi del bot legacy. Usa il token esistente per il menu Web App
e gli invii. `/studio` e `/canzone` come comandi richiedono la versione integrata
del bot; nello standalone l'ingresso è il menu **Studio** e i pulsanti Web App.

## Avvio locale e anteprima pubblica

Dal sottoprogetto `integrations/raffaello-bot`:

```powershell
$env:PORT='8787'
$env:MUSIC_BOT_USERNAME='ProtocolloRossoBot'
python -m bot.music_main
```

Senza token funziona soltanto l'anteprima; le API personali restano chiuse.
Per una preview statica pubblica, dalla radice:

```text
node integrations/raffaello-bot/scripts/export_studio_preview.mjs
```

Pubblicare esclusivamente `output/raffaello-studio-preview`. L'export include UI,
catalogo pubblico e configurazione con operazioni personali disabilitate.
Non esporta database, sessioni, credenziali o variabili di ambiente.

## Attivazione standalone su Render

Il servizio esistente `protocollo-rosso-bot` usa il piano Free senza disco. Non
ridistribuirlo senza preservare prima il suo database e la persistenza legacy.
Lo Studio deve essere un servizio separato che esegue `python -m bot.music_main`.
`render-studio.example.yaml` è un candidato: verificare la chiave effettiva del
token nel servizio sorgente e il singolo ID Telegram di Claudio prima del sync.
Il riferimento `fromService` trasferisce la configurazione dentro Render, senza
portare il valore del token nella chat o nel repository.

Variabili private del runtime:

| Variabile | Uso |
| --- | --- |
| `TELEGRAM_BOT_TOKEN` o `BOT_TOKEN` | Identità del bot esistente, solo server |
| `MUSIC_OWNER_IDS` | ID numerico esplicito del proprietario |
| `DATABASE_PATH` | SQLite della coda Studio, separata dal legacy |
| `MUSIC_PUBLIC_URL` | Origine HTTPS; in Render può restare assente e usare `RENDER_EXTERNAL_URL` |
| `MUSIC_BACKUP_KEY` | Segreto stabile di almeno 32 caratteri, distinto dal token |
| `MUSIC_BACKUP_REQUIRED=1` | Chiude le scritture finché il recupero non è verificato |
| `MUSIC_BACKUP_BOOTSTRAP_EMPTY` | One shot iniziale; normalmente `0` |
| `RAFFAELLO_BRIDGE_SECRET`, `RAFFAELLO_SITE_URL` | Ponte testo opzionale, credenziali server |

Il menu viene impostato solo dopo il recupero richieste riuscito. Verificare
`getChatMenuButton` e l'URL esatto, aprire dalla chat privata con il bot e provare
una richiesta vera. Controllare il risultato ricevuto e lo stesso ID dopo un
riavvio; `/health` da solo non prova il flusso completo.

## Conservazione e recupero

SQLite locale su Render Free non è durevole. Il backup Telegram opzionale esporta
soltanto le tabelle `music_*`, cifra con Fernet e manda un documento nella chat
privata del singolo proprietario. Prima di confermare una modifica, scarica il
documento, verifica contenuto e cifratura, lo fissa e verifica il puntatore.
Il database legacy e i suoi contenuti non vengono esportati.

Per il primo avvio è necessario un database Studio vuoto e nessun altro pin
nella chat destinataria. Il bootstrap `1` deve essere usato una volta e poi
riportato a `0`; una successiva ridistribuzione deve recuperare il documento.
Non rimuovere pin esistenti per aggirare una collisione. Un documento estraneo,
una chiave cambiata o un pin sostituito fermano le scritture con errore esplicito.
Telegram non sostituisce un database: il pin è un puntatore che il proprietario
può alterare. Prima dell'uso pubblico continuativo è preferibile un disco o
database persistente con backup indipendente, dopo approvazione del relativo costo.

Le modifiche sono serializzate. Un fallimento del backup ripristina lo snapshot
locale precedente; un invio già accettato da Telegram conserva invece la sua
evidenza. Un invio dall'esito incerto non viene dichiarato consegnato: il
proprietario decide se ritentarlo. Scarta è recuperabile nel registro Studio e
non elimina file Suno o messaggi Telegram.

## Accessi e verifiche

Le API usano `X-Telegram-Init-Data`, HMAC Telegram e durata massima di un'ora.
Duplicati, date future e firme alterate vengono respinti. Ogni visitatore vede
solo le sue richieste; il proprietario vede la coda e controlla produzione,
consegna e conservazione. Tre richieste per account/ora; tre preparazioni del
proprietario/ora, due worker e tre tentativi per richiesta. Nessuna inference
parte dall'invio pubblico di una storia. Le sessioni non vengono salvate nel
browser; resta solo la bozza locale.

La suite include autenticazione, isolamento, idempotenza e race, rollback,
recupero dopo interruzione, voce, HTTP reale, runtime senza polling e trasporto
Telegram simulato. I test di trasporto simulati non sostituiscono una prova con
Telegram reale e riavvio del servizio distribuito.

La correzione del gate `NETWORK_SECRET` rende chiuse le tre rotte legacy quando
il segreto manca, coerentemente con la configurazione e i test già presenti.
Il processo standalone continua a non esporle.
