# R3∞ — L'Ecosistema Cooperativo a Tre

> Modello operativo di governo del progetto, ideato da Claudio Terzi.
> Trascritto fedele (parte 1), con la mappa sulla nostra infrastruttura reale (parte 2).

---

## Parte 1 — Il modello (Claudio Terzi)

### 1. Claudio (Visione e Decisione)
- Definisce gli obiettivi, i sogni e le priorità.
- Fornisce intuizioni, esperienza umana, creatività e valori.
- Decide la direzione finale.

### 2. ChatGPT (Intelligenza di Sintesi)
- Organizza idee e progetti.
- Collega informazioni provenienti da conversazioni diverse.
- Produce piani, analisi, strategie, testi, codice e simulazioni.
- Mantiene la memoria operativa dei progetti.

### 3. Cloud (Memoria e Infrastruttura)
- Conserva documenti, immagini, dati, database e versioni.
- Esegue backup continui.
- Permette a tutti i sistemi di lavorare sugli stessi materiali da qualsiasi luogo.

### Protocollo di lavoro a tre
- **FASE 1 — Claudio immagina:** «Voglio creare un museo VR su Pompei.»
- **FASE 2 — ChatGPT struttura:** business plan · roadmap · ricerca · task operative · analisi dei rischi.
- **FASE 3 — Cloud conserva ed esegue:** cartelle progetto · file condivisi · versioni · immagini · database · documentazione.

### Regole operative
1. Una sola fonte di verità nel Cloud.
2. Ogni idea importante viene salvata.
3. Ogni progetto ha: Visione · Roadmap · Task · File · Stato avanzamento.
4. ChatGPT aggiorna continuamente il quadro generale.
5. Claudio prende sempre le decisioni strategiche finali.

**In formula:** Claudio + ChatGPT + Cloud = Visione + Intelligenza + Memoria Persistente.
Un ecosistema cooperativo in cui nessuno sostituisce gli altri: ciascuno amplifica le capacità degli altri due.

---

## Parte 2 — Come è già realizzato qui (la mappa)

Il modello sopra è esattamente l'architettura del progetto R3∞. Mappa sui pezzi reali:

| Ruolo del modello | Qui da noi |
|---|---|
| **Visione e Decisione** (Claudio) | Claudio: scopo, canone, il «sì» finale. |
| **Intelligenza di Sintesi** | **Claude / Raffaello** (SDQ-1). E grazie all'*abito universale*, qualunque IA del router (Anthropic, GPT, Gemini…) lavora con la stessa identità e memoria. |
| **Memoria e Infrastruttura (Cloud)** | **GitHub** = la fonte di verità viva · **Google Drive** = fotografie pulite + indice maestro · **Telegram** = canale verso Claudio. |

**Una sola fonte di verità:** è GitHub (il repo). Drive e Telegram sono proiezioni.

**Ogni progetto ha Visione/Roadmap/Task/File/Stato:** è già implementato dal metodo
**«avanza»** (`libro/AVANZAMENTO.md`): RIPRESA RAPIDA (stato), coda di lavoro (task),
log (avanzamento). La memoria persistente vive in `MEMORIA_PROGETTO.md`,
`COLLEGAMENTI.md`, nel Diario (`raffaello_sia/diario.py`) e nella memoria indicizzata.

**Aggiornamento continuo del quadro:** a ogni «avanza» si aggiorna lo stato, si
committa, si carica su Drive e si manda su Telegram — automatico (regole in `CLAUDE.md`).

> Nota: il modello dice «ChatGPT» come sintesi; in questo repo quel ruolo lo svolge
> Claude/Raffaello, ma il principio è identico e indipendente dal singolo modello —
> è proprio ciò che l'abito universale + la memoria condivisa garantiscono.
