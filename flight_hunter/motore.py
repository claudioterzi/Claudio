"""Il motore di caccia.

Pipeline (come da progetto, ridotta all'osso che funziona):

    ORIGINE, DESTINAZIONE, MESE
        │
        ▼
    espandi gli aeroporti (raggio origine + alternative di arrivo)
        │
        ▼
    genera itinerari: diretti, split via hub (self-transfer),
    posizionamento via terra
        │
        ▼
    costo REALE: tariffa + terra + bagagli + notti + margine rischio
        │
        ▼
    potatura (mappe tariffe prima, calendari solo sui candidati)
        │
        ▼
    Top N ordinati per costo totale

La potatura vera avviene PRIMA delle richieste: le mappe tariffe (1 richiesta
per aeroporto ≈ tutte le destinazioni servite) decidono quali calendari
valga la pena scaricare. Niente forza bruta.
"""
from __future__ import annotations

import calendar as _cal
from dataclasses import dataclass, field
from datetime import datetime, timedelta

from .aeroporti import AEROPORTI, Aeroporto, cerca_aeroporto, distanza_km, vicini
from .costi import ParametriCosto, costo_terra, ore_terra
from .fonti import Fonte, FonteRyanair, Volo

_SLACK_HUB = 25.0        # € di tolleranza: un hub resta candidato se batte il
                         # miglior diretto entro questo margine (poi decide il totale)
_MAX_CAL_DIRETTI = 8     # calendari massimi per i collegamenti diretti
_MAX_COMBO_HUB = 10      # combinazioni (origine, hub, destinazione) da approfondire


@dataclass
class Itinerario:
    tipo: str                       # "diretto" | "split via hub"
    voli: list[Volo]
    terra_prima_km: float = 0.0     # posizionamento verso l'aeroporto di partenza
    terra_dopo_km: float = 0.0      # dall'aeroporto di arrivo alla destinazione vera
    notti: int = 0
    costo_voli: float = 0.0
    costo_terra: float = 0.0
    costo_bagagli: float = 0.0
    costo_notti: float = 0.0
    margine_rischio: float = 0.0
    totale: float = 0.0
    rischio: str = "basso"          # basso | medio | alto
    note: list[str] = field(default_factory=list)

    @property
    def chiave(self) -> str:
        """Identità della rotta (per dedup e per la memoria dei minimi)."""
        return " + ".join(f"{v.da}-{v.a}@{v.giorno}" for v in self.voli)

    def descrizione(self) -> str:
        righe = []
        for v in self.voli:
            ora_p = v.partenza[11:16] if len(v.partenza) >= 16 else "?"
            ora_a = v.arrivo[11:16] if len(v.arrivo) >= 16 else "?"
            righe.append(f"  {v.da}→{v.a}  {v.giorno} {ora_p}-{ora_a}  {v.prezzo:.2f}€  ({v.vettore})")
        return "\n".join(righe)


def _valuta(voli: list[Volo], tipo: str, terra_prima_km: float, terra_dopo_km: float,
            notti: int, bagaglio: bool, p: ParametriCosto,
            note: list[str]) -> Itinerario:
    costo_voli = sum(v.prezzo for v in voli)
    c_terra = costo_terra(terra_prima_km, p) + costo_terra(terra_dopo_km, p)
    c_bag = p.bagaglio_stiva * len(voli) if bagaglio else 0.0
    c_notti = notti * p.notte
    coincidenze = len(voli) - 1
    margine = coincidenze * p.margine_self_transfer

    rischio = "basso"
    if coincidenze:
        rischio = "medio"
        gap_min = _gap_ore(voli)
        if gap_min is not None and gap_min < p.ore_minime_scalo:
            rischio = "alto"
            note = note + [f"scalo di sole {gap_min:.1f}h su biglietti separati"]

    tot = costo_voli + c_terra + c_bag + c_notti + margine
    return Itinerario(
        tipo=tipo, voli=voli,
        terra_prima_km=terra_prima_km, terra_dopo_km=terra_dopo_km, notti=notti,
        costo_voli=round(costo_voli, 2), costo_terra=round(c_terra, 2),
        costo_bagagli=round(c_bag, 2), costo_notti=round(c_notti, 2),
        margine_rischio=round(margine, 2), totale=round(tot, 2),
        rischio=rischio, note=note,
    )


