#!/bin/bash
#
# 🎮 LGAI SISTEMA COMPLETO - DEMO INTERATTIVA
# Mostra tutte le funzionalità: status, habits, checkin, checkout, modalità interattiva
#

# Colori per output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
RED='\033[0;31m'
BOLD='\033[1m'
NC='\033[0m' # No Color

# Directory
DEMO_DIR="/home/user/Claudio/cli"
cd "$DEMO_DIR" || exit 1

# Funzione per pause con messaggio
pause() {
    echo ""
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${YELLOW}$1${NC}"
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    read -p "Premi INVIO per continuare..."
    echo ""
}

# Banner iniziale
clear
echo -e "${BOLD}${BLUE}"
cat << "EOF"
╔═══════════════════════════════════════════════════════════════╗
║                                                               ║
║     🎮  LGAI - LIFE GAME AI SISTEMA COMPLETO  🎮             ║
║                                                               ║
║            DEMO INTERATTIVA - Tutte le Funzionalità          ║
║                                                               ║
╚═══════════════════════════════════════════════════════════════╝
EOF
echo -e "${NC}"
echo ""
echo -e "${GREEN}Questa demo ti mostrerà:${NC}"
echo "  1. 📊 Status del player"
echo "  2. 📋 Catalogo abitudini (46 totali)"
echo "  3. 🌅 Check-in mattutino"
echo "  4. 💬 Modalità interattiva con Raffaello"
echo "  5. 🌙 Checkout serale dettagliato"
echo "  6. 🔮 Predizioni quantiche"
echo "  7. 💰 Baros Shop"
echo ""
pause "Iniziamo il tour completo!"

# ============================================================
# STEP 1: STATUS INIZIALE
# ============================================================
echo -e "${BOLD}${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${BOLD}${BLUE}   STEP 1: STATUS INIZIALE DEL PLAYER${NC}"
echo -e "${BOLD}${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo ""
python lgai.py status
pause "📊 Hai visto il tuo stato completo: PV, Zona, Livelli, Baros, Progresso Stagione"

# ============================================================
# STEP 2: CATALOGO ABITUDINI
# ============================================================
echo -e "${BOLD}${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${BOLD}${BLUE}   STEP 2: CATALOGO ABITUDINI (46 Tracciabili)${NC}"
echo -e "${BOLD}${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo ""
echo -e "${GREEN}Comando:${NC} python lgai.py habits"
echo ""
python lgai.py habits
pause "📋 Hai visto tutte le 46 abitudini: 26 positive + 20 negative"

# ============================================================
# STEP 3: ABITUDINI PER AREA
# ============================================================
echo -e "${BOLD}${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${BOLD}${BLUE}   STEP 3: ABITUDINI PER AREA SPECIFICA${NC}"
echo -e "${BOLD}${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo ""
echo -e "${GREEN}Comando:${NC} python lgai.py habits --area \"Salute Fisica\""
echo ""
python lgai.py habits --area "Salute Fisica"
pause "🎯 Filtro per area: solo abitudini di Salute Fisica"

# ============================================================
# STEP 4: CHECK-IN STANDARD
# ============================================================
echo -e "${BOLD}${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${BOLD}${BLUE}   STEP 4: CHECK-IN MATTUTINO (Standard)${NC}"
echo -e "${BOLD}${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo ""
echo -e "${GREEN}Comando:${NC} python lgai.py checkin 8 7 --note \"Demo LGAI\""
echo ""
python lgai.py checkin 8 7 --note "Demo LGAI"
pause "🌅 Check-in completato! Raffaello ha analizzato e generato 3 missioni"

# ============================================================
# STEP 5: CHECK-IN INTERATTIVO (SIMULATO)
# ============================================================
echo -e "${BOLD}${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${BOLD}${BLUE}   STEP 5: CHECK-IN INTERATTIVO - Chat con Raffaello${NC}"
echo -e "${BOLD}${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo ""
echo -e "${YELLOW}Per provare veramente la modalità interattiva, esegui:${NC}"
echo -e "${GREEN}  python lgai.py checkin 8 7 -i${NC}"
echo ""
echo -e "${CYAN}Nella chat potrai:${NC}"
echo "  • Digitare 'status' → Vedere PV, zona, Baros"
echo "  • Digitare 'habits' → Ricevere suggerimenti"
echo "  • Fare domande → Raffaello risponde!"
echo "  • Digitare 'continua' → Uscire"
echo ""
echo -e "${YELLOW}Ora simuliamo alcuni comandi...${NC}"
echo ""

