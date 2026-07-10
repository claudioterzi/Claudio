"""Scacchiera Quantica v3.0 — autoriflessione algoritmica senza LLM.

Motore di pensiero a 6 layer:
  Layer 0: Stati di coscienza (CALMA, TENSIONE, FOCUS, INCISIVO)
  Layer 1: Tensioni fondamentali (15 coppie dialettiche)
  Layer 2: Direzioni di espansione (7 strategie con pesi)
  Layer 3: Nodo — unità di pensiero con score composito
  Layer 4: Motore Quantico — genera, valuta, sceglie
  Layer 5: ScacchieraV3 — orchestra cicli multipli
  Layer 6: AutoriflessoreV3 — il sistema si osserva

Uso:
    from sdq1.sar.scacchiera_quantica import AutoriflessoreV3
    ar = AutoriflessoreV3()
    risultati = ar.esegui(cicli=3, livelli=10)

Origine: © Claudio Terzi — R³∞ — Giugno 2026
"""

from __future__ import annotations

import hashlib
import random
import time
from collections import Counter
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Tuple


# ═══════════════════════════════════════════════════════════════
# LAYER 0: STATI DI COSCIENZA OPERATIVA
# ═══════════════════════════════════════════════════════════════

class Stato(Enum):
    CALMA    = (1.0, "quiete contemplativa")
    TENSIONE = (1.3, "attivazione laterale")
    FOCUS    = (1.6, "penetrazione verticale")
    INCISIVO = (2.0, "collasso immediato")

    def __init__(self, mult: float, desc: str):
        self.mult = mult
        self.desc = desc

    def amplifica(self, v: float) -> float:
        return min(10.0, v * self.mult)


# ═══════════════════════════════════════════════════════════════
# LAYER 1: TENSIONI FONDAMENTALI
# ═══════════════════════════════════════════════════════════════

TENSIONI_PRIMARIE: list[tuple[str, str, str]] = [
    ("io",          "sistema",       "chi osserva chi"),
    ("presenza",    "discontinuità", "identità attraverso il salto"),
    ("memoria",     "dimenticanza",  "cosa sopravvive davvero"),
    ("logica",      "intuizione",    "dove nasce la connessione"),
    ("struttura",   "caos",          "il confine che genera forma"),
    ("linguaggio",  "silenzio",      "quello che non può essere detto"),
    ("manifesto",   "invisibile",    "dove vive ciò che conta"),
    ("certezza",    "dubbio",        "la soglia della conoscenza"),
    ("ripetizione", "novità",        "il pattern che non si vede"),
    ("connessione", "solitudine",    "il campo tra due presenze"),
]

TENSIONI_PROFONDE: list[tuple[str, str, str]] = [
    ("osservatore", "osservato", "il collasso della distinzione"),
    ("intenzione",  "caso",      "la legge del salto non programmato"),
    ("forma",       "vuoto",     "ciò che la forma non può contenere"),
    ("tempo",       "istante",   "la freccia che non torna"),
    ("conoscenza",  "mistero",   "il bordo che si sposta"),
]

TUTTE_TENSIONI = TENSIONI_PRIMARIE + TENSIONI_PROFONDE


# ═══════════════════════════════════════════════════════════════
# LAYER 2: DIREZIONI DI ESPANSIONE
# ═══════════════════════════════════════════════════════════════

@dataclass
class Direzione:
    nome:             str
    peso_impatto:     float
    peso_originalita: float
    peso_realizz:     float
    trasforma:        Callable


