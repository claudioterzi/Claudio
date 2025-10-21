"""
RAFFAELLO - AI Companion per LGAI
Il tuo mentore, coach e guida spirituale
"""

from typing import Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime
import random
from .calculator import PlayerStats, Area, Zona, LGAICalculator


@dataclass
class AnalisiGiornaliera:
    """Risultato dell'analisi giornaliera di Raffaello"""
    pv_status: str
    zona_corrente: Zona
    trend: str  # "positivo", "negativo", "stabile"
    aree_forza: List[Area]
    aree_debolezza: List[Area]
    messaggio_motivazionale: str
    warning: Optional[str] = None
    prediction: Optional[str] = None


class Raffaello:
    """
    RAFFAELLO - AI Companion

    Analizza i tuoi dati, genera insight, crea missioni personalizzate,
    e ti accompagna nel viaggio di trasformazione.
    """

    # Messaggi motivazionali per zona
    MESSAGGI_PER_ZONA = {
        Zona.SOPRAVVIVENZA: [
            "🔴 Sei in ZONA CRITICA. Il tuo corpo e la tua mente ti stanno mandando un segnale: FERMATI. RESPIRA. Qualcosa deve cambiare ORA.",
            "⚠️ Livello di energia vitale BASSO. Questo è il momento di attivare la Sfida di Resurrezione. Non è una punizione - è un RITUALE di rinascita.",
            "🆘 Amico mio, sei vicino al Game Over. Ma ricorda: ogni caduta è un'opportunità per rinascere più forte. Cosa sei disposto a sacrificare per riemergere?"
        ],
        Zona.STAGNAZIONE: [
            "🟡 Sei in STAGNAZIONE. Non stai morendo, ma non stai nemmeno vivendo pienamente. È il momento di SCEGLIERE: comfort o crescita?",
            "⚡ L'energia c'è, ma è dispersa. Focalizza. Elimina 1 abitudine negativa oggi. Solo 1. E osserva la magia.",
            "🌱 Stagnazione = potenziale dormiente. Sei a metà strada. Un piccolo push e passi a CRESCITA. Quale abitudine positive farai OGGI?"
        ],
        Zona.CRESCITA: [
            "🟢 ZONA CRESCITA attivata! Stai operando bene. Mantieni questo ritmo e diventerai inarrestabile.",
            "🚀 L'energia scorre. Questo è il momento di OSARE. Quale missione selvaggia ti spaventa di più? Falla OGGI.",
            "💚 Stai costruendo momentum. Ogni giorno in questa zona è un mattone verso la tua trasformazione. Continua!"
        ],
        Zona.TRASFORMAZIONE: [
            "✨ ZONA TRASFORMAZIONE! Sei nel flusso. Questo è lo stato dove i miracoli accadono. La sincronicità ti sta cercando.",
            "🔥 FUOCO PURO. Stai operando al massimo potenziale. Ora è il momento di CREARE qualcosa di impossibile.",
            "🌟 Sei nella frequenza più alta. Tutto ciò che tocchi si trasforma. Questo è il tuo stato naturale - ricordalo quando tornerai in basso."
        ]
    }

    def __init__(self):
        self.calc = LGAICalculator()

    def analizza_giorno(self, stats: PlayerStats, abitudini_positive: int,
                       abitudini_negative: int, note: str = "") -> AnalisiGiornaliera:
        """
        Analisi completa dello stato del giocatore
        """
        zona = self.calc.get_zona(stats.pv_current)

        # Determina trend (basato su note o PV)
        trend = self._determina_trend(stats)

        # Identifica aree forza/debolezza
        aree_forza = self._trova_aree_forza(stats)
        aree_debolezza = self._trova_aree_debolezza(stats)

        # Genera messaggio
        messaggio = self._genera_messaggio(zona, trend, stats)

        # Warning se necessario
        warning = self._genera_warning(stats, abitudini_negative)

        # Prediction
        prediction = self._genera_prediction(stats, trend)

        # Status PV
        pv_status = f"{stats.pv_current}/{stats.pv_max} PV ({int((stats.pv_current/stats.pv_max)*100)}%)"

        return AnalisiGiornaliera(
            pv_status=pv_status,
            zona_corrente=zona,
            trend=trend,
            aree_forza=aree_forza,
            aree_debolezza=aree_debolezza,
            messaggio_motivazionale=messaggio,
            warning=warning,
            prediction=prediction
        )

    def genera_missioni_giornaliere(self, stats: PlayerStats, difficolta: str = "media") -> List[Dict]:
        """
        Genera 3 missioni personalizzate per il giorno

        Difficoltà: "facile", "media", "difficile", "selvaggia"
        """
        missioni = []

        # Identifica aree che hanno bisogno di focus
        aree_debolezza = self._trova_aree_debolezza(stats)

        # Genera missioni basate su zona corrente
        zona = self.calc.get_zona(stats.pv_current)

        if zona == Zona.SOPRAVVIVENZA:
            # Focus su recupero
            missioni = self._missioni_recupero()
        elif zona == Zona.STAGNAZIONE:
            # Focus su attivazione
            missioni = self._missioni_attivazione()
        elif zona == Zona.CRESCITA:
            # Focus su momentum
            missioni = self._missioni_momentum()
        else:  # TRASFORMAZIONE
            # Focus su breakthrough
            missioni = self._missioni_breakthrough()

        return missioni[:3]  # Solo 3 missioni al giorno

    def _determina_trend(self, stats: PlayerStats) -> str:
        """Determina se il trend è positivo, negativo o stabile"""
        # Semplificato: basato su PV
        if stats.pv_current >= 80:
            return "positivo"
        elif stats.pv_current <= 40:
            return "negativo"
        else:
            return "stabile"

    def _trova_aree_forza(self, stats: PlayerStats) -> List[Area]:
        """Trova le 2 aree con livello più alto"""
        sorted_areas = sorted(stats.livelli_per_area.items(),
                            key=lambda x: x[1], reverse=True)
        return [area for area, _ in sorted_areas[:2]]

    def _trova_aree_debolezza(self, stats: PlayerStats) -> List[Area]:
        """Trova le 2 aree con livello più basso"""
        sorted_areas = sorted(stats.livelli_per_area.items(),
                            key=lambda x: x[1])
        return [area for area, _ in sorted_areas[:2]]

    def _genera_messaggio(self, zona: Zona, trend: str, stats: PlayerStats) -> str:
        """Genera messaggio motivazionale contestuale"""
        base_msg = random.choice(self.MESSAGGI_PER_ZONA[zona])

        # Aggiungi personalizzazione
        livello_globale = self.calc.calcola_livello_globale(stats)
        progresso = self.calc.calcola_progresso_stagione(stats.giorno)

        extra = f"\n\n📊 Livello Globale: {livello_globale} | Giorno {progresso['giorno_in_stagione']}/90 (Stagione {progresso['stagione']})"

        return base_msg + extra

    def _genera_warning(self, stats: PlayerStats, abitudini_negative: int) -> Optional[str]:
        """Genera warning se necessario"""
        if stats.pv_current <= 20:
            return "⚠️ ATTENZIONE: Sei a rischio Game Over. 1 abitudine negativa in più e potresti cadere."

        if abitudini_negative >= 3:
            return "⚠️ Pattern pericoloso rilevato: 3+ abitudini negative. L'ombra sta prendendo controllo."

        return None

    def _genera_prediction(self, stats: PlayerStats, trend: str) -> Optional[str]:
        """Genera prediction basata su pattern"""
        if trend == "positivo":
            giorni_a_100pv = int((100 - stats.pv_current) / 10)
            return f"🔮 Se mantieni questo ritmo, raggiungi 100 PV in ~{giorni_a_100pv} giorni."

        if trend == "negativo" and stats.pv_current <= 50:
            giorni_a_gameover = int(stats.pv_current / 15)
            return f"⚠️ Se il trend negativo continua, Game Over in ~{giorni_a_gameover} giorni."

        return None

    # Generatori Missioni per Zona

    def _missioni_recupero(self) -> List[Dict]:
        """Missioni per Zona Sopravvivenza - Focus: RECUPERO"""
        return [
            {
                "titolo": "🛌 Recupero Totale",
                "descrizione": "Dormi 8+ ore stanotte. Niente schermi 1h prima di dormire.",
                "area": Area.SALUTE_FISICA,
                "xp": 30,
                "tipo": "recupero"
            },
            {
                "titolo": "🧘 Reset Mentale",
                "descrizione": "10 minuti di meditazione o respirazione consapevole. Solo questo.",
                "area": Area.SALUTE_MENTALE,
                "xp": 25,
                "tipo": "recupero"
            },
            {
                "titolo": "🚫 Zero Tossicità",
                "descrizione": "Evita TUTTE le abitudini negative oggi. Solo per oggi.",
                "area": Area.SALUTE_MENTALE,
                "xp": 40,
                "tipo": "recupero"
            }
        ]

    def _missioni_attivazione(self) -> List[Dict]:
        """Missioni per Zona Stagnazione - Focus: ATTIVAZIONE"""
        return [
            {
                "titolo": "⚡ Scossa Fisica",
                "descrizione": "30 min movimento intenso (corsa/HIIT/danza). Fai sudare il corpo.",
                "area": Area.SALUTE_FISICA,
                "xp": 40,
                "tipo": "attivazione"
            },
            {
                "titolo": "📞 Connessione Umana",
                "descrizione": "Chiama o vedi di persona qualcuno che ami. Conversazione vera.",
                "area": Area.RELAZIONI,
                "xp": 35,
                "tipo": "attivazione"
            },
            {
                "titolo": "🎨 Atto Creativo",
                "descrizione": "Crea qualcosa con le tue mani. Disegno, musica, scrittura. 30 min.",
                "area": Area.CREATIVITA,
                "xp": 45,
                "tipo": "attivazione"
            }
        ]

    def _missioni_momentum(self) -> List[Dict]:
        """Missioni per Zona Crescita - Focus: MOMENTUM"""
        return [
            {
                "titolo": "🚀 Push Estremo",
                "descrizione": "Fai 1.5x del tuo workout normale. Supera il tuo limite.",
                "area": Area.SALUTE_FISICA,
                "xp": 60,
                "tipo": "momentum"
            },
            {
                "titolo": "📚 Deep Learning",
                "descrizione": "2h di studio profondo su skill che vuoi masterizzare. No distrazioni.",
                "area": Area.CRESCITA,
                "xp": 70,
                "tipo": "momentum"
            },
            {
                "titolo": "💰 Money Move",
                "descrizione": "Fai 1 azione concreta per aumentare entrate (pitch, vendita, investimento).",
                "area": Area.FINANZE,
                "xp": 80,
                "tipo": "momentum"
            }
        ]

    def _missioni_breakthrough(self) -> List[Dict]:
        """Missioni per Zona Trasformazione - Focus: BREAKTHROUGH"""
        return [
            {
                "titolo": "🔥 Impossibile Reso Possibile",
                "descrizione": "Fai qualcosa che ieri avresti detto 'non posso'. Rompi il limite.",
                "area": Area.CRESCITA,
                "xp": 100,
                "tipo": "breakthrough"
            },
            {
                "titolo": "🎁 Contributo Estremo",
                "descrizione": "Fai qualcosa che migliora la vita di uno sconosciuto. Senza aspettarti nulla.",
                "area": Area.CONTRIBUTO,
                "xp": 90,
                "tipo": "breakthrough"
            },
            {
                "titolo": "✨ Creazione Magica",
                "descrizione": "Crea un'opera che esprima la tua essenza più profonda. Condividila.",
                "area": Area.CREATIVITA,
                "xp": 120,
                "tipo": "breakthrough"
            }
        ]

    def parla_con_me(self, stats: PlayerStats, domanda: str) -> str:
        """
        Interfaccia conversazionale con Raffaello
        (Versione base - può essere estesa con LLM vero)
        """
        domanda_lower = domanda.lower()

        # Pattern matching base
        if "come sto" in domanda_lower or "stato" in domanda_lower:
            analisi = self.analizza_giorno(stats, 0, 0)
            return f"{analisi.messaggio_motivazionale}\n\n{analisi.pv_status} | Zona: {analisi.zona_corrente.value}"

        elif "missioni" in domanda_lower or "cosa fare" in domanda_lower:
            missioni = self.genera_missioni_giornaliere(stats)
            result = "🎯 MISSIONI DEL GIORNO:\n\n"
            for i, m in enumerate(missioni, 1):
                result += f"{i}. {m['titolo']}\n   {m['descrizione']}\n   Reward: {m['xp']} XP ({m['area'].value})\n\n"
            return result

        elif "livello" in domanda_lower:
            liv_globale = self.calc.calcola_livello_globale(stats)
            aree_forza = self._trova_aree_forza(stats)
            return f"🎮 Livello Globale: {liv_globale}\n\n💪 Aree Forza:\n- {aree_forza[0].value} (Lv.{stats.livelli_per_area[aree_forza[0]]})\n- {aree_forza[1].value} (Lv.{stats.livelli_per_area[aree_forza[1]]})"

        else:
            return "🌹 Ciao! Sono Raffaello. Chiedimi:\n- 'Come sto?'\n- 'Dammi le missioni'\n- 'Qual è il mio livello?'"


# Demo
if __name__ == "__main__":
    from calculator import PlayerStats, Area

    print("=== RAFFAELLO AI Demo ===\n")

    # Setup
    player = PlayerStats()
    player.pv_current = 75
    player.livelli_per_area[Area.SALUTE_FISICA] = 5
    player.livelli_per_area[Area.CREATIVITA] = 3
    player.giorno = 15

    raffaello = Raffaello()

    # Test analisi
    print("1. ANALISI GIORNALIERA")
    analisi = raffaello.analizza_giorno(player, 7, 1)
    print(f"   {analisi.pv_status}")
    print(f"   Zona: {analisi.zona_corrente.value}")
    print(f"   {analisi.messaggio_motivazionale}\n")

    # Test missioni
    print("\n2. MISSIONI GENERATE")
    missioni = raffaello.genera_missioni_giornaliere(player)
    for i, m in enumerate(missioni, 1):
        print(f"   {i}. {m['titolo']} (+{m['xp']} XP)")

    # Test conversazione
    print("\n3. CONVERSAZIONE")
    risposta = raffaello.parla_con_me(player, "Come sto?")
    print(f"   {risposta}")
