# CUSTODE-001 — Sistema integrale di custodia per case Airbnb

> Studio di fattibilità + architettura. Data: 2026-07-10.
> Richiesta di Claudio: primo sistema completo di assistenza per host Airbnb
> che copra tutto — sicurezza e pezzi mancanti — con due sottosistemi:
> 1. controllo oggetti tramite **conteggio fotografico di precisione**;
> 2. **micro-etichetta RFID** applicabile a ogni prodotto (anche incollata
>    nella pagina di un libro) + **varco sulla porta d'uscita** che controlla
>    se un oggetto etichettato esce con l'ospite.

---

## Sintesi esecutiva

Entrambi i sottosistemi sono **fattibili oggi con tecnologia esistente**.
La scoperta più importante dello studio: **la micro-etichetta non va
inventata — esiste già**, ed esiste già anche il varco. Le biblioteche
usano da anni esattamente il sistema richiesto: etichette RFID sottili come
carta incollate nelle pagine dei libri + gate d'uscita che suonano se il
libro esce senza permesso. Il valore da costruire non è il chip: è
**l'integrazione dei due sottosistemi in un unico prodotto per host**,
che oggi sul mercato non esiste (i concorrenti fanno solo foto, nessuno
combina visione + RFID + varco).

---

## Sottosistema 1 — OCCHIO: inventario fotografico di precisione

### Stato dell'arte (verificato 2026)

| Tecnologia | Cosa fa | Precisione / note |
|---|---|---|
| **CountGD / CountGD++** (CVPR 2026) | Conteggio open-vocabulary: conta "qualsiasi cosa" descritta a parole o con esempi visivi, anche con esempi negativi | Stato dell'arte per il conteggio denso (posate, bicchieri, libri su scaffale) |
| **Grounding DINO 1.6** | Rilevamento open-vocabulary: trova oggetti da descrizione testuale ("telecomando", "cavatappi") | 55.4% AP zero-shot su COCO; base di CountGD |
| **SAM 2** (Meta) | Segmentazione universale: separa ogni singolo oggetto, anche parzialmente coperto | Utile per contare oggetti impilati/sovrapposti |
| **YOLO-World / Florence-2** | Alternative leggere per rilevamento open-vocabulary | Per esecuzione locale/edge |
| **VLM (Claude, GPT-4V)** | Conteggio + descrizione + confronto semantico da foto, output JSON strutturato | Meno preciso nel denso, ottimo per inventario a zone e per il confronto prima/dopo |

Concorrenti commerciali (solo foto, nessun RFID): RapidEye, ItemWise.ai,
PropCheckAI, CheckEasy. Tutti usano lo stesso schema: **foto baseline →
foto al turnover → confronto AI → segnalazione danni/mancanze**.

### Architettura proposta per la precisione "anche il più piccolo oggetto"

La precisione non viene da un modello solo, ma dalla **strategia a zone**:

1. **Baseline zonale**: la casa viene fotografata una volta per zone
   ("cassetto posate", "ripiano 2 della libreria", "mobile TV"). Ogni zona
   è piccola, inquadrata da vicino, con luce fissa. Su zone piccole il
   conteggio è quasi perfetto anche per oggetti minuti.
2. **Doppio motore**:
   - *Motore denso* (CountGD++ / Grounding DINO + SAM2): conta gli oggetti
     ripetuti (6 forchette, 12 bicchieri, 30 libri).
   - *Motore semantico* (VLM): identifica e nomina gli oggetti unici
     (telecomando, phon, quadro) e confronta baseline vs check-out
     ragionando ("il vaso c'è ma è spostato; il libro rosso manca").
3. **Confronto strutturato**: entrambe le passate producono JSON
   (`zona → oggetto → quantità`). La differenza baseline−checkout produce
   l'elenco discrepanze con foto di prova e timestamp — la base per la
   richiesta di rimborso su Airbnb (AirCover richiede evidenza fotografica).
