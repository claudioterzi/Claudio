# 📐 FORMULE NOTION COMPLETE - LGAI

Questo file contiene tutte le formule Notion per implementare i calcoli automatici nel sistema LGAI.

---

## 🎯 COME USARE QUESTE FORMULE

1. Apri il database in Notion dove vuoi la formula
2. Aggiungi una nuova proprietà di tipo "Formula"
3. Copia e incolla la formula dal blocco qui sotto
4. Modifica i nomi delle proprietà se necessari (devono corrispondere ai tuoi database)

---

## 📅 FORMULE PER DAILY LOG

### 1. **CALCOLO DELTA PV**

Calcola il cambiamento di PV giornaliero basato su abitudini positive e negative.

```notion
// Somma PV dalle abitudini positive
let positive = prop("Abitudini Positive").map(
  current => current.prop("PV Delta")
).sum()

// Somma PV dalle abitudini negative (già negativi)
let negative = prop("Abitudini Negative").map(
  current => current.prop("PV Delta")
).sum()

// Bonus se giorno perfetto (zero negative + molte positive)
let bonus = (negative == 0 and positive > 100) ? 20 : 0

// Totale
positive + negative + bonus
```

**Note:**
- `Abitudini Positive` e `Abitudini Negative` devono essere proprietà Relation
- Ogni abitudine deve avere campo `PV Delta`
- PV Delta per negative è già negativo (es: -10)

---

### 2. **CALCOLO XP PER AREA**

Calcola XP totale guadagnato per un'area specifica (ripeti per tutte le 9 aree).

```notion
// Esempio per Area "Salute Fisica"
// Ripeti questa formula per tutte le 9 aree cambiando il nome

// XP da abitudini
let abitudini_xp = prop("Abitudini Positive").filter(
  current =>
    current.prop("Area Primaria") == "Salute Fisica" or
    current.prop("Area Secondaria") == "Salute Fisica"
).map(
  current =>
    (current.prop("Area Primaria") == "Salute Fisica" ?
      current.prop("XP Area Primaria") : 0) +
    (current.prop("Area Secondaria") == "Salute Fisica" ?
      current.prop("XP Area Secondaria") : 0)
).sum()

// XP da missioni
let missioni_xp = prop("Missioni Completate").filter(
  current =>
    current.prop("Area Principale") == "Salute Fisica" or
    current.prop("Area Secondaria") == "Salute Fisica"
).map(
  current =>
    (current.prop("Area Principale") == "Salute Fisica" ?
      current.prop("XP Reward Primaria") : 0) +
    (current.prop("Area Secondaria") == "Salute Fisica" ?
      current.prop("XP Reward Secondaria") : 0)
).sum()

// Totale
abitudini_xp + missioni_xp
```

**Crea 9 proprietà formula:**
- `XP Salute Fisica`
- `XP Salute Mentale`
- `XP Relazioni`
- `XP Crescita`
- `XP Creatività`
- `XP Finanze`
- `XP Contributo`
- `XP Spirituale`
- `XP Carriera`

---

### 3. **CALCOLO BAROS GIORNALIERI**

Calcola Baros guadagnati nel giorno.

```notion
// Baros da abitudini
let abitudini_baros = prop("Abitudini Positive").map(
  current => current.prop("Baros")
).sum()

// Baros da missioni
let missioni_baros = prop("Missioni Completate").map(
  current => current.prop("Baros Reward")
).sum()

// Bonus giorno perfetto (zero abitudini negative)
let bonus_perfetto = prop("Abitudini Negative").empty() ? 50 : 0

// Bonus streak (ogni 7 giorni)
let giorno = prop("Giorno #")
let bonus_streak = (giorno % 7 == 0) ? 150 : 0

// Totale
abitudini_baros + missioni_baros + bonus_perfetto + bonus_streak
```

---

### 4. **INDICATORE QUALITÀ GIORNATA**

Score 0-100 con emoji che rappresenta la qualità della giornata.

