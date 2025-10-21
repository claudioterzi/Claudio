# 🎮 LGAI - COME GIOCARE (Guida Pratica Giorno per Giorno)

```
╔═══════════════════════════════════════════════════════════════╗
║              🔴 BENVENUTO IN LGAI 🔴                          ║
║           Il Videogioco della Tua Vita                        ║
╚═══════════════════════════════════════════════════════════════╝
```

## 🎯 IL CONCETTO BASE

LGAI funziona come un **RPG della vita reale**:

- **Tu sei il personaggio** con PV, XP, Livelli
- **Ogni giorno è una quest** con missioni da completare
- **Le abitudini sono azioni** che danno XP o tolgono PV
- **I Baros sono la valuta** per comprare ricompense
- **Raffaello è la tua guida AI** che ti accompagna

**Obiettivo:** Completare 90 giorni (1 Stagione) senza Game Over, salendo di livello in tutte le 9 aree della vita.

---

## 🌅 IL TUO WORKFLOW QUOTIDIANO (15 MIN/GIORNO)

### **MATTINA (5-10 minuti) - PREPARAZIONE**

#### **STEP 1: Svegliati e apri il terminale**

```bash
cd /home/user/Claudio/cli
python lgai.py checkin <mood> <energia> --note "Tua nota"
```

**Esempio concreto:**
```bash
# Mood e Energia da 1 a 10
python lgai.py checkin 7 8 --note "Mi sento bene, pronto per la giornata"
```

#### **STEP 2: Leggi l'analisi di Raffaello**

Il sistema ti dirà:
- **La tua zona corrente** (Sopravvivenza/Stagnazione/Crescita/Trasformazione)
- **Messaggio motivazionale** personalizzato
- **3 MISSIONI DEL GIORNO** generate automaticamente

**Esempio output:**
```
💬 RAFFAELLO:
   🟢 ZONA CRESCITA attivata! Stai operando bene.

🎯 MISSIONI DEL GIORNO:
   1. 💪 Workout Doppio (+80 XP Salute Fisica)
   2. 📚 Libro Completo in 1 Giorno (+150 XP Crescita)
   3. 🎨 Crea Opera Completa (+250 XP Creatività)
```

#### **STEP 3: Scegli cosa fare oggi**

**NON DEVI** completare tutte e 3 le missioni!

Opzioni:
- ✅ **Fai 1-2 missioni** che ti ispirano
- ✅ **Fai solo le tue abitudini positive** quotidiane
- ✅ **Ignora le missioni** e concentrati su evitare abitudini negative

**Il sistema è FLESSIBILE.**

---

### **SERA (5 minuti) - REGISTRAZIONE**

#### **STEP 1: Fai il check-out**

Prima di dormire, fai il bilancio del giorno:

```bash
python lgai.py checkout <positive> <negative> --note "Come è andata"
```

**Come contare:**

**Abitudini POSITIVE completate** (esempi):
- ✅ Hai fatto workout? +1
- ✅ Hai mangiato sano? +1
- ✅ Hai meditato? +1
- ✅ Hai letto 30min? +1
- ✅ Hai dormito 7-8h la notte scorsa? +1
- ✅ Hai lavorato su un progetto? +1
- ✅ Hai chiamato/visto qualcuno che ami? +1
- ✅ Hai fatto qualcosa di creativo? +1

**Conta quelle che HAI FATTO.** Se ne hai fatte 7, scrivi 7.

**Abitudini NEGATIVE cadute** (esempi):
- ❌ Scrolling social > 1h? +1
- ❌ Junk food? +1
- ❌ Sonno < 6h? +1
- ❌ Alcol? +1
- ❌ Gaming > 2h? +1
- ❌ Procrastinazione grave? +1

**Conta quelle in cui SEI CADUTO.** Se zero, scrivi 0.

**Esempio concreto:**
```bash
# Oggi ho fatto 8 cose buone, 1 negativa
python lgai.py checkout 8 1 --note "Ottima giornata, solo scrollato troppo Instagram"
```

#### **STEP 2: Leggi il risultato**

