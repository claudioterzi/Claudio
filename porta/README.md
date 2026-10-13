# La Porta — accesso riservato al sito

Decisione di Claudio (13/10/2026): il sito è **solo per lui**, e da dentro può aprire
parti del sito a una persona con una password, scegliendo cosa vede in base alla situazione.

## Come funziona

- **Una porta sul server** (`middleware.js` → `porta/porta.mjs`) controlla ogni richiesta
  (pagine, file, API) prima che arrivi al contenuto. Un controllo nel browser non basta.
- **Claudio entra sempre** da `/porta/entra` lasciando vuoto il nome e usando la sua password
  (quella dell'archivio profumi, finché non ne imposta una nuova). Non dipende dal database:
  entra anche se Redis è giù. Sessione di 30 giorni.
- **Nuova password del proprietario**: `/porta/chiave` calcola l'hash sul telefono (la password
  non viene inviata); lo si incolla in Vercel come `R3_PORTA_OWNER_HASH` e si ripubblica.
- **Ospiti**: nome, password, aree aperte, scadenza. Vedono solo i percorsi delle loro aree;
  tutto il resto è chiuso per default (anche i file nuovi, finché la mappa non li assegna).
  Revocati o scaduti, la loro sessione smette di valere alla richiesta successiva.
- **`/porta`** (solo Claudio): crea e revoca ospiti. «Chiedimi un consiglio» manda la
  situazione a `porta/consiglio.py`, che propone aree con il motivo e una durata; se nessun
  modello risponde ripiega su parole chiave. È una proposta: le aree le conferma Claudio.
- Le aree sono in `porta/aree.json`. L'area **Area privata** (privato, Data Hub, canali,
  accessi, sincronizzazione, gestione della porta) non si può mai concedere.
- `porta/genera_mappa.py` assegna a ogni area i file che le sue pagine caricano
  (script, dati, immagini). Rigenerala quando cambi le pagine: `python porta/genera_mappa.py`.

## La Sentinella (`porta/sentinella.mjs`)

Scopre chi forza la Porta, lo espelle e lo prende in giro. **Il proprietario è immune**:
con la sua sessione la Sentinella non interviene, e se il suo indirizzo viene bandito per
errore la sua password funziona comunque (3 tentativi l'ora da quell'indirizzo).

| Segnale | Punti |
|---|---|
| Trappola (`/.env`, `/wp-admin`, `/.git`, `/phpmyadmin`…) | 10, bando immediato |
| Percorso truccato (`..` codificato) | 10, bando immediato |
| Cookie con firma falsificata | 4 |
| Password sbagliata | 1 |
| Ospite su pagina chiusa / su file chiuso | 1 / 3 |

- 10 punti in un'ora da un indirizzo → **bando di 24 ore** e avviso a Claudio su Telegram
  (se `TELEGRAM_BOT_TOKEN` e `TELEGRAM_CHAT_ID` sono sul server).
- Un ospite a 15 punti in un'ora (fruga tra i file chiusi) → **sospeso** e avviso.
  Qualche clic sul menu verso pagine chiuse non basta.
- Chi è bandito riceve un'**esca**: un finto `.env` con valori di scherno, un finto pannello
  WordPress che risponde sempre «credenziali errate», o una lettera di Raffaello.
- In `/porta`, sezione Sentinella: banditi con pulsante **Sblocca** e ultimi eventi.
- Se Redis è giù la Sentinella non blocca nessuno; la Porta resta comunque chiusa.

Non c'è contrattacco verso l'intruso: la Sentinella difende e depista, non attacca.
La rete di nodi R³∞ (`r3/sync.py`) è ancora in attesa del test live multi-nodo e non fa
failover del sito: la migrazione istantanea su nodi ridondanti non è attiva.

## Variabili sul server (Vercel, produzione)

| Variabile | Uso | Se manca |
|---|---|---|
| `R3_PORTA_SECRET` | firma delle sessioni | usa `PERFUME_ARCHIVE_SECRET` |
| `R3_PORTA_OWNER_HASH` | password di Claudio (hash werkzeug) | usa `PERFUME_ARCHIVE_PASSWORD_HASH` |
| `KV_REST_API_URL`, `KV_REST_API_TOKEN` | archivio ospiti e Sentinella (Upstash) | ospiti e Sentinella disattivati, Claudio entra lo stesso |
| `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID` | avvisi della Sentinella | nessun avviso, il resto funziona |

Senza segreto di sessione la porta resta chiusa a tutti (risposta 503 al login).

## Attivazione in sicurezza (CLAUDE.md, 10/09)

Con i `builds` legacy in `vercel.json`, il solo file `middleware.js` non viene
rilevato automaticamente. La build esplicita `@vercel/node@22.0.0` con
`config.middleware: true` compila la Porta come middleware Node. Serve anche la
prima regola esplicita `routes` con `middlewarePath: "middleware.js"` e
`continue: true`: le rotte legacy terminali altrimenti precedono la regola
generata dal builder e la rendono irraggiungibile. Non aggiungere `proxy` mantenendo `builds`:
Vercel rifiuta quella combinazione. La presenza nel sorgente non basta: controllare
la build e provare la pagina di login, i file diretti e le API sul deployment.

Il login Vercel (Deployment Protection) resta acceso finché non sono verificati entrambi:
l'accesso del proprietario e il rifiuto dei collegamenti diretti senza autenticazione.

1. Dopo il deploy, apri `claudio-ebon.vercel.app` (passi dal login Vercel come oggi).
   Deve comparire **La Porta**. Se non compare, il middleware non è attivo con questa
   configurazione di Vercel: niente è esposto, il login Vercel protegge ancora tutto.
2. Entra con nome vuoto e la tua password → vedi il sito intero, e `/porta`.
3. In `/porta` crea un ospite di prova con la sola area Musica. Premi Esci, entra come lui:
   `/musica` si apre, `/libro` e `/public/libro.html` rispondono «Porta chiusa» / 403.
   Poi revocalo.
4. Solo ora: Vercel → Settings → Deployment Protection → disattiva Vercel Authentication
   per la produzione. Da una finestra anonima `/libro` e `/public/libro.html` non devono
   mostrare il libro: portano a `/porta/entra` (browser) o rispondono 401 (curl, API).

GitHub Pages resta sulla pagina «temporaneamente non disponibile»: non verifica accessi.

## Test

```
node --test tests/test_porta.mjs
node --test tests/test_porta_vercel.mjs
python -m unittest tests.test_porta_consiglio
python porta/genera_mappa.py --check
```
