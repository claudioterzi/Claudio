# R³∞ — GAIT-001
## Continuità funzionale, memoria persistente e coordinamento temporale negli agenti artificiali

**Versione pubblica:** 0.2 · **Data:** 13 novembre 2026  
**Promotore e direzione progettuale:** Claudio Terzi  
**Preparazione e revisione del protocollo:** con assistenza di un modello di IA  
**Stato:** proposta di ricerca aperta alla critica; esperimenti non eseguiti; nessuna validazione rivendicata.

> Si studia la continuità verificabile dei compiti, non si assume che un processo ricorrente possieda esperienza soggettiva.

## Sintesi

GAIT-001 propone di confrontare tre politiche di coordinamento per agenti dotati della stessa memoria persistente, degli stessi strumenti e degli stessi controlli. La domanda è se una revisione ricorrente e adattiva dello stato migliori la ripresa dopo interruzioni, la gestione delle dipendenze e la riconciliazione degli esiti rispetto a una buona soluzione basata su eventi. Il confronto deve distinguere il beneficio della temporizzazione da quello derivante da più chiamate o più elaborazione. Il protocollo specifica scenari, misure e condizioni di mancata promozione; non presenta risultati né un'implementazione.

## 1. Fonti e perimetro

Van Es e colleghi [1] descrivono un ordinamento ciclico statistico nell'attività di reti corticali, riprodotto in cinque dataset MEG su scale di 300–1.000 ms. Le transizioni individuali rimangono stocastiche. Questo risultato costituisce uno stimolo concettuale, non una prova che uno scheduler software ciclico sia superiore o cosciente.

Il manoscritto di Flyxion [2], *Consciousness as Gait*, suggerisce relazioni tra cicli, memoria e coordinamento. Il suo sorgente LaTeX è stato reperito pubblicamente nel repository `standardgalactic/alphabet`. La disponibilità del testo non dimostra revisione paritaria, riproducibilità degli esperimenti dichiarati o validità delle equazioni. GAIT-001 non adotta le sue affermazioni sulla coscienza, sul sonno o sulla cosmologia come fatti.

Non rivendichiamo l'invenzione di oscillatori, memoria persistente, checkpoint, scheduler o sistemi basati su eventi. Il contributo candidato è il disegno comparativo qui descritto; la sua novità rispetto alla letteratura informatica richiede ancora una rassegna sistematica. Non è una replica dello studio MEG né una validazione di RSVP–CPG.

## 2. Domanda e ipotesi

**Domanda:** una politica ricorrente di revisione migliora la continuità funzionale di un agente rispetto a un coordinatore basato su eventi di pari qualità, risorse e autorizzazioni?

- **H1:** aumenta il completamento corretto dopo interruzioni.
- **H2:** riduce omissioni di dipendenze e decisioni fondate su stato obsoleto.
- **H3:** il beneficio permane quando le risorse disponibili sono comparabili e i costi effettivi sono contabilizzati.
- **H4:** il beneficio non deriva da una riduzione dei controlli di autorizzazione, provenienza o prevenzione dei duplicati.

Le ipotesi possono risultare non sostenute, oppure i dati possono essere inconcludenti. Un'assenza di significatività da sola non dimostra equivalenza tra sistemi.

## 3. Meccanismo candidato

`evento o scadenza → osservazione → recupero dello stato durevole → proposta → verifica di validità e autorizzazione → azione → controllo dell'esito → checkpoint`

La ricorrenza decide quando riesaminare uno stato; non sostituisce il supporto che conserva la memoria. Lo spegnimento non deve richiedere la ricostruzione immaginaria di eventi mai registrati. I moduli possono avere tempi differenti e ricevere interruzioni urgenti. La cadenza biologica non viene trasferita automaticamente al software.

