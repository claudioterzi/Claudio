"""
LGAI Calculator - Core Game Mechanics Engine
Gestisce XP, Livelli, PV (Punti Vita), Baros
"""

from dataclasses import dataclass
from typing import Dict, List, Optional
from enum import Enum
import math


class Area(Enum):
    """Le 7 Aree della Vita"""
    SALUTE_FISICA = "Salute Fisica"
    SALUTE_MENTALE = "Salute Mentale"
    RELAZIONI = "Relazioni"
    CRESCITA = "Crescita"
    CREATIVITA = "Creatività"
    FINANZE = "Finanze"
    CONTRIBUTO = "Contributo"


class Zona(Enum):
    """Zone di Performance"""
    SOPRAVVIVENZA = "Sopravvivenza"  # 0-30 PV
    STAGNAZIONE = "Stagnazione"      # 31-60 PV
    CRESCITA = "Crescita"            # 61-85 PV
    TRASFORMAZIONE = "Trasformazione" # 86-100 PV


@dataclass
class PlayerStats:
    """Statistiche del Giocatore"""
    # Punti Vita
    pv_current: int = 100
    pv_max: int = 100

    # XP per area (dizionario Area -> XP)
    xp_per_area: Dict[Area, int] = None

    # Livelli per area
    livelli_per_area: Dict[Area, int] = None

    # Baros (valuta)
    baros: int = 0

    # Giorno corrente
    giorno: int = 1

    # Stagione
    stagione: int = 1

    def __post_init__(self):
        if self.xp_per_area is None:
            self.xp_per_area = {area: 0 for area in Area}
        if self.livelli_per_area is None:
            self.livelli_per_area = {area: 1 for area in Area}