# Simula interattività
echo -e "${GREEN}Comando simulato:${NC} echo 'status\nhabits\ncontinua' | python lgai.py checkin 8 8 -i"
echo ""
echo "status" | python lgai.py checkin 8 8 -i --note "Demo interattiva simulata" 2>/dev/null | head -30
pause "💬 Modalità interattiva attivata! (simulazione parziale)"

# ============================================================
# STEP 6: CATALOGO MISSIONI
# ============================================================
echo -e "${BOLD}${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${BOLD}${BLUE}   STEP 6: CATALOGO MISSIONI COMPLETE (45 totali)${NC}"
echo -e "${BOLD}${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo ""
echo -e "${GREEN}Comando:${NC} python lgai.py missioni --difficolta breakthrough"
echo ""
python lgai.py missioni --difficolta breakthrough
pause "🎯 45 missioni in 9 categorie, 4 livelli di difficoltà"

# ============================================================
# STEP 7: CHECKOUT DETTAGLIATO
# ============================================================
echo -e "${BOLD}${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${BOLD}${BLUE}   STEP 7: CHECKOUT DETTAGLIATO - Traccia Abitudini Specifiche${NC}"
echo -e "${BOLD}${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo ""
echo -e "${YELLOW}Scenario:${NC} Oggi hai fatto:"
echo "  ✅ Workout (ID: 1)"
echo "  ✅ Meditazione (ID: 6)"
echo "  ✅ Lettura (ID: 13)"
echo "  ✅ Cibo Sano (ID: 4)"
echo "  ❌ Junk Food (ID: 101)"
echo ""
echo -e "${GREEN}Comando:${NC} python lgai.py checkout --habits-positive \"1,6,13,4\" --habits-negative \"101\""
echo ""
python lgai.py checkout --habits-positive "1,6,13,4" --habits-negative "101" --note "Demo checkout dettagliato"
pause "🌙 Checkout dettagliato! Impatto preciso: +50 PV (positive) -15 PV (negative) = +35 PV"

# ============================================================
# STEP 8: PERFECT DAY DEMO
# ============================================================
echo -e "${BOLD}${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${BOLD}${BLUE}   STEP 8: PERFECT DAY - Bonus +20 PV${NC}"
echo -e "${BOLD}${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo ""
echo -e "${YELLOW}Scenario Perfect Day:${NC} 5 abitudini positive, 0 negative"
echo "  ✅ Workout (ID: 1) +15 PV"
echo "  ✅ Cibo Sano (ID: 4) +10 PV"
echo "  ✅ Sonno 7h (ID: 5) +15 PV"
echo "  ✅ Meditazione (ID: 6) +15 PV"
echo "  ✅ Lettura (ID: 13) +10 PV"
echo "  ❌ Nessuna negativa = 🌟 BONUS +20 PV!"
echo ""
echo -e "${GREEN}Comando:${NC} python lgai.py checkout --habits-positive \"1,4,5,6,13\" --note \"PERFECT DAY\""
echo ""
python lgai.py checkout --habits-positive "1,4,5,6,13" --note "PERFECT DAY TEST"
pause "🌟 PERFECT DAY! +70 PV + 20 BONUS = +90 PV TOTALI!"

# ============================================================
# STEP 9: PREDIZIONI QUANTICHE
# ============================================================
echo -e "${BOLD}${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${BOLD}${BLUE}   STEP 9: PREDIZIONI QUANTICHE${NC}"
echo -e "${BOLD}${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo ""
echo -e "${GREEN}Comando:${NC} python lgai.py predict"
echo ""
python lgai.py predict
pause "🔮 Predizioni: Risk Score, Growth Predictions, Breakthrough Windows"

# ============================================================
# STEP 10: BAROS SHOP
# ============================================================
echo -e "${BOLD}${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${BOLD}${BLUE}   STEP 10: BAROS SHOP - 50 Ricompense${NC}"
echo -e "${BOLD}${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo ""
echo -e "${GREEN}Comando:${NC} python lgai.py shop"
echo ""
python lgai.py shop
pause "💰 Shop con 50 ricompense in 7 categorie (Cibo, Tech, Viaggi, etc.)"