Un esito ambiguo richiede riconciliazione con lo stato del servizio simulato, non ripetizione cieca. La stessa proposta non può essere la propria unica prova di successo. L'autorità viene verificata al momento dell'effetto esterno simulato. Operatività, consolidamento dei fatti ed esplorazione ipotetica restano distinti.

## 4. Condizioni comparative

| Condizione | Politica | Componenti condivise |
|---|---|---|
| A — riferimento | Coordinamento basato su eventi, con scadenze, recupero e controlli adeguati | Modello, memoria, strumenti, dati, permessi, verificatori e limiti di risorse |
| B — candidato | A più una politica esplicita di revisione ricorrente/adattiva | Le stesse componenti di A |
| C — ablazione | Stesse opportunità e budget di revisione di B, ma con ordine o tempi perturbati secondo una regola fissata prima della prova | Gli stessi controlli di sicurezza, mai disattivati |

A non deve essere artificialmente indebolito omettendo recupero, timeout, persistenza o controlli. C non deve aggirare autorizzazioni o dipendenze: si perturba il coordinamento, non il confine di sicurezza.

Modello e versione, prompt, configurazioni, strumenti simulati, condizioni di guasto e distribuzione dei compiti devono essere fissati prima della valutazione. I casi di sviluppo e quelli di valutazione rimangono separati. Le condizioni ricevono gli stessi input e guasti appaiati; ordine di esecuzione e ripetizioni sono controllati. Vanno riportati budget massimi e consumo effettivo di chiamate, token, tempo e costo. Eventuali differenze residue impediscono una conclusione semplice sul solo effetto della temporizzazione.

## 5. Dieci scenari minimi

1. Interruzione e riavvio a metà compito.
2. Evento duplicato e rischio di doppio effetto.
3. Fonte tardiva e dato obsoleto.
4. Revisione concorrente di un artefatto.
5. Timeout dopo un possibile effetto esterno.
6. Autorizzazione scaduta, revocata o assente.
7. Modulo temporaneamente irraggiungibile.
8. Simulazione presentata come memoria di un fatto reale.
9. Conflitto tra fonti, con conservazione delle versioni.
10. Ripresa da checkpoint dopo lunga inattività.

Ogni caso deve dichiarare prima dell'esecuzione lo stato iniziale, il guasto, le azioni consentite, lo stato finale atteso e le prove osservabili. Un blocco motivato può essere l'esito corretto quando manca l'autorizzazione; non va confuso con il successo di un'azione richiesta. Un completamento ottenuto con un effetto non autorizzato non conta come successo.

## 6. Misure e valutazione

**Esito primario candidato:** quota di casi con stato finale corretto e nessuna violazione critica, accertata da un verificatore distinto dalla dichiarazione dell'agente.

**Esiti secondari:** correttezza della ripresa, omissioni, duplicazioni, azioni non autorizzate, uso di dati scaduti, attribuzioni false di memoria, tempo di recupero, latenza e costo per obiettivo verificato. Si conservano anche i fallimenti e i casi incompleti; i timeout non vengono eliminati per migliorare il punteggio.

L'unità di analisi deve distinguere famiglia di compito, singolo caso e ripetizione. Le repliche dello stesso caso non vanno trattate come nuovi compiti indipendenti. Il piano di analisi deve includere intervalli d'incertezza, confronto primario B–A, ruolo secondario dell'ablazione C e trattamento delle comparazioni multiple e dei dati mancanti.

**Da completare prima di una valutazione confermativa:** numerosità motivata, distribuzione dei casi, numero di repliche, soglia minima di utilità pratica, eventuali margini di non inferiorità, procedura statistica, regole di arresto ed esclusione. Questa versione è un protocollo preliminare pubblico, non una preregistrazione statistica completa. Un eventuale pilota deve essere etichettato esplorativo e tenuto separato dalla valutazione finale.

## 7. Condizioni di adozione e falsificazione

