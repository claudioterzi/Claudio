# SKYID-005 — Analisi Polygon ID / Privado ID per Identità Auto-Sovrana
*Completato automaticamente da Agente Orario SDQ-1 — 2026-06-18*

---

## 1. Cos'è Privado ID (ex Polygon ID)

**Privado ID** (rinominato da Polygon ID nel 2024) è un framework open-source per identità digitale auto-sovrana basato su:
- **W3C Decentralized Identifiers (DID)** per identificatori univoci non controllati da nessuna entità
- **W3C Verifiable Credentials (VC)** per attestazioni verificabili crittograficamente
- **Zero-Knowledge Proofs (ZK)** per dimostrare attributi senza rivelare dati

**Architettura chiave:** L'identità non è su blockchain — il DID è un identificatore locale. La blockchain (Polygon PoS) è usata solo per ancorare lo stato del credenziale (revocation tree), non per i dati personali.

**GitHub:** https://github.com/0xPolygonID/  
**Docs:** https://devs.polygonid.com/

---

## 2. Architettura Tecnica

```
┌─────────────────────────────────────────────────┐
│                  HOLDER (Rifugiato)              │
│  ┌─────────────────────────────────────────┐    │
│  │  Wallet (mobile app)                    │    │
│  │  - DID privado:xxx (identità locale)    │    │
│  │  - Verifiable Credentials (VC)          │    │
│  │  - ZK proof engine (SnarkJS/WASM)       │    │
│  └─────────────────────────────────────────┘    │
└─────────────────────────────────────────────────┘
         │ presenta proof           ↑ emette VC
         ▼                         │
┌──────────────────┐    ┌─────────────────────────┐
│  VERIFIER         │    │  ISSUER                 │
│  (campo UNHCR,   │    │  (SkyRights Foundation, │
│   confine,        │    │   ONG, governo)          │
│   ospedale)       │    │                          │
│                   │    │  - Identifica persona    │
│  Riceve ZK proof  │    │  - Emette VC:            │
│  Verifica SENZA   │    │    "è rifugiato"         │
│  accedere ai dati │    │    "ha diritto a X"      │
└──────────────────┘    └─────────────────────────┘
```

### Come Funziona ZK Proof
1. L'issuer emette una credential: `{nome: "Ali Hassan", status: "rifugiato", età: 32}`
2. Il holder la riceve nel wallet
3. Per accedere al servizio, il verifier chiede: "Prova che hai >18 anni e sei registrato come rifugiato"
4. Il wallet genera una **ZK proof** che dimostra SOLO questo (senza rivelare nome o età esatta)
5. Il verifier verifica la proof in millisecondi, senza mai vedere i dati originali

---

## 3. SDK Disponibili

| SDK | Linguaggio | Stato (2026) | Link |
|-----|-----------|--------------|------|
| **JS SDK** | JavaScript/TypeScript | Attivo | github.com/0xPolygonID/js-sdk |
| **Android SDK** | Kotlin/Java | Attivo | github.com/0xPolygonID/android-sdk |
| **iOS SDK** | Swift | Attivo | github.com/0xPolygonID/ios-sdk |
| **Flutter SDK** | Dart | Community | github.com/0xPolygonID/polygonid-flutter-sdk |
| **React Native** | JS | Sperimentale | github.com/0xPolygonID/react-native-sdk |

**Migliore scelta per SkyID:**
- **Android SDK** per app mobile primaria (rifugiati hanno prevalentemente Android)
- **JS SDK** per issuer backend (Node.js server di SkyRights)

---

## 4. Capacità Offline

Questo è il punto **critico** per SkyRights. Analisi dettagliata:

| Operazione | Online richiesto? | Offline possibile? |
|------------|-------------------|-------------------|
| Generare DID | No (DID è locale) | Sì ✓ |
| Ricevere VC dall'issuer | Sì (connessione issuer) | No ✗ |
| Generare ZK proof | No (calcolo locale) | Sì ✓ |
| Verificare proof (verifier) | Sì (se verifica on-chain) | Parzialmente |
| Verificare proof (off-chain) | No | Sì ✓ |
| Revocare credenziale | Sì (issuer + chain) | No ✗ |

**Conclusione per SkyID:**
- L'**emissione** della credential richiede connessione (una tantum nel campo base)
- Successivamente il **holder può presentare prove completamente offline**
- Il **verifier** può verificare offline se usa verificazione off-chain (firma crittografica senza query blockchain)

Questo è sufficiente per SkyID: si emette l'identità quando c'è connessione nel campo base UNHCR, poi la persona usa il documento offline ai check-point.

---

## 5. Costi

**Privado ID è open-source (Apache 2.0)** — nessun costo di licenza.

Costi reali per deployment:
| Voce | Costo |
|------|-------|
| Node RPC Polygon PoS (per issuer) | ~$50-200/mese (Infura, Alchemy, o nodo proprio) |
| Gas per transazioni (revocation) | ~$0.01-0.05 per revoca |
| Server issuer | ~$20-100/mese (VPS basic) |
| Wallet app (distribuzione) | Gratis (open source, self-hosted) |
| **Costo per utente/anno** | **~$0.50-2** (principalmente infrastruttura) |

Per un'ONG con 10.000 rifugiati: costo totale infrastruttura ~$5.000-20.000/anno.

---

## 6. Esempio Codice — Issuer Side (Node.js)

