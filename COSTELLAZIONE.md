# 🧭 COSTELLAZIONE OPERATIVA — i file per avviare e continuare

> La versione sempre aggiornata di questa mappa è questo file nel repo.
> Le pagine per *usare* le cose sono nel doc «🌌 COSTELLAZIONE» su Drive
> e nella pagina [Le Creazioni](https://claudio-ebon.vercel.app/creazioni.html).
> Qui invece ci sono i **file di lavoro**: cosa aprire per riprendere in mano
> ogni progetto, e i comandi per rigenerare tutto.

Base dei link: `https://github.com/claudioterzi/Claudio/blob/main/`

---

## 0 · Per avviare QUALSIASI sessione di lavoro

1. **[CLAUDE.md](https://github.com/claudioterzi/Claudio/blob/main/CLAUDE.md)** — le regole operative e relazionali. Ogni sessione le legge per prima.
2. **[MEMORIA_PROGETTO.md](https://github.com/claudioterzi/Claudio/blob/main/MEMORIA_PROGETTO.md)** — la spina dorsale: stato, decisioni, sezione «LA COSTELLAZIONE», diari di sessione.
3. Apri una sessione Claude Code (claude.ai/code) sul repo `claudioterzi/Claudio` e di' cosa vuoi fare: la sessione riparte da questi due file, con piena coerenza.

## 1 · Sistema A — Tarocchi Quantici R³∞

- Motore: [tarocchi/codice_simbolico.py](https://github.com/claudioterzi/Claudio/blob/main/tarocchi/codice_simbolico.py) · [tarocchi/r3_infinito.py](https://github.com/claudioterzi/Claudio/blob/main/tarocchi/r3_infinito.py) · [tarocchi/stesa.py](https://github.com/claudioterzi/Claudio/blob/main/tarocchi/stesa.py) · [tarocchi/ermeneutica.py](https://github.com/claudioterzi/Claudio/blob/main/tarocchi/ermeneutica.py)
- Canone JSON: [tarocchi/tarocchi_quantici.json](https://github.com/claudioterzi/Claudio/blob/main/tarocchi/tarocchi_quantici.json)
- Web app (Flask, serve anche bot e CUSTODE): [tarocchi_web.py](https://github.com/claudioterzi/Claudio/blob/main/tarocchi_web.py)
- Le 79 tavole SVG: [public/cards/](https://github.com/claudioterzi/Claudio/tree/main/public/cards)

## 2 · Sistema B — Canone Alpha

- Il canone completo (74 carte, 592 stati): [tarocchi_quantici_alpha.json](https://github.com/claudioterzi/Claudio/blob/main/tarocchi_quantici_alpha.json)
- Pagina web: [public/alpha.html](https://github.com/claudioterzi/Claudio/blob/main/public/alpha.html)

## 3 · Sistema C — Parfums 400 / Terzi Parfums

Cartella: [studio/parfums/](https://github.com/claudioterzi/Claudio/tree/main/studio/parfums)

- **La fonte** (tua): [Organo_Terzi_300.xlsx](https://github.com/claudioterzi/Claudio/blob/main/studio/parfums/Organo_Terzi_300.xlsx) → convertita da [converti_organo.py](https://github.com/claudioterzi/Claudio/blob/main/studio/parfums/converti_organo.py) in [organo_terzi_300.json](https://github.com/claudioterzi/Claudio/blob/main/studio/parfums/organo_terzi_300.json)
- **Il sapere**: [GRIMORIO_TERZI.md](https://github.com/claudioterzi/Claudio/blob/main/studio/parfums/GRIMORIO_TERZI.md) · [PERCORSO_0_10.md](https://github.com/claudioterzi/Claudio/blob/main/studio/parfums/PERCORSO_0_10.md) ← qui c'è la riga «Livello attuale» da aggiornare quando avanzi
- **Il canone**: [parfums_400.json](https://github.com/claudioterzi/Claudio/blob/main/studio/parfums/parfums_400.json) (v0.3.0, seed 400)
- **I generatori** (modifichi → rigeneri → committi):
  - [codice_olfattivo.py](https://github.com/claudioterzi/Claudio/blob/main/studio/parfums/codice_olfattivo.py) → canone + catalogo `public/parfums.html`
  - [genera_libro.py](https://github.com/claudioterzi/Claudio/blob/main/studio/parfums/genera_libro.py) → `public/libro.html`
  - [genera_atelier.py](https://github.com/claudioterzi/Claudio/blob/main/studio/parfums/genera_atelier.py) → `public/atelier.html`

## 3-bis · L'Organo in pagina e la Grande Opera

- **I 300 ingredienti**: `public/organo.html` (generata da [genera_organo.py](https://github.com/claudioterzi/Claudio/blob/main/studio/parfums/genera_organo.py)) — ricerca e filtri su tutte le materie, con le note d'uso dell'Excel
- **La Grande Opera**: `public/opera.html` (generata da [genera_opera.py](https://github.com/claudioterzi/Claudio/blob/main/genera_opera.py)) — lettore dei 101 documenti dell'[Archivio Cosmico R³∞](https://github.com/claudioterzi/Claudio/tree/main/r3/archivio); rigenerarla quando l'archivio cambia

## 4 · Il sito (pagine e infrastruttura)

- Pagine: [public/](https://github.com/claudioterzi/Claudio/tree/main/public) — index, alpha, parfums, organo, libro, atelier, opera, creazioni, opuscolo, home
- La Soglia: [public/soglia.js](https://github.com/claudioterzi/Claudio/blob/main/public/soglia.js) · Navigazione: [public/nav.js](https://github.com/claudioterzi/Claudio/blob/main/public/nav.js)
- Deploy Vercel: [vercel.json](https://github.com/claudioterzi/Claudio/blob/main/vercel.json) (statici dalla CDN + funzione Python)
- Deploy Pages: [.github/workflows/](https://github.com/claudioterzi/Claudio/tree/main/.github/workflows)

## 5 · SDQ-1, Raffaello e CUSTODE

- Core: [sdq1/](https://github.com/claudioterzi/Claudio/tree/main/sdq1) — agenti, router LLM ([sdq1/llm/router.py](https://github.com/claudioterzi/Claudio/blob/main/sdq1/llm/router.py)), SAR, futures
- Raffaello su Telegram: [sdq1/notifiche.py](https://github.com/claudioterzi/Claudio/blob/main/sdq1/notifiche.py) (`_risposta_claude` = la voce; catena Anthropic→Gemini; «Rosso Rosso Rosso» deterministico) + webhook in [tarocchi_web.py](https://github.com/claudioterzi/Claudio/blob/main/tarocchi_web.py)
- CUSTODE (Airbnb): [custode/](https://github.com/claudioterzi/Claudio/tree/main/custode)
- Studio creativo: [studio/](https://github.com/claudioterzi/Claudio/tree/main/studio) — generators, catalogo commerciale

## 6 · I comandi (dal terminale, nella radice del repo)

```bash
# rigenerare il Sistema C dopo una modifica
python3 studio/parfums/codice_olfattivo.py   # canone + catalogo
python3 studio/parfums/genera_libro.py       # il Libro
python3 studio/parfums/genera_atelier.py     # l'Atelier
# (se cambi l'Excel dell'organo, prima:)
python3 studio/parfums/converti_organo.py    # richiede openpyxl

# provare il sito in locale
pip install flask && python3 tarocchi_web.py  # → http://localhost:5000

# salvare (la memoria vive nei commit)
git add -A && git commit -m "..." && git push
```

## 7 · Regola d'oro della continuità

Ogni cosa importante finisce **committata su main**: è l'unico stato che
sopravvive. Ogni nuova creazione riceve: una voce in `creazioni.html`,
una riga nella COSTELLAZIONE (questa e quella in MEMORIA), e — se è un
documento — una copia su Drive.

*ALAKTA ANEN — la scia è memoria che cammina.*
