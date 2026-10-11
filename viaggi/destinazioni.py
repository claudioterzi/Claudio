"""Database curato di destinazioni low cost raggiungibili dall'Italia.

Stime prudenziali per persona (2026):
    budget_giorno  → alloggio economico (ostello/guesthouse) + pasti + trasporti locali, in €
    volo_ar        → volo andata/ritorno low cost prenotato con 4-8 settimane di anticipo, in €
I mesi ideali tengono conto di clima e prezzi (evitando l'altissima stagione dove possibile).
"""
from __future__ import annotations

from dataclasses import dataclass, field

MESI = (
    "gennaio", "febbraio", "marzo", "aprile", "maggio", "giugno",
    "luglio", "agosto", "settembre", "ottobre", "novembre", "dicembre",
)

TIPI = ("città", "mare", "natura", "cibo", "cultura", "terme", "notturna")


@dataclass(frozen=True)
class Destinazione:
    nome: str
    paese: str
    tipi: tuple[str, ...]
    budget_giorno: int          # € al giorno: alloggio + vitto + trasporti locali
    volo_ar: int                # € volo A/R low cost dall'Italia (stima prudente)
    mesi_ideali: tuple[int, ...]  # numeri mese 1-12
    partenze: tuple[str, ...]   # aeroporti italiani con voli diretti economici
    perche: str                 # perché è low cost e perché vale il viaggio
    consigli: tuple[str, ...] = field(default_factory=tuple)


# Aeroporto principale di ogni meta: permette di incrociare i prezzi LIVE
# (Flight Hunter) calcolati dalla città di partenza dell'utente.
IATA: dict[str, str] = {
    "Tirana + riviera albanese": "TIA",
    "Cracovia": "KRK",
    "Budapest": "BUD",
    "Porto": "OPO",
    "Valencia": "VLC",
    "Siviglia": "SVQ",
    "Atene + Egina": "ATH",
    "Malta": "MLA",
    "Praga": "PRG",
    "Sofia + monte Vitosha": "SOF",
    "Bucarest + Transilvania": "OTP",
    "Marrakech": "RAK",
    "Sarajevo + Mostar": "SJJ",
    "Belgrado": "BEG",
    "Salonicco": "SKG",
    "Tenerife": "TFS",
    "Napoli + Procida": "NAP",
    "Palermo": "PMO",
    "Bari + Polignano e Matera": "BRI",
    "Danzica": "GDN",
    "Skopje + canyon Matka": "SKP",
    "Zagabria + laghi di Plitvice": "ZAG",
    "Bratislava + Vienna in giornata": "BTS",
    "Fès": "FEZ",
    "Riga": "RIX",
}