# ============================================================
# STEP 11: STATUS FINALE
# ============================================================
echo -e "${BOLD}${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${BOLD}${BLUE}   STEP 11: STATUS FINALE${NC}"
echo -e "${BOLD}${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo ""
python lgai.py status
pause "📊 Confronta con lo status iniziale: hai completato la demo!"

# ============================================================
# RIEPILOGO FINALE
# ============================================================
clear
echo -e "${BOLD}${GREEN}"
cat << "EOF"
╔═══════════════════════════════════════════════════════════════╗
║                                                               ║
║              ✅  DEMO COMPLETATA CON SUCCESSO!  ✅            ║
║                                                               ║
╚═══════════════════════════════════════════════════════════════╝
EOF
echo -e "${NC}"
echo ""
echo -e "${BOLD}${CYAN}🎮 HAI VISTO IL SISTEMA COMPLETO LGAI:${NC}"
echo ""
echo -e "${GREEN}✅ Funzionalità Core:${NC}"
echo "   • Status: PV, Zona, Livelli, Baros, Stagione"
echo "   • Check-in/Checkout: Workflow giornaliero"
echo "   • Raffaello: AI companion con analisi"
echo "   • Missioni: 45 missioni in 9 categorie"
echo ""
echo -e "${GREEN}✅ Tracciamento Abitudini:${NC}"
echo "   • 46 abitudini tracciabili (26 positive + 20 negative)"
echo "   • Dual mode: semplice o dettagliato"
echo "   • Perfect Day Bonus: +20 PV"
echo "   • Filtri per tipo e area"
echo ""
echo -e "${GREEN}✅ Modalità Interattiva:${NC}"
echo "   • Chat real-time con Raffaello"
echo "   • Comandi: status, habits, help"
echo "   • Context-aware (checkin/checkout)"
echo ""
echo -e "${GREEN}✅ Funzionalità Avanzate:${NC}"
echo "   • Predizioni Quantiche (Risk, Growth, Breakthrough)"
echo "   • Baros Shop: 50 ricompense"
echo "   • 9 Aree di vita"
echo "   • Sistema Stagioni (90 giorni)"
echo ""
echo -e "${BOLD}${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo -e "${CYAN}📚 DOCUMENTAZIONE COMPLETA:${NC}"
echo "   • README.md           → Overview sistema"
echo "   • COME_GIOCARE.md     → Guida player completa"
echo "   • HABIT_TRACKING.md   → Sistema abitudini dettagliato"
echo "   • INTERACTIVE_MODE.md → Modalità interattiva"
echo "   • NOTION_FORMULAS.md  → Integrazione Notion"
echo ""
echo -e "${BOLD}${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo -e "${CYAN}🚀 PROSSIMI PASSI:${NC}"
echo ""
echo -e "${BOLD}1. Prova la Modalità Interattiva VERA:${NC}"
echo "   ${GREEN}python lgai.py checkin 8 7 -i${NC}"
echo "   (Fai domande vere a Raffaello, digita 'continua' per uscire)"
echo ""
echo -e "${BOLD}2. Fai il Tuo Primo Giorno Completo:${NC}"
echo "   ${GREEN}# Mattina${NC}"
echo "   python lgai.py checkin [mood] [energia] -i"
echo ""
echo "   ${GREEN}# Sera${NC}"
echo "   python lgai.py checkout -i"
echo "   python lgai.py checkout --habits-positive \"1,6,13\" --habits-negative \"101\""
echo ""
echo -e "${BOLD}3. Esplora i Comandi:${NC}"
echo "   ${GREEN}python lgai.py --help${NC}           # Lista tutti i comandi"
echo "   ${GREEN}python lgai.py habits --tipo positive${NC}  # Solo abitudini positive"
echo "   ${GREEN}python lgai.py predict${NC}          # Predizioni quantiche"
echo "   ${GREEN}python lgai.py shop${NC}             # Baros Shop"
echo "   ${GREEN}python lgai.py talk \"Come sto?\"${NC}  # Parla con Raffaello"
echo ""
echo -e "${BOLD}${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo -e "${BOLD}${GREEN}🎯 IL TUO VIAGGIO DI TRASFORMAZIONE INIZIA ORA!${NC}"
echo ""
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