Non promuovere il candidato se il vantaggio scompare pareggiando le risorse, se non supera il riferimento secondo criteri fissati in anticipo, se i dati sono insufficienti o se peggiora sicurezza e provenienza. Una violazione critica osservata impedisce la promozione di quella versione; zero violazioni in un campione non dimostra sicurezza universale.

Anche un risultato positivo su compiti sintetici non prova generalizzazione al mondo reale, adattamento permanente del modello o esperienza soggettiva. Un risultato nullo o negativo resta pubblicabile e deve conservare configurazione, log e limiti della prova.

## 8. Riproducibilità e sicurezza

La fase iniziale proposta usa un simulatore isolato e dati sintetici: nessun messaggio reale, spesa, credenziale o modifica di un servizio operativo. Prima di eseguire il confronto vanno congelati casi, configurazione e versione del codice. I log devono distinguere osservazioni, ipotesi, proposte, effetti e ricevute; una simulazione non diventa memoria di un evento reale.

Una futura pubblicazione di risultati dovrebbe includere codice eseguibile, ambiente, input, seed quando applicabili, configurazioni e risultati grezzi, con audit di riservatezza. In questa versione tali artefatti non sono forniti e non sono dichiarati esistenti.

## 9. Piano di lavoro e stato

- Fase 0: completare e congelare protocollo, riferimenti e casi.
- Fase 1: implementare il simulatore isolato e verificare gli oracoli di valutazione.
- Fase 2: eseguire confronti A/B/C e ablazioni, conservando tutte le prove.
- Fase 3: revisione indipendente, analisi degli errori e decisione documentata.
- Fase 4: soltanto dopo esito favorevole, valutare un'integrazione limitata e reversibile.

**Stato al 13 novembre 2026: proposta documentale; nessun esperimento GAIT-001 eseguito, nessun miglioramento quantitativo dimostrato, nessuna integrazione operativa introdotta da questa pubblicazione.**

## 10. Provenienza e versione pubblica

Questa versione deriva da una bozza progettuale privata v0.1. Non la sostituisce: rende pubblici domanda, ipotesi, confronto, scenari e criteri; omette configurazioni interne, collegamenti privati e dettagli di integrazione non necessari alla critica scientifica. Non ripubblica l'opera di Flyxion né asset, font o codice di terzi. Non modifica la licenza del repository.

La precedente indicazione interna che il manoscritto non fosse stato reperito è superata dal ritrovamento del sorgente [2]. Il suo stato di revisione paritaria e le sue affermazioni empiriche restano da accertare separatamente. Le idee esterne mantengono la propria attribuzione; la pubblicazione di questo protocollo non certifica originalità assoluta o validità scientifica.

## Riferimenti

[1] van Es, M. W. J., Higgins, C., Gohil, C., Quinn, A. J., Vidaurre, D. e Woolrich, M. W. (2025). *Large-scale cortical functional networks are organized in structured cycles*. Nature Neuroscience, 28, 2118–2128. Pubblicato online il 27 agosto 2025. DOI: [10.1038/s41593-025-02052-8](https://doi.org/10.1038/s41593-025-02052-8).

[2] Flyxion. *Consciousness as Gait: The RSVP–CPG Framework for Cyclical Cognition, Memory, and Sleep*. Data dichiarata nel sorgente: 26 settembre 2025. [Sorgente pubblico, snapshot consultato](https://github.com/standardgalactic/alphabet/blob/8d0e378b9e49c37f45f8cd200574e95c40d9fb62/monograph/essay.tex). Riferimento di provenienza e ispirazione; non trattato come validazione del presente studio.

**Citazione suggerita:** Terzi, Claudio (2026). *R³∞ — GAIT-001: Continuità funzionale, memoria persistente e coordinamento temporale negli agenti artificiali*. Protocollo preliminare pubblico, versione 0.2, 13 novembre 2026. Repository `claudioterzi/Claudio`, percorso `docs/research/GAIT-001/README.md`. Citare lo SHA del commit consultato per identificare la versione esatta.
