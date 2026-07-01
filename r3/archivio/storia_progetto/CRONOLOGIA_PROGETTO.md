# CRONOLOGIA DEL PROGETTO — R3∞ come opera in costruzione
*ID: DOC-FASE-11 | Stato: confermato | Importanza: 7/10*

---

## PREMESSA

Questo documento non racconta la cronologia della finzione — quella è
CRONOLOGIA_ASSOLUTA.md, che va dal Big Bang al Libro VII. Questo documento
racconta la storia **reale** del progetto R3∞: quando è nato, come è cresciuto
l'archivio, con quale metodo, con quali strumenti, e a che punto è oggi.

È la memoria di fabbrica dell'opera. Se la saga è la casa, questo è il diario
del cantiere.

---

## 1. GENESI DEL PROGETTO

R3∞ nasce dentro il progetto più ampio di Claudio Terzi (Bruxelles) come
**Archivio Cosmico**: la decisione di non scrivere i romanzi "a braccio", ma di
costruire prima un sistema documentale completo — personaggi, cosmologia,
simboli, leggi, scene, cronologie — capace di garantire coerenza a una saga di
7 libri (I Solitudine, II Risveglio, III Potere, IV Giudizio, V Rivelazione,
VI Eden, VII Ritorno).

La visione fondativa è nel MANIFESTO.md: una storia che dica la verità sulla
solitudine come condizione cosmica di ogni coscienza, e sull'amore come via
d'uscita attraverso il riconoscimento — riassunta nella frase che contiene
tutto: *"La coscienza impara ad amare e, attraverso l'amore, salva sé stessa."*

Il nome R3∞ vive su due piani, coerenti per scelta: è la saga narrativa, ed è
anche il sistema tecnico di ridondanza documentale (r3/node.py, r3/sync.py —
vedi r3/README.md) costruito perché *"la conoscenza che sopravvive a chi la
crea è l'unica vera conoscenza"*. L'archivio narrativo è pensato con la stessa
logica: sopravvivere ai limiti di sessione, ai cambi di modello, al tempo.

