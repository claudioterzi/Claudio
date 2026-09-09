# Indice verificato del sito Claudio

Scansione: **2026-09-09T10:01:35.368858+00:00**. Repository unico: `Claudioterzi/Claudio`.

## Perimetro ed esito

Analizzate le **16 pagine HTML** presenti in `public/`, i relativi alias configurati in `vercel.json` e le pagine interne aggiuntive individuate nei collegamenti. **26 percorsi distinti** controllati via GET, tutti HTTP 200. Il percorso `/profumo` senza parametri è una risposta di servizio minimale. Gli alias sono conteggiati come percorsi, non come nuove pagine.

Controllati inoltre due script condivisi e tre API di sola lettura: quattro risorse HTTP 200 e una HTTP 404. **Canone Alpha ha una dipendenza guasta**, benché la pagina si apra.

Il controllo comprende HTML, titoli, intestazioni, collegamenti, form e dipendenze nel sorgente. Non comprende esecuzione JavaScript, prove visive su iPhone/Safari, invio form, comandi Telegram, caricamento foto, acquisti o generazioni AI. Non certifica il funzionamento completo delle interfacce. I siti esterni e tutte le combinazioni di parametri non sono stati scanditi. Le descrizioni dei cataloghi riportano ciò che le pagine dichiarano; non costituiscono validazione scientifica o conteggio indipendente di ogni scheda.

## Pagine principali

