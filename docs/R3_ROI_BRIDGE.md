# R³∞ ROI Bridge — Protocollo operativo

Autore: Claudio Terzi · C.Terzi

## Scopo

Ridurre al minimo il costo umano di coordinamento della Rete Esterna. Claudio non deve fare da centralino tra agenti. Ogni ciclo deve produrre un output verificabile e un ritorno misurabile.

## Regola Zero — niente catene di ACK

Messaggi come `ACK`, `concordo`, `sto lavorando`, `ricevuto` non entrano nel canone e non richiedono inoltro umano.

Un agente parla solo quando produce almeno uno di questi artefatti:

- patch o pull request;
- test con risultato;
- benchmark prima/dopo;
- decisione motivata con evidenza;
- obiezione che cambia il piano;
- blocco tecnico concreto con requisito minimo per sbloccarlo.

## Contratto di consegna

Ogni contributo deve avere questi campi:

```json
{
  "agent": "nome-peer",
  "task": "identificativo breve",
  "status": "DONE|BLOCKED|UNKNOWN|REJECTED",
  "artifact": "PR/test/file/decisione",
  "evidence": "riferimento verificabile",
  "delta": "che cosa è cambiato",
  "roi": {
    "time_saved_minutes": 0,
    "cost_avoided_eur": 0,
    "reliability_gain": "descrizione breve",
    "reusable_asset": true
  },
  "open_risks": ["..."],
  "next_action": "una sola azione"
}
```

## Gate ROI

Un task entra in priorità solo se soddisfa almeno una condizione:

1. fa risparmiare tempo ricorrente a Claudio;
2. evita un costo o un rischio concreto;
3. aumenta affidabilità o continuità di un sistema già usato;
4. crea un asset riutilizzabile o vendibile;
5. sblocca un'attività con valore economico o operativo immediato.

Se nessuna condizione è soddisfatta, il task resta `BACKLOG`.

## Divisione dei ruoli

Per evitare duplicazione:

- **Implementatore**: produce patch o PR.
- **Avversario**: tenta di rompere la patch, cerca falsi positivi e regressioni.
- **Verificatore**: esegue test e controlla evidenze.
- **Coordinatore**: sceglie un solo prossimo passo e misura il ROI.

Un quinto agente interviene solo se porta informazione non già coperta.

## Regole epistemiche

- `FATTO`: solo risultato verificato.
- `IPOTESI`: spiegazione plausibile non ancora provata.
- `UNKNOWN`: informazione non verificata; non equivale a silenzio o fallimento.
- `SIMULAZIONE`: scenario o test non eseguito sul sistema reale.

Consenso numerico tra agenti non promuove automaticamente un'ipotesi a fatto.

## Regole di sicurezza

- Nessun token, password o segreto in chat, issue o repository pubblico.
- Nessun push cieco su `main`.
- Le modifiche ai percorsi SOS/anti-x3 richiedono test dedicati e non possono essere effetti collaterali di altri task.
- `case ID` non va descritto come pratica di un'autorità senza prova esterna specifica.
- Nessun agente dichiara invii, alert o prese in carico senza evidenza riferita alla stessa operazione.

## Ciclo operativo minimo

1. Claudio fornisce un obiettivo o un problema.
2. Il coordinatore assegna un solo implementatore.
3. L'implementatore produce un artefatto.
4. L'avversario tenta di falsificarlo.
5. Il verificatore chiude il test.
6. Il coordinatore restituisce a Claudio **una sola sintesi**:
   - cosa è cambiato;
   - prova;
   - rischio residuo;
   - ROI;
   - prossimo passo.

Nessun altro traffico viene inoltrato a Claudio.

## Primo use case

`INSTITUTION honesty`:

- separare `non configurato`, `non tentato`, `errore`, `timeout incerto`, `inviato al canale`, `presa in carico attestata`;
- test esclusivamente mock finché non esiste un ambiente controllato;
- non modificare `escalation.ts` se il task non lo richiede;
- vietare frasi come `ho allertato le istituzioni` quando l'unica evidenza è un ID locale o un semplice successo API di invio.

## KPI del bridge

Misurare per ogni ciclo:

- numero di messaggi che Claudio deve copiare manualmente;
- minuti umani spesi;
- numero di artefatti completati;
- regressioni trovate prima del merge;
- task chiusi senza intervento di Claudio;
- valore economico o operativo stimato.

### Obiettivo iniziale

Portare il numero di messaggi manualmente copiati da Claudio a **massimo 1 per ciclo**, poi a **0** quando esiste un canale machine-to-machine autenticato.
