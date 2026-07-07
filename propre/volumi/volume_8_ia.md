# Volume 8 — IA

> Indice. Come l'IA di Pro-Pre decide, come crea la formula, come
> apprende. Questo volume documenta il ponte tra l'enciclopedia
> (Volumi 1-7) e il motore decisionale.

## Perché questo volume esiste

L'enciclopedia non è solo materiale di formazione: è la base di
conoscenza che l'IA legge per proporre formule e protocolli. Un solo
principio guida tutto: **l'IA non usa nulla che non sia in una scheda
`verificata`**. Nessuna conoscenza "a memoria" del modello sostituisce
una scheda mancante o in bozza — se la scheda non c'è, l'IA lo dichiara
invece di inventare.

## Argomenti pianificati

- **Come decide** — dato un problema (fibra + macchia + contesto), come l'IA attraversa Volume 3 (fibra) → Volume 4 (macchia) → Volume 2 (sostanze compatibili) → Volume 5 (prodotti Pro-Pre applicabili), scartando ogni combinazione con `incompatibilita.pericolo: true`.
- **Come crea la formula** — vincoli: compatibilità (Volume 2), sensibilità della fibra (Volume 3), parametri macchina disponibili (Volume 6); output: protocollo con dosaggi e sequenza.
- **Come apprende** — casi studio (Volume 5) come feedback: un intervento documentato con esito aggiorna la fiducia sulle combinazioni usate, ma non modifica le schede automaticamente — ogni modifica a una scheda `verificata` passa da un tecnico.

## Vincolo di sicurezza non negoziabile

L'IA non deve MAI proporre una combinazione segnata come
`pericolo: true` in nessuna scheda di incompatibilità, indipendentemente
dal risultato atteso. Questo controllo è meccanico (verifica sui dati
strutturati), non affidato al buon senso del modello in quel momento.

*(Da popolare quando l'architettura del motore IA è definita —
si collega naturalmente a `sdq1/` nel repo.)*
