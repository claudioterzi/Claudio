# MAXAR-002 — Test API Maxar / Guide Developer
*Completato automaticamente da Agente Orario SDQ-1 — 2026-06-18*

---

## 1. Registrazione Account Developer

### Passo 1: Crea account
1. Vai su **https://developers.maxar.com**
2. Click "Sign Up" → inserisci nome, email aziendale, paese
3. Verifica email
4. Completa il profilo: organizzazione (SkyRights Foundation), use case (humanitarian monitoring, refugee area surveillance)

### Passo 2: Richiesta API Key
1. Dal dashboard → "Applications" → "New Application"
2. Dai un nome all'app (es. "SkyRights-SDQ1-Dev")
3. Seleziona i prodotti: **Streaming API**, **STAC API**, **Basemap API**
4. Accetta i termini di servizio
5. Ricevi la **API Key** nella sezione "Credentials"

> **Nota (giugno 2026):** Il piano gratuito developer include accesso limitato a immagini standard (non premium), STAC search, e Basemap streaming. Per imagery ad alta risoluzione e tasking, è richiesto un contratto commerciale.

---

## 2. Tipi di API Disponibili

| API | Cosa fa | Piano gratuito |
|-----|---------|---------------|
| **STAC API** | Cerca catalogo immagini satellite per area/data | Sì |
| **Streaming (WMTS/WMS)** | Tile map imagery per visualizzazione | Sì (bassa res) |
| **Vivid Basemaps** | Mosaici globali aggiornati mensile | Limitato |
| **ARD (Analysis Ready Data)** | Dati preprocessati per analisi | No (commerciale) |
| **Tasking API** | Ordina immagini future su aree specifiche | No (commerciale) |

---

## 3. Prima Chiamata Python — STAC Search su Bruxelles

```python
"""
Maxar STAC API — Prima chiamata: ricerca immagini su Bruxelles
Prerequisiti: pip install requests
"""
import requests
import json

# Configurazione
API_KEY = "your-maxar-api-key-here"
STAC_URL = "https://api.maxar.com/discovery/v1"

# Bounding box: Bruxelles
BBOX = [4.32, 50.79, 4.43, 50.91]  # [lon_min, lat_min, lon_max, lat_max]

def cerca_immagini_bruxelles(api_key: str, max_cloud: int = 30) -> dict:
    """Cerca immagini Maxar su Bruxelles con cloud cover <= max_cloud%"""
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    # STAC search request
    payload = {
        "bbox": BBOX,
        "datetime": "2025-01-01T00:00:00Z/2026-06-01T00:00:00Z",
        "limit": 10,
        "collections": ["wv02", "wv03", "ge01"],  # WorldView-2, WorldView-3, GeoEye-1
        "query": {
            "eo:cloud_cover": {"lte": max_cloud}
        }
    }
    
    response = requests.post(
        f"{STAC_URL}/search",
        headers=headers,
        json=payload
    )
    response.raise_for_status()
    return response.json()


def stampa_risultati(risultati: dict) -> None:
    """Stampa le immagini trovate in modo leggibile"""
    features = risultati.get("features", [])
    print(f"\nImmagini trovate: {len(features)}")
    print("-" * 60)
    
    for img in features:
        props = img.get("properties", {})
        print(f"ID:          {img.get('id')}")
        print(f"Satellite:   {props.get('platform', 'N/A')}")
        print(f"Data:        {props.get('datetime', 'N/A')[:10]}")
        print(f"Cloud cover: {props.get('eo:cloud_cover', 'N/A')}%")
        print(f"Risoluzione: {props.get('gsd', 'N/A')} m")
        print("-" * 60)


if __name__ == "__main__":
    print("Ricerca immagini Maxar su Bruxelles...")
    risultati = cerca_immagini_bruxelles(API_KEY, max_cloud=20)
    stampa_risultati(risultati)
    
    # Salva in JSON per analisi successiva
    with open("maxar_bruxelles.json", "w") as f:
        json.dump(risultati, f, indent=2)
    print("\nRisultati salvati in maxar_bruxelles.json")
```

### Output atteso:
```
Immagini trovate: 7
------------------------------------------------------------
ID:          5f97b8...
Satellite:   WorldView-3
Data:        2025-11-15
Cloud cover: 3%
Risoluzione: 0.3 m
------------------------------------------------------------
```

---

## 4. Accesso con Authentication (alternativa Bearer Token)