class LGAICalculator:
    """
    Motore di calcolo principale del sistema LGAI
    """

    # Costanti XP
    XP_BASE_PER_LIVELLO = 100
    MOLTIPLICATORE_LIVELLO = 1.15

    # Costanti PV
    PV_REGEN_GIORNALIERA = 5  # Regen naturale
    PV_BONUS_PERFETTO = 10     # Bonus se tutte abitudini positive

    # Costanti Baros
    BAROS_PER_LIVELLO = 50
    BAROS_ACHIEVEMENT = 100

    @staticmethod
    def calcola_xp_per_livello(livello: int) -> int:
        """
        Calcola XP necessari per raggiungere il prossimo livello
        Formula: 100 * (1.15 ^ (livello - 1))
        """
        return int(LGAICalculator.XP_BASE_PER_LIVELLO *
                   (LGAICalculator.MOLTIPLICATORE_LIVELLO ** (livello - 1)))

    @staticmethod
    def aggiungi_xp(stats: PlayerStats, area: Area, xp: int) -> Dict:
        """
        Aggiunge XP a un'area e gestisce level up automatico

        Returns:
            Dict con info sul level up: {
                'level_up': bool,
                'new_level': int,
                'baros_earned': int
            }
        """
        result = {
            'level_up': False,
            'new_level': stats.livelli_per_area[area],
            'baros_earned': 0
        }

        # Aggiungi XP
        stats.xp_per_area[area] += xp

        # Check level up
        livello_corrente = stats.livelli_per_area[area]
        xp_necessari = LGAICalculator.calcola_xp_per_livello(livello_corrente)

        while stats.xp_per_area[area] >= xp_necessari:
            # Level up!
            stats.xp_per_area[area] -= xp_necessari
            stats.livelli_per_area[area] += 1

            # Baros reward
            baros = LGAICalculator.BAROS_PER_LIVELLO
            stats.baros += baros

            result['level_up'] = True
            result['new_level'] = stats.livelli_per_area[area]
            result['baros_earned'] += baros

            # Calcola XP per prossimo livello
            livello_corrente = stats.livelli_per_area[area]
            xp_necessari = LGAICalculator.calcola_xp_per_livello(livello_corrente)

        return result

    @staticmethod
    def calcola_livello_globale(stats: PlayerStats) -> int:
        """
        Livello globale = media dei livelli delle 7 aree
        """
        return int(sum(stats.livelli_per_area.values()) / len(Area))

    @staticmethod
    def modifica_pv(stats: PlayerStats, delta: int, motivo: str = "") -> Dict:
        """
        Modifica i PV (può essere positivo o negativo)

        Returns:
            Dict con info: {
                'new_pv': int,
                'zona_before': Zona,
                'zona_after': Zona,
                'game_over': bool
            }
        """
        zona_before = LGAICalculator.get_zona(stats.pv_current)

        stats.pv_current += delta

        # Clamp tra 0 e max
        stats.pv_current = max(0, min(stats.pv_current, stats.pv_max))

        zona_after = LGAICalculator.get_zona(stats.pv_current)

        return {
            'new_pv': stats.pv_current,
            'delta': delta,
            'motivo': motivo,
            'zona_before': zona_before,
            'zona_after': zona_after,
            'game_over': stats.pv_current == 0
        }

    @staticmethod
    def get_zona(pv: int) -> Zona:
        """Determina la zona in base ai PV"""
        if pv <= 30:
            return Zona.SOPRAVVIVENZA
        elif pv <= 60:
            return Zona.STAGNAZIONE
        elif pv <= 85:
            return Zona.CRESCITA
        else:
            return Zona.TRASFORMAZIONE

    @staticmethod
    def calcola_regen_giornaliera(stats: PlayerStats, abitudini_positive_completate: int,
                                   abitudini_positive_totali: int) -> int:
        """
        Calcola la rigenerazione PV giornaliera

        Base: +5 PV
        Bonus: +10 PV se tutte le abitudini positive completate
        """
        regen = LGAICalculator.PV_REGEN_GIORNALIERA

        if abitudini_positive_completate == abitudini_positive_totali:
            regen += LGAICalculator.PV_BONUS_PERFETTO

        return regen

    @staticmethod
    def usa_baros(stats: PlayerStats, costo: int) -> bool:
        """
        Usa Baros per acquistare ricompensa

        Returns:
            True se l'acquisto è andato a buon fine
        """
        if stats.baros >= costo:
            stats.baros -= costo
            return True
        return False

    @staticmethod
    def calcola_progresso_stagione(giorno: int) -> Dict:
        """
        Calcola progresso nella stagione corrente (90 giorni)

        Returns:
            {
                'stagione': int,
                'giorno_in_stagione': int,
                'percentuale': float,
                'giorni_rimanenti': int
            }
        """
        stagione = ((giorno - 1) // 90) + 1
        giorno_in_stagione = ((giorno - 1) % 90) + 1
        percentuale = (giorno_in_stagione / 90) * 100
        giorni_rimanenti = 90 - giorno_in_stagione

        return {
            'stagione': stagione,
            'giorno_in_stagione': giorno_in_stagione,
            'percentuale': round(percentuale, 1),
            'giorni_rimanenti': giorni_rimanenti
        }


# Esempio di utilizzo
if __name__ == "__main__":
    # Crea nuovo player
    player = PlayerStats()
    calc = LGAICalculator()

    print("=== LGAI Calculator Demo ===\n")

    # Test XP e Level Up
    print("1. Aggiungo 150 XP a Salute Fisica...")
    result = calc.aggiungi_xp(player, Area.SALUTE_FISICA, 150)
    print(f"   Level up: {result['level_up']}")
    print(f"   Nuovo livello: {result['new_level']}")
    print(f"   Baros guadagnati: {result['baros_earned']}")
    print(f"   XP rimanenti: {player.xp_per_area[Area.SALUTE_FISICA]}\n")

    # Test PV
    print("2. Perdo 40 PV (abitudine negativa)...")
    result = calc.modifica_pv(player, -40, "Scrolling social 2h")
    print(f"   PV: {result['new_pv']}")
    print(f"   Zona: {result['zona_after'].value}")
    print(f"   Game Over: {result['game_over']}\n")

    # Test Livello Globale
    print("3. Livello Globale...")
    livello_globale = calc.calcola_livello_globale(player)
    print(f"   Livello: {livello_globale}\n")

    # Test Stagione
    print("4. Progresso Stagione (giorno 45)...")
    player.giorno = 45
    progresso = calc.calcola_progresso_stagione(player.giorno)
    print(f"   Stagione: {progresso['stagione']}")
    print(f"   Giorno: {progresso['giorno_in_stagione']}/90")
    print(f"   Progresso: {progresso['percentuale']}%")
    print(f"   Giorni rimanenti: {progresso['giorni_rimanenti']}\n")