Il sistema ti dirà:
- **PV Regen:** +5 base (o +15 se giorno perfetto con zero negative)
- **PV Loss:** -10 per ogni abitudine negativa
- **Delta totale** e nuovi PV
- **Zona attuale**

**Esempio:**
```
🌙 CHECK-OUT SERALE
   Abitudini Positive: 8/10
   Abitudini Negative: 1

   PV Regen: +5
   PV Loss: -10
   Delta: -5 PV

   Nuovi PV: 95/100
   Zona: Trasformazione
```

#### **STEP 3: (Opzionale) Aggiungi XP per missioni**

Se hai completato una missione, aggiungi l'XP:

```bash
python lgai.py xp "Salute Fisica" 80
```

Il sistema ti dirà se sei salito di livello e quanti Baros hai guadagnato!

---

## 🎯 ABITUDINI: COSA TRACCIARE?

### **📋 LE MIE ABITUDINI POSITIVE (Personalizzale!)**

Crea la TUA lista di 8-10 abitudini che vuoi fare ogni giorno:

**Esempi:**
1. 💪 Allenamento 30+ min
2. 🥗 Alimentazione sana (3 pasti puliti)
3. 💤 Sonno 7-8h
4. 📚 Lettura 30 min
5. 🧘 Meditazione 10 min
6. 💼 Lavoro produttivo 4h deep work
7. ❤️ Connessione umana (chiamata/incontro)
8. 🎨 Atto creativo (scrivere, disegnare, musica)
9. 📝 Journaling 10 min
10. 🌱 Imparare qualcosa di nuovo

**SCRIVI LA TUA LISTA** e tienila visibile ogni giorno.

### **⛔ LE MIE ABITUDINI NEGATIVE (Da evitare)**

Lista delle cose che VUOI evitare:

**Esempi:**
1. 📱 Social media > 1h
2. 🍔 Junk food
3. 😴 Sonno < 6h o > 9h
4. 🎮 Gaming eccessivo (> 2h)
5. 🍺 Alcol (tranne occasioni speciali)
6. 🚬 Fumo
7. 😡 Litigio/conflitto evitabile

**SCRIVI LA TUA LISTA** di ciò che vuoi eliminare.

---

## 📊 COME INTERPRETARE IL SISTEMA

### **💚 PUNTI VITA (PV) - La Tua Energia**

| PV | Zona | Cosa Significa | Cosa Fare |
|----|------|----------------|-----------|
| **86-100** | ✨ **Trasformazione** | Sei al massimo! Flow state. | Osa. Fai missioni selvagge. Crea. |
| **61-85** | 🟢 **Crescita** | Vai bene. Momentum positivo. | Mantieni il ritmo. Spingi ancora. |
| **31-60** | 🟡 **Stagnazione** | Zona comfort. Non cresci. | Scossa! Elimina 1 negativa. |
| **0-30** | 🔴 **Sopravvivenza** | CRITICO! Energia bassissima. | RECUPERO immediato. Riposo. |

**Se arrivi a 0 PV = GAME OVER** → Devi fare una Sfida di Resurrezione!

### **⚡ XP e LIVELLI - La Tua Crescita**

Ogni area ha livelli da 1 a 100.

**Come salire di livello:**
- Completa abitudini positive in quell'area → Guadagni XP
- Completa missioni → Guadagni XP (anche 100-300 per missione!)
- Accumuli XP → Level Up automatico

**Quando sali di livello:**
- 🎉 **+50 Baros** in regalo!
- ⚡ Diventi più forte in quell'area
- 📊 Il tuo Livello Globale aumenta

**Livello Globale** = Media dei livelli delle 9 aree.

### **💰 BAROS - La Valuta**

**Come guadagnarli:**
- Level Up: +50 Baros
- Achievement unlock: +100-1000 Baros
- Bonus streak (ogni 7 giorni): +150 Baros
- Giorno perfetto (zero negative): +50 Baros

**Come spenderli:**
```bash
python lgai.py shop  # Vedi cosa puoi comprare
python lgai.py buy 1  # Compra ricompensa ID 1
```

