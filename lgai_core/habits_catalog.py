"""
HABITS CATALOG - Catalogo Abitudini Positive e Negative
Sistema di tracciamento dettagliato delle abitudini quotidiane
"""

from dataclasses import dataclass
from typing import List, Optional
try:
    from .calculator import Area
except ImportError:
    from calculator import Area


@dataclass
class Habit:
    """Definizione di un'abitudine"""
    id: int
    nome: str
    tipo: str  # "positive" o "negative"
    area: Area
    pv_delta: int  # Quanto impatta sui PV
    descrizione: str
    icona: str


class HabitsCatalog:
    """
    Catalogo completo di 40 abitudini tracciabili
    20 Positive + 20 Negative
    """

    # ==================== ABITUDINI POSITIVE ====================

    POSITIVE = [
        # SALUTE FISICA (5 abitudini)
        Habit(1, "Workout/Palestra", "positive", Area.SALUTE_FISICA, 15,
              "Allenamento fisico 30+ minuti", "💪"),
        Habit(2, "Corsa/Cardio", "positive", Area.SALUTE_FISICA, 15,
              "Attività cardio 20+ minuti", "🏃"),
        Habit(3, "Camminata 10k passi", "positive", Area.SALUTE_FISICA, 10,
              "Almeno 10.000 passi", "🚶"),
        Habit(4, "Cibo Sano", "positive", Area.SALUTE_FISICA, 10,
              "Pasti nutrienti, no junk food", "🥗"),
        Habit(5, "Sonno 7+ ore", "positive", Area.SALUTE_FISICA, 15,
              "Almeno 7 ore di sonno qualità", "😴"),

        # SALUTE MENTALE (4 abitudini)
        Habit(6, "Meditazione", "positive", Area.SALUTE_MENTALE, 15,
              "Pratica meditativa 10+ minuti", "🧘"),
        Habit(7, "Journaling", "positive", Area.SALUTE_MENTALE, 10,
              "Scrittura riflessiva/diario", "📝"),
        Habit(8, "Terapia/Coaching", "positive", Area.SALUTE_MENTALE, 20,
              "Sessione con professionista", "🧠"),
        Habit(9, "Tempo Natura", "positive", Area.SALUTE_MENTALE, 10,
              "Almeno 30min all'aperto", "🌳"),

        # RELAZIONI (3 abitudini)
        Habit(10, "Chiamata Famiglia", "positive", Area.RELAZIONI, 10,
              "Contatto significativo con famiglia", "👨‍👩‍👧"),
        Habit(11, "Tempo Qualità Partner", "positive", Area.RELAZIONI, 15,
              "Momento di connessione profonda", "💑"),
        Habit(12, "Socializzazione", "positive", Area.RELAZIONI, 10,
              "Uscita/incontro con amici", "👥"),

        # CRESCITA (4 abitudini)
        Habit(13, "Lettura 30min", "positive", Area.CRESCITA, 10,
              "Libro di crescita/conoscenza", "📚"),
        Habit(14, "Corso Online", "positive", Area.CRESCITA, 15,
              "Lezione/modulo completato", "🎓"),
        Habit(15, "Podcast Educativo", "positive", Area.CRESCITA, 8,
              "Ascolto contenuto formativo", "🎧"),
        Habit(16, "Nuova Skill", "positive", Area.CRESCITA, 15,
              "Pratica abilità che stai imparando", "🎯"),

        # CREATIVITÀ (2 abitudini)
        Habit(17, "Progetto Creativo", "positive", Area.CREATIVITA, 15,
              "Lavoro su progetto personale", "🎨"),
        Habit(18, "Scrittura Creativa", "positive", Area.CREATIVITA, 10,
              "500+ parole originali", "✍️"),

        # FINANZE (2 abitudini)
        Habit(19, "Budget Review", "positive", Area.FINANZE, 10,
              "Controllo spese/entrate", "💰"),
        Habit(20, "Side Income Work", "positive", Area.FINANZE, 15,
              "Lavoro su entrate extra", "💵"),

        # CONTRIBUTO (2 abitudini)
        Habit(21, "Aiuto agli Altri", "positive", Area.CONTRIBUTO, 15,
              "Azione concreta di aiuto", "🤝"),
        Habit(22, "Contenuto Pubblicato", "positive", Area.CONTRIBUTO, 10,
              "Post/video/articolo condiviso", "📢"),

        # SPIRITUALE (2 abitudini)
        Habit(23, "Pratica Spirituale", "positive", Area.SPIRITUALE, 15,
              "Preghiera/rituale/connessione", "🙏"),
        Habit(24, "Gratitudine", "positive", Area.SPIRITUALE, 10,
              "Lista 3+ cose per cui sei grato", "✨"),

        # CARRIERA (2 abitudini)
        Habit(25, "Deep Work 2h", "positive", Area.CARRIERA, 20,
              "Focus profondo su lavoro importante", "🚀"),
        Habit(26, "Networking", "positive", Area.CARRIERA, 10,
              "Connessione professionale", "🌐"),
    ]

    # ==================== ABITUDINI NEGATIVE ====================

    NEGATIVE = [
        # SALUTE FISICA (4 abitudini)
        Habit(101, "Junk Food", "negative", Area.SALUTE_FISICA, -15,
              "Fast food, snack, dolci eccessivi", "🍔"),
        Habit(102, "Fumo/Alcol Eccessivo", "negative", Area.SALUTE_FISICA, -20,
              "Sigarette o alcol oltre limite", "🚬"),
        Habit(103, "Sedentarietà", "negative", Area.SALUTE_FISICA, -10,
              "Zero movimento, tutto il giorno seduto", "🛋️"),
        Habit(104, "Sonno <5 ore", "negative", Area.SALUTE_FISICA, -15,
              "Dormito meno di 5 ore", "😵"),

        # SALUTE MENTALE (4 abitudini)
        Habit(105, "Overthinking/Ansia", "negative", Area.SALUTE_MENTALE, -10,
              "Ore in loop mentale negativo", "😰"),
        Habit(106, "Auto-Critica Eccessiva", "negative", Area.SALUTE_MENTALE, -10,
              "Dialogo interno distruttivo", "😔"),
        Habit(107, "Evitare Emozioni", "negative", Area.SALUTE_MENTALE, -8,
              "Reprimere/ignorare sentimenti", "🙈"),
        Habit(108, "Notizie Negative Binge", "negative", Area.SALUTE_MENTALE, -8,
              "Consumo eccessivo notizie negative", "📰"),

        # RELAZIONI (3 abitudini)
        Habit(109, "Conflitto non Risolto", "negative", Area.RELAZIONI, -15,
              "Litigio/tensione con persona cara", "⚡"),
        Habit(110, "Isolamento", "negative", Area.RELAZIONI, -10,
              "Evitare contatti sociali", "🚪"),
        Habit(111, "Comunicazione Passivo-Aggressiva", "negative", Area.RELAZIONI, -8,
              "Comportamento tossico in relazione", "😒"),

        # CRESCITA (2 abitudini)
        Habit(112, "Procrastinazione", "negative", Area.CRESCITA, -15,
              "Rimandare task importanti", "⏰"),
        Habit(113, "Contenuto Passivo", "negative", Area.CRESCITA, -8,
              "3+ ore TV/video senza apprendere", "📺"),

        # CREATIVITÀ (1 abitudine)
        Habit(114, "Blocco Creativo", "negative", Area.CREATIVITA, -10,
              "Non lavorare su progetti per pigrizia", "🚫"),

        # FINANZE (2 abitudini)
        Habit(115, "Spesa Impulsiva", "negative", Area.FINANZE, -15,
              "Acquisto non pianificato >€50", "💸"),
        Habit(116, "Ignorare Budget", "negative", Area.FINANZE, -10,
              "Spendere senza controllo", "🙈"),

        # CONTRIBUTO (1 abitudine)
        Habit(117, "Egoismo/Indifferenza", "negative", Area.CONTRIBUTO, -10,
              "Rifiutare aiuto quando potevi darlo", "🚫"),

        # SPIRITUALE (1 abitudine)
        Habit(118, "Negatività/Cinismo", "negative", Area.SPIRITUALE, -10,
              "Giudizio, critica, pessimismo", "☁️"),

        # CARRIERA (2 abitudini)
        Habit(119, "Distrazioni Lavoro", "negative", Area.CARRIERA, -15,
              "Social/YouTube durante lavoro importante", "📱"),
        Habit(120, "Burnout Push", "negative", Area.CARRIERA, -20,
              "Lavorare oltre limite sano (>12h)", "🔥"),
    ]

    @classmethod
    def get_all_positive(cls) -> List[Habit]:
        """Tutte le abitudini positive"""
        return cls.POSITIVE

    @classmethod
    def get_all_negative(cls) -> List[Habit]:
        """Tutte le abitudini negative"""
        return cls.NEGATIVE

    @classmethod
    def get_by_area(cls, area: Area, tipo: str = "positive") -> List[Habit]:
        """Abitudini per area specifica"""
        source = cls.POSITIVE if tipo == "positive" else cls.NEGATIVE
        return [h for h in source if h.area == area]

    @classmethod
    def get_by_id(cls, habit_id: int) -> Optional[Habit]:
        """Trova abitudine per ID"""
        all_habits = cls.POSITIVE + cls.NEGATIVE
        for habit in all_habits:
            if habit.id == habit_id:
                return habit
        return None

    @classmethod
    def search(cls, query: str, tipo: Optional[str] = None) -> List[Habit]:
        """Cerca abitudini per nome"""
        query = query.lower()
        source = []
        if tipo == "positive":
            source = cls.POSITIVE
        elif tipo == "negative":
            source = cls.NEGATIVE
        else:
            source = cls.POSITIVE + cls.NEGATIVE

        return [h for h in source if query in h.nome.lower() or query in h.descrizione.lower()]

    @classmethod
    def calculate_pv_impact(cls, positive_ids: List[int], negative_ids: List[int]) -> dict:
        """Calcola impatto PV totale dalle abitudini"""
        positive_delta = 0
        negative_delta = 0

        for pid in positive_ids:
            habit = cls.get_by_id(pid)
            if habit:
                positive_delta += habit.pv_delta

        for nid in negative_ids:
            habit = cls.get_by_id(nid)
            if habit:
                negative_delta += habit.pv_delta  # È già negativo

        # Bonus Perfect Day (0 negative + almeno 5-6 positive)
        bonus = 20 if len(negative_ids) == 0 and positive_delta >= 70 else 0

        return {
            'positive_delta': positive_delta,
            'negative_delta': negative_delta,
            'bonus': bonus,
            'total_delta': positive_delta + negative_delta + bonus
        }


