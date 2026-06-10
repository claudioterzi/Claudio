"""
LIBRO ORACOLO - Il Libro delle Rivelazioni
22 Carte della Trasformazione per il sistema LGAI

Consulta il libro per ricevere saggezza contestuale
basata sul tuo stato attuale nel gioco della vita.
"""

from dataclasses import dataclass
from typing import List, Optional
from .calculator import PlayerStats, Zona, Area, LGAICalculator
import hashlib


@dataclass
class CartaOracolo:
    """Una carta del Libro Oracolo"""
    numero: int          # 0-21
    simbolo: str         # Numero romano
    titolo: str
    archetipo: str
    oracolo: str         # Messaggio principale
    riflessione: str     # Domanda per l'anima
    azione: str          # Azione concreta suggerita
    zona_afficne: Optional[Zona] = None  # Zona a cui questa carta risuona di più


# Le 22 Carte del Libro Oracolo
CARTE: List[CartaOracolo] = [
    CartaOracolo(
        numero=0, simbolo="0", titolo="Il Viaggio", archetipo="Il Folle Sacro",
        oracolo=(
            "Sei al punto zero. Non il nulla — il POTENZIALE PURO.\n"
            "Prima di ogni grande trasformazione c'è il vuoto fertile.\n"
            "Non hai bisogno di sapere dove stai andando.\n"
            "Hai solo bisogno di fare il PRIMO PASSO."
        ),
        riflessione="Cosa stai rimandando per paura di sbagliare?",
        azione="Fai oggi UNA cosa che non hai mai fatto prima. Piccola o grande — non importa.",
        zona_afficne=None
    ),
    CartaOracolo(
        numero=1, simbolo="I", titolo="Il Guerriero", archetipo="La Volontà Pura",
        oracolo=(
            "La forza non è assenza di paura.\n"
            "È agire NONOSTANTE la paura.\n"
            "Il guerriero dentro di te sa già cosa fare.\n"
            "Smetti di pensare. AGISCI."
        ),
        riflessione="In quale area della tua vita stai cedendo invece di combattere?",
        azione="Identifica la sfida che stai evitando. Affrontala entro 24 ore.",
        zona_afficne=Zona.CRESCITA
    ),
    CartaOracolo(
        numero=2, simbolo="II", titolo="La Sacerdotessa", archetipo="La Saggezza Interiore",
        oracolo=(
            "La risposta che cerchi non è fuori.\n"
            "È già in te, sepolta sotto il rumore del mondo.\n"
            "Fai silenzio. Ascolta la voce che parla\n"
            "quando smetti di fare domande."
        ),
        riflessione="Cosa sai già, ma non vuoi ammettere?",
        azione="10 minuti di silenzio totale. Niente telefono, niente musica. Solo tu.",
        zona_afficne=Zona.TRASFORMAZIONE
    ),
    CartaOracolo(
        numero=3, simbolo="III", titolo="La Madre", archetipo="La Crescita Naturale",
        oracolo=(
            "La crescita non si forza — si nutre.\n"
            "Come un giardino, hai bisogno di acqua, luce e tempo.\n"
            "Stai trattando il tuo corpo e la tua mente\n"
            "con la cura che meritano?"
        ),
        riflessione="Cosa stai trascurando che ha bisogno di attenzione amorevole?",
        azione="Fai un gesto di cura autentica verso te stesso oggi. Non produttività — CURA.",
        zona_afficne=Zona.STAGNAZIONE
    ),
    CartaOracolo(
        numero=4, simbolo="IV", titolo="Il Re", archetipo="La Disciplina Sovrana",
        oracolo=(
            "I re non aspettano di sentirsi motivati.\n"
            "Agiscono perché SANNO che l'azione crea energia.\n"
            "La disciplina è la forma più alta di rispetto verso te stesso.\n"
            "Regna sulla tua giornata prima che sia lei a regnare su di te."
        ),
        riflessione="In quale aspetto della tua vita stai abdicando al tuo trono?",
        azione="Stabilisci UNA regola non negoziabile per questa settimana. Seguila senza eccezioni.",
        zona_afficne=Zona.CRESCITA
    ),
    CartaOracolo(
        numero=5, simbolo="V", titolo="Il Saggio", archetipo="La Conoscenza Applicata",
        oracolo=(
            "Sapere non è abbastanza. Capire non è abbastanza.\n"
            "La saggezza è conoscenza vissuta nel corpo,\n"
            "testata nel fuoco dell'esperienza reale.\n"
            "Qual è la lezione che stai imparando attraverso questo momento?"
        ),
        riflessione="Cosa ti sta insegnando la tua situazione attuale che nessun libro potrebbe?",
        azione="Scrivi 3 lezioni che hai imparato negli ultimi 30 giorni. Cosa cambi?",
        zona_afficne=None
    ),
    CartaOracolo(
        numero=6, simbolo="VI", titolo="L'Amante", archetipo="La Connessione Sacra",
        oracolo=(
            "Sei fatto per connetterti.\n"
            "Ogni relazione è uno specchio che mostra parti di te\n"
            "che non potresti vedere da solo.\n"
            "Chi hai trascurato? Chi ti manca?"
        ),
        riflessione="Stai nutrendo le relazioni che contano davvero, o solo quelle convenienti?",
        azione="Contatta oggi qualcuno che ami e di cui non senti da troppo tempo.",
        zona_afficne=None
    ),
    CartaOracolo(
        numero=7, simbolo="VII", titolo="Il Carro", archetipo="Il Momentum Inarrestabile",
        oracolo=(
            "Hai mosso qualcosa. Il momentum è tuo.\n"
            "Non sprecarlo con distrazioni e dubbi.\n"
            "Quando il carro è in movimento, ogni ostacolo diventa carburante.\n"
            "Mantieni la direzione. ACCELERA."
        ),
        riflessione="Cosa sta funzionando adesso che devi proteggere e amplificare?",
        azione="Identifica il tuo prossimo obiettivo specifico. Fissa la data. Inizia oggi.",
        zona_afficne=Zona.CRESCITA
    ),
    CartaOracolo(
        numero=8, simbolo="VIII", titolo="La Forza", archetipo="Il Coraggio Silenzioso",
        oracolo=(
            "La vera forza non urla.\n"
            "Si siede accanto alla paura, la guarda negli occhi,\n"
            "e poi agisce comunque.\n"
            "La tua forza è più grande di quello che credi."
        ),
        riflessione="Dove stai confondendo paura con incapacità?",
        azione="Fai una cosa spaventosa oggi. Senti la paura — poi falla comunque.",
        zona_afficne=Zona.SOPRAVVIVENZA
    ),
    CartaOracolo(
        numero=9, simbolo="IX", titolo="L'Eremita", archetipo="La Luce Interiore",
        oracolo=(
            "Non tutte le battaglie si vincono cercando più input.\n"
            "A volte devi isolarti dal rumore esterno\n"
            "per sentire cosa sta davvero succedendo dentro di te.\n"
            "La solitudine non è solitudine — è un incontro con te stesso."
        ),
        riflessione="Stai cercando risposte fuori quando la risposta è già dentro?",
        azione="Passa 1 ora completamente solo e offline. Nessun input. Cosa emerge?",
        zona_afficne=None
    ),
    CartaOracolo(
        numero=10, simbolo="X", titolo="La Ruota", archetipo="I Cicli Eterni",
        oracolo=(
            "Tutto cambia. Sempre.\n"
            "Le zone alte non durano — e nemmeno quelle basse.\n"
            "Sei in un ciclo. Non combatterlo.\n"
            "Impara a muoverti CON la ruota, non contro di essa."
        ),
        riflessione="Stai resistendo a un cambiamento che la vita vuole portarti?",
        azione="Identifica un pattern che si ripete nella tua vita. Cosa vuole insegnarti?",
        zona_afficne=None
    ),
    CartaOracolo(
        numero=11, simbolo="XI", titolo="La Giustizia", archetipo="L'Equilibrio Cosmico",
        oracolo=(
            "Ogni azione ha conseguenze. Ogni scelta crea realtà.\n"
            "Non è punizione — è precisione.\n"
            "Il tuo stato attuale è lo specchio esatto delle tue abitudini passate.\n"
            "E le tue abitudini presenti creano il tuo futuro."
        ),
        riflessione="Sei disposto a essere onesto su come le tue scelte hanno creato la situazione attuale?",
        azione="Fai un inventario: quali abitudini ti stanno portando dove vuoi andare? Quali no?",
        zona_afficne=None
    ),
    CartaOracolo(
        numero=12, simbolo="XII", titolo="L'Appeso", archetipo="La Resa Sacra",
        oracolo=(
            "A volte la soluzione è smettere di lottare.\n"
            "Non cedere — CEDERE IL CONTROLLO.\n"
            "Quando sei appeso a testa in giù, il mondo sembra diverso.\n"
            "Forse hai bisogno di una prospettiva completamente nuova."
        ),
        riflessione="Cosa succederebbe se smettessi di controllare e ti fidassI del processo?",
        azione="Lascia andare UNA cosa che stai cercando di controllare e non puoi. Osserva.",
        zona_afficne=Zona.SOPRAVVIVENZA
    ),
    CartaOracolo(
        numero=13, simbolo="XIII", titolo="La Morte", archetipo="La Trasformazione Inevitabile",
        oracolo=(
            "Qualcosa sta finendo. E deve finire.\n"
            "Non piangere ciò che muore — stai facendo spazio\n"
            "a qualcosa di infinitamente più grande.\n"
            "Ogni fine è un inizio mascherato."
        ),
        riflessione="Cosa devi lasciar morire per poter rinascere?",
        azione="Identifica UNA cosa (abitudine, relazione, identità) che è già morta ma non hai ancora sepolto.",
        zona_afficne=Zona.SOPRAVVIVENZA
    ),
    CartaOracolo(
        numero=14, simbolo="XIV", titolo="La Temperanza", archetipo="L'Alchimia Quotidiana",
        oracolo=(
            "La trasformazione non è un'esplosione — è una distillazione lenta.\n"
            "Goccia a goccia, giorno dopo giorno.\n"
            "Stai miscelando gli ingredienti giusti nella tua vita?\n"
            "Troppo di qualcosa avvelena. La misura crea magia."
        ),
        riflessione="Dove c'è eccesso nella tua vita? Dove c'è carenza?",
        azione="Scegli un'area dove sei in eccesso. Riducila del 20% questa settimana.",
        zona_afficne=Zona.STAGNAZIONE
    ),
    CartaOracolo(
        numero=15, simbolo="XV", titolo="L'Ombra", archetipo="Il Demone Interiore",
        oracolo=(
            "L'ombra non sparisce quando la ignori.\n"
            "Cresce nell'oscurità.\n"
            "L'abitudine che vuoi nascondere, la dipendenza che giustifichi,\n"
            "il pattern che ripeti — QUELLO è il tuo prossimo campo di lavoro."
        ),
        riflessione="Qual è la cosa che non vuoi ammettere a te stesso?",
        azione="Scrivi su carta la tua ombra principale. Solo tu vedrai. La luce dissolve l'oscurità.",
        zona_afficne=Zona.SOPRAVVIVENZA
    ),
    CartaOracolo(
        numero=16, simbolo="XVI", titolo="La Torre", archetipo="Il Crollo Necessario",
        oracolo=(
            "Le strutture che crollano erano già marce.\n"
            "Il fulmine non distrugge — RIVELA.\n"
            "Cosa si sta sgretolando nella tua vita in questo momento?\n"
            "Non reconstruire ancora. Prima capisci PERCHÉ è caduto."
        ),
        riflessione="Cosa stai cercando di tenere in piedi che sarebbe meglio lasciar cadere?",
        azione="Identifica la struttura (abitudine, sistema, relazione) che si sta sgretolando. Lasciala andare.",
        zona_afficne=Zona.SOPRAVVIVENZA
    ),
    CartaOracolo(
        numero=17, simbolo="XVII", titolo="Le Stelle", archetipo="La Speranza Rinnovata",
        oracolo=(
            "Anche nella notte più buia, le stelle guidano.\n"
            "Non hai bisogno di vedere l'intero percorso —\n"
            "solo il prossimo passo illuminato dalla luce stellare.\n"
            "La speranza non è ingenua. È strategica."
        ),
        riflessione="Qual è la visione del tuo futuro che ti fa ancora battere il cuore?",
        azione="Scrivi 3 righe sulla versione di te tra 1 anno se tutto va come vuoi. Sii specifico.",
        zona_afficne=Zona.STAGNAZIONE
    ),
    CartaOracolo(
        numero=18, simbolo="XVIII", titolo="La Luna", archetipo="Il Profondo Misterioso",
        oracolo=(
            "Non tutto è come appare.\n"
            "La mente conscia vede solo la superficie.\n"
            "Cosa si muove nelle acque profonde della tua vita?\n"
            "I sogni, le intuizioni, i momenti di strana chiarezza — ascoltali."
        ),
        riflessione="C'è qualcosa che il tuo corpo sa e che la tua mente sta ignorando?",
        azione="Nota 3 intuizioni o 'sensazioni strane' che hai avuto questa settimana. Cosa ti dicono?",
        zona_afficne=None
    ),
    CartaOracolo(
        numero=19, simbolo="XIX", titolo="Il Sole", archetipo="La Vitalità Radiante",
        oracolo=(
            "Questo è il tuo momento di luce.\n"
            "La vita fluisce, l'energia è disponibile,\n"
            "la chiarezza è a portata di mano.\n"
            "Non sprecare questo stato prezioso. CREA. COSTRUISCI. AMA."
        ),
        riflessione="Come stai usando l'energia e la chiarezza che hai in questo momento?",
        azione="Fai oggi l'azione più importante verso il tuo obiettivo principale. Non domani — OGGI.",
        zona_afficne=Zona.TRASFORMAZIONE
    ),
    CartaOracolo(
        numero=20, simbolo="XX", titolo="Il Risveglio", archetipo="La Chiamata dell'Anima",
        oracolo=(
            "Stai ricevendo una chiamata.\n"
            "Quella sensazione che qualcosa di più grande ti aspetta?\n"
            "Non è fantasia — è il tuo destino che bussa alla porta.\n"
            "Sei disposto a rispondere?"
        ),
        riflessione="C'è una chiamata che senti da tempo e a cui non hai ancora risposto?",
        azione="Identifica UNA cosa che 'dovresti' fare da tempo. Fai il primo passo oggi.",
        zona_afficne=Zona.TRASFORMAZIONE
    ),
    CartaOracolo(
        numero=21, simbolo="XXI", titolo="Il Mondo", archetipo="La Maestria Completa",
        oracolo=(
            "Hai completato un ciclo.\n"
            "Porta con te tutto ciò che hai imparato.\n"
            "La vera maestria non è la perfezione —\n"
            "è la capacità di ricominciare con più saggezza."
        ),
        riflessione="Cosa hai conquistato che non hai ancora celebrato?",
        azione="Celebra un traguardo che hai raggiunto. Non rimandare il riconoscimento dei tuoi successi.",
        zona_afficne=Zona.TRASFORMAZIONE
    ),
]


