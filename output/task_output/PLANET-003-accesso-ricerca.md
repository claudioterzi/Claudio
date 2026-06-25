# PLANET-003 — Accesso Planet Labs Education & Research
*Task autonomo SDQ-1 — completato 2026-06-20*

---

## Programma Education & Research (E&R)

Planet Labs offre accesso gratuito alla propria archivio di immagini satellite
(PlanetScope, SkySat) per ricercatori, università e ONG accreditate.

**URL ufficiale:** planet.com/markets/education-and-research/

---

## Criteri di Ammissibilità

Per essere accettati occorre rientrare in almeno una categoria:

| Categoria | Idoneità SDQ-1/SkyRights |
|---|---|
| Ricercatori accademici | ✓ se affiliazione universitaria |
| ONG / non-profit | ✓ con ASBL SkyRights Foundation registrata |
| Giornalismo investigativo | Possibile (caso per caso) |
| Studenti dottorato | Solo con advisor letter |
| Organizzazioni umanitarie | ✓ con missione documentata |

**Percorso ottimale per Claudio:** attendere registrazione ASBL SkyRights Foundation (ASBL-001),
poi fare richiesta come ONG umanitaria. Aumenta le probabilità di approvazione.

---

## Procedura di Richiesta

### Passo 1 — Registrazione
1. Vai su **planet.com/markets/education-and-research/**
2. Clicca "Apply Now" o "Request Access"
3. Crea account Planet con email istituzionale (o @skyrights.org quando disponibile)

### Passo 2 — Modulo di richiesta
Compila:
- **Organizzazione:** SkyRights Foundation (o "Claudio Terzi — Ricercatore Indipendente")
- **Tipo:** Non-profit / Humanitarian organization
- **Paese:** Belgio
- **Descrizione del progetto (campo chiave):**

```
SkyRights Foundation is developing an AI-powered digital identity system 
for undocumented refugees and stateless persons. We use satellite imagery 
to monitor displacement patterns, verify geographic claims in asylum 
procedures, and document humanitarian situations where traditional 
documentation is unavailable. The system operates under EU GDPR and 
is non-commercial, open-source, and aligned with UNHCR protocols.
```

- **Dati richiesti:** PlanetScope (3m risoluzione), frequenza giornaliera

### Passo 3 — Invio e attesa
- Invia il modulo
- Tempi tipici: **2-6 settimane** per risposta
- Planet invia email di approvazione con API key e crediti allocati

---

## Cosa si ottiene con E&R

| Risorsa | Quantità |
|---|---|
| Crediti mensili | 10.000–100.000 km² (dipende dal progetto) |
| Satelliti accessibili | PlanetScope (150+ satellite, revisit giornaliero) |
| Risoluzione | 3.0m PlanetScope, 0.5m SkySat (quota separata) |
| Archive | Da 2009 a oggi |
| API | Planet Data API v1 |

---

## Codice Python — Prima Chiamata (dopo approvazione)

```python
"""
PLANET-003 — Test Planet Data API
Cerca immagini PlanetScope su Bruxelles ultimi 30 giorni.
"""

import requests
import json
from datetime import datetime, timedelta

PLANET_API_KEY = "IL_TUO_API_KEY_QUI"

# Bruxelles bbox (GeoJSON)
BRUXELLES_AOI = {
    "type": "Polygon",
    "coordinates": [[
        [4.25, 50.78], [4.48, 50.78],
        [4.48, 50.91], [4.25, 50.91],
        [4.25, 50.78],
    ]],
}

def cerca_immagini():
    data_fine   = datetime.utcnow()
    data_inizio = data_fine - timedelta(days=30)

    filtro = {
        "type": "AndFilter",
        "config": [
            {
                "type": "GeometryFilter",
                "field_name": "geometry",
                "config": BRUXELLES_AOI,
            },
            {
                "type": "DateRangeFilter",
                "field_name": "acquired",
                "config": {
                    "gte": data_inizio.isoformat() + "Z",
                    "lte": data_fine.isoformat() + "Z",
                },
            },
            {
                "type": "RangeFilter",
                "field_name": "cloud_cover",
                "config": {"lte": 0.3},  # max 30% nuvole
            },
        ],
    }

    richiesta = {
        "item_types": ["PSScene"],   # PlanetScope
        "filter": filtro,
    }

    risposta = requests.post(
        "https://api.planet.com/data/v1/quick-search",
        auth=(PLANET_API_KEY, ""),
        json=richiesta,
        timeout=30,
    )

    if risposta.status_code == 200:
        dati = risposta.json()
        items = dati.get("features", [])
        print(f"✓ Trovate {len(items)} immagini PlanetScope")
        for item in items[:5]:
            prop = item["properties"]
            print(f"  • {item['id']} — {prop['acquired'][:10]} — nuvole: {prop['cloud_cover']:.0%}")
        return dati
    else:
        print(f"✗ {risposta.status_code}: {risposta.text[:300]}")
        return None

if __name__ == "__main__":
    cerca_immagini()
```

---

## Alternativa Immediata — Open Data

Mentre si aspetta l'approvazione Planet, usare:

| Fonte | Risoluzione | Gratuito | Note |
|---|---|---|---|
| **Sentinel-2** (ESA) | 10m | Sì | API: Copernicus Data Space |
| **Landsat 8/9** (NASA) | 30m | Sì | API: earthexplorer.usgs.gov |
| **OpenAerialMap** | Variabile | Sì | Drone/aerei, open dataset |

```python
# Sentinel-2 — nessun account richiesto
import requests
url = "https://catalogue.dataspace.copernicus.eu/odata/v1/Products"
params = {
    "$filter": "Collection/Name eq 'SENTINEL-2' and OData.CSC.Intersects(area=geography'SRID=4326;POINT(4.35 50.85)')",
    "$top": 5,
    "$orderby": "ContentDate/Start desc",
}
r = requests.get(url, params=params)
```

---

## Piano d'azione raccomandato

1. **Ora:** Fai richiesta E&R come ricercatore indipendente
2. **Appena ASBL registrata:** Fai seconda richiesta come ONG — più crediti
3. **Nel frattempo:** Usa Sentinel-2 (gratuito, 10m, no account)
4. **Quando approvato:** Integra Planet API in Sistema Minerva SDQ-1

---

*PLANET-003 completato — 2026-06-20*
*SDQ-1 / Claudio Terzi, Bruxelles*
