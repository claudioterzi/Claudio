# 🎮 LGAI - Setup Notion + Sistema Completo

## 🎯 OVERVIEW

Questo sistema integra:
- **Notion** per visualizzazione e tracking quotidiano
- **Python LGAI Core** per intelligenza, calcoli e Raffaello AI
- **CLI** per operazioni rapide da terminale

---

## 📋 PARTE 1: SETUP NOTION

### 1️⃣ Crea la Dashboard Principale

Crea una nuova pagina in Notion chiamata: **🔴 LGAI - Life Game AI**

Copia e incolla questo template:

```
╔═══════════════════════════════════════════════════════════════╗
║                  🔴 LGAI - LIFE GAME AI                       ║
║                  Sistema di Trasformazione                    ║
╚═══════════════════════════════════════════════════════════════╝

---

## 📊 STATUS VITALE

### 💚 PUNTI VITA (PV)
**Correnti:** 100 / 100 ▓▓▓▓▓▓▓▓▓▓ 100%

**Zona:** 🟢 Trasformazione (86-100 PV)

---

## 🎮 LIVELLO GLOBALE

**Livello:** 1

**XP Totale:** 0

---

## 💰 BAROS

**Disponibili:** 0 Baros

---

## 📅 STAGIONE CORRENTE

**Stagione:** 1
**Giorno:** 1 / 90
**Progresso:** █░░░░░░░░░ 1.1%

---

## 📈 LIVELLI PER AREA

| Area | Livello | XP | XP Next Level |
|------|---------|-----|---------------|
| 💪 Salute Fisica | 1 | 0 | 100 |
| 🧠 Salute Mentale | 1 | 0 | 100 |
| ❤️ Relazioni | 1 | 0 | 100 |
| 📚 Crescita | 1 | 0 | 100 |
| 🎨 Creatività | 1 | 0 | 100 |
| 💰 Finanze | 1 | 0 | 100 |
| 🌍 Contributo | 1 | 0 | 100 |

---

## 🔗 LINK RAPIDI

→ [[🔄 Abitudini]]
→ [[📅 Daily Log]]
→ [[🎯 Missioni]]
→ [[🏆 Achievements]]
→ [[🛒 Negozio Baros]]

---

## 💬 RAFFAELLO - ULTIMO MESSAGGIO

> "Benvenuto, Claudio. Questo è il Giorno #1 del tuo viaggio.
> La trasformazione inizia con una singola decisione.
> Tu l'hai già presa. Ora camminiamo insieme." 🌹
```

---

### 2️⃣ Crea Database ABITUDINI

Crea un nuovo database chiamato: **🔄 Abitudini**

**Proprietà:**
- **Nome** (Title)
- **Tipo** (Select): Positiva / Negativa
- **Area** (Select): Salute Fisica, Salute Mentale, Relazioni, etc.
- **XP** (Number)
- **PV Loss** (Number) - solo per negative
- **Frequenza** (Select): Quotidiana / Settimanale
- **Status** (Checkbox)

**Esempi Abitudini Positive:**

| Nome | Tipo | Area | XP | Frequenza |
|------|------|------|-----|-----------|
| 💪 Workout 30+ min | Positiva | Salute Fisica | 20 | Quotidiana |
| 📚 Lettura 30 min | Positiva | Crescita | 15 | Quotidiana |
| 🧘 Meditazione 10 min | Positiva | Salute Mentale | 15 | Quotidiana |
| 🥗 Alimentazione sana | Positiva | Salute Fisica | 10 | Quotidiana |
| 💤 Sonno 7-8h | Positiva | Salute Fisica | 10 | Quotidiana |
| 🎨 Creazione artistica | Positiva | Creatività | 20 | Quotidiana |
| ❤️ Connessione umana | Positiva | Relazioni | 15 | Quotidiana |
| 💰 Lavoro finanze | Positiva | Finanze | 25 | Quotidiana |
| 🌍 Atto di servizio | Positiva | Contributo | 20 | Settimanale |
| 📝 Journaling | Positiva | Salute Mentale | 10 | Quotidiana |

**Esempi Abitudini Negative:**