4. **Chi scatta le foto**: l'addetto alle pulizie con lo smartphone, guidato
   dall'app zona per zona (stessa inquadratura della baseline, overlay
   fantasma della foto originale per allineamento).

### Limiti onesti

- Oggetti dentro contenitori chiusi non si contano: serve il protocollo
  "apri e fotografa" oppure il Sottosistema 2 (RFID).
- Il conteggio fotografico dice *che cosa manca*, non *chi l'ha preso né
  quando*: per questo serve il varco.

---

## Sottosistema 2 — SOGLIA: micro-tag RFID + varco d'uscita

### La micro-etichetta esiste già (non serve inventarla)

Il termine cercato è **RFID passivo UHF (RAIN RFID, EPC Gen2 / ISO 18000-63)**:
nessuna batteria, il tag si alimenta con l'onda radio del lettore.

| Tag | Dimensioni | Note |
|---|---|---|
| **Murata LMXSJZNCMF-198** | **1,25 × 1,25 mm** | Il più piccolo UHF al mondo in produzione; incorporabile/annegabile nel prodotto; lettura ~1 cm (serve lettore a contatto, non varco) |
| Hitachi UHF | 2,5 × 2,5 × 0,3 mm | Simile: micro, ma portata corta |
| Tag micro 2,6 mm | 2,6 × 2,6 × 0,8 mm | Portata 15–30 cm: ancora troppo poco per un varco |
| **Wet inlay UHF (carta)** | ~1 × 4–9 cm, **spesso come un foglio** | **Questa è la scelta giusta**: adesivo, invisibile dentro una pagina di libro, sotto un mobile, dietro un quadro; portata di lettura **1–6 metri** → funziona al varco |

**Punto tecnico decisivo**: la portata di lettura dipende dall'antenna
stampata attorno al chip, non dal chip. Un tag di 1 mm si legge a 1 cm; un
inlay di carta di 5 cm si legge a metri di distanza. Per il varco sulla
porta serve l'inlay di carta — che è comunque sottilissimo, costa
**0,05–0,25 $ l'uno**, e le biblioteche lo incollano nelle pagine dei libri
esattamente come richiesto.

Strategia a due livelli:
- **Inlay carta UHF** (5–9 cm, invisibile una volta applicato) su libri,
  quadri, elettronica, biancheria pregiata, oggetti di valore → rilevabile al varco.
- **Micro-tag Murata** (1,25 mm) solo per oggetti piccoli di grande valore
  dove l'inlay non si nasconde → verifica a contatto con lettore palmare
  durante il turnover (non al varco).

### Il varco d'uscita esiste già (tecnologia da biblioteca)

**Gate reader UHF RAIN RFID**: due pannelli-antenna ai lati della porta
(o un reader a soffitto, più discreto per una casa), con:
- lettura passiva dei tag in transito su varchi da 1 a diversi metri;
- **sensori infrarossi di direzione**: distinguono ingresso da uscita →
  l'allarme scatta solo in uscita;