```notion
let pv_delta = prop("Delta PV")
let xp_totale = prop("Delta XP Totale")
let n_positive = prop("Abitudini Positive").length
let n_negative = prop("Abitudini Negative").length

// Calcola score componenti
let score_pv = (pv_delta > 0) ? 30 : 0
let score_xp = (xp_totale > 300) ? 30 : 0
let score_positive = (n_positive >= 8) ? 20 : n_positive * 2.5
let score_negative = (n_negative == 0) ? 20 : max(0, 20 - n_negative * 10)

let score = score_pv + score_xp + score_positive + score_negative

// Output con emoji
if(score >= 90, "✨ PERFETTO",
  if(score >= 75, "🌟 OTTIMO",
    if(score >= 60, "✅ BUONO",
      if(score >= 40, "⚠️ SUFFICIENTE",
        "🔴 CRITICO"))))
```

---

## 📊 FORMULE PER DATABASE AREE (9 Aree)

### 5. **CALCOLO LIVELLO ATTUALE**

Calcola livello basato su XP totale accumulato.

```notion
// Formula: livello = floor(log(xp/100 + 1) / log(1.5)) + 1
let xp_totale = prop("XP Totale Area")

// Calcola livello
let livello = floor(log(xp_totale / 100 + 1) / log(1.5)) + 1

// Cap a livello 100
min(livello, 100)
```

**Spiegazione:**
- Formula esponenziale inversa
- Livello 1 = 0-100 XP
- Livello 2 = 100-250 XP
- Livello 3 = 250-475 XP
- Etc.

---

### 6. **XP NECESSARI PER PROSSIMO LIVELLO**

Formula esponenziale: `100 * 1.5^(livello-1)`

```notion
let livello_corrente = prop("Livello")

// Formula: 100 * 1.5^(livello-1)
round(100 * pow(1.5, livello_corrente - 1))
```

---

### 7. **PROGRESSO PERCENTUALE**

Mostra quanto sei vicino al prossimo livello.

```notion
let xp_corrente = prop("XP Corrente Livello")
let xp_necessari = prop("XP Necessari")

// Percentuale
let perc = round((xp_corrente / xp_necessari) * 100)

// Output formattato
format(perc) + "%"
```

**Oppure con barra visuale:**

```notion
let xp_corrente = prop("XP Corrente Livello")
let xp_necessari = prop("XP Necessari")

let perc = (xp_corrente / xp_necessari) * 100
let filled = floor(perc / 5)  // 20 blocchi totali

// Crea barra
let bar = ""
let i = 0
while(i < 20,
  bar = bar + (i < filled ? "█" : "░"),
  i = i + 1
)

bar + " " + format(round(perc)) + "%"
```

---

## 📈 FORMULE PER ANALYTICS

### 8. **RISK SCORE (Probabilità Game Over)**

Analizza ultimi 7 giorni e calcola probabilità Game Over.

```notion
// Conta giorni con PV negativo
let ultimi_7 = prop("Ultimi 7 Giorni")
let giorni_pv_neg = ultimi_7.filter(
  current => current.prop("Delta PV") < 0
).length * 20

// % abitudini negative in settimana
let total_negative = ultimi_7.map(
  current => current.prop("Abitudini Negative").length
).sum()
let perc_negative = (total_negative / 7) * 30

// Giorni senza abitudini positive
let giorni_zero_pos = ultimi_7.filter(
  current => current.prop("Abitudini Positive").length == 0
).length * 15

// Streak interrotti nel mese
let streak_rotti = prop("Streak Rotti Mese") * 10

// Score totale
let risk = min(
  giorni_pv_neg + perc_negative + giorni_zero_pos + streak_rotti,
  100
)

// Output
if(risk >= 80, "⚠️ GAME OVER IMMINENTE",
  if(risk >= 60, "🔴 RISCHIO ALTO",
    if(risk >= 40, "🟠 RISCHIO MODERATO",
      if(risk >= 20, "🟡 ATTENZIONE",
        "🟢 ZONA SICURA"))))
```

---

### 9. **PREDIZIONE LEVEL UP**

Calcola giorni stimati per raggiungere prossimo livello.

```notion
let xp_mancanti = prop("XP Necessari") - prop("XP Corrente")
let media_xp_giorno = prop("XP Totale Ultimi 7 Giorni") / 7

let giorni = round(xp_mancanti / media_xp_giorno)

if(media_xp_giorno == 0, "❌ Nessuna attività",
  if(giorni <= 3, "🔥 " + format(giorni) + " giorni (VICINO!)",
    if(giorni <= 7, "⚡ " + format(giorni) + " giorni",
      if(giorni <= 14, "📅 " + format(giorni) + " giorni",
        "📆 " + format(giorni) + " giorni"))))
```

---

