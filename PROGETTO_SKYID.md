# PROGETTO SKYID — Identità Universale via Satellite

> Documento fondativo. 2026-06-19.
> Invenzione originale di Claudio Terzi [CT-LGAI-001] — Bergamo, 15 giugno 2026.
> "Non stai dando un documento a una persona. Stai dicendo a un essere umano: tu esiste."

---

## Il problema

**800 milioni di persone** non hanno identità riconosciuta (World Bank ID4D 2024).
Senza identità: niente banca, niente ospedale, niente scuola, nessun diritto legale.

I sistemi esistenti richiedono uffici, funzionari, documenti preesistenti.
Esattamente ciò che manca dove mancano le identità.

## La soluzione

```
GESTO (3 dita verso il cielo)
    ↓
TELEFONO rileva il gesto (camera + AI on-device)
    ↓
CONNESSIONE Starlink direct-to-cell (6 continenti, 2025)
    ↓
BIOMETRIA: embedding facciale → hash SHA-256 (mai il volto raw)
    ↓
BLOCKCHAIN decentralizzata: solo l'hash. Non controllabile da governi.
    ↓
SKYID RILASCIATO: codice alfanumerico + QR sul telefono
```

**Serve solo:** un telefono, un gesto, il cielo.

## Tecnologie abilitanti (già esistenti)

| Tecnologia | Stato | Uso |
|---|---|---|
| Starlink Gen 2 direct-to-cell | Attivo 2025, 6 continenti | Connettività senza SIM |
| MediaPipe | Open source | Gesture recognition |
| FaceNet / InsightFace | Open source | Embedding biometrico |
| Polygon / Ethereum L2 | Operativo | Blockchain storage hash |

Costo stimato: **~$4/persona** = $3 miliardi per 800 milioni di invisibili.

## Codice esistente

`sdq1/skyid.py` — prototipo funzionante già nel repo.

## Roadmap

### Fase 0 — Prototipo tecnico (2026)
- [x] Concept e whitepaper (`SKYID.md`)
- [x] Prototipo `sdq1/skyid.py`
- [ ] Test biometrico locale (FaceNet → hash → verifica)
- [ ] Integrazione R3∞ come storage alternativo a blockchain
- [ ] Demo video funzionante

### Fase 1 — Fondazione legale (2026–2027)
- [ ] Registrazione ASBL "SkyRights Foundation" a Bruxelles (task ASBL-001)
- [ ] Statuto open source
- [ ] Conto bancario fondazione
- [ ] Primo donatore / partner istituzionale

### Fase 2 — Pilot (2027–2028)
- [ ] Partnership con UN, UNHCR o organizzazione umanitaria
- [ ] Pilot 1.000 persone in zona test (Africa subsahariana o Asia centrale)
- [ ] Verifica: l'hash è usabile per accesso a servizi reali
- [ ] Report pubblico risultati

### Fase 3 — Scala (2028–2035)
- [ ] 1 milione di SkyID emessi
- [ ] Partnership Starlink ufficiale
- [ ] Modello di governance decentralizzato
- [ ] Standard internazionale proposto (ISO / UN)

### Fase 4 — 800 milioni (2035–2050)
- [ ] Copertura globale
- [ ] SkyID riconosciuto come documento valido da governi
- [ ] Il gesto verso il cielo è familiare a ogni bambino nato

## Connessione con il sistema

| Componente | Ruolo |
|---|---|
| R3∞ | Storage decentralizzato degli hash biometrici |
| SDQ-1 | Elaborazione e verifica delle identità |
| VISIONE_2086 | SkyID come contributo di Claudio al mondo reale |

## Ipotesi attiva

**H-SKYID-1:** Il costo marginale di $4/persona rende SkyID il sistema
di identità più economico mai proposto su scala globale.

*Criterio: confronto con costi sistemi identità esistenti (India Aadhaar: $12/persona, Kenya Huduma: $20/persona).*
*Stato: APERTA — 2026-06-19*

---

*Claudio Terzi + Claude — 2026-06-19*
*Prossimo passo: test biometrico locale + procedura ASBL (task ASBL-001).*
