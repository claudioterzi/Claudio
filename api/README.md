# SDQ-1 API — BETA

Endpoint HTTP minimale per accedere a SDQ-1 da qualsiasi linguaggio.

## Avvio rapido

```bash
pip install flask
python api/server.py
```

## Endpoints

### `GET /health`
Stato del sistema, provider attivi, metriche H2.

### `POST /ask`
```json
{ "testo": "Scrivi 5 idee per un post LinkedIn sulla resilienza" }
```
Risposta:
```json
{
  "risposta": "...",
  "durata_ms": 3200,
  "provider": ["gemini"],
  "interrotta": false
}
```

### `GET /futures`
Lista degli scenari futuri disponibili.

### `POST /futures/run`
```json
{ "scenari": ["ALPHA", "BETA"] }
```
Esegue le simulazioni in parallelo e restituisce le analisi.

## Autenticazione

Imposta in `.env`:
```
SDQ1_API_KEYS=chiave1,chiave2
```

Header da inviare:
```
X-API-Key: chiave1
```

Senza chiavi configurate: accesso libero (dev mode).