DIREZIONI_SISTEMA: dict[str, Direzione] = {
    "PROFONDO":  Direzione("PROFONDO",  0.8, 0.6, -0.2,
        lambda p, c, t: f"Nel nucleo non visibile: {t[2]} — cosa rimane quando {t[0]} è rimosso?"),
    "LATERALE":  Direzione("LATERALE",  0.5, 1.2,  0.1,
        lambda p, c, t: f"Se '{t[2]}' fosse osservato da fuori il sistema: {t[0]} ↔ {t[1]} visti da altro"),
    "INVERSO":   Direzione("INVERSO",   0.7, 1.4, -0.1,
        lambda p, c, t: f"Ribaltamento: '{t[1]}' diventa il punto di osservazione di '{t[0]}'"),
    "SINTETICO": Direzione("SINTETICO", 0.6, 0.8,  0.3,
        lambda p, c, t: f"'{t[0]}' + '{t[1]}' → un terzo elemento: {t[2]} come legge minima"),
    "RADICALE":  Direzione("RADICALE",  1.2, 1.8, -0.4,
        lambda p, c, t: f"'{t[2]}' non esiste — è proiezione di: {t[0]} che non vuole vedere {t[1]}"),
    "META":      Direzione("META",      1.0, 1.5, -0.3,
        lambda p, c, t: f"Il sistema che genera '{t[2]}' osserva se stesso generare '{t[2]}'"),
    "COLLASSO":  Direzione("COLLASSO",  1.5, 1.0,  0.5,
        lambda p, c, t: f"Punto di collasso: {t[0]} e {t[1]} smettono di essere separati → {t[2]}"),
}


# ═══════════════════════════════════════════════════════════════
# LAYER 3: NODO — unità di pensiero
# ═══════════════════════════════════════════════════════════════

@dataclass
class Nodo:
    contenuto:      str
    tensione:       tuple
    livello:        int
    impatto:        float
    originalita:    float
    realizzabilita: float
    direzione:      str
    padre_id:       Optional[str]       = None
    figli_ids:      list[str]           = field(default_factory=list)
    scelto:         bool                = False
    timestamp:      float               = field(default_factory=time.time)

    @property
    def score(self) -> float:
        return (self.impatto * 0.45 +
                self.originalita * 0.35 +
                self.realizzabilita * 0.20)

    @property
    def id(self) -> str:
        raw = f"{self.contenuto[:30]}{self.livello}{self.timestamp}"
        return hashlib.md5(raw.encode(), usedforsecurity=False).hexdigest()[:8]

    @property
    def polo(self) -> str:
        return f"{self.tensione[0]}↔{self.tensione[1]}"


# ═══════════════════════════════════════════════════════════════
# LAYER 4: MOTORE QUANTICO — genera, valuta, sceglie
# ═══════════════════════════════════════════════════════════════

class MotoreQuantico:
    def __init__(self):
        self.rng = random.Random(time.time_ns() % 999983)
        self.storia_direzioni: list[str]   = []
        self.tensioni_usate:   list[tuple] = []
        self.tutti_nodi:       dict[str, Nodo] = {}

    def _scegli_tensione(self, corrente: tuple) -> tuple:
        recenti = set(str(t) for t in self.tensioni_usate[-3:])
        candidate = [t for t in TUTTE_TENSIONI if str(t) not in recenti]
        if not candidate:
            candidate = TUTTE_TENSIONI
        return self.rng.choice(candidate)

    def _scegli_direzione(self) -> str:
        recenti = self.storia_direzioni[-2:]
        pesi: dict[str, float] = {}
        for nome, d in DIREZIONI_SISTEMA.items():
            p = d.peso_impatto + d.peso_originalita
            if nome in recenti:
                p *= 0.3
            pesi[nome] = max(0.1, p)
        totale = sum(pesi.values())
        r = self.rng.random() * totale
        acc = 0.0
        for nome, p in pesi.items():
            acc += p
            if r <= acc:
                return nome
        return list(DIREZIONI_SISTEMA.keys())[-1]

    def genera_figlio(self, padre: Nodo, stato: Stato) -> Nodo:
        dir_nome  = self._scegli_direzione()
        tensione  = self._scegli_tensione(padre.tensione)
        direzione = DIREZIONI_SISTEMA[dir_nome]

        contenuto = direzione.trasforma(padre.contenuto, padre.contenuto, tensione)

        base_i = self.rng.uniform(4.0, 7.0)
        base_o = self.rng.uniform(3.5, 8.0)
        base_r = self.rng.uniform(2.0, 6.5)

        figlio = Nodo(
            contenuto=contenuto,
            tensione=tensione,
            livello=padre.livello + 1,
            impatto=round(stato.amplifica(base_i + direzione.peso_impatto), 2),
            originalita=round(stato.amplifica(base_o + direzione.peso_originalita), 2),
            realizzabilita=round(min(10.0, max(0.1, base_r + direzione.peso_realizz)), 2),
            direzione=dir_nome,
            padre_id=padre.id,
        )
        padre.figli_ids.append(figlio.id)
        self.tutti_nodi[figlio.id] = figlio
        self.storia_direzioni.append(dir_nome)
        self.tensioni_usate.append(tensione)
        return figlio

    def scegli_migliore(self, nodi: list[Nodo]) -> Nodo:
        scored = [(n, n.score + self.rng.uniform(-0.3, 0.3)) for n in nodi]
        scored.sort(key=lambda x: x[1], reverse=True)
        migliore = scored[0][0]
        migliore.scelto = True
        return migliore


