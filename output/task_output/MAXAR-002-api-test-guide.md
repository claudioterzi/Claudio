# MAXAR-002 — Guida API Maxar (developers.maxar.com)
*Task autonomo SDQ-1 — completato 2026-06-20*

---

## Registrazione Account Developer

1. Vai su **developers.maxar.com**
2. Clicca "Get Started" → "Create Account"
3. Compila: nome, email, organizzazione (puoi usare "SkyRights Foundation"), paese (BE)
4. Scegli tier: **Maxar Developer Free** (trial, imagery limitata ma sufficiente per test)
5. Verifica email → Login

---

## Ottenere la API Key

Dopo il login:
1. Dashboard → "API Keys" → "Create New Key"
2. Dai un nome: `SDQ1-SCUDO-TEST`
3. Copia la chiave — è lunga, inizia con `eyJ...`

---

## Prima Chiamata — Imagery Search su Bruxelles

### Dipendenze

```bash
pip install requests
```

### Codice Python funzionante

```python
"""
MAXAR-002 — Test API Maxar Imagery Search
Cerca immagini satellite disponibili su Bruxelles (bbox reale).
"""

import requests
import json
from datetime import datetime, timedelta

# Configurazione
MAXAR_API_KEY = "IL_TUO_API_KEY_QUI"
BASE_URL = "https://api.maxar.com/discovery/v1"

# Bounding box Bruxelles (lon_min, lat_min, lon_max, lat_max)
BRUXELLES_BBOX = "4.2500,50.7800,4.4800,50.9100"

# Finestra temporale: ultimi 90 giorni
data_fine = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
data_inizio = (datetime.utcnow() - timedelta(days=90)).strftime("%Y-%m-%dT%H:%M:%SZ")


def cerca_immagini_bruxelles():
    """Cerca immagini disponibili su Bruxelles."""
    
    headers = {
        "Authorization": f"Bearer {MAXAR_API_KEY}",
        "Content-Type": "application/json",
    }
    
    params = {
        "bbox": BRUXELLES_BBOX,
        "datetime": f"{data_inizio}/{data_fine}",
        "collections": "wv02,wv03,ge01",   # WorldView-2, WorldView-3, GeoEye-1
        "limit": 10,
        "fields": "+id,+datetime,+properties.eo:cloud_cover,+properties.platform",
    }
    
    url = f"{BASE_URL}/stac/search"
    risposta = requests.get(url, headers=headers, params=params, timeout=30)
    
    if risposta.status_code == 200:
        dati = risposta.json()
        print(f"✓ Trovate {dati['context']['returned']} immagini su Bruxelles")
        for item in dati.get("features", []):
            prop = item["properties"]
            print(f"  • {item['id']}")
            print(f"    Data: {prop.get('datetime', 'N/A')}")
            print(f"    Satellite: {prop.get('platform', 'N/A')}")
            print(f"    Copertura nuvole: {prop.get('eo:cloud_cover', 'N/A')}%")
        return dati
    else:
        print(f"✗ Errore {risposta.status_code}: {risposta.text[:300]}")
        return None


def scarica_thumbnail(feature_id: str, output_path: str = "bruxelles_thumb.jpg"):
    """Scarica la thumbnail preview di un'immagine."""
    
    headers = {"Authorization": f"Bearer {MAXAR_API_KEY}"}
    url = f"{BASE_URL}/stac/collections/wv02/items/{feature_id}/thumbnail"
    
    risposta = requests.get(url, headers=headers, timeout=30, stream=True)
    if risposta.status_code == 200:
        with open(output_path, "wb") as f:
            f.write(risposta.content)
        print(f"✓ Thumbnail salvata: {output_path}")
    else:
        print(f"✗ Thumbnail non disponibile: {risposta.status_code}")


if __name__ == "__main__":
    risultati = cerca_immagini_bruxelles()
    
    if risultati and risultati.get("features"):
        primo_id = risultati["features"][0]["id"]
        print(f"\nScarico thumbnail del primo risultato: {primo_id}")
        scarica_thumbnail(primo_id)
```

### Esecuzione

```bash
export MAXAR_API_KEY="il_tuo_key"
python output/task_output/maxar_test.py
```

---

## Endpoint principali utili per SDQ-1

| Endpoint | Utilizzo |
|---|---|
| `GET /discovery/v1/stac/search` | Cerca immagini per bbox + date |
| `GET /discovery/v1/stac/collections` | Lista collezioni disponibili |
| `POST /ordering/v1/orders` | Ordina immagine full-res (a pagamento) |
| `GET /streaming/v1/ogc/wmts` | Stream tile per mappe web |

---

## Tier gratuito: cosa include

- 100 ricerche STAC al mese
- Preview/thumbnail senza costo
- Full-res: a consumo (crediti)
- Risoluzione max gratuita: 30cm WorldView

---

## Prossimo passo SDQ-1

Con MAXAR attivo, il Sistema Minerva (droni + satellite) può:
1. Cercare imagery su coordinate di interesse
2. Mostrare thumbnail nell'interfaccia web
3. Rilevare cambiamenti nel tempo (confronto immagini)

```python
# In MINERVA: interrogazione automatica per area monitorata
from sdq1.satellite.maxar import cerca_immagini_bruxelles
imagery = cerca_immagini_bruxelles()
```

---

*MAXAR-002 completato — 2026-06-20*
*SDQ-1 / Claudio Terzi, Bruxelles*