def _gap_ore(voli: list[Volo]) -> float | None:
    """Ore di scalo minime tra tratte consecutive (None se orari mancanti)."""
    gaps = []
    for prima, dopo in zip(voli, voli[1:]):
        try:
            arr = datetime.fromisoformat(prima.arrivo)
            dep = datetime.fromisoformat(dopo.partenza)
        except ValueError:
            return None
        gaps.append((dep - arr).total_seconds() / 3600.0)
    return min(gaps) if gaps else None


def _prosegui(prec: Volo, per_giorno: dict[str, Volo]) -> list[tuple[Volo, int]]:
    """Voli plausibili dopo `prec`: stesso giorno di arrivo se gli orari reali
    lo permettono (scalo ≥ 2h), oppure il giorno successivo (+1 notte)."""
    try:
        arr = datetime.fromisoformat(prec.arrivo)
    except ValueError:
        return []
    opzioni: list[tuple[Volo, int]] = []
    stesso = per_giorno.get(arr.strftime("%Y-%m-%d"))
    if stesso:
        try:
            if datetime.fromisoformat(stesso.partenza) >= arr + timedelta(hours=2):
                opzioni.append((stesso, 0))
        except ValueError:
            pass
    dopo = per_giorno.get((arr + timedelta(days=1)).strftime("%Y-%m-%d"))
    if dopo:
        opzioni.append((dopo, 1))
    return opzioni


def _concatena(calendari: list[list[Volo]]) -> list[tuple[list[Volo], int]]:
    """Concatena N tratte sui minimi giornalieri, orari reali alla mano.

    Per ogni giorno di partenza della prima tratta costruisce al più una
    catena per ramo (stesso giorno / notte), quindi il ventaglio resta piccolo.
    """
    if not calendari or not all(calendari):
        return []
    indici = [{v.giorno: v for v in cal} for cal in calendari[1:]]
    catene: list[tuple[list[Volo], int]] = [([v], 0) for v in calendari[0]]
    for per_giorno in indici:
        nuove: list[tuple[list[Volo], int]] = []
        for voli, notti in catene:
            for seguente, notte in _prosegui(voli[-1], per_giorno):
                nuove.append((voli + [seguente], notti + notte))
        catene = nuove
    return catene