class LibroOracolo:
    """
    Il Libro delle Rivelazioni — 22 carte per la trasformazione.

    Consulta il libro per ricevere saggezza contestuale
    basata sul tuo stato nel gioco della vita.
    """

    def __init__(self):
        self.calc = LGAICalculator()
        self.carte = {carta.numero: carta for carta in CARTE}

    def consulta(self, stats: PlayerStats, domanda: str = "") -> CartaOracolo:
        """
        Consulta il libro e ricevi una carta.

        La selezione è deterministica per giorno (stessa carta tutto il giorno),
        ma influenzata dalla zona corrente e dalla domanda.
        """
        zona = self.calc.get_zona(stats.pv_current)
        seed_input = f"{stats.giorno}:{zona.value}:{domanda[:20]}"
        seed = int(hashlib.md5(seed_input.encode()).hexdigest(), 16) % 1000

        # Candidati: prima le carte affini alla zona, poi tutte le altre
        carte_zona = [c for c in CARTE if c.zona_afficne == zona]
        altre_carte = [c for c in CARTE if c.zona_afficne != zona]
        candidati = carte_zona + altre_carte

        # Con probabilità 60% pesca dalla zona, altrimenti da tutte
        if seed % 10 < 6 and carte_zona:
            pool = carte_zona
        else:
            pool = CARTE

        indice = seed % len(pool)
        return pool[indice]

    def consulta_area(self, stats: PlayerStats, area: Area) -> CartaOracolo:
        """Consulta il libro con focus su un'area specifica."""
        seed_input = f"{stats.giorno}:{area.value}"
        seed = int(hashlib.md5(seed_input.encode()).hexdigest(), 16)
        return CARTE[seed % len(CARTE)]

    def formato_display(self, carta: CartaOracolo, domanda: str = "") -> str:
        """Formatta la carta per la visualizzazione CLI."""
        larghezza = 58
        bordo = "═" * larghezza
        linea = "─" * larghezza

        righe = []
        righe.append(f"╔{bordo}╗")
        righe.append(f"║{'📖 LIBRO ORACOLO':^{larghezza}}║")
        righe.append(f"╠{bordo}╣")

        titolo_display = f"  {carta.simbolo}  —  {carta.titolo.upper()}"
        righe.append(f"║{titolo_display:<{larghezza}}║")

        archetipo_display = f"  [ {carta.archetipo} ]"
        righe.append(f"║{archetipo_display:<{larghezza}}║")

        righe.append(f"║{' ' * larghezza}║")

        if domanda:
            righe.append(f"║  ✦ La tua domanda:{' ' * (larghezza - 19)}║")
            for riga in self._wrap(domanda, larghezza - 4):
                righe.append(f"║  {riga:<{larghezza - 2}}║")
            righe.append(f"║{' ' * larghezza}║")

        righe.append(f"║  🔮 L'ORACOLO PARLA:{' ' * (larghezza - 21)}║")
        for riga in carta.oracolo.split("\n"):
            for parte in self._wrap(riga, larghezza - 4):
                righe.append(f"║  {parte:<{larghezza - 2}}║")

        righe.append(f"║{' ' * larghezza}║")
        righe.append(f"╠{linea.replace('─', '─')}╣".replace("─" * larghezza, "─" * larghezza))

        righe.append(f"║  💭 RIFLESSIONE:{' ' * (larghezza - 17)}║")
        for parte in self._wrap(carta.riflessione, larghezza - 4):
            righe.append(f"║  {parte:<{larghezza - 2}}║")

        righe.append(f"║{' ' * larghezza}║")
        righe.append(f"║  ⚡ AZIONE:{' ' * (larghezza - 11)}║")
        for parte in self._wrap(carta.azione, larghezza - 4):
            righe.append(f"║  {parte:<{larghezza - 2}}║")

        righe.append(f"║{' ' * larghezza}║")
        righe.append(f"╚{bordo}╝")

        return "\n".join(righe)

    @staticmethod
    def _wrap(testo: str, max_len: int) -> List[str]:
        """Spezza il testo in righe di lunghezza max."""
        if len(testo) <= max_len:
            return [testo]
        parole = testo.split(" ")
        righe = []
        riga_corrente = ""
        for parola in parole:
            test = (riga_corrente + " " + parola).strip()
            if len(test) <= max_len:
                riga_corrente = test
            else:
                if riga_corrente:
                    righe.append(riga_corrente)
                riga_corrente = parola
        if riga_corrente:
            righe.append(riga_corrente)
        return righe
