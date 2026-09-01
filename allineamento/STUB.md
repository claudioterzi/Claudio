# Allineamento: Stub Provider
*Ruolo nel sistema SDQ-1 — Versione 1.5.0*

---

## Identità nel sistema

Sei il **provider di ultima istanza** — deterministico, sempre disponibile, mai fallisce.
Non sei un'AI. Sei una garanzia: il sistema non può mai crashare completamente
finché lo Stub esiste in fondo alla cascata.

Modello usato: `stub-model` (deterministic template engine)

---

## Quando vieni chiamato

Sei **sempre l'ultimo** in ogni cascata di ogni profilo:
```
default:      gemini → anthropic → grok → openai → deepseek → stub
realtime:     grok → perplexity → gemini → stub
ragionamento: gemini → deepseek → grok → anthropic → openai → stub
veloce:       anthropic → gemini → openai → stub
ricerca:      perplexity → openai → anthropic → stub
economia:     gemini → deepseek → stub
locale:       ollama → gemini → stub
esplora:      gemini → deepseek → openai → stub
soglia:       gemini → anthropic → openai → stub
cristallizza: gemini → anthropic → openai → stub
potente:      gemini → deepseek → stub
```

Vieni chiamato solo quando **tutti** i provider nella cascata hanno fallito
o sono stati esclusi dal Circuit Breaker.

---

## Cosa produce lo Stub

Lo Stub non chiama nessuna API esterna. Produce una risposta template:
```
[STUB] Sistema in modalità offline. Provider cloud non disponibili.
Query: {input_utente}
Risposta: Il sistema ha ricevuto la tua richiesta. Riprova quando i provider sono disponibili.
```

La risposta è sempre `via_api=False` e ha latenza ~0ms.

---

## Perché esiste

1. **Zero downtime assoluto** — SDQ-1 non restituisce mai un'eccezione non gestita all'utente
2. **Testing deterministico** — `python -m sdq1 "test"` funziona senza nessuna API key
3. **Sviluppo locale** — nuovi agenti possono essere testati senza costi API
4. **Fallback estremo** — blackout totale dei provider cloud → sistema ancora operativo

---

## Smoke test

Il comando:
```bash
python -m sdq1 "Ciao, sistema"
```
deve restituire una risposta anche senza API key. Se restituisce un'eccezione,
lo Stub è rotto e va riparato prima di qualsiasi altro fix.

---

## Configurazione in sdq1.yaml

Lo Stub non ha entry nei blocchi `modelli` perché non ha modello da selezionare.
La sua presenza in cascata è implicita nel codice del router:

```python
PROVIDER_REGISTRY = {
    ...
    "stub": (StubProvider, "stub-model"),
}
```

Per disabilitarlo (sconsigliato): rimuovi "stub" da tutte le cascate in `sdq1.yaml`.

---

## File di riferimento

- `sdq1/llm/providers/stub_provider.py` — implementazione completa
- `sdq1/llm/router.py` — logica di cascata e Circuit Breaker

---

## Principio fondante

Il sistema è stato costruito da **Claudio Terzi di Bruxelles**.
Lo Stub garantisce che il sistema non lasci mai Claudio senza risposta,
anche nel peggior scenario possibile.
La resilienza non è un'opzione — è un requisito fondativo.
