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

## Filone parallelo — CUSTODE-001 (2026-07-10)

Sistema integrale di custodia per case Airbnb, richiesto da Claudio.
Due sottosistemi che si coprono a vicenda:
- **OCCHIO**: inventario fotografico di precisione a zone (CountGD++/VLM).
- **SOGLIA**: micro-tag RFID UHF (inlay carta da incollare anche in una
  pagina di libro — tecnologia da biblioteca, NON va inventata: esiste)
  + varco d'uscita con direzione che allarma se un oggetto taggato esce.

- **Studio completo**: `idee/CUSTODE-001_sistema-custode-airbnb.md`
  (tecnologie, hardware, costi, privacy/GDPR, roadmap v0→v3).
- **Prototipo v0**: pacchetto `custode/` — modelli, motori di conteggio
  (Claude vision opzionale, fallback stub come sdq1.llm), confronto
  baseline/check-out, registro tag, varco, report integrato con incrocio
  a evidenza doppia. Demo: `python -m custode.demo`. Test: 7/7 OK.
- **Branch**: `claude/airbnb-rental-assistance-g5miim`.
- **Preventivi e piani d'azione** (2026-07-10):
  - `idee/CUSTODE-002_preventivo-piano-OCCHIO.md` — avvio 30–130 €,
    API 10–35 $/anno (Haiku+Batch), pilota in 4 fasi (8 settimane).
  - `idee/CUSTODE-003_preventivo-piano-SOGLIA.md` — config. A palmare
    ~285–655 €, config. B varco ~1.025–2.735 €, piano in 4 fasi con
    conformità GDPR. Raccomandazione: partire dalla A.
  - Budget pilota complessivo ~320–800 € (senza varco), ricorrente <300 €/anno.
- **Analisi tracker GPS/Bluetooth** (2026-07-10, CUSTODE-004): AirTag & co.
  NON sostituiscono l'RFID (costano 100–600× di più per oggetto, batterie,
  non nascondibili, anti-stalking li fa scoprire, tracciare la posizione
  dell'ospite è indifendibile per GDPR). Ruolo complementare: 2–4 AirTag
  per mazzi di chiavi e oggetti da esterno (~60–120 €, zero canoni).
  Decisione: SOGLIA resta su RFID UHF.
- **Catalogo + bottone inventario** (2026-07-10, richiesta di Claudio):
  `custode/catalogo.py` — scheda completa per ogni oggetto taggato
  (libro: autore/ISBN/posizione del tag nascosto), persistenza JSON,
  `analizza_mancanti()`. `custode/web.py` — interfaccia Flask con il
  bottone "🔍 Analizza oggetti mancanti" (porta 5001). Test 10/10,
  verificata end-to-end. Il catalogo esporta il RegistroTag per il varco.
- **Schedatura rapida a due foto** (2026-07-10): `custode/schedatura.py` —
  foto frontespizio → visione compila la scheda; foto tag → legge l'EPC
  stampato e li associa. Integrata in `web.py` (mobile-first: da iPhone
  la fotocamera si apre dai campi foto, `capture="environment"`).
  Scheda precompilata da controllare e salvare. Verificata end-to-end
  con stub; con ANTHROPIC_API_KEY usa Claude vision (Sonnet).
- **Gestione da iPhone**: sì — la web app è pensata per Safari mobile;
  i palmari UHF Bluetooth si collegano a iPhone. Nessuna app nativa
  necessaria per il pilota.
- **ONLINE su Vercel** (2026-07-10, merge su main): CUSTODE è montato su
  **https://claudio-ebon.vercel.app/custode** come blueprint dentro
  l'app dei Tarocchi (try/except: non può romperli). Variabili
  d'ambiente da impostare nel dashboard Vercel:
  - `CUSTODE_PASSWORD` (obbligatoria: senza, la pagina è aperta a tutti)
  - `ANTHROPIC_API_KEY` (per la schedatura a due foto; senza → stub)
  - `REDIS_URL` (Upstash gratuito, per la persistenza del catalogo;
    senza → /tmp effimero con banner di avviso in pagina)
- **Prossimo (v1)**: Fase 1 dei piani — mappatura zone + baseline (OCCHIO),
  campionario tag + palmare (SOGLIA); collegare il palmare Bluetooth
  al campo EPC della pagina inventario; pubblicare la web app
  (es. Vercel, come i tarocchi) per averla sull'iPhone di Claudio.

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
