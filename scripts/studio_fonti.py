"""Morning Brief basato sui metadati pubblici di Crossref e OpenAIRE Graph."""

import datetime
import html
import json
import re
from time import sleep
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlencode
from urllib.request import Request, urlopen

# Solo termini di ricerca pubblici vengono trasmessi ai servizi.
# I frammenti richiesti nel titolo impediscono che una corrispondenza generica
# nella ricerca testuale basti a considerare coperto un argomento.
PISTE = (
    ("self sovereign digital identity", ("sovereign", "identit"),
     "Cerca quale componente conserva le credenziali e come funziona la revoca quando il dispositivo è offline."),
    ("satellite task scheduling", ("satellite", "schedul", "task"),
     "Distingui il tempo di pianificazione dal tempo di acquisizione e annota quale latenza viene misurata."),
    ("urban drone emergency response", ("urban", "drone", "emergency"),
     "Individua lo scenario urbano studiato e verifica se il tempo di intervento è misurato sul campo o simulato."),
    ("robot manipulation sim-to-real", ("robot", "sim to real"),
     "Confronta il compito simulato con la prova sul robot fisico e annota la metrica usata per il trasferimento."),
    ("humanitarian earth observation", ("humanitarian", "earth observation"),
     "Verifica quali dati satellitari sono stati usati per l’intervento umanitario e se è indicata una licenza di riuso."),
    ("digital legacy", ("digital", "legacy"),
     "Cerca chi può autorizzare l’accesso a un archivio dopo la morte e come questa scelta viene documentata."),
    ("edge computing satellite", ("satellite", "edge comput"),
     "Confronta quali elaborazioni possono avvenire a bordo e quali richiedono un collegamento a terra."),
)
CONNESSIONI = (
    "satellite disaster response", ("satellite", "disaster", "response"),
    "Per collegare osservazione satellitare e soccorso, cerca l’intervallo fra acquisizione e consegna di una mappa utilizzabile.",
)


def _json(url, parametri):
    richiesta = Request(url + "?" + urlencode(parametri), headers={
        "Accept": "application/json", "User-Agent": "SDQ-Studio/1.0",
    })
    for tentativo in range(2):
        try:
            with urlopen(richiesta, timeout=20) as risposta:
                return json.load(risposta)
        except (URLError, TimeoutError) as errore:
            if tentativo or (isinstance(errore, HTTPError) and errore.code not in {429, 500, 502, 503, 504}):
                raise
            sleep(2)


def _titolo(testo, termini):
    testo = html.unescape(re.sub(r"<[^>]+>", " ", testo))
    testo = " ".join(testo.split())
    semplice = re.sub(r"[^\w]+", " ", testo.casefold())
    if all(termine in semplice for termine in termini):
        # I titoli forniti da terzi sono testo, anche se contengono Markdown.
        return re.sub(r"([\\`*_\[\]<>|~])", r"\\\1", testo[:300])


def _articoli(pista, inizio, oggi, usati):
    query, termini, _ = pista
    dati = _json("https://api.crossref.org/works", {
        "query.title": query, "rows": 20, "select": "DOI,title,published",
        "filter": f"type:journal-article,from-pub-date:{inizio},until-pub-date:{oggi}",
    })
    righe = []
    for record in dati["message"]["items"]:
        doi = record.get("DOI", "").lower()
        titoli = record.get("title") or []
        titolo = _titolo(titoli[0], termini) if titoli else None
        if not titolo or not re.fullmatch(r"10\.\d{4,9}/[^\s]+", doi) or doi in usati:
            continue
        parti = record.get("published", {}).get("date-parts", [[]])[0]
        try:
            data = datetime.date(*(parti + [1] * (3 - len(parti))))
        except (ValueError, TypeError):
            continue
        if not parti or not inizio <= data <= oggi:
            continue
        # Conserva la precisione (solo anno, mese oppure giorno) indicata dall'editore.
        data_visibile = data.isoformat()[:(4, 7, 10)[len(parti) - 1]]
        url = "https://doi.org/" + quote(doi, safe="/")
        righe.append(f"- {titolo} · {data_visibile} · [DOI]({url})")
        usati.add(doi)
        if len(righe) == 2:
            break
    if not righe:
        raise RuntimeError(f"Crossref: nessun articolo pertinente con DOI e data per «{query}»")
    return righe


def _progetti_ue(inizio, oggi):
    dati = _json("https://api.openaire.eu/graph/v3/projects", {
        "title": "earth observation", "fundingShortName": "EC", "fromStartDate": inizio,
        "toStartDate": oggi, "sortBy": "startDate DESC", "pageSize": 10,
    })
    righe = []
    codici = set()
    for progetto in dati["results"]:
        codice = progetto.get("code") or ""
        titolo = _titolo(progetto.get("title") or "", ("earth observation",))
        avvio = progetto.get("startDate") or ""
        if not titolo or not re.fullmatch(r"[0-9]{6,9}", codice) or codice in codici:
            continue
        if not progetto.get("id", "").startswith("corda_") or not any(
            ente.get("shortName") == "EC" for ente in progetto.get("fundings") or []
        ):
            continue
        try:
            if not inizio <= datetime.date.fromisoformat(avvio) <= oggi:
                continue
        except ValueError:
            continue
        url = f"https://cordis.europa.eu/project/id/{codice}"
        righe.append(f"- {titolo} · avvio {avvio} · [CORDIS {codice}]({url})")
        codici.add(codice)
        if len(righe) == 2:
            break
    if not righe:
        raise RuntimeError("OpenAIRE: nessun progetto UE pertinente con codice CORDIS e data")
    return righe


def genera_brief_fonti(temi, oggi):
    """Produce tre sezioni documentate o solleva un errore prima del salvataggio."""
    giorno = oggi.weekday()
    domani = (giorno + 1) % 7
    inizio = oggi - datetime.timedelta(days=730)
    righe = [
        f"# Morning Brief — {oggi:%Y-%m-%d}", "",
        f"Intervallo di ricerca dal {inizio} al {oggi}. Le schede riportano metadati bibliografici e date degli editori.",
        "Le indicazioni di lettura sono proposte da verificare nei testi integrali.", "",
    ]
    sezioni = (
        (f"Tema del giorno — {temi[giorno]['nome']}", PISTE[giorno], giorno),
        (f"Domani — {temi[domani]['nome']}", PISTE[domani], domani),
        ("Connessioni — Osservazione satellitare e risposta alle catastrofi", CONNESSIONI, None),
    )
    usati = set()
    for nome, pista, indice in sezioni:
        righe.extend([f"## {nome}", "", "Articoli indicizzati da Crossref", ""])
        righe.extend(_articoli(pista, inizio, oggi, usati))
        righe.extend(["", f"**Indicazione di lettura.** {pista[2]}", ""])
        if indice == 4:
            righe.extend(["### Progetti UE di osservazione terrestre", "",
                          "OpenAIRE registra finanziamenti già assegnati. Lo stato dei bandi aperti resta da verificare.", ""])
            righe.extend(_progetti_ue(inizio, oggi))
            righe.extend(["", "Apri una scheda CORDIS, identifica il coordinatore e risali al programma che ha finanziato il progetto.", ""])
    return "\n".join(righe)
