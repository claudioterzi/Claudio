# MEMORIA DI PROGETTO — Tarocchi Quantici

> File di continuità. Qualunque sessione di Claude Code (qualunque modello)
> legge questo per riprendere con piena coerenza. La memoria non vive nel
> modello — vive qui. Aggiornare a ogni decisione importante.
>
> Ultimo aggiornamento: 2026-06-19

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

## SDQ-1 — Sistema Autonomo (aggiunto 2026-06-18)

Claudio ha un secondo sistema parallelo ai Tarocchi: **SDQ-1**, un'orchestrazione
multi-agente automatica su GitHub Actions. Repo: `claudioterzi/Claudio` (pubblico).
Branch di sviluppo attuale: `claude/rosso-rosso-rosso-ure5A`.

### Componenti SDQ-1 (tutti in `scripts/`)

| Script | Funzione | Quando gira |
|--------|----------|-------------|
| `studio_notturno.py` | Morning brief + analisi portfolio | 2:30 Brussels (GH Actions) |
| `analisi_portfolio.py` | CoinGecko API, 35 posizioni crypto, staking yield | dentro studio_notturno |
| `sync_to_drive.py` | Sync output → Google Drive (4 cartelle) | 8:30 Brussels (GH Actions) |
| `agente_profumiere.py` | Formula profumo al giorno + clone di 12 fragranze celebri | 6:00 Brussels (GH Actions) |
| `scacchiera_quantica.py` | Motore vettoriale R³∞ — modalità demo/chat/CLI | manuale + integrabile |
| `osservatore.py` | Osserva lavoro reale → Scacchiera asincrona via Batch API | dopo Studio Notturno (GH Actions) |
| `setup_drive_folders.py` | Crea cartelle Drive (da eseguire una volta sul PC) | manuale sul PC |

### Output dirs
- `output/morning_brief/` — brief giornalieri (in git)
- `output/portfolio/` — analisi crypto (.gitignore, solo Drive)
- `output/profumiere/` — studio profumiere quotidiano (in git)
- `output/scacchiera/` — sessioni scacchiera JSON+MD (in git)
- `output/osservatore/` — analisi OSSERVATORE-1 JSON+MD (in git) · `stato.json` = batch pendenti
- `personale/` — MADRE.md e dati privati (.gitignore, solo Drive)
- `fabrizio/` — casella lettere Claudio↔Fabrizio (.gitignore, solo Drive)
- `portfolio/holdings.json` — 35 posizioni crypto (.gitignore, solo Drive)

### Google Drive — CONFIGURATO (2026-06-19)

Cartelle Drive create e IDs hardcodati in `sync_to_drive.py`.
File personali già caricati via MCP.

| Cartella Drive | ID | Contenuto |
|---|---|---|
| Agorà Digitale — SDQ-1 (root) | `1-pJYRwoZ0uYCtyoLoBjNvSe2s_kNoMlm` | radice |
| Brief Mattutini — SDQ-1 | `1nuL-2lu8gQMziHptzpMQ4NutBJLAw3Vj` | morning brief |
| Portfolio — SDQ-1 | `17Gs7ZrYYmRNect-huQ4YYiBuQdN4N5R1` | crypto portfolio |
| PERSONALE | `1iC__qD1gJ4ZzTG8ad6gj8my4P6jDxtHB` | MADRE.md, ALLIANZ_SINISTRE.md |
| Io e Fabri — Casella Lettere | `1ifyqeh7gU0qlugF1LBuZL6-p7-QH2BKH` | lettere Claudio↔Fabrizio |
| lettere (sottocartella) | `1pAy_JWYvi252n-wR7jH5KVHH0dr8MECb` | 2026-06-18_claudio.md ✓ |

**File personali già su Drive:** MADRE.md ✓ · ALLIANZ_SINISTRE.md ✓ · COME_FUNZIONA.md ✓ · 2026-06-18_claudio.md ✓

**Unico secret ancora mancante su GitHub:**
- `GOOGLE_CREDENTIALS_JSON` — JSON del service account Google
  Senza questo, il workflow `sync_drive.yml` non può autenticarsi.
  Gli IDs delle cartelle sono già nel codice — non servono altri secrets.

**Come aggiungere il secret:**
1. Vai su GitHub → repo claudioterzi/Claudio → Settings → Secrets → Actions
2. New secret: nome `GOOGLE_CREDENTIALS_JSON`, valore = contenuto JSON del service account

### Dossier attivi (personale)
- **Allianz Direct** — sinistro n° 2026 50007694, appartamento 28t Rue Guersant 75017 Paris
  - PV firmato expert Remy NGUYEN: totale riconosciuto €16.024,38 (VAN €17.339,50)
  - Multiassistance: fiche de travaux con prezzi N/D (contestata)
  - Prossimo: ricevere devis Patrick Boisseau (artigiano) sabato 21/06
  - Inviare devis a sinistres@allianzdir... con rif. 2026 50007694
- **Pelan** (dossier separato, huissier Hinoux, RG 22/08190)

### AURA-50 / Terzi Parfums
- Master: `progetti/aura50/AURA50_MASTER.md` (158 essenze, formula CLAUDIO-001)
- Formula CLAUDIO-001 "Mistero Corporeo": 10 ingredienti, MIS+SEN registri
- Ordine De Hekserij: `progetti/aura50/ordine_de_hekserij.md` (pronto da ordinare)
- Agente profumiere: genera 1 formula/giorno + studia 1 clone celebre tra 12 (Rush, Ambre d'Argent, BR540, ecc.)
- H2 (verità): prima riga in `progetti/aura50/contatti.jsonl` = progetto vivo

### Scacchiera Quantica — R³∞ · Alakta Anen
- Python: `scripts/scacchiera_quantica.py` (demo/chat/CLI, generazione Claude)
- HTML workspace: `studio/web/scacchiera.html` (UI identica al design PDF)
- Formula: score = imp×0.40 + orig×0.40 + real×0.10 + caos×0.10 · Q = media top3 × 5 (0-50)
- Tensioni preset: 8 (connessione↔solitudine, ordine↔caos, ecc.)
- Chat mode: polo1 ↔ polo2 + focus opzionale + Claude auto-genera vettori

### OSSERVATORE-1 (aggiunto 2026-06-19)
- Script: `scripts/osservatore.py`
- Workflow: `.github/workflows/osservatore.yml` (si avvia dopo Studio Notturno)
- Cosa fa: estrae tensioni reali da git log + morning brief + REGISTRO_DESIDERI
  → sottomette **Anthropic Batch API** (spare compute, -50% costo, asincrono)
  → al run successivo ritira risultati → sessione Scacchiera completa
- Output: `output/osservatore/osservatore_YYYY-MM-DD.json+md`
- Stato batch: `output/osservatore/stato.json` (batch_id + tensioni_map)
- 5 tensioni estratte automaticamente ogni giorno:
  1. costruire cose nuove ↔ riparare ciò che esiste (da feat: vs fix:)
  2. costruire il sistema ↔ risolvere la vita concreta (commit per dominio)
  3. azione immediata ↔ gestire l'attesa (da morning brief)
  4. sistema agisce da solo ↔ Claudio supervisiona (commit auto vs manuali)
  5. desiderare con precisione ↔ fare con priorità (da REGISTRO_DESIDERI)
- Non rallenta nessun workflow live. Mai in foreground. Usa Haiku (veloce, economico).

---

## Prossimo passo concordato (tarocchi)

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
