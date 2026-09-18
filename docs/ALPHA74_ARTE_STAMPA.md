# Alpha 74 - arte, stampa e lettura

Autore: Claudio Terzi. Firma sulle carte: C.Terzi.

74 carte, 148 facce, 592 significati presi senza parafrasi da `tarocchi_quantici_alpha.json`.
Ogni faccia contiene quattro settori. Nome, asse, polarità e significato ruotano insieme.
Angoli tipografici nel documento: Nord 0, Est 90 orario, Sud 180, Ovest 270 orario.
La vista web applica la rotazione opposta per portare in alto l'asse selezionato.

## Uso e dimensioni

- Prova di stampa: 120 x 120 mm, PDF con testo vettoriale incorporato.
- A4: due carte per foglio, fronte/retro sul lato lungo, 100%, 37 fogli / 74 pagine.
- Dipinti: 887 x 887 pixel nativi per faccia, circa 187,7 ppi a 120 mm.
- Il file è una prova RGB in scala reale, senza abbondanza. Non è un PDF/X tipografico da 300 ppi.
- Il titolo ripetuto nei quattro versi evita di privilegiare il Nord.

## Caricamento web

`public/alpha74-art.js` risolve soltanto ID canonici 1-74, polarità valide e assi validi.
Le miniature WebP sono 160 px, circa 4 KB ciascuna, visualizzate a 80 px.
La versione 640 px viene richiesta soltanto aprendo il dettaglio di una carta.
Nessun originale da stampa è incluso nel sito. Nessun caricamento anticipato del mazzo illustrato.
Le immagini sono una rappresentazione dello stato estratto: non partecipano ai calcoli.

## Coerenza della lettura

La richiesta conserva una copia delle carte, della domanda e del contesto. Durante la richiesta
non si possono aggiungere carte; una nuova estrazione invalida la lettura precedente.
Le domande successive riusano il contesto della lettura originale. Analisi e voce si avviano
esclusivamente dai rispettivi comandi dell'utente. Una risposta tardiva relativa a una lettura
superata non viene aggiunta alla lettura nuova.

## Verifiche

- 592 significati e 592 orientazioni confrontati nel testo effettivo dei PDF.
- 148 facce di 120 mm; 74 pagine A4 con i fronti e retri corrispondenti.
- 296 WebP decodificati e verificati durante l'esportazione.
- 9 test Python esistenti superati.
- `node tests/test_alpha74_frontend.cjs`: 592 stati, snapshot, ascolto manuale,
  invalidazione lettura e dettaglio caricato su richiesta.
- Nessuna verifica visiva su un iPhone fisico o browser di produzione della nuova versione.

## Stato della consegna

Implementazione verificata localmente. Il 12 settembre 2026 Claudio ha autorizzato
esplicitamente la pubblicazione delle sole immagini per lo schermo e dell'integrazione
nel repository pubblico claudioterzi/Claudio, per aggiornare il sito Vercel.
L'autorizzazione non include gli originali illustrati o i PDF da stampa, né modifica
la riservatezza degli altri progetti o la protezione degli accessi al sito.
Il risultato del deployment va verificato prima di dichiarare la versione online.

## Lezione di progetto

Intenzione -> gesto -> attenzione -> significato -> forma. La carta deve essere progettata
come oggetto da usare. La leggibilità dipende dall'orientamento selezionato; un'immagine bella
con quattro testi tutti diritti non soddisfa questa funzione. Le verifiche devono testare
le otto condizioni d'uso, non soltanto la vista con il Nord in alto.