DESTINAZIONI: tuple[Destinazione, ...] = (
    Destinazione(
        nome="Tirana + riviera albanese", paese="Albania",
        tipi=("mare", "città", "cibo"),
        budget_giorno=35, volo_ar=45,
        mesi_ideali=(5, 6, 9, 10),
        partenze=("Milano Bergamo", "Bologna", "Roma Fiumicino", "Bari"),
        perche="Prezzi tra i più bassi d'Europa, mare tipo Grecia a metà costo, cucina eccellente.",
        consigli=(
            "Bus Tirana→Saranda ~15€: la riviera (Ksamil, Himarë) è il vero motivo del viaggio.",
            "Si paga quasi ovunque in contanti (lek): prelevare in loco, evitare cambi in aeroporto.",
            "Giugno e settembre: stesso mare di agosto, metà dei prezzi.",
        ),
    ),
    Destinazione(
        nome="Cracovia", paese="Polonia",
        tipi=("città", "cultura", "notturna"),
        budget_giorno=40, volo_ar=35,
        mesi_ideali=(4, 5, 6, 9, 10, 12),
        partenze=("Milano Bergamo", "Roma Ciampino", "Bologna", "Napoli"),
        perche="Centro storico intatto, pierogi a 4€, birra a 2€: qualità/prezzo imbattibile.",
        consigli=(
            "Auschwitz e le miniere di sale di Wieliczka: prenotare online con anticipo.",
            "Quartiere Kazimierz per mangiare e uscire spendendo poco.",
            "A dicembre il mercatino di Natale è tra i più belli e meno cari d'Europa.",
        ),
    ),
    Destinazione(
        nome="Budapest", paese="Ungheria",
        tipi=("città", "terme", "notturna", "cultura"),
        budget_giorno=45, volo_ar=40,
        mesi_ideali=(4, 5, 6, 9, 10),
        partenze=("Milano Bergamo", "Roma Fiumicino", "Bologna", "Napoli"),
        perche="Terme monumentali, ruin bar e una capitale imperiale a prezzi da Est Europa.",
        consigli=(
            "Terme Széchenyi al mattino presto: meno folla, biglietto pieno ma vale ogni euro.",
            "Mangiare nei mercati coperti (Grande Mercato): lángos e gulasch a pochi euro.",
            "La travelcard 72h dei mezzi costa meno di tre corse in taxi.",
        ),
    ),
    Destinazione(
        nome="Porto", paese="Portogallo",
        tipi=("città", "cibo", "cultura"),
        budget_giorno=50, volo_ar=60,
        mesi_ideali=(4, 5, 6, 9, 10),
        partenze=("Milano Bergamo", "Milano Malpensa", "Roma Fiumicino", "Bologna"),
        perche="Atlantico, azulejos e francesinha: la città più autentica e conveniente del Portogallo.",
        consigli=(
            "Cantine del vino Porto a Vila Nova de Gaia: le visite con degustazione partono da ~10€.",
            "Pranzo del giorno («prato do dia») nei ristorantini: piatto+bibita sotto i 10€.",
            "Il tram 1 lungo il Douro costa come un biglietto normale ed è meglio di un tour.",
        ),
    ),
    Destinazione(
        nome="Valencia", paese="Spagna",
        tipi=("mare", "città", "cibo", "notturna"),
        budget_giorno=50, volo_ar=45,
        mesi_ideali=(4, 5, 6, 9, 10),
        partenze=("Milano Bergamo", "Roma Fiumicino", "Bologna", "Napoli"),
        perche="Spiaggia in città, paella vera e clima perfetto quasi tutto l'anno, senza i prezzi di Barcellona.",
        consigli=(
            "La paella si mangia a pranzo, mai a cena: menù del giorno ~12-15€ nei locali de El Cabanyal.",
            "Il parco del Turia attraversa tutta la città: bici a noleggio e zero spese di trasporto.",
            "Città delle Arti e delle Scienze: spettacolare anche solo da fuori, gratis.",
        ),
    ),
    Destinazione(
        nome="Siviglia", paese="Spagna",
        tipi=("città", "cultura", "cibo"),
        budget_giorno=50, volo_ar=50,
        mesi_ideali=(3, 4, 5, 10, 11),
        partenze=("Milano Bergamo", "Roma Fiumicino", "Bologna"),
        perche="La città più bella d'Andalusia: tapas, flamenco e monumenti moreschi a prezzi onesti.",
        consigli=(
            "Evitare luglio-agosto: 45 gradi reali. Marzo-maggio è il momento perfetto.",
            "Tapas in piedi al bancone: si spende la metà che seduti al tavolo.",
            "Alcázar: biglietti online giorni prima, la fila fisica è infinita.",
        ),
    ),
    Destinazione(
        nome="Atene + Egina", paese="Grecia",
        tipi=("città", "cultura", "mare", "cibo"),
        budget_giorno=50, volo_ar=60,
        mesi_ideali=(4, 5, 6, 9, 10),
        partenze=("Milano Bergamo", "Roma Fiumicino", "Bologna", "Napoli"),
        perche="Acropoli + isola del Golfo Saronico in giornata: la Grecia senza i prezzi delle Cicladi.",
        consigli=(
            "Traghetto Pireo→Egina ~1h, ~10€: mare greco vero senza pagare Mykonos.",
            "Souvlaki e gyros: pasto completo sotto i 5€, ovunque.",
            "Biglietto combinato siti archeologici: conviene dal secondo sito in poi.",
        ),
    ),
    Destinazione(
        nome="Malta", paese="Malta",
        tipi=("mare", "cultura", "notturna"),
        budget_giorno=55, volo_ar=40,
        mesi_ideali=(4, 5, 6, 9, 10, 11),
        partenze=("Milano Bergamo", "Roma Fiumicino", "Catania", "Napoli"),
        perche="Voli tra i più economici dall'Italia, si parla inglese (e spesso italiano), mare da ottobre ad aprile mite.",
        consigli=(
            "I bus coprono tutta l'isola: tallinja card settimanale, niente auto a noleggio.",
            "Comino e la Blue Lagoon all'alba o mai: dalle 10 è invivibile.",
            "La Valletta e le Tre Città valgono più delle spiagge: Malta è prima di tutto pietra e storia.",
        ),
    ),
    Destinazione(
        nome="Praga", paese="Cechia",
        tipi=("città", "cultura", "notturna"),
        budget_giorno=50, volo_ar=50,
        mesi_ideali=(4, 5, 6, 9, 10, 12),
        partenze=("Milano Bergamo", "Roma Fiumicino", "Bologna", "Napoli"),
        perche="Una delle città più belle del continente; birra migliore d'Europa a 2€ alla spina.",
        consigli=(
            "Cambiare mai in strada e mai in centro: prelevare corone al bancomat di una banca.",
            "Il Castello al mattino presto, il Ponte Carlo all'alba: dopo le 10 è fiume di gente.",
            "Pranzo nei «polední menu»: menù operaio a 6-8€ anche in centro.",
        ),
    ),
    Destinazione(
        nome="Sofia + monte Vitosha", paese="Bulgaria",
        tipi=("città", "natura", "terme"),
        budget_giorno=35, volo_ar=45,
        mesi_ideali=(5, 6, 7, 8, 9),
        partenze=("Milano Bergamo", "Roma Fiumicino", "Bologna"),
        perche="Capitale più economica dell'UE: si mangia bene con 10€ e la montagna è dentro la città.",
        consigli=(
            "Free walking tour di Sofia: uno dei migliori d'Europa, si paga quel che si vuole.",
            "Il monastero di Rila in giornata: bus organizzato ~25€, imperdibile.",
            "Vitosha in mezz'ora di bus: trekking estivo o sci low cost d'inverno.",
        ),
    ),
    Destinazione(
        nome="Bucarest + Transilvania", paese="Romania",
        tipi=("città", "natura", "cultura"),
        budget_giorno=40, volo_ar=40,
        mesi_ideali=(5, 6, 7, 8, 9, 10),
        partenze=("Milano Bergamo", "Roma Fiumicino", "Bologna", "Torino"),
        perche="Treni interni a pochi euro verso Brașov e i castelli: due viaggi al prezzo di uno.",
        consigli=(
            "Treno Bucarest→Brașov ~3h ~10€: base perfetta per Bran e Sighișoara.",
            "La vecchia Lipscani per la sera; il Palazzo del Parlamento va prenotato.",
            "Attenzione ai taxi non ufficiali: usare le app locali (Bolt).",
        ),
    ),
    Destinazione(
        nome="Marrakech", paese="Marocco",
        tipi=("città", "cultura", "cibo"),
        budget_giorno=40, volo_ar=60,
        mesi_ideali=(2, 3, 4, 10, 11),
        partenze=("Milano Bergamo", "Roma Fiumicino", "Bologna"),
        perche="Un altro continente a 3 ore di volo: riad, medina e tajine a prezzi minimi.",
        consigli=(
            "Dormire in un riad nella medina: colazione inclusa e spesso costa meno di un ostello europeo.",
            "Contrattare è la norma: partire da un terzo del prezzo chiesto, con il sorriso.",
            "Escursione alle cascate di Ouzoud o a Essaouira in giornata: ~20-25€ in bus condiviso.",
        ),
    ),
    Destinazione(
        nome="Sarajevo + Mostar", paese="Bosnia ed Erzegovina",
        tipi=("città", "cultura", "natura", "cibo"),
        budget_giorno=35, volo_ar=70,
        mesi_ideali=(5, 6, 7, 8, 9),
        partenze=("Milano Bergamo", "Roma Fiumicino"),
        perche="Storia recente che si tocca con mano, ćevapi a 4€, e il ponte di Mostar a due ore di treno.",
        consigli=(
            "Il treno Sarajevo→Mostar è tra i più panoramici dei Balcani e costa ~6€.",
            "Tunnel della Speranza e free walking tour: la storia dell'assedio raccontata da chi c'era.",
            "In alternativa al volo: Flixbus da Trieste/Venezia, spesso sotto i 40€ A/R.",
        ),
    ),
    Destinazione(
        nome="Belgrado", paese="Serbia",
        tipi=("città", "notturna", "cibo"),
        budget_giorno=40, volo_ar=50,
        mesi_ideali=(4, 5, 6, 9, 10),
        partenze=("Milano Bergamo", "Roma Fiumicino", "Bologna"),
        perche="La vita notturna più viva dei Balcani e porzioni doppie a metà prezzo.",
        consigli=(
            "Gli splavovi (locali galleggianti sul Danubio) d'estate: ingresso quasi sempre gratuito.",
            "Quartiere Skadarlija per cena: la Montmartre serba, senza i prezzi di Montmartre.",
            "La fortezza di Kalemegdan al tramonto è il posto giusto ed è gratis.",
        ),
    ),
    Destinazione(
        nome="Salonicco", paese="Grecia",
        tipi=("città", "cibo", "mare", "notturna"),
        budget_giorno=45, volo_ar=50,
        mesi_ideali=(5, 6, 9, 10),
        partenze=("Milano Bergamo", "Roma Fiumicino", "Bologna"),
        perche="La capitale gastronomica greca, senza folla: e la Calcidica è a un'ora di bus.",
        consigli=(
            "Mercato Modiano e i mezedopoleia del centro: si cena con 12-15€ mangiando benissimo.",
            "Bus per la Calcidica (Kassandra) dall'autostazione KTEL: mare top in giornata.",
            "La città alta (Ano Poli) è il quartiere che tutti saltano e vale mezzo viaggio.",
        ),
    ),
    Destinazione(
        nome="Tenerife", paese="Spagna — Canarie",
        tipi=("mare", "natura"),
        budget_giorno=55, volo_ar=100,
        mesi_ideali=(1, 2, 3, 11, 12),
        partenze=("Milano Bergamo", "Milano Malpensa", "Roma Fiumicino", "Bologna"),
        perche="Estate a gennaio: l'unico mare caldo d'Europa in pieno inverno, con voli diretti low cost.",
        consigli=(
            "Il nord (Puerto de la Cruz, La Laguna) costa meno ed è più vero del sud turistico.",
            "Teide: salire con il primo bus del mattino o prenotare la funivia online.",
            "Menù del giorno nei guachinche (osterie canarie): vino della casa incluso.",
        ),
    ),
    Destinazione(
        nome="Napoli + Procida", paese="Italia",
        tipi=("città", "cibo", "mare", "cultura"),
        budget_giorno=55, volo_ar=45,
        mesi_ideali=(3, 4, 5, 6, 9, 10),
        partenze=("Milano Bergamo", "Milano Malpensa", "Torino", "treno AV da tutta Italia"),
        perche="La città italiana dove si mangia meglio spendendo meno; Procida è la low cost delle isole del Golfo.",
        consigli=(
            "Pizza a portafoglio 2€, sfogliatella 2€: lo street food è un pasto completo.",
            "Aliscafo per Procida ~20€ A/R: i colori di Instagram senza i prezzi di Capri.",
            "Treni AV prenotati 2-3 settimane prima: Milano→Napoli anche a 30-40€.",
        ),
    ),
    Destinazione(
        nome="Palermo", paese="Italia",
        tipi=("città", "cibo", "mare", "cultura"),
        budget_giorno=50, volo_ar=45,
        mesi_ideali=(4, 5, 6, 9, 10),
        partenze=("Milano Bergamo", "Milano Malpensa", "Roma Fiumicino", "Bologna", "Torino"),
        perche="Street food tra i migliori al mondo, mercati arabi, e Mondello a 20 minuti di bus.",
        consigli=(
            "Mercati di Ballarò e del Capo: panelle, crocchè e sfincione per pochi euro.",
            "Bus 806 per Mondello: spiaggia bianca urbana, gratis fuori dagli stabilimenti.",
            "Cattedrale di Monreale: mezz'ora di bus, mosaici da capitale bizantina.",
        ),
    ),
    Destinazione(
        nome="Bari + Polignano e Matera", paese="Italia",
        tipi=("città", "mare", "cibo", "cultura"),
        budget_giorno=50, volo_ar=40,
        mesi_ideali=(4, 5, 6, 9, 10),
        partenze=("Milano Bergamo", "Milano Malpensa", "Torino", "Bologna"),
        perche="Base perfetta: treni regionali a 3-5€ per Polignano, e Matera a un'ora e mezza.",
        consigli=(
            "Orecchiette delle signore di Bari Vecchia e focaccia barese: pranzo sotto i 5€.",
            "Treno per Polignano a Mare ~30 min: tuffo e ritorno in giornata.",
            "Matera con le Ferrovie Appulo Lucane: i Sassi valgono la deviazione, sempre.",
        ),
    ),
    Destinazione(
        nome="Danzica", paese="Polonia",
        tipi=("città", "mare", "cultura"),
        budget_giorno=42, volo_ar=45,
        mesi_ideali=(5, 6, 7, 8, 9),
        partenze=("Milano Bergamo", "Roma Ciampino", "Bologna"),
        perche="Il Baltico d'estate: centro anseatico ricostruito, spiagge di Sopot e prezzi polacchi.",
        consigli=(
            "Treno urbano per Sopot ~20 min: il molo più lungo d'Europa e spiaggia libera.",
            "Museo della Seconda Guerra Mondiale: tra i migliori d'Europa, mezza giornata.",
            "Pierogi e zuppe nei bar mleczny (mense popolari): pasto a 4-6€.",
        ),
    ),
    Destinazione(
        nome="Skopje + canyon Matka", paese="Macedonia del Nord",
        tipi=("città", "natura", "cibo"),
        budget_giorno=32, volo_ar=40,
        mesi_ideali=(4, 5, 6, 9, 10),
        partenze=("Milano Bergamo", "Roma Ciampino", "Bologna"),
        perche="Probabilmente il viaggio più economico in assoluto dall'Italia: si vive bene con 30€ al giorno.",
        consigli=(
            "Canyon Matka a 40 minuti di bus: kayak tra le gole a prezzi simbolici.",
            "Il vecchio bazar ottomano è il cuore vero della città, altro che le statue del centro.",
            "Con un bus si arriva a Ohrid (lago UNESCO): valuta 2-3 notti extra.",
        ),
    ),
    Destinazione(
        nome="Zagabria + laghi di Plitvice", paese="Croazia",
        tipi=("città", "natura"),
        budget_giorno=45, volo_ar=50,
        mesi_ideali=(4, 5, 6, 9, 10),
        partenze=("Milano Bergamo", "Roma Fiumicino", "in bus/auto dal Nord Italia"),
        perche="La Croazia senza i prezzi della costa: capitale rilassata e i laghi più belli d'Europa.",
        consigli=(
            "Plitvice in bus da Zagabria ~2h: biglietto parco più caro in estate, andare a giugno o settembre.",
            "Dal Nord-Est Italia conviene il bus o l'auto: Trieste→Zagabria ~3h.",
            "Mercato Dolac la mattina per frutta e formaggi: picnic da 5€.",
        ),
    ),
    Destinazione(
        nome="Bratislava + Vienna in giornata", paese="Slovacchia",
        tipi=("città", "cultura"),
        budget_giorno=42, volo_ar=35,
        mesi_ideali=(4, 5, 6, 9, 10, 12),
        partenze=("Milano Bergamo", "Roma Ciampino"),
        perche="Il trucco: dormire e mangiare a prezzi slovacchi, e Vienna è a un'ora di treno (~15€ A/R).",
        consigli=(
            "Il centro storico si gira in mezza giornata: il bello è il ritmo lento e i caffè.",
            "Treno o Flixbus per Vienna: si visita in giornata spendendo un decimo dell'hotel viennese.",
            "A dicembre: due mercatini di Natale (Bratislava + Vienna) con un solo volo low cost.",
        ),
    ),
    Destinazione(
        nome="Fès", paese="Marocco",
        tipi=("città", "cultura", "cibo"),
        budget_giorno=35, volo_ar=55,
        mesi_ideali=(3, 4, 10, 11),
        partenze=("Milano Bergamo", "Roma Ciampino"),
        perche="La medina medievale più grande del mondo, meno turistica e più economica di Marrakech.",
        consigli=(
            "Le concerie Chouara dalle terrazze dei negozi: 'ingresso' = una foglia di menta per l'odore.",
            "Perdersi nella medina è il programma: 9000 vicoli, serve solo tempo.",
            "Pastilla e cous cous nei ristorantini locali fuori dai circuiti: 4-6€.",
        ),
    ),
    Destinazione(
        nome="Riga", paese="Lettonia",
        tipi=("città", "cultura", "natura"),
        budget_giorno=45, volo_ar=45,
        mesi_ideali=(5, 6, 7, 8, 12),
        partenze=("Milano Bergamo", "Roma Ciampino", "Bologna"),
        perche="Art Nouveau ovunque, mercato nei vecchi hangar per zeppelin, e il Baltico a 30 minuti.",
        consigli=(
            "Jūrmala in treno ~30 min: spiaggia baltica chilometrica, quasi gratis.",
            "Il Mercato Centrale è il posto dove mangiare: pesce affumicato e piatti locali a pochi euro.",
            "D'estate il sole tramonta alle 22: giornate doppie, stesso prezzo.",
        ),
    ),
)
