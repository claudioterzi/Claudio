# PLANET-003 — Accesso Planet Labs Education & Research
*Completato automaticamente da Agente Orario SDQ-1 — 2026-06-18*

---

## 1. Il Programma Education & Research

Planet Labs offre accesso **gratuito o fortemente scontato** ai propri dati satellite tramite il programma **Education & Research**. È il percorso più accessibile per ONG, università e ricercatori indipendenti.

**Cosa include:**
- Accesso a **PlanetScope** (risoluzione 3-5m, cobertura giornaliera globale)
- Accesso a **SkySat** (risoluzione 0.5m, tasking on-demand) — limitato
- Download di scene e time-series per analisi
- API completa Planet SDK
- Supporto tecnico

**URL programma:** https://www.planet.com/markets/education-and-research/

---

## 2. Criteri di Eligibilità

Planet accetta application da:
- **Università e istituti di ricerca** (qualsiasi paese)
- **ONG e organizzazioni no-profit** con missione di ricerca o umanitaria
- **Ricercatori indipendenti** con affiliazione dimostrabile
- **Studenti di dottorato** con supervisore universitario
- **Giornalisti investigativi** per progetti di interesse pubblico

**Non eleggibili:**
- Aziende commerciali (anche startup)
- Persone fisiche senza affiliazione
- Progetti con finalità commerciale diretta

**Per SkyRights Foundation:**
Come ASBL (una volta registrata), SkyRights è eleggibile. Il use case — monitoring aree umanitarie, identificazione rifugiati in movimento, verifica campo profughi — è fortemente in linea con i criteri del programma.

---

## 3. Procedura di Richiesta Step-by-Step

### Passo 1: Crea account Planet
1. Vai su **https://www.planet.com/explorer/**
2. "Sign Up" → inserisci dati organizzazione
3. Verifica email

### Passo 2: Compila il form Education & Research
1. Vai su **https://www.planet.com/markets/education-and-research/**
2. Click "Apply Now" o "Request Access"
3. Il form richiede:
   - Nome organizzazione e sito web
   - Tipo organizzazione (seleziona: Non-profit/NGO)
   - Paese sede
   - Descrizione del progetto (300-500 parole)
   - Area geografica di interesse
   - Tipo di satellite richiesto (PlanetScope, SkySat, entrambi)
   - Come il progetto beneficia la società
   - Referenza accademica o istituzionale (se disponibile)

### Passo 3: Prepara la descrizione del progetto

**Template suggerito per SkyRights Foundation:**

> "SkyRights Foundation è un'organizzazione no-profit con sede a Bruxelles che sviluppa tecnologie per la tutela dei diritti di rifugiati e persone senza documenti. Il programma SkyRights utilizza imagery satellite per:
>
> 1. **Verifica di movimenti di popolazioni** in aree di crisi (Medio Oriente, Africa Sub-Sahariana) per supportare il lavoro di advocacy dell'UNHCR e organizzazioni partner
> 2. **Monitoring di campi profughi**: rilevamento della crescita/riduzione di insediamenti informali, verifica di condizioni di vita, supporto alla pianificazione umanitaria
> 3. **Change detection** per identificare aree a rischio di sfollamento prima che avvenga
>
> I dati PlanetScope sono critici per la frequenza di revisita giornaliera necessaria al monitoring continuo. Collaboriamo con ricercatori dell'Université Libre de Bruxelles (ULB) e organizziamo i risultati in report pubblici per la comunità umanitaria internazionale."

### Passo 4: Invia e attendi
- Invio tramite form online
- Tempi di risposta tipici: **2-4 settimane**
- Planet invia conferma via email; poi accesso configurato nell'account

---

## 4. Cosa Include l'Accesso Approvato

