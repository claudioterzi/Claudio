# Backup di stato — Raffaello / ONDA 1.0
Data: 2026-10-19

## Scopo
Checkpoint documentale dello stato di ONDA/Raffaello comunicato durante la sessione. Questo file registra i risultati e i limiti noti; **non è una copia completa del codice sorgente o dei dati runtime**.

## Riferimento dichiarato dall'ambiente di sviluppo
- Commit locale dichiarato: `ef8d144`
- Suite ONDA dichiarata: **51 test superati su 51**, nessuno saltato
- Durata dichiarata: **16,75 secondi**
- Il rapporto dell'autore afferma che Redis è disponibile e che i test con Redis reale e processi agente reali sono stati eseguiti.
- Nota di verifica: il commit breve `ef8d144` non è stato trovato tramite la connessione GitHub al momento della creazione di questo checkpoint. Verificare che sia stato pubblicato sul repository remoto prima di considerarlo un backup del codice.

## Funzionalità dichiarate collaudate
Secondo il rapporto dell'autore, lo stack Docker ha superato prove di:
- persistenza del comando STOP dopo riavvii;
- mantenimento di PAUSA dopo un ciclo down/up completo;
- riconnessione degli agenti dopo il riavvio di Redis.

È stato inoltre riportato un build riuscito dell'immagine `r3-onda:1.0` in un ambiente container x86_64.

## Architettura e componenti citati
- ONDA/1.0, creato da zero sulla base dell'incarico del 2026-10-19.
- Bus Redis con messaggi firmati.
- Adattatore per gli agenti RAFFA-001, SENTIN-004 e MEMO-002.
- CLI per stato, richieste, comandi, verifica e gestione chiavi.
- Configurazione Compose prevista per Synology DS223.
- Test citati: `tests/test_onda_envelope.py`, `tests/test_onda_redis.py`, `tests/test_onda_agenti.py`, `tests/_onda_supporto.py`.

## Stato e limiti
- **Test automatici locali:** PASS secondo il risultato riferito dall'autore (51/51).
- **Test d'integrazione con Redis reale:** dichiarati eseguiti dall'autore.
- **Stack Docker in ambiente x86_64:** prove dichiarate superate dall'autore; build dell'immagine riuscito nell'output mostrato.
- **Codice corrispondente al commit remoto:** NON VERIFICATO; GitHub non ha trovato `ef8d144` come commit del repository al momento del checkpoint.
- **Deploy e runtime sul Synology DS223 fisico:** NON VERIFICATI in questa sessione.
- **Backup completo del codice, delle chiavi e dei dati runtime:** NON incluso. Non salvare password, chiavi private o token in questo documento.

## Passi per rendere il backup completo
1. Nel repository locale, controllare `git status --short` e confermare che il commit sia `ef8d144`.
2. Pubblicare il commit sul repository remoto corretto e verificare il relativo SHA completo.
3. Conservare la specifica ONDA/1.0, la guida deploy DS223, il file Compose e i test sotto controllo versione.
4. Eseguire un backup separato e sicuro della configurazione persistente, escludendo segreti in chiaro; testare la procedura di ripristino.
5. Dopo il deploy sul NAS, aggiungere qui data, architettura, versione immagine e risultati dei test eseguiti direttamente sul dispositivo.

---
Questo checkpoint è una registrazione di stato, non una certificazione indipendente dei risultati dichiarati.
