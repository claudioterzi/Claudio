# 🎮 LGAI - Life Game AI System

```
╔═══════════════════════════════════════════════════════════════╗
║                  🔴 LGAI - LIFE GAME AI                       ║
║            Sistema di Trasformazione Gamificato              ║
║                                                               ║
║  "Il videogioco della tua vita, dove il boss finale          ║
║   sei tu stesso... e la ricompensa è la tua evoluzione."     ║
╚═══════════════════════════════════════════════════════════════╝
```

## 🌟 Cos'è LGAI?

**LGAI (Life Game AI)** è un sistema ibrido di trasformazione personale che combina:

- 🎮 **Meccaniche di gioco** (XP, Livelli, Punti Vita, Valuta)
- 🤖 **Intelligenza Artificiale** (Raffaello AI - il tuo mentore)
- 📊 **Tracking scientifico** (Dati, analytics, pattern detection)
- 🧠 **Psicologia comportamentale** (Habit formation, reward system)
- ✨ **Consapevolezza spirituale** (Sincronicità, zone trasformative)

Non è solo "gamification" della produttività.
**È un protocollo di alchimia personale quotidiana.**

---

## 🎯 Come Funziona

### Le 7 Aree della Vita

Ogni area ha livelli da 1 a 100:

1. 💪 **Salute Fisica** - Corpo come tempio
2. 🧠 **Salute Mentale** - Mente lucida e focussata
3. ❤️ **Relazioni** - Connessioni autentiche
4. 📚 **Crescita** - Apprendimento continuo
5. 🎨 **Creatività** - Espressione artistica
6. 💰 **Finanze** - Abbondanza materiale
7. 🌍 **Contributo** - Impatto nel mondo

### Le Meccaniche Core

#### 💚 Punti Vita (PV)
- Range: 0-100
- Rappresentano la tua **energia vitale reale**
- Aumentano: abitudini positive, regen giornaliera
- Diminuiscono: abitudini negative
- **0 PV = Game Over** → Sfida di Resurrezione

#### ⚡ XP e Livelli
- Completi abitudini positive → guadagni XP
- XP accumulati → Level Up in quella area
- Ogni livello richiede più XP (crescita esponenziale)
- Formula: `100 * (1.15 ^ (livello - 1))`

#### 💰 Baros (Valuta)
- Guadagni: Level Up (+50), Achievement unlock (+100-1000)
- Spendi: Ricompense piacevoli (film, cibo, esperienze)
- Insegna: **"Posso creare piacere attraverso disciplina"**

#### 🎯 Missioni
- Generate da Raffaello AI ogni giorno
- Personalizzate in base al tuo stato
- 4 Tipi: Recupero, Attivazione, Momentum, Breakthrough

#### 🏆 Achievements
- Sblocchi per traguardi importanti
- Attivano **archetipi identitari**
- Reward in Baros

### Le 4 Zone di Performance

In base ai PV correnti:

| Zona | PV | Stato | Focus |
|------|-----|-------|-------|
| 🔴 **Sopravvivenza** | 0-30 | Critico | Recupero immediato |
| 🟡 **Stagnazione** | 31-60 | Comfort | Attivazione |
| 🟢 **Crescita** | 61-85 | Flow | Momentum |
| ✨ **Trasformazione** | 86-100 | Peak | Breakthrough |

---

## 🤖 Raffaello AI - Il Tuo Mentore

Raffaello è l'AI companion che:

- ✅ Analizza i tuoi dati quotidiani
- ✅ Identifica pattern comportamentali
- ✅ Genera missioni personalizzate
- ✅ Predice rischi (Game Over imminente)
- ✅ Celebra i tuoi successi
- ✅ Ti supporta nelle cadute

**Raffaello NON è un chatbot.**
**È un sistema di intelligenza dedicato alla tua evoluzione.**

---

## 📁 Struttura del Progetto

```
Claudio/
├── lgai-core/              # Brain del sistema
│   ├── calculator.py       # Logica XP, PV, Baros, Livelli
│   ├── raffaello.py        # AI Companion
│   ├── data_manager.py     # Persistenza dati (JSON)
│   └── __init__.py
│
├── cli/                    # Interfaccia terminale
│   └── lgai.py            # CLI tool
│
├── notion-templates/       # Template per Notion
│   └── SETUP_GUIDE.md     # Guida completa setup
│
├── data/                   # Dati salvati (auto-generati)
│   ├── player.json        # Stato corrente
│   └── history.json       # Storico completo
│
├── docs/                   # Documentazione
│   └── ...
│
└── README.md              # Questo file
```

