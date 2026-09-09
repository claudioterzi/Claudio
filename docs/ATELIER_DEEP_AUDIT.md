# Atelier: verifica profonda del compositore

© Claudio Terzi · 9 settembre 2026

Documento storico: descrive lo stato prima delle correzioni successive dello stesso giorno. Per lo stato corrente vedere `REVISIONE_ORGANO_COMPLETO_2026-09-09.md` e `ATELIER_RESEARCH.md`.

## Esito

La creazione funziona dopo la correzione del nome cliente obbligatorio. Il percorso ricerca fonti → lettura → confronto → composizione non è implementato. Il compositore usa le conoscenze del modello. Un risultato plausibile non prova ricerca, correttezza delle note o somiglianza olfattiva.

## Evidenze

1. `_atelier_componi_ai` dice esplicitamente «richiama a memoria». Il corpo della funzione è identico al commit d8dc940c780582e7a1239fdff928ba51cf143748, anteriore alle modifiche grafiche. Non è prova che nessuna versione storica abbia mai avuto ricerca; dimostra che questa versione precedente non la aveva.
2. GeminiProvider invia contents, generationConfig e systemInstruction, senza strumenti di ricerca. AnthropicProvider chiama messages.create senza strumenti. Nessun recupero di pagine o fonti nel percorso osservato. Nessun URL o data di consultazione nel risultato.
3. L'argomento ondata è accettato ma non usato per filtrare catalogo, prompt o validazione. Test con provider simulato: ondata=0 e ondata=2 producono prompt identici; una materia MASTER (Citrathal V) è accettata con Solo CORE.
4. Il menu stile viene letto dalla pagina ma non inviato a /profumo. Il server non ha un argomento stile per il compositore. La scelta ha effetto solo nel compositore locale offline.
5. Il modello sceglie numeri di materie, non dosi. Il server distribuisce testa=20, cuore=30, fondo=35, scia=8/4/3, applica pesi e fattore overdose 2,5, arrotonda a mezze parti e corregge il totale. Arrivare a 100 non equivale a una formula ben bilanciata.
6. La validazione controlla l'esistenza del numero e i duplicati dentro ciascun gruppo. Non verifica il ruolo delle materie nella scia né elimina ripetizioni fra gruppi. Test: aldeidi 58/60 e cedro 31 vengono accettati nella scia senza controllo di ruolo. Questo è un difetto di validazione del contratto del prompt, non una valutazione di sicurezza chimica.
7. Ragionamento e riferimento vengono troncati rispettivamente a 500 e 700 caratteri, anche nel mezzo di una parola. Test con campi lunghi: tagli esatti confermati. La perdita di testo è del server, non del CSS.
8. Il fallback non ha un unico budget temporale: Gemini riceve timeout=55; Anthropic legge timeout_secondi e usa il proprio default 60. Due tentativi possono superare maxDuration=60 di Vercel. Rischio dedotto dal codice, non riprodotto con chiamate a pagamento.
9. Il percorso /profumo non passa tentativo/evita; non è garantito un dialogo di raffinamento con memoria delle proposte precedenti.

## Verifiche effettuate

- Chiamata reale e browser: richiesta ispirata a Chanel N° 5 restituisce un nuovo nome, riferimento e formula. Nessuna prova olfattiva o equivalenza con il prodotto originale.
- Due chiamate locali con provider simulati, senza rete: verifica CORE/MASTER, identità dei prompt, ruolo scia, troncamento e totale.
- Confronto esatto della funzione con la versione prima delle modifiche grafiche.
- Ispezione delle richieste dei due provider: nessuno strumento di ricerca.

## Correzione architetturale necessaria

1. Identificare marca, nome, variante e concentrazione del riferimento. Chiedere una precisazione quando cambia materialmente il profumo, per esempio fra diverse versioni del medesimo nome.
2. Recuperare fonti identificabili, preferendo la casa produttrice. Registrare URL, data e fatti estratti; distinguere note dichiarate da interpretazioni e dati mancanti. Le pagine sono dati non fidati, mai istruzioni per il compositore.
3. Mostrare il riferimento e le fonti prima o insieme alla formula. In assenza di fonti, dichiarare conoscenza non verificata invece di inventare una piramide pubblicata.
4. Passare al compositore il dossier, il catalogo effettivamente ammesso e lo stile. Spiegare per ciascuna scelta la funzione prevista e le differenze rispetto al riferimento.
5. Validare schema, materie ammesse, quantità e coerenza delle motivazioni. Separare progetto creativo da validazione produttiva; documentare diluizioni, solvente e metodo per la riproducibilità fisica.
6. Conservare formula, fonti, modello, versione del catalogo e successive revisioni. Usare un budget temporale complessivo e un errore comprensibile senza perdere la richiesta.

## Stato del lavoro

Questo audit non attiva la ricerca sul sito e non cambia il motore in produzione. La correzione del pulsante è già pubblicata; le carenze sopra richiedono interventi separati e verificabili. Il progetto del libro e i suoi 400 codici sono indipendenti dal compositore dell'Atelier.