# Test
if __name__ == "__main__":
    print("=== HABITS CATALOG ===\n")

    print("📈 ABITUDINI POSITIVE:")
    print(f"   Totale: {len(HabitsCatalog.POSITIVE)}")
    print("\n   Top 5:")
    for h in HabitsCatalog.POSITIVE[:5]:
        print(f"   {h.icona} {h.id}. {h.nome} ({h.area.value}) +{h.pv_delta} PV")

    print("\n📉 ABITUDINI NEGATIVE:")
    print(f"   Totale: {len(HabitsCatalog.NEGATIVE)}")
    print("\n   Top 5:")
    for h in HabitsCatalog.NEGATIVE[:5]:
        print(f"   {h.icona} {h.id}. {h.nome} ({h.area.value}) {h.pv_delta} PV")

    print("\n🔍 TEST CALCOLO IMPATTO:")
    # Esempio: 3 positive (workout, meditazione, lettura) - 1 negative (junk food)
    impact = HabitsCatalog.calculate_pv_impact([1, 6, 13], [101])
    print(f"   Positive: +{impact['positive_delta']} PV")
    print(f"   Negative: {impact['negative_delta']} PV")
    print(f"   Bonus: +{impact['bonus']} PV")
    print(f"   TOTALE: {impact['total_delta']:+d} PV")

    print("\n✅ Sistema completo! Ora puoi tracciare abitudini specifiche.")
