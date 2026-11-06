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
    ("satellite image acquisition scheduling", ("satellite", "imag", "schedul"),
     "Distingui il tempo di pianificazione dal tempo di acquisizione e annota quale latenza viene misurata."),
    ("EU AI Act", ("ai act",),
     "Confronta le norme UE effettivamente citate con il dossier Minerva; non dedurre applicabilità ai droni o scadenze legali dal solo titolo."),
    ("CNC toolpath generation", ("cnc", "toolpath"),
     "Confronta la generazione dei percorsi CNC con gli esempi già studiati; non presumere compatibilità con CadQuery o Pocket NC senza prove."),
    ("refugee digital identity", ("digital", "refugee", "identit"),
     "Verifica quali bisogni di identità digitale dei rifugiati sono documentati; non dedurre accesso a finanziamenti o eleggibilità ASBL da un articolo."),
    ("digital legacy", ("digital", "legacy"),
     "Cerca chi può autorizzare l’accesso a un archivio dopo la morte e come questa scelta viene documentata."),
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
    titoli_usati = set()
    for record in dati["message"]["items"]:
        doi = record.get("DOI", "").lower()
        titoli = record.get("title") or []
        titolo = _titolo(titoli[0], termini) if titoli else None
        if not titolo or titolo.casefold() in titoli_usati or not re.fullmatch(r"10\.\d{4,9}/[^\s]+", doi) or doi in usati:
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
        titoli_usati.add(titolo.casefold())
        if len(righe) == 2:
            break
    if not righe:
        raise RuntimeError(f"Crossref: nessun articolo pertinente con DOI e data per «{query}»")
    return righe


def _progetti_ue(inizio, oggi):
    dati = _json("https://api.openaire.eu/graph/v3/projects", {
        "title": "digital identity", "fundingShortName": "EC", "fromStartDate": inizio,
        "toStartDate": oggi, "sortBy": "startDate DESC", "pageSize": 10,
    })
    righe = []
    codici = set()
    for progetto in dati["results"]:
        codice = progetto.get("code") or ""
        titolo = _titolo(progetto.get("title") or "", ("digital identit",))
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


def genera_brief_fonti(temi, oggi, indici=None):
    """Produce tre sezioni documentate o solleva un errore prima del salvataggio."""
    if indici is None:
        # Anche chi chiama direttamente il fallback rispetta il perimetro lavorato.
        if __package__:
            from .studio_priorita import seleziona_temi
        else:
            from studio_priorita import seleziona_temi
        indici = [s["indice"] for s in seleziona_temi(temi, oggi)]
    if not indici or len(indici) > 3 or len(set(indici)) != len(indici) or any(
        type(i) is not int or i not in range(6) or i not in temi for i in indici
    ):
        raise ValueError("Sono richiesti da uno a tre temi già lavorati, senza wildcard")
    inizio = oggi - datetime.timedelta(days=730)
    righe = [
        f"# Morning Brief — {oggi:%Y-%m-%d}", "",
        f"Intervallo di ricerca dal {inizio} al {oggi}. Le schede riportano metadati bibliografici e date degli editori.",
        "Rinnovo bibliografico limitato ai temi già lavorati. Non è una revisione completa dei dossier.",
        "Le indicazioni di lettura sono proposte da verificare nei testi integrali. "
        "Norme, procedure, prezzi e disponibilità di servizi non sono verificati da questi metadati.", "",
    ]
    sezioni = tuple((f"Rinnovo — {temi[i]['nome']}", PISTE[i], i) for i in indici)
    usati = set()
    for nome, pista, indice in sezioni:
        righe.extend([f"## {nome}", "", "Articoli indicizzati da Crossref", ""])
        righe.extend(_articoli(pista, inizio, oggi, usati))
        righe.extend(["", f"**Indicazione di lettura.** {pista[2]}", ""])
        if indice == 4:
            righe.extend(["### Progetti UE di identità digitale", "",
                          "OpenAIRE registra finanziamenti già assegnati. Bandi aperti, eleggibilità e procedura ASBL restano da verificare.", ""])
            righe.extend(_progetti_ue(inizio, oggi))
            righe.extend(["", "Apri una scheda CORDIS, identifica il coordinatore e risali al programma che ha finanziato il progetto.", ""])
    return "\n".join(righe)