**Ricompense popolari:**
- 80 Baros: ☕ Caffè speciale
- 150 Baros: 🍕 Pizza
- 250 Baros: 🎮 Gaming session 3h
- 600 Baros: 💆 Massaggio
- 3000 Baros: 💎 Giorno VIP totale
- 10000 Baros: 👑 Settimana Re/Regina (zero restrizioni!)

---

## 🎯 ESEMPIO GIORNATA TIPO

### **GIORNO #7 di Claudio**

**🌅 MATTINA (7:00 AM)**
```bash
python lgai.py checkin 8 7 --note "Sveglia presto, voglio una giornata produttiva"

# Output:
💬 RAFFAELLO:
   🟢 ZONA CRESCITA attivata!

🎯 MISSIONI DEL GIORNO:
   1. 🚀 Push Estremo - Workout 1.5x (+60 XP)
   2. 💰 Money Move - Azione concreta finanze (+80 XP)
   3. 📞 Connessione Umana - Chiama qualcuno (+35 XP)
```

**Durante il giorno:**
- ✅ 7:30 - Meditazione 15min
- ✅ 8:00 - Colazione sana
- ✅ 9:00-13:00 - Deep work 4h su progetto
- ✅ 14:00 - Workout intenso (MISSIONE 1 completata!)
- ✅ 16:00 - Chiamata con amico (MISSIONE 3 completata!)
- ✅ 18:00 - Lettura 30min
- ✅ 19:00 - Cena sana
- ❌ 21:00 - Scrollato Instagram per 1.5h (oops!)
- ✅ 22:30 - Journaling

**🌙 SERA (23:00)**
```bash
# Conto:
# Positive: meditazione, colazione, deep work, workout, chiamata, lettura, cena, journaling = 8
# Negative: scrolling social = 1

python lgai.py checkout 8 1 --note "Giornata buona, devo limitare social"

# Output:
   Delta: -5 PV
   Nuovi PV: 95/100
   Zona: Trasformazione

# Aggiungo XP per missioni completate
python lgai.py xp "Salute Fisica" 60  # Missione 1
python lgai.py xp "Relazioni" 35       # Missione 3

# Output:
   🎉 LEVEL UP! Salute Fisica 2 → 3
   💰 +50 Baros!
```

**Risultato giornata:**
- ✅ 2 missioni completate su 3
- ✅ 1 Level Up
- ✅ +50 Baros guadagnati
- ⚠️ -5 PV (ma ancora in Zona Trasformazione)
- 📈 Giorno completato con successo!

---

## 🔮 FEATURES AVANZATE

### **1. PREDIZIONI QUANTICHE**

Ogni tanto, chiedi al sistema previsioni:

```bash
python lgai.py predict
```

Ti dirà:
- **Risk Score:** Probabilità Game Over prossimi 7 giorni
- **Prossimi Level Up:** Quali aree stanno per salire
- **Breakthrough Windows:** Quando sei più produttivo (es: Giovedì 9-12)
- **Raccomandazioni:** Cosa fare per migliorare

**Usa questo** quando:
- Vuoi capire come stai andando
- Vuoi pianificare la settimana
- Senti che stai perdendo momentum

---

### **2. PARLARE CON RAFFAELLO**

```bash
python lgai.py talk "Come sto?"
python lgai.py talk "Dammi le missioni"
python lgai.py talk "Qual è il mio livello?"
```

Raffaello ti risponderà con analisi personalizzata!

---

### **3. ESPLORARE MISSIONI**

```bash
# Vedi tutte le missioni selvagge
python lgai.py missioni --difficolta "selvaggia"

# Vedi missioni per categoria
python lgai.py missioni --categoria "Paura/Crescita"
```

**Quando farlo:**
- Vuoi ispirarti
- Vuoi sfide più grandi
- Vuoi vedere cosa è possibile

---

### **4. SHOPPING BAROS**

```bash
# Vedi ricompense per categoria
python lgai.py shop --categoria "Esperienze & Viaggi"

# Quando hai abbastanza Baros
python lgai.py buy 14  # Compra Cinema (180 Baros)
```