```javascript
/**
 * SkyID Issuer — Emissione credential identità rifugiato
 * Prerequisiti: npm install @0xpolygonid/js-sdk
 */
import {
  BjjProvider,
  CredentialStatusType,
  CredentialStorage,
  CredentialWallet,
  EthStateStorage,
  IdentityStorage,
  IdentityWallet,
  InMemoryDataSource,
  W3CCredential,
} from "@0xpolygonid/js-sdk";

// Configurazione issuer (SkyRights Foundation)
const ISSUER_DID = "did:polygonid:polygon:main:2q...(DID di SkyRights)";
const NETWORK_URL = "https://rpc.ankr.com/polygon"; // o nodo proprio

async function emettiCredentialRifugiato(
  holderDID: string,
  datiPersona: {
    id_skyid: string;
    status: "rifugiato" | "richiedente_asilo";
    nazionalita: string;
    data_registrazione: string;
  }
): Promise<W3CCredential> {
  
  // Schema credential (JSON-LD)
  const credential = await identityWallet.issueCredential(
    ISSUER_DID,
    {
      credentialSchema: "https://skyid.org/schemas/refugee-status/v1",
      type: "SkyIDRefugeeStatus",
      credentialSubject: {
        id: holderDID,
        skyid: datiPersona.id_skyid,
        status: datiPersona.status,
        nazionalita: datiPersona.nazionalita,
        data_registrazione: datiPersona.data_registrazione,
        // NON includiamo: nome, data nascita, biometria
        // Il holder può aggiungere attributi privati localmente
      },
    },
    {
      revocationOpts: {
        type: CredentialStatusType.Iden3ReverseSparseMerkleTreeProof,
        id: `${ISSUER_SERVER}/revocation/status`,
      },
    }
  );
  
  console.log(`Credential emessa: ${credential.id}`);
  return credential;
}
```

---

## 7. Esempio Codice — Verifier Side (Checkpoint)

```javascript
/**
 * SkyID Verifier — Verificazione al checkpoint
 * Funziona OFFLINE con verificazione off-chain
 */
import { ProofService, ZKProof } from "@0xpolygonid/js-sdk";

async function verificaPassaggio(
  zkProof: ZKProof,
  offlineMode: boolean = true
): Promise<{ valida: boolean; attributi: Record<string, unknown> }> {
  
  const proofService = new ProofService();
  
  // Verifica la prova ZK (calcolo locale, nessuna blockchain)
  const valida = await proofService.verifyProof(zkProof, {
    // Request: dimostra che sei rifugiato registrato (senza rivelare altro)
    query: {
      allowedIssuers: ["did:polygonid:polygon:main:2q...(DID SkyRights)"],
      type: "SkyIDRefugeeStatus",
      context: "https://skyid.org/schemas/refugee-status/v1",
      credentialSubject: {
        status: { $in: ["rifugiato", "richiedente_asilo"] }
      }
    },
    skipRevocationCheck: offlineMode,  // True se offline
  });
  
  return {
    valida,
    attributi: valida ? zkProof.pub_signals : {}
    // Nessun dato personale, solo la prova booleana
  };
}
```

---

## 8. Confronto con Alternative

| Sistema | Offline | ZK Privacy | Costo utente | Blockchain | Adatto rifugiati |
|---------|---------|------------|--------------|-----------|-----------------|
| **Privado ID** | Parziale ✓ | Sì ✓ | ~$1/anno ✓ | Polygon (opzionale) | **Sì** |
| WorldID | No ✗ (richiede Orb) | Sì | ~$0 (hardware) | World Chain | No (Orb) |
| Proof of Humanity | No ✗ | No ✗ | ~$50 gas | Ethereum | No |
| UNHCR PRIMES | Limitato | No ✗ | 0 (istituzionale) | No | Parziale |
| EUDI Wallet | Sì ✓ | Sì ✓ | 0 | No | No (richiede UE) |

---

## 9. Fit per SkyID — Analisi

### Punti di forza
- ✓ Open source completo (Apache 2.0)
- ✓ ZK proof = privacy by design
- ✓ Funziona offline per holder e verifier
- ✓ Standard W3C (interoperabile)
- ✓ Android SDK stabile
- ✓ Costo bassissimo

### Limitazioni per SkyID
- ✗ L'emissione richiede connessione (una tantum, ma vincolante nelle zone più remote)
- ✗ Revoca credential richiede connessione blockchain
- ✗ UX tecnica complessa per persone non alfabetizzate digitalmente
- ✗ Recovery del wallet se il telefono è perso o confiscato

### Soluzioni proposte per SkyID
1. **Emissione con backup fisico**: QR code stampato + codice di recovery in lingua madre
2. **Revoca asincrona**: coda locale di revoche da propagare quando connessione disponibile
3. **UX semplificata**: wrapper SkyID con biometria locale (impronta) invece di seed phrase
4. **Social recovery**: 3 "guardiani" (altri rifugiati o operatori) possono recuperare l'identità

---

## 10. Roadmap Privado ID 2026

Da fonti pubbliche:
- **Etherum L2 support**: migrare verso Ethereum mainnet tramite zk-rollup per più liquidità
- **eIDAS 2.0 compliance**: work in progress per compatibilità EUDI Wallet europeo
- **Offline-first improvement**: RFC per emissione offline via QR code pre-generati
- **Mobile biometrics**: integrazione Face SDK locale (on-device, no server) per binding biometria-DID

La roadmap di eIDAS 2.0 compliance è particolarmente interessante per SkyRights: potrebbe rendere SkyID interoperabile con l'identità europea dei paesi di accoglienza.

---

*Fonti: developers.polygonid.com, github.com/0xPolygonID, W3C DID spec, Privado ID blog 2025-2026*
