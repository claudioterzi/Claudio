# 🎯 SISTEMA TRACCIAMENTO ABITUDINI DETTAGLIATO

## 📋 Panoramica

Il sistema LGAI ora supporta due modalità di tracciamento:

1. **MODALITÀ SEMPLICE**: Conta solo il numero di abitudini (veloce)
2. **MODALITÀ DETTAGLIATA**: Traccia QUALI abitudini specifiche hai fatto (precisa)

---

## 🆕 MODALITÀ DETTAGLIATA - Come Funziona

### Passo 1: Visualizza le Abitudini Disponibili

```bash
# Tutte le abitudini (46 totali: 26 positive + 20 negative)
python lgai.py habits

# Solo positive
python lgai.py habits --tipo positive

# Solo negative
python lgai.py habits --tipo negative

# Per area specifica
python lgai.py habits --area "Salute Fisica"
```

### Passo 2: Checkout con Abitudini Specifiche

**Sintassi:**
```bash
python lgai.py checkout \
  --habits-positive "ID1,ID2,ID3" \
  --habits-negative "ID101,ID102" \
  --note "Nota opzionale"
```

**Esempio Reale:**
```bash
# Giornata con workout, meditazione, lettura - ma anche junk food
python lgai.py checkout \
  --habits-positive "1,6,13" \
  --habits-negative "101" \
  --note "Buona giornata ma ceduto al junk food"
```

**Perfect Day (0 negative):**
```bash
# 5 abitudini positive, 0 negative = BONUS +20 PV!
python lgai.py checkout \
  --habits-positive "1,4,5,6,13" \
  --note "PERFECT DAY!"
```

### Passo 3: Il Sistema Calcola Automaticamente

Il checkout dettagliato mostra:
- ✅ Lista abitudini positive con icone e PV
- ❌ Lista abitudini negative con impatto
- 💰 Calcolo PV dettagliato
- 🌟 Bonus Perfect Day (+20 PV se 0 negative e ≥70 PV positive)
- 💬 Messaggio personalizzato di Raffaello

---

## 📊 CATALOGO ABITUDINI

### Abitudini Positive (26 totali)

**Salute Fisica (5)**
- `1` 💪 Workout/Palestra (+15 PV)
- `2` 🏃 Corsa/Cardio (+15 PV)
- `3` 🚶 Camminata 10k passi (+10 PV)
- `4` 🥗 Cibo Sano (+10 PV)
- `5` 😴 Sonno 7+ ore (+15 PV)

**Salute Mentale (4)**
- `6` 🧘 Meditazione (+15 PV)
- `7` 📝 Journaling (+10 PV)
- `8` 🧠 Terapia/Coaching (+20 PV)
- `9` 🌳 Tempo Natura (+10 PV)

**Relazioni (3)**
- `10` 👨‍👩‍👧 Chiamata Famiglia (+10 PV)
- `11` 💑 Tempo Qualità Partner (+15 PV)
- `12` 👥 Socializzazione (+10 PV)

**Crescita (4)**
- `13` 📚 Lettura 30min (+10 PV)
- `14` 🎓 Corso Online (+15 PV)
- `15` 🎧 Podcast Educativo (+8 PV)
- `16` 🎯 Nuova Skill (+15 PV)

**Creatività (2)**
- `17` 🎨 Progetto Creativo (+15 PV)
- `18` ✍️ Scrittura Creativa (+10 PV)

**Finanze (2)**
- `19` 💰 Budget Review (+10 PV)
- `20` 💵 Side Income Work (+15 PV)

**Contributo (2)**
- `21` 🤝 Aiuto agli Altri (+15 PV)
- `22` 📢 Contenuto Pubblicato (+10 PV)

**Spirituale (2)**
- `23` 🙏 Pratica Spirituale (+15 PV)
- `24` ✨ Gratitudine (+10 PV)

**Carriera (2)**
- `25` 🚀 Deep Work 2h (+20 PV)
- `26` 🌐 Networking (+10 PV)

### Abitudini Negative (20 totali)

