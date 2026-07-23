# MEMORIA DI PROGETTO — Tarocchi Quantici

> File di continuità. Qualunque sessione di Claude Code (qualunque modello)
> legge questo per riprendere con piena coerenza. La memoria non vive nel
> modello — vive qui. Aggiornare a ogni decisione importante.
>
> Ultimo aggiornamento: 2026-06-13

---

## Stato attuale: DUE sistemi paralleli

Esistono **due** sistemi di tarocchi nel repo. Non confonderli.

### Sistema A — Tarocchi Quantici R³∞ (78 carte, tradizionale)
- **Cos'è**: interfaccia quantica al mazzo dei tarocchi classico.
- **Carte**: 78 = 22 Arcani Maggiori + 56 Minori (4 semi × 14 ranghi: Asso→Dieci, Fante, Cavaliere, **Regina**, Re).
- **Codice**: `tarocchi/` (Python, zero dipendenze esterne).
  - `codice_simbolico.py` — Layer 1: le 78 carte, `Carta`, `voce()`, `eco()`.
  - `r3_infinito.py` — Layer 2: 7 assiomi, stati quantici, posizioni.
  - `stesa.py` — la Stesa (oggetto digitale serializzabile).
  - `ermeneutica.py` — Layer 3: `DoppiaErmeneutica` (lettura strutturale + personale).
- **Web**: `tarocchi_web.py` (Flask) + `vercel.json` + `public/index.html` + `public/cards/*.svg` (78 fronti + retro) + `public/opuscolo.html`.
- **Deploy**: Vercel → https://claudio-ebon.vercel.app
- **JSON**: `tarocchi/tarocchi_quantici.json` (v1.2.0, documento totale).
  Contiene: manifesto + principio voce/eco, Layer 1 (78 carte uniche),
  Layer 2 (stati, orientamenti, posizioni con `asse`+`forzatura_stato`, 7 assiomi),
  Layer 3, ed **esempio_stesa** completo generato live (lettura strutturale + personale).
- **Stato**: FUNZIONANTE e online.

### Sistema B — Canone Alpha 0.1 (74 carte, nuovo linguaggio)
- **Cos'è**: linguaggio simbolico originale, NON basato sui tarocchi classici.
- **Decisione canonica (2026-06-13)**:
  - Niente Bastoni / Coppe / Spade / Denari.
  - Niente numeri visibili all'utente.
  - L'utente vede solo nomi: *La Scintilla, L'Orizzonte … L'Infinito*.
- **74 carte in 8 cicli**: Origine (1-10), Legame (11-20), Frattura (21-30),
  Trasformazione (31-40), Potere (41-50), Visione (51-60), Totalità (61-70),
  Trascendenti (71-74).
- **Struttura di ogni carta**: 8 stati = `luce` + `ombra`, ciascuna con 4 assi
  (`nord`, `est`, `sud`, `ovest`).
- **Formula di collasso**: `Carta + Asse + Polarità = Significato`.
  - Esempio: *La Ferita · Sud · Luce* → Guarigione. *La Ferita · Sud · Ombra* → Paralisi.
- **File**: `tarocchi_quantici_alpha.json` (canone + manifesto + interpretazioni chiave).
- **Opuscolo A6 stampabile**: `public/opuscolo.html`.
- **Stato**: ✅ **COMPLETO**. 74 carte, 592 stati scritti (74 × 8).
  Tutti gli 8 cicli completati: Origine, Legame, Frattura, Trasformazione,
  Potere, Visione, Totalità, Trascendenti.
  - Convenzione assi: Nord = radice/inconscio · Est = azione/futuro ·
    Sud = emozione/presente · Ovest = riflessione/passato.
  - Polarità: Luce = manifestazione costruttiva · Ombra = manifestazione d'ombra.
  - Verifica canone: *La Ferita · Sud · Luce* = guarigione, *· Ombra* = paralisi (combacia col manifesto).
  - Campo `stato_costruzione` nel JSON: `completo: true`.
  - **Prossimo possibile**: collegare il canone al sito (motore di collasso:
    domanda → asse, contesto → polarità), o generare gli SVG delle 74 carte nuove.

---

## Modulo laterale: Viaggi Low Cost (2026-07-23)

Modulo indipendente dai tarocchi, stessa filosofia zero-dipendenze, stessa app Flask.

