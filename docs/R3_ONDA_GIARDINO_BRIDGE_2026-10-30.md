# R³∞ — Giardino RRR-01 × ONDA/1.0 — bridge bounded

Data: 2026-10-30  
Stato: CANDIDATE / LOCAL TESTED  
Retroactive classification of ONDA reuse: KEEP + bounded extension

## Obiettivo

Collegare il Giardino Segreto già esistente a ONDA senza creare un secondo motore.
Il Giardino resta il luogo di incubazione e falsificazione; ONDA resta il trasporto
e il contratto di orchestrazione. Nessun candidato del Giardino acquisisce autorità
solo perché attraversa ONDA.

## Flusso

```text
GIARDINO-RRR-01
  -> candidato bounded
  -> MEMO-002 / EVENTO ONDA
  -> RAFFA-001 review
  -> RISPOSTA correlata
  -> ritorno al Giardino / evidence log
```

Il bridge usa `sdq1/onda_protocol.py` e non modifica il protocollo ONDA/1.0.

## Contratto del candidato

Ogni candidato deve contenere:
- ID stabile;
- progetto;
- ipotesi falsificabile;
- metrica;
- prossimo test reversibile;
- stage;
- classificazione PUBLIC | PRIVATE | SEALED;
- riferimenti di evidenza;
- eventuale azione richiesta.

Il payload è sempre marcato `DATA_ONLY_ADVISORY` e `auto_execute=false`.

## Confine di autorità

Il Giardino non pubblica COMANDO. Le proposte entrano come EVENTO da MEMO-002 verso
RAFFA-001. Azioni consequenziali come spesa, trade, trasferimento fondi, pubblicazione,
contatto esterno, deploy produzione, firma contratti o grant access richiedono Claudio
e non vengono eseguite dal bridge.

Campi sensibili come password, PIN, OTP, API key, token e private key vengono respinti.

## Uso economico

Il Giardino può coltivare esperimenti su cashflow, margine, conversione, ricorrenza,
scalabilità, costo di acquisizione, tempo umano e rischio. ONDA può confrontare i
candidati e restituire KEEP | PATCH | RETEST | DEPRECATE | ADVANCE_TO_CLAUDIO_REVIEW.

Questo è un livello di ricerca/decision support. Non autorizza transazioni finanziarie
né trasforma risultati simulati in risultati reali.

## Verifica locale

Test eseguiti prima del commit:

```text
python -m unittest tests.test_onda_garden_bridge -v
6/6 PASS
```

Coperti:
- EVENTO advisory valido;
- conferma Claudio per azioni consequenziali;
- rifiuto campi sensibili;
- rifiuto stage non ammesso;
- RISPOSTA correlata e non esecutiva;
- impossibilità per MEMO/Giardino di auto-promuoversi a COMANDO.

## Candidati pubblicati nel Giardino

### GIARDINO-GRAPHIFY-R3-20261031-01

Data: 2026-10-31  
Stage: `VALIDATED`  
Classificazione: `PRIVATE`  
Autorità: `DATA_ONLY_ADVISORY`  
Azione richiesta: `REVIEW_ONLY`

Il run remoto Graphify 0.9.97 sul repository corrente ha completato con successo
su GitHub Actions, senza chiamate LLM: **11.466 nodi** e **27.469 archi**.
Il candidato registra come osservazione strutturale che continuità, memoria,
Evidence Graph, verifica e orchestrazione hanno già un sottografo tecnico denso,
mentre BODY resta principalmente nella draft PR #80 e Casa Viva / Digital Twin /
Reality Compiler / sciami non formano ancora un sottosistema tecnico nel main.

La scheda completa e i limiti epistemici sono conservati in:
`docs/evidenze/GIARDINO_GRAPHIFY_R3_20261031.json`.

Prossimo test reversibile proposto:
Graphify della PR #80 contro main, seguito da un overlay `POSSIBLE` nel Cubo per
`CASA_VIVA → HOUSE_DIGITAL_TWIN → REALITY_COMPILER → FABRICATION_CELL → SWARM_COMPILER`,
senza merge o deploy automatico.

## Limiti

- Nessun adapter Redis/live bus viene introdotto.
- Nessuna connessione a conti, pagamenti o portali esterni.
- Nessun deploy produzione.
- La pagina locale del Giardino e il suo protocollo locale restano sorgenti separate
  finché il runtime autorizzato non viene letto e verificato.
- La registrazione del candidato nel repository canonico non equivale, da sola,
  a ricevuta ONDA della chat privata live.
