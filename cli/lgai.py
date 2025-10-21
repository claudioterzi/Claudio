#!/usr/bin/env python3
"""
LGAI CLI - Interfaccia a linea di comando per Life Game AI
Comandi rapidi per gestire il tuo sistema quotidiano
"""

import sys
import os

# Aggiungi parent directory al path per import
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from lgai_core.calculator import PlayerStats, Area, LGAICalculator
from lgai_core.raffaello import Raffaello
from lgai_core.data_manager import DataManager
from lgai_core.baros_shop import BarosShop, PurchaseHistory
from lgai_core.predictions import PredictionSystem
from lgai_core.missions_catalog import MissionsCatalog
from lgai_core.habits_catalog import HabitsCatalog
import argparse
from datetime import datetime


class LGAICLI:
    """CLI principale"""

    def __init__(self):
        self.dm = DataManager()
        self.calc = LGAICalculator()
        self.raffaello = Raffaello()
        self.shop = BarosShop()
        self.pred_system = PredictionSystem()
        self.purchase_history = PurchaseHistory()

        # Carica o crea player
        self.player = self.dm.load_player()
        if self.player is None:
            print("🎮 Nessun save trovato. Creazione nuovo player...")
            self.player = PlayerStats()
            self.dm.save_player(self.player)
            print("✅ Player creato! Giorno #1 inizia ora.\n")

    def status(self):
        """Mostra status corrente"""
        print("\n" + "="*50)
        print("📊 LGAI - STATUS")
        print("="*50)

        # PV e Zona
        zona = self.calc.get_zona(self.player.pv_current)
        pv_percent = int((self.player.pv_current / self.player.pv_max) * 100)
        pv_bar = "█" * (pv_percent // 5) + "░" * (20 - pv_percent // 5)

        print(f"\n💚 PUNTI VITA: {self.player.pv_current}/{self.player.pv_max}")
        print(f"   [{pv_bar}] {pv_percent}%")
        print(f"   Zona: {zona.value}")

        # Livello Globale
        liv_globale = self.calc.calcola_livello_globale(self.player)
        print(f"\n🎮 LIVELLO GLOBALE: {liv_globale}")

        # Livelli per area
        print(f"\n📈 LIVELLI PER AREA:")
        for area, livello in sorted(self.player.livelli_per_area.items(),
                                   key=lambda x: x[1], reverse=True):
            xp = self.player.xp_per_area[area]
            xp_needed = self.calc.calcola_xp_per_livello(livello)
            print(f"   {area.value:20s} Lv.{livello:3d} ({xp}/{xp_needed} XP)")

        # Baros
        print(f"\n💰 BAROS: {self.player.baros}")

        # Progresso Stagione
        progresso = self.calc.calcola_progresso_stagione(self.player.giorno)
        print(f"\n📅 STAGIONE {progresso['stagione']} - Giorno {progresso['giorno_in_stagione']}/90")
        print(f"   Progresso: {progresso['percentuale']}% | {progresso['giorni_rimanenti']} giorni rimanenti")

        print("\n" + "="*50 + "\n")

    def checkin(self, mood: int, energia: int, note: str = "", interactive: bool = False):
        """Check-in mattutino"""
        print("\n🌅 CHECK-IN MATTUTINO")
        print(f"   Mood: {mood}/10")
        print(f"   Energia: {energia}/10")
        if note:
            print(f"   Note: {note}")

        # Analisi Raffaello
        analisi = self.raffaello.analizza_giorno(self.player, 0, 0, note)

        print(f"\n💬 RAFFAELLO:")
        print(f"   {analisi.messaggio_motivazionale}")

        if analisi.warning:
            print(f"\n   {analisi.warning}")

        # Genera missioni
        print(f"\n🎯 MISSIONI DEL GIORNO:")
        missioni = self.raffaello.genera_missioni_giornaliere(self.player)
        for i, m in enumerate(missioni, 1):
            print(f"   {i}. {m['titolo']}")
            print(f"      {m['descrizione']}")
            print(f"      Reward: {m['xp']} XP ({m['area'].value})\n")

        # Modalità Interattiva
        if interactive:
            self._interactive_chat(context="checkin", mood=mood, energia=energia, missioni=missioni)

        # Salva log (converti Area enum in string)
        missioni_serializable = [
            {**m, 'area': m['area'].value} for m in missioni
        ]
        log = {
            'tipo': 'checkin',
            'mood': mood,
            'energia': energia,
            'note': note,
            'missioni': missioni_serializable
        }
        self.dm.save_daily_log(self.player.giorno, log)

        print("✅ Check-in salvato!\n")

    def checkout(self, abitudini_positive: int = None, abitudini_negative: int = None,
                 note: str = "", habits_positive: str = None, habits_negative: str = None,
                 interactive: bool = False):
        """Check-out serale - supporta sia conteggio semplice che tracking dettagliato"""
        print("\n🌙 CHECK-OUT SERALE")

        # Modalità Interattiva PRIMA del checkout (per decidere quali abitudini tracciare)
        if interactive:
            print("\n💡 Stai per fare il checkout. Vuoi chattare con Raffaello prima?")
            print("   Può aiutarti a riflettere sulla giornata e scegliere le abitudini.\n")
            self._interactive_chat(context="pre-checkout")

        # Determina se usiamo tracking dettagliato o semplice
        use_detailed = habits_positive is not None or habits_negative is not None

        if use_detailed:
            # MODALITÀ DETTAGLIATA - Usa HabitsCatalog
            positive_ids = [int(x.strip()) for x in habits_positive.split(',')] if habits_positive else []
            negative_ids = [int(x.strip()) for x in habits_negative.split(',')] if habits_negative else []

            # Calcola impatto PV
            impact = HabitsCatalog.calculate_pv_impact(positive_ids, negative_ids)

            print("\n📈 ABITUDINI POSITIVE COMPLETATE:")
            if positive_ids:
                for hid in positive_ids:
                    habit = HabitsCatalog.get_by_id(hid)
                    if habit:
                        print(f"   {habit.icona} {habit.nome} ({habit.pv_delta:+d} PV)")
            else:
                print("   Nessuna")

            print("\n📉 ABITUDINI NEGATIVE CADUTE:")
            if negative_ids:
                for hid in negative_ids:
                    habit = HabitsCatalog.get_by_id(hid)
                    if habit:
                        print(f"   {habit.icona} {habit.nome} ({habit.pv_delta} PV)")
            else:
                print("   Nessuna 🎉 PERFECT DAY!")

            pv_delta = impact['total_delta']
            print(f"\n💰 CALCOLO PV:")
            print(f"   Positive: +{impact['positive_delta']}")
            print(f"   Negative: {impact['negative_delta']}")
            if impact['bonus'] > 0:
                print(f"   🌟 BONUS PERFECT DAY: +{impact['bonus']}")
            print(f"   DELTA TOTALE: {pv_delta:+d} PV")

            # Salva dettagli abitudini nel log
            positive_habits_details = [
                {'id': hid, 'nome': HabitsCatalog.get_by_id(hid).nome}
                for hid in positive_ids if HabitsCatalog.get_by_id(hid)
            ]
            negative_habits_details = [
                {'id': hid, 'nome': HabitsCatalog.get_by_id(hid).nome}
                for hid in negative_ids if HabitsCatalog.get_by_id(hid)
            ]

        else:
            # MODALITÀ SEMPLICE - Conteggio base
            if abitudini_positive is None or abitudini_negative is None:
                print("❌ Devi fornire o i conteggi (positive negative) o gli ID (--habits-positive --habits-negative)")
                return

            pv_loss = abitudini_negative * 10
            pv_gain = self.calc.calcola_regen_giornaliera(self.player,
                                                          abitudini_positive, 10)
            pv_delta = pv_gain - pv_loss

            print(f"   Abitudini Positive: {abitudini_positive}/10")
            print(f"   Abitudini Negative: {abitudini_negative}")
            print(f"\n   PV Regen: +{pv_gain}")
            print(f"   PV Loss: -{pv_loss}")
            print(f"   Delta: {pv_delta:+d} PV")

            positive_habits_details = None
            negative_habits_details = None

        # Applica modifiche PV
        result = self.calc.modifica_pv(self.player, pv_delta, "Daily checkout")

        print(f"\n   Nuovi PV: {result['new_pv']}/{self.player.pv_max}")
        print(f"   Zona: {result['zona_after'].value}")

        if result['game_over']:
            print("\n   🔴🔴🔴 GAME OVER 🔴🔴🔴")
            print("   Attiva Sfida di Resurrezione!")

        # Messaggio Raffaello
        if use_detailed and positive_habits_details:
            print(f"\n💬 RAFFAELLO:")
            analisi = self.raffaello.analizza_giorno(self.player,
                                                     len(positive_habits_details),
                                                     len(negative_habits_details) if negative_habits_details else 0,
                                                     note)
            print(f"   {analisi.messaggio_motivazionale}")

        # Incrementa giorno
        self.player.giorno += 1

        # Salva
        self.dm.save_player(self.player)

        # Log con dettagli
        log = {
            'tipo': 'checkout',
            'pv_delta': pv_delta,
            'pv_final': result['new_pv'],
            'note': note
        }

        if use_detailed:
            log['abitudini_positive_dettagli'] = positive_habits_details
            log['abitudini_negative_dettagli'] = negative_habits_details
            log['abitudini_positive'] = len(positive_ids)
            log['abitudini_negative'] = len(negative_ids)
        else:
            log['abitudini_positive'] = abitudini_positive
            log['abitudini_negative'] = abitudini_negative

        self.dm.save_daily_log(self.player.giorno - 1, log)

        print("\n✅ Check-out salvato! Giorno completato.\n")

    def add_xp(self, area_name: str, xp: int):
        """Aggiungi XP a un'area"""
        try:
            area = Area(area_name)
        except ValueError:
            print(f"❌ Area non valida: {area_name}")
            print(f"   Aree disponibili: {[a.value for a in Area]}")
            return

        print(f"\n⚡ Aggiungo {xp} XP a {area.value}...")

        result = self.calc.aggiungi_xp(self.player, area, xp)

        if result['level_up']:
            print(f"\n   🎉 LEVEL UP! {result['new_level']-1} → {result['new_level']}")
            print(f"   💰 +{result['baros_earned']} Baros guadagnati!")

        print(f"   XP attuali: {self.player.xp_per_area[area]}")
        print(f"   XP per next level: {self.calc.calcola_xp_per_livello(self.player.livelli_per_area[area])}")

        self.dm.save_player(self.player)
        print("\n✅ Salvato!\n")

    def talk(self, domanda: str):
        """Parla con Raffaello"""
        print(f"\n💬 Tu: {domanda}\n")
        risposta = self.raffaello.parla_con_me(self.player, domanda)
        print(f"🌹 Raffaello: {risposta}\n")

    def shop_list(self, categoria: str = None):
        """Mostra ricompense shop"""
        print("\n💰 BAROS SHOP")
        print(f"   Baros Disponibili: {self.player.baros}\n")

        if categoria:
            rewards = self.shop.get_by_categoria(categoria)
            print(f"📦 Categoria: {categoria}\n")
        else:
            affordable = self.shop.get_affordable(self.player.baros)
            print(f"🛍️ Ricompense che puoi permetterti ({len(affordable)}):\n")
            rewards = affordable[:10]  # Solo prime 10

        for r in rewards:
            can_afford = "✅" if r.costo <= self.player.baros else "❌"
            print(f"{can_afford} {r.icona} {r.nome} - {r.costo} Baros")
            print(f"   {r.descrizione}")
            if r.restrizioni:
                print(f"   Restrizioni: {r.restrizioni}")
            print()

        if not categoria:
            print(f"💡 Usa 'shop --categoria \"Nome Categoria\"' per vedere tutte le ricompense\n")

    def shop_buy(self, reward_id: int):
        """Acquista ricompensa"""
        reward = self.shop.get_by_id(reward_id)

        if not reward:
            print("❌ Ricompensa non trovata!\n")
            return

        if reward.costo > self.player.baros:
            print(f"❌ Baros insufficienti!")
            print(f"   Ti servono: {reward.costo} Baros")
            print(f"   Hai: {self.player.baros} Baros")
            print(f"   Mancano: {reward.costo - self.player.baros} Baros\n")
            return

        # Check restrizioni
        now = datetime.now()
        can_buy = self.purchase_history.can_purchase(reward, now.month, now.year)

        if not can_buy:
            print(f"❌ Limite mensile raggiunto per questa ricompensa!")
            print(f"   Restrizione: {reward.restrizioni}\n")
            return

        # Acquista
        self.player.baros -= reward.costo
        self.purchase_history.add_purchase(reward_id, reward.costo)
        self.dm.save_player(self.player)

        print(f"\n🎉 ACQUISTO COMPLETATO!")
        print(f"   {reward.icona} {reward.nome}")
        print(f"   Costo: {reward.costo} Baros")
        print(f"   Baros rimasti: {self.player.baros}\n")
        print(f"✨ Goditi la tua ricompensa! ✨\n")

    def predictions(self):
        """Mostra predizioni avanzate"""
        print("\n🔮 PREDIZIONI QUANTICHE\n")

        # Carica history
        history = list(self.dm.load_history().values())

        # Risk Score
        print("1️⃣ RISK SCORE")
        risk = self.pred_system.calculate_risk_score(self.player, history)
        print(f"   Score: {risk.score}/100")
        print(f"   Livello: {risk.livello}")
        if risk.raccomandazioni:
            print(f"\n   📋 Raccomandazioni:")
            for r in risk.raccomandazioni[:3]:
                print(f"   - {r}")

        # Growth Predictions
        print(f"\n2️⃣ LEVEL UP PREDICTIONS (Top 5)")
        growth = self.pred_system.predict_level_ups(self.player, history)
        for g in growth[:5]:
            print(f"   {g.area.value:20s} Lv.{g.livello_attuale} → {g.livello_attuale+1}")
            print(f"   {' '*23}~{g.giorni_stimati} giorni ({g.probabilita}% probabilità)")

        # Breakthrough Windows
        print(f"\n3️⃣ BREAKTHROUGH WINDOWS (Prossimi 3 giorni)")
        windows = self.pred_system.find_breakthrough_windows(history, days_ahead=3)
        for w in windows[:3]:
            print(f"   {w.data.strftime('%A %d/%m')}: {w.ora_inizio}-{w.ora_fine}")
            print(f"   Energia: {w.energia_prevista}/10 | Prob: {w.probabilita_breakthrough}%")

        print("\n" + "="*50 + "\n")

    def missioni_catalog(self, categoria: str = None, difficolta: str = None):
        """Mostra catalogo missioni"""
        print("\n🎯 CATALOGO MISSIONI\n")

        if categoria:
            missions = MissionsCatalog.get_by_categoria(categoria)
            print(f"📦 Categoria: {categoria}\n")
        elif difficolta:
            missions = MissionsCatalog.get_by_difficolta(difficolta)
            print(f"⚡ Difficoltà: {difficolta.capitalize()}\n")
        else:
            missions = MissionsCatalog.get_all_missions()
            print(f"📚 TUTTE LE MISSIONI ({len(missions)} totali)\n")

        for i, m in enumerate(missions[:15], 1):  # Max 15
            print(f"{i}. {m.titolo}")
            print(f"   {m.descrizione}")
            print(f"   Reward: {m.xp_primaria} XP ({m.area_primaria.value}) + {m.baros} Baros")
            print(f"   Tipo: {m.tipo.capitalize()} | Difficoltà: {m.difficolta.capitalize()}")
            if m.restrizioni:
                print(f"   ⚠️  {m.restrizioni}")
            print()

        if len(missions) > 15:
            print(f"... e altre {len(missions) - 15} missioni!\n")

    def habits_list(self, tipo: str = None, area: str = None):
        """Mostra catalogo abitudini tracciabili"""
        print("\n📋 CATALOGO ABITUDINI\n")

        if tipo and tipo.lower() == "positive":
            habits = HabitsCatalog.get_all_positive()
            print("📈 ABITUDINI POSITIVE\n")
        elif tipo and tipo.lower() == "negative":
            habits = HabitsCatalog.get_all_negative()
            print("📉 ABITUDINI NEGATIVE\n")
        elif area:
            try:
                area_enum = Area(area)
                pos = HabitsCatalog.get_by_area(area_enum, "positive")
                neg = HabitsCatalog.get_by_area(area_enum, "negative")
                print(f"🎯 ABITUDINI PER AREA: {area}\n")
                print("📈 Positive:")
                for h in pos:
                    print(f"   {h.icona} {h.id}. {h.nome} ({h.pv_delta:+d} PV)")
                    print(f"      {h.descrizione}\n")
                print("📉 Negative:")
                for h in neg:
                    print(f"   {h.icona} {h.id}. {h.nome} ({h.pv_delta} PV)")
                    print(f"      {h.descrizione}\n")
                return
            except ValueError:
                print(f"❌ Area non valida: {area}")
                return
        else:
            print("📊 TUTTE LE ABITUDINI\n")
            print("📈 POSITIVE (26 totali):")
            habits_pos = HabitsCatalog.get_all_positive()
            for h in habits_pos:
                print(f"   {h.icona} {h.id:3d}. {h.nome:30s} ({h.area.value}) {h.pv_delta:+d} PV")

            print("\n📉 NEGATIVE (20 totali):")
            habits_neg = HabitsCatalog.get_all_negative()
            for h in habits_neg:
                print(f"   {h.icona} {h.id:3d}. {h.nome:30s} ({h.area.value}) {h.pv_delta} PV")

            print(f"\n💡 Usa 'habits --tipo positive' o '--tipo negative' per vedere solo un tipo")
            print(f"💡 Usa 'habits --area \"Nome Area\"' per vedere abitudini di un'area\n")
            return

        # Mostra habits filtrate
        for h in habits:
            print(f"{h.icona} {h.id}. {h.nome}")
            print(f"   Area: {h.area.value}")
            print(f"   Impatto: {h.pv_delta:+d} PV" if h.tipo == "positive" else f"   Impatto: {h.pv_delta} PV")
            print(f"   {h.descrizione}\n")

        print(f"Totale: {len(habits)} abitudini\n")

    def _interactive_chat(self, context: str = "general", **kwargs):
        """
        Modalità chat interattiva con Raffaello
        Permette di fare domande durante checkin/checkout
        """
        print("\n" + "="*60)
        print("💬 MODALITÀ INTERATTIVA - CHAT CON RAFFAELLO")
        print("="*60)
        print("📝 Puoi fare domande a Raffaello sul tuo stato, abitudini, strategie...")
        print("💡 Comandi speciali:")
        print("   - 'continua' o 'esci' → Termina la chat e continua")
        print("   - 'status' → Mostra il tuo stato attuale")
        print("   - 'habits' → Suggerisce abitudini da tracciare")
        print("   - 'help' → Mostra questi comandi")
        print("="*60 + "\n")

        chat_count = 0
        while True:
            try:
                # Input utente
                domanda = input("🌹 Tu: ").strip()

                if not domanda:
                    continue

                # Comandi speciali
                if domanda.lower() in ['continua', 'esci', 'exit', 'quit']:
                    print("\n🌹 Raffaello: Perfetto! Torniamo al flusso principale.\n")
                    break

                if domanda.lower() == 'status':
                    zona = self.calc.get_zona(self.player.pv_current)
                    liv_globale = self.calc.calcola_livello_globale(self.player)
                    print(f"\n📊 STATUS RAPIDO:")
                    print(f"   PV: {self.player.pv_current}/{self.player.pv_max} | Zona: {zona.value}")
                    print(f"   Livello Globale: {liv_globale}")
                    print(f"   Baros: {self.player.baros}")
                    print(f"   Giorno: {self.player.giorno}\n")
                    continue

                if domanda.lower() == 'habits':
                    print("\n🎯 ABITUDINI CONSIGLIATE PER OGGI:")
                    zona = self.calc.get_zona(self.player.pv_current)

                    # Suggerisci 5 abitudini positive base
                    base_habits = [1, 4, 5, 6, 13]  # Workout, Cibo, Sonno, Meditazione, Lettura
                    print("   📈 Positive da prioritizzare:")
                    for hid in base_habits:
                        h = HabitsCatalog.get_by_id(hid)
                        if h:
                            print(f"      {h.icona} {h.id}. {h.nome} (+{h.pv_delta} PV)")

                    # Avvisa su negative comuni
                    print("\n   📉 Negative da evitare oggi:")
                    danger_habits = [101, 105, 112]  # Junk food, Overthinking, Procrastination
                    for hid in danger_habits:
                        h = HabitsCatalog.get_by_id(hid)
                        if h:
                            print(f"      {h.icona} {h.id}. {h.nome} ({h.pv_delta} PV)")
                    print()
                    continue

                if domanda.lower() == 'help':
                    print("\n💡 COMANDI DISPONIBILI:")
                    print("   - 'status' → Il tuo stato corrente")
                    print("   - 'habits' → Suggerimenti abitudini")
                    print("   - 'continua' → Esci dalla chat")
                    print("   - Qualsiasi domanda → Raffaello risponde!\n")
                    continue

                # Domanda normale a Raffaello
                # Aggiungi contesto alla domanda
                contesto_extra = f"\n\nContesto: {context}"
                if context == "checkin":
                    contesto_extra += f" - Mood: {kwargs.get('mood')}/10, Energia: {kwargs.get('energia')}/10"
                elif context == "checkout" and 'habits_done' in kwargs:
                    contesto_extra += f" - Abitudini completate oggi"

                risposta = self.raffaello.parla_con_me(self.player, domanda + contesto_extra)

                print(f"\n🌹 Raffaello: {risposta}\n")
                chat_count += 1

                # Dopo 5 messaggi, suggerisci gentilmente di continuare
                if chat_count >= 5:
                    print("💡 (Hai fatto molte domande! Ricorda: puoi scrivere 'continua' quando sei pronto)\n")

            except KeyboardInterrupt:
                print("\n\n🌹 Raffaello: Capisco. Torniamo al flusso principale.\n")
                break
            except EOFError:
                print("\n\n🌹 Raffaello: Sembra che tu voglia uscire. Procediamo!\n")
                break

        print("="*60 + "\n")

    def reset(self):
        """Reset completo (usa con cautela!)"""
        confirm = input("⚠️  Sei sicuro? Questo cancellerà TUTTI i dati. (scrivi 'RESET'): ")
        if confirm == "RESET":
            self.player = self.dm.reset_player()
            print("✅ Reset completato. Nuovo inizio - Giorno #1.\n")
        else:
            print("❌ Reset annullato.\n")


def main():
    parser = argparse.ArgumentParser(description='LGAI - Life Game AI CLI')
    subparsers = parser.add_subparsers(dest='command', help='Comandi disponibili')

    # Status
    subparsers.add_parser('status', help='Mostra status corrente')

    # Check-in
    checkin_parser = subparsers.add_parser('checkin', help='Check-in mattutino')
    checkin_parser.add_argument('mood', type=int, help='Mood 1-10')
    checkin_parser.add_argument('energia', type=int, help='Energia 1-10')
    checkin_parser.add_argument('--note', type=str, default='', help='Note opzionali')
    checkin_parser.add_argument('--interactive', '-i', action='store_true', help='Modalità interattiva con Raffaello')

    # Check-out
    checkout_parser = subparsers.add_parser('checkout', help='Check-out serale')
    checkout_parser.add_argument('positive', type=int, nargs='?', help='Abitudini positive (conteggio semplice)')
    checkout_parser.add_argument('negative', type=int, nargs='?', help='Abitudini negative (conteggio semplice)')
    checkout_parser.add_argument('--habits-positive', type=str, help='ID abitudini positive (es: 1,3,6)')
    checkout_parser.add_argument('--habits-negative', type=str, help='ID abitudini negative (es: 101,112)')
    checkout_parser.add_argument('--note', type=str, default='', help='Note opzionali')
    checkout_parser.add_argument('--interactive', '-i', action='store_true', help='Modalità interattiva con Raffaello')

    # Add XP
    xp_parser = subparsers.add_parser('xp', help='Aggiungi XP a un\'area')
    xp_parser.add_argument('area', type=str, help='Nome area')
    xp_parser.add_argument('xp', type=int, help='Quantità XP')

    # Talk
    talk_parser = subparsers.add_parser('talk', help='Parla con Raffaello')
    talk_parser.add_argument('domanda', type=str, help='Cosa vuoi chiedere?')

    # Shop
    shop_parser = subparsers.add_parser('shop', help='Baros Shop - lista ricompense')
    shop_parser.add_argument('--categoria', type=str, help='Filtra per categoria')

    # Shop Buy
    buy_parser = subparsers.add_parser('buy', help='Acquista ricompensa Baros')
    buy_parser.add_argument('reward_id', type=int, help='ID ricompensa (1-50)')

    # Predictions
    subparsers.add_parser('predict', help='Predizioni Quantiche (Risk, Growth, Breakthrough)')

    # Missioni Catalog
    missioni_parser = subparsers.add_parser('missioni', help='Catalogo missioni complete')
    missioni_parser.add_argument('--categoria', type=str, help='Filtra per categoria')
    missioni_parser.add_argument('--difficolta', type=str, help='Filtra per difficoltà')

    # Habits Catalog
    habits_parser = subparsers.add_parser('habits', help='Catalogo abitudini tracciabili')
    habits_parser.add_argument('--tipo', type=str, help='positive o negative')
    habits_parser.add_argument('--area', type=str, help='Filtra per area vita')

    # Reset
    subparsers.add_parser('reset', help='Reset completo (ATTENZIONE!)')

    args = parser.parse_args()

    # Crea CLI instance
    cli = LGAICLI()

    # Esegui comando
    if args.command == 'status' or args.command is None:
        cli.status()
    elif args.command == 'checkin':
        cli.checkin(args.mood, args.energia, args.note, args.interactive)
    elif args.command == 'checkout':
        cli.checkout(args.positive, args.negative, args.note,
                     getattr(args, 'habits_positive', None),
                     getattr(args, 'habits_negative', None),
                     args.interactive)
    elif args.command == 'xp':
        cli.add_xp(args.area, args.xp)
    elif args.command == 'talk':
        cli.talk(args.domanda)
    elif args.command == 'shop':
        cli.shop_list(args.categoria)
    elif args.command == 'buy':
        cli.shop_buy(args.reward_id)
    elif args.command == 'predict':
        cli.predictions()
    elif args.command == 'missioni':
        cli.missioni_catalog(args.categoria, args.difficolta)
    elif args.command == 'habits':
        cli.habits_list(args.tipo, args.area)
    elif args.command == 'reset':
        cli.reset()


if __name__ == "__main__":
    main()