Maxar usa OAuth2. Se l'API Key non funziona direttamente, ottieni un access token:

```python
def ottieni_token(api_key: str) -> str:
    """Scambia API key per Bearer token OAuth2"""
    response = requests.post(
        "https://account.maxar.com/auth/realms/mds/protocol/openid-connect/token",
        data={
            "grant_type": "client_credentials",
            "client_id": api_key,
            "client_secret": "your-api-secret"
        }
    )
    return response.json()["access_token"]
```

---

## 5. Visualizzare un'Immagine (WMS/WMTS)

```python
def genera_url_tile(api_key: str, zoom: int = 14, x: int = 8594, y: int = 5591) -> str:
    """
    Genera URL tile WMTS per Bruxelles (zoom=14).
    Calcolo tile: https://wiki.openstreetmap.org/wiki/Slippy_map_tilenames
    """
    base_url = "https://securewatch.digitalglobe.com/earthservice/wmtsaccess"
    return (
        f"{base_url}"
        f"?connectid={api_key}"
        f"&SERVICE=WMTS&REQUEST=GetTile&VERSION=1.0.0"
        f"&LAYER=DigitalGlobe:ImageryTileService"
        f"&STYLE=&FORMAT=image/jpeg"
        f"&TileMatrixSet=EPSG:3857&TileMatrix=EPSG:3857:{zoom}"
        f"&TileRow={y}&TileCol={x}"
    )

# Integrazione con folium (mappa interattiva)
# pip install folium
import folium

def mappa_bruxelles(api_key: str) -> folium.Map:
    m = folium.Map(location=[50.85, 4.35], zoom_start=13)
    tile_url = (
        f"https://securewatch.digitalglobe.com/earthservice/wmtsaccess"
        f"?connectid={api_key}&SERVICE=WMTS&REQUEST=GetTile"
        f"&VERSION=1.0.0&LAYER=DigitalGlobe:ImageryTileService"
        f"&STYLE=&FORMAT=image/jpeg&TileMatrixSet=EPSG:3857"
        f"&TileMatrix=EPSG:3857:{{z}}&TileRow={{y}}&TileCol={{x}}"
    )
    folium.TileLayer(
        tiles=tile_url,
        attr="© Maxar Technologies",
        name="Maxar Satellite"
    ).add_to(m)
    return m
```

---

## 6. Limiti Piano Gratuito Developer

| Parametro | Piano Dev Gratuito | Piano Commerciale |
|-----------|-------------------|-------------------|
| STAC Search | 1.000 query/mese | Illimitato |
| Imagery streaming | Basemap standard (0.5-1m) | WorldView-3 (0.3m) |
| Area scaricabile | Non disponibile | Su contratto |
| Tasking | No | Sì |
| ARD | No | Sì |
| SLA | No | Sì |
| Storico immagini | 90 giorni | Dal 2008 |

---

## 7. Confronto Maxar vs Planet vs Airbus per SkyRights

| Criterio | Maxar | Planet | Airbus |
|----------|-------|--------|--------|
| Risoluzione massima | 0.3m (WV-3) | 0.5m (SkySat) | 0.3m (Pléiades) |
| Frequenza revisita | 1-3 giorni | Giornaliera (3m) | 1-3 giorni |
| Programma Education | No | Sì (Education & Research) | No |
| Costo per km² | $15-25 | $1.5-3 (PlanetScope) | $10-20 |
| API STAC | Sì | Sì | Sì |
| Offline | No | No | No |
| Migliore per SkyRights | Imagery puntuale alta res | Monitoring continuo | Imagery puntuale alta res |

**Raccomandazione per SkyRights:** Usare **Planet Labs** per monitoring continuo (Education Program, giornaliero, più economico) e **Maxar** per imagery ad alta risoluzione puntuale quando serve dettaglio (es. verifica incidente specifico).

---

## 8. Prossimi Passi

1. Registra account su developers.maxar.com
2. Esegui il codice Python qui sopra con la tua API key
3. Verifica quante immagini sono disponibili su Bruxelles nel periodo di interesse
4. Per SkyRights: esplora il programma **Maxar Unclassified** per NGO e programmi umanitari (richiedere via email)
5. Considera prioritariamente **Planet Education & Research** (vedi PLANET-003) come prima opzione gratuita

---

*Documentazione Maxar: https://developers.maxar.com/docs — Versione giugno 2026*
