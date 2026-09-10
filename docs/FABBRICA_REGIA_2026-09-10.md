# Fabbrica dei Desideri — regia e prima versione web

Autore del concetto: Claudio Terzi. Firma: C.Terzi. 10 settembre 2026.

## Esperienza pubblica

Pagina dedicata `/fabbrica.html`, accessibile anche da `/fabbrica`, con identità
visiva autonoma: blu, bianco, tipografia leggibile e un’immagine originale della
serata fra amici, dichiarata illustrativa. Collegamento dal catalogo Creazioni e
dal menu Progetto. Nessuna testimonianza, numero di clienti o offerta disponibile
inventati. Nessun pagamento richiesto nella prima versione.

Il cliente racconta un desiderio, indica luogo, budget, tempi e limiti delle
sorprese. Quattro ingressi: matrimonio, festa/addio al celibato o nubilato, viaggio,
desiderio personale. La leva a cinque intensità definisce l’ampiezza proposta della
regia e influenza la generazione. Non controlla la capacità del modello.

Gli esempi originali seguono una prima canzone dal vivo: prova privata, esibizione
intima, serata organizzata, collegamento in tre città, spettacolo in cinque città.
Ogni livello ha condizioni, scene, dipendenze, domande e alternativa. Il massimo
non promette simultaneità audio fisicamente irrealistica: gli interventi remoti
sono sequenziali; le eventuali registrazioni devono essere dichiarate.

## Capacità implementate

- `GET /api/fabbrica/status`: disponibilità configurata dell’IA, archivio e ultimo
  copione della sessione; cookie opaco, HttpOnly, SameSite Strict, Secure in produzione.
- `POST /api/fabbrica/plans`: brief con intensità 1–5, proposta strutturata del
  provider, validazione di dimensioni, campi e dipendenze acicliche; ID generato
  prima della chiamata, stato pending e output salvati sul database.
- `GET /api/fabbrica/plans/<id>`: riapertura soltanto nella sessione proprietaria.
- `PATCH` sulla stessa risorsa: completamento dichiarato dall’utente, prerequisiti
  obbligatori, revoca transitiva, versione e aggiornamento atomico contro conflitti.
- `DELETE`: rimozione del copione scelto. Le revisioni hanno identità separate.
- Revisione: nuovo copione con riferimento al precedente e nuove conferme.
- Download JSON: copia conservabile dall’utente. L’esempio resta una prova locale.

Non sono implementati telefonate, WhatsApp, email, acquisti, prenotazioni, ricerca
web eseguita dal backend, accesso alla rubrica, lettura di conversazioni o controllo
autonomo di un evento. Le ricerche sono link da avviare; i messaggi sono bozze.
La disponibilità di un provider non viene confusa con l’esito di una generazione.

## Archivio, limiti e dati

Namespace Redis `terzi:fabbrica:v1:` separato dall’archivio profumi. Nessuna nuova
credenziale viene creata. I copioni scadono dopo 30 giorni; l’utente viene informato
prima della generazione. Il collegamento contiene un ID che da solo non concede
accesso: serve anche il cookie della sessione. Non esiste ancora accesso da account
fra dispositivi; la copia JSON costituisce l’esportazione personale.

Risposte API senza cache e senza CORS pubblico. Scritture protette da header
personalizzato e controllo dell’origine. Payload e output hanno limiti. La quota
condivisa Redis consente al massimo 5 tentativi per ora per sessione e indirizzo
osservato e 100 al giorno complessivi. Non è un sistema commerciale completo di
identità/antiabuso. Se l’archivio non funziona, la chiamata pagata non viene avviata.

Deduplicazione per sessione e contenuto. Ogni tentativo con output conserva testo,
provider, modello, timestamp e token disponibili, compresi output scartati dallo
schema. La stima monetaria è `null`: non sono state verificate tariffe per modello.
Le risposte pubbliche non espongono segreti, output grezzi o identificativo del
proprietario. Nessun testo dei desideri viene scritto nei log. L’IA riceve il brief
e l’eventuale revisione, non una rubrica o la memoria privata di Claudio.

## Prossima architettura della regia operativa

Il copione deve diventare un grafo eseguibile con attività, prerequisiti, finestra
temporale, responsabile, autorizzazione, costo massimo e prova di esecuzione.
La qualità dell’IA va misurata sul risultato della coordinazione, non sul numero
di messaggi prodotti o su affermazioni di superintelligenza.