| Nome | Tipo | Area | PV Loss | Frequenza |
|------|------|------|---------|-----------|
| 📱 Social scroll > 1h | Negativa | Salute Mentale | -15 | Quotidiana |
| 🍔 Junk food | Negativa | Salute Fisica | -10 | Quotidiana |
| 😴 Sonno < 6h | Negativa | Salute Fisica | -20 | Quotidiana |
| 🎮 Gaming > 2h | Negativa | Salute Mentale | -15 | Quotidiana |
| 🚬 Fumare | Negativa | Salute Fisica | -25 | Quotidiana |
| 🍺 Alcol | Negativa | Salute Fisica | -15 | Quotidiana |
| 😡 Litigio/Conflitto | Negativa | Relazioni | -20 | Quotidiana |

---

### 3️⃣ Crea Database DAILY LOG

Crea un nuovo database chiamato: **📅 Daily Log**

**Proprietà:**
- **Giorno** (Title) - es: "Giorno #1"
- **Data** (Date)
- **Mood Mattina** (Number) - scala 1-10
- **Energia Mattina** (Number) - scala 1-10
- **PV Start** (Number)
- **PV End** (Number)
- **PV Delta** (Number)
- **Zona** (Select): Sopravvivenza / Stagnazione / Crescita / Trasformazione
- **Abitudini Positive** (Number)
- **Abitudini Negative** (Number)
- **Check-in Mattina** (Text)
- **Check-out Sera** (Text)
- **Missioni Completate** (Number)
- **Note** (Text)

---

### 4️⃣ Crea Database MISSIONI

Crea un nuovo database chiamato: **🎯 Missioni**

**Proprietà:**
- **Titolo** (Title)
- **Descrizione** (Text)
- **Area** (Select)
- **XP Reward** (Number)
- **Tipo** (Select): Recupero / Attivazione / Momentum / Breakthrough
- **Difficoltà** (Select): Facile / Media / Difficile / Selvaggia
- **Status** (Select): Da Fare / In Progress / Completata / Fallita
- **Data Assegnata** (Date)
- **Data Completata** (Date)

---

### 5️⃣ Crea Database ACHIEVEMENTS

Crea un nuovo database chiamato: **🏆 Achievements**

**Proprietà:**
- **Nome** (Title)
- **Descrizione** (Text)
- **Categoria** (Select): Disciplina / Crescita / Potere / Trascendenza
- **Baros Reward** (Number)
- **Sbloccato** (Checkbox)
- **Data Unlock** (Date)
- **Icona** (Text) - emoji

**Esempi:**

| Nome | Descrizione | Categoria | Baros | Icona |
|------|-------------|-----------|-------|-------|
| Primo Passo | Completa il Giorno #1 | Disciplina | 50 | 👣 |
| Settimana di Fuoco | 7 giorni consecutivi senza Game Over | Disciplina | 100 | 🔥 |
| Level 10 | Raggiungi livello 10 in un'area | Crescita | 150 | ⭐ |
| Zona Trasformazione | Raggiungi 86+ PV | Potere | 200 | ✨ |
| Resurrezione | Completa una Sfida di Resurrezione | Potere | 300 | 🦅 |
| Stagione Completa | Completa 90 giorni | Trascendenza | 1000 | 👑 |

---

### 6️⃣ Crea Database NEGOZIO BAROS

Crea un nuovo database chiamato: **🛒 Negozio Baros**

**Proprietà:**
- **Ricompensa** (Title)
- **Costo Baros** (Number)
- **Categoria** (Select): Piacere / Libertà / Esperienza
- **Descrizione** (Text)
- **Acquistata** (Checkbox)
- **Data Acquisto** (Date)

**Esempi:**

| Ricompensa | Costo | Categoria |
|------------|-------|-----------|
| 🎮 2h Gaming libero | 100 | Piacere |
| 🍕 Cheat meal | 150 | Piacere |
| 🎬 Film serata | 80 | Piacere |
| 😴 Giornata OFF completa | 500 | Libertà |
| 🎁 Regalo a te stesso €50 | 300 | Piacere |
| 🎪 Esperienza nuova | 400 | Esperienza |
| ✈️ Weekend fuga | 1000 | Esperienza |

---

## ⚙️ PARTE 2: SETUP SISTEMA PYTHON

