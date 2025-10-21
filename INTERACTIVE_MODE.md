# 💬 MODALITÀ INTERATTIVA CON RAFFAELLO

## 🌟 Cos'è la Modalità Interattiva?

La modalità interattiva ti permette di **parlare con Raffaello** durante il check-in e checkout, facendo domande, chiedendo consigli, e riflettendo sulla tua giornata in tempo reale.

---

## 🚀 Come Attivare la Modalità Interattiva

### Check-in Mattutino Interattivo

```bash
python lgai.py checkin 8 7 --interactive --note "Giorno importante"
# Oppure versione corta
python lgai.py checkin 8 7 -i
```

**Cosa succede:**
1. Raffaello analizza il tuo stato
2. Genera le missioni del giorno
3. **Si apre una chat interattiva** dove puoi fare domande

### Check-out Serale Interattivo

```bash
# Modalità semplice
python lgai.py checkout 6 2 --interactive

# Modalità dettagliata
python lgai.py checkout --habits-positive "1,6,13" --habits-negative "101" -i
```

**Cosa succede:**
1. **Chat interattiva PRE-checkout** per riflettere sulla giornata
2. Puoi chiedere a Raffaello di aiutarti a scegliere le abitudini
3. Dopo la chat, completi normalmente il checkout

---

## 🎯 COMANDI SPECIALI nella Chat

Mentre sei in modalità interattiva, puoi usare questi comandi:

| Comando | Descrizione |
|---------|-------------|
| `continua` o `esci` | Termina la chat e procedi con il flusso normale |
| `status` | Mostra il tuo stato attuale (PV, zona, livello, Baros) |
| `habits` | Ricevi suggerimenti su quali abitudini tracciare oggi |
| `help` | Mostra l'elenco dei comandi disponibili |
| Qualsiasi domanda | Raffaello risponde in base al contesto! |

---

## 💡 ESEMPI DI UTILIZZO

### Esempio 1: Check-in con Domande Strategiche

```bash
$ python lgai.py checkin 7 8 -i

🌅 CHECK-IN MATTUTINO
   Mood: 7/10
   Energia: 8/10

💬 RAFFAELLO:
   Sei in Zona Trasformazione! Energia alta...

🎯 MISSIONI DEL GIORNO:
   1. Sessione Visione...
   2. Perdono Radicale...

============================================================
💬 MODALITÀ INTERATTIVA - CHAT CON RAFFAELLO
============================================================
📝 Puoi fare domande a Raffaello...
💡 Comandi speciali: 'continua', 'status', 'habits', 'help'
============================================================

🌹 Tu: Quale missione dovrei fare per prima?

🌹 Raffaello: Con questa energia da 8/10, ti consiglio di iniziare
   con la Sessione Visione. È una missione breakthrough che richiede
   focus, e tu ce l'hai ora. Il Perdono può aspettare il pomeriggio
   quando l'energia cala naturalmente.

🌹 Tu: E se mi sento sopraffatto?

🌹 Raffaello: Allora spezza la missione in micro-task da 5 minuti.
   Non devi completarla tutta subito. Anche 10 minuti di lavoro
   sulla Sessione Visione sono meglio di zero.

🌹 Tu: continua

🌹 Raffaello: Perfetto! Torniamo al flusso principale.

============================================================

✅ Check-in salvato!
```

### Esempio 2: Check-out con Riflessione Guidata

```bash
$ python lgai.py checkout --interactive

🌙 CHECK-OUT SERALE

💡 Stai per fare il checkout. Vuoi chattare con Raffaello prima?
   Può aiutarti a riflettere sulla giornata e scegliere le abitudini.

============================================================
💬 MODALITÀ INTERATTIVA - CHAT CON RAFFAELLO
============================================================

🌹 Tu: Ho fatto workout, meditazione, e letto. Ma ho mangiato junk food

🌹 Raffaello: Ottimo che tu sia consapevole. Hai fatto 3 abitudini
   forti (+40 PV), ma il junk food (-15 PV) erode il guadagno.
   Domanda: il junk food è stato una scelta o una reazione automatica?

🌹 Tu: Reazione a stress lavorativo

🌹 Raffaello: Ecco il pattern. Quando lo stress sale, il junk food
   diventa il tuo reflex. Strategia: la prossima volta che senti
   l'impulso, fai 3 respiri profondi PRIMA di aprire il frigo.
   Costa 10 secondi. Può salvarti 15 PV.

🌹 Tu: habits

🎯 ABITUDINI CONSIGLIATE PER OGGI:
   📈 Positive da prioritizzare:
      💪 1. Workout/Palestra (+15 PV)
      🥗 4. Cibo Sano (+10 PV)
      😴 5. Sonno 7+ ore (+15 PV)
      🧘 6. Meditazione (+15 PV)
      📚 13. Lettura 30min (+10 PV)

   📉 Negative da evitare oggi:
      🍔 101. Junk Food (-15 PV)
      😰 105. Overthinking/Ansia (-10 PV)
      ⏰ 112. Procrastinazione (-15 PV)

🌹 Tu: Quindi inserisco: --habits-positive "1,6,13" --habits-negative "101"?

🌹 Raffaello: Esattamente! Dopo che esci da questa chat, esegui:
   python lgai.py checkout --habits-positive "1,6,13" --habits-negative "101"

🌹 Tu: continua

============================================================

# Ora esegui il comando con i dettagli
```

