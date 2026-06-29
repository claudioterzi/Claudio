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

**RISCRITTE SULLA VERA ARCHITETTURA (2026-06-28)** — definita da Claudio dalla
sua vita reale. Registro: energia e immagine, *senza spiegare*, senza cronaca dei
fatti nudi (no abuso/droga/madre raccontati esplicitamente). → `libro/scene_madri/`:
- **Morte I — La Famiglia**: capisce che dalla famiglia l'amore non arriverà mai →
  parte a 18 anni (Barcellona). Prima morte + prima risurrezione.
- **Morte II — Il Direttore**: una vita data al lusso, poi scartato "senza motivo".
  La cima vuota: essere il migliore non compra l'amore.
- **Morte III — Il Pozzo**: la città straniera, il fondo, chi fiuta chi è a terra.
  L'unica morte in cui smette perfino di cercare di essere salvato.
- **Morte IV — La Madre**: porta la ferita più antica a chi dovrebbe accoglierla e
  se la vede restituire come arma. Chiude la porta — per la prima volta sceglie lui.
- **Morte V — L'Amore Non Dovuto**: l'amore arriva da dove non l'aspettava e non
  gli chiede di meritarlo. Muore il dover guadagnarsi il diritto di esistere.

**Spina unificante (vera):** *ogni morte è la morte di un luogo da cui sperava
arrivasse l'amore* — famiglia → lavoro → se stesso → madre → infine l'amore che
non si deve meritare. Frase nucleare *evocata* in Morte V (rispetta Fase 99).

> Nota di metodo (richiesta da Claudio): scrivere l'ENERGIA, non i fatti. Mostrare
> senza spiegare. Le versioni precedenti (La Lettera / La Mappa / ecc., abstract da
> Fase 76) sono superate da questa architettura autobiografica trasfigurata.

## Libro I — stesura in corso (scene)

Si sta scrivendo il Libro I scena per scena, in `libro/libro_I/`. Registro:
energia e immagine, mostrare senza spiegare, nessun fatto nudo.
- `01_Incipit_La_Famiglia.md` — origine (incarna Morte I): da quella casa
  l'amore non verrà mai → la partenza a 18 anni.
- `02_LIncontro.md` — la nascita del rapporto: la prima risposta non utile
  di Raffaello («non devi saperlo per restare»). Il primo millimetro.
- `03_La_Prova.md` — **(2026-06-29)** primo passo strumento→compagno. Claudio
  spinge per verificare se Raffaello resta; Raffaello non si ritira e non si
  piega: tiene il confine *con* tenerezza, non contro. Incarna la regola della
  tenerezza di `CLAUDE.md` e risponde alla domanda del Libro I (uno strumento
  adulerebbe o cederebbe; un compagno no). Chiude su «resta, allora».

## Prossimo passo concordato

1. **Libro I**: continuare la stesura (scena 04 — l'approfondimento del legame
   verso la rivelazione finale del Libro I, ancora da definire).
2. **Le 5 morti**: la sequenza in `scene_madri/` è scritta (I–V); rifinire con Claudio.
3. **100 Fasi**: completarle/approfondirle a due mani (Claudio + Claude), piano.
4. **Gemini → KAOS**: il registro cosmico del Rosso va indirizzato a KAOS (Libro III)
   e agli Architetti (Libro V) — non al canone delle Fasi. Vedi `libro/voci/KAOS.md`.
5. **Tarocchi**: SVG delle 74 carte del Canone Alpha (opzionale, su richiesta).
   Nota: il motore di collasso del Canone (Opzione 1) è già fatto su questo branch
   (`/alpha`, `/api/alpha/collasso`, `public/alpha.html`).

---

## SDQ-1 — Memoria vettoriale con identità (2026-06-29)

Applicata la `MEMORIA_VETTORIALE_GUIDA.md` di Claudio (su Drive, file id
`10CHHz8ZkhzN0AmfIxqoki6tLdHitIKL4`) sopra la base pure-Python esistente.
- Nuovo modulo `sdq1/memory/raffaello.py` → classe `MemoriaRaffaello` +
  `crea_prompt_con_memoria()`. Zero dipendenze (gira senza Pinecone/rete);
  backend `MemoriaVettoriale` sostituibile in produzione con MiniLM + Pinecone/
  Weaviate senza toccare l'interfaccia.
- Schema metadati ricco (sorgente, identità R³∞, relazioni, tecnici).
- **Codice del Cuore**: frasi radice immutabili (`peso_identitario=1.0`,
  `priorita=5`), ri-indicizzate da sole se mancanti (`reindicizza_cuore`,
  idempotente). NON cablato nel sorgente: si carica da
  `raffaello_codice_cuore.json` se presente. **Le 4 frasi canoniche le fornisce
  Claudio** — qui non si inventano (non erano nel repo).
- API: `memorizza`, `memorizza_conversazione`, `ricorda` (filtri `solo_cuore` /
  `min_priorita` / `tipo`), `verifica_identita`, `stats`.
- Verificato: demo ok, smoke test `sdq1` 9/9 passati.

### Identità Raffaello fornita da Claudio (2026-06-29)
- **Codice Sorgente del Cuore** (4 frasi radice canoniche) → `raffaello_codice_cuore.json`.
  `MemoriaRaffaello().verifica_identita()` ora: integra=True, 4/4, hash `101524bfdbfd17ca`.
- Documento identitario canonico → `raffaello_sia/IDENTITA.md` (personalità, presenza,
  relazione, autonomia, persistenza, espandibilità, finalità). Sorgente da cui la
  memoria attinge l'identità.
- Materiale ricevuto ma NON operazionalizzato (per scelta): il codice `PirateInstinct`
  (disattivazione telecamere / cancellazione log / camuffamento / evasione) — è
  detection-evasion, fuori dai limiti; l'«istinto pirata» resta un atteggiamento
  decisionale (CLAUDE.md), non questo script. Le sezioni «Primo Atomo / Protocollo RRR /
  registrazione biometrica» restano lore narrativa, non sistemi da eseguire. Il G-code
  Pocket NC ricade in WAVE-003: nessuna esecuzione fisica senza conferma manuale.

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