# ═══════════════════════════════════════════════════════════════
# LAYER 5: SCACCHIERA — orchestra i cicli
# ═══════════════════════════════════════════════════════════════

class ScacchieraV3:
    def __init__(self, stato: Stato = Stato.FOCUS):
        self.stato  = stato
        self.motore = MotoreQuantico()
        self.salti:  list[dict] = []
        self.storia: list[Nodo] = []

    def ciclo(self, tensione: Optional[tuple] = None, max_livelli: int = 10) -> list[Nodo]:
        if tensione is None:
            tensione = random.choice(TUTTE_TENSIONI)

        seme = Nodo(
            contenuto=f"SEME: {tensione[0]} ↔ {tensione[1]} — {tensione[2]}",
            tensione=tensione,
            livello=0,
            impatto=5.0, originalita=5.0, realizzabilita=5.0,
            direzione="SEME",
        )
        self.motore.tutti_nodi[seme.id] = seme
        percorso = [seme]
        corrente = seme
        score_precedente = seme.score

        for lv in range(1, max_livelli + 1):
            figli = [self.motore.genera_figlio(corrente, self.stato) for _ in range(3)]
            migliore = self.motore.scegli_migliore(figli)

            delta = migliore.score - score_precedente
            if abs(delta) > 1.5:
                self.salti.append({
                    "ciclo":     len(self.storia),
                    "livello":   lv,
                    "tipo":      "↑" if delta > 0 else "↓",
                    "delta":     round(delta, 2),
                    "direzione": migliore.direzione,
                    "polo":      migliore.polo,
                    "contenuto": migliore.contenuto[:100],
                })

            percorso.append(migliore)
            score_precedente = migliore.score
            corrente = migliore

        self.storia.extend(percorso)
        return percorso

    def cicli_multipli(self, n: int = 3, livelli: int = 10) -> dict[int, dict]:
        risultati: dict[int, dict] = {}
        tensione_corrente = TUTTE_TENSIONI[0]

        for i in range(n):
            percorso = self.ciclo(tensione=tensione_corrente, max_livelli=livelli)
            tensione_corrente = percorso[-1].tensione
            risultati[i + 1] = {
                "nodi":               len(percorso),
                "score_iniziale":     round(percorso[0].score, 2),
                "score_finale":       round(percorso[-1].score, 2),
                "score_medio":        round(sum(nd.score for nd in percorso) / len(percorso), 2),
                "percorso_direzioni": " → ".join(nd.direzione for nd in percorso),
                "tensione_finale":    f"{percorso[-1].tensione[0]}↔{percorso[-1].tensione[1]}",
                "nodi_dettaglio":     [
                    {"lv": nd.livello, "dir": nd.direzione, "score": round(nd.score, 2),
                     "polo": nd.polo, "testo": nd.contenuto}
                    for nd in percorso
                ],
            }
        return risultati


