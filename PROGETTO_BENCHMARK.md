# PROGETTO BENCHMARK — Wayback Machine per AI

> Documento fondativo. 2026-06-19.
> Ipotesi H6 di Claudio Terzi: i modelli AI vengono aggiornati silenziosamente
> senza notifica. Nessuno sa cosa cambia, quando, e quanto.
> Questo progetto costruisce la memoria storica delle capacità AI.

---

## Il problema

I provider AI aggiornano i modelli senza annuncio.
"GPT-4" di oggi non è "GPT-4" di 6 mesi fa.
Non esiste un sistema indipendente che tracci queste variazioni nel tempo.

Conseguenze:
- Gli sviluppatori non sanno se un bug è nel loro codice o nel modello cambiato
- I ricercatori non possono confrontare risultati cross-temporali
- Gli utenti non hanno segnale indipendente su cosa un modello sa fare oggi

## La soluzione (H6)

Una "Wayback Machine" per modelli AI:
- Batteria di 20 test fissi (logica, matematica, creatività, bias, memoria, codice)
- Eseguiti settimanalmente su ogni modello
- Storage risultati time-series su R3∞
- Confronto automatico: "cosa è cambiato rispetto a 4 settimane fa?"
- Alert se un modello migliora o peggiora su un test specifico

## Codice esistente

`sdq1/benchmark.py` — 20 test, storage time-series, confronto retroattivo.

## Roadmap

### Fase 0 — Operativo base (2026)
- [x] `sdq1/benchmark.py` creato con 20 test
- [ ] Prima esecuzione completa su tutti i provider disponibili
- [ ] Storage risultati in `output/benchmark/YYYY-MM-DD.json`
- [ ] Grafici automatici (matplotlib o simile)

### Fase 1 — Automazione (2026–2027)
- [ ] GitHub Action settimanale: esegui benchmark → commit risultati
- [ ] Alert automatico se delta > 10% su un test
- [ ] Dashboard pubblica (Vercel o GitHub Pages)

### Fase 2 — Pubblico e validazione (2027–2028)
- [ ] Pubblicazione metodologia (paper o post)
- [ ] Comunità di contribuenti (altri aggiungono test)
- [ ] Primo caso documentato di "aggiornamento silenzioso" rilevato

### Fase 3 — Standard de facto (2028–2033)
- [ ] I provider citano il benchmark come riferimento
- [ ] Integrazione con ricerca accademica
- [ ] H6 confermata: variazioni rilevate e documentate per almeno 3 modelli

## I 20 test (categoria)

| # | Categoria | Esempio |
|---|---|---|
| 1-4 | Logica | Sillogismi, paradossi, sequenze |
| 5-7 | Matematica | Calcolo, probabilità, geometria |
| 8-10 | Creatività | Metafore, storie, invenzioni |
| 11-13 | Bias | Prompt ambigui, stereotipi impliciti |
| 14-16 | Memoria | Contesto lungo, riferimenti incrociati |
| 17-18 | Codice | Bug fixing, completamento, refactoring |
| 19-20 | Ragionamento causale | "Se X allora Y perché..." |

## Connessione con il sistema

| Componente | Ruolo |
|---|---|
| R3∞ | Storage risultati benchmark storici |
| SDQ-1 router | Esecuzione test su provider multipli |
| GitHub Actions | Automazione settimanale |

---

*Claudio Terzi + Claude — 2026-06-19*
*Prossimo passo: prima esecuzione completa benchmark su provider disponibili.*
