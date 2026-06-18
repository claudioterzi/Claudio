# SKYID-008 — Confronto Provider Identità Digitale per Rifugiati
*Completato automaticamente da Agente Orario SDQ-1 — 2026-06-18*

---

## 1. Tabella Comparativa

| Provider | Modello | Utenti 2026 | Offline? | Data ownership | Costo utente | Problemi principali |
|---------|---------|------------|---------|---------------|-------------|---------------------|
| **UNHCR PRIMES** | Centralizzato, istituzionale | ~20M rifugiati | No | UNHCR | 0 (sussidiato) | Dipendente da UNHCR, no portabilità |
| **World Bank ID4D** | Supporto governi, centralizzato | 1.4B (India+altri) | No | Governo nazionale | 0-$2 | Richiede governo funzionante |
| **Aadhaar (India)** | Centralizzato, biometrico | 1.4 miliardi | Parziale | Governo India | 0 | Solo cittadini indiani |
| **WorldID** | ZK biometrico (Orb) | ~10M | No | World Foundation | 0 hardware/usage | Richiede Orb fisico, non EU |
| **Proof of Humanity** | Blockchain, video | ~25.000 | No | Utente (blockchain) | ~$50 gas | Non scala, lento |
| **EUDI Wallet** | PKI, SSI, EU standard | Milioni (2026) | Sì | Utente | 0 | Solo cittadini/residenti EU |
| **SkyID (proposta)** | SSI, ZK, offline-first | 0 (da lanciare) | Sì | Utente | ~$1/anno | Da costruire |

---

## 2. UNHCR PRIMES — Analisi Dettagliata

### Cos'è
**PRIMES** (Population Registration and Identity Management EcoSystem) è il sistema integrato UNHCR per la registrazione e gestione dei rifugiati. Include il database biometrico **BIMS** e l'applicazione di registration **proGres v4**.

### Come funziona
1. Il rifugiato si presenta al campo/ufficio UNHCR
2. Raccolta biometrica: impronta digitale + iris scan + foto
3. Registrazione nel database centrale UNHCR
4. Emissione carta rifugiato fisica (se il paese lo permette)
5. Accesso a servizi (assistenza, salute, trasferimenti) legato all'ID

### Copertura (2026)
- ~20 milioni di rifugiati e richiedenti asilo registrati
- Operativo in 60+ paesi
- Database centralizzato a Ginevra

### Limitazioni critiche

1. **Non portabile**: l'identità PRIMES esiste solo nell'ecosistema UNHCR. Quando il rifugiato lascia il mandato UNHCR (es. ottiene status in un paese), perde accesso.

2. **Completamente offline**: il sistema funziona SOLO con connessione ai server UNHCR. In zone remote senza connessione, il rifugiato non esiste per il sistema.

3. **Data ownership zero**: i dati appartengono a UNHCR. Il rifugiato non può portarsi i propri dati fuori, né scegliere chi può accedervi.

4. **Dipendenza statale**: PRIMES funziona solo dove UNHCR ha accordi con il governo locale. In zone di conflitto attivo o con governi ostili, il sistema collassa.

5. **Single point of failure**: attacco informatico a UNHCR o fallimento istituzionale = 20 milioni di identità a rischio.

6. **Duplicazione incentivata**: chi non è registrato non ha diritti, quindi il sistema incoraggia registrazioni multiple per sicurezza.

---

## 3. World Bank ID4D — Analisi

### Cos'è
**ID4D** (Identification for Development) è un programma della Banca Mondiale che supporta i governi nell'implementare sistemi di identità nazionale inclusivi. Non è un sistema diretto, ma un framework e finanziamento.

### Paesi target
Bangladesh, Côte d'Ivoire, DRC, Ethiopia, Jordan, Nigeria, Pakistan, Tanzania, Tunisia, Yemen — focus su paesi con grandi popolazioni di rifugiati.

### Limitazioni
- **Dipende dai governi**: se il governo non vuole includere i rifugiati nel sistema nazionale, ID4D non può forzarlo
- **Lentezza**: implementazione richiede anni (10-15 anni per avere copertura nazionale in Africa)
- **Esclusione per design**: sistemi nazionali tipicamente escludono non-cittadini (rifugiati, apolidi)
- **Banca dati centralizzata**: stesso problema di PRIMES, ma a livello statale