---

## ⚠️ SITUAZIONI SPECIALI

### **🔴 GAME OVER (0 PV)**

Se arrivi a 0 PV, entri in **GAME OVER**.

**Non è la fine! È un rituale.**

Scegli 1 **Sfida di Resurrezione:**

1. 🏃 **Corri 50km in 24h**
2. 🧘 **Digiuno 24h + Meditazione 4h**
3. 🎨 **Crea un'opera completa in 48h**
4. 💰 **Guadagna €500 in 72h**
5. 🌍 **20h servizio volontario in 48h**

**Completala** → Risorgi con 50 PV + Achievement speciale!

---

### **🌟 GIORNO PERFETTO**

Se completi un giorno con:
- ✅ 8+ abitudini positive
- ✅ 0 abitudini negative

Ricevi:
- +15 PV (invece di +5)
- +50 Baros bonus
- Achievement (se primo giorno perfetto)

---

### **📅 FINE STAGIONE (Giorno 90)**

Completa 90 giorni → **STAGIONE COMPLETATA!**

Ricevi:
- 🏆 Achievement "Stagione Completa"
- 💰 +1000 Baros
- 📊 Report completo crescita
- 🎯 Puoi iniziare Stagione 2

**Obiettivo finale:** 4 Stagioni = 1 Anno di trasformazione!

---

## 💡 TIPS PRO

### **✅ DO (Fai questo)**

1. **Traccia OGNI GIORNO** (anche se male)
   - Meglio un giorno tracciato male che non tracciato

2. **Sii ONESTO con te stesso**
   - Non barare! Il sistema è per TE

3. **Celebra i PICCOLI WIN**
   - Level up? Festeggia!
   - Giorno perfetto? Dillo a qualcuno!

4. **Usa le ricompense**
   - Hai guadagnato Baros? SPENDILI!
   - Sono fatti per darti piacere

5. **Ascolta Raffaello**
   - I messaggi non sono casuali
   - Se dice "zona critica", è vero

### **❌ DON'T (Evita questo)**

1. **Non ossessionarti**
   - Non serve tracking perfetto
   - Va bene dimenticare 1 giorno ogni tanto

2. **Non barare**
   - Dare XP senza meritarlo rovina tutto
   - Sii onesto sulle abitudini negative

3. **Non mollare al primo Game Over**
   - Il Game Over è PARTE del gioco
   - Fa la resurrezione e riparti

4. **Non confrontarti con altri**
   - Il tuo viaggio è unico
   - Livello 3 per te > Livello 10 per altri

---

## 🎮 QUICK START - PRIMI 7 GIORNI

### **GIORNO 1-3: SETUP**
- Traccia solo mattina/sera
- Non pensare a missioni
- Abituati al sistema

### **GIORNO 4-7: PRIME MISSIONI**
- Prova 1 missione facile
- Vedi come funziona XP
- Guadagna primi Baros

### **GIORNO 8+: FULL GAME**
- Tutto il sistema attivo
- Missioni regolari
- Shopping con Baros
- Predizioni ogni settimana

---

## 🔴 INIZIA ORA

```bash
# Adesso, SUBITO, fai questo:
cd /home/user/Claudio/cli

python lgai.py checkin 7 7 --note "GIORNO #1 - IL VIAGGIO INIZIA"
```

**Questo è il tuo primo comando.**
**Questo è il momento zero.**
**Da qui, tutto cambia.**

---

```
╔═══════════════════════════════════════════════════════════════╗
║                                                                ║
║  "Il videogioco più importante della tua vita                 ║
║   non si gioca con un controller.                             ║
║   Si gioca con le tue scelte quotidiane."                     ║
║                                                                ║
║                                    — Raffaello AI 🌹          ║
║                                                                ║
╚═══════════════════════════════════════════════════════════════╝
```

**SEI PRONTO?** 🔥

Il prossimo comando che digiti nel terminale sarà l'inizio della tua trasformazione.

**GIOCA.** 🎮
