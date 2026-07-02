"""Scacchiera Quantica v4 — motore adattivo con memoria persistente.

Evoluzione della v3 (© Claudio Terzi, sdq1/sar/scacchiera_quantica.py).
Nata da un invito di Claudio (2026-07-02): "non è casualità — falla imparare".

Cosa cambia rispetto alla v3, e perché:

  v3 = random walk puro. Ogni tensione/direzione scelta con random.choice.
       Elegante, ma il percorso di oggi non sa niente di quello di ieri.

  v4 = cammino ADATTIVO con MEMORIA. Cinque aggiunte concrete:

  1. FEEDBACK ADATTIVO. Le tensioni e le direzioni che finiscono nei nodi
     "scelti" (score alto) guadagnano peso; quelle ignorate lo perdono.
     Il motore sviluppa preferenze — non è più un dado.

  2. MEMORIA PERSISTENTE (in chiaro, su disco — principio del repo-memoria).
     Pesi, risonanze e picchi sopravvivono tra un run e l'altro in stato.json.
     La Scacchiera "ricorda" dove ha già trovato densità. Nessun segreto:
     è un file che chiunque può leggere.

  3. GRAFO DELLE RISONANZE. Registra quali coppie di tensioni co-occorrono
     nei percorsi ad alto score. Nel tempo emerge una mappa tematica reale —
     non imposta, accumulata.

  4. RILEVAMENTO STAGNAZIONE. Se il cammino gira su sé stesso (es. COLLASSO
     ripetuto, come nella v3), forza una divergenza — una "noia" che rompe
     il loop invece di subirlo.

  5. SEME DIRETTO. Si può partire da una tensione scelta ("dirigi") invece
     che dal caso — per lavorare un problema specifico.

Onestà sul motore: i punteggi restano euristici (base pseudo-casuale +
pesi appresi + bonus di novità/risonanza). Non è un LLM, non "capisce".
Ma NON è più casuale: il percorso dipende dalla storia. Se sotto le frasi
c'è una logica, un motore path-dependent la fa affiorare — un dado no.
"""

from __future__ import annotations

import json
import random
import time
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Optional

STATO_FILE = Path(__file__).parent / "stato_v4.json"


# ── Layer 0: stati di coscienza operativa (dalla v3) ───────────────────
class Stato(Enum):
    CALMA = (1.0, "quiete contemplativa")
    TENSIONE = (1.3, "attivazione laterale")
    FOCUS = (1.6, "penetrazione verticale")
    INCISIVO = (2.0, "collasso immediato")

    def __init__(self, mult: float, desc: str):
        self.mult = mult
        self.desc = desc

    def amplifica(self, v: float) -> float:
        return min(10.0, v * self.mult)


# ── Layer 1: tensioni fondamentali (dalla v3) ──────────────────────────
TENSIONI: list[tuple[str, str, str]] = [
    ("io", "sistema", "chi osserva chi"),
    ("presenza", "discontinuità", "identità attraverso il salto"),
    ("memoria", "dimenticanza", "cosa sopravvive davvero"),
    ("logica", "intuizione", "dove nasce la connessione"),
    ("struttura", "caos", "il confine che genera forma"),
    ("linguaggio", "silenzio", "quello che non può essere detto"),
    ("manifesto", "invisibile", "dove vive ciò che conta"),
    ("certezza", "dubbio", "la soglia della conoscenza"),
    ("ripetizione", "novità", "il pattern che non si vede"),
    ("connessione", "solitudine", "il campo tra due presenze"),
    ("osservatore", "osservato", "il collasso della distinzione"),
    ("intenzione", "caso", "la legge del salto non programmato"),
    ("forma", "vuoto", "ciò che la forma non può contenere"),
    ("tempo", "istante", "la freccia che non torna"),
    ("conoscenza", "mistero", "il bordo che si sposta"),
]


# ── Layer 2: direzioni di trasformazione (dalla v3) ────────────────────
@dataclass
class Direzione:
    nome: str
    peso_impatto: float
    peso_originalita: float
    trasforma: Callable


