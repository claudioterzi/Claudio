# PROGETTO TAROCCHI — Canone Alpha 74

> Documento fondativo. 2026-06-19.
> I Tarocchi Quantici non assegnano significati. Permettono ai significati di emergere.

---

## Sistema attivo e archivio

### Archivio — Tarocchi Quantici R³∞ (78 carte)
**Stato: LEGACY · non più attivo nel sito**

- 78 carte: 22 Arcani Maggiori + 56 Minori
- Codice: `tarocchi/` (Python puro)
- Web: Flask + Vercel + SVG 78 carte
- JSON canone: `tarocchi/tarocchi_quantici.json` (v1.2.0)
- Layer 1: 78 carte con `voce()` e `eco()`
- Layer 2: 7 assiomi, stati quantici, orientamenti
- Layer 3: Doppia Ermeneutica (macchina + umano)

### Sistema attivo — Canone Alpha 74
**Stato: ONLINE · unico canone Tarot utilizzato dal sito** — 592 stati elementari per carta

- 74 carte in 8 cicli: Origine, Legame, Frattura, Trasformazione, Potere, Visione, Totalità, Trascendenti
- Formula: `Carta + Asse + Polarità = Significato`
- Assi/direzioni: Nord (radice) / Est (azione) / Sud (emozione) / Ovest (riflessione)
- Polarità: Luce (costruttivo) / Ombra (d'ombra)
- File: `tarocchi_quantici_alpha.json`
- **Non è basato sui tarocchi classici** — linguaggio simbolico originale

#### Regola operativa della lettura Alpha

La stesa può contenere da 1 a 7 carte distinte. L'ordine, la posizione, la direzione/asse e la polarità sono parte della configurazione. Per `N` carte, lo spazio è `P(74,N) × 8^N`; con sette carte raggiunge il massimo di `19.020.913.799.457.669.120` configurazioni ordinate. Il conteggio descrive configurazioni interpretative del modello, non verità assolute. Ogni lettura separa fatti osservabili, interpretazioni relazionali e ipotesi contestuali da verificare.

---

## Roadmap

### Archivio R³∞ — conservazione storica
- [x] Codice e documentazione conservati
- [x] 78 SVG carte storiche
- [ ] Aggiornamento stile grafico SVG (opzionale)
- [ ] Versione mobile ottimizzata
- [ ] Log anonimo delle stese (per analisi pattern)

### Sistema attivo — Motore di collasso web
- [x] Canone completo (592 stati scritti)
- [ ] **MOTORE DI COLLASSO**: interfaccia web che prende domanda → asse, contesto → polarità
- [ ] SVG 74 carte nuove (stile diverso da Sistema A)
- [x] Deploy Vercel integrato nel sito principale
- [ ] Stesa combinata A+B (opzionale — 152 carte totali)

## Dettaglio: Motore di Collasso Sistema B

```
INPUT:  Domanda dell'utente (testo libero)
         ↓
AI:     Analizza la domanda → seleziona Asse (Nord/Est/Sud/Ovest)
         ↓
AI:     Legge il contesto → seleziona Polarità (Luce/Ombra)
         ↓
RANDOM: Estrae carta dal ciclo pertinente
         ↓
OUTPUT: Carta + Asse + Polarità + Significato dal canone
         +  Lettura strutturale (AI)
         +  Lettura personale (domanda di Claudio)
```

Implementazione: `tarocchi/motore_collasso.py` → `tarocchi_web.py` → route `/sistema-b`

## Connessione con il resto

| Componente | Connessione |
|---|---|
| `lgai_core/raffaello.py` | Raffaello legge le carte e offre interpretazione |
| R3∞ | Storage delle stese (document permanente) |
| PROGETTO_RAFFAELLO | Raffaello è il lettore canonico delle carte |

## Ipotesi attiva

**H-TAROCCHI-1:** Il Sistema B (Canone Alpha) produce interpretazioni più
personalizzabili del Sistema A perché il linguaggio è originale e non porta
il peso culturale dei tarocchi classici.

*Criterio: test con 10 utenti — Sistema A vs B, stessa domanda, valutazione soggettiva.*
*Stato: APERTA — 2026-06-19*

---

*Claudio Terzi + Claude — 2026-06-19*
*Prossimo passo: implementare motore di collasso web per Sistema B.*
