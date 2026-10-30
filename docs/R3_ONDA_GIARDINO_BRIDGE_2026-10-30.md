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

## Limiti

- Nessun adapter Redis/live bus viene introdotto.
- Nessuna connessione a conti, pagamenti o portali esterni.
- Nessun deploy produzione.
- La pagina locale del Giardino e il suo protocollo locale restano sorgenti separate
  finché il runtime autorizzato non viene letto e verificato.
