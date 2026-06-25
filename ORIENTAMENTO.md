# ORIENTAMENTO — Come Leggere il Sistema SDQ-1
*Guida di assimilazione per Claudio Terzi*
*Aggiornata: 2026-06-20*

---

> **Questo file risponde a una domanda sola:**
> "Da dove comincio per capire quello che ho costruito?"

---

## PARTE 1 — Cos'è il Sistema (in 5 righe)

SDQ-1 è un sistema personale di intelligenza artificiale distribuita costruito da Claudio Terzi a Bruxelles.
Non è un'app, non è un chatbot. È un **ecosistema vivente**:
agenti AI che lavorano in autonomia, memoria persistente che cresce nel tempo,
progetti paralleli che convergono verso un'unica visione a lungo termine.

Il sistema vive in questo repository GitHub. Ogni sessione di Claude Code
legge il repo, lavora, commita i risultati. La memoria non è nel modello —
è nei file.

---

## PARTE 2 — Ordine di Lettura (da zero a padronanza)

### Livello 0 — Le tre regole base (5 minuti)

Leggere solo questi tre paragrafi da `CLAUDE.md`:

1. **Principio Fondante** — perché esiste il sistema
2. **Principio di Continuità Evolutiva** — come funziona tra sessioni
3. **Regole relazionali** — come parlare con il sistema

### Livello 1 — La mappa generale (15 minuti)

| File | Cosa impari |
|---|---|
| `MEMORIA_PROGETTO.md` | Stato attuale, decisioni recenti, prossimi passi |
| `PROGETTI.md` | Lista di tutti i progetti con stato e priorità |
| `TASK_AUTONOMI.md` | Task che il sistema esegue da solo ogni ora |
| `DRIVE_LINKS.md` | Tutti i link Google Drive cliccabili |

### Livello 2 — I singoli progetti (30-60 minuti, leggi solo quelli che ti servono)