### Lezione per SkyID
ID4D dimostra che la strada "top-down via governi" è troppo lenta e politicamente fragile. SkyID deve essere **bottom-up**, funzionare indipendentemente dalla volontà politica del governo ospitante.

---

## 4. Aadhaar — Cosa Ha Funzionato e Cosa No

### Successi
- 1,4 miliardi di persone con identità digitale in 10 anni
- Inclusione finanziaria: 500M nuovi conti bancari linkati
- Riduzione frode nei sussidi statali ($20B/anno risparmiati)
- Offline verification possibile via one-time password (OTP)

### Fallimenti per migranti/rifugiati
- **Richiede cittadinanza o residenza legale** → i rifugiati rohingya in India non possono registrarsi
- **Database centralizzato** → ogni accesso registrato, totale sorveglianza statale
- **Biometria obbligatoria** → lavori fisici degradano le impronte, anziani esclusi
- **Single company** → UIDAI (governo indiano) controlla tutto

### Lezione per SkyID
L'approccio "scala di Aadhaar" con "privacy di Privado ID": raggiungere 1+ miliardo di persone ma con ownership dell'identità. Il modello di scaling è corretto, non il modello di governance.

---

## 5. WorldID — Analisi

### Come funziona
1. Utente va a un "Orb" (dispositivo biometrico fisico)
2. L'Orb scansiona l'iris dell'utente
3. Genera un "iris code" + ZK proof che l'utente è umano e unico
4. Emette un WorldID nel wallet dell'utente (app Worldcoin)
5. L'utente può provare "proof of personhood" senza rivelare chi è

### Stato 2026
- ~10 milioni di utenti verificati via Orb
- Presente in ~50 paesi (esclusa EU per problemi GDPR)
- WLD token distribuiti agli utenti (controverso)

### Controversie EU
- **GDPR**: raccolta iris scan = dato biometrico di categoria speciale
- **Italia, Spagna, Francia, Germania**: indagini GDPR, sospensioni
- **Data retention**: World Foundation conserva template iris per indeterminato
- **Centralizzazione**: nonostante ZK proof, il database Orb è centralizzato

### Perché non funziona per rifugiati
- **Richiede Orb fisico**: nessun Orb nei campi profughi di Kakuma, Cox's Bazar, Zaatari
- **Token economico**: il sistema è nato come crypto project, non humanitarian
- **Sovranità**: il "proof" è legato all'ecosistema WorldCoin — se l'azienda chiude, l'identità scompare
- **Not EU-compatible**: non usabile in EU, dove molti rifugiati arrivano

---

## 6. Proof of Humanity — Analisi

### Come funziona
1. Utente carica video selfie + deposita ETH come garanzia
2. Comunità verifica il video manualmente
3. Se approvato, l'utente è registrato come "umano unico" sulla blockchain Ethereum

### Stato 2026
- ~25.000 utenti attivi (pochissimi)
- Governato da Kleros DAO
- Integrato con UBI token (Proof of Humanity = reddito di base in crypto)

### Perché non scala
- **Processo manuale**: revisione umana del video è lenta e costosa
- **ETH deposit**: barriera economica per rifugiati
- **Gas costs**: ogni operazione costa ETH
- **No offline**: completamente dipendente da Ethereum mainnet
- **Attacco Sybil continuo**: persone che tentano di registrarsi più volte con video diversi

---

## 7. EUDI Wallet — Analisi

### Cos'è
Il **European Digital Identity Wallet** (eIDAS 2.0) è lo standard EU per identità digitale degli europei. Ogni Stato Membro deve offrire un wallet gratuito ai cittadini entro fine 2026.

### Punti di forza
- Open standard (ARF - Architecture Reference Framework)
- Offline capability nativa
- Privacy by design (selective disclosure)
- Gratis per cittadini
- Interoperabile tra tutti gli Stati Membri

### Limitazione fondamentale per SkyID
**L'EUDI Wallet richiede cittadinanza UE o residenza legale documentata.** Un rifugiato appena arrivato, un richiedente asilo in attesa, o un apolide non può ottenere un EUDI Wallet.