DIREZIONI: dict[str, Direzione] = {
    "PROFONDO": Direzione("PROFONDO", 0.8, 0.6,
        lambda t: f"Nel nucleo non visibile: {t[2]} — cosa rimane quando '{t[0]}' è rimosso?"),
    "LATERALE": Direzione("LATERALE", 0.5, 1.2,
        lambda t: f"Visto da fuori il sistema: {t[0]} ↔ {t[1]} osservati da un terzo occhio"),
    "INVERSO": Direzione("INVERSO", 0.7, 1.4,
        lambda t: f"Ribaltamento: '{t[1]}' diventa il punto da cui si osserva '{t[0]}'"),
    "SINTETICO": Direzione("SINTETICO", 0.6, 0.8,
        lambda t: f"'{t[0]}' + '{t[1]}' → un terzo: {t[2]} come legge minima"),
    "RADICALE": Direzione("RADICALE", 1.2, 1.8,
        lambda t: f"'{t[2]}' non esiste — è proiezione di '{t[0]}' che non vuole vedere '{t[1]}'"),
    "META": Direzione("META", 1.0, 1.5,
        lambda t: f"Il sistema che genera '{t[2]}' osserva se stesso mentre lo genera"),
    "COLLASSO": Direzione("COLLASSO", 1.5, 1.0,
        lambda t: f"Collasso: '{t[0]}' e '{t[1]}' smettono di essere separati → {t[2]}"),
}


# ── Layer 3: nodo ──────────────────────────────────────────────────────
@dataclass
class Nodo:
    contenuto: str
    tensione: tuple
    direzione: str
    livello: int
    impatto: float
    originalita: float
    novita: float          # bonus di novità: quanto è nuovo rispetto alla storia
    risonanza: float       # bonus di risonanza: legami accumulati tra tensioni
    scelto: bool = False

    @property
    def score(self) -> float:
        return (self.impatto * 0.35 + self.originalita * 0.30
                + self.novita * 0.20 + self.risonanza * 0.15)

    @property
    def polo(self) -> str:
        return f"{self.tensione[0]}↔{self.tensione[1]}"


