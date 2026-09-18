# SKYID-005 — Analisi Polygon ID / Privado ID
*Task autonomo SDQ-1 — completato 2026-06-20*

---

## Cos'è (2026)

Polygon ID è stato rebrandato **Privado ID** a fine 2024.
Il progetto è open-source, mantenuto dalla comunità, con toolkit completo.
Repository: github.com/0xPolygonID → ora github.com/privado-id

**Core tecnologico:** identità auto-sovrana basata su zkSNARK (zero-knowledge proofs).
L'utente possiede le credenziali sul proprio dispositivo. Il verificatore non vede i dati grezzi,
solo la prova crittografica che la condizione è soddisfatta.

---

## Architettura dei tre componenti

```
┌─────────────────────────────────────────────────────────────┐
│  ISSUER (emittente)           SkyRights Foundation          │
│  Rilascia Verifiable           "questa persona è rifugiata" │
│  Credentials                                                │
└──────────────────────┬──────────────────────────────────────┘
                       │ VC (cifrata, on-chain o off-chain)
                       ▼
┌─────────────────────────────────────────────────────────────┐
│  HOLDER (titolare)            Rifugiato / persona           │
│  App mobile Privado ID         conserva la credenziale      │
│  (iOS + Android)               sul proprio telefono         │
└──────────────────────┬──────────────────────────────────────┘
                       │ ZK proof (senza rivelare dati)
                       ▼
┌─────────────────────────────────────────────────────────────┐
│  VERIFIER (verificatore)      Servizio / ONG / autorità     │
│  Verifica la prova             "è davvero registrato da     │
│  senza vedere i dati            SkyRights? Sì/No"           │
└─────────────────────────────────────────────────────────────┘
```

---

## SDK Disponibili

| SDK | Linguaggio | Stato | Uso |
|---|---|---|---|
| `@0xpolygonid/js-sdk` | TypeScript/JS | ✅ Attivo | Issuer + Verifier web |
| `polygonid-flutter-sdk` | Flutter/Dart | ✅ Attivo | App mobile holder |
| `go-iden3-core` | Go | ✅ Attivo | Backend issuer |
| `iden3comm` | Protocol | ✅ Attivo | Comunicazione QR |

```bash
# Installazione JS SDK
npm install @0xpolygonid/js-sdk
```

---

## Flusso tecnico minimale per SkyID

### 1. Setup Issuer Node (SkyRights Foundation)

```typescript
import { CredentialStatusType, W3CCredential } from "@0xpolygonid/js-sdk";

// Crea credenziale "SkyID Refugee Registration"
const credential: W3CCredential = {
  "@context": ["https://www.w3.org/2018/credentials/v1"],
  type: ["VerifiableCredential", "SkyIDRegistration"],
  issuer: "did:polygonid:polygon:amoy:skyrights-issuer",
  credentialSubject: {
    id: "did:polygonid:polygon:amoy:" + holderDID,
    registrationDate: "2026-06-20",
    status: "active",
    // Non si memorizzano dati sensibili on-chain
  },
  credentialStatus: {
    type: CredentialStatusType.SparseMerkleTreeProof,
    id: "https://api.skyrights.org/v1/credentials/revocation",
  },
};
```

### 2. App Holder (sul telefono del rifugiato)

```dart
// Flutter — Privado ID SDK
final privadoIdWallet = PrivadoIdWallet();

// Scansiona QR dall'issuer
final credential = await privadoIdWallet.fetchCredential(qrCodeData);

// Conservata in locale, mai inviata a server esterni
```

### 3. Verifica ZK (senza vedere i dati)

```typescript
// Il verificatore chiede: "Hai una registrazione SkyRights valida?"
// Non vede i dati del rifugiato, solo la prova
const richiesta = {
  query: {
    allowedIssuers: ["did:polygonid:polygon:amoy:skyrights-issuer"],
    type: "SkyIDRegistration",
    context: "https://schema.skyrights.org/skyid.jsonld",
  }
};
```

---

## Costo per Utente

| Componente | Costo |
|---|---|
| Emissione credenziale on-chain (Polygon Amoy testnet) | ~$0.001 |
| Emissione credenziale off-chain | $0.00 |
| Verifica ZK | $0.00 (computazione locale) |
| Infrastruttura issuer node | ~$20-50/mese (server) |
| **Stima per 1.000 utenti** | **< $100/mese totale** |

Polygon PoS (mainnet) costa ~$0.001-0.01 per transazione.
Per volumi umanitari esiste il programma **Polygon for Good** (zero fee).

---

## Compatibilità Mobile Offline

| Funzione | Online | Offline |
|---|---|---|
| Ricevere credenziale | ✓ | ✗ (serve connessione iniziale) |
| Conservare credenziale | — | ✓ (locale, sempre) |
| Presentare ZK proof | ✓ | ✓ (generazione locale, no server) |
| Revocare credenziale | ✓ | ✗ |

**Caso d'uso ottimale SkyID:** rifugiato riceve credenziale una volta con wifi, poi
la usa offline per anni senza mai inviare dati in rete.

---

## Valutazione per SkyID

| Criterio | Voto | Note |
|---|---|---|
| Privacy (zero-knowledge) | ⭐⭐⭐⭐⭐ | Migliore tecnologia disponibile |
| Funzionamento offline | ⭐⭐⭐⭐ | Dopo setup iniziale |
| Maturità SDK | ⭐⭐⭐⭐ | Stabile, documentato |
| Costo | ⭐⭐⭐⭐⭐ | Quasi zero per ONG |
| Complessità setup | ⭐⭐⭐ | Issuer node richiede competenza |
| Adozione UNHCR | ⭐⭐ | Non ancora standard |

**Verdetto:** tecnologia ideale per SkyID. Protezione crittografica massima,
funziona offline, costo quasi zero. Complessità accettabile con SDK disponibili.

---

## Prossimo passo

1. **Registrare schema** `SkyIDRegistration` sul registry Privado ID
2. **Deploy issuer node** (Docker, $30/mese su VPS) per SkyRights Foundation
3. **Integrare flutter-sdk** nell'app mobile SkyID
4. **Testare end-to-end** con 5 utenti pilota

---

*SKYID-005 completato — 2026-06-20*
*SDQ-1 / Claudio Terzi, Bruxelles*