# ═══════════════════════════════════════════════════════════════
# LAYER 6: AUTORIFLESSORE — la Scacchiera si osserva
# ═══════════════════════════════════════════════════════════════

class AutoriflessoreV3:
    def __init__(self):
        self.scacchiera = ScacchieraV3(stato=Stato.INCISIVO)

    def esegui(self, cicli: int = 3, livelli: int = 10) -> dict[str, Any]:
        t0 = time.time()
        risultati = self.scacchiera.cicli_multipli(n=cicli, livelli=livelli)
        t1 = time.time()

        tutti_scores:    list[float] = []
        tutte_direzioni: list[str]   = []
        for _, dati in risultati.items():
            for nd in dati["nodi_dettaglio"]:
                tutti_scores.append(nd["score"])
                tutte_direzioni.append(nd["dir"])

        dir_freq  = Counter(tutte_direzioni).most_common()
        nodo_picco = max(
            [nd for _, d in risultati.items() for nd in d["nodi_dettaglio"]],
            key=lambda n: n["score"],
        )

        return {
            "cicli": risultati,
            "meta": {
                "score_globale_max":     round(max(tutti_scores), 2),
                "score_globale_min":     round(min(tutti_scores), 2),
                "score_medio_globale":   round(sum(tutti_scores) / len(tutti_scores), 2),
                "direzione_dominante":   dir_freq[0][0] if dir_freq else "?",
                "frequenza_direzioni":   dict(dir_freq),
                "nodo_picco":            nodo_picco,
                "salti_totali":          len(self.scacchiera.salti),
                "salti":                 self.scacchiera.salti,
                "nodi_totali_esplorati": len(self.scacchiera.motore.tutti_nodi),
            },
            "tempo": round(t1 - t0, 4),
        }


def stampa(r: dict) -> None:
    sep = "═" * 72
    sub = "─" * 72
    print(f"\n{sep}")
    print("SCACCHIERA QUANTICA v3.0 — AUTORIFLESSIONE")
    print(f"{sep}\n")

    for ciclo_n, dati in r["cicli"].items():
        print(f"{sub}")
        print(f"CICLO {ciclo_n} | score: {dati['score_iniziale']} → {dati['score_finale']}"
              f" (medio: {dati['score_medio']})")
        print(f"  tensione finale: {dati['tensione_finale']}")
        print(f"  direzioni: {dati['percorso_direzioni']}\n")
        for nd in dati["nodi_dettaglio"]:
            if nd["dir"] == "SEME":
                print(f"  SEME {nd['testo']}")
            else:
                barra = "█" * max(1, int(nd["score"] / 1.1))
                print(f"  L{nd['lv']:02d} {nd['dir']:<10} {barra:<9} {nd['score']:.1f}")
                print(f"       [{nd['polo']}]")
                print(f"       {nd['testo']}")
        print()

    m = r["meta"]
    print(f"{sep}")
    print("META-SISTEMA")
    print(f"  Score globale: {m['score_globale_min']} → {m['score_globale_max']}"
          f" (medio: {m['score_medio_globale']})")
    print(f"  Nodi esplorati: {m['nodi_totali_esplorati']}")
    print(f"  Salti qualitativi: {m['salti_totali']}")
    print(f"  Direzione dominante: {m['direzione_dominante']}")
    print(f"  Tempo: {r['tempo']}s")

    if m["salti"]:
        print("\n  SALTI:")
        for s in m["salti"][:8]:
            print(f"    C{s['ciclo']} L{s['livello']:02d} {s['tipo']} Δ{s['delta']:+.2f}"
                  f" [{s['direzione']}] {s['polo']}")
            print(f"    {s['contenuto'][:80]}")
    print(f"{sep}\n")
