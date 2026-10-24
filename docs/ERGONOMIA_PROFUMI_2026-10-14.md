# Correzioni ergonomia: profumi, Talenti e Libro

Stato: candidato nel branch `codex/ergonomia-completa-2026-10-14`, derivato dal commit `17cac359250b8af1850ac22cf21944fa0448da78`. Non è una verifica del sito pubblicato. Le prove usano dati fittizi e un browser Chromium isolato; non sono state invocate API applicative o servizi IA, né modificati dati del browser di Claudio.

| Finding | Comportamento corretto | File principali | Prova |
|---|---|---|---|
| FPC-01 | Ripristina il profilo prima di montare le viste. Lettura, matching e consiglio non salvano più i default DOM. Una modifica esplicita può anche svuotare servizio/descrizione. | talenti-pro.js, talenti.html | Node: ripristino senza scritture, edit e limiti; Chromium: boot con richieste salvate, edit e reload senza perdita. |
| FPC-02 | Le 400 schede sono pulsanti nativi con nome accessibile. | parfums.html | Chromium: 400 button; Enter apre la scheda. |
| FPC-03 | Il parametro URL precompila l'intenzione e mostra l'invito a premere il pulsante. Non invia più un POST ritardato. Il draft dell'atmosfera resta una precompilazione. | atelier.html | Node: URL senza timer/invio; Chromium: zero API dopo arrivo con query; test Atelier esistente: invio esplicito e 72 combinazioni locali. |
| FPC-04 | Dialogo nativo, titolo accessibile, focus iniziale sul comando Chiudi, sfondo inert e restituzione del focus. | parfums.html | Chromium: apertura da tastiera, nome, focus, sfondo inert, Escape e ritorno al pulsante originario. |
| FPC-05 | Intestazioni ordinabili con pulsante e aria-sort aggiornato. | organo.html | Chromium: Enter alterna ascending/descending e filtro resta operativo. |
| FPC-06 | Etichette dei dieci campi statici e nomi dei controlli stock generati. | organo.html, parfums.html, spesa.html, valigia.html | Chromium: getByLabel risolve i campi; tutti i checkbox hanno un nome. |
| FPC-07 | Consumo limitato a 0–volume disponibile, coerente in riga, totali, calcolatore e CSV. I vecchi valori invalidi non sono riscritti al boot: il messaggio spiega il limite applicato ai totali. L'edit aggiorna la riga senza rimuovere l'input dal DOM. | spesa.html | Node: cinque controesempi; Chromium: vecchio 20ml/10ml produce 0ml residui, nuovo input 20 viene limitato a 10. |
| FPC-08 | Digitare evidenzia i risultati senza spostare la pagina. Un pulsante esplicito porta al risultato. La griglia conserva sette colonne fisiche, scorre nel suo contenitore e usa nomi leggibili. | valigia.html | Chromium: scroll fermo durante input, salto esplicito e focus sullo slot; pagina a 390px senza overflow esterno. |
| ROOT-02, quota profumi | Tabelle e QR del Magazine, tabelle e mappa Valigia, contenuti del reader Libro restano dentro la larghezza della pagina. | magazine.html/css, valigia.html, libro-reader.css | Chromium a 390px: scrollWidth ≤ innerWidth nelle tre pagine. |
| ROOT-04, quota Libro | Indice, ricerca, venti risultati per volta, capitoli su richiesta, bookmark storici, comandi per tornare all'indice e stampare il capitolo. | libro.html, libro-reader.js/css, libro/* | Chromium: ricerca, apertura della famiglia da 50 schede, focus sul profumo, bookmark rubrica; Node: 400 link TRZ1 e derivazione completa dei dodici frammenti. |

## Edizione integrale e provenienza

`public/libro-integrale.html` conserva la copia esatta iniziale, incluso CRLF: **1.942.529 byte**, SHA256 `78b8d9bc6bba3a224aa92bdb41284f158f9e66360767ffb8c15e15a844923bec`. Il contenuto Git LF della vecchia `public/libro.html` misura **1.931.353 byte**, SHA256 `3060e9576b1cbc6e4c84732d8f1c2c79d6b5865cf833fbe6ff4ef95177188b85`. Sono due rappresentazioni distinte: nessuno dei due digest sostituisce l'altro.

`public/libro/provenienza.json` riporta entrambi i digest, gli intervalli della sorgente normalizzata e i digest dei frammenti. La consultazione sposta H1→H2 e H2→H3; testo, immagini, ricette e link dei frammenti derivano dalla stessa fonte senza omissioni. L'edizione integrale conserva anche i suoi titoli storici originali.

L'HTML iniziale è ora circa **5,4 kB**; l'indice JSON misura **166.294 byte**. I dodici capitoli vengono richiesti separatamente e il browser mantiene in memoria quelli già letti. Queste sono misure dei file, non tempi di caricamento, byte compressi, quota Vercel o risparmi economici. La copia integrale e i derivati aumentano i file conservati per mantenere recuperabilità e confronto.

La catena prevista è `studio/parfums/genera_libro.py` → `public/libro-integrale.html` → `scripts/build_libro_reader.py` → indice e capitoli. Il generatore completo non è stato eseguito durante questa correzione. Una futura edizione differente viene marcata `GENERATED_CANDIDATE` con `source_commit: null` finché non possiede provenienza accettata; non eredita automaticamente il commit della copia congelata. Gli audit `studia_libro_400.py` e `verifica_flaconi_400.py` leggono l'integrale, con fallback alla vecchia pagina per checkout precedenti.

## Verifiche e confini

- `node tests/test_profumi_ergonomia.cjs`: ripristino del profilo senza scritture, edit espliciti, limiti, cinque controesempi stock, query senza invio, SHA dell'integrale, copertura continua dei dodici frammenti e identità dei 400 link TRZ1.
- `node tests/test_atelier_submission.cjs`: campi POST espliciti, catalogo di 293 materie e 72 combinazioni locali.
- Compilazione senza esecuzione dei quattro file Python modificati.
- Dieci controlli Chromium con documenti, script, CSS e immagini reali del checkout, serviti da un router di test in memoria. Nessuna API/provider, nessun errore JS e nessuna immagine sostituita. Le API e i servizi esterni non sono validati da queste prove.
- L'audit storico iniziale sul checkout Windows rilevava 400 `code_error_ValueError`: i due cataloghi JSON convertiti in CRLF avevano digest `5f234b0de4e12dc3...`, anziché il digest Git LF `13aff1815ecef350...` richiesto dai codici. Il controllo isolato con byte Git dichiarati è passato: 400 schede, 4.800 righe, 400 codici e zero failure; conserva separatamente i quindici warning storici sulle materie di supporto. Questo confronto non va presentato come un pass del runtime Windows precedente alla correzione delle terminazioni di riga.

Report e screenshot sono in `outputs/ergonomia-2026-10-14/fix-profumi/` nel workspace Raffaello-SIA. L'esito dell'eventuale ripristino LF del checkout e delle verifiche finali di integrazione appartiene al coordinatore; il fallimento iniziale resta disponibile come evidenza.
