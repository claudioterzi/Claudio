# CUBO VIVO — SPEC 0.1

**Stato:** SANDBOX / CANDIDATE PROJECT  
**Primo mondo:** `Mon premier cirque / Il mio primo circo`  
**Obiettivo:** trasformare i nodi del Cubo Quantico da documenti consultabili a esperienze attraversabili, iniziando da un player 2D e conservando una traiettoria tecnica diretta verso 3D/WebXR/VR.

## 1. Principio

Il Cubo Quantico resta la mappa canonica delle opere. **Cubo Vivo** è il livello esperienziale.

Non duplica il canone: ogni esperienza deve puntare a una fonte verificabile e mantenere:

- `scene_id` stabile;
- provenienza della fonte;
- versione del trattamento;
- stato della produzione;
- relazioni con il nodo del Cubo;
- separazione fra testo originale, interpretazione scenica e asset generati.

## 2. Architettura a strati

```text
CUBO QUANTICO / R³∞
        │
        ▼
SOURCE + PROVENANCE
        │
        ▼
SCENE GRAPH (persistente)
        │
        ├──► PLAYER 2D          ← FASE ATTUALE
        │
        ├──► OPENMONTAGE BRIDGE ← produzione audiovisiva
        │
        └──► WORLD GRAPH 3D     ← fase successiva
                    │
                    ▼
                 WEBXR / VR
```

### Strato A — Source

Fonte narrativa o documentale. Nessun asset generato può sostituire la fonte.

### Strato B — Scene Graph

Una scena è l'unità persistente. Deve poter essere rappresentata oggi in 2D e domani come stanza/spazio 3D senza cambiare identità.

Campi minimi:

```yaml
scene_id: pista
source_ref: <provenance>
order: 4
location: pista-del-circo
time: pomeriggio
narrative_function: apparizione
experience_modes:
  - osserva
  - vivi
  - ricorda
visual_direction: <descrizione>
production_status: storyboard-2d
```

### Strato C — Player 2D

Il browser è il primo laboratorio. Serve a verificare:

1. ritmo delle scene;
2. transizioni;
3. prospettiva dell'utente;
4. densità del testo;
5. comprensibilità delle modalità;
6. corrispondenza fra fonte e atmosfera.

Il player non deve dipendere da immagini o video generati per funzionare: gli asset reali possono essere inseriti progressivamente.

### Strato D — OpenMontage bridge

OpenMontage non viene copiato dentro R³∞. È trattato come motore esterno di produzione.

Repo di riferimento: `calesthio/OpenMontage`.

Pipeline candidata iniziale: `cinematic`.

Mappatura prevista:

```text
Cubo Vivo source      → research input / source context
scene graph           → script + scene_plan
visual_direction      → asset direction
scene_id              → asset provenance key
generated assets      → scene asset bundle
final 2D sequence     → compose output
```

La pipeline OpenMontage resta responsabile dei propri gate e delle proprie verifiche. Cubo Vivo conserva la relazione fra gli output e la scena canonica.

## 3. Primo mondo: Il mio primo circo

Storyboard 0.1:

1. `campo` — la campagna cambia;
2. `tendone` — il piccolo tendone;
3. `fessura` — attraversare la soglia;
4. `pista` — apparizione al centro della pista;
5. `sera` — spettacolo;
6. `invito` — «torna domani»;
7. `vuoto` — il campo vuoto;
8. `memoria` — lo spazio rimasto dentro.

La rappresentazione della scena infantile resta **non sessualizzata**. Il prototipo visuale usa meraviglia, memoria, perdita e scoperta come assi narrativi.

## 4. Tre modi di esperienza

### OSSERVA
Terza persona / lettura cinematografica. Serve come baseline.

### VIVI
Seconda persona. Il visitatore viene collocato nello spazio e riceve indicazioni sensoriali e spaziali. È il ponte concettuale verso VR.

### RICORDA
La scena viene interpretata dalla distanza temporale: mostra ciò che il ricordo conserva e collega il momento al Cubo/R³∞.

I tre modi condividono la stessa `scene_id`; non sono tre versioni della storia.

## 5. Regole di continuità 2D → 3D

Quando arriverà il world graph 3D:

- `scene_id` non cambia;
- gli asset 2D diventano riferimenti/texture/storyboard, non vengono cancellati;
- ogni oggetto persistente riceve un `object_id`;
- posizione e stato degli oggetti saranno separati dall'asset visivo;
- una modifica non sovrascrive la provenienza precedente;
- una scena può avere più prospettive senza duplicare la scena canonica.

Esempio futuro:

```text
scene:pista
 ├─ object:tendone-interno
 ├─ object:pista
 ├─ actor:acrobata
 ├─ observer:utente
 ├─ audio:cicale-lontane
 └─ light:sole-filtrato
```

## 6. Gate di avanzamento

### Gate A — 2D storyboard
- navigazione scene funzionante;
- mobile/iPhone usabile;
- Osserva/Vivi/Ricorda coerenti;
- source/provenance visibile;
- nessuna modifica al Cubo canonico.

### Gate B — Asset sample
Generare **una sola scena campione** con OpenMontage, non l'intero film. Confrontare il risultato con la baseline 2D e approvare/rifiutare.

### Gate C — Sequenza 2D audiovisiva
Dopo approvazione del sample: immagini/video, ambiente, musica, voce e composizione.

### Gate D — World graph 3D
Convertire una scena approvata (`pista`) in ambiente 3D persistente.

### Gate E — WebXR / VR
Ingresso nell'ambiente con headset. Interazione prima osservativa, poi agentica.

## 7. File del prototipo

```text
public/cubo-vivo-2d.html
public/cubo-vivo-2d.css
public/cubo-vivo-2d-data.js
public/cubo-vivo-2d.js
docs/CUBO_VIVO_2D_SPEC.md
```

## 8. Criterio di successo della fase 0.1

Il visitatore deve capire, senza spiegazioni tecniche, che non sta leggendo una pagina sul racconto: **sta attraversando una sequenza di luoghi e momenti appartenenti allo stesso ricordo**.

La tecnologia 2D è temporanea. Il `scene graph` è il patrimonio che deve sopravvivere alle future interfacce.