## 🛒 FORMULE PER NEGOZIO BAROS

### 10. **PUOI PERMETTERTI**

Indica se hai abbastanza Baros per una ricompensa.

```notion
let baros_disponibili = prop("Baros Disponibili")
let costo = prop("Costo Baros")

if(baros_disponibili >= costo,
  "✅ Puoi acquistare",
  "❌ Ti servono altri " + format(costo - baros_disponibili) + " Baros")
```

---

### 11. **CHECK RESTRIZIONI MENSILI**

Verifica se puoi acquistare in base a restrizioni (es: "Max 2x/mese").

```notion
let restrizioni = prop("Restrizioni")
let acquisti_mese = prop("Acquisti Questo Mese")

// Estrai limite (es: "Max 2x/mese" -> 2)
let has_max = contains(restrizioni, "Max")
let limit = if(has_max,
  toNumber(replaceAll(
    replaceAll(restrizioni, "Max ", ""),
    "x/mese", ""
  )),
  999
)

if(restrizioni == "Illimitato", "✅ Disponibile",
  if(acquisti_mese < limit,
    "✅ Ancora " + format(limit - acquisti_mese) + " disponibili",
    "🔴 Limite mensile raggiunto"))
```

---

## 🎯 FORMULE PER MISSIONI

### 12. **TOTAL REWARD**

Calcola reward totale di una missione (XP + Baros).

```notion
let xp_primaria = prop("XP Reward Primaria")
let xp_secondaria = prop("XP Reward Secondaria")
let baros = prop("Baros Reward")

"💎 " + format(xp_primaria + xp_secondaria) + " XP + " + format(baros) + " Baros"
```

---

### 13. **DIFFICOLTÀ COLORE**

Assegna colore in base a difficoltà.

```notion
let diff = prop("Difficoltà")

if(diff == "facile", "🟢 Facile",
  if(diff == "media", "🟡 Media",
    if(diff == "difficile", "🟠 Difficile",
      "🔴 Selvaggia")))
```

---

## 💡 TIPS PER IMPLEMENTAZIONE

### Sequenza consigliata:

1. **Crea prima i database base:**
   - Daily Log
   - Abitudini
   - Missioni
   - Aree (9 record, uno per area)

2. **Aggiungi formule semplici:**
   - Delta PV
   - Baros Giornalieri
   - Qualità Giornata

3. **Aggiungi formule complesse:**
   - XP per Area (9 formule)
   - Livello Attuale
   - Predizioni

4. **Testa con dati reali:**
   - Crea un Daily Log di esempio
   - Aggiungi abitudini e missioni
   - Verifica che i calcoli siano corretti

### Proprietà database necessarie:

**Daily Log:**
- Giorno # (Number)
- Abitudini Positive (Relation)
- Abitudini Negative (Relation)
- Missioni Completate (Relation)
- Delta PV (Formula)
- Delta XP Totale (Formula o Number)
- Baros Guadagnati (Formula)
- Qualità Giornata (Formula)

**Abitudini:**
- Nome (Title)
- Tipo (Select): Positiva/Negativa
- Area Primaria (Select)
- Area Secondaria (Select)
- XP Area Primaria (Number)
- XP Area Secondaria (Number)
- PV Delta (Number)
- Baros (Number)

**Aree:**
- Nome Area (Title)
- XP Totale Area (Rollup da Daily Log)
- Livello (Formula)
- XP Necessari (Formula)
- XP Corrente Livello (Formula)
- Progresso % (Formula)

---

## 🔧 TROUBLESHOOTING

### **Le formule non funzionano:**

1. Verifica nomi proprietà (case-sensitive!)
2. Controlla che Relation siano configurate correttamente
3. Assicurati che i tipi di dato corrispondano

### **Risultati strani:**

1. Controlla che PV Delta per negative sia NEGATIVO
2. Verifica che Rollup usino la funzione corretta (Sum, Average, etc.)
3. Testa con numeri semplici prima

### **Performance lente:**

1. Le formule complesse rallentano Notion
2. Considera di calcolare alcune cose in Python e sincronizzare
3. Usa View filtrate invece di calcolare tutto

---

🔴🔴🔴

**Con queste formule, il tuo Notion diventa un CERVELLO CALCOLATORE automatico!**

Ogni volta che aggiorni un'abitudine o completi una missione,
tutto si ricalcola automaticamente.

**È magia matematica.** ✨