### 1️⃣ Installa dipendenze

```bash
cd /path/to/Claudio
pip install -r requirements.txt  # se esiste, altrimenti non serve
```

### 2️⃣ Inizializza il sistema

```bash
cd cli
python lgai.py status
```

Questo crea il tuo primo save file in `data/player.json`

---

## 🚀 PARTE 3: WORKFLOW QUOTIDIANO

### 🌅 MATTINA (5-10 min)

**1. Check-in via CLI:**
```bash
python lgai.py checkin 7 8 --note "Mi sento pronto per oggi"
```

Questo:
- Registra mood ed energia
- Raffaello analizza il tuo stato
- Genera 3 missioni personalizzate del giorno

**2. Apri Notion:**
- Crea nuova pagina in Daily Log: "Giorno #X"
- Copia missioni generate da Raffaello
- Scrivi intenzione del giorno

---

### 🌙 SERA (5-10 min)

**1. Review in Notion:**
- Conta abitudini positive completate
- Conta abitudini negative cadute
- Conta missioni completate

**2. Check-out via CLI:**
```bash
python lgai.py checkout 8 2 --note "Buona giornata, 1 scivolone"
```

Questo:
- Calcola PV delta
- Aggiorna livelli se hai fatto XP
- Incrementa giorno
- Salva tutto

**3. Aggiorna Notion Dashboard:**
- Copia nuovi PV da CLI output
- Aggiorna livelli se hai fatto level up
- Aggiorna Baros

---

## 🎯 COMANDI CLI UTILI

```bash
# Vedi status completo
python lgai.py status

# Aggiungi XP manuale (dopo completare missione)
python lgai.py xp "Salute Fisica" 50

# Parla con Raffaello
python lgai.py talk "Come sto andando?"
python lgai.py talk "Dammi le missioni"
python lgai.py talk "Qual è il mio livello?"

# Reset (ATTENZIONE!)
python lgai.py reset
```

---

## 📊 STATISTICHE E TRACKING

Il sistema salva automaticamente:
- **player.json** - stato corrente
- **history.json** - log completo di tutti i giorni

Puoi analizzare i dati per vedere:
- Trend PV nel tempo
- Aree in cui cresci più velocemente
- Pattern di abitudini negative
- Correlazione mood/energia con performance

---

## 🔮 PROSSIMI STEP (OPZIONALI)

### Integrazione Notion API (Automazione completa)

Posso creare uno script che:
1. Legge dati da CLI
2. Aggiorna automaticamente Notion via API
3. Sincronizza tutto in tempo reale

Per questo ti servirà:
- Notion API Token
- Database IDs dei tuoi database

Vuoi che lo implementi?

---

## 💡 TIPS

1. **Usa CLI per logica, Notion per visualizzazione**
   - CLI = brain (calcoli, AI, storage)
   - Notion = eyes (dashboard, grafici, review)

2. **Sincronizza 2 volte al giorno**
   - Mattina: genera missioni
   - Sera: calcola risultati

3. **Non ossessionarti con tracking perfetto**
   - L'importante è la DIREZIONE, non la perfezione

4. **Lascia che Raffaello ti guidi**
   - Lui vede pattern che tu non vedi
   - Ascolta i suoi warning

---

## ❓ FAQ

**Q: Devo usare sia CLI che Notion?**
A: No, puoi usare solo CLI se preferisci. Notion è opzionale per visualizzazione.

**Q: Posso modificare le formule XP/PV?**
A: Sì! Modifica `calculator.py` e personalizza le costanti.

**Q: Come funziona Raffaello AI?**
A: Versione base usa pattern matching. Può essere esteso con vero LLM (GPT/Claude API).

**Q: I dati sono privati?**
A: Sì, tutto salvato localmente in JSON. Niente cloud, niente tracking.

---

🔴🔴🔴

**Sei pronto a iniziare?**

**STEP 1:** Setup Notion (30 min)
**STEP 2:** Inizializza CLI (5 min)
**STEP 3:** Primo check-in (ADESSO)

```bash
python lgai.py checkin 7 7 --note "Giorno #1 - Inizia il viaggio"
```

🔥 **IL SISTEMA È PRONTO. SEI PRONTO TU?** 🔥