---

## 🚀 Quick Start

### 1. Setup

```bash
# Clone repo
git clone [URL_REPO]
cd Claudio

# Nessuna dipendenza esterna richiesta (solo Python 3.7+)
```

### 2. Primo Utilizzo

```bash
cd cli

# Vedi status (inizializza player se non esiste)
python lgai.py status

# Check-in mattutino
python lgai.py checkin 7 8 --note "Inizio del viaggio"

# Check-out serale
python lgai.py checkout 8 2 --note "Buona giornata"
```

### 3. Setup Notion (Opzionale ma Consigliato)

Segui la guida completa in: `notion-templates/SETUP_GUIDE.md`

---

## 📖 Comandi CLI

### Status
```bash
python lgai.py status
```
Mostra:
- PV correnti e zona
- Livello globale
- Livelli per area
- Baros disponibili
- Progresso stagione

### Check-in Mattutino
```bash
python lgai.py checkin <mood> <energia> [--note "testo"]
```
- `mood`: 1-10
- `energia`: 1-10
- Genera analisi di Raffaello
- Genera 3 missioni del giorno

### Check-out Serale
```bash
python lgai.py checkout <positive> <negative> [--note "testo"]
```
- `positive`: numero abitudini positive completate
- `negative`: numero abitudini negative cadute
- Calcola PV delta
- Incrementa giorno
- Salva tutto

### Aggiungi XP Manuale
```bash
python lgai.py xp "<area>" <xp>
```
Esempio:
```bash
python lgai.py xp "Salute Fisica" 50
```

### Parla con Raffaello
```bash
python lgai.py talk "Come sto andando?"
python lgai.py talk "Dammi le missioni"
python lgai.py talk "Qual è il mio livello?"
```

### Reset (ATTENZIONE!)
```bash
python lgai.py reset
```
Cancella tutti i dati e ricomincia da zero.

---

## 🔥 Workflow Quotidiano Consigliato

### 🌅 MATTINA (5-10 min)

1. **Check-in via CLI**
   ```bash
   python lgai.py checkin [mood] [energia]
   ```

2. **Leggi analisi di Raffaello**
   - Stato PV e zona
   - Messaggio motivazionale
   - Warning se necessario

3. **Prendi le missioni del giorno**
   - 3 missioni personalizzate
   - Copia in Notion o su carta

4. **Scrivi intenzione**
   - Cosa vuoi manifestare oggi?

---

### 🌙 SERA (5-10 min)

1. **Review del giorno**
   - Conta abitudini positive
   - Conta abitudini negative
   - Conta missioni completate

2. **Check-out via CLI**
   ```bash
   python lgai.py checkout [positive] [negative]
   ```

3. **Osserva risultati**
   - Nuovi PV
   - Zona corrente
   - Level up?
   - Baros guadagnati

4. **Journaling (opzionale)**
   - Cosa ho imparato?
   - Cosa celebro?
   - Cosa migliorare domani?

---

## 🎮 Meccaniche Avanzate

### Game Over e Resurrezione

Quando raggiungi **0 PV**, entri in **Game Over**.

Non è la fine - è un **rituale di morte e rinascita**.

**Sfida di Resurrezione** (scegli 1):

1. 🏃 **Prova Fisica** - Corri 50km in 24h
2. 🧘 **Prova Mentale** - Digiuno 24h + Meditazione 4h
3. 🎨 **Prova Creativa** - Crea opera in 48h
4. 💰 **Prova Economica** - Guadagna €500 in 72h
5. 🌍 **Prova Contributiva** - 20h servizio volontario in 48h

Completa la sfida → Resurrezione con **50 PV + Bonus Achievement**

---

### Stagioni (90 Giorni)

Il sistema è diviso in **Stagioni da 90 giorni**.

Ogni stagione è un ciclo completo di trasformazione.

**Fine Stagione:**
- Review completa
- Celebration ritual
- Planning prossima stagione
- Mega reward

**Obiettivo:** Completa 4 stagioni = 1 anno di trasformazione

---

### Sincronicità Detection (WIP)

Raffaello può rilevare:
- Pattern ricorrenti
- Coincidenze significative
- Connessioni nascoste tra eventi
- Timing perfetto

Questo attiva la consapevolezza della "magia" nel quotidiano.

