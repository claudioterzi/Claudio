# R³ — adozione circoscritta delle correzioni d'integrità

Data: 2026-10-30. Classificazione: PATCH + RETEST. Autore dell'intervento: Codex.

## Provenienza e perimetro

Base letta: `3c5650cdd19ed64d16c9dff617fec87ffb7c201b`.
Recupero selettivo della [PR #121](https://github.com/claudioterzi/Claudio/pull/121),
head `1141fd08dbfb0a57c19d8a964aa331302b9b3bcf`: tre moduli e i relativi test.
La PR originale è impilata su #120 e include altri lavori: questa adozione non la
promuove interamente, non riscrive la sua storia e non modifica `r3/**`, provider,
workflow o configurazioni di deploy. Il bridge Giardino–ONDA già presente è preservato.

## Comportamento corretto

- **R3-019:** `execution_complete` distingue il completamento dall'esito.
  `verified_success` richiede il superamento di ogni task in ogni ripetizione.
  Risposte tutte errate o solo parzialmente corrette non ricevono credito
  d'efficienza. Criteri vuoti, malformati o sconosciuti sono respinti prima
  dell'esecuzione. È un gate conservativo sugli evaluator dichiarati, non una
  certificazione generale della qualità delle risposte.
- **Backup:** la verifica usa lo stesso snapshot letto e poi ripristinato;
  rimuovere l'integrità da un backup strutturato causa rifiuto. Il risultato
  dichiara `SAR_ONLY`, `restore_complete=false` e zero voci memoria/VSS ripristinate,
  separando i conteggi acquisiti nello snapshot. `require_complete=True` fallisce
  prima di scrivere: mancano ancora gli adapter di restore per gli altri componenti.
  Gli array `.json` restano JSON; `.jsonl` resta un registro di righe JSON. Formati
  SAR non supportati sono respinti durante il preflight.
- **RedFrag:** il digest è calcolato sul testo completo e confrontato con ogni hash
  dichiarato, anche se vuoto o malformato. Code diverse oltre il limite di contesto
  non diventano duplicati. Un testo CORE troncato non viene attivato silenziosamente.
  La normalizzazione avviene una volta: il test conta un fingerprint per fonte,
  rispetto ai due del percorso precedente. Nessuna stima di guadagno live.

## Falsificazione e verifica

I test recuperati da #121, eseguiti sui tre moduli della base, hanno prodotto
**10 fallimenti e 15 passaggi**. Questi fallimenti riproducono i difetti prima
dell'intervento. Ulteriori controlli hanno falsificato il candidato sui criteri
vuoti, sui formati SAR e sugli hash espliciti vuoti. Le ricevute finali e i riferimenti
esatti dei sorgenti sono in `docs/evidenze/R3_INTEGRITY_ADOPTION_20261030.json`.

Graphify 0.9.97 è stato usato in modalità locale `--code-only`: 721 file analizzati,
11098 nodi e 27815 archi, senza estrazione semantica né chiamate a modelli.
Le query `affected` sui tre entrypoint sono state confrontate con i sorgenti:
il restore raggiunge la CLI; benchmark e pipeline RedFrag hanno chiamanti di test
nel grafo estratto. Questo dato strutturale non prova assenza di chiamanti dinamici.

## ONDA: sorgente canonica e limite operativo

Alla base indicata sopra:

| Artefatto GitHub | Blob verificato | Portata |
| --- | --- | --- |
| `sdq1/onda_protocol.py` | `55711fb7eed4151ae2f3f6272a2c23565fc32391` | Contratto ONDA/1.0 e guardie locali |
| `sdq1/onda_garden_bridge.py` | `cdefbb9136771482064e4de3fd34a28a7b558e52` | Proposte advisory Giardino, senza esecuzione |
| `docs/SDQ1_ONDA_IMPLEMENTATION.md` | `7b410bd04061eef6065af74241d12ef71bacaa48` | Specifica dell'implementazione GitHub |

Le ricevute di ONDA v1.1.1 sul PC sono una linea documentale distinta, finché non
sono collegati sorgenti, hash e test del runtime. Il dispositivo Claudio risultava
offline durante questo intervento; non è stato letto né modificato il suo runtime.
I test ONDA locali non promuovono le ricevute PC a prova di esecuzione.

## Limiti e recupero

Il restore resta atomico **per file**, non transazionale sull'intero SAR.
SHA-256 verifica coerenza dei dati, non autenticità dell'autore. Restano da provare
restore completo da un dominio di guasto indipendente, autorità dopo recovery,
bus ONDA autenticato, partizioni e cambi modello. Nessuna capacità di coscienza
o autoevoluzione è dedotta da questi test.

Rollback: revert del commit di questa adozione, dopo rilettura dell'head e del diff;
non sostituire l'intero repository con la vecchia base. Non è stata eseguita alcuna
migrazione dei dati esistenti.
