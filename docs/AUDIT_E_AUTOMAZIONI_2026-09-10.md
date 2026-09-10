# Sito Claudio Terzi — verifica e automazioni

Progetto di **Claudio Terzi · C.Terzi**. Verifica tecnica: 10 settembre 2026.
Questo documento distingue risultati osservati, interventi realizzati e lavoro successivo.

## Un solo ingresso riconoscibile

- Home: https://claudio-ebon.vercel.app/
- Soglia, anche per un browser già entrato: https://claudio-ebon.vercel.app/soglia
- Tutti i progetti: https://claudio-ebon.vercel.app/progetti
- Libro: https://claudio-ebon.vercel.app/libro.html
- Fabbrica: https://claudio-ebon.vercel.app/fabbrica

La home serve il catalogo dei progetti; la pagina Tarocchi resta raggiungibile come
`index.html`. La Soglia originale resta un ingresso scenografico nel browser,
non un sistema di autenticazione per informazioni riservate.

Il link `claudio-62rs9kwhv-claudio-terzi-s-projects.vercel.app` indicato da Claudio
ha il formato di un indirizzo legato a una singola pubblicazione. Questi indirizzi
non seguono gli aggiornamenti del dominio di produzione, come spiega la
[documentazione Vercel](https://vercel.com/docs/deployments/generated-urls).
Il confronto pubblico del 10 settembre rimanda quel link al login Vercel; non è
stato possibile leggere il suo libro o accertare la data della versione.
L'API Vercel restituisce **403: account da riautenticare per il team del progetto**.
Non è quindi stata cancellata quella pubblicazione. Non sono stati aggirati i
controlli di accesso. Le future anteprime mostrano un collegamento al sito stabile;
questa modifica non può riscrivere una pubblicazione storica già esistente.

## Perché la Fabbrica sembrava scomparsa

Prima della correzione, `/fabbrica.html` rispondeva 200 con la pagina completa,
mentre `/fabbrica` e `/fabbrica-dei-desideri` restituivano 404. Il percorso breve
arrivava alla funzione Python, che cercava l'HTML nel proprio pacchetto, mentre
Vercel distribuisce `public/` come contenuto statico separato. La configurazione
non includeva l'HTML nel pacchetto Python. La pagina non era stata eliminata.

Correzione pubblicata: instradamento esplicito dei due indirizzi verso la risorsa
statica. Commit `1db30ee05c89091baba3bcceca347f191fa7a07c`.
Verificati successivamente quattro indirizzi, tutti 200 con contenuto identico:
`/fabbrica`, `/fabbrica/`, `/fabbrica-dei-desideri`, `/fabbrica.html`.
L'API di stato confermava archivio e configurazione IA disponibili. Non è una prova
di prenotazioni, chiamate o di una nuova generazione a pagamento.

## Estensione dell'analisi

Controllate tutte le **21 pagine HTML pubbliche**, titoli, collegamenti e risorse
statiche, sintassi di 19 script esterni prima delle aggiunte e 14 script inline.
Tutte le 21 pagine rispondevano HTTP 200; nessuna risorsa statica referenziata
mancava nell'analisi locale. Campionati solo endpoint GET esplicitamente sicuri.
Non sono stati scandagliati archivi privati, inviati messaggi o eseguiti acquisti.
Questa verifica non equivale al collaudo completo di ogni funzione di ogni progetto.
Non sono state misurate Core Web Vitals né simulati utenti su diversi dispositivi.

## Interventi implementati

| Meccanismo | Comportamento | Limite concreto |
|---|---|---|
| Controlli rigorosi GitHub | Verifica pagine, risorse, JavaScript, indirizzi e test funzionali; un errore fa fallire il controllo | Il vecchio workflow di sicurezza resta informativo; non è stato dichiarato certificazione |
| Monitor di produzione | Pagine, alias e quattro API sicure, dopo una pubblicazione riuscita e con pianificazione ogni 15 minuti | Gli orari GitHub sono indicativi, non una garanzia di disponibilità |
| Riparazione degli indirizzi | Ripristina esclusivamente i percorsi elencati nel registro e conserva tutte le altre regole | Non riscrive applicazioni né corregge indiscriminatamente qualsiasi errore |
| Foto dei profumi | Numero esplicito P001–P400, nuova foto principale, rigenerazione del libro, conservazione delle versioni | Parte quando un file viene importato nel progetto; non sorveglia telefono o altre app |
| Flaconi | 400 illustrazioni individuali, collegate alle formule tramite impronta verificabile | Concept estetici, non disegni di produzione industriale |
| Diagnostica Fabbrica | Evento, classe d'errore, endpoint e durata delle richieste fallite | Nessun testo privato, cookie o token nei nuovi log; accesso ai log Vercel ancora limitato |
| Diagnostica Telegram | GET restituisce solo stato della configurazione | Non invia più messaggi e non dichiara la connessione verificata |
| Report CI | Conservati come allegati delle esecuzioni | Eliminato il commit di solo timestamp che poteva causare pubblicazioni inutili |

Il monitor usa `config/site_monitor.json`, `scripts/site_monitor.py` e
`.github/workflows/site_health.yml`; le foto usano `.github/workflows/flaconi_foto.yml`.
Non cancella dati e non fa rollback autonomi. I report delle esecuzioni sono
conservati per 30 giorni negli allegati GitHub. Le notifiche dipendono dalle
preferenze GitHub già configurate; nessun destinatario aggiunto.

GitHub può ritardare i cron e disabilita quelli di repository pubblici dopo 60 giorni
senza attività: per un servizio commerciale serve un monitor indipendente con
livello di servizio concordato. [Regole GitHub](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows#schedule).

## Strategia: ridurre davvero il lavoro manuale

| Priorità | Prossimo intervento | Risultato verificabile |
|---|---|---|
| 1 | Collegare i controlli GitHub ai Deployment Checks Vercel | Una nuova versione non riceve il dominio principale se fallisce un controllo richiesto |
| 1 | Backup automatici indipendenti di dati e immagini, con prove di ripristino | Recupero misurato di una formula, un copione e la relativa cronologia |
| 1 | Verificare configurazione dell'area Custode e protezione del webhook Telegram | Accessi negati senza identità valida; richieste contraffatte respinte |
| 2 | Esecutore durevole per la Fabbrica: coda, identificatore operazione, ripresa, tentativi limitati | Un compito interrotto riparte senza raddoppiare inviti o prenotazioni |
| 2 | Account e archivio permanente scelto dall'utente | Ritrovare i copioni su più dispositivi e oltre gli attuali 30 giorni |
| 2 | Caricamento foto semplificato con selezione del profumo | Un'immagine caricata aggiorna la scheda senza interventi sul codice |
| 3 | Cataloghi caricati a sezioni e immagini responsive | Navigazione leggera, mantenendo un'edizione integrale per la stampa |
| 3 | Dipendenze bloccate e aggiornamenti verificati | Pubblicazioni riproducibili con controlli prima dell'aggiornamento |

Il codice Custode consente accesso se manca `CUSTODE_PASSWORD` e contiene un valore
di sviluppo per la chiave sessione: è un rischio **condizionato alla configurazione**,
non la prova che l'area online sia esposta. Configurazione non letta, dati non aperti.
Sul webhook Telegram va verificata l'autenticazione all'ingresso oltre al filtro
del destinatario: non modificare il webhook o i segreti senza una verifica completa.

Il libro HTML supera 1,9 MB, Opera circa 1,16 MB e il catalogo Parfums circa 0,77 MB:
sono dimensioni osservate dei file, non misure di lentezza per gli utenti.
Gli attuali copioni Fabbrica hanno scadenza 30 giorni e sono associati al browser.
La conservazione Git dei sorgenti non sostituisce il backup dei dati degli utenti.

I nuovi controlli GitHub **non bloccano da soli** la promozione Vercel. L'associazione
va configurata sul progetto con accesso amministrativo disponibile.
[Deployment Checks Vercel](https://vercel.com/docs/deployment-checks).

## Verifiche e stato della pubblicazione

Verifica conclusiva: 32 test Python superati, controllo del renderer superato,
400 geometrie e raster distinti, formule/QR/mouillette preservati. Campione di stampa:
otto ricette su otto pagine, controllate visivamente. Dopo l'importazione della foto,
la scheda P001 è stata nuovamente stampata: una pagina, immagine, formula e QR leggibili.

L'autonomia attiva deve restare verificabile: rilevare, classificare, correggere
solo casi previsti, ricontrollare, registrare. Le azioni esterne della Fabbrica
richiedono connettori, consenso e conferme reali; non vengono presentate come eseguite.


### Esito online consolidato

- Pubblicazione principale: `6682c8068b4e075ef6e36cb9fe93842c57835c94`, Vercel riuscito.
- Controlli rigorosi eseguiti da GitHub: [esecuzione 34519082868](https://github.com/claudioterzi/Claudio/actions/runs/34519082868), riuscita.
- Prova foto reale: commit con la sola immagine P001; [workflow 34519271634](https://github.com/claudioterzi/Claudio/actions/runs/34519271634) riuscito.
- Il workflow ha prodotto autonomamente `f8a6524e69a9753bc8b6489f67d1377506b70412`: solo registro foto e libro. Vercel ha pubblicato anche questo aggiornamento.
- Monitor di produzione eseguito realmente dopo il deployment: [esecuzione 34519396136](https://github.com/claudioterzi/Claudio/actions/runs/34519396136), riuscita.
- Controllo diretto: **38 verifiche, nessun errore**. Home, Soglia, progetti, Fabbrica, libro, due script, otto disegni e nuova foto rispondono 200 con byte identici ai file pubblicati.
- Nuova immagine principale di P001 verificata; il disegno originale resta disponibile. Gli altri 399 disegni sono principali nelle rispettive schede.
- Cron configurato ogni 15 minuti: verificata la configurazione e l'esecuzione post-deployment, non ancora un'intera giornata di esecuzioni pianificate.
- La vecchia pubblicazione indicata da Claudio resta **non cancellata** per il limite di accesso Vercel 403 già descritto.

Evidenze: `docs/evidenze/SITO_AUTOMAZIONI_LIVE_2026-09-10.json` e
`docs/evidenze/FLACONI_400_2026-09-10.json`. I risultati non implicano assenza
assoluta di guasti futuri: documentano copertura, controlli e limiti effettivi.
