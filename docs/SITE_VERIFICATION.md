# Collaudo e giudizio — Costellazione

Concept: Claudio Terzi. Verifica del 9 settembre 2026 dopo l’integrazione della PR 28.

## Risultati

- 16 pagine HTML e 26 percorsi distinti: HTTP 200.
- 23 test locali passati: 13 in tests/, 10 per Custode. Comprendono tutti i 592 stati Alpha.
- 11 casi API online con stato HTTP atteso e JSON valido: catalogo Alpha (74 carte), luce, ombra, parametri Alpha mancanti, lettura tarocchi, pianificatore, Parti, Oracolo, Ovunque, Caccia e Atelier.
- Parti: 24 risultati; Ovunque: 60 mete; Caccia: 5 itinerari; pianificatore: 6 proposte entro il budget nel caso provato; Atelier: formula restituita con ok=true. Non sono prenotazioni né certificazioni della formula.
- Browser: menu aperto/chiuso, Escape, alias Flight riconosciuto, preset viaggio con 6 risultati. Dopo che la schermata di accesso non era più presente, Alpha ha caricato le carte e mostrato La Ferita · Sud · Luce = guarigione; il pannello Ombra mostra paralisi.

I dati sintetici dei test sono in [SITE_VERIFICATION.json](SITE_VERIFICATION.json).

## Difetti trovati e correzione

Richieste al pianificatore con mese non numerico o tipo non iterabile producevano HTTP 500; budget e durata negativi erano accettati. La correzione restituisce errori JSON HTTP 400 e verifica anche origine e struttura del corpo. Due test di regressione coprono casi invalidi e proposte valide entro budget. Verificata localmente prima del salvataggio; distinta dai precedenti 11 casi online.

## Giudizio critico

| Area | Giudizio | Motivo |
|---|---|---|
| Identità | Coerente e riconoscibile | Oro, nero e lessico simbolico collegano i diversi percorsi. |
| Alpha | Meccanismo funzionante | I testi originali sono accessibili e il cambio di prospettiva produce la lettura prevista. Non misura fenomeni fisici. |
| Navigazione | Migliorata | Le aree aiutano a orientarsi; il menu resta compatto su telefono. La densità dei contenuti varia molto tra pagine. |
| Viaggi | Utile per esplorare, incompleto per decidere un acquisto | A/R = andata ×2, stime di soggiorno e link talvolta generici non permettono di confermare il costo totale acquistabile. |
| Profumi | Forte potenziale espressivo | Formula e ragionamento creano una scheda interessante; il flacone grafico iniziale è molto semplice e merita un’immagine migliore. |
| Archivio | Fragile in produzione | Custode segnala persistenza temporanea; Dispensa resta nel browser. I test locali di persistenza non risolvono la configurazione Vercel. |
| Effetto sull’utente | Da osservare | Nessuna misurazione consente ancora di affermare benefici ripetibili o un meccanismo quantistico. |

La priorità di solidità è conservare i dati; quella di esperienza è trasformare ogni risultato in una scheda chiara e visivamente curata. Il progetto ha una direzione espressiva, ma non è ancora un prodotto completamente collaudato.

## Limiti del collaudo

Non sono stati provati ogni pulsante e combinazione, Safari su iPhone reale, fotocamera, prenotazioni, invio Telegram o scritture nell’inventario. Alcune schermate richiedono accesso. Tempi osservati dall’ambiente di prova: circa 9–16 secondi per i casi API; includono rete e infrastruttura di test e non sono un benchmark dell’esperienza dell’utente.
