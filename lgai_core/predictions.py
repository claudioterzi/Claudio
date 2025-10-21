"""
PREDICTION SYSTEM - Sistema Predizioni Quantiche
Risk Score, Growth Predictions, Breakthrough Windows, Sincronicità
"""

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import statistics

try:
    from .calculator import PlayerStats, Area, LGAICalculator
except ImportError:
    from calculator import PlayerStats, Area, LGAICalculator


@dataclass
class RiskAnalysis:
    """Analisi rischio Game Over"""
    score: int  # 0-100
    livello: str  # "ZONA SICURA", "ATTENZIONE", etc.
    componenti: Dict[str, float]
    raccomandazioni: List[str]
    giorni_stimati_go: Optional[int] = None


@dataclass
class GrowthPrediction:
    """Predizione crescita per area"""
    area: Area
    livello_attuale: int
    xp_mancanti: int
    media_xp_giorno: float
    giorni_stimati: int
    probabilita: int  # 0-100%


@dataclass
class BreakthroughWindow:
    """Finestra ottimale per breakthrough"""
    data: datetime
    ora_inizio: str
    ora_fine: str
    energia_prevista: float
    focus_previsto: float
    creativita_prevista: float
    probabilita_breakthrough: int


@dataclass
class SyncPrediction:
    """Predizione sincronicità"""
    data: datetime
    tipo: str
    descrizione: str
    probabilita: int  # 0-100%
    fascia_oraria: str