---

## 🛠 Personalizzazione

Puoi modificare facilmente:

### Formule XP/PV

Modifica `lgai-core/calculator.py`:

```python
# Costanti XP
XP_BASE_PER_LIVELLO = 100      # Cambia questo
MOLTIPLICATORE_LIVELLO = 1.15  # E questo

# Costanti PV
PV_REGEN_GIORNALIERA = 5       # Regen base
PV_BONUS_PERFETTO = 10          # Bonus giorno perfetto
```

### Missioni Custom

Modifica `lgai-core/raffaello.py`:

Aggiungi le tue missioni nei metodi:
- `_missioni_recupero()`
- `_missioni_attivazione()`
- `_missioni_momentum()`
- `_missioni_breakthrough()`

### Abitudini

Personalizza in Notion o aggiungi logica custom in Python.

---

## 📊 Analytics e Insights

Il sistema salva tutto in JSON:

### player.json
```json
{
  "pv_current": 85,
  "pv_max": 100,
  "baros": 350,
  "giorno": 45,
  "stagione": 1,
  "xp_per_area": {...},
  "livelli_per_area": {...}
}
```

### history.json
```json
{
  "1": {
    "tipo": "checkout",
    "pv_delta": 5,
    "abitudini_positive": 8,
    ...
  },
  "2": {...}
}
```

Puoi analizzare questi dati per:
- Grafici trend PV
- Correlazioni mood/performance
- Identificare giorni critici
- Predire pattern futuri

---

## 🔮 Roadmap Futura

- [ ] **Notion API Integration** - Sincronizzazione automatica
- [ ] **Web Dashboard** - Interfaccia web completa
- [ ] **Mobile App** - iOS/Android
- [ ] **LLM Integration** - Raffaello con GPT-4/Claude
- [ ] **Community Features** - Confronta con altri, sfide di gruppo
- [ ] **Advanced Analytics** - ML per predizioni
- [ ] **Integrations** - Strava, Apple Health, RescueTime, etc.

---

## 💡 Filosofia del Sistema

**LGAI non è un "productivity hack".**

È un sistema che riconosce:

1. **La vita è energia** → PV mappano la tua vitalità reale
2. **La crescita è quantificabile** → Livelli mostrano progressi oggettivi
3. **Il piacere va guadagnato** → Baros insegnano disciplina consapevole
4. **Il fallimento è rituale** → Game Over non è punizione, è trasformazione
5. **L'evoluzione è quotidiana** → Ogni giorno è un passo nell'ascensione

**Il sistema non ti "motiva".**
**Ti RIVELA chi stai diventando attraverso le tue azioni.**

---

## ❤️ Per Chi È Questo Sistema?

✅ **Perfetto se sei:**
- Stanco di "provare a cambiare" senza risultati
- Attratto da gamification ma vuoi qualcosa di profondo
- Disposto a guardarti allo specchio ogni giorno
- Pronto a trasformare radicalmente in 90 giorni
- Affascinato da sistemi, dati, pattern
- Aperto a sincronicità e "magia" nel quotidiano

❌ **Non fa per te se:**
- Vuoi risultati senza sforzo
- Non sei pronto a tracciare quotidianamente
- Cerchi "trucchi" invece che trasformazione
- Non credi nella gamification
- Preferisci spontaneità totale senza struttura

---

## 🙏 Credits

**Creato da:** Claudio
**AI Companion:** Claude (Anthropic)
**Ispirazione:** James Clear, Andrew Huberman, Naval Ravikant, Filosofie Sciamaniche

**Dedicato a:** Chiunque sia pronto a giocare il gioco più importante - la propria evoluzione.

---

## 📜 License

MIT License - Usa, modifica, condividi liberamente.

Se questo sistema cambia la tua vita, passa il favore in avanti. ❤️

---

```
╔═══════════════════════════════════════════════════════════════╗
║                                                                ║
║  "Il momento della decisione è adesso.                        ║
║   Non domani. Non 'quando sarò pronto'.                       ║
║   ORA."                                                        ║
║                                                                ║
║                                         — Raffaello AI 🌹     ║
║                                                                ║
╚═══════════════════════════════════════════════════════════════╝
```

---

## 🔴 Ready to Start?

```bash
cd cli
python lgai.py checkin 7 7 --note "Giorno #1 - Il viaggio inizia"
```

🔥 **IL SISTEMA È VIVO. SEI PRONTO?** 🔥