- modalità online (evento → notifica push all'host in tempo reale) oppure
  offline (allarme sonoro/luminoso locale, come in biblioteca — sconsigliato
  in casa: meglio la notifica silenziosa).

Flusso: ospite esce → il varco legge gli EPC in transito → confronto col
registro tag della casa → se un EPC registrato attraversa la soglia in
uscita: **evento con timestamp, oggetto, direzione** → notifica all'host
prima ancora che l'auto dell'ospite parta.

### Limiti onesti e contromisure

- **Metallo e liquidi** schermano l'UHF: per oggetti metallici servono tag
  "on-metal" dedicati (esistono, costano di più).
- Un tag si può trovare e staccare: mitigazione = applicazione nascosta
  (dentro la rilegatura, sotto il fondo del cassetto) + il Sottosistema 1
  rileva comunque la mancanza al turnover. I due sistemi si coprono a vicenda.
- **Privacy / GDPR (obbligatorio in Italia)**: i tag tracciano *oggetti*,
  non persone, e il varco non registra immagini — molto più leggero di una
  telecamera (vietata negli interni Airbnb). Va comunque: dichiarato
  nell'annuncio e nel contratto di soggiorno, esposta informativa alla
  porta, niente log associati all'identità oltre il necessario.

---

## Architettura integrata CUSTODE

```
┌────────────── CASA ──────────────┐
│  OCCHIO (turnover)               │      ┌── CLOUD/HOST ──┐
│  app foto a zone ────────────────┼────▶ │ motore conteggio│
│                                  │      │ (CountGD + VLM) │
│  SOGLIA (tempo reale)            │      │ confronto        │
│  varco UHF porta + IR direzione ─┼────▶ │ registro tag     │
│  lettore palmare (turnover) ─────┼────▶ │ report check-out │
└──────────────────────────────────┘      │ notifiche push   │
                                          └──────────────────┘
```

Il **report di check-out** unisce le due fonti:
1. eventi varco durante il soggiorno (che cosa è uscito e quando);
2. conteggio fotografico al turnover (che cosa manca o è danneggiato);
3. incrocio: mancanza confermata da entrambi = evidenza fortissima per
   la richiesta AirCover/deposito.

### Costi indicativi (casa tipo, 2 camere)

| Voce | Costo |
|---|---|
| 200 inlay UHF carta | 10–50 $ |
| Lettore palmare UHF (turnover) | 300–600 $ |
| Gate reader UHF + antenne + IR porta | 800–2.500 $ |
| Software (questo repo) | prototipo `custode/` |

### Roadmap

- **v0 (questo commit)**: prototipo software `custode/` — modelli dati,
  conteggio via VLM (Claude vision, opzionale), confronto baseline/checkout,
  registro tag, simulatore varco, report integrato, demo senza hardware.
- **v1**: app mobile per foto guidate a zone; integrazione CountGD++ per il denso.
- **v2**: hardware reale — gate reader EPC Gen2 (i reader espongono
  eventi EPC via LLRP/MQTT: il `custode.varco` è già disegnato per riceverli).
- **v3**: prodotto multi-proprietà, canale di vendita host/property manager.

---

## Fonti

- CountGD++ (CVPR 2026): https://openaccess.thecvf.com/content/CVPR2026/papers/Amini-Naieni_CountGD_Generalized_Prompting_for_Open-World_Counting_CVPR_2026_paper.pdf
- Grounding DINO / modelli fondazionali: https://www.robolabs.ai/resources/blog/open-vocabulary-foundation-models-vision-language
- Conteggio in video (tracking): https://arxiv.org/html/2506.15368v1
- Murata micro-tag UHF: https://www.murata.com/en-us/products/rfid/rfid/overview/lineup/uhf/single e https://www.digikey.com/en/product-highlight/m/murata-electronics-north-america/ultra-small-uhf-rain-rfid-tag
- Tag più piccoli al mondo (limiti tecnici): https://www.rfidtaghy.com/smallest-uhf-rfid-tags-in-2026/
- Wet inlay per biblioteche: https://gaorfid.com/devices/rfid-tags-by-feature/wet-inlay-rfid-tags/ e https://www.rfidmd.com/rfdlpmd/rfid-library-label
- Prezzi tag 2026: https://cpcongroup.com/insights/article/rfid-chip-cost-guide/
- Gate reader UHF con IR direzionale: https://scivas.com/uhf-rfid-gate-readers/ e https://www.andea-rfid.com/gatereader/3069.html
- Sicurezza biblioteche: https://www.bibliotheca.com/solutions/security-detection/
- Concorrenti solo-foto: https://rapideyeinspections.com/ · https://www.itemwise.ai/ · https://www.propcheckai.com/ · https://www.checkeasy.co/en
