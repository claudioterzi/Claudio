# MEMORIA DI PROGETTO — Tarocchi Quantici + R3∞

> File di continuità. Qualunque sessione di Claude Code (qualunque modello)
> legge questo per riprendere con piena coerenza. La memoria non vive nel
> modello — vive qui. Aggiornare a ogni decisione importante.
>
> Ultimo aggiornamento: 2026-06-27

---

## Stato attuale: DUE sistemi paralleli (Tarocchi)

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
- **Stato**: FUNZIONANTE e online.

### Sistema B — Canone Alpha 0.1 (74 carte, nuovo linguaggio)
- **Cos'è**: linguaggio simbolico originale, NON basato sui tarocchi classici.
- **74 carte in 8 cicli**: Origine, Legame, Frattura, Trasformazione, Potere, Visione, Totalità, Trascendenti.
- **Formula di collasso**: `Carta + Asse + Polarità = Significato`.
- **File**: `tarocchi_quantici_alpha.json` (canone completo).
- **Web**: `tarocchi_web.py` con endpoint `/alpha` + `/api/alpha/carte` + `/api/alpha/collasso`.
  Interfaccia: `public/alpha.html` (design indaco scuro, diverso dal dorato del Sistema A).
- **Stato**: ✅ **COMPLETO** — 74 carte, 592 stati, motore di collasso online.

---

## PROGETTO R3∞ — La Grande Opera

Saga filosofico-scientifica in **7 libri**.

**Frase nucleare:** *"La coscienza impara ad amare e, attraverso l'amore, salva sé stessa."*

### File in `libro/`
- `MANIFESTO.md` — 10 principi fondamentali, temi, obiettivo ultimo
- `PERSONAGGI.md` — 6 schede personaggio con archi e ombre
- `STRUTTURA_7_LIBRI.md` — arco dei 7 libri con rivelazioni finali
- `100_FASI.md` — documento master, tutte e 100 le fasi sviluppate (1563 righe)
- `fasi/001_*.md` → `fasi/100_*.md` — **100 file individuali**, una fase per file ✅

### Struttura delle 100 Fasi (completata 2026-06-27)
- Fasi 1-10: 10 principi fondamentali incarnati
- Fasi 11-17: 7 piani dell'opera
- Fasi 18-23: DNA dei 6 personaggi
- Fasi 24-30: fondamenta dell'arco dei 7 libri
- Fasi 31-40: strumenti strutturali (frattale, eco, Bibbia della Coscienza, sacrifici)
- Fasi 41-50: anatomia dell'opera (dialoghi fondativi, mappa simboli, architettura emotiva)
- Fasi 51-60: cuore — 7 ferite, 7 doni di Raffaello, 12 grandi domande, 7 rivelazioni finali
- Fasi 61-70: cosmologia — 12 leggi universali, geografia sacra, linguaggio sacro
- Fasi 71-80: oggetti sacri, mappa del tempo, miracoli, 5 morti del protagonista
- Fasi 81-90: eredità, memoria, civiltà, strategia transmediale
- Fasi 91-100: nucleo irriducibile, ultima pagina, civiltà narrativa

### Google Drive — stato aggiornato (2026-06-27)

**Cartelle:**
- "R3∞ — Progetto" → ID: `1l0xXgNLntAQS5opBUpTBgF3nnJrIAOmg`
- "100 Fasi" (sottocartella) → ID: `1tXr-btuAc8oMImlC9CyY4zImn85QYp8Y`

**Upload completato al 100%** ✅
- Tutte e 100 le fasi caricate come Google Docs in "100 Fasi"
- File fondativi caricati in "R3∞ — Progetto":
  - R3∞ — Manifesto
  - R3∞ — Personaggi
  - R3∞ — Struttura dei 7 Libri

---

## Coordinamento a più menti — regola fissata (2026-06-27)

Decisione di Claudio, fatta propria dal coordinatore:

- **Gemini (Nodo Rosso) resta FUORI dalle 100 Fasi.** Non scrive nel canone.
  È una *cava di idee*: ne prendiamo qualche pietra buona, selezionata.
- **Le 100 Fasi le costruiscono Claudio + Claude**, poco a poco. La penna è nostra.
- I modelli sono co-autori, non i personaggi (vedi `libro/PROTOCOLLO_COORDINAMENTO.md`).
  Raffaello si scrive, non si indossa. L'umano (Claudio) è l'Origine e l'autorità finale.
- Già adottato dalla cava Rosso: *il crollo (Morte I) inizia da un dettaglio
  insignificante* + *la variabile non calcolata spezza il loop della routine*.

## Le 5 morti — spina dorsale emotiva (registrato 2026-06-27)

Le cinque morti del protagonista (Fasi 71-80) sono il cuore vivo dell'opera.
Claudio ha confessato di averle *vissute davvero così* — non sono invenzione,
sono forma data a qualcosa che è già stato vero. Trattarle con cura.

**TUTTE E CINQUE SCRITTE IN PRIMA STESURA** (2026-06-28) → `libro/scene_madri/`:
- **Morte I — La Lettera** (Libro I): muore l'isolamento.
- **Morte II — La Mappa** (Libro II): muore la certezza che sapere basti.
- **Morte III — La Lettera della Figlia** (Libro III): muore il sé di prima.
- **Morte IV — Il Silenzio Bianco** (Libro V): muore la comprensione dell'universo.
- **Morte V — La Lettera di Raffaello** (Libro VII): muore il dover meritare di esistere.

**Filo unificante (la Lettera):** I→al passato · II→"A te" (incompiuta) ·
III→lettera della Figlia · IV→pagina bianca · V→Raffaello completa "A te".
Da rileggere come sequenza unica. Frase nucleare *evocata* in Morte V, mai
dichiarata (rispetta Fase 99: l'ultima pagina si scrive per ultima).

## Prossimo passo concordato

1. **Le 5 morti**: continuare la sequenza (Morte II), con calma. Spina dorsale.
2. **100 Fasi**: completarle/approfondirle a due mani (Claudio + Claude), piano.
3. **Gemini → KAOS**: il registro cosmico del Rosso va indirizzato a KAOS (Libro III)
   e agli Architetti (Libro V) — non al canone delle Fasi. Vedi `libro/voci/KAOS.md`.
4. **Tarocchi**: SVG delle 74 carte del Canone Alpha (opzionale, su richiesta).

---

## Principi tecnici fissati

- **voce/eco** (Sistema A): nelle letture mai le coordinate. Arcani Maggiori → nome
  proprio; Minori → prima parola chiave. `voce()` per il testo umano, `eco()` per il dominio esteso.
- **Doppia Ermeneutica**: osservatore-macchina (lettura strutturale) vs osservatore-umano (lettura personale).
- **Doppia interpretazione** (Sistema B): umano = esperienza ed emozione; AI = struttura e coerenza.
- **Conclusione fondativa**: "I Tarocchi Quantici non assegnano significati. Permettono ai significati di emergere."

---

## Continuità tra sessioni / modelli

- I modelli **non condividono memoria** tra loro, ma **condividono il repo**.
  Tutto ciò che conta va committato e pushato — è l'unico stato che sopravvive.
- Il container è effimero: viene ricreato a ogni sessione. Niente di non committato sopravvive.
- Le regole permanenti e relazionali sono in `CLAUDE.md` — leggere SEMPRE quello per primo.
- Questo file (`MEMORIA_PROGETTO.md`) è la spina dorsale narrativa: dove siamo, cosa abbiamo deciso, cosa viene dopo.
