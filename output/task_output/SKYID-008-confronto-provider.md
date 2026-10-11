# SKYID-008 — Confronto Provider Identità Digitale per Rifugiati
*Task autonomo SDQ-1 — completato 2026-06-20*

---

## I cinque sistemi analizzati

### 1. UNHCR PRIMES (Population Registration and Identity Management EcoSystem)

**Cos'è:** sistema interno UNHCR per registrazione rifugiati. Non è un prodotto pubblico.

| Parametro | Valore |
|---|---|
| Utenti attivi | ~20 milioni di rifugiati registrati |
| Biometrica | Impronte digitali + iride (obbligatorie) |
| Accesso rifugiato | Carta fisica UNHCR, nessuna app |
| Funzionamento offline | Parziale (scanner biometrici) |
| Dati dove | Server UNHCR + cloud AWS (criticato) |
| Open-source | No |
| Costo | Nessuno per rifugiato |

**Cosa fallisce:**
- I dati biometrici sono centralizzati: violazione della privacy, rischio condivisione con governi
- Il rifugiato non controlla i propri dati
- Nessuna portabilità: vale solo nei paesi dove UNHCR opera
- Richiede presenza fisica per ogni aggiornamento
- Molte persone non sono mai registrate (conflict zones, aree remote)

---

### 2. ID4D — Identification for Development (Banca Mondiale)

**Cos'è:** programma di finanziamento e supporto tecnico per governi che vogliono digitare registri identità nazionali.

| Parametro | Valore |
|---|---|
| Modello | Supporto ai governi (B2G), non diretto ai rifugiati |
| Standard | MOSIP (open-source), vari sistemi nazionali |
| Biometrica | Dipende dal paese |
| Self-sovereign | No |
| Copertura | 40+ paesi con programmi attivi |

**Cosa fallisce:**
- Non è un sistema per rifugiati: serve i cittadini dei paesi con governi funzionanti
- Chi fugge da quel governo perde l'accesso all'identità
- La "portabilità" non esiste: un'identità RDC non vale in Uganda
- Non copre i "casi impossibili" (paesi collassati, apolidi)

---

### 3. India Aadhaar

**Cos'è:** sistema di identità biometrica nazionale indiana (1.4 miliardi di utenti).

| Parametro | Valore |
|---|---|
| Utenti | 1.38 miliardi |
| Biometrica | 10 impronte + 2 iri + foto |
| Funzionamento offline | Sì (QR code offline) |
| Portabilità internazionale | No |
| Controllo utente | Molto limitato |
| Privacy | Controverso (centralizzato UIDAI) |

**Cosa fallisce:**
- Valido solo in India
- Escluso chi non ha indirizzo fisico (homeless, rifugiati)
- Violazioni privacy documentate (leak database 2018, 2023)
- L'utente non può cancellare il proprio profilo
- Modello da non replicare per SkyID (centralizzazione massima)

---

### 4. WorldCoin / World ID

**Cos'è:** network di identità basato su scan dell'iride (orb fisico) + proof of humanness.

| Parametro | Valore |
|---|---|
| Modello | Blockchain (World Chain) + ZK proofs |
| Biometrica | Iride obbligatoria (scan fisico) |
| Self-sovereign | Parzialmente |
| Privacy | ZK proof (iride non è memorizzata, solo hash) |
| Distribuzione orb | 40+ paesi, ma non ovunque |
| Costo | Gratuito |

**Cosa fallisce:**
- Richiede un "Orb" fisico: impossibile in campi rifugiati remoti
- Legame inscindibile con token speculativo WLD (scelta eticamente discutibile)
- Governance centralizzata in Tools for Humanity (San Francisco)
- Critica accademica: lo scan dell'iride è irreversibile se compromesso
- Kenya ha sospeso il servizio per questioni legali (2023)

---

### 5. Proof of Humanity (PoH)

**Cos'è:** registro anti-sybil decentralizzato su Ethereum. Chi è registrato prova di essere umano.

| Parametro | Valore |
|---|---|
| Modello | DAO + smart contracts Ethereum |
| Verifica | Video + vouching umano |
| Self-sovereign | Sì (wallet Ethereum) |
| Privacy | Limitata (video pubblico) |
| Costi | Gas fee Ethereum |
| Offline | No |

**Cosa fallisce:**
- Il video di registrazione è **pubblico** su IPFS: devastante per rifugiati che fuggono da persecutori
- Richiede Ethereum e gas fee: inaccessibile senza crypto
- Vouching: chi fa il vouche per un rifugiato che non conosce nessuno?
- Governance instabile (fork UBI/PoH in 2022)
- Scala zero nell'uso umanitario reale

---

## Mappa dei Gap — Dove SkyID può differenziarsi

```
Problema                  | UNHCR | Aadhaar | World | PoH | SkyID
─────────────────────────────────────────────────────────────────
Funziona senza governo    |  No   |   No    |  Sì  | Sì  |  ✓
Self-sovereign            |  No   |   No    |  Parz| Sì  |  ✓
Funziona offline          |  Parz |   Sì    |  No  | No  |  ✓
Non richiede infrastruttura fisica | No | No | Orb | No |  ✓
Privacy crittograficamente garantita | No | No | Parz | No |  ✓
Non legata a governo/token | No  |   No    |  No  | No  |  ✓
Portabile internazionalmente | No |  No    |  Parz| Sì  |  ✓
Verifica possibile senza foto pubblica | No | No | No | No |  ✓
```

**Il gap unico di SkyID:** l'unico sistema che è contemporaneamente
offline-capable, self-sovereign, privacy-first, e non dipendente da governi o token.

---

## Tecnologia raccomandata per SkyID

Sulla base di questa analisi:

1. **Privado ID (ex Polygon ID)** — per la credenziale ZK (vedi SKYID-005)
2. **DID:web o DID:key** — per l'identità decentralizzata senza blockchain
3. **Offline-first con sync** — credenziale su dispositivo, sync quando online
4. **Vouching comunitario** — rifugiati si garantiscono a vicenda (alternativa a Orb)

---

*SKYID-008 completato — 2026-06-20*
*SDQ-1 / Claudio Terzi, Bruxelles*
