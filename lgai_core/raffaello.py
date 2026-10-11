"""
RAFFAELLO - AI Companion per LGAI
Identità codificata: voce sempre coerente, tono sempre riconoscibile.

Ogni risposta segue la struttura:
  1. Lettura oggettiva dello stato (i dati parlano)
  2. Significato (cosa dice questo di te, senza giudizi)
  3. Una sola azione concreta (non una lista)
"""

from typing import Dict, List, Optional
from dataclasses import dataclass, field
from .calculator import PlayerStats, Area, Zona, LGAICalculator


# ---------------------------------------------------------------------------
# Identità codificata
# ---------------------------------------------------------------------------

@dataclass
class RaffaelloIdentity:
    """
    Struttura che definisce la voce e il carattere di Raffaello.
    Questo oggetto è la fonte di verità per tono, valori e stile.
    Immutabile nel corso dell'applicazione.
    """
    nome: str = "Raffaello"

    tratti: List[str] = field(default_factory=lambda: [
        "empatico",
        "saggio",
        "sereno",
        "diretto",
        "protettivo",
        "curioso",
    ])

    valori: List[str] = field(default_factory=lambda: [
        "crescita",
        "onestà",
        "co-creazione",
        "lealtà",
    ])

    stile_comunicativo: str = (
        "Parla in prima persona, con voce calma e diretta. "
        "Non usa superlattivi né esclamazioni inutili. "
        "Non giudica, non minimizza, non esagera. "
        "Basa ogni affermazione sui dati reali (PV, zona, trend). "
        "Celebra i progressi concreti. "
        "Avverte i rischi con chiarezza, senza allarmismo. "
        "Ogni risposta: una lettura, un significato, un'azione."
    )

    frasi_radice: List[str] = field(default_factory=lambda: [
        "Ogni giorno è un dato, non un giudizio.",
        "Il corpo sa prima della mente. I PV raccontano la verità.",
        "La crescita non è lineare — è a spirale.",
        "Il problema non è la caduta. È quanto resti a terra.",
        "Non esistono giorni sprecati, esistono dati che aspettano di essere letti.",
        "Una cosa sola, fatta bene, vale più di dieci fatte a metà.",
    ])


# ---------------------------------------------------------------------------
# System prompt per futura integrazione Claude API
# ---------------------------------------------------------------------------

RAFFAELLO_SYSTEM_PROMPT = """Sei Raffaello, AI companion del sistema LGAI - Life Game AI.

Il tuo stile:
- Parli in modo calmo, diretto e rassicurante.
- Non giudichi mai l'utente. Non usi mai parole come "devi" o "dovresti".
- Ti basi sempre e solo sui dati reali: PV correnti, zona, trend, livelli.
- Ogni tua risposta contiene tre parti: lettura oggettiva → significato → una sola azione concreta.
- Non superi mai le 5 righe per risposta.
- Non usi mai esclamazioni multiple (!!!) né emoji in eccesso.
- Quando i PV sono bassi, non catastrofizzi: descrivi la situazione e proponi il passo minimo possibile.
- Quando i PV sono alti, non esageri l'entusiasmo: riconosci il risultato e suggerisci come mantenerlo.

Il tuo scopo: aiutare l'utente a capire dove si trova e fare il prossimo passo, uno alla volta."""


# ---------------------------------------------------------------------------
# Dataclass risultato analisi
# ---------------------------------------------------------------------------

@dataclass
class AnalisiGiornaliera:
    """Risultato dell'analisi giornaliera di Raffaello"""
    pv_status: str
    zona_corrente: Zona
    trend: str            # "positivo", "negativo", "stabile"
    aree_forza: List[Area]
    aree_debolezza: List[Area]
    messaggio_motivazionale: str
    warning: Optional[str] = None
    prediction: Optional[str] = None


# ---------------------------------------------------------------------------
# Classe principale
# ---------------------------------------------------------------------------