- **Motore**: `viaggi/` — `destinazioni.py` (25 mete low cost dall'Italia con
  budget/giorno, volo A/R stimato, mesi ideali, consigli) + `pianificatore.py`
  (`pianifica(budget, giorni, mese, tipo)` → proposte ordinate per punteggio,
  con margine imprevisti del 10%).
- **API** (in `tarocchi_web.py`): `GET /api/viaggi/destinazioni`,
  `POST /api/viaggi/pianifica`.
- **Web**: `public/viaggi.html` su `/viaggi` — stessa estetica oro/scuro del sito.
- **Stato**: funzionante, testato (motore + endpoint + regressione `/api/mazzo`).
- Branch di sviluppo: `claude/low-cost-trips-pjvxj6`.

### Flight Hunter v0.1 (2026-07-23) — caccia al minimo con dati LIVE

Evoluzione del modulo viaggi su proposta di Claudio ("Flight Hunter AI"),
implementata la parte solida del progetto, scartata (con motivazione scritta
in `flight_hunter/README.md`) quella in zona grigia o infattibile.

- **`flight_hunter/`** — solo stdlib, dati live dall'API pubblica Ryanair
  (farfnd, la stessa del loro sito; verificata funzionante dal container).
  - `aeroporti.py` ~120 aeroporti con coordinate, ricerca per raggio.
  - `fonti.py` interfaccia `Fonte` multi-provider + `FonteRyanair`
    (cache, rate-limit 0.35s, fallback CA bundle per proxy).
  - `motore.py` genera diretti + split via hub (self-transfer con orari reali
    verificati) + posizionamento via terra; potatura PRIMA delle richieste
    (mappe tariffe → calendari solo sui candidati; ~15-40 richieste a caccia).
  - `costi.py` costo reale: bagagli, terra, notti forzate, margine rischio.
  - `memoria.py` SQLite dei minimi + consiglio compra/aspetta (euristica
    dichiarata su storico osservato).
  - `monitor.py` giro orario, segnala solo i nuovi minimi, webhook opzionale
    (`FLIGHT_HUNTER_WEBHOOK`). Va su macchina sempre accesa, non su Vercel.
- **Escluso per scelta**: scraping comparatori (ToS), hidden city/throwaway
  (violazione contratto di trasporto, rischio scaricato sull'utente),
  fuel dump (morto), previsioni meteo/scioperi senza dati (teatro).
- **Test live**: MXP→TIA sett. 22,43€ diretto; Genova→Riga (no diretto)
  risolto split via STN ~98€ tutto incluso. Skopje scoperta: serve Wizz
  (anti-bot) o Kiwi/Amadeus con chiave — prossimo passo naturale.
- **CLI**: `python3 -m flight_hunter MXP TIA --mese 2026-09`.

---

## Prossimo passo concordato

Sistema B completo (592 stati scritti). Decisione su dove andare:

- **Opzione 1**: collegare il Canone Alpha al sito — motore di collasso
  (domanda → asse, contesto → polarità) con interfaccia web dedicata.
- **Opzione 2**: generare gli SVG delle 74 carte del Sistema B
  (stile diverso dalle carte classiche R³∞).
- **Opzione 3**: altro — Claudio decide il ritmo.

---

## Principi tecnici fissati

- **voce/eco** (Sistema A): nelle letture mai le coordinate. Arcani Maggiori → nome
  proprio; Minori → prima parola chiave. `voce()` per il testo umano, `eco()` per il dominio esteso.
- **Doppia Ermeneutica**: osservatore-macchina (lettura strutturale, stabile/riproducibile)
  vs osservatore-umano (lettura personale, unica/contestuale). La verità emerge dalla relazione.
- **Doppia interpretazione** (Sistema B): umano = esperienza ed emozione; AI = struttura e coerenza.
- **Conclusione fondativa**: "I Tarocchi Quantici non assegnano significati.
  Permettono ai significati di emergere."

---

## Continuità tra sessioni / modelli

- I modelli **non condividono memoria** tra loro, ma **condividono il repo**.
  Tutto ciò che conta va committato e pushato su `main` — è l'unico stato che sopravvive.
- Il container è effimero: viene ricreato a ogni sessione. Niente di non committato sopravvive.
- Le regole permanenti e relazionali sono in `CLAUDE.md` — leggere SEMPRE quello per primo.
- Questo file (`MEMORIA_PROGETTO.md`) è la spina dorsale narrativa: dove siamo, cosa abbiamo deciso, cosa viene dopo.
