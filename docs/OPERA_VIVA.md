# Opera Viva — Atelier cinetico C.Terzi

Concept e direzione artistica: Claudio Terzi [CT-LGAI-001].
Firma artistica obbligatoria: **C.Terzi**. © 2026 Claudio Terzi.

## Progetto
Un generatore di opere ottiche a due lastre: una griglia regolare davanti,
un'immagine tradotta in punti dietro. La parallasse del visitatore modifica
la sovrapposizione. L'opera fisica resta ferma.

Prima versione: `public/opera-viva.html`, percorso Vercel `/opera-viva`.
Nuova voce nel menu comune e nel catalogo Creazioni. L'archivio `opera.html`
rimane distinto e conservato.

## Funzioni realizzate
- Ritratto completo di Raffaello, con testa, capelli, orecchie e mento nel quadro.
  Nuova interpretazione generata dai tratti del brief, non modello biometrico canonico verificato.
- Caricamento locale PNG/JPEG/WebP fino a 20 MB, inserimento intero senza ritaglio.
- Composizione astratta generativa a onde come secondo soggetto.
- Regolazione intercapedine e rotazione, tre preset di sensibilita.
- Simulazione di un passaggio e vista separata delle due lastre.
- Esportazione PNG firmato, due SVG in millimetri, JSON con parametri e campionamento sorgente.
- Nessuna richiesta AI o upload al server durante l'uso. Non e un generatore fotografico da prompt.

## Firma
Tratto vettoriale calligrafico disegnato per questo progetto: C.Terzi.
Non e una riproduzione della firma autografa di Claudio.
La stessa geometria e usata sul canvas, nell'anteprima PNG e sulla lastra
anteriore SVG. Fascia inferiore dedicata, fuori dal reticolo: evita che
il moire renda il nome illeggibile. La lastra posteriore reca attribuzione
nei metadati e si abbina alla lastra anteriore firmata; nessuna seconda
firma disallineata. ID progetto comune negli SVG e nel JSON.

## Geometria
Formato 600x800 mm; reticolo fino a quota 746 mm, fascia inferiore per firma.
Lastra posteriore 636x836 mm. Passo anteriore 4,5 mm; diametro davanti 3,15 mm.
Osservatore a 2500 mm. Intercapedine default 50 mm, angolo 0,6446 gradi.
Compensazione posteriore 1+gap/2500: passo fisico default 4,59 mm.
Centri: anteriore (300,400), posteriore (318,418); ruotare solo la lastra posteriore.
Punti posteriori: copertura = 1 - luminanza; r = passo * sqrt(copertura/pi),
con copertura limitata a [0,005;0,77] per evitare sovrapposizione di punti adiacenti.
Il JSON conserva l'immagine campionata a 300x400, non il file fotografico originale.

## Verifica e limiti
Validazione sintattica JS; verifica matematica della compensazione,
controllo SVG, firma e parametri. Nessun test browser o collaudo fisico dichiarato.
Simulazione di dischi opachi e fondale chiaro: escluse riflessione, rifrazione,
illuminazione reale, binocularita. Lo schermo puo produrre aliasing.
Gli SVG sono da provino. Il filtro originale collaudo.py/viso.py non e stato
eseguito da questa implementazione e nessuna soglia del 70% e dichiarata superata.

## Evoluzione prevista, non ancora implementata
1. Importazione del JSON per riaprire un'opera.
2. Archivio privato con versioni e confronto di prove fisiche.
3. Generazione fotografica da descrizione tramite un servizio AI configurato.
4. Collaudo incrociato con il motore originale e misura della resa di stampa.
Ogni evoluzione conserva C.Terzi in tutti gli esportati dell'opera.