Questa è l'esclusione strutturale che SkyID risolve: essere l'identità per chi l'EUDI Wallet non può raggiungere (ancora).

### Opportunità di integrazione
Quando un rifugiato ottiene status di residenza EU, SkyID dovrebbe poter "bridge" verso EUDI Wallet, portando con sé la storia di credenziali verificate. SkyID come on-ramp verso l'identità europea formale.

---

## 8. Le 7 Lacune che SkyID Colma

### Lacuna 1: Offline-first totale
**Nessun sistema attuale** funziona completamente offline per l'emissione E la verifica. PRIMES richiede server online. EUDI ha offline verification ma non emission. SkyID: emissione assistita (campo base) + uso completamente offline.

### Lacuna 2: Zero data custodian
Tutti i sistemi attuali hanno un custode (UNHCR, governo, World Foundation, Ethereum). SkyID: l'identità appartiene fisicamente alla persona nel suo dispositivo. Nessun database centrale.

### Lacuna 3: Non richiede documento preesistente
Aadhaar, EUDI, ID4D richiedono almeno un documento di partenza. PRIMES richiede registrazione fisica. SkyID: può emettere identità da zero, con attestazione da witnesses (altri rifugiati, operatori ONG).

### Lacuna 4: Portabilità cross-mandato
Un rifugiato con PRIMES Uganda perde la storia quando va in Turchia. Con SkyID: il DID e le credential viaggiano con la persona, cross-border, cross-provider.

### Lacuna 5: Privacy selettiva
Nessun sistema attuale permette al rifugiato di scegliere quali attributi rivelare. PRIMES: l'operatore vede tutto. SkyID: "dimostro che sono rifugiato registrato" senza rivelare nome o nazionalità.

### Lacuna 6: Recovery sociale
Tutti i sistemi hardware-bound (Orb, carta fisica) sono vulnerabili a perdita o confisca. SkyID: recovery tramite "social key" — 3 witness possono attestare l'identità e recuperare l'accesso.

### Lacuna 7: Legacy della persona
Nessun sistema pensa alla continuità dell'identità dopo la morte o la dissoluzione dell'istituzione. SkyID + Avatar Eterno: l'identità della persona sopravvive e può essere passata ai figli.

---

## 9. Posizionamento Strategico SkyID

### Non competitor di UNHCR
SkyID non sostituisce PRIMES — lo completa. PRIMES gestisce la logistica istituzionale (sussidi, trasferimenti, housing). SkyID gestisce l'identità personale portabile. I due sistemi dovrebbero interoperare.

**Pitch per UNHCR:** "Usiamo SkyID per dare ai rifugiati una identità portabile che persiste fuori dal mandato UNHCR. Integriamo con PRIMES come layer di attestazione."

### Partnership strategiche possibili

| Partner | Motivo | Primo contatto |
|---------|--------|---------------|
| UNHCR Innovation Fund | Pilot SkyID in un campo | unhcr.org/innovation |
| World Bank ID4D | SkyID come complemento SSI | worldbank.org/id4d |
| ICRC (Croce Rossa) | Monitoring zone di conflitto | icrc.org/digital |
| Médecins Sans Frontières | Identità in zone senza governo | msf.org/tech |
| IRC (International Rescue Committee) | USA + internazionale | rescue.org/tech |
| Fedasil (Belgio) | Pilot locale Bruxelles | fedasil.be |

### Come presentarsi agli investitori EU

**Narrative principale:** "Stiamo costruendo l'infrastruttura di identità per 100 milioni di persone che il sistema attuale non può raggiungere — rifugiati, apolidi, vittime di conflitti. È un'opportunità di mercato da €2 miliardi che nessuno vede perché tutti guardano il mercato enterprise."

**Il white space:** L'EUDI Wallet copre 450 milioni di europei. SkyID copre i 100 milioni che non possono avere un EUDI Wallet. Siamo l'on-ramp.

---

*Fonti: UNHCR PRIMES documentation, World Bank ID4D Report 2025, WorldID whitepaper, Proof of Humanity docs, eIDAS 2.0 Architecture Reference Framework v1.4*