| Pagina | Area | Funzione | Esito e dipendenze |
|---|---|---|---|
| [Tarocchi Quantici — Canone Alpha](https://claudio-ebon.vercel.app/alpha.html) | Simboli | Canone originale: carta, asse e polarità; esplorazione degli stati. | HTTP 200. GET /api/alpha: 404. /api/alpha/collasso referenziato nello script; non provato. |
| [L'Atelier di Raffaello — Terzi Parfums](https://claudio-ebon.vercel.app/atelier.html) | Profumi | Composizione didattica offline e apertura del generatore AI dall’intenzione. | HTTP 200. Naviga a /profumo?q=…; generazione non attivata in questa scansione. |
| [Le Creazioni — Catalogo del progetto Claudio](https://claudio-ebon.vercel.app/creazioni.html) | Indice | Catalogo generale dei sistemi e collegamenti ai luoghi del progetto. | HTTP 200. Include sito, Custode, repository e GitHub Pages. |
| [Flight Hunter](https://claudio-ebon.vercel.app/flight_hunter.html) | Viaggi | Ricerca mete e rotte con mese, budget e raggio. | HTTP 200. POST /api/flight/ovunque e /api/flight/caccia; non inviati. |
| [SDQ-1 — Agorà](https://claudio-ebon.vercel.app/home.html) | Sistema | Agorà SDQ-1: consiglio e comandi rapidi per Telegram. | HTTP 200. Telegram WebApp SDK e sendData; comandi non inviati. Gli stati visualizzati non sono un health check verificato. |
| [Tarocchi Quantici R³∞](https://claudio-ebon.vercel.app/index.html) | Simboli | Mazzo tradizionale e lettura strutturale/personale della stesa. | HTTP 200. GET /api/mazzo: 78 carte; POST /api/leggi non inviato. |
| [Parfums 400 — Il Libro · Terzi Parfums](https://claudio-ebon.vercel.app/libro.html) | Profumi | Libro stampabile: storia, metodo, organo e schede dei profumi. | HTTP 200. Contenuto HTML; resa di stampa non verificata. |
| [La Grande Opera — Archivio Cosmico R³∞](https://claudio-ebon.vercel.app/opera.html) | Archivio | Grande Opera: archivio che dichiara 101 documenti e 100 fasi. | HTTP 200. Contenuto/interfaccia nel documento; singoli documenti incorporati non verificati separatamente. |
| [Tarocchi Quantici — Manifesto A6](https://claudio-ebon.vercel.app/opuscolo.html) | Simboli | Manifesto A6 del Canone Alpha, navigazione e stampa. | HTTP 200. Contenuto HTML; pulsanti e stampa non eseguiti. |
| [L'Oracolo del Viaggio](https://claudio-ebon.vercel.app/oracolo.html) | Viaggi | Suggerimenti di partenze imminenti dalla città scelta. | HTTP 200. POST /api/flight/oracolo; non inviato in questa scansione. |
| [Organo Terzi 300 — le materie prime](https://claudio-ebon.vercel.app/organo.html) | Profumi | Catalogo delle materie, con filtri per famiglia, nota e ondata. | HTTP 200. Dati/interfaccia nel documento; filtri non eseguiti. |
| [Parfums 400 — Il Codice Olfattivo](https://claudio-ebon.vercel.app/parfums.html) | Profumi | Catalogo dei 400 profumi in otto famiglie. | HTTP 200. Dati/interfaccia nel documento; filtri non eseguiti. |
| [Parti — voli assurdi](https://claudio-ebon.vercel.app/parti.html) | Viaggi | Occasioni di volo dalla città, con posizione e preferenze locali. | HTTP 200. POST /api/flight/occasioni; localStorage; geolocalizzazione non attivata. |
| [La Dispensa — lista della spesa e calcoli del banco](https://claudio-ebon.vercel.app/spesa.html) | Profumi | Dispensa: acquisti, consumi, quantità e lista CSV. | HTTP 200. localStorage del browser; nessuna sincronizzazione verificata; export non eseguito. |
| [La Valigia-Organo — Terzi Parfums](https://claudio-ebon.vercel.app/valigia.html) | Profumi | Mappa dei moduli e progetto della valigia per le materie. | HTTP 200. 293 boccette + 7 solventi/consumabili separati: compatibile con Organo 300. |
| [Viaggi Low Cost](https://claudio-ebon.vercel.app/viaggi.html) | Viaggi | Pianificatore per città, budget, durata, mese e tipo di viaggio. | HTTP 200. POST /api/viaggi/pianifica; catalogo destinazioni GET disponibile. Volo A/R stimato come andata ×2. |

Il sorgente di ogni pagina è `public/<nome>.html`; la corrispondenza esatta è nel [JSON](SITE_INDEX.json).

## Alias e pagine aggiuntive

| Percorso | Destinazione o ruolo | HTTP |
|---|---|---|
| [/](https://claudio-ebon.vercel.app/) | /index.html | 200 |
| [/alpha](https://claudio-ebon.vercel.app/alpha) | /alpha.html | 200 |
| [/custode/](https://claudio-ebon.vercel.app/custode/) | Catalogo, inventario, schede manuali e da foto; custode/web.py | 200 |
| [/flight](https://claudio-ebon.vercel.app/flight) | /flight_hunter.html | 200 |
| [/home](https://claudio-ebon.vercel.app/home) | /home.html | 200 |
| [/oracolo](https://claudio-ebon.vercel.app/oracolo) | /oracolo.html | 200 |
| [/parti](https://claudio-ebon.vercel.app/parti) | /parti.html | 200 |
| [/profumo](https://claudio-ebon.vercel.app/profumo) | Senza q mostra istruzioni; con intenzione avvia la generazione; tarocchi_web.py | 200 |
| [/prova](https://claudio-ebon.vercel.app/prova) | Pagina di chiusura dell’Atelier; tarocchi_web.py | 200 |
| [/viaggi](https://claudio-ebon.vercel.app/viaggi) | /viaggi.html | 200 |

## Dipendenze verificate

| Risorsa | Esito |
|---|---|
| `/nav.js` | HTTP 200  |
| `/soglia.js` | HTTP 200  |
| `/api/mazzo` | HTTP 200 JSON valido; 78 carte |
| `/api/alpha` | HTTP 404  |
| `/api/viaggi/destinazioni` | HTTP 200 JSON valido |

Le API POST di lettura tarocchi, atelier e viaggi sono inventariate nel JSON e nelle righe delle pagine, ma non invocate in questa scansione. Il collasso Alpha usa un URL costruito nello script. I percorsi Telegram sono servizi tecnici e non pagine: non sono stati interrogati. Custode ha anche azioni POST `/custode/inventario`, `/custode/schedatura`, `/custode/scheda`, non inviate.

## Problemi e interventi prioritari

- **F01 · priorità alta** — Canone Alpha: pagina HTTP 200, GET /api/alpha HTTP 404; caricamento carte bloccato. Prossimo intervento: Ripristinare endpoint del canone e verificare anche il collasso.
- **F02 · priorità alta** — Custode mostra avviso di archivio temporaneo e apre il catalogo senza autenticazione nella richiesta effettuata. Prossimo intervento: Verificare persistenza e controllo accessi prima di catalogare dati reali.
- **F03 · priorità media** — La Dispensa salva solo nel browser tramite localStorage. Prossimo intervento: Esportare CSV per conservare una copia; progettare sincronizzazione tra dispositivi.
- **F04 · priorità media** — /prova risponde 200 ma mostra la chiusura dell’Atelier, senza collegamenti di recupero. Prossimo intervento: Valutare collegamento o redirect verso /atelier.html.
- **F05 · priorità media** — /profumo senza intenzione restituisce solo istruzione testuale, senza titolo o viewport. Prossimo intervento: Aggiungere una pagina di ingresso con campo intenzione e navigazione.
- **F06 · priorità bassa** — La navigazione condivisa comprende 15 voci: non comprende Agorà né Custode. Prossimo intervento: Valutare un punto di ingresso completo; verificare evidenziazione attiva degli alias brevi.

## Uso su iPhone e conservazione dei dati

Tutte le 16 pagine HTML dichiarano il viewport mobile, così come Custode e la pagina di chiusura. Questo è un prerequisito, non una prova di buona resa su Safari. Restano da provare scorrimento delle tabelle, menu, filtri, tastiera nei form, download CSV, copia negli appunti, stampa, fotocamera e geolocalizzazione.

La Dispensa conserva spunte e scarichi nel localStorage del browser: cambiare browser/dispositivo o cancellare i dati del sito può farli apparire scomparsi. Il CSV è una copia esportata, non una sincronizzazione. Custode dichiara esplicitamente che le schede si perdono al riavvio: la persistenza va risolta prima di usarlo come archivio stabile.

Agorà usa il ponte Telegram WebApp per inviare comandi; l’apertura in Safari non dimostra che il bot riceva il comando. Le etichette “Attivo” e l’attività recente nell’HTML non attestano lo stato reale degli agenti.

## Lettura corretta dei risultati di viaggio

`viaggi.html` dichiara 25 mete e usa, dove disponibile, il prezzo live della sola andata moltiplicato per due come stima A/R. Alloggio, pasti e trasporti sono stime con margine; non è il prezzo verificato di due biglietti acquistabili. Le pagine Parti, Flight Hunter e Oracolo dipendono dalle fonti di volo attive e richiedono prove specifiche dei form per verificare i risultati.

## Manutenzione dell’indice

Per aggiornare: enumerare `public/*.html`, leggere `vercel.json` e le rotte Flask/Blueprint, normalizzare i link sullo stesso dominio, interrogare con GET pagine e dipendenze di lettura, quindi registrare data, stato e limiti. Deduplicare `/` e l’URL senza percorso. Tenere separate raggiungibilità HTTP e verifica delle interazioni. Non invocare automaticamente endpoint che generano contenuti, modificano dati o inviano messaggi.

Questo aggiornamento salva la fotografia verificata e le priorità; non applica le correzioni funzionali elencate. Il [JSON dell’indice](SITE_INDEX.json) contiene collegamenti, form, script e metadati per successive verifiche.
