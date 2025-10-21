"""
MISSIONS CATALOG - Catalogo Completo Missioni Selvagge
40+ missioni suddivise per categoria e difficoltà
"""

from dataclasses import dataclass
from typing import List, Optional

try:
    from .calculator import Area
except ImportError:
    from calculator import Area


@dataclass
class Mission:
    """Definizione di una missione"""
    titolo: str
    descrizione: str
    area_primaria: Area
    area_secondaria: Optional[Area]
    xp_primaria: int
    xp_secondaria: int
    baros: int
    difficolta: str  # "facile", "media", "difficile", "selvaggia"
    categoria: str
    tipo: str  # "recupero", "attivazione", "momentum", "breakthrough"
    restrizioni: Optional[str] = None


class MissionsCatalog:
    """Catalogo completo di tutte le missioni disponibili"""

    # CATEGORIA: FISICA/SALUTE
    FISICA_SALUTE = [
        Mission(
            titolo="💪 Workout Doppio",
            descrizione="Allenamento 2x più lungo del normale. Supera i tuoi limiti.",
            area_primaria=Area.SALUTE_FISICA,
            area_secondaria=None,
            xp_primaria=80,
            xp_secondaria=0,
            baros=40,
            difficolta="media",
            categoria="Fisica/Salute",
            tipo="momentum"
        ),
        Mission(
            titolo="🏃 Corsa 10km",
            descrizione="Corri 10km senza fermarti. Il corpo è tempio.",
            area_primaria=Area.SALUTE_FISICA,
            area_secondaria=Area.SALUTE_MENTALE,
            xp_primaria=120,
            xp_secondaria=30,
            baros=60,
            difficolta="difficile",
            categoria="Fisica/Salute",
            tipo="momentum"
        ),
        Mission(
            titolo="🥗 Zero Zuccheri 7 Giorni",
            descrizione="Una settimana senza zuccheri aggiunti. Solo cibo pulito.",
            area_primaria=Area.SALUTE_FISICA,
            area_secondaria=Area.SALUTE_MENTALE,
            xp_primaria=200,
            xp_secondaria=50,
            baros=100,
            difficolta="selvaggia",
            categoria="Fisica/Salute",
            tipo="breakthrough",
            restrizioni="7 giorni consecutivi"
        ),
        Mission(
            titolo="🧊 Bagno Freddo 5 Minuti",
            descrizione="Immersione completa in acqua fredda per 5 minuti. Wim Hof style.",
            area_primaria=Area.SALUTE_FISICA,
            area_secondaria=Area.SALUTE_MENTALE,
            xp_primaria=100,
            xp_secondaria=50,
            baros=75,
            difficolta="difficile",
            categoria="Fisica/Salute",
            tipo="breakthrough"
        ),
        Mission(
            titolo="💤 Sonno Perfetto 7 Giorni",
            descrizione="7-8h ogni notte per 7 giorni. Traccia qualità.",
            area_primaria=Area.SALUTE_FISICA,
            area_secondaria=None,
            xp_primaria=150,
            xp_secondaria=0,
            baros=75,
            difficolta="media",
            categoria="Fisica/Salute",
            tipo="recupero",
            restrizioni="7 giorni consecutivi"
        ),
        Mission(
            titolo="🚴 100km Bici in Giornata",
            descrizione="Percorri 100km in bicicletta in un singolo giorno.",
            area_primaria=Area.SALUTE_FISICA,
            area_secondaria=Area.SALUTE_MENTALE,
            xp_primaria=250,
            xp_secondaria=50,
            baros=125,
            difficolta="selvaggia",
            categoria="Fisica/Salute",
            tipo="breakthrough"
        ),
    ]

    # CATEGORIA: MENTALE/FOCUS
    MENTALE_FOCUS = [
        Mission(
            titolo="🧘 Meditazione 1 Ora",
            descrizione="Sessione di meditazione continuata per 60 minuti.",
            area_primaria=Area.SALUTE_MENTALE,
            area_secondaria=Area.SPIRITUALE,
            xp_primaria=120,
            xp_secondaria=80,
            baros=100,
            difficolta="difficile",
            categoria="Mentale/Focus",
            tipo="breakthrough"
        ),
        Mission(
            titolo="📵 Digital Detox 24h",
            descrizione="Zero schermi per 24 ore. Solo natura, libri, persone.",
            area_primaria=Area.SALUTE_MENTALE,
            area_secondaria=Area.RELAZIONI,
            xp_primaria=200,
            xp_secondaria=50,
            baros=100,
            difficolta="selvaggia",
            categoria="Mentale/Focus",
            tipo="breakthrough"
        ),
        Mission(
            titolo="📚 Libro Completo in 1 Giorno",
            descrizione="Leggi un intero libro dall'inizio alla fine in 24h.",
            area_primaria=Area.CRESCITA,
            area_secondaria=Area.SALUTE_MENTALE,
            xp_primaria=150,
            xp_secondaria=50,
            baros=75,
            difficolta="difficile",
            categoria="Mentale/Focus",
            tipo="momentum"
        ),
        Mission(
            titolo="🎯 Deep Work 4h Consecutive",
            descrizione="4 ore di lavoro profondo senza interruzioni. Timer prova tutto.",
            area_primaria=Area.CARRIERA,
            area_secondaria=Area.SALUTE_MENTALE,
            xp_primaria=120,
            xp_secondaria=30,
            baros=60,
            difficolta="difficile",
            categoria="Mentale/Focus",
            tipo="momentum"
        ),
        Mission(
            titolo="✍️ Journaling Profondo 90 Min",
            descrizione="Scrittura libera, stream of consciousness per 90 minuti.",
            area_primaria=Area.SALUTE_MENTALE,
            area_secondaria=Area.CRESCITA,
            xp_primaria=100,
            xp_secondaria=30,
            baros=50,
            difficolta="media",
            categoria="Mentale/Focus",
            tipo="attivazione"
        ),
    ]

    # CATEGORIA: PAURA/CRESCITA
    PAURA_CRESCITA = [
        Mission(
            titolo="🎤 Parla in Pubblico",
            descrizione="Fai una presentazione, speech, o intervento pubblico.",
            area_primaria=Area.CRESCITA,
            area_secondaria=Area.CARRIERA,
            xp_primaria=200,
            xp_secondaria=100,
            baros=150,
            difficolta="selvaggia",
            categoria="Paura/Crescita",
            tipo="breakthrough"
        ),
        Mission(
            titolo="💬 Conversazione con Sconosciuto",
            descrizione="Inizia conversazione profonda (10+ min) con persona mai vista prima.",
            area_primaria=Area.RELAZIONI,
            area_secondaria=Area.CRESCITA,
            xp_primaria=80,
            xp_secondaria=40,
            baros=60,
            difficolta="media",
            categoria="Paura/Crescita",
            tipo="attivazione"
        ),
        Mission(
            titolo="📹 Video Pubblico Vulnerabile",
            descrizione="Crea e pubblica video dove mostri vulnerabilità reale.",
            area_primaria=Area.CREATIVITA,
            area_secondaria=Area.CRESCITA,
            xp_primaria=250,
            xp_secondaria=100,
            baros=150,
            difficolta="selvaggia",
            categoria="Paura/Crescita",
            tipo="breakthrough"
        ),
        Mission(
            titolo="📞 Chiamata Difficile",
            descrizione="Quella telefonata che rimandi da settimane. Falla oggi.",
            area_primaria=Area.RELAZIONI,
            area_secondaria=Area.SALUTE_MENTALE,
            xp_primaria=150,
            xp_secondaria=50,
            baros=75,
            difficolta="difficile",
            categoria="Paura/Crescita",
            tipo="breakthrough"
        ),
        Mission(
            titolo="🙅 Rejection Therapy",
            descrizione="Chiedi qualcosa sapendo che diranno no. Pratica il rifiuto.",
            area_primaria=Area.CRESCITA,
            area_secondaria=Area.SALUTE_MENTALE,
            xp_primaria=100,
            xp_secondaria=50,
            baros=50,
            difficolta="media",
            categoria="Paura/Crescita",
            tipo="attivazione"
        ),
        Mission(
            titolo="💔 Perdona Qualcuno",
            descrizione="Perdona attivamente persona che ti ha ferito. Libera il peso.",
            area_primaria=Area.SALUTE_MENTALE,
            area_secondaria=Area.SPIRITUALE,
            xp_primaria=200,
            xp_secondaria=100,
            baros=150,
            difficolta="selvaggia",
            categoria="Paura/Crescita",
            tipo="breakthrough"
        ),
    ]

    # CATEGORIA: PRODUTTIVITÀ ESTREMA
    PRODUTTIVITA_ESTREMA = [
        Mission(
            titolo="🚀 24h Maker",
            descrizione="Dall'idea al prodotto finito in 24h. Ship something.",
            area_primaria=Area.CARRIERA,
            area_secondaria=Area.CREATIVITA,
            xp_primaria=400,
            xp_secondaria=200,
            baros=250,
            difficolta="selvaggia",
            categoria="Produttività Estrema",
            tipo="breakthrough"
        ),
        Mission(
            titolo="📧 Inbox Zero + Desktop Zero",
            descrizione="Email inbox a zero + desktop completamente pulito.",
            area_primaria=Area.CARRIERA,
            area_secondaria=Area.SALUTE_MENTALE,
            xp_primaria=120,
            xp_secondaria=30,
            baros=60,
            difficolta="media",
            categoria="Produttività Estrema",
            tipo="momentum"
        ),
        Mission(
            titolo="⚙️ Sistema Completo",
            descrizione="Crea sistema/processo per automatizzare qualcosa nella tua vita.",
            area_primaria=Area.CARRIERA,
            area_secondaria=Area.CRESCITA,
            xp_primaria=200,
            xp_secondaria=50,
            baros=100,
            difficolta="difficile",
            categoria="Produttività Estrema",
            tipo="momentum"
        ),
        Mission(
            titolo="💡 100 Idee in 1 Ora",
            descrizione="Sprint creativo: genera 100 idee su un problema/progetto.",
            area_primaria=Area.CREATIVITA,
            area_secondaria=Area.CARRIERA,
            xp_primaria=150,
            xp_secondaria=50,
            baros=75,
            difficolta="difficile",
            categoria="Produttività Estrema",
            tipo="breakthrough"
        ),
        Mission(
            titolo="📊 Deep Work Marathon 8h",
            descrizione="8 ore lavoro profondo in un giorno. Massima produttività.",
            area_primaria=Area.CARRIERA,
            area_secondaria=Area.SALUTE_MENTALE,
            xp_primaria=300,
            xp_secondaria=50,
            baros=150,
            difficolta="selvaggia",
            categoria="Produttività Estrema",
            tipo="momentum"
        ),
        Mission(
            titolo="📝 Content Batch 10x",
            descrizione="Crea 10 pezzi di contenuto in una sessione (post, video, articoli).",
            area_primaria=Area.CREATIVITA,
            area_secondaria=Area.CARRIERA,
            xp_primaria=250,
            xp_secondaria=100,
            baros=125,
            difficolta="selvaggia",
            categoria="Produttività Estrema",
            tipo="breakthrough"
        ),
    ]

    # CATEGORIA: BENESSERE ESTREMO
    BENESSERE_ESTREMO = [
        Mission(
            titolo="🌿 Detox Totale 24h",
            descrizione="Solo acqua, meditazione, natura per 24 ore.",
            area_primaria=Area.SALUTE_FISICA,
            area_secondaria=Area.SPIRITUALE,
            xp_primaria=250,
            xp_secondaria=100,
            baros=125,
            difficolta="selvaggia",
            categoria="Benessere Estremo",
            tipo="recupero"
        ),
        Mission(
            titolo="💆 Spa Day Self-Care",
            descrizione="4 ore dedicate esclusivamente a cura di sé.",
            area_primaria=Area.SALUTE_FISICA,
            area_secondaria=Area.SALUTE_MENTALE,
            xp_primaria=150,
            xp_secondaria=50,
            baros=75,
            difficolta="media",
            categoria="Benessere Estremo",
            tipo="recupero"
        ),
        Mission(
            titolo="😴 Sleep Optimization",
            descrizione="10h sonno + ambiente perfetto (buio totale, temperatura ideale).",
            area_primaria=Area.SALUTE_FISICA,
            area_secondaria=None,
            xp_primaria=100,
            xp_secondaria=0,
            baros=50,
            difficolta="media",
            categoria="Benessere Estremo",
            tipo="recupero"
        ),
        Mission(
            titolo="🔥 Sauna + Bagno Freddo Ciclo",
            descrizione="Ciclo completo: Sauna 20min → Bagno freddo 5min → ripeti 3x.",
            area_primaria=Area.SALUTE_FISICA,
            area_secondaria=Area.SALUTE_MENTALE,
            xp_primaria=180,
            xp_secondaria=40,
            baros=90,
            difficolta="difficile",
            categoria="Benessere Estremo",
            tipo="breakthrough"
        ),
        Mission(
            titolo="🥑 Alimentazione Perfetta 3 Giorni",
            descrizione="3 giorni dove ogni macro è calcolato perfettamente.",
            area_primaria=Area.SALUTE_FISICA,
            area_secondaria=None,
            xp_primaria=200,
            xp_secondaria=0,
            baros=100,
            difficolta="difficile",
            categoria="Benessere Estremo",
            tipo="momentum",
            restrizioni="3 giorni consecutivi"
        ),
    ]

    # CATEGORIA: SOCIALE/RELAZIONI
    SOCIALE_RELAZIONI = [
        Mission(
            titolo="❤️ Giornata Qualità con Partner",
            descrizione="8+ ore dedicate solo a persona amata. Zero telefono.",
            area_primaria=Area.RELAZIONI,
            area_secondaria=None,
            xp_primaria=150,
            xp_secondaria=0,
            baros=75,
            difficolta="media",
            categoria="Sociale/Relazioni",
            tipo="attivazione"
        ),
        Mission(
            titolo="👨‍👩‍👧 Chiamata Famiglia Profonda",
            descrizione="Chiamata 1h+ con familiare. Conversazione vera, non superficiale.",
            area_primaria=Area.RELAZIONI,
            area_secondaria=Area.SALUTE_MENTALE,
            xp_primaria=100,
            xp_secondaria=30,
            baros=50,
            difficolta="media",
            categoria="Sociale/Relazioni",
            tipo="attivazione"
        ),
        Mission(
            titolo="🎉 Organizza Evento Sociale",
            descrizione="Crea e organizza evento per 5+ amici (cena, escursione, etc).",
            area_primaria=Area.RELAZIONI,
            area_secondaria=Area.CREATIVITA,
            xp_primaria=200,
            xp_secondaria=50,
            baros=100,
            difficolta="difficile",
            categoria="Sociale/Relazioni",
            tipo="breakthrough"
        ),
        Mission(
            titolo="💌 Lettera Gratitudine",
            descrizione="Scrivi e invia lettera di gratitudine a qualcuno importante.",
            area_primaria=Area.RELAZIONI,
            area_secondaria=Area.SALUTE_MENTALE,
            xp_primaria=120,
            xp_secondaria=40,
            baros=60,
            difficolta="media",
            categoria="Sociale/Relazioni",
            tipo="attivazione"
        ),
        Mission(
            titolo="🤝 Riconciliazione",
            descrizione="Riconnetti con persona con cui hai perso contatto.",
            area_primaria=Area.RELAZIONI,
            area_secondaria=Area.CRESCITA,
            xp_primaria=180,
            xp_secondaria=60,
            baros=90,
            difficolta="difficile",
            categoria="Sociale/Relazioni",
            tipo="breakthrough"
        ),
    ]

    # CATEGORIA: SPIRITUALE/TRASCENDENZA
    SPIRITUALE_TRASCENDENZA = [
        Mission(
            titolo="🙏 Pratica Spirituale Quotidiana 7 Giorni",
            descrizione="7 giorni consecutivi di pratica spirituale (meditazione/preghiera/yoga).",
            area_primaria=Area.SPIRITUALE,
            area_secondaria=Area.SALUTE_MENTALE,
            xp_primaria=200,
            xp_secondaria=100,
            baros=150,
            difficolta="difficile",
            categoria="Spirituale/Trascendenza",
            tipo="momentum",
            restrizioni="7 giorni consecutivi"
        ),
        Mission(
            titolo="🌅 Alba in Natura",
            descrizione="Svegliati all'alba e passa 2h in natura in silenzio.",
            area_primaria=Area.SPIRITUALE,
            area_secondaria=Area.SALUTE_FISICA,
            xp_primaria=120,
            xp_secondaria=30,
            baros=60,
            difficolta="media",
            categoria="Spirituale/Trascendenza",
            tipo="attivazione"
        ),
        Mission(
            titolo="📿 Ritiro Silenzio 24h",
            descrizione="24 ore in completo silenzio. Zero parole.",
            area_primaria=Area.SPIRITUALE,
            area_secondaria=Area.SALUTE_MENTALE,
            xp_primaria=300,
            xp_secondaria=100,
            baros=200,
            difficolta="selvaggia",
            categoria="Spirituale/Trascendenza",
            tipo="breakthrough"
        ),
        Mission(
            titolo="🔮 Visioning Session 3h",
            descrizione="3 ore dedicate a visualizzazione e connessione con futuro ideale.",
            area_primaria=Area.SPIRITUALE,
            area_secondaria=Area.CRESCITA,
            xp_primaria=150,
            xp_secondaria=50,
            baros=75,
            difficolta="media",
            categoria="Spirituale/Trascendenza",
            tipo="breakthrough"
        ),
    ]

    # CATEGORIA: CREATIVITÀ/ESPRESSIONE
    CREATIVITA_ESPRESSIONE = [
        Mission(
            titolo="🎨 Crea Opera Completa",
            descrizione="Crea un'opera artistica completa in 48h (pittura, musica, video, etc).",
            area_primaria=Area.CREATIVITA,
            area_secondaria=Area.SALUTE_MENTALE,
            xp_primaria=250,
            xp_secondaria=50,
            baros=125,
            difficolta="selvaggia",
            categoria="Creatività/Espressione",
            tipo="breakthrough"
        ),
        Mission(
            titolo="✍️ Scrivi Articolo 2000+ Parole",
            descrizione="Articolo completo e pubblicato su tema che ti appassiona.",
            area_primaria=Area.CREATIVITA,
            area_secondaria=Area.CRESCITA,
            xp_primaria=150,
            xp_secondaria=50,
            baros=75,
            difficolta="difficile",
            categoria="Creatività/Espressione",
            tipo="momentum"
        ),
        Mission(
            titolo="🎵 Impara Nuova Skill Creativa",
            descrizione="Dedica 5h ad apprendere completamente nuova skill creativa.",
            area_primaria=Area.CREATIVITA,
            area_secondaria=Area.CRESCITA,
            xp_primaria=200,
            xp_secondaria=100,
            baros=100,
            difficolta="difficile",
            categoria="Creatività/Espressione",
            tipo="attivazione"
        ),
        Mission(
            titolo="📸 Progetto Fotografico 100 Foto",
            descrizione="Scatta 100 foto su un tema in un giorno. Cura e pubblica le migliori 10.",
            area_primaria=Area.CREATIVITA,
            area_secondaria=None,
            xp_primaria=180,
            xp_secondaria=0,
            baros=90,
            difficolta="difficile",
            categoria="Creatività/Espressione",
            tipo="breakthrough"
        ),
    ]

    # CATEGORIA: FINANZE/ABBONDANZA
    FINANZE_ABBONDANZA = [
        Mission(
            titolo="💰 Genera €100 in 24h",
            descrizione="Crea €100 extra in 24h con side hustle/vendita/servizio.",
            area_primaria=Area.FINANZE,
            area_secondaria=Area.CARRIERA,
            xp_primaria=250,
            xp_secondaria=100,
            baros=150,
            difficolta="selvaggia",
            categoria="Finanze/Abbondanza",
            tipo="breakthrough"
        ),
        Mission(
            titolo="📊 Budgeting Completo",
            descrizione="Crea budget dettagliato e tracking spese per 30 giorni.",
            area_primaria=Area.FINANZE,
            area_secondaria=None,
            xp_primaria=150,
            xp_secondaria=0,
            baros=75,
            difficolta="media",
            categoria="Finanze/Abbondanza",
            tipo="momentum"
        ),
        Mission(
            titolo="📚 Financial Education 10h",
            descrizione="10 ore dedicate a educazione finanziaria (libri, corsi, podcast).",
            area_primaria=Area.FINANZE,
            area_secondaria=Area.CRESCITA,
            xp_primaria=200,
            xp_secondaria=50,
            baros=100,
            difficolta="difficile",
            categoria="Finanze/Abbondanza",
            tipo="attivazione"
        ),
        Mission(
            titolo="💎 Investimento Consapevole",
            descrizione="Ricerca e fai primo investimento consapevole (azioni, crypto, etc).",
            area_primaria=Area.FINANZE,
            area_secondaria=Area.CRESCITA,
            xp_primaria=180,
            xp_secondaria=40,
            baros=90,
            difficolta="difficile",
            categoria="Finanze/Abbondanza",
            tipo="breakthrough"
        ),
    ]

    @classmethod
    def get_all_missions(cls) -> List[Mission]:
        """Ritorna tutte le missioni disponibili"""
        return (
            cls.FISICA_SALUTE +
            cls.MENTALE_FOCUS +
            cls.PAURA_CRESCITA +
            cls.PRODUTTIVITA_ESTREMA +
            cls.BENESSERE_ESTREMO +
            cls.SOCIALE_RELAZIONI +
            cls.SPIRITUALE_TRASCENDENZA +
            cls.CREATIVITA_ESPRESSIONE +
            cls.FINANZE_ABBONDANZA
        )

    @classmethod
    def get_by_categoria(cls, categoria: str) -> List[Mission]:
        """Ottieni missioni per categoria"""
        mapping = {
            "Fisica/Salute": cls.FISICA_SALUTE,
            "Mentale/Focus": cls.MENTALE_FOCUS,
            "Paura/Crescita": cls.PAURA_CRESCITA,
            "Produttività Estrema": cls.PRODUTTIVITA_ESTREMA,
            "Benessere Estremo": cls.BENESSERE_ESTREMO,
            "Sociale/Relazioni": cls.SOCIALE_RELAZIONI,
            "Spirituale/Trascendenza": cls.SPIRITUALE_TRASCENDENZA,
            "Creatività/Espressione": cls.CREATIVITA_ESPRESSIONE,
            "Finanze/Abbondanza": cls.FINANZE_ABBONDANZA,
        }
        return mapping.get(categoria, [])

    @classmethod
    def get_by_difficolta(cls, difficolta: str) -> List[Mission]:
        """Ottieni missioni per difficoltà"""
        all_missions = cls.get_all_missions()
        return [m for m in all_missions if m.difficolta == difficolta]

    @classmethod
    def get_by_tipo(cls, tipo: str) -> List[Mission]:
        """Ottieni missioni per tipo"""
        all_missions = cls.get_all_missions()
        return [m for m in all_missions if m.tipo == tipo]

    @classmethod
    def get_random_missions(cls, n: int = 3, difficolta: str = None) -> List[Mission]:
        """Ottieni N missioni casuali"""
        import random

        if difficolta:
            pool = cls.get_by_difficolta(difficolta)
        else:
            pool = cls.get_all_missions()

        return random.sample(pool, min(n, len(pool)))


# Test
if __name__ == "__main__":
    print("=== CATALOGO MISSIONI LGAI ===\n")

    all_missions = MissionsCatalog.get_all_missions()
    print(f"📊 Totale Missioni: {len(all_missions)}\n")

    # Per categoria
    print("📋 PER CATEGORIA:")
    for cat in ["Fisica/Salute", "Paura/Crescita", "Produttività Estrema"]:
        missions = MissionsCatalog.get_by_categoria(cat)
        print(f"   {cat}: {len(missions)} missioni")

    print("\n📋 PER DIFFICOLTÀ:")
    for diff in ["facile", "media", "difficile", "selvaggia"]:
        missions = MissionsCatalog.get_by_difficolta(diff)
        print(f"   {diff.capitalize()}: {len(missions)} missioni")

    print("\n🎯 ESEMPIO 3 MISSIONI CASUALI:")
    random_missions = MissionsCatalog.get_random_missions(3)
    for i, m in enumerate(random_missions, 1):
        print(f"\n{i}. {m.titolo}")
        print(f"   {m.descrizione}")
        print(f"   Reward: {m.xp_primaria} XP ({m.area_primaria.value}) + {m.baros} Baros")
        print(f"   Difficoltà: {m.difficolta}")
