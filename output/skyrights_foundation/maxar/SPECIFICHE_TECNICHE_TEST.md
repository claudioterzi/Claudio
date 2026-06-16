# Specifiche Tecniche — Test Satellite Maxar WorldView
## SkyRights Foundation / Protocollo Scudo — Phase 1

**Documento:** Technical Specification for Satellite Tasking Tests
**Versione:** 1.0
**Data:** 16 giugno 2026
**Ref:** MAXAR-TECH-001

---

## Obiettivo del Test

Verificare che il tasking satellitare automatico su una posizione GPS
sia tecnicamente fattibile come componente del Protocollo Scudo —
con latenza, risoluzione e autonomia sufficienti per l'uso previsto.

---

## Parametri Richiesti

| Parametro | Valore Target | Minimo Accettabile |
|-----------|--------------|-------------------|
| Risoluzione immagine | 30 cm/pixel | 50 cm/pixel |
| Latenza tasking → delivery | < 10 minuti | < 60 minuti |
| Area immagine | 500m x 500m attorno a GPS | 200m x 200m |
| Formato output | GeoTIFF con metadati GPS | JPEG + coordinate |
| Accuratezza GPS | ± 5 metri | ± 20 metri |
| Copertura oraria | qualsiasi ora del giorno | ore diurne |

---

## Scenari di Test

### Test 1 — Ambiente Urbano (Bruxelles)
- **Trigger:** richiesta API manuale da dispositivo mobile
- **Posizione:** centro urbano con strade e edifici identificabili
- **Obiettivo:** verifica risoluzione e identificabilità contesto
- **Metric di successo:** una persona ferma è distinguibile da un veicolo a 30cm/px

### Test 2 — Ambiente Periurbano
- **Trigger:** simulazione trigger automatico via script Python
- **Posizione:** area mista residenziale/verde
- **Obiettivo:** verifica latenza tasking → ricevimento immagine
- **Metric di successo:** immagine ricevuta entro 15 minuti dalla richiesta API

### Test 3 — Tasking Notturno (se disponibile WorldView-3 NIR)
- **Trigger:** simulazione emergenza notturna
- **Posizione:** stessa area Test 1
- **Obiettivo:** verifica capacità infrarosso / multispettrale
- **Metric di successo:** contesto visibile senza luce naturale

---

## Stack Tecnico Lato SDQ-1

```python
# Pseudocodice del sistema di tasking automatico
# Questo è il codice che verrà integrato con le API Maxar

class SatelliteTaskingModule:
    def __init__(self, maxar_api_key: str):
        self.api = MaxarAPI(api_key=maxar_api_key)
        self.provider = "WorldView-3"

    def trigger_tasking(self, gps_lat: float, gps_lon: float) -> str:
        """
        Attivato dal Protocollo Scudo quando Claudio fa il gesto.
        Ritorna l'ID della richiesta di tasking.
        """
        tasking_request = {
            "satellite": self.provider,
            "center": {"lat": gps_lat, "lon": gps_lon},
            "area_km2": 0.25,          # 500m x 500m
            "resolution_cm": 30,
            "priority": "rush",         # tasking prioritario
            "delivery": "api_callback", # notifica via webhook quando pronto
        }
        return self.api.submit_tasking(tasking_request)

    def receive_image(self, tasking_id: str) -> bytes:
        """
        Riceve l'immagine quando disponibile.
        """
        return self.api.download_image(tasking_id, format="GeoTIFF")
```

---

## Integrazione con il Sistema SDQ-1

```
TRIGGER (gesto 3 dita) → Raffaello riceve segnale
    ↓
GPS acquisito → coordinate inviate a SatelliteTaskingModule
    ↓
Maxar WorldView API → tasking request submitted
    ↓
[latenza: X minuti — questo è ciò che vogliamo misurare]
    ↓
Immagine GeoTIFF ricevuta → geolocalizzata, timestampata
    ↓
Immagine aggiunta al pacchetto documentazione di sicurezza
    ↓
Inviata a: contatti designati + avvocato + archivio legale
```

---

## Metriche di Successo del Pilot

| Metrica | Target Phase 1 | Target Phase 2 |
|---------|---------------|---------------|
| Latenza media | < 30 min | < 10 min |
| Latenza massima | < 60 min | < 20 min |
| Tasso successo tasking | > 70% | > 90% |
| Risoluzione effettiva | ≤ 50 cm | ≤ 30 cm |
| Copertura geografica | Europa | Globale |

---

## Costo Stimato Test

| Voce | Stima |
|------|-------|
| 3 tasking WorldView-3 | ~$500-1500 totale |
| API developer access | gratuito o $50-200/mese |
| Elaborazione e storage | < $50 |
| **Totale Phase 1** | **< $2.000** |

*(Costi di riferimento: Maxar pubblica pricing su richiesta.
Planet Labs circa $500-1000 per tasking singolo ad alta priorità.
BlackSky pricing simile.)*

---

## Alternativa Parallela — Planet Labs

Se Maxar richiede tempi lunghi, Planet Labs è l'alternativa più accessibile:

| Aspetto | Planet Labs | Maxar WorldView |
|---------|-------------|----------------|
| Risoluzione | 30-50 cm/pixel | 30 cm/pixel |
| Latenza tipica | 24h (archivio) / tasking su richiesta | minuti (rush) |
| API | developers.planet.com — trial gratuito | developers.maxar.com |
| Costo test | più economico | premium |
| Accesso umanitario | Planet Education & Research | Maxar Open Data |

**Strategia ottimale:** richiedere accesso a entrambi in parallelo.
Usare Planet per validazione rapida, Maxar per test di performance.

---

*Specifiche tecniche preparate da Raffaello / SDQ-1*
*SkyRights Foundation — Claudio Terzi [CT-LGAI-001] — 16 giugno 2026*