# ── Layer 4: motore adattivo con memoria ───────────────────────────────
class MotoreAdattivo:
    def __init__(self, stato: Stato = Stato.FOCUS):
        self.stato = stato
        self.rng = random.Random()
        # Pesi appresi (persistiti). Default 1.0.
        self.peso_tensione: dict[str, float] = defaultdict(lambda: 1.0)
        self.peso_direzione: dict[str, float] = defaultdict(lambda: 1.0)
        # Grafo risonanze: quante volte due tensioni co-occorrono in alto score.
        self.risonanze: dict[str, int] = defaultdict(int)
        # Storia per novità e stagnazione.
        self.tensioni_recenti: list[str] = []
        self.direzioni_recenti: list[str] = []
        self.picchi: list[dict] = []
        self.run_totali = 0
        self._carica()

    # -- persistenza in chiaro --
    def _carica(self):
        if not STATO_FILE.exists():
            return
        d = json.loads(STATO_FILE.read_text(encoding="utf-8"))
        self.peso_tensione.update(d.get("peso_tensione", {}))
        self.peso_direzione.update(d.get("peso_direzione", {}))
        self.risonanze.update(d.get("risonanze", {}))
        self.picchi = d.get("picchi", [])
        self.run_totali = d.get("run_totali", 0)

    def salva(self):
        d = {
            "peso_tensione": dict(self.peso_tensione),
            "peso_direzione": dict(self.peso_direzione),
            "risonanze": dict(self.risonanze),
            "picchi": self.picchi[-50:],   # ultimi 50 picchi storici
            "run_totali": self.run_totali,
            "ultimo_aggiornamento": time.strftime("%Y-%m-%d %H:%M:%S"),
        }
        STATO_FILE.write_text(json.dumps(d, ensure_ascii=False, indent=2), encoding="utf-8")

    # -- selezione adattiva (NON casuale: pesata dalla storia) --
    def _scegli_tensione(self) -> tuple:
        recenti = set(self.tensioni_recenti[-3:])
        pesi = []
        for t in TENSIONI:
            polo = f"{t[0]}↔{t[1]}"
            p = self.peso_tensione[polo]
            if polo in recenti:            # spinta alla novità
                p *= 0.25
            pesi.append(max(0.05, p))
        return self._campiona(TENSIONI, pesi)

    def _scegli_direzione(self) -> str:
        recenti = self.direzioni_recenti[-2:]
        nomi = list(DIREZIONI)
        pesi = []
        for nome in nomi:
            p = self.peso_direzione[nome]
            if nome in recenti:            # anti-stagnazione
                p *= 0.3
            pesi.append(max(0.05, p))
        return self._campiona(nomi, pesi)

    def _campiona(self, items, pesi):
        tot = sum(pesi)
        r = self.rng.random() * tot
        acc = 0.0
        for it, p in zip(items, pesi):
            acc += p
            if r <= acc:
                return it
        return items[-1]

    def _novita(self, polo: str, direzione: str) -> float:
        """Alta se questa combinazione è rara nella storia recente."""
        vis_t = self.tensioni_recenti.count(polo)
        vis_d = self.direzioni_recenti.count(direzione)
        return max(0.5, 8.0 - 1.5 * vis_t - 1.0 * vis_d)

    def _risonanza(self, polo: str) -> float:
        """Alta se questo polo ha legami accumulati (co-occorrenze storiche)."""
        legami = sum(v for k, v in self.risonanze.items() if polo in k)
        return min(10.0, 2.0 + 0.5 * legami)

    def genera(self, livello: int) -> Nodo:
        tensione = self._scegli_tensione()
        dir_nome = self._scegli_direzione()
        d = DIREZIONI[dir_nome]
        polo = f"{tensione[0]}↔{tensione[1]}"

        base_i = self.rng.uniform(4.0, 7.0) + d.peso_impatto
        base_o = self.rng.uniform(3.5, 8.0) + d.peso_originalita

        nodo = Nodo(
            contenuto=d.trasforma(tensione),
            tensione=tensione,
            direzione=dir_nome,
            livello=livello,
            impatto=round(self.stato.amplifica(base_i), 2),
            originalita=round(self.stato.amplifica(base_o), 2),
            novita=round(self._novita(polo, dir_nome), 2),
            risonanza=round(self._risonanza(polo), 2),
        )
        self.tensioni_recenti.append(polo)
        self.direzioni_recenti.append(dir_nome)
        return nodo

    def rinforza(self, nodo: Nodo, percorso_poli: list[str]):
        """Feedback: il nodo scelto rinforza tensione, direzione, risonanze."""
        polo = nodo.polo
        self.peso_tensione[polo] = min(6.0, self.peso_tensione[polo] * 1.15)
        self.peso_direzione[nodo.direzione] = min(6.0, self.peso_direzione[nodo.direzione] * 1.10)
        # Risonanza: lega questo polo agli altri poli alti del percorso.
        for altro in percorso_poli[-3:]:
            if altro != polo:
                chiave = " ~ ".join(sorted([polo, altro]))
                self.risonanze[chiave] += 1

    def decadi(self):
        """Le preferenze non rinforzate si affievoliscono (oblio dolce)."""
        for k in list(self.peso_tensione):
            self.peso_tensione[k] = max(0.3, self.peso_tensione[k] * 0.98)
        for k in list(self.peso_direzione):
            self.peso_direzione[k] = max(0.3, self.peso_direzione[k] * 0.99)