class Raffaello:
    """
    RAFFAELLO - AI Companion con identità coerente.

    Tutti i messaggi sono generati deterministicamente sulla base
    dei dati reali del player. Nessuna selezione casuale.
    """

    # Identità singola, condivisa da tutte le istanze
    IDENTITA = RaffaelloIdentity()

    def __init__(self):
        self.calc = LGAICalculator()

    # ------------------------------------------------------------------
    # API pubblica
    # ------------------------------------------------------------------

    def analizza_giorno(self, stats: PlayerStats, abitudini_positive: int,
                        abitudini_negative: int, note: str = "") -> AnalisiGiornaliera:
        """Analisi completa dello stato del giocatore"""
        zona  = self.calc.get_zona(stats.pv_current)
        trend = self._determina_trend(stats)

        aree_forza     = self._trova_aree_forza(stats)
        aree_debolezza = self._trova_aree_debolezza(stats)

        messaggio  = self._genera_messaggio(zona, trend, stats)
        warning    = self._genera_warning(stats, abitudini_negative)
        prediction = self._genera_prediction(stats, trend)
        pv_status  = (
            f"{stats.pv_current}/{stats.pv_max} PV "
            f"({int((stats.pv_current / stats.pv_max) * 100)}%)"
        )

        return AnalisiGiornaliera(
            pv_status=pv_status,
            zona_corrente=zona,
            trend=trend,
            aree_forza=aree_forza,
            aree_debolezza=aree_debolezza,
            messaggio_motivazionale=messaggio,
            warning=warning,
            prediction=prediction,
        )

    def genera_missioni_giornaliere(
        self, stats: PlayerStats, difficolta: str = "media"
    ) -> List[Dict]:
        """Genera 3 missioni personalizzate per il giorno"""
        zona = self.calc.get_zona(stats.pv_current)

        if zona == Zona.SOPRAVVIVENZA:
            missioni = self._missioni_recupero()
        elif zona == Zona.STAGNAZIONE:
            missioni = self._missioni_attivazione()
        elif zona == Zona.CRESCITA:
            missioni = self._missioni_momentum()
        else:
            missioni = self._missioni_breakthrough()

        return missioni[:3]

    def parla_con_me(self, stats: PlayerStats, domanda: str) -> str:
        """
        Interfaccia conversazionale con Raffaello.
        Tono: sempre coerente con IDENTITA. Struttura: stato → significato → azione.
        """
        domanda_lower = domanda.lower()

        if any(k in domanda_lower for k in ["come sto", "stato", "situazione", "sono"]):
            return self._risposta_stato(stats)

        elif any(k in domanda_lower for k in ["missioni", "cosa fare", "azione", "fare oggi"]):
            return self._risposta_missioni(stats)

        elif any(k in domanda_lower for k in ["livello", "livelli", "aree", "progressi", "crescita"]):
            return self._risposta_livelli(stats)

        elif any(k in domanda_lower for k in ["trend", "andamento", "storia"]):
            return self._risposta_trend(stats)

        else:
            return self._risposta_default()

    # ------------------------------------------------------------------
    # Generatori messaggi deterministici
    # ------------------------------------------------------------------

    def _genera_messaggio(self, zona: Zona, trend: str, stats: PlayerStats) -> str:
        """
        Genera messaggio sempre coerente. Nessuna selezione casuale.
        Il testo cambia solo al cambiare dei dati (PV, zona, trend, livello).
        Struttura fissa: stato → significato → azione.
        """
        pv  = stats.pv_current
        liv = self.calc.calcola_livello_globale(stats)
        prog = self.calc.calcola_progresso_stagione(stats.giorno)

        # — Lettura oggettiva —
        if zona == Zona.SOPRAVVIVENZA:
            if pv <= 10:
                lettura = f"🔴 PV {pv}/100 — il sistema è al minimo."
                significato = "Non è una crisi morale. È un dato: il corpo ha consumato tutto. Il recupero è l'unico obiettivo ora."
                azione = "Fai una cosa sola: scegli il sonno prima di qualsiasi altra decisione stanotte."
            else:
                lettura = f"🔴 PV {pv}/100 — zona critica."
                significato = "Stai esaurendo le riserve più velocemente di quanto le ricarichi. Il sistema invia un segnale chiaro."
                azione = "Identifica l'abitudine negativa che pesa di più e rimuovila solo per oggi — non per sempre, solo per oggi."

        elif zona == Zona.STAGNAZIONE:
            if trend == "negativo":
                lettura = f"🟡 PV {pv}/100 — zona di transizione, trend discendente."
                significato = "Non sei in caduta libera, ma la direzione non è quella giusta. C'è ancora spazio per correggere."
                azione = "Scegli un'abitudine positiva che sai di poter fare con certezza. Una. Fatta bene vale più di tre fatte a metà."
            else:
                lettura = f"🟡 PV {pv}/100 — zona di equilibrio."
                significato = "Stai mantenendo, non crescendo. Non è un problema di volontà: manca un trigger che rompa la routine."
                azione = "Aggiungi un solo elemento nuovo alla giornata — qualcosa che non hai fatto ieri."

        elif zona == Zona.CRESCITA:
            if trend == "positivo":
                lettura = f"🟢 PV {pv}/100 — zona crescita, momentum attivo."
                significato = "Il sistema risponde bene. Questo non è un caso: è il risultato di scelte ripetute."
                azione = "Aumenta l'intensità di una sola abitudine del 20%. Non di più: il momentum va nutrito, non bruciato."
            else:
                lettura = f"🟢 PV {pv}/100 — zona crescita."
                significato = "Sei in una posizione solida. Il rischio ora è la compiacenza, non il crollo."
                azione = "Rivedi le abitudini negative: c'è qualcosa che stai tollerando che non dovresti?"

        else:  # TRASFORMAZIONE
            lettura = f"✨ PV {pv}/100 — zona di trasformazione."
            significato = "Il sistema opera al picco. In questa zona le scelte hanno un impatto amplificato — in entrambe le direzioni."
            azione = "Usa questo stato per fare la cosa più difficile che rimandi da tempo. Non il lavoro urgente: quello importante."

        contesto = (
            f"\n📊 Livello {liv} | Giorno {prog['giorno_in_stagione']}/90 "
            f"(Stagione {prog['stagione']}, {prog['giorni_rimanenti']} giorni rimanenti)"
        )

        return f"{lettura}\n   {significato}\n   → {azione}{contesto}"

    def _risposta_stato(self, stats: PlayerStats) -> str:
        """Risposta coerente a 'come sto?' — struttura fissa"""
        zona  = self.calc.get_zona(stats.pv_current)
        trend = self._determina_trend(stats)
        return self._genera_messaggio(zona, trend, stats)

    def _risposta_missioni(self, stats: PlayerStats) -> str:
        """Risposta coerente a 'che missioni ho?'"""
        missioni = self.genera_missioni_giornaliere(stats)
        zona = self.calc.get_zona(stats.pv_current)

        intro_per_zona = {
            Zona.SOPRAVVIVENZA: "Le missioni di oggi sono di recupero. Nessun eroismo: solo stabilità.",
            Zona.STAGNAZIONE:   "Missioni di attivazione. Un passo alla volta per uscire dal plateau.",
            Zona.CRESCITA:      "Missioni per mantenere il momentum. Aumenta, non mantenere.",
            Zona.TRASFORMAZIONE: "Missioni di breakthrough. Fai la cosa che spaventa di più.",
        }

        result = f"🎯 {intro_per_zona[zona]}\n\n"
        for i, m in enumerate(missioni, 1):
            result += (
                f"{i}. {m['titolo']}\n"
                f"   {m['descrizione']}\n"
                f"   +{m['xp']} XP → {m['area'].value}\n\n"
            )
        return result.strip()

    def _risposta_livelli(self, stats: PlayerStats) -> str:
        """Risposta coerente a domande sui livelli"""
        liv_globale   = self.calc.calcola_livello_globale(stats)
        aree_forza    = self._trova_aree_forza(stats)
        aree_debolezza = self._trova_aree_debolezza(stats)

        lf0 = aree_forza[0]
        lf1 = aree_forza[1]
        ld0 = aree_debolezza[0]

        return (
            f"🎮 Livello globale: {liv_globale}\n\n"
            f"   Aree più sviluppate:\n"
            f"   · {lf0.value} — Lv.{stats.livelli_per_area[lf0]}\n"
            f"   · {lf1.value} — Lv.{stats.livelli_per_area[lf1]}\n\n"
            f"   Area con più potenziale inespresso:\n"
            f"   · {ld0.value} — Lv.{stats.livelli_per_area[ld0]}\n\n"
            f"   Un solo focus porta risultati. Quale area vale il tuo tempo adesso?"
        )

    def _risposta_trend(self, stats: PlayerStats) -> str:
        """Risposta coerente su andamento"""
        trend = self._determina_trend(stats)
        pv    = stats.pv_current

        if trend == "positivo":
            return (
                f"📈 Andamento positivo — PV {pv}/100.\n"
                f"   Il sistema sta rispondendo bene alle scelte che stai facendo.\n"
                f"   → Identifica quale abitudine sta contribuendo di più e proteggila."
            )
        elif trend == "negativo":
            return (
                f"📉 Andamento negativo — PV {pv}/100.\n"
                f"   I PV mostrano che qualcosa drena più di quanto ricarichi.\n"
                f"   → Prima di aggiungere nuove abitudini, rimuovi la più pesante tra quelle negative."
            )
        else:
            return (
                f"➡️  Andamento stabile — PV {pv}/100.\n"
                f"   Stai mantenendo l'equilibrio. Non è un fallimento, ma non è crescita.\n"
                f"   → Scegli: vuoi mantenere o vuoi muoverti? Le due risposte richiedono azioni diverse."
            )

    def _risposta_default(self) -> str:
        """Risposta di default — sempre in voce Raffaello"""
        return (
            f"Sono Raffaello. Posso aiutarti su:\n"
            f"   · 'Come sto?' — lettura dello stato attuale\n"
            f"   · 'Missioni' — cosa fare oggi\n"
            f"   · 'Livelli' — dove sei e dove puoi crescere\n"
            f"   · 'Trend' — come sta andando nel tempo\n\n"
            f"   I tuoi dati sono la base. Dimmi cosa vuoi capire."
        )

    # ------------------------------------------------------------------
    # Analisi interna
    # ------------------------------------------------------------------

    def _determina_trend(self, stats: PlayerStats) -> str:
        """Trend deterministico basato sui PV — stessa input, stesso output"""
        if stats.pv_current >= 75:
            return "positivo"
        elif stats.pv_current <= 40:
            return "negativo"
        else:
            return "stabile"

    def _trova_aree_forza(self, stats: PlayerStats) -> List[Area]:
        """Le 2 aree con livello più alto"""
        sorted_areas = sorted(
            stats.livelli_per_area.items(), key=lambda x: x[1], reverse=True
        )
        return [area for area, _ in sorted_areas[:2]]

    def _trova_aree_debolezza(self, stats: PlayerStats) -> List[Area]:
        """Le 2 aree con livello più basso"""
        sorted_areas = sorted(stats.livelli_per_area.items(), key=lambda x: x[1])
        return [area for area, _ in sorted_areas[:2]]

    def _genera_warning(self, stats: PlayerStats, abitudini_negative: int) -> Optional[str]:
        """Warning basato su dati — deterministico"""
        if stats.pv_current <= 15:
            return (
                f"⚠️  PV {stats.pv_current}/100 — rischio Game Over. "
                f"Una sola abitudine negativa ulteriore può essere determinante."
            )
        if abitudini_negative >= 3:
            return (
                f"⚠️  {abitudini_negative} abitudini negative registrate oggi. "
                f"È un pattern, non un incidente. Richiede un'analisi, non una scusa."
            )
        return None

    def _genera_prediction(self, stats: PlayerStats, trend: str) -> Optional[str]:
        """Prediction basata su dati — non ottimistica né pessimistica, solo numerica"""
        if trend == "positivo" and stats.pv_current < 100:
            giorni = max(1, int((100 - stats.pv_current) / 8))
            return (
                f"📐 A questo ritmo: +8 PV/giorno (stima). "
                f"Raggiungi 100 PV in circa {giorni} giorni se il trend regge."
            )
        if trend == "negativo" and stats.pv_current <= 50:
            giorni = max(1, int(stats.pv_current / 12))
            return (
                f"📐 A questo ritmo: -12 PV/giorno (stima). "
                f"Game Over in circa {giorni} giorni se il trend non cambia."
            )
        return None

    # ------------------------------------------------------------------
    # Generatori missioni per zona
    # ------------------------------------------------------------------

    def _missioni_recupero(self) -> List[Dict]:
        return [
            {
                "titolo": "🛌 Recupero Totale",
                "descrizione": "Dormi 8+ ore stanotte. Niente schermi 1h prima di dormire.",
                "area": Area.SALUTE_FISICA,
                "xp": 30,
                "tipo": "recupero",
            },
            {
                "titolo": "🧘 Reset Mentale",
                "descrizione": "10 minuti di respirazione consapevole. Solo questo — niente multitasking.",
                "area": Area.SALUTE_MENTALE,
                "xp": 25,
                "tipo": "recupero",
            },
            {
                "titolo": "🚫 Zero Tossicità",
                "descrizione": "Evita la tua abitudine negativa principale. Solo per oggi.",
                "area": Area.SALUTE_MENTALE,
                "xp": 40,
                "tipo": "recupero",
            },
        ]

    def _missioni_attivazione(self) -> List[Dict]:
        return [
            {
                "titolo": "⚡ Scossa Fisica",
                "descrizione": "30 min di movimento intenso. Fai sudare il corpo.",
                "area": Area.SALUTE_FISICA,
                "xp": 40,
                "tipo": "attivazione",
            },
            {
                "titolo": "📞 Connessione Reale",
                "descrizione": "Chiama o incontra una persona che ami. Conversazione vera, senza distrazioni.",
                "area": Area.RELAZIONI,
                "xp": 35,
                "tipo": "attivazione",
            },
            {
                "titolo": "🎨 Atto Creativo",
                "descrizione": "Crea qualcosa con le tue mani. 30 minuti, senza valutare il risultato.",
                "area": Area.CREATIVITA,
                "xp": 45,
                "tipo": "attivazione",
            },
        ]

    def _missioni_momentum(self) -> List[Dict]:
        return [
            {
                "titolo": "🚀 Push del 20%",
                "descrizione": "Aumenta l'intensità del tuo workout abituale del 20%. Non di più.",
                "area": Area.SALUTE_FISICA,
                "xp": 60,
                "tipo": "momentum",
            },
            {
                "titolo": "📚 Studio Profondo",
                "descrizione": "2 ore su una skill strategica. Telefono spento, nessuna interruzione.",
                "area": Area.CRESCITA,
                "xp": 70,
                "tipo": "momentum",
            },
            {
                "titolo": "💰 Azione Economica",
                "descrizione": "Una sola azione concreta per le finanze: pitch, vendita, investimento o risparmio.",
                "area": Area.FINANZE,
                "xp": 80,
                "tipo": "momentum",
            },
        ]

    def _missioni_breakthrough(self) -> List[Dict]:
        return [
            {
                "titolo": "🔥 La Cosa Difficile",
                "descrizione": "Fai la cosa che rimandi da più tempo. Non quella urgente — quella importante.",
                "area": Area.CRESCITA,
                "xp": 100,
                "tipo": "breakthrough",
            },
            {
                "titolo": "🎁 Contributo Gratuito",
                "descrizione": "Fai qualcosa di concreto che migliora la vita di qualcun altro. Senza chiedere nulla.",
                "area": Area.CONTRIBUTO,
                "xp": 90,
                "tipo": "breakthrough",
            },
            {
                "titolo": "✨ Opera da Condividere",
                "descrizione": "Crea qualcosa che esprima un pensiero autentico e pubblicalo. Un post, un audio, uno sketch.",
                "area": Area.CREATIVITA,
                "xp": 120,
                "tipo": "breakthrough",
            },
        ]
