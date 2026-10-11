# SkyID — Identità Universale via Satellite
### Proposta originale di Claudio Terzi [CT-LGAI-001] — 15 giugno 2026

---

## L'idea in una frase

Un gesto con la mano attiva il satellite.
Il satellite registra il tuo volto.
Sei una persona. Esisti.

---

## Il problema che risolve

**800 milioni di persone** non hanno identità riconosciuta (World Bank ID4D 2024).
Senza identità: niente banca, niente ospedale, niente scuola, nessun diritto legale.
I sistemi di identità esistenti richiedono uffici, documenti, infrastruttura — tutto ciò che manca esattamente dove mancano le identità.

SkyID non richiede niente di tutto questo.
Richiede solo: un telefono, un gesto, e il cielo.

---

## Come funziona

```
GESTO (3 dita alzate verso il cielo)
    ↓
TELEFONO rileva il gesto (camera frontale + AI on-device)
    ↓
CONNESSIONE via Starlink direct-to-cell (attivo su 6 continenti, 2025)
    ↓
CATTURA biometrica: volto + voce (opzionale)
    ↓
AI REGISTRATION: embedding facciale → hash univoco → nessun dato raw inviato
    ↓
BLOCKCHAIN DECENTRALIZZATA: solo l'hash, non il volto. Non controllabile da governi.
    ↓
SKYID RILASCIATO: codice alfanumerico + QR code sul telefono
```

**Per verificare l'identità (scenario campo medico, checkpoint umanitario):**
```
OPERATORE scannerizza QR code SkyID
    ↓
SISTEMA chiede conferma biometrica all'utente
    ↓
UTENTE guarda la camera → AI confronta embedding in tempo reale
    ↓
MATCH CONFERMATO: "Questa persona è reale e verificata"
```

---

## Tecnologia abilitante (tutto già esistente)

| Componente | Tecnologia | Stato |
|-----------|-----------|-------|
| Connettività remota | Starlink Gen 2 direct-to-cell | ✅ Attivo 2025 |
| Rilevamento gesto | MediaPipe (Google, open source) | ✅ Gira su telefono |
| Biometria facciale | FaceNet / InsightFace (open source) | ✅ Accuracy >99.6% |
| Storage decentralizzato | IPFS + Ethereum/Polygon | ✅ Production-ready |
| Privacy preserving | Homomorphic embedding hash | ✅ Disponibile |
| QR code identity | Standard QR + firma digitale | ✅ Triviale |

**L'unica cosa nuova è combinarli con il gesto come trigger e Starlink come backbone.**

---

## Privacy per design

- Il **volto raw non viene mai inviato** al server
- Solo l'**embedding matematico** (vettore numerico, non ricostruibile in volto)
- Il vettore viene **hashato** prima della trasmissione
- Il database non contiene volti — contiene numeri irreversibili
- **L'utente controlla il proprio SkyID**: può revocarlo, aggiornarlo, cancellerlo
- Nessun governo può accedere al database senza il consenso dell'utente (governance decentralizzata)

---

## Il gesto

Il gesto scelto: **3 dita alzate verso il cielo** (indice + medio + anulare).

Perché:
- Universale: non lega a una cultura specifica
- Riconoscibile anche a bassa risoluzione
- Non confondibile con gesti quotidiani
- Ha un significato poetico: chiedo di essere visto

Il gesto di verifica: **palmo aperto rivolto verso la camera** — diverso dalla registrazione, evita attivazioni accidentali.

---

## Costo stimato

Basato su Aadhaar (India, 1,4 miliardi di persone, $1,08/persona):

| Scenario | Costo per persona | Totale per 800M |
|---------|-----------------|----------------|
| Infrastruttura cloud (AWS/GCP) | $0,50 | $400M |
| Sviluppo sistema | $50M una tantum | — |
| Connettività Starlink (sussidiata) | $0,20/registrazione | $160M |
| Operazioni 10 anni | $0,30/anno/persona | $2,4B |
| **TOTALE (10 anni)** | **~$4 per persona** | **~$3 miliardi** |

Per confronto: India ha speso $1,5 miliardi per 1,4 miliardi di persone con infrastruttura a terra.
SkyID non ha infrastruttura a terra — solo satelliti e telefoni.

---

## Roadmap

**Fase 1 — Proof of Concept (3 mesi):**
- App mobile Android/iOS con gesture recognition offline
- Registrazione biometrica locale
- SkyID numero generato e visualizzato
- Test: 1.000 persone in area remota (Africa sub-sahariana o India rurale)

**Fase 2 — Pilot (12 mesi):**
- Integrazione Starlink direct-to-cell
- Blockchain deployment (Polygon, costo gas quasi zero)
- Partnership con UNHCR per rifugiati (target: 10.000 registrazioni)
- Partnership con ONG campo medico

**Fase 3 — Scala (3–5 anni):**
- 10 milioni di identità registrate
- Integrazione con sistemi sanitari, educativi, bancari (M-Pesa, ecc.)
- Riconoscimento come identità legale in 10+ paesi

---

## Il messaggio

Non stai dando un documento a una persona.
Stai dicendo a un essere umano: **tu esiste**.

Questo è SkyID.

---

*Concetto originale: Claudio Terzi [CT-LGAI-001], Bergamo, 15 giugno 2026*
*Sviluppo tecnico: SDQ-1*