| Componente da aggiungere | Responsabilità concreta |
| --- | --- |
| Delega dell’utente | Budget massimo, persone ammesse/escluse, sorprese autorizzate, canali e azioni delegabili, scadenza e revoca |
| Connettori autorizzati | Accessi concessi per rubrica, canali di messaggistica, telefonia, calendari e prenotazioni; nessuna importazione implicita di conversazioni private |
| Esecutore durevole | Attività riprendibili dopo interruzioni, scadenze, attese di risposta, ritentativi delimitati e annullamenti |
| Registro di invio | Un identificativo univoco per impedire doppi inviti, ordini o pagamenti durante ritentativi |
| Conferme verificabili | ID del servizio, timestamp, stato restituito dal fornitore e distinzione fra consegnato, letto, accettato e completato |
| Regia temporale | Data e fuso espliciti, margini di arrivo, prove, segnali di pronto e via; gestione del ritardo reale |
| Gestione degli imprevisti | Alternative approvate, soglie di spesa, rinvio o riduzione del programma quando una condizione manca |

Stati futuri da tenere distinti: proposta, autorizzata, inviata, ricevuta,
accettata, pronta, eseguita con evidenza, fallita e annullata. L’output del modello
non può scegliere arbitrariamente uno stato di esecuzione. Le transizioni vengono
validate dall’esecutore contro delega, dipendenze, budget e risposta del servizio.
Un pagamento richiede un provider e regole economiche esplicite, non un campo
testuale nel prompt.

Il sistema deve poter ricevere tutti i segnali di pronto prima di dare il via,
oppure scegliere una versione ridotta già autorizzata. Non garantisce esecuzione
fisica al secondo né presume che assenza di risposta significhi consenso.
Preferenze dichiarate e selezione volontaria dei contatti sostituiscono inferenze
non verificate sui segreti o sulle relazioni delle persone.

## Una regia sopra servizi diversi

Ulteriore richiesta dell’autore: includere spostamenti, hotel e camere, diventando
un’alternativa nell’esperienza d’uso a servizi oggi separati. La prima integrazione
di prodotto è il brief per otto persone con partenze diverse, camere e budget comune.
Il backend pianifica questi vincoli; nessun inventario è stato collegato.

Architettura proposta: il desiderio diventa un piano con elementi comuni a tutti
i fornitori — persone, luoghi, finestre temporali, costo totale e dipendenze. Ogni
connettore dichiara le proprie capacità: ricerca, preventivo, opzione temporanea,
prenotazione, modifica, cancellazione e ricezione di aggiornamenti. Una capacità
mancante rimane esplicita; non viene sostituita da un successo narrato dall’IA.

La documentazione ufficiale Booking.com Demand API descrive integrazioni dalla
ricerca con rinvio fino alla prenotazione integrata e gestione successiva. L’accesso
ha prerequisiti e non è stato ottenuto per questo progetto. [Booking.com Demand API](https://developers.booking.com/demand/docs).
Google Routes offre percorsi e matrici di tempi/distanze: può contribuire alla
logistica, ma non costituisce un servizio di prenotazione di passaggi.
[Google Routes API](https://developers.google.com/maps/documentation/routes).
Non è stato verificato un accesso di prenotazione utilizzabile dal progetto per
Airbnb o BlaBlaCar. Non promettere che questi marchi siano partner o già integrati.

Un ordine complesso richiede di coordinare servizi con condizioni diverse.
Prima si raccolgono offerte con scadenza; poi si verifica la compatibilità del
totale con la delega. Dove disponibili, si usano opzioni temporanee prima delle
conferme. Se una parte fallisce dopo un acquisto, la regia applica una procedura
concordata di sostituzione o annullamento: non esiste un rollback universale delle
prenotazioni. Nessun doppio addebito nei ritentativi; ogni servizio conserva il
proprio identificativo e le sue condizioni. Una modifica di volo riapre i controlli
su trasferimento, check-in e attività dipendenti, lasciando intatti gli altri elementi.

Per partire: pochi fornitori verificati di trasporti, soggiorni e attività in una
zona pilota, con operatori umani per gli imprevisti. Misurare quota di itinerari
completati, discrepanze di prezzo, annullamenti, tempi di risoluzione e costo della
regia. L’esperienza memorabile dipende dalla continuità del servizio prima, durante
e dopo l’evento; il numero di applicazioni collegate da solo non la misura.

## Verifica eseguita prima della pubblicazione

15 test Python sul flusso Flask con provider e Redis sostituiti solo nei test:
conservazione/riapertura, deduplicazione, separazione delle sessioni, origine,
conflitti, revisione, cancellazione, quote, errori, dipendenze e impossibilità per
il modello di marcare un’azione come eseguita. Cinque esempi validati con lo schema
usato in produzione. Controlli di sintassi JS/Python, ID dei controlli, link locali
e presenza dei quattro percorsi e cinque livelli.

L’archivio e le chiamate reali richiedono inoltre il collaudo dopo la pubblicazione.
Il test locale usa un sostituto Redis e non prova il comportamento di Lua sul
servizio reale. Nessuna verifica nel browser è stata richiesta o effettuata.