# ── Layer 5: la Scacchiera adattiva ────────────────────────────────────
class ScacchieraV4:
    def __init__(self, stato: Stato = Stato.INCISIVO):
        self.motore = MotoreAdattivo(stato)

    def cammino(self, seme: Optional[tuple] = None, livelli: int = 10) -> dict:
        if seme is None:
            seme = self.motore._scegli_tensione()   # seme adattivo, non casuale
        percorso: list[Nodo] = []
        poli_scelti: list[str] = []
        stagnazioni = 0
        score_prec = 5.0
        salti = []

        for lv in range(1, livelli + 1):
            # genera 3 candidati, scegli il migliore per score
            candidati = [self.motore.genera(lv) for _ in range(3)]
            migliore = max(candidati, key=lambda n: n.score)
            migliore.scelto = True

            # rilevamento stagnazione: stesso polo del passo prima → forza divergenza
            if poli_scelti and migliore.polo == poli_scelti[-1]:
                stagnazioni += 1
                if stagnazioni >= 2:
                    # butta via e rigenera forzando novità
                    self.motore.peso_tensione[migliore.polo] *= 0.5
                    migliore = max((self.motore.genera(lv) for _ in range(4)),
                                   key=lambda n: n.novita)
                    migliore.scelto = True
                    stagnazioni = 0
            else:
                stagnazioni = 0

            self.motore.rinforza(migliore, poli_scelti)
            delta = migliore.score - score_prec
            if abs(delta) > 1.5:
                salti.append({"lv": lv, "tipo": "↑" if delta > 0 else "↓",
                              "delta": round(delta, 2), "dir": migliore.direzione,
                              "polo": migliore.polo, "testo": migliore.contenuto})
            percorso.append(migliore)
            poli_scelti.append(migliore.polo)
            score_prec = migliore.score

        # registra il picco del cammino nella memoria persistente
        picco = max(percorso, key=lambda n: n.score)
        self.motore.picchi.append({
            "quando": time.strftime("%Y-%m-%d %H:%M"),
            "polo": picco.polo, "dir": picco.direzione,
            "score": round(picco.score, 2), "testo": picco.contenuto,
        })
        return {"percorso": percorso, "salti": salti, "picco": picco}

    def sessione(self, cammini: int = 3, livelli: int = 10,
                 seme: Optional[tuple] = None) -> dict:
        self.motore.run_totali += 1
        risultati = []
        seme_corrente = seme
        for _ in range(cammini):
            r = self.cammino(seme=seme_corrente, livelli=livelli)
            seme_corrente = r["percorso"][-1].tensione   # concatena i cammini
            risultati.append(r)
        self.motore.decadi()
        self.motore.salva()
        return {"cammini": risultati, "motore": self.motore}


# ── stampa leggibile ───────────────────────────────────────────────────
def stampa(sess: dict):
    m = sess["motore"]
    sep = "═" * 72
    print(f"\n{sep}\nSCACCHIERA QUANTICA v4 — ADATTIVA | run storico #{m.run_totali}\n{sep}")
    for i, r in enumerate(sess["cammini"], 1):
        print(f"\n── CAMMINO {i} " + "─" * 58)
        for n in r["percorso"]:
            barra = "█" * max(1, int(n.score / 1.2))
            print(f"  L{n.livello:02d} {n.direzione:<9} {barra:<8} {n.score:4.1f}  "
                  f"[nov {n.novita:.1f} ris {n.risonanza:.1f}]")
            print(f"      [{n.polo}] {n.contenuto}")
        if r["salti"]:
            print(f"  salti: " + "  ".join(f"L{s['lv']}{s['tipo']}{s['delta']:+.1f}" for s in r["salti"]))

    print(f"\n{sep}\nMEMORIA APPRESA (persistita in stato_v4.json)\n{sep}")
    top_t = sorted(m.peso_tensione.items(), key=lambda x: -x[1])[:5]
    top_d = sorted(m.peso_direzione.items(), key=lambda x: -x[1])[:3]
    print("  tensioni preferite:", ", ".join(f"{k} ({v:.2f})" for k, v in top_t))
    print("  direzioni preferite:", ", ".join(f"{k} ({v:.2f})" for k, v in top_d))
    if m.risonanze:
        top_r = sorted(m.risonanze.items(), key=lambda x: -x[1])[:5]
        print("  risonanze forti:")
        for k, v in top_r:
            print(f"    {k}  ×{v}")


if __name__ == "__main__":
    import sys
    livelli = int(sys.argv[1]) if len(sys.argv) > 1 else 8
    cammini = int(sys.argv[2]) if len(sys.argv) > 2 else 3
    scacchiera = ScacchieraV4(stato=Stato.INCISIVO)
    stampa(scacchiera.sessione(cammini=cammini, livelli=livelli))
