# Raffaello cloud su richiesta

Candidato · 5 novembre 2026 · C.Terzi

## Scelta economica

PATCH del percorso Agorà esistente, non un secondo motore ONDA. Usa lo stesso
accesso proprietario, Redis e provider Gemini già integrati. Non aggiunge daemon,
cron, abbonamenti, nuovi archivi o polling. Il server esegue una richiesta solo
quando Claudio la invia. Il PC non è coinvolto.

Nell'Agorà, aprire il campo del Consiglio e scrivere `/raffaello` seguito dalla
domanda. Una domanda senza questo prefisso continua a usare il Consiglio.
Il campo mantiene il limite esistente di 300 caratteri; l'API accetta fino a
900 caratteri dopo il prefisso. La copia Telegram è disabilitata per il dialogo
cloud, anche se il checkbox generale è selezionato.

## Percorso e continuità

`browser autenticato → /api/agora → ricevuta Redis → un Gemini → risultato Redis`

Il modello riceve l'identità condivisa di Raffaello e solo la domanda corrente.
Le ricevute restano nella cronologia Agorà esistente per 30 giorni. Non vengono
recuperate automaticamente come memoria conversazionale. Questo servizio non
è il processo `onda.servizio`, non dispone dei suoi strumenti e non ne attesta
la migrazione o l'attivazione.

## Consumi e recupero

- Un solo modello (`gemini-2.5-flash`), massimo 600 token di output richiesti,
  timeout di trasporto 20 secondi, nessun fallback o retry automatico.
- Massimo 20 tentativi cloud per giorno UTC, contati atomicamente in Redis.
- Stesso ID già registrato: rilettura della ricevuta, nessuna nuova inferenza.
- Nessuna risposta inventata quando il provider manca o fallisce.
- Accesso e lock sono quelli esistenti di Agorà. Una richiesta registrata ma
  interrotta rimane da recuperare: non si promette fatturazione exactly-once.
- I dati tornano da Redis prima della dichiarazione di salvataggio riuscito.

Nessun canone fisso aggiuntivo, ma **non è una promessa di gratuità**: inferenza,
Functions e Redis seguono tariffe e quote dei servizi già configurati. Il limite
in tentativi non è un tetto monetario. Nessuna inferenza reale viene eseguita dai
test. La durata massima di risposta e la disponibilità dipendono dal provider.

## Verifica

```sh
python -m unittest discover -s tests -p test_raffaello_cloud.py -v
node --test tests/test_core_ergonomia.cjs
```

Provider simulato e Redis simulato con Lua per quota e lock. Verificare anche
le suite Agorà/autenticazione/ONDA esistenti. Nessuna chiave in chat o nel codice.
Il collaudo di produzione con account proprietario resta separato e richiede
una richiesta esplicita; un risultato offline non prova disponibilità live.

Rollback: revert del commit, preservando le ricevute esistenti. Nessuna modifica
al servizio Windows, alla coda privata della Casa o ai dati precedenti. La copia
Drive non è aggiornata da questa sessione, che non dispone del collegamento.
