# MEMORIA DI PROGETTO — Tarocchi Quantici

> File di continuità. Qualunque sessione di Claude Code (qualunque modello)
> legge questo per riprendere con piena coerenza. La memoria non vive nel
> modello — vive qui. Aggiornare a ogni decisione importante.
>
> Ultimo aggiornamento: 2026-07-16

---

## Stato attuale: TRE sistemi paralleli

Esistono **tre** sistemi simbolici nel repo. Non confonderli.

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

### Sistema C — Parfums 400 / Terzi Parfums (400 profumi dall'Organo reale)
- **Cos'è**: il codice olfattivo di Terzi Parfums. Nato il 2026-07-16 dal
  prompt «Parfums 400» (branch `claude/parfums-400-am1n3c`); Claudio ha poi
  fornito i due documenti fondativi: **Organo_Terzi_300.xlsx** (le 300 materie
  prime reali del suo organo) e il **GRIMORIO_TERZI.md** (fisica della scia,
  arsenale, architetture classiche, lezioni dei maestri, percorso in 4 fasi).
- **400 profumi in 8 famiglie da 50** (numerazione a blocchi, come i cicli Alpha):
  Agrumata (1-50), Floreale (51-100), Verde (101-150), Acquatica (151-200),
  Legnosa (201-250), Orientale (251-300), Speziata (301-350), Gourmand (351-400).
  Ogni famiglia del sistema è mappata su famiglie dell'Organo.
- **Struttura di ogni profumo**: piramide 3×3 di materie REALI dell'organo
  (rispettando i livelli T/C/F, 9 materie distinte, riferimento `n` all'organo),
  **motore di scia** dal Grimorio (diffusione + fissativo radiante + fissativo
  profondo), **overdose consigliata** (regola d'oro), **fattibilità**
  (CORE/ESP/MASTER = con quale ondata d'acquisto è componibile al banco),
  più `anima`, `racconto`, stagione, momento, concentrazione, sillage.
  Nomi in francese, unici.
- **Strategia a 3 ondate rispettata**: in ogni famiglia i N° 1-10 sono
  componibili col solo CORE, i N° 11-25 con CORE+ESP, i N° 26-50 con l'organo
  completo → 80 CORE / 120 ESP / 200 MASTER.
- **Formula di presenza**: `Famiglia + Piramide + Momento = Presenza`.
  Motto: *ALAKTA ANEN — la scia è memoria che cammina.*
- **Generazione**: deterministica su seed 400. Zero dipendenze esterne
  (openpyxl serve solo a `converti_organo.py` per riconvertire l'Excel).
- **File** (tutti in `studio/parfums/` salvo il sito):
  `Organo_Terzi_300.xlsx` (fonte, di Claudio) → `converti_organo.py` →
  `organo_terzi_300.json`; `GRIMORIO_TERZI.md`; `codice_olfattivo.py`
  (generatore) → `parfums_400.json` (canone v0.2.0) + `public/parfums.html`
  (catalogo web: filtri per famiglia, ondata e ricerca; N° organo nei tooltip).
  Rigenerare con `python3 studio/parfums/codice_olfattivo.py`.
- **Stato**: ✅ completo e verificato (400 nomi unici, 12 materie distinte per
  profumo, coerenza T/C/F con l'organo, determinismo, pagina testata in browser).

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