class PredictionSystem:
    """
    Sistema Predizioni Quantiche Avanzato
    Analizza pattern storici e predice future events
    """

    def __init__(self):
        self.calc = LGAICalculator()

    def calculate_risk_score(self, stats: PlayerStats, history: List[dict]) -> RiskAnalysis:
        """
        Calcola Risk Score dettagliato
        Componenti:
        1. Giorni PV negativo (ultimi 7)
        2. % Abitudini negative
        3. Giorni zero positive
        4. Streak interrotti
        5. Energia media
        """
        componenti = {}

        # Ultimi 7 giorni
        last_7 = history[-7:] if len(history) >= 7 else history

        # 1. Giorni PV negativo (max 20 punti)
        giorni_pv_neg = sum(1 for day in last_7 if day.get('pv_delta', 0) < 0)
        componenti['giorni_pv_negativo'] = giorni_pv_neg * 20 / 7

        # 2. % Abitudini negative (max 30 punti)
        total_neg = sum(day.get('abitudini_negative', 0) for day in last_7)
        perc_negative = (total_neg / len(last_7)) if last_7 else 0
        componenti['perc_abitudini_negative'] = min(perc_negative * 10, 30)

        # 3. Giorni zero positive (max 15 punti)
        giorni_zero_pos = sum(1 for day in last_7 if day.get('abitudini_positive', 0) == 0)
        componenti['giorni_zero_positive'] = giorni_zero_pos * 15 / 7

        # 4. Streak interrotti ultimi 30 giorni (max 10 punti)
        last_30 = history[-30:] if len(history) >= 30 else history
        streak_rotti = sum(1 for day in last_30 if day.get('abitudini_negative', 0) > 0)
        componenti['streak_interrotti'] = min(streak_rotti, 10)

        # 5. Energia media bassa (max 25 punti)
        if last_7:
            energia_media = statistics.mean([day.get('energia', 5) for day in last_7])
            # Se energia < 5, aggiungi punti
            if energia_media < 5:
                componenti['energia_bassa'] = (5 - energia_media) * 5
            else:
                componenti['energia_bassa'] = 0
        else:
            componenti['energia_bassa'] = 0

        # Calcola score totale
        total_score = int(sum(componenti.values()))
        total_score = min(total_score, 100)

        # Determina livello rischio
        if total_score >= 80:
            livello = "⚠️ GAME OVER IMMINENTE"
        elif total_score >= 60:
            livello = "🔴 RISCHIO ALTO"
        elif total_score >= 40:
            livello = "🟠 RISCHIO MODERATO"
        elif total_score >= 20:
            livello = "🟡 ATTENZIONE"
        else:
            livello = "🟢 ZONA SICURA"

        # Raccomandazioni
        raccomandazioni = []
        if componenti['giorni_pv_negativo'] > 10:
            raccomandazioni.append("Elimina immediatamente 1 abitudine negativa principale")
        if componenti['perc_abitudini_negative'] > 15:
            raccomandazioni.append("Pattern abitudini negative troppo frequente. Focus su sostituzione.")
        if componenti['giorni_zero_positive'] > 5:
            raccomandazioni.append("Troppi giorni senza abitudini positive. Inizia con solo 1-2 facili.")
        if componenti['energia_bassa'] > 10:
            raccomandazioni.append("Energia sotto soglia critica. Priorità: sonno e recupero.")
        if total_score < 20:
            raccomandazioni.append("Situazione stabile. Continua così e celebra progressi!")

        # Stima giorni a Game Over se trend negativo
        giorni_go = None
        if total_score >= 40 and stats.pv_current < 50:
            # Calcola trend PV
            if last_7:
                pv_deltas = [day.get('pv_delta', 0) for day in last_7]
                avg_delta = statistics.mean(pv_deltas)
                if avg_delta < 0:
                    giorni_go = int(stats.pv_current / abs(avg_delta))

        return RiskAnalysis(
            score=total_score,
            livello=livello,
            componenti=componenti,
            raccomandazioni=raccomandazioni,
            giorni_stimati_go=giorni_go
        )

    def predict_level_ups(self, stats: PlayerStats, history: List[dict]) -> List[GrowthPrediction]:
        """
        Predice level up per ogni area
        Basato su media XP ultimi 7 giorni
        """
        predictions = []

        # Calcola media XP per area ultimi 7 giorni
        last_7 = history[-7:] if len(history) >= 7 else history

        for area in Area:
            # XP mancanti per next level
            livello_attuale = stats.livelli_per_area[area]
            xp_corrente = stats.xp_per_area[area]
            xp_necessari = self.calc.calcola_xp_per_livello(livello_attuale)
            xp_mancanti = xp_necessari - xp_corrente

            # Media XP/giorno per questa area
            if last_7:
                xp_per_giorno = []
                for day in last_7:
                    # Simula XP guadagnati (in realtà dovrebbero essere salvati in history)
                    # Per ora usiamo stima basata su abitudini
                    xp_day = day.get(f'xp_{area.value}', 0)
                    xp_per_giorno.append(xp_day)

                media_xp = statistics.mean(xp_per_giorno) if xp_per_giorno else 0
            else:
                media_xp = 0

            # Calcola giorni stimati
            if media_xp > 0:
                giorni_stimati = int(xp_mancanti / media_xp)
            else:
                giorni_stimati = 999  # Impossibile stimare

            # Calcola probabilità
            if giorni_stimati <= 1:
                probabilita = 95
            elif giorni_stimati <= 3:
                probabilita = 85
            elif giorni_stimati <= 7:
                probabilita = 70
            elif giorni_stimati <= 14:
                probabilita = 50
            else:
                probabilita = 30

            predictions.append(GrowthPrediction(
                area=area,
                livello_attuale=livello_attuale,
                xp_mancanti=xp_mancanti,
                media_xp_giorno=media_xp,
                giorni_stimati=giorni_stimati,
                probabilita=probabilita
            ))

        # Ordina per giorni stimati (più vicini prima)
        predictions.sort(key=lambda p: p.giorni_stimati)

        return predictions

    def find_breakthrough_windows(self, history: List[dict], days_ahead: int = 7) -> List[BreakthroughWindow]:
        """
        Identifica finestre ottimali per breakthrough nei prossimi giorni
        Basato su pattern storici di energia/produttività
        """
        windows = []

        if not history:
            return windows

        # Analizza pattern per giorno settimana e ora
        # Per semplicità, usiamo pattern fissi + dati storici

        oggi = datetime.now()

        for i in range(days_ahead):
            data = oggi + timedelta(days=i)
            giorno_settimana = data.weekday()  # 0=Lunedì, 6=Domenica

            # Pattern energia per giorno settimana (euristici)
            energia_base = {
                0: 7.5,  # Lunedì
                1: 8.0,  # Martedì
                2: 8.5,  # Mercoledì
                3: 9.0,  # Giovedì (MIGLIORE)
                4: 7.0,  # Venerdì
                5: 8.0,  # Sabato
                6: 6.5,  # Domenica
            }

            energia = energia_base.get(giorno_settimana, 7.5)

            # Aggiungi variazione da history se disponibile
            same_weekday_days = [
                day for day in history[-30:]
                if datetime.fromisoformat(day.get('timestamp', oggi.isoformat())).weekday() == giorno_settimana
            ]

            if same_weekday_days:
                avg_energia_history = statistics.mean([
                    day.get('energia', 7) for day in same_weekday_days
                ])
                energia = (energia + avg_energia_history) / 2

            # Focus e creatività correlati
            focus = energia + 0.5 if energia > 8 else energia
            creativita = energia - 0.2

            # Probabilità breakthrough
            if energia >= 9.0:
                prob = 85
            elif energia >= 8.5:
                prob = 78
            elif energia >= 8.0:
                prob = 70
            else:
                prob = 50

            # Finestra oraria ottimale (mattina presto generalmente migliore)
            if giorno_settimana < 5:  # Giorni lavorativi
                ora_inizio = "09:00"
                ora_fine = "12:00"
            else:  # Weekend
                ora_inizio = "07:00"
                ora_fine = "10:00"

            windows.append(BreakthroughWindow(
                data=data,
                ora_inizio=ora_inizio,
                ora_fine=ora_fine,
                energia_prevista=round(energia, 1),
                focus_previsto=round(focus, 1),
                creativita_prevista=round(creativita, 1),
                probabilita_breakthrough=prob
            ))

        # Ordina per probabilità (migliori prima)
        windows.sort(key=lambda w: w.probabilita_breakthrough, reverse=True)

        return windows

    def predict_synchronicity(self, stats: PlayerStats, days_ahead: int = 7) -> List[SyncPrediction]:
        """
        Predice sincronicità basate su:
        - Livello Sovranità (livello globale)
        - Fase lunare (approssimata)
        - Pattern storici
        """
        predictions = []

        livello_globale = self.calc.calcola_livello_globale(stats)
        zona = self.calc.get_zona(stats.pv_current)

        # Maggiore sincronicità con livello alto e zona Trasformazione
        base_prob = 30
        if livello_globale >= 10:
            base_prob += 20
        if livello_globale >= 25:
            base_prob += 15
        if zona.value == "Trasformazione":
            base_prob += 20

        oggi = datetime.now()

        for i in range(days_ahead):
            data = oggi + timedelta(days=i)
            giorno_settimana = data.weekday()

            # Probabilità varia per giorno settimana
            prob_modifier = {
                0: 0,   # Lunedì
                1: +5,  # Martedì (Marte - energia)
                2: +10, # Mercoledì (Mercurio - comunicazione)
                3: +15, # Giovedì (Giove - espansione) **MIGLIORE**
                4: +5,  # Venerdì (Venere - relazioni)
                5: +10, # Sabato
                6: -5,  # Domenica (riposo)
            }

            prob = base_prob + prob_modifier.get(giorno_settimana, 0)
            prob = min(prob, 90)  # Cap a 90%

            # Genera predizioni diverse per probabilità
            if prob >= 75:
                # Alta probabilità
                predictions.append(SyncPrediction(
                    data=data,
                    tipo="Incontro Significativo",
                    descrizione="Persona che può aiutarti in progetto corrente",
                    probabilita=prob,
                    fascia_oraria="14:00-17:00"
                ))
            elif prob >= 60:
                # Media probabilità
                predictions.append(SyncPrediction(
                    data=data,
                    tipo="Insight Trasformativo",
                    descrizione="Soluzione a problema che stai affrontando",
                    probabilita=prob,
                    fascia_oraria="Mattina durante pratica"
                ))
            elif prob >= 45:
                # Bassa-media probabilità
                predictions.append(SyncPrediction(
                    data=data,
                    tipo="Messaggio Inaspettato",
                    descrizione="Persona del passato ti contatta",
                    probabilita=prob,
                    fascia_oraria="Pomeriggio"
                ))

        return predictions

    def monthly_forecast(self, stats: PlayerStats, month_ahead: int = 1) -> Dict:
        """
        Previsione completa per un mese futuro
        """
        oggi = datetime.now()
        target_month = (oggi.month + month_ahead - 1) % 12 + 1
        target_year = oggi.year + (oggi.month + month_ahead - 1) // 12

        # Calcola energia generale del mese (pattern stagionali)
        energia_mese = {
            1: 7.0,   # Gennaio - Inizio anno
            2: 7.5,   # Febbraio
            3: 8.5,   # Marzo - Primavera
            4: 9.0,   # Aprile
            5: 9.0,   # Maggio
            6: 8.0,   # Giugno
            7: 7.5,   # Luglio - Estate, vacanze
            8: 7.0,   # Agosto
            9: 8.5,   # Settembre - Ripartenza
            10: 9.0,  # Ottobre
            11: 8.5,  # Novembre
            12: 7.5,  # Dicembre - Fine anno
        }

        energia_generale = energia_mese.get(target_month, 8.0)

        # Tema del mese (basato su stagione e energia)
        if energia_generale >= 9.0:
            tema = "ESPANSIONE & MANIFESTAZIONE"
        elif energia_generale >= 8.0:
            tema = "CRESCITA & CONSOLIDAMENTO"
        elif energia_generale >= 7.5:
            tema = "MANTENIMENTO & PREPARAZIONE"
        else:
            tema = "RECUPERO & RIFLESSIONE"

        return {
            'mese': target_month,
            'anno': target_year,
            'tema': tema,
            'energia_generale': energia_generale,
            'livello_globale_previsto': stats.livelli_per_area[list(Area)[0]] + 2,  # Stima
            'sincronicita_prevista': "Alta" if energia_generale >= 8.5 else "Media",
        }


# Test
if __name__ == "__main__":
    from calculator import PlayerStats, Area

    print("=== PREDICTION SYSTEM DEMO ===\n")

    # Setup player con history simulato
    player = PlayerStats()
    player.pv_current = 75
    player.giorno = 45

    history = [
        {'pv_delta': 5, 'abitudini_positive': 8, 'abitudini_negative': 1, 'energia': 7, 'timestamp': datetime.now().isoformat()},
        {'pv_delta': -5, 'abitudini_positive': 6, 'abitudini_negative': 2, 'energia': 6, 'timestamp': datetime.now().isoformat()},
        {'pv_delta': 10, 'abitudini_positive': 9, 'abitudini_negative': 0, 'energia': 8, 'timestamp': datetime.now().isoformat()},
        {'pv_delta': 5, 'abitudini_positive': 7, 'abitudini_negative': 1, 'energia': 7, 'timestamp': datetime.now().isoformat()},
        {'pv_delta': 0, 'abitudini_positive': 7, 'abitudini_negative': 1, 'energia': 7, 'timestamp': datetime.now().isoformat()},
        {'pv_delta': 5, 'abitudini_positive': 8, 'abitudini_negative': 1, 'energia': 8, 'timestamp': datetime.now().isoformat()},
        {'pv_delta': 10, 'abitudini_positive': 9, 'abitudini_negative': 0, 'energia': 9, 'timestamp': datetime.now().isoformat()},
    ]

    pred = PredictionSystem()

    # Test Risk Score
    print("1. RISK SCORE")
    risk = pred.calculate_risk_score(player, history)
    print(f"   Score: {risk.score}/100")
    print(f"   Livello: {risk.livello}")
    print(f"   Raccomandazioni:")
    for r in risk.raccomandazioni[:2]:
        print(f"   - {r}")

    # Test Breakthrough Windows
    print("\n2. BREAKTHROUGH WINDOWS (Prossimi 3 giorni)")
    windows = pred.find_breakthrough_windows(history, days_ahead=3)
    for w in windows[:3]:
        print(f"   {w.data.strftime('%A %d/%m')}: {w.ora_inizio}-{w.ora_fine}")
        print(f"   Energia: {w.energia_prevista}/10 | Prob: {w.probabilita_breakthrough}%")

    # Test Monthly Forecast
    print("\n3. MONTHLY FORECAST")
    forecast = pred.monthly_forecast(player)
    print(f"   Mese: {forecast['mese']}/{forecast['anno']}")
    print(f"   Tema: {forecast['tema']}")
    print(f"   Energia Generale: {forecast['energia_generale']}/10")