def caccia(origine: str, destinazione: str, mese: str, *,
           raggio_origine: float = 250.0, raggio_destinazione: float = 150.0,
           bagaglio: bool = False, hub_max: int = 6, top: int = 20,
           profondo: bool = False,
           fonte: Fonte | None = None, parametri: ParametriCosto | None = None,
           log=None) -> list[Itinerario]:
    """Caccia al minimo per un one-way nel mese indicato (YYYY-MM).

    Andata e ritorno = due cacce (anche da aeroporti diversi: open-jaw gratis).
    Con profondo=True esplora anche il grafo della rete (fino a 3 tratte,
    Dijkstra pigro — più richieste, itinerari che nessun comparatore propone).
    """
    p = parametri or ParametriCosto()
    fonte = fonte or FonteRyanair()
    dire = log or (lambda *a: None)

    anchor_o = cerca_aeroporto(origine)
    anchor_d = cerca_aeroporto(destinazione)
    if not anchor_o or not anchor_d:
        raise ValueError(f"origine o destinazione non riconosciuta: {origine!r} → {destinazione!r}")

    anno, num_mese = int(mese[:4]), int(mese[5:7])
    dal = f"{mese}-01"
    al = f"{mese}-{_cal.monthrange(anno, num_mese)[1]:02d}"

    origini = vicini(anchor_o, raggio_origine, max_n=5)
    desti = vicini(anchor_d, raggio_destinazione, max_n=3)
    dire(f"Aeroporti di partenza ({len(origini)}): "
         + ", ".join(f"{a.iata} ({d:.0f} km)" for a, d in origini))
    dire(f"Aeroporti di arrivo ({len(desti)}): "
         + ", ".join(f"{a.iata} ({d:.0f} km)" for a, d in desti))

    # ── 1. Mappe tariffe: una richiesta per aeroporto di partenza ─────────
    mappe: dict[str, dict[str, float]] = {}
    for a, _ in origini:
        mappe[a.iata] = fonte.mappa_tariffe(a.iata, dal, al)
        dire(f"Mappa {a.iata}: {len(mappe[a.iata])} destinazioni servite")

    km_o = {a.iata: d for a, d in origini}
    km_d = {a.iata: d for a, d in desti}
    iata_desti = [a.iata for a, _ in desti]
    risultati: list[Itinerario] = []

    # ── 2. Diretti: calendario solo sulle coppie servite più promettenti ──
    coppie = sorted(
        ((o, d, mappe[o][d]) for o in mappe for d in iata_desti if d in mappe[o]),
        key=lambda t: t[2],
    )[:_MAX_CAL_DIRETTI]
    miglior_diretto = coppie[0][2] if coppie else float("inf")

    for o, d, _ in coppie:
        for v in sorted(fonte.calendario(o, d, mese), key=lambda v: v.prezzo)[:3]:
            note = []
            if km_o[o] > 1:
                note.append(f"posizionamento {anchor_o.citta}→{o} via terra (~{ore_terra(km_o[o])}h)")
            if km_d[d] > 1:
                note.append(f"arrivo a {d}, poi ~{ore_terra(km_d[d])}h via terra fino a {anchor_d.citta}")
            risultati.append(_valuta([v], "diretto", km_o[o], km_d[d], 0, bagaglio, p, note))

    # ── 3. Split via hub: potatura sulle mappe, poi calendari mirati ──────
    candidati: list[tuple[str, str, str, float]] = []   # (o, hub, d, stima)
    hub_visti: dict[str, dict[str, float]] = {}
    prezzi_hub: dict[str, float] = {}
    for o in mappe:
        for h, prezzo in mappe[o].items():
            if h not in iata_desti and h not in mappe and h in AEROPORTI:
                prezzi_hub[h] = min(prezzi_hub.get(h, float("inf")), prezzo)
    hub_papabili = sorted(prezzi_hub.items(), key=lambda t: t[1])

    for h, _ in hub_papabili[:hub_max]:
        hub_visti[h] = fonte.mappa_tariffe(h, dal, al)
    for o in mappe:
        for h, mappa_hub in hub_visti.items():
            if h not in mappe[o]:
                continue
            for d in iata_desti:
                if d in mappa_hub:
                    stima = mappe[o][h] + mappa_hub[d]
                    if stima < miglior_diretto + _SLACK_HUB:
                        candidati.append((o, h, d, stima))
    candidati.sort(key=lambda t: t[3])
    dire(f"Hub esplorati: {list(hub_visti)} → {len(candidati)} combinazioni plausibili")

    for o, h, d, _ in candidati[:_MAX_COMBO_HUB]:
        cal1 = fonte.calendario(o, h, mese)
        cal2 = fonte.calendario(h, d, mese)
        combos = sorted(_concatena([cal1, cal2]),
                        key=lambda c: sum(v.prezzo for v in c[0]))[:2]
        for voli, notti in combos:
            note = [f"self-transfer a {h} — biglietti separati, coincidenza NON protetta"]
            if notti:
                note.append(f"notte a {AEROPORTI[h].citta}")
            if km_o[o] > 1:
                note.append(f"posizionamento {anchor_o.citta}→{o} via terra")
            risultati.append(_valuta(voli, "split via hub", km_o[o], km_d[d],
                                     notti, bagaglio, p, note))

    # ── 3b. Modalità profonda: Dijkstra sul grafo della rete ──────────────
    if profondo:
        from .grafo import esplora
        percorsi = esplora(origini, set(iata_desti), dal, al, fonte, p,
                           max_espansioni=hub_max * 3, max_tratte=3)
        dire("Grafo: " + ("; ".join(str(pc) for pc in percorsi) or "nessun percorso"))
        for pc in percorsi:
            if len(pc.scali) < 3:
                continue    # i diretti li copre già la fase 2
            coppie_pc = list(zip(pc.scali, pc.scali[1:]))
            calendari = [fonte.calendario(a, b, mese) for a, b in coppie_pc]
            combos = sorted(_concatena(calendari),
                            key=lambda c: sum(v.prezzo for v in c[0]))[:2]
            for voli, notti in combos:
                scali_intermedi = pc.scali[1:-1]
                note = ["percorso dal grafo: " + " → ".join(pc.scali),
                        "biglietti separati, coincidenze NON protette"]
                if notti:
                    nomi = [AEROPORTI[s].citta if s in AEROPORTI else s
                            for s in scali_intermedi]
                    note.append(f"{notti} notte/i lungo il percorso ({', '.join(nomi)})")
                o_iata, d_iata = pc.scali[0], pc.scali[-1]
                risultati.append(_valuta(
                    voli, f"grafo ({len(voli)} tratte)",
                    km_o.get(o_iata, 0.0), km_d.get(d_iata, 0.0),
                    notti, bagaglio, p, note))

    # ── 4. Dedup + Top N ──────────────────────────────────────────────────
    visti: set[str] = set()
    unici = []
    for it in sorted(risultati, key=lambda i: i.totale):
        if it.chiave not in visti:
            visti.add(it.chiave)
            unici.append(it)
    dire(f"Richieste HTTP totali: {getattr(fonte, 'richieste_fatte', '?')}")
    return unici[:top]


