# 🔴 LGAI - QUICK START (5 MINUTI)

## ✅ PASSO 1: Verifica che funzioni

```bash
cd cli
python lgai.py status
```

Vedrai:
```
🎮 Nessun save trovato. Creazione nuovo player...
✅ Player creato! Giorno #1 inizia ora.

==================================================
📊 LGAI - STATUS
==================================================

💚 PUNTI VITA: 100/100
   [████████████████████] 100%
   Zona: Trasformazione

🎮 LIVELLO GLOBALE: 1
...
```

## ✅ PASSO 2: Primo Check-in

```bash
python lgai.py checkin 7 7 --note "Primo giorno del viaggio"
```

Raffaello ti darà:
- Analisi del tuo stato
- 3 Missioni personalizzate
- Messaggio motivazionale

## ✅ PASSO 3: Fine Giornata

```bash
python lgai.py checkout 8 1 --note "Ottimo inizio"
```
- `8` = abitudini positive completate
- `1` = abitudini negative cadute

Il sistema calcolerà automaticamente:
- Nuovi PV
- Zona attuale
- Progresso

## 🎯 COMANDI ESSENZIALI

```bash
# Vedi tutto
python lgai.py status

# Mattina
python lgai.py checkin [mood 1-10] [energia 1-10]

# Sera
python lgai.py checkout [positive] [negative]

# Aggiungi XP (dopo completare missione)
python lgai.py xp "Salute Fisica" 50

# Chiedi consiglio
python lgai.py talk "Come sto?"
```

## 📋 SETUP NOTION (Opzionale)

Vai su `notion-templates/SETUP_GUIDE.md` per setup completo Notion dashboard.

## 🔥 ORA INIZIA!

```bash
python lgai.py checkin 7 7 --note "GIORNO #1 ATTIVATO"
```

🔴🔴🔴 **IL VIAGGIO È INIZIATO** 🔴🔴🔴