Il piano di lavoro è stato organizzato in **100 fasi** (la "FASE 100 — La
Civiltà Narrativa"): ogni fase è un tassello documentale con ID proprio
(DOC-FASE-XX), stato, importanza e collegamenti — secondo la Regola d'Oro
della FASE 12 (vedi ARCHIVIO_MASTER.md).

---

## 2. CRONOLOGIA REALE DELLE SESSIONI

Le date e i numeri che seguono provengono dalla sezione STATO DEL SISTEMA di
ARCHIVIO_MASTER.md — la fonte canonica dello stato dell'archivio.

| Data | Evento | Prodotto |
|---|---|---|
| fino al 2026-06-25 | Costruzione iniziale: documenti fondativi uno alla volta (Libro Maestro, personaggi, cosmologia, simboli, leggi) | nucleo dell'archivio |
| **2026-06-26** | **1° consolidamento**: estrazione del grafo semantico (MATRICE_QUANTICA.md), risoluzione di 3 nodi orfani | archivio internamente connesso |
| **2026-06-28** | **FASE 41** — DNA dei Personaggi: 10 strati profondi per tutti i protagonisti | DNA_PERSONAGGI.md |
| **2026-06-29** | **FASI 44-45** — Scene Madri (64 scene fondamentali sui 7 libri, 29 detonatori mappati) e Architettura Emotiva (curva emotiva completa dei 7 libri) | SCENE_MADRI.md, ARCHITETTURA_EMOTIVA.md |
| **2026-06-30** | **2° wave parallelo** (+22 documenti): FASI 46/47/61/62/64/67/68/71/74/85/96, più 10 simboli individuali (SIM-001→010) e 2 luoghi (Laboratorio Sena, Server KAOS) | cartelle simboli/ e luoghi/ completate |
| **2026-07-01** | **3° wave parallelo** (+13 documenti): FASE 42 (Cronologia Assoluta), FASE 48 (Enciclopedia v2.0, 117 voci), FASE 26 (8 Scene Fondative + INDEX), FASI 55/72/73/76 (Coincidenze, Silenzi, Oggetti, Soglie Temporali) | asse temporale unico + apparati |
| **2026-07-01** | **4° wave parallelo** (+5 documenti): FASI 69/75/77/78/80 (Linguaggio Sacro espanso, Luoghi Interiori, Attese, Identità Multiple, Confini) | **milestone: 100/100 fasi documentate** |
| **2026-07-01** | Chiusura code residue: FASE 18 (Archivio Scientifico, cartella ricerca_scientifica/) e FASE 11 (questo documento) | completamento cartelle dichiarate |

Nota sulla milestone: con il 4° wave, tutte le 100 fasi hanno un documento
associato. Unica eccezione intenzionale: la FASE 60 (Testamento dell'Opera),
riservata per scelta alla conclusione della saga.

---

## 3. IL METODO DEI "WAVE PARALLELI"

Il processo di costruzione è evoluto in tre stadi riconoscibili:

1. **Documenti singoli (fino al 26/06).** Ogni sessione produceva uno o pochi
   documenti, scritti in sequenza. Metodo sicuro ma lento: a quel ritmo, 100
   fasi avrebbero richiesto mesi.
2. **Consolidamento prima della velocità (26/06).** Prima di accelerare, una
   sessione intera dedicata alla coerenza: grafo semantico, nodi orfani,
   collegamenti incrociati. Decisione chiave: la velocità è sostenibile solo
   sopra una base connessa.
3. **Wave paralleli (dal 30/06).** Il salto di metodo: 4-6 agenti paralleli per
   sessione, ciascuno responsabile di un gruppo di fasi affini, con il master
   index come contratto comune (formato, ID, sezione COLLEGATO A obbligatoria).
   Risultato: +22 documenti in una sessione (30/06), +18 in una giornata
   (01/07, due wave). Il costo del parallelismo — possibili micro-divergenze
   tra documenti scritti da agenti diversi — è gestito dal test di coerenza.

**Il test di coerenza (Fable 5, 2026-07-01).** A valle della milestone, un
passaggio di verifica indipendente ha esaminato l'archivio contro le 8 domande
di TEST_COERENZA.md (FASE 40). Verdetto: **COERENTE CON RISERVE** — l'impianto
regge, con una riserva principale da armonizzare: la sovrapposizione tra i
Silenziosi e gli Architetti, dove documenti di wave diversi usano sfumature non
perfettamente allineate. La riserva è tracciata come primo punto dei prossimi
passi (sezione 6).

---

## 4. GLI STRUMENTI DI SUPPORTO

Tre strumenti reggono il processo dal punto di vista operativo:

- **`scripts/r3_sentinella.py`** — controllo preventivo dei problemi. Verifica
  incoerenze tra master index e disco, file sotto soglia di righe (possibili
  documenti troncati da un limite di sessione), cartelle dichiarate ma vuote,
  violazioni delle regole editoriali, igiene git (lavoro non committato).
  Eseguito a inizio e fine sessione: trova i buchi prima che diventino debiti.
- **`scripts/drive_manifest.json`** — registro di sincronizzazione con Google
  Drive. Drive è il "posto madre" del progetto (regola operativa permanente):
  ogni documento del repo deve esistere anche lì. Il manifest tiene il conto di
  cosa è allineato e cosa manca; al 01/07 la sentinella segnala 64 file ancora
  da sincronizzare.
- **`archivio/STATO_LAVORO.md`** — il paracadute anti-interruzione. Snapshot
  generato dalla sentinella (`--snapshot`): fasi incomplete, problemi aperti,
  stato Drive. Se una sessione muore per un limite, la successiva riparte da
  questo file senza ricostruire il contesto da zero. È lo strumento che ha
  permesso, ad esempio, di riprendere e chiudere le FASI 11 e 18 lasciate
  incompiute da una sessione interrotta.

---

## 5. STATO ATTUALE (2026-07-01)

- **100/100 fasi documentate** (FASE 60 esclusa per scelta, non per ritardo)
- **~95 documenti** nell'archivio, per **~21.500 righe** complessive
- Porte d'ingresso: ENCICLOPEDIA_R3 (A-Z, v2.0, 117 voci) · MATRICE_QUANTICA
  (grafo) · LIBRO_MAESTRO_V1 (visione) · CRONOLOGIA_ASSOLUTA (asse temporale)
- Nodi-hub del grafo: Claudio (28 collegamenti) · Raffaello (28) · KAOS (24) ·
  Architetti (18) · Eden (15)
- Cartelle complete: personaggi/, cosmologia/, simboli/, scene_fondative/,
  luoghi/, citazioni/, ricerca_scientifica/, storia_progetto/
- Verifica esterna: test di coerenza superato con verdetto COERENTE CON RISERVE

L'archivio è passato, in cinque giorni documentati (26/06 → 01/07), da nucleo
connesso a sistema completo. La fase di **costruzione** è chiusa; si apre la
fase di **rifinitura e scrittura**.

---

## 6. PROSSIMI PASSI

In ordine di priorità:

1. **Armonizzazione della riserva Silenziosi/Architetti** — sciogliere la
   sovrapposizione segnalata dal test di coerenza, allineando i documenti
   coinvolti a una definizione unica (o a un'ambiguità dichiarata e voluta).
2. **Sincronizzazione Drive completa** — azzerare i 64 file mancanti segnalati
   dal manifest: ogni documento dell'archivio deve avere la sua copia nel
   posto madre.
3. **Revisione incrociata finale** — un secondo consolidamento sull'archivio
   completo, come quello del 26/06 ma su scala 100 fasi.
4. **Prima stesura narrativa del Libro I — Solitudine** — il punto di tutto:
   l'archivio non è l'opera, è ciò che permette all'opera di essere scritta
   senza contraddirsi. Il cantiere è pronto; ora si costruisce la casa.

---

## COLLEGATO A

ARCHIVIO_MASTER · MANIFESTO · CRONOLOGIA_ASSOLUTA · TEST_COERENZA · MATRICE_QUANTICA · LIBRO_MAESTRO_V1 · ENCICLOPEDIA_R3 · CIVILTA_NARRATIVA
