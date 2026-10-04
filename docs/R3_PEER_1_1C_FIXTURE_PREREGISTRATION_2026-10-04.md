# R3_PEER_1_1C_FIXTURE — PRE-REGISTRAZIONE

Da congelare prima che C giri. Cinque punti, niente altro.

## 1. Seed

Fonte esterna, pubblica, pre-registrata: `SHA256(81dce982dfbd1d4b5f646b1418efbc24c8be4bf0 || "R3-FIXTURE-1000")`.
C non sceglie. C esegue.

## 2. Formato

JSONL, una riga per evento, JCS RFC 8785 canonico. Nessun whitespace extra. UTF-8. Fine riga `\n`.

## 3. Interazione

Sequenza ordinata. Ogni evento vede lo stato degli eventi precedenti. Stato iniziale: ledger vuoto, replay store vuoto, canonical memory vuota.

## 4. Distribuzione

Fissata al momento della generazione, non scelta da C. Registrata nel manifest del fixture. C genera secondo dominio definito, non secondo giudizio.

## 5. Scoring

- A:X, B:X → accordo
- A:X, B:Y, X≠Y → disaccordo
- A:UNDERSPECIFIED, B:UNDERSPECIFIED → accordo su underspecified, contato separato
- A:UNDERSPECIFIED, B:X → disaccordo
- A:X, B:UNDERSPECIFIED → disaccordo

Soglia: disaccordo < 2% su decisioni binarie del subset preregistrato.

Nessuna riclassificazione post-hoc.