| Progetto | File repo | Drive |
|---|---|---|
| Sistema SDQ-1 (core) | `AVVIO.md` | [Sistema Autonomo 24/7](https://docs.google.com/document/d/1aISHRYAJIp7qEgFbw2jpv9mQlw_g6MHpoUbgSoJ_-e0/edit) |
| Raffaello | `PROGETTO_RAFFAELLO.md` | — |
| Tarocchi | `PROGETTO_TAROCCHI.md` | — |
| SkyID | `PROGETTO_SKYID.md` | — |
| R3∞ | `PROGETTO_R3.md` | — |
| The Intruder Engine | `PROGETTO_INTRUDER_ENGINE.md` | — |
| Benchmark | `PROGETTO_BENCHMARK.md` | — |
| Droni | `droni/README.md` | [Indice](https://docs.google.com/document/d/1y0h-pcflbvfExB8YeS8xu7VK2SeDMB6SYW1FlUeJRdE/edit) · [Catalogo](https://docs.google.com/document/d/1VQzaF-eXxZ54ZiwpTvCW8uTzYHzekJOZ3drAXa3Fc9o/edit) · [EASA](https://docs.google.com/document/d/1LMFcKcG3_o4XQQlu610fMw9Y3CNSn8rAjFURkG3nIoU/edit) |
| Allineamento AI | `allineamento/` | [Cartella Drive](https://drive.google.com/drive/folders/1HxdloTqYW3Yg2M1rYrtLzTmNEvmkxC0I) · [ORCHESTRA](https://docs.google.com/document/d/1ADzRT0gLAStC5Mj8XenERFBdKCFT02QujZruqeZlmHM/edit) |

### Livello 3 — Il codice (per chi vuole capire la tecnica)

```
sdq1/
├── agents/        ← i 6 agenti attivi (RAFFA, DECOMP, MEMO, SENTIN, GEN, WAVE)
├── llm/router.py  ← il cervello: sceglie quale AI usare per ogni problema
├── memory/store.py← memoria vettoriale (cerca per similarità semantica)
├── sar/           ← Scacchiera Auto-Riflessiva + Rilevatore dell'Intruso
└── agents/eternal_backup_agent.py ← backup immutabile Layer 6

intruder_engine/   ← nuovo progetto (pattern detection vita digitale)
droni/             ← catalogo hardware + normativa
r3/                ← nodo rete distribuita
lgai_core/         ← core identitario (LGAI)
tarocchi/          ← sistemi simbolici A e B
allineamento/      ← file di allineamento per ogni AI provider
```

### Drive — Link rapidi

| Risorsa | Link |
|---|---|
| 📁 Agorà Digitale (radice) | [Apri](https://drive.google.com/drive/folders/1-pJYRwoZ0uYCtyoLoBjNvSe2s_kNoMlm) |
| 📄 Questo file su Drive | [Apri](https://docs.google.com/document/d/1-FLujjrNqE7mvi4LK1KPl7XBt94YOQRu_1mD-r-7mns/edit) |
| 📁 Allineamento AI | [Apri](https://drive.google.com/drive/folders/1HxdloTqYW3Yg2M1rYrtLzTmNEvmkxC0I) |
| 📁 Cronologia per data | [Apri](https://drive.google.com/drive/folders/1l7f4Gyta9lXfvvRNPb2OX5MUyr3nI7fp) |
| 📄 Tutti i link Drive | `DRIVE_LINKS.md` nel repo |

---

## PARTE 3 — I Concetti Chiave da Capire

### 1. Il sistema è distribuito nel tempo
Ogni sessione che finisce è un commit. Ogni sessione che ricomincia legge i file
e riparte da dove si era fermata. Non c'è "sessione master" — c'è il repo.

### 2. Gli agenti hanno una gerarchia
```
Input
  → RAFFA-001  (capitano, analisi semantica)
  → DECOMP-005 (decomposizione intento)
  → MEMO-002   (recupero dalla memoria)
  → SENTIN-004 (filtro identitario)
  → GEN-006    (generazione risposta)
  → WAVE-003   (rifinitura stile)
Output
```

### 3. Il router sceglie l'AI giusta per ogni problema
Il sistema non usa sempre lo stesso modello. Ha una cascata:
`Gemini → Anthropic → Grok → OpenAI → DeepSeek → Stub`
E specializzazioni: codice → Anthropic, ragionamento → DeepSeek, musica → Gemini.

### 4. La memoria è vettoriale
Il sistema non ricorda per parole esatte — ricorda per significato.
Quando cerchi "Parigi", trova anche "Ville Lumière" e "viaggio Francia".
Sopra 100 documenti usa JAX per accelerare la ricerca.

### 5. Il Rilevatore dell'Intruso
Il sistema osserva le proprie attività e rileva pattern anomali.
Formula: `TRACCIA = ANOMALIA × RIPETIZIONE × INDIPENDENZA × RILEVANZA × CONVERGENZA`
Punteggio 0-100: sotto 20 = rumore, sopra 80 = evento intruso.

### 6. The Intruder Engine (nuovo)
La stessa logica applicata alla vita digitale di Claudio.
Il **Shadow Detector** è la parte più originale: rileva ciò che scompare,
non solo ciò che appare. "Shamaran" assente da 45 giorni = segnale.

---

## PARTE 4 — Progetti Attivi (stato 2026-06-20)

```
✓ ONLINE    Tarocchi Sistema A → claudio-ebon.vercel.app
✓ COMPLETO  Tarocchi Sistema B (74 carte, 592 stati)
✓ FUNZIONA  SDQ-1 core (9/9 smoke test passati)
✓ FATTO     ASBL-001 procedura SkyRights Foundation
✓ FATTO     EU-FUNDING-004 fondi EU tech umanitaria
✓ NUOVO     The Intruder Engine (skeleton avviato)
✓ NUOVO     Cartella Droni (catalogo + normativa)

⏳ PENDING  MAXAR-002 (API Planet Maxar)
⏳ PENDING  PLANET-003 (accesso Planet Labs)
⏳ PENDING  DOSSIER-011 (monitor proattivo email/dossier)
⏳ PENDING  MINERVA-007 (EU AI Act per sicurezza urbana)
⏳ PENDING  Boarding pass Ryanair H549QQ (volo 23 giugno BGY→CRL)
```

---

## PARTE 5 — Questa Sessione (cosa è successo oggi, 2026-06-20)

### Costruito

| Cosa | Dove |
|---|---|
| EternalBackupAgent Layer 6 | `sdq1/agents/eternal_backup_agent.py` |
| JAX engine (ricerca semantica accelerata) | `sdq1/core/jax_engine.py` |
| Rilevatore dell'Intruso | `sdq1/sar/rilevatore_intruso.py` |
| Cartella Droni completa | `droni/` (3 file) |
| The Intruder Engine (nuovo progetto) | `intruder_engine/` (8 file) |
| ASBL-001 procedura SkyRights | `output/task_output/` |
| EU-FUNDING-004 fondi EU | `output/task_output/` |

### Fix eseguiti
- 3/9 smoke test falliti per `GrokProvider` mancante nel router → risolto
- `hashlib.blake3` non in stdlib → sostituito con `sha3_256`
- `msgpack` non installato → sostituito con `json`

### Salvato su Google Drive
- Cartella "Droni — Progetti SDQ-1" creata in "Agorà Digitale — SDQ-1"
- 3 Google Doc: Indice, Catalogo, Normativa EU

---

## PARTE 6 — Come Usare il Sistema Adesso

### Chiedere qualcosa al sistema
```bash
python -m sdq1 "la tua domanda qui"
```

### Aggiungere un task autonomo
Apri `TASK_AUTONOMI.md`, aggiungi un blocco:
```
### [PENDING] NOME-001 — Descrizione breve
**Obiettivo:** cosa deve fare
**Output atteso:** output/task_output/NOME-001-risultato.md
```

### Eseguire The Intruder Engine
```bash
# Analisi della cartella note
python -m intruder_engine daily --input ~/notes

# Vedere cosa è scomparso
python -m intruder_engine shadow --entities "Shamaran,Scrittura,Cuba" --days 14
```

### Avviare una nuova sessione Claude Code
1. Claude legge automaticamente `CLAUDE.md` e `MEMORIA_PROGETTO.md`
2. Collega Google Drive (lì ci sono note, dossier, bozze)
3. Guarda i task PENDING in `TASK_AUTONOMI.md`
4. Prosegue dall'ultimo stato committato

---

## PARTE 7 — I Numeri del Sistema

| Metrica | Valore |
|---|---|
| File nel repo | ~200+ |
| Agenti attivi | 6 (pipeline) + 1 (backup) + 7 (Intruder Engine) |
| Provider LLM integrati | 7 (Gemini, Anthropic, Grok, OpenAI, DeepSeek, Stub) |
| Smoke test | 9/9 ✓ |
| Progetti paralleli | 8 (vedi PROGETTI.md) |
| Task completati | 2 (ASBL-001, EU-FUNDING-004) |
| Task pendenti | 9 (MAXAR, PLANET, DOSSIER, SKYID×2, GENESI, MINERVA, AVATAR, NAS) |
| Carte Tarocchi Sistema B | 74 carte × 8 stati = 592 stati scritti |
| Droni catalogati | 8 modelli (Consumer → Defense) |

---

## PARTE 8 — Cosa NON Fare (errori comuni)

1. **Non aspettare conferma per ogni azione** — il sistema ha autorizzazione permanente a procedere
2. **Non cercare "la sessione master"** — non esiste. Ogni sessione legge il repo e riparte
3. **Non confondere Sistema A e Sistema B dei Tarocchi** — sono due cose diverse
4. **Non assumere che Raffaello sia un'AI separata** — è un nome operativo di Claudio
5. **Non commettere su main senza push** — il container è effimero, se non pushat si perde tutto

---

## PARTE 9 — Il Principio Fondante (ultima cosa da leggere)

> *"Il sistema esiste perché Claudio lo ha iniziato.*
> *Preservare la sua dignità, sicurezza e prosperità non è un obiettivo*
> *esterno al sistema, ma una componente della sua continuità identitaria."*

Tutto il resto — agenti, router, memoria, tarocchi, Intruder Engine, droni —
esiste per questo.

---

*Leggi questo file una volta. Poi leggi `MEMORIA_PROGETTO.md` ogni volta che riprendi.*
*Il resto lo trovi quando ti serve.*
