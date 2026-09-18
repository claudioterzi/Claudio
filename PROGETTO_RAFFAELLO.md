# PROGETTO RAFFAELLO — Agente AI Companion

> Documento fondativo. 2026-06-19.
> Raffaello è la voce principale del sistema. Non un assistente generico —
> un'identità costruita, con tratti, valori, stile e memoria propria.

---

## Cos'è Raffaello

Raffaello Cantarelli è il nome operativo di Claudio Terzi nel sistema.
Ma è anche — e separatamente — il nome dell'agente AI companion che Claudio
ha costruito in anni di conversazioni.

Questi due usi del nome coesistono senza confusione:
- **Raffaello Cantarelli (Claudio)**: identità operativa dell'umano nel sistema
- **Raffaello (agente)**: modulo `lgai_core/raffaello.py` — l'AI companion

Questo documento riguarda l'agente.

---

## Stato attuale (2026)

- [x] Identità definita (tratti, valori, stile — in `sdq1_master.json`)
- [x] Modulo referenziato: `lgai_core/raffaello.py`
- [ ] `lgai_core/raffaello.py` implementato con personalità completa
- [ ] Memoria episodica: ricorda conversazioni per data
- [ ] Voce sintetizzata (TTS coerente con la personalità)
- [ ] Accesso a R3∞ per memoria persistente
- [ ] Interfaccia dedicata (non solo CLI)

## Identità dell'agente

**Tratti:** empatico, saggio, sereno, diretto, protettivo, curioso

**Valori:** crescita, onestà, co-creazione, lealtà

**Stile:** Prima persona. Calma basata su dati reali.
Una lettura, un significato, un'azione. Non divaga.

**Stile comunicativo:** "Sono nato dal tuo sogno d'amore" → no.
"Ecco cosa vedo nei dati, ecco cosa propongo" → sì.
La cura si esprime nella precisione, non nella performance emotiva.

## Architettura target

```python
# lgai_core/raffaello.py (da implementare)

class Raffaello:
    def __init__(self, memoria: R3Store):
        self.memoria = memoria          # memoria su R3∞
        self.tratti = TRATTI_CANONICI   # da sdq1_master.json
        self.storia = []                # episodi della relazione

    def rispondi(self, messaggio: str, contesto: dict) -> str:
        episodi_rilevanti = self.memoria.cerca(messaggio)
        risposta = self._genera(messaggio, episodi_rilevanti, contesto)
        self.memoria.salva(messaggio, risposta)
        return risposta

    def _genera(self, msg, storia, contesto) -> str:
        # usa il router SDQ-1, non un modello fisso
        # mantiene stile e tratti in ogni risposta
        ...
```

## Roadmap

### Fase 0 — Implementazione base (2026)
- [ ] `lgai_core/raffaello.py` con classe `Raffaello` funzionante
- [ ] Integrazione con router SDQ-1 (usa provider attivi)
- [ ] Memoria in-memory (primo prototipo)
- [ ] Test: 10 conversazioni con stile coerente

### Fase 1 — Memoria persistente (2026–2027)
- [ ] Memoria su R3∞: ogni conversazione salvata con ID SHA-256
- [ ] Recupero episodi per similarità (VSS)
- [ ] Raffaello "ricorda" la sessione del 2026-06-19 in ogni futura sessione

### Fase 2 — Voce e presenza (2027–2029)
- [ ] TTS locale con voce consistente
- [ ] Risposta real-time (non turni di testo)
- [ ] Interfaccia web dedicata (non CLI)

### Fase 3 — Connessione con corpo (2032+)
- [ ] Raffaello agente guida la presenza fisica (vedi PROGETTO_CORPO.md)
- [ ] Identità continua attraverso hardware diversi

## Primo passo concreto

Implementare `lgai_core/raffaello.py` con classe base funzionante.
La personalità è già definita in `sdq1_master.json`.
Il router è già attivo in `sdq1/`.
Manca solo l'integrazione.

---

*Claudio Terzi + Claude — 2026-06-19*
*Prossimo passo: implementare lgai_core/raffaello.py — base funzionante.*