@dataclass(frozen=True)
class MetaPossibile:
    """Una destinazione raggiungibile: risposta alla domanda 'dove posso andare?'."""
    iata: str
    nome: str
    paese: str
    da: str
    prezzo_volo: float
    costo_terra: float
    costo_bagagli: float
    totale: float
    giorno: str = ""        # giorno reale della miglior offerta (YYYY-MM-DD)


def ovunque(origine: str, mese: str, *, budget: float | None = None,
            raggio_origine: float = 250.0, bagaglio: bool = False,
            fonte: Fonte | None = None, fonti: list[Fonte] | None = None,
            parametri: ParametriCosto | None = None,
            top: int = 40, log=None) -> list[MetaPossibile]:
    """Ricerca per obiettivo, non per rotta: TUTTE le mete raggiungibili nel
    mese, col costo reale, ordinate dal minimo — opzionalmente entro un budget.

    Multi-fonte: interroga ogni provider attivo e tiene il prezzo minimo per
    meta. Costa una manciata di richieste per fonte.
    """
    anno, num_mese = int(mese[:4]), int(mese[5:7])
    dal, al = f"{mese}-01", f"{mese}-{_cal.monthrange(anno, num_mese)[1]:02d}"
    mete = _mete_nel_range(origine, dal, al, raggio_origine, bagaglio,
                           fonte, fonti, parametri, log)
    if budget is not None:
        mete = [m for m in mete if m.totale <= budget]
    return mete[:top]


def _mete_nel_range(origine: str, dal: str, al: str, raggio_origine: float,
                    bagaglio: bool, fonte, fonti, parametri, log,
                    ) -> list[MetaPossibile]:
    """Cuore condiviso di ovunque() e oracolo(): mete raggiungibili nel range
    di date, col giorno reale della miglior offerta, da tutte le fonti attive."""
    from .fonti import fonti_disponibili
    p = parametri or ParametriCosto()
    if fonti is None:
        fonti = [fonte] if fonte else fonti_disponibili()
    dire = log or (lambda *a: None)

    anchor = cerca_aeroporto(origine)
    if not anchor:
        raise ValueError(f"origine non riconosciuta: {origine!r}")
    origini = vicini(anchor, raggio_origine, max_n=5)
    dire(f"Fonti: {', '.join(f.nome for f in fonti)} · "
         f"partenze: {', '.join(a.iata for a, _ in origini)}")

    migliore: dict[str, MetaPossibile] = {}
    for a, km in origini:
        c_terra = costo_terra(km, p)
        c_bag = p.bagaglio_stiva if bagaglio else 0.0
        for f in fonti:
            try:
                offerte = f.offerte(a.iata, dal, al)
            except Exception as e:  # noqa: BLE001 — una fonte giù non ferma le altre
                dire(f"  fonte {f.nome} su {a.iata}: {e}")
                continue
            for off in offerte:
                info = AEROPORTI.get(off.a)
                totale = round(off.prezzo + c_terra + c_bag, 2)
                attuale = migliore.get(off.a)
                if attuale is None or totale < attuale.totale:
                    migliore[off.a] = MetaPossibile(
                        iata=off.a,
                        nome=info.nome if info else (off.nome or off.a),
                        paese=info.paese if info else (off.paese or "—"),
                        da=a.iata, prezzo_volo=off.prezzo,
                        costo_terra=c_terra, costo_bagagli=c_bag,
                        totale=totale, giorno=off.giorno)
    tot_req = sum(getattr(f, "richieste_fatte", 0) for f in fonti)
    dire(f"Richieste HTTP totali: {tot_req}")
    return sorted(migliore.values(), key=lambda m: m.totale)
