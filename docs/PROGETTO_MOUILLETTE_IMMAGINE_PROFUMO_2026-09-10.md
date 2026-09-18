# Libro dei 400, Mouillette e Immagine ↔ Profumo
Ideazione e direzione: Claudio Terzi · C.Terzi. 10 settembre 2026.

## Richiesta e correzione dell’autore
La rubrica fisica appartiene al Libro dei 400, anche nella versione stampabile.
Il magazine mensile estende il concetto a industria, nicchia e materie prime.
L’autore vuole un codice a barre per ogni articolo che apra un futuro documentario
3D generato con AI, fruibile con Meta/Oculus. Esempio: lavanda nel sud della Francia,
attraversando i luoghi e la trasformazione in essenza.

Il principio dell’autore è bidirezionale: **immagine → profumo → immagine**.
Il primo verso è già rappresentato dall’Atelier con foto e intenzione; il secondo
è ora esplicitato come progetto editoriale e immersivo. Non risulta verificata
una precedente registrazione integrale di questa formulazione: non attribuirla
retroattivamente a un documento che non è stato letto.

## Realizzazione di questa versione
- `libro.html#rubrica-olfattiva`: coordinate A–E e righe numerate, esempio C3;
  registro e stampa isolata dell’inserto. Ogni scheda ha campi campione e QR.
- `magazine.html`: numero zero di 9 pagine stampabili e PDF scaricabile.
  Titolo di lavoro proposto: Mouillette. Mensile proposto: 24 pagine e 6 campioni,
  due per categoria. Sono proposte editoriali, non notizie o lanci verificati.
- `esperienze-olfattive.json`: 404 percorsi, 400 dal canone del libro, 3 modelli
  editoriali e l’episodio pilota LAVANDA. Gli ID P001–P400 restano stabili.
- `esperienza.html?id=...`: sequenza delle scene e trasferimento di una descrizione
  modificabile all’Atelier tramite parametro `scena`, senza invio automatico all’AI.
- QR PNG con zona bianca di rispetto. URL assoluto sulla pubblicazione Vercel
  esistente; testo del codice e link cliccabile affiancano ogni QR.

## Riferimenti distinti
| Riferimento | Funzione |
| --- | --- |
| Numero 001–400 | Identità della creazione |
| TRZ1… | Formula ricostruibile |
| Volume/modulo/C3 | Posizione del campione fisico |
| P001 / M00-IND / LAVANDA | Percorso editoriale collegato al QR |

Le posizioni delle mouillette si assegnano preparando i campioni, senza inventare
un’associazione con le lettere o con il numero del profumo. Estrarre le strisce
da sinistra verso destra con pollice e indice. Alloggiamenti orizzontali separati;
A corta per essenze forti/concentrate, E più lunga. Misure intermedie, conservazione,
barriere agli odori e rilegatura richiedono un prototipo fisico.

## Fase immersiva da sviluppare
Le pagine attuali mostrano sceneggiature, non video o ambienti 3D già prodotti.
Ogni percorso ha `media:null`. Il rilevamento WebXR segnala solo il supporto del
browser e non abilita un player inesistente. Non è attestata la scansione diretta
con le telecamere Meta/Oculus. Accesso attuale tramite QR su telefono o link.

Per un episodio reale: individuare luogo e materia; raccogliere fonti e riprese
con autorizzazioni; preparare la sceneggiatura; generare e revisionare media;
distinguere riprese documentate e ricostruzioni AI; archiviare versioni e crediti;
integrare un player WebXR; collaudare sul modello di visore effettivo. La mouillette
fornisce l’odore. Il passaggio fra sensi è una interpretazione creativa, senza
pretesa di una corrispondenza universale o di ricostruzione esatta della formula.

Fonte tecnica consultata il 10 settembre 2026:
[Meta: WebXR overview](https://developers.meta.com/horizon/documentation/web/webxr-overview/).

## Rigenerazione
Dalla radice del repository:
```
python -m pip install -r studio/parfums/requirements-editoriale.txt
python studio/parfums/genera_esperienze.py
python studio/parfums/genera_libro.py
```
ReportLab e Pillow servono solo alla generazione locale dei QR. Il sito serve
asset statici. Il PDF deriva dalla versione stampabile HTML/CSS tramite WeasyPrint.

## Verifiche
- Audit esistente: 400 formule, 400 codici TRZ1 e 4800 righe della ricetta corrispondono
  al canone; nessun errore. I 15 avvisi preesistenti del canone restano da rivedere
  nel lavoro sulle formule, fuori dall’intervento editoriale.
- Tutti i 404 QR sono stati decodificati con ZXing e corrispondono ai rispettivi URL.
- I404 ID sono unici e presenti nell’indice; le 400 schede hanno ancore esistenti.
- Controllata la sintassi JavaScript dei file aggiunti e della navigazione.
- Revisione PDF di tutte le pagine del magazine e campione di schede 001, 200, 400.

## Continuità
Claudio autorizza i salvataggi su Drive e chiede un diario durante la sessione,
con parole originali, interpretazioni, motivazioni sintetiche, verifiche e prossimo
passo. Conservare le idee originali; eliminare solo copie temporanee dopo il
consolidamento verificato. Nessuna cancellazione eseguita in questa sessione.
Diario: https://drive.google.com/file/d/1f8V8de2OymvJbCUeWnKztA8PZI1Yhjrj/view
Copia di ripresa: https://drive.google.com/file/d/15ihVZWUYoFMphxreUfMK4fzCoN70MXYO/view