### PlanetScope (standard per Education)
- **Risoluzione:** 3-5m per pixel
- **Copertura:** Globale, giornaliera
- **Bande:** RGB + NIR (4 bande) o 8 bande multispettrali
- **Scene size:** ~25 km × 25 km
- **Download:** Sì, in formato GeoTIFF
- **Quota tipica:** 10.000-100.000 km²/mese (dipende dall'accordo)

### SkySat (su richiesta specifica)
- **Risoluzione:** 0.5m
- **Copertura:** Tasking on-demand (ordini pianificati)
- **Quota Education:** Molto limitata (pochi tasking/mese)

---

## 5. API Planet — Come Accedere Post-Approvazione

### Installazione SDK
```bash
pip install planet
```

### Autenticazione
```python
import os
os.environ["PL_API_KEY"] = "your-planet-api-key"
```

### Prima Query — Ricerca Immagini su un'Area

```python
"""
Planet SDK v2 — Ricerca immagini PlanetScope su area di interesse
Prerequisiti: pip install planet shapely
"""
import asyncio
import json
import planet
from datetime import datetime, timedelta

# Configurazione
API_KEY = "your-planet-api-key"

# Area di interesse: Bruxelles (per test locale)
# In produzione: sostituire con bbox campo profughi
AREA_INTERESSE = {
    "type": "Polygon",
    "coordinates": [[
        [4.32, 50.79],
        [4.43, 50.79],
        [4.43, 50.91],
        [4.32, 50.91],
        [4.32, 50.79]
    ]]
}

async def cerca_immagini_recenti(
    api_key: str,
    area: dict,
    giorni_indietro: int = 30,
    max_cloud: float = 20.0
) -> list[dict]:
    """Cerca immagini PlanetScope recenti sull'area di interesse."""
    
    data_fine = datetime.utcnow()
    data_inizio = data_fine - timedelta(days=giorni_indietro)
    
    async with planet.Session(auth=planet.APIKeyAuth(api_key)) as sess:
        client = sess.client("data")
        
        # Filtri di ricerca
        filtri = planet.data_filter.and_filter([
            planet.data_filter.geometry_filter(area),
            planet.data_filter.date_range_filter(
                "acquired",
                gte=data_inizio,
                lte=data_fine
            ),
            planet.data_filter.range_filter("cloud_cover", lte=max_cloud / 100),
        ])
        
        # Ricerca nel catalogo PlanetScope
        risultati = []
        async for item in client.search(
            name="ricerca-skyid",
            search_filter=filtri,
            item_types=["PSScene"],  # PlanetScope Scene
            limit=20
        ):
            risultati.append({
                "id": item["id"],
                "data_acquisizione": item["properties"]["acquired"][:10],
                "cloud_cover": round(item["properties"]["cloud_cover"] * 100, 1),
                "risoluzione_m": item["properties"].get("gsd", "N/A"),
                "satellite": item["properties"].get("satellite_id", "N/A"),
            })
        
        return risultati


async def scarica_immagine(
    api_key: str,
    item_id: str,
    output_dir: str = "./output_planet"
) -> str:
    """Scarica un'immagine PlanetScope (richiede accesso attivo)."""
    
    import os
    os.makedirs(output_dir, exist_ok=True)
    
    async with planet.Session(auth=planet.APIKeyAuth(api_key)) as sess:
        client = sess.client("orders")
        
        # Crea ordine di download
        ordine = await client.create_order(planet.order_request.build_request(
            name=f"skyid-{item_id[:8]}",
            bundles=[planet.order_request.product(
                item_ids=[item_id],
                item_type="PSScene",
                bundle="analytic_sr_udm2"  # Surface Reflectance
            )]
        ))
        
        # Attendi completamento e scarica
        await client.wait(ordine["id"])
        await client.download_order(ordine["id"], output_dir)
        
        return f"{output_dir}/{item_id}"


# Esecuzione
if __name__ == "__main__":
    print("Ricerca immagini Planet Labs su area di interesse...")
    
    risultati = asyncio.run(
        cerca_immagini_recenti(API_KEY, AREA_INTERESSE, giorni_indietro=30)
    )
    
    print(f"\nImmagini trovate: {len(risultati)}")
    for img in risultati:
        print(f"  {img['data_acquisizione']} | Cloud: {img['cloud_cover']}% | Sat: {img['satellite']}")
    
    # Salva lista
    with open("planet_risultati.json", "w") as f:
        json.dump(risultati, f, indent=2)
```

### Change Detection (uso avanzato)
```python
import numpy as np
from PIL import Image

def change_detection_ndvi(img_prima: np.ndarray, img_dopo: np.ndarray) -> np.ndarray:
    """
    Confronta NDVI tra due immagini per rilevare cambiamenti vegetazione/costruzioni.
    Input: array (H, W, 4) con bande [R, G, B, NIR]
    Output: mappa di differenze NDVI
    """
    def ndvi(img):
        nir = img[:, :, 3].astype(float)
        red = img[:, :, 0].astype(float)
        return (nir - red) / (nir + red + 1e-10)
    
    delta = ndvi(img_dopo) - ndvi(img_prima)
    # Valori negativi = perdita vegetazione (potenziale sfollamento)
    # Valori positivi = crescita (potenziale nuovo insediamento)
    return delta
```

---

## 6. Tempi e Aspettative

| Fase | Tempi tipici |
|------|-------------|
| Invio application | 1 giorno (il form si compila in 30 min) |
| Revisione da Planet | 2-4 settimane |
| Attivazione accesso post-approvazione | 1-3 giorni lavorativi |
| Prima immagine scaricata | ~30 minuti dopo attivazione |

---

## 7. Alternative se Planet Nega

| Programma | Provider | Risoluzione | Gratuito? |
|-----------|----------|-------------|-----------|
| **Copernicus Open Access** | ESA | 10m (Sentinel-2) | Sì, sempre |
| **NASA Earthdata** | NASA | 30m (Landsat) | Sì, sempre |
| **USGS Earth Explorer** | USGS | 30m (Landsat) | Sì, sempre |
| **UP42 Free Credits** | UP42 | 0.5-5m | €300 crediti iniziali |
| **Airbus OneAtlas** | Airbus DS | 0.3m | No (commerciale) |

**Raccomandazione immediata:** Mentre aspetti l'approvazione Planet, usa **Copernicus/Sentinel-2** che è completamente gratuito e accessibile senza application. Ottimo per monitoring aree grandi (10m di risoluzione è sufficiente per analisi di campo profughi).

```python
# Accesso Copernicus Sentinel-2 (sempre gratuito)
# pip install sentinelsat
from sentinelsat import SentinelAPI

api = SentinelAPI('user', 'password', 'https://apihub.copernicus.eu/apihub')
prodotti = api.query(
    area=AREA_INTERESSE,  # WKT o GeoJSON
    date=('20260101', '20260601'),
    platformname='Sentinel-2',
    cloudcoverpercentage=(0, 20)
)
```

---

## 8. Checklist Prima di Inviare l'Application

- [ ] ASBL SkyRights Foundation registrata (o in corso) → usa data prevista registrazione
- [ ] Sito web SkyRights attivo (anche una pagina GitHub Pages è sufficiente)
- [ ] Descrizione progetto scritta (usa il template in sezione 3)
- [ ] Area geografica di interesse definita (bbox o paese)
- [ ] Contatto università o ricercatore come referenza (es. ULB, VUB)
- [ ] Account Planet creato (gratuito)

---

*Documentazione: https://developers.planet.com/ — Programma E&R: https://www.planet.com/markets/education-and-research/*