### Esempio 3: Chiedere Status Durante la Giornata

```bash
🌹 Tu: status

📊 STATUS RAPIDO:
   PV: 85/100 | Zona: Trasformazione
   Livello Globale: 12
   Baros: 340
   Giorno: 23

🌹 Tu: Quanti Baros mi servono per la pizza?

🌹 Raffaello: La pizza costa 100 Baros. Ne hai 340, quindi
   puoi permettertela 3 volte! Ma ricorda: è limitata a 4
   volte al mese. Hai già usato 1 slot questo mese.
```

---

## 🎨 CASI D'USO AVANZATI

### 1. **Decision Making Mattutino**
```bash
# Sei indeciso su come prioritizzare la giornata
python lgai.py checkin 6 7 -i

🌹 Tu: Ho 3 progetti importanti oggi. Come scelgo?
🌹 Raffaello: [Analizza il tuo stato e suggerisce basandosi su energia/zona]
```

### 2. **Analisi Post-Fallimento**
```bash
# Giornata difficile, hai bisogno di supporto
python lgai.py checkout -i

🌹 Tu: Ho fallito tutte le missioni oggi. Mi sento un fallimento.
🌹 Raffaello: [Offre prospettiva, strategie di recovery, compassion]
```

### 3. **Strategia Pre-Perfect Day**
```bash
# Vuoi tentare un Perfect Day
python lgai.py checkin 9 9 -i

🌹 Tu: Oggi voglio fare Perfect Day. Come mi preparo?
🌹 Raffaello: [Dà strategia dettagliata per 0 abitudini negative]
```

### 4. **Riflessione Serale Profonda**
```bash
python lgai.py checkout -i

🌹 Tu: Cosa sto imparando dai miei pattern?
🌹 Raffaello: [Analizza i log storici e identifica pattern ricorrenti]
```

---

## ⚡ TIPS PER USARE AL MEGLIO LA MODALITÀ INTERATTIVA

### ✅ QUANDO USARLA

- **Mattina**: Quando hai bisogno di clarità su priorità
- **Sera**: Quando vuoi riflettere profondamente sulla giornata
- **Dubbio**: Quando non sai quali abitudini tracciare
- **Blocco**: Quando ti senti stuck e serve prospettiva
- **Vittoria**: Quando vuoi celebrare un breakthrough

### ❌ QUANDO NON USARLA

- Quando hai fretta (usa modalità standard)
- Quando sei già chiaro su cosa fare
- Quando vuoi solo loggare dati velocemente

### 🎯 DOMANDE POTENTI DA FARE

**Check-in:**
- "Quale missione ha più impatto oggi?"
- "Come gestisco l'energia bassa?"
- "Cosa devo sapere prima di iniziare?"

**Check-out:**
- "Perché ho ceduto su [abitudine]?"
- "Cosa posso migliorare domani?"
- "Ho fatto progressi questa settimana?"

---

## 🔄 WORKFLOW COMPLETO CON INTERATTIVITÀ

### Mattina (10 minuti)
```bash
# Check-in standard
python lgai.py checkin 7 8

# Oppure se hai domande
python lgai.py checkin 7 8 -i
# Fai 2-3 domande strategiche
# Esci con 'continua'
```

### Sera (15 minuti)
```bash
# Rifletti prima
python lgai.py checkout -i
# Chatta con Raffaello sulla giornata
# Decidi quali abitudini tracciare
# Esci con 'continua'

# Poi esegui il checkout
python lgai.py checkout --habits-positive "1,6,13" --habits-negative "101"
```

---

## 🎪 FEATURE BONUS

### Limitatore Gentile
Dopo 5 domande, Raffaello ti ricorda che puoi continuare:
```
💡 (Hai fatto molte domande! Ricorda: puoi scrivere 'continua' quando sei pronto)
```

### Gestione Interruzioni
- `Ctrl+C` → Esce gentilmente dalla chat
- `EOF` (Ctrl+D) → Chiude la sessione

### Context-Aware
Raffaello sa sempre in che contesto sei:
- Check-in → Conosce il tuo mood/energia
- Pre-checkout → Sa che stai per tracciare abitudini
- Generale → Accesso completo al tuo stato

---

## 🚀 PROSSIMI PASSI

Prova questo workflow per 7 giorni:

**Giorni 1-3**: Usa `-i` ogni giorno per familiarizzare
**Giorni 4-5**: Usa `-i` solo quando serve (blocco/dubbio)
**Giorni 6-7**: Trova il tuo ritmo personale

---

## 🎭 EASTER EGGS

Raffaello risponde in modo unico a certe domande:

```bash
🌹 Tu: Chi sei?
🌹 Raffaello: [Filosofia profonda sull'essere un companion AI]

🌹 Tu: Ho paura di fallire
🌹 Raffaello: [Messaggio potente sulla natura del fallimento come feedback]

🌹 Tu: Grazie
🌹 Raffaello: [Risposta sincera e motivazionale]
```

---

💬 **La modalità interattiva trasforma LGAI da tracker in companion di crescita** 💬
