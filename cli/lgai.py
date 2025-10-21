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
import argparse
from datetime import datetime


class LGAICLI:
    """CLI principale"""

    def __init__(self):
        self.dm = DataManager()
        self.calc = LGAICalculator()
        self.raffaello = Raffaello()

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

    def checkin(self, mood: int, energia: int, note: str = ""):
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

    def checkout(self, abitudini_positive: int, abitudini_negative: int, note: str = ""):
        """Check-out serale"""
        print("\n🌙 CHECK-OUT SERALE")

        # Calcola PV delta
        pv_loss = abitudini_negative * 10
        pv_gain = self.calc.calcola_regen_giornaliera(self.player,
                                                      abitudini_positive, 10)

        pv_delta = pv_gain - pv_loss

        print(f"   Abitudini Positive: {abitudini_positive}/10")
        print(f"   Abitudini Negative: {abitudini_negative}")
        print(f"\n   PV Regen: +{pv_gain}")
        print(f"   PV Loss: -{pv_loss}")
        print(f"   Delta: {pv_delta:+d} PV")

        # Applica modifiche
        result = self.calc.modifica_pv(self.player, pv_delta, "Daily checkout")

        print(f"\n   Nuovi PV: {result['new_pv']}/{self.player.pv_max}")
        print(f"   Zona: {result['zona_after'].value}")

        if result['game_over']:
            print("\n   🔴🔴🔴 GAME OVER 🔴🔴🔴")
            print("   Attiva Sfida di Resurrezione!")

        # Incrementa giorno
        self.player.giorno += 1

        # Salva
        self.dm.save_player(self.player)

        log = {
            'tipo': 'checkout',
            'abitudini_positive': abitudini_positive,
            'abitudini_negative': abitudini_negative,
            'pv_delta': pv_delta,
            'pv_final': result['new_pv'],
            'note': note
        }
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

    # Check-out
    checkout_parser = subparsers.add_parser('checkout', help='Check-out serale')
    checkout_parser.add_argument('positive', type=int, help='Abitudini positive completate')
    checkout_parser.add_argument('negative', type=int, help='Abitudini negative cadute')
    checkout_parser.add_argument('--note', type=str, default='', help='Note opzionali')

    # Add XP
    xp_parser = subparsers.add_parser('xp', help='Aggiungi XP a un\'area')
    xp_parser.add_argument('area', type=str, help='Nome area')
    xp_parser.add_argument('xp', type=int, help='Quantità XP')

    # Talk
    talk_parser = subparsers.add_parser('talk', help='Parla con Raffaello')
    talk_parser.add_argument('domanda', type=str, help='Cosa vuoi chiedere?')

    # Reset
    subparsers.add_parser('reset', help='Reset completo (ATTENZIONE!)')

    args = parser.parse_args()

    # Crea CLI instance
    cli = LGAICLI()

    # Esegui comando
    if args.command == 'status' or args.command is None:
        cli.status()
    elif args.command == 'checkin':
        cli.checkin(args.mood, args.energia, args.note)
    elif args.command == 'checkout':
        cli.checkout(args.positive, args.negative, args.note)
    elif args.command == 'xp':
        cli.add_xp(args.area, args.xp)
    elif args.command == 'talk':
        cli.talk(args.domanda)
    elif args.command == 'reset':
        cli.reset()


if __name__ == "__main__":
    main()
