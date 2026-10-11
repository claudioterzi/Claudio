"""
Data Manager - Gestisce salvataggio/caricamento dati player
Usa JSON locale per storage
"""

import json
import os
from typing import Optional
from datetime import datetime
from .calculator import PlayerStats, Area


class DataManager:
    """Gestisce persistenza dati del player"""

    def __init__(self, data_dir: str = "data"):
        self.data_dir = data_dir
        self.player_file = os.path.join(data_dir, "player.json")
        self.history_file = os.path.join(data_dir, "history.json")

        # Crea directory se non esiste
        os.makedirs(data_dir, exist_ok=True)

    def save_player(self, stats: PlayerStats) -> bool:
        """Salva statistiche player"""
        try:
            data = {
                'pv_current': stats.pv_current,
                'pv_max': stats.pv_max,
                'baros': stats.baros,
                'giorno': stats.giorno,
                'stagione': stats.stagione,
                'xp_per_area': {area.value: xp for area, xp in stats.xp_per_area.items()},
                'livelli_per_area': {area.value: liv for area, liv in stats.livelli_per_area.items()},
                'last_update': datetime.now().isoformat()
            }

            with open(self.player_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            return True
        except Exception as e:
            print(f"Errore nel salvataggio: {e}")
            return False

    def load_player(self) -> Optional[PlayerStats]:
        """Carica statistiche player"""
        if not os.path.exists(self.player_file):
            return None

        try:
            with open(self.player_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            stats = PlayerStats(
                pv_current=data['pv_current'],
                pv_max=data['pv_max'],
                baros=data['baros'],
                giorno=data['giorno'],
                stagione=data['stagione']
            )

            # Ricostruisci dizionari con enum
            stats.xp_per_area = {
                Area(area_name): xp
                for area_name, xp in data['xp_per_area'].items()
            }
            stats.livelli_per_area = {
                Area(area_name): liv
                for area_name, liv in data['livelli_per_area'].items()
            }

            return stats
        except Exception as e:
            print(f"Errore nel caricamento: {e}")
            return None

    def save_daily_log(self, giorno: int, log_data: dict) -> bool:
        """Salva log giornaliero in history"""
        try:
            # Carica history esistente
            history = self.load_history()

            # Aggiungi nuovo log
            log_data['timestamp'] = datetime.now().isoformat()
            history[str(giorno)] = log_data

            # Salva
            with open(self.history_file, 'w', encoding='utf-8') as f:
                json.dump(history, f, indent=2, ensure_ascii=False)

            return True
        except Exception as e:
            print(f"Errore nel salvataggio log: {e}")
            return False

    def load_history(self) -> dict:
        """Carica storico completo"""
        if not os.path.exists(self.history_file):
            return {}

        try:
            with open(self.history_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Errore nel caricamento history: {e}")
            return {}

    def get_last_7_days(self) -> list:
        """Ottieni ultimi 7 giorni di log"""
        history = self.load_history()
        giorni = sorted([int(k) for k in history.keys()])[-7:]
        return [history[str(g)] for g in giorni]

    def reset_player(self) -> PlayerStats:
        """Reset completo - nuovo inizio"""
        stats = PlayerStats()
        self.save_player(stats)
        return stats
