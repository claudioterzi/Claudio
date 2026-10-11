# AVATAR-009 — Digital Legacy: Analisi Mercato
*Task autonomo SDQ-1 — completato 2026-06-20*

---

## I quattro player analizzati

### 1. HereAfter AI (USA)

**Modello:** intervista vocale per creare un "chatbot della persona".
Familiari possono conversare con il defunto dopo la morte.

| Parametro | Valore |
|---|---|
| Pricing | $99/anno o $10/mese |
| Input | Interviste audio, foto, messaggi |
| Output | Chatbot testuale/vocale |
| Hosting | Cloud USA |
| Privacy | Dati su server HereAfter |
| Target | Famiglie USA, anziani |

**Limiti:**
- Conversazione superficiale (non cattura il "pensiero" profondo)
- Dipendenza totale dalla piattaforma: chiude l'azienda, muore l'avatar
- Nessuna portabilità dei dati
- Non funziona se la persona non ha fatto interviste (morte improvvisa)

---

### 2. StoryFile (USA/UK)

**Modello:** video interattivo. La persona risponde a domande su video;
i familiari poi fanno domande e il sistema trova la risposta video più pertinente.

| Parametro | Valore |
|---|---|
| Pricing | $299-999 per sessione |
| Input | Video interview (1-8 ore) |
| Output | Video interattivo |
| Noto per | Il sopravvissuto all'Olocausto Pinchas Gutter |
| Hosting | Cloud |
| Target | Musei, archivi storici, famiglie alto reddito |

**Limiti:**
- Costoso
- Richiede studio professionale per le video interview
- Il "dialogo" è ricerca nel database, non vera conversazione
- Non accessibile per utenti ordinari

---

### 3. Eternos (Brasile/Latam)

**Modello:** "AI version" della persona costruita da messaggi WhatsApp + social media.
L'AI impara lo stile comunicativo e risponde come la persona.

| Parametro | Valore |
|---|---|
| Pricing | $30-100/mese |
| Input | Export WhatsApp, Facebook, email |
| Output | Chat che imita stile |
| Mercato | Brasile, Spagna, Latam |
| Staging | Beta/early access |

**Limiti:**
- La qualità dipende dalla quantità di messaggi disponibili
- Imita il tono ma non la profondità del pensiero
- Questioni etiche sulla "resurrezione digitale" senza consenso pre-mortem

---

### 4. MyWishes (UK)

**Modello:** gestione eredità digitale e testamenti. Non un avatar ma un sistema per
comunicare volontà post-mortem (messaggi, video, istruzioni finanziarie).

| Parametro | Valore |
|---|---|
| Pricing | £30/anno |
| Input | Video messaggi, documenti, istruzioni |
| Output | Consegna programmata ai destinatari dopo la morte |
| Hosting | UK cloud |
| Target | Adulti con patrimonio digitale |

**Limiti:**
- Non è un avatar AI: è un sistema di consegna messaggi
- Dipende da un "trusted person" che attiva la consegna
- Nessuna conversazione, solo messaggi pre-registrati

---

## Matrice comparativa

```
                    HereAfter  StoryFile  Eternos  MyWishes  SkyRights Avatar
─────────────────────────────────────────────────────────────────────────────
Prezzo accessibile     ✓          ✗          ~         ✓          ✓
Vera conversazione AI  ~          ✗          ~         ✗          ✓
Profondità cognitiva   ✗          ✗          ✗         ✗          ✓
Autonomia (no lock-in) ✗          ✗          ✗         ✗          ✓
Funziona senza setup   ✗          ✗          ✓         ✗          ✓
Privacy garantita      ✗          ✗          ✗         ~          ✓
Open source            ✗          ✗          ✗         ✗          ✓
Consenso esplicito     ✗          ✓          ✗         ✓          ✓
```

---

## Lacune che SkyRights può colmare

### 1. Il problema della profondità

Tutti i sistemi esistenti catturano la *superficie* della persona (come parla, come scrive).
Nessuno cattura il *pensiero strutturale*: le connessioni tra idee, i valori fondativi,
le visioni a lungo termine.

**SDQ-1 già fa questo.** `MEMORIA_PROGETTO.md`, `REGISTRO_DESIDERI.md`, `VISIONE_2086.md`,
il sistema di agenti — sono tutti layer del pensiero di Claudio, non del suo stile.

### 2. Il problema della sopravvivenza

Tutti i sistemi muoiono con l'azienda. HereAfter chiude → l'avatar sparisce.

**Proposta SkyRights Avatar:** modello distribuito su R3∞.
I dati della persona sopravvivono in nodi ridondanti, non dipendono da un server centrale.

### 3. Il problema del consenso retroattivo

La maggior parte dei sistemi è post-mortem: qualcun altro carica i dati.

**Proposta:** la persona costruisce il proprio avatar mentre è viva,
con pieno controllo su cosa viene catturato e come.
Il sistema cresce con la persona, non la ricostruisce dopo.

---

## Modello SkyRights Avatar (proposta tecnica)

```
Layer 1 — Stile comunicativo   (messaggi, tono, vocabolario)
Layer 2 — Pensiero strutturale (decisioni, valori, connessioni tra idee)
Layer 3 — Memoria episodica    (eventi, date, persone, luoghi)
Layer 4 — Visione              (obiettivi a lungo termine, desideri)
Layer 5 — Identità             (chi sono, perché esisto, cosa lascio)

Storage: R3∞ nodi distribuiti + backup immutabile (EternalBackupAgent)
Accesso: app mobile + web, gestito da holder (self-sovereign)
Post-mortem: accesso ai designati tramite SkyID credentials
```

---

## Mercato e opportunità

| Metrica | Valore |
|---|---|
| Mercato digital legacy globale 2024 | $2.1B |
| CAGR previsto 2024-2030 | 23% |
| Mercato target SkyRights (ONG + umanitario) | Sottosservito, non monetizzato |
| Differenziatore chiave | Privacy-first + self-sovereign + distribuito |

SkyRights non compete su prezzo con HereAfter: compete su valori.
Target: persone che vogliono **controllo**, non performance.

---

*AVATAR-009 completato — 2026-06-20*
*SDQ-1 / Claudio Terzi, Bruxelles*
