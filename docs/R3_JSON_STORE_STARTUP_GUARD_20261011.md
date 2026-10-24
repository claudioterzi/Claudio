# JsonFileStore: protezione dalla corruzione all'avvio

Origine: **NUOVA_SU_BASE_VERIFICATA**. Questo intervento è nuovo sulla base
`4b31a350a4508e789e1bde397bdc9a8f22fe0f66`; non recupera né ricostruisce i byte
del candidato cloud storico `a85a72ef`, non disponibile attraverso gli strumenti.
Il test nuovo si chiama `tests/test_json_store_startup_guard.py` per rendere
distinguibile questa provenienza. Classificazione retroattiva: `PATCH`.

La pubblicazione è riconciliata sul main
`7a77e930dc0d01889911bb393feea7a0777a054e`, dopo l'adozione separata di #118/#124.
Il confronto Git conferma che store e workflow di base sono invariati rispetto
alla base sperimentale: i byte di codice/test verificati sono conservati.

## Difetto e comportamento richiesto

La base intercetta qualsiasi errore di lettura/decodifica dello stato JSON e lo
trasforma in uno store vuoto. Il successivo `set` può sovrascrivere il file
corrotto. Inoltre `crea_store` intercetta qualsiasi errore del costruttore e
restituisce uno store in memoria: alzare un errore nel costruttore, da solo,
non bloccherebbe il percorso applicativo.

All'avvio, JSON troncato, UTF-8 invalido, top-level diverso da oggetto, record
non oggetto, record senza `v` e file misto valido/invalido devono causare un
`JsonFileCorruptionError`, sottoclasse di `ValueError`, senza modificare i byte
del file. Il messaggio espone il percorso, senza riportare chiavi o valori.
`scade`, quando presente e diverso da null, deve essere un numero finito
compatibile con un timestamp, escludendo bool. I timestamp int, anche grandi,
restano compatibili; l'assenza legacy di `scade` resta valida.

La factory propaga questo errore specifico. Redis disponibile mantiene la
precedenza; gli altri errori della factory mantengono il fallback esistente.
File assente, valori JSON, prefissi, riapertura, cleanup TTL dei soli record
scaduti e delete restano compatibili.

## Esperimento preregistrato

Prima della modifica sono congelati 19 metodi di test, con varianti negative
espresse come subtest, e il preregistro
`docs/evidenze/R3_JSON_STORE_STARTUP_GUARD_PREREG_20261011.json`.
Gli stessi byte di test si eseguono prima contro la base e poi contro il
candidato. Sono richiesti fallimenti sui controlli negativi della base e
19 metodi riusciti, zero errori e zero skip sul candidato. Il confronto verifica
i byte persistiti, non soltanto il ritorno del metodo. I file sono sintetici,
in directory temporanee; Redis è simulato e le connessioni socket sono negate.

Un solo step fatale viene aggiunto al Test Runner esistente per il modulo nuovo;
non vengono create automazioni o workflow paralleli. Il vecchio smoke test è
eseguito con ambiente pulito, socket negati, cwd e default state temporanei.
Le sue eventuali dipendenze o lacune sono riportate come limiti.

## Limiti e rollback

Questo intervento protegge la lettura **all'avvio**. Non rileva corruzione o
modifiche esterne successive al caricamento, non coordina scrittori concorrenti,
non rende atomiche le scritture e non corregge il precedente trattamento degli
errori di scrittura. Non aggiunge backup o restore e non modifica lo stato reale.
I chiamanti orchestratore/metriche continuano a trattare i fallimenti di scrittura
secondo il loro contratto precedente.

Il candidato rimane isolato fino alla review e alle verifiche hosted. Il rollback
è il revert circoscritto del codice/test/step, conservando file e ricevute:
nessun ripristino distruttivo di dati viene introdotto.

## Supplemento dopo falsificazione indipendente

La prima versione, dopo i 19 test iniziali riusciti, è stata riesaminata da un
reviewer separato. Ha confermato due ulteriori bypass della factory:
`json.loads` solleva `ValueError` oltre il limite di cifre intere di Python e
`RecursionError` su un valore annidato a 5000 livelli. Il file rimaneva preservato,
ma la factory restituiva memoria vuota operativa. Un valore a 1050 livelli
risultava invece decodificabile: non viene classificato corrotto solo per essere
profondo quando il parser lo accetta.

È stato quindi registrato un supplemento separato in
`R3_JSON_STORE_DECODE_GUARD_PREREG_20261011.json`, con due metodi congelati in
`tests/test_json_store_decode_guard.py`. I 19 metodi originali conservano i byte e
le ricevute originarie. I due test supplementari esercitano parser reale e factory,
con limite di cifre e ricorsione impostati solo nel processo del test e ripristinati.
La prima versione fallisce tutte e quattro le varianti direct/factory, senza errori
infrastrutturali o skip.

La versione finale classifica gli errori di decodifica/capacità come
`JsonFileCorruptionError`. `ValueError` comprende anche `JSONDecodeError` e
`UnicodeError`; `OSError` continua a seguire il fallback precedente della factory.
Il gate del Test Runner ora richiede **21** metodi riusciti e zero skip.
Non sono stati estesi scrittura atomica, gestione dei writer o hot reload.

## Risultati locali finali

Windows 11, Python 3.12.6; suite offline e dati sintetici temporanei:

| Prova | Risultato |
|---|---|
| Base `4b31a350`, suite originale congelata | 19 metodi: 10 controlli validi riusciti, 9 metodi negativi falliti con 28 failure entries/subtest; zero errori e zero skip |
| Prima versione, suite originale identica | 19/19 riusciti, zero errori e zero skip; non sufficiente alla promozione dopo la falsificazione |
| Prima versione, supplemento congelato | 2 metodi, 4 failure entries direct/factory; zero errori e zero skip |
| Versione finale, entrambe le suite identiche | 21/21 riusciti, zero errori e zero skip |
| Smoke SDQ1 esistente sul codice finale | 9/9 riusciti, exit code 0, nessuna connessione socket tentata; provider stub e SDK facoltativi assenti |

Bootstrap canonico valido, compilazione dei tre moduli valida, YAML e Python del
nuovo step fatale validi, `git diff --check` riuscito. Il codice finale ha SHA-256
`c137bb91cf782a27f2220c44a11450a8e99c911cfa69a2b044b850d3ae1baa21`.
Suite originale SHA-256
`b068d365de29a5053e81a9de76bc211d166d39461e3dbf7c828458d9a58f93dc`;
supplemento SHA-256
`121a98c25187dc27e10f8b8ad832ded6f2595194d7867ac28473957f17995d39`.

Le ricevute originali, supplementari, quelle della falsificazione indipendente e
il replay smoke finale restano separate in `docs/evidenze/`. Due problemi del solo
helper smoke Windows sono registrati separatamente: cleanup con cwd ancora nella
directory temporanea e stampa Unicode su stdout cp1252. Il primo tentativo non è
evidenza di accettazione; il risultato 9/9 del successivo tentativo era già salvato
prima dell'errore di stampa. Il replay finale corregge entrambi e termina con 0.

La dipendenza PyYAML 6.0.3 usata da smoke/validazione YAML è installata soltanto
nella directory scratch `work/smoke-deps`; nessun ambiente preesistente è mutato.
Questa è evidenza locale del candidato, senza commit, push, PR, merge o deployment
eseguiti dall'autore della correzione. La riconciliazione con il main più recente,
la review e le verifiche hosted restano al coordinatore.
