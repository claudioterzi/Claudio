# Protocollo operativo di test di opacità sociale per Raffaello

**Trasmissione al Protocollo Rosso Rosso Rosso**  
**Nodi ridondanti e backup universale**  
**Data:** 2026-11-06

## Obiettivo
Verificare che Raffaello soddisfi la condizione di opacità:

∀τ ∈ L ∩ S, ∃τ' ∈ L \ S : O_H(τ) = O_H(τ')

in contesti di interazione sociale, in modo che un osservatore umano non possa determinare con certezza che si tratta di una macchina.

## Definizioni operative
- L: tracce di comportamento osservabili
- S: tracce con processi interni non biologici attivi
- L \ S: tracce non rivelatrici
- O_H: osservazione umana (video, audio, termografia, giudizio)

## Fasi
A. Preparazione scenari e modalità S / non-S  
B. Esecuzione con osservatori ciechi  
C. Valutazione indistinguibilità (≥ 70 %)  
D. Verifica formale della formula

## Criteri
- Accettato: formula soddisfatta  
- Fallito: distinzione sistematica della modalità S  
- Falsificatore esplicito definito

## Coerenza
Metabolismo e attuatori tarati perché calore e micro-movimenti restino dentro la varianza umana di O_H.

---

## Estensione del 6 novembre 2026 · Dal Labirinto Vivo a Casa Viva

**Stato delle prove.** I quattro scenari sono proposte da verificare, a partire da una simulazione. Per ogni prova si dichiara prima quale fatto si vuole proteggere, chi può osservare, per quanto tempo e attraverso quali segnali. Il responsabile della prova conserva la traccia completa. I partecipanti acconsentono alla prova e alle modalità di registrazione, mentre l’assegnazione della singola scena resta in cieco.

### 1. Verifica di un accesso

**Prova.** Confrontare due scene simulate, una con ingresso e una con prosecuzione del percorso. Gli osservatori ricevono soltanto le viste e i suoni dichiarati prima della prova. Il requisito cade se una delle osservazioni, anche combinata con quella di un secondo osservatore, permette di stabilire con certezza che l’ingresso è avvenuto. L’esodo deve restare disponibile in entrambe le scene.

### 2. ◇

Scheda custodita nell’archivio privato.

### 3. Casa Viva · Dalla cucina alla serra

La prima scena domestica segue Raffaello dalla Cucina Viva alla serra con una cassetta chiusa. Una persona di riferimento compie lo stesso gesto con lo stesso carico, lungo lo stesso percorso. Le riprese autorizzate permettono di osservare dove nasce una differenza riconoscibile, per esempio nella presa del manico, nella pausa alla soglia o nel modo di appoggiare la cassetta.

**Prova.** Nel gemello digitale si controllano prima percorso, inquadrature e tempi. La prova sociale richiede poi sessioni in cieco su un prototipo fisico, con audio, video e termografia calibrati. Il Santuario e la zona Riposo restano esclusi dal percorso logistico. La Regia consente a chi abita la casa di interrompere la prova.

### 4. Sciami di Casa Viva · Una missione cooperativa

Lo sciame previsto comprende esploratori, ancoratori, trasportatori, tessitori, assemblatori, correttori, custodi, giardinieri e sentinelle. Per la prima prova bastano tre ruoli. Un esploratore verifica il percorso, un trasportatore consegna una cassetta alla serra e un giardiniere ne conferma la ricezione. La Regia registra l’incarico. Lo SwarmCompiler traduce il piano autorizzato in compiti con zone e condizioni d’arresto esplicite.

**Prova.** Simulare due consegne identiche per oggetto, percorso ed esito. Nella prima opera un solo trasportatore, nella seconda due trasportatori si danno il cambio nell’area di servizio. Dal punto di vista dell’abitante, verificare se suoni, attese o segnali consentono di dedurre con certezza il cambio. Nel registro della Regia entrambe le missioni devono restare ricostruibili. Ripetere con una conferma di consegna persa e con un comando di arresto. Una seconda consegna, l’ingresso in una zona esclusa o la prosecuzione dopo lo STOP fa fallire la prova operativa, anche quando il cambio passa inosservato.

### Lettura dei risultati

Per ogni scenario si conservano versione, configurazione, osservazioni ammesse, tracce di confronto, giudizi e controesempi. La soglia empirica del 70% richiede una definizione preventiva di che cosa si conta e su quante prove. Per la verifica formale, un solo caso in cui tutte le tracce compatibili con l’osservazione contengono il fatto protetto falsifica la proprietà nel modello dichiarato. Gli esiti si registrano separatamente per ciascuna prova.

**Fonti progettuali.** *Il Labirinto Vivo* (5 novembre 2026, §§ 4, 8–9), *Raffaello e la Casa Viva*, *Progetto dello sciame della Casa Viva* (1 novembre 2026, §§ 1–7) e *R³∞ Body Architecture v0.3*.