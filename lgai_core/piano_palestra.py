"""
PIANO PALESTRA LGAI - Body Recomposition Protocol
Programma DUP (Daily Undulating Periodization) 3x/settimana
Livello: Intermedio | Obiettivo: Body Recomposition
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional
from enum import Enum


class TipoGiorno(Enum):
    FORZA = "A - Forza"
    IPERTROFIA = "B - Ipertrofia"
    METABOLICO = "C - Metabolico"


class GruppoMuscolare(Enum):
    GAMBE = "Gambe"
    PETTO = "Petto"
    SCHIENA = "Schiena"
    SPALLE = "Spalle"
    BICIPITI = "Bicipiti"
    TRICIPITI = "Tricipiti"
    CORE = "Core"
    FULL_BODY = "Full Body"


@dataclass
class Esercizio:
    nome: str
    gruppo: GruppoMuscolare
    serie: int
    rip_min: int
    rip_max: int
    riposo_sec: int
    note: str = ""
    peso_iniziale_kg: Optional[float] = None  # suggerimento per iniziare
    incremento_kg: float = 2.5  # incremento progressivo

    @property
    def reps_str(self) -> str:
        if self.rip_min == self.rip_max:
            return str(self.rip_min)
        return f"{self.rip_min}-{self.rip_max}"

    @property
    def riposo_str(self) -> str:
        if self.riposo_sec >= 60:
            m = self.riposo_sec // 60
            s = self.riposo_sec % 60
            return f"{m}min {s}sec" if s else f"{m}min"
        return f"{self.riposo_sec}sec"


@dataclass
class SessioneAllenamento:
    tipo: TipoGiorno
    durata_stimata_min: int
    esercizi: List[Esercizio]
    descrizione: str
    focus_cardio: str = ""
    xp_reward: int = 0
    pv_reward: int = 0


@dataclass
class ProgressioneEsercizio:
    """Traccia i progressi su un esercizio specifico"""
    esercizio_nome: str
    peso_corrente_kg: float
    serie_completate: List[bool] = field(default_factory=list)
    rip_raggiunte: List[int] = field(default_factory=list)
    data_ultimo_aggiornamento: str = ""

    def pronto_per_progressione(self, rip_target_max: int) -> bool:
        """True se tutte le serie hanno raggiunto le reps massime"""
        if not self.rip_raggiunte:
            return False
        return all(r >= rip_target_max for r in self.rip_raggiunte)


class PianoPalestra:
    """
    Piano Palestra Body Recomposition per livello intermedio.
    Struttura DUP: Giorno A (Forza) -> B (Ipertrofia) -> C (Metabolico)
    """

    # Ricompense XP/PV
    XP_GIORNO_A = 90
    XP_GIORNO_B = 80
    XP_GIORNO_C = 70
    XP_BONUS_SETTIMANA_COMPLETA = 60
    PV_PER_ALLENAMENTO = 6
    PV_BONUS_SETTIMANA = 10

    def __init__(self):
        self.giorni = {
            TipoGiorno.FORZA: self._crea_giorno_forza(),
            TipoGiorno.IPERTROFIA: self._crea_giorno_ipertrofia(),
            TipoGiorno.METABOLICO: self._crea_giorno_metabolico(),
        }

    def _crea_giorno_forza(self) -> SessioneAllenamento:
        return SessioneAllenamento(
            tipo=TipoGiorno.FORZA,
            durata_stimata_min=75,
            descrizione=(
                "Focus su carichi massimali con esercizi compound. "
                "Attiva il sistema nervoso centrale e costruisce forza base. "
                "Riscaldamento 10 min obbligatorio."
            ),
            esercizi=[
                Esercizio(
                    "Squat Bilanciere", GruppoMuscolare.GAMBE,
                    serie=4, rip_min=4, rip_max=6, riposo_sec=180,
                    note="Scendi sotto parallelo, schiena neutra",
                    incremento_kg=2.5
                ),
                Esercizio(
                    "Stacco da Terra", GruppoMuscolare.GAMBE,
                    serie=3, rip_min=4, rip_max=6, riposo_sec=180,
                    note="Hip hinge, barra vicina alle gambe, non arrotondare la schiena",
                    incremento_kg=2.5
                ),
                Esercizio(
                    "Panca Piana Bilanciere", GruppoMuscolare.PETTO,
                    serie=4, rip_min=4, rip_max=6, riposo_sec=180,
                    note="Presa simmetrica, scapole retratte, piedi a terra",
                    incremento_kg=2.5
                ),
                Esercizio(
                    "Trazioni / Lat Machine", GruppoMuscolare.SCHIENA,
                    serie=3, rip_min=6, rip_max=8, riposo_sec=120,
                    note="Se non riesci le trazioni usa lat machine. Presa supina per più bicipiti",
                    incremento_kg=2.5
                ),
                Esercizio(
                    "Military Press Bilanciere", GruppoMuscolare.SPALLE,
                    serie=3, rip_min=5, rip_max=7, riposo_sec=120,
                    note="In piedi o seduto, core contratto, no arco lombare",
                    incremento_kg=2.5
                ),
                Esercizio(
                    "Curl Bilanciere", GruppoMuscolare.BICIPITI,
                    serie=2, rip_min=8, rip_max=8, riposo_sec=90,
                    note="Gomiti fissi, non dondolare il busto",
                    incremento_kg=2.5
                ),
                Esercizio(
                    "Dip / French Press", GruppoMuscolare.TRICIPITI,
                    serie=2, rip_min=8, rip_max=8, riposo_sec=90,
                    note="Dip se possibile, altrimenti French press con bilanciere EZ",
                    incremento_kg=2.5
                ),
            ],
            xp_reward=90,
            pv_reward=6,
        )

    def _crea_giorno_ipertrofia(self) -> SessioneAllenamento:
        return SessioneAllenamento(
            tipo=TipoGiorno.IPERTROFIA,
            durata_stimata_min=80,
            descrizione=(
                "Volume moderato nel range ottimale per l'ipertrofia (8-12 rip). "
                "Enfasi sulla connessione mente-muscolo e tempo sotto tensione. "
                "Riscaldamento 10 min. Riposi brevi per massimizzare il metabolismo."
            ),
            esercizi=[
                Esercizio(
                    "Leg Press", GruppoMuscolare.GAMBE,
                    serie=4, rip_min=10, rip_max=12, riposo_sec=90,
                    note="Piedi larghi per glutei/hamstring, piedi stretti per quadricipiti",
                    incremento_kg=5.0
                ),
                Esercizio(
                    "Romanian Deadlift (RDL)", GruppoMuscolare.GAMBE,
                    serie=4, rip_min=10, rip_max=12, riposo_sec=90,
                    note="Senti lo stretch agli hamstring, barra vicino alle gambe",
                    incremento_kg=2.5
                ),
                Esercizio(
                    "Panca Inclinata Manubri", GruppoMuscolare.PETTO,
                    serie=3, rip_min=10, rip_max=12, riposo_sec=90,
                    note="30-45° inclinazione, porta i manubri al petto controllato",
                    incremento_kg=2.0
                ),
                Esercizio(
                    "Rematore Bilanciere / Manubri", GruppoMuscolare.SCHIENA,
                    serie=4, rip_min=10, rip_max=12, riposo_sec=90,
                    note="Schiena inclinata ~45°, porta il bilanciere all'ombelico",
                    incremento_kg=2.5
                ),
                Esercizio(
                    "Shoulder Press Manubri", GruppoMuscolare.SPALLE,
                    serie=3, rip_min=10, rip_max=12, riposo_sec=90,
                    note="Seduto con schienale, controllato in discesa",
                    incremento_kg=2.0
                ),
                Esercizio(
                    "Leg Curl (sdraiato o seduto)", GruppoMuscolare.GAMBE,
                    serie=3, rip_min=12, rip_max=15, riposo_sec=75,
                    note="Contrazione piena, non usare lo slancio",
                    incremento_kg=2.5
                ),
                Esercizio(
                    "Leg Extension", GruppoMuscolare.GAMBE,
                    serie=3, rip_min=12, rip_max=15, riposo_sec=75,
                    note="Tieni la contrazione 1 sec in cima",
                    incremento_kg=2.5
                ),
                Esercizio(
                    "Curl Manubri Alternato", GruppoMuscolare.BICIPITI,
                    serie=3, rip_min=12, rip_max=12, riposo_sec=60,
                    note="Supina il polso in cima, posa lenta in 3 sec",
                    incremento_kg=2.0
                ),
                Esercizio(
                    "Skullcrusher (EZ bar)", GruppoMuscolare.TRICIPITI,
                    serie=3, rip_min=12, rip_max=12, riposo_sec=60,
                    note="Gomiti puntati al soffitto, non allargare",
                    incremento_kg=2.0
                ),
                Esercizio(
                    "Plank", GruppoMuscolare.CORE,
                    serie=3, rip_min=45, rip_max=60, riposo_sec=45,
                    note="Corpo dritto come un'asse, respira regolarmente (rip = secondi)",
                    incremento_kg=0
                ),
            ],
            xp_reward=80,
            pv_reward=6,
        )

    def _crea_giorno_metabolico(self) -> SessioneAllenamento:
        return SessioneAllenamento(
            tipo=TipoGiorno.METABOLICO,
            durata_stimata_min=70,
            descrizione=(
                "Circuit training ad alta densità per massimizzare il dispendio calorico "
                "e la risposta ormonale anabolica. 4 round del circuito completo. "
                "Riposo 45-60 sec tra esercizi, 2 min tra round."
            ),
            focus_cardio=(
                "FINISHER (scegli uno): "
                "a) 15-20 min LISS: camminata veloce 6-7 km/h o cyclette leggera "
                "b) 10 min HIIT: 30 sec sprint / 30 sec riposo x 10 round"
            ),
            esercizi=[
                Esercizio(
                    "Goblet Squat (manubrio)", GruppoMuscolare.GAMBE,
                    serie=4, rip_min=15, rip_max=15, riposo_sec=50,
                    note="Manubrio al petto, gomiti dentro le ginocchia in basso",
                    incremento_kg=2.0
                ),
                Esercizio(
                    "Push-up / Panca Inclinata Leggera", GruppoMuscolare.PETTO,
                    serie=4, rip_min=15, rip_max=20, riposo_sec=50,
                    note="Se push-up troppo facile, usa un gilet zavorrato",
                    incremento_kg=0
                ),
                Esercizio(
                    "Kettlebell / Manubrio Swing", GruppoMuscolare.FULL_BODY,
                    serie=4, rip_min=20, rip_max=20, riposo_sec=50,
                    note="Movimento da anche, non le braccia! Esplosivo verso l'alto",
                    incremento_kg=2.0
                ),
                Esercizio(
                    "Chin-up / Lat Machine Presa Stretta", GruppoMuscolare.SCHIENA,
                    serie=4, rip_min=10, rip_max=15, riposo_sec=50,
                    note="Presa supina, porta il mento sopra la sbarra",
                    incremento_kg=0
                ),
                Esercizio(
                    "Affondi Alternati", GruppoMuscolare.GAMBE,
                    serie=4, rip_min=12, rip_max=12, riposo_sec=50,
                    note="12 per gamba. Ginocchio posteriore sfiora il pavimento",
                    incremento_kg=2.0
                ),
                Esercizio(
                    "Face Pull (cavo o elastico)", GruppoMuscolare.SPALLE,
                    serie=4, rip_min=20, rip_max=20, riposo_sec=45,
                    note="Cavo all'altezza del viso, gomiti alti, estrai verso il viso",
                    incremento_kg=0
                ),
            ],
            xp_reward=70,
            pv_reward=6,
        )

    def stampa_piano(self, tipo: TipoGiorno = None):
        """Stampa il piano formattato su console"""
        giorni_da_stampare = (
            [self.giorni[tipo]] if tipo
            else list(self.giorni.values())
        )

        for sessione in giorni_da_stampare:
            self._stampa_sessione(sessione)

    def _stampa_sessione(self, sessione: SessioneAllenamento):
        icone = {
            TipoGiorno.FORZA: "🔴",
            TipoGiorno.IPERTROFIA: "🟡",
            TipoGiorno.METABOLICO: "🟢",
        }
        icona = icone[sessione.tipo]

        print(f"\n{'='*60}")
        print(f"{icona} GIORNO {sessione.tipo.value.upper()}")
        print(f"   Durata: ~{sessione.durata_stimata_min} min")
        print(f"   Reward: +{sessione.xp_reward} XP | +{sessione.pv_reward} PV")
        print(f"{'='*60}")
        print(f"\n{sessione.descrizione}\n")

        print(f"{'N°':<4} {'Esercizio':<35} {'Serie':<7} {'Rip':<10} {'Riposo':<10}")
        print("-" * 66)

        for i, es in enumerate(sessione.esercizi, 1):
            print(
                f"{i:<4} {es.nome:<35} {es.serie}x{'':<4} "
                f"{es.reps_str:<10} {es.riposo_str:<10}"
            )
            if es.note:
                print(f"     💡 {es.note}")

        if sessione.focus_cardio:
            print(f"\n🏃 CARDIO FINISHER:")
            print(f"   {sessione.focus_cardio}")

        print()

    def ottieni_prossimo_giorno(self, allenamenti_completati: int) -> TipoGiorno:
        """Determina il prossimo giorno in base al ciclo A -> B -> C -> A..."""
        ciclo = [TipoGiorno.FORZA, TipoGiorno.IPERTROFIA, TipoGiorno.METABOLICO]
        return ciclo[allenamenti_completati % 3]

    def calcola_progressione(
        self, prog: ProgressioneEsercizio, tipo_giorno: TipoGiorno
    ) -> Dict:
        """
        Calcola se incrementare il peso basandosi sul completamento delle serie.
        Regola: se tutte le serie raggiungono le reps massime -> aumenta peso.
        """
        esercizi_giorno = self.giorni[tipo_giorno].esercizi
        esercizio = next(
            (e for e in esercizi_giorno if e.nome == prog.esercizio_nome), None
        )

        if not esercizio:
            return {"incrementa": False, "motivo": "Esercizio non trovato"}

        pronto = prog.pronto_per_progressione(esercizio.rip_max)
        nuovo_peso = prog.peso_corrente_kg + esercizio.incremento_kg if pronto else prog.peso_corrente_kg

        return {
            "incrementa": pronto,
            "peso_attuale": prog.peso_corrente_kg,
            "nuovo_peso": nuovo_peso,
            "incremento": esercizio.incremento_kg if pronto else 0,
            "motivo": (
                f"Hai raggiunto {esercizio.rip_max} rip su tutte le serie! Aumenta di {esercizio.incremento_kg}kg"
                if pronto
                else f"Raggiungi {esercizio.rip_max} rip su TUTTE le serie prima di aumentare"
            ),
        }

    def stampa_schema_settimanale(self):
        """Stampa lo schema settimanale consigliato"""
        print("\n" + "="*60)
        print("📅 SCHEMA SETTIMANALE BODY RECOMPOSITION")
        print("="*60)
        print()
        schema = [
            ("Lunedì",   TipoGiorno.FORZA,      "🔴 Giorno A - Forza"),
            ("Martedì",  None,                   "😴 Riposo attivo / mobilità"),
            ("Mercoledì",TipoGiorno.IPERTROFIA,  "🟡 Giorno B - Ipertrofia"),
            ("Giovedì",  None,                   "😴 Riposo attivo / mobilità"),
            ("Venerdì",  TipoGiorno.METABOLICO,  "🟢 Giorno C - Metabolico"),
            ("Sabato",   None,                   "😴 Riposo / attività libera"),
            ("Domenica", None,                   "😴 Riposo completo"),
        ]
        for giorno, tipo, desc in schema:
            reward = ""
            if tipo:
                sessione = self.giorni[tipo]
                reward = f"  → +{sessione.xp_reward} XP | +{sessione.pv_reward} PV"
            print(f"  {giorno:<12} {desc}{reward}")

        print()
        print("  BONUS settimana completa (3/3 allenamenti):")
        print(f"  → +{self.XP_BONUS_SETTIMANA_COMPLETA} XP bonus | +{self.PV_BONUS_SETTIMANA} PV bonus")
        print()
        print("  PRINCIPIO PROGRESSIVO: Quando completi TUTTE le serie")
        print("  al numero MAX di reps → aumenta il peso la settimana dopo.")
        print("  Forza: +2.5kg | Ipertrofia: +2-2.5kg | Metabolico: +2kg")
        print()