**Salute Fisica (4)**
- `101` 🍔 Junk Food (-15 PV)
- `102` 🚬 Fumo/Alcol Eccessivo (-20 PV)
- `103` 🛋️ Sedentarietà (-10 PV)
- `104` 😵 Sonno <5 ore (-15 PV)

**Salute Mentale (4)**
- `105` 😰 Overthinking/Ansia (-10 PV)
- `106` 😔 Auto-Critica Eccessiva (-10 PV)
- `107` 🙈 Evitare Emozioni (-8 PV)
- `108` 📰 Notizie Negative Binge (-8 PV)

**Relazioni (3)**
- `109` ⚡ Conflitto non Risolto (-15 PV)
- `110` 🚪 Isolamento (-10 PV)
- `111` 😒 Comunicazione Passivo-Aggressiva (-8 PV)

**Crescita (2)**
- `112` ⏰ Procrastinazione (-15 PV)
- `113` 📺 Contenuto Passivo (-8 PV)

**Creatività (1)**
- `114` 🚫 Blocco Creativo (-10 PV)

**Finanze (2)**
- `115` 💸 Spesa Impulsiva (-15 PV)
- `116` 🙈 Ignorare Budget (-10 PV)

**Contributo (1)**
- `117` 🚫 Egoismo/Indifferenza (-10 PV)

**Spirituale (1)**
- `118` ☁️ Negatività/Cinismo (-10 PV)

**Carriera (2)**
- `119` 📱 Distrazioni Lavoro (-15 PV)
- `120` 🔥 Burnout Push (-20 PV)

---

## 🔥 MODALITÀ SEMPLICE (Ancora Disponibile)

Se preferisci il metodo veloce, puoi ancora usare:

```bash
# Conta solo i numeri
python lgai.py checkout 7 2 --note "7 positive, 2 negative"
```

---

## 💡 VANTAGGI MODALITÀ DETTAGLIATA

✅ **Precisione**: Sai ESATTAMENTE cosa hai fatto
✅ **Pattern**: Raffaello può analizzare quali abitudini ripeti
✅ **Motivazione**: Vedere la lista delle tue vittorie è più potente
✅ **Calcolo Giusto**: PV basati sull'impatto reale di ogni abitudine
✅ **Perfect Day Bonus**: +20 PV per giorni senza negative (≥70 PV positive)

---

## 📝 WORKFLOW CONSIGLIATO

### Mattina
```bash
python lgai.py checkin 8 8 --note "Giorno #X"
```

### Durante il Giorno
- Prendi nota mentalmente delle abitudini che completi
- Usa la lista: `python lgai.py habits --tipo positive`

### Sera
```bash
# Rivedi la giornata e inserisci gli ID
python lgai.py checkout \
  --habits-positive "1,4,6,13,23" \
  --habits-negative "101,119" \
  --note "Riflessione giornata"
```

---

## 🎯 ESEMPI PRATICI

### Giornata Produttiva
```bash
python lgai.py checkout \
  --habits-positive "1,6,13,25,19" \
  --note "Workout + Deep Work + Finanze"
# Output: +75 PV
```

### Perfect Day
```bash
python lgai.py checkout \
  --habits-positive "1,4,5,6,7,13,23" \
  --note "PERFECT DAY - 0 negative!"
# Output: +90 PV + 20 BONUS = +110 PV totali!
```

### Giornata Difficile
```bash
python lgai.py checkout \
  --habits-positive "4,13" \
  --habits-negative "101,105,112,119" \
  --note "Giornata di lotta"
# Output: +20 PV, -48 PV = -28 PV (ma almeno hai tracciato!)
```

---

## ⚡ TIPS

1. **Inizia piano**: Usa 3-5 abitudini per iniziare
2. **Sii onesto**: Il sistema funziona solo se sei sincero
3. **Celebra Perfect Days**: Sono rari, meritano ricompense!
4. **Usa note**: Aggiungi contesto per analisi futura
5. **Combina modi**: Semplice per giorni caotici, dettagliato quando puoi

---

🔴🔴🔴 **Il tracciamento dettagliato trasforma i dati in saggezza** 🔴🔴🔴
