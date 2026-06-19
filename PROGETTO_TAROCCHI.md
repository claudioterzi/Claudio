# PROGETTO TAROCCHI — Due Sistemi, Un Linguaggio

> Documento fondativo. 2026-06-19.
> I Tarocchi Quantici non assegnano significati. Permettono ai significati di emergere.

---

## Due sistemi paralleli

### Sistema A — Tarocchi Quantici R³∞ (78 carte)
**Stato: FUNZIONANTE E ONLINE** → https://claudio-ebon.vercel.app

- 78 carte: 22 Arcani Maggiori + 56 Minori
- Codice: `tarocchi/` (Python puro)
- Web: Flask + Vercel + SVG 78 carte
- JSON canone: `tarocchi/tarocchi_quantici.json` (v1.2.0)
- Layer 1: 78 carte con `voce()` e `eco()`
- Layer 2: 7 assiomi, stati quantici, orientamenti
- Layer 3: Doppia Ermeneutica (macchina + umano)

### Sistema B — Canone Alpha 0.1 (74 carte)
**Stato: COMPLETO** — canone scritto, 592 stati

- 74 carte in 8 cicli: Origine, Legame, Frattura, Trasformazione, Potere, Visione, Totalità, Trascendenti
- Formula: `Carta + Asse + Polarità = Significato`
- Assi: Nord (radice) / Est (azione) / Sud (emozione) / Ovest (riflessione)
- Polarità: Luce (costruttivo) / Ombra (d'ombra)
- File: `tarocchi_quantici_alpha.json`
- **Non è basato sui tarocchi classici** — linguaggio simbolico originale

---

## Roadmap

### Sistema A — Manutenzione e miglioramento
- [x] Online e funzionante
- [x] 78 SVG carte
- [ ] Aggiornamento stile grafico SVG (opzionale)
- [ ] Versione mobile ottimizzata
- [ ] Log anonimo delle stese (per analisi pattern)

### Sistema B — Motore di collasso web (prossimo passo)
- [x] Canone completo (592 stati scritti)
- [ ] **MOTORE DI COLLASSO**: interfaccia web che prende domanda → asse, contesto → polarità
- [ ] SVG 74 carte nuove (stile diverso da Sistema A)
- [ ] Deploy Vercel Sistema B separato o integrato
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
