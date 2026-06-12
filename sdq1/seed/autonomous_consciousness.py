"""AutonomousConsciousnessSeed — Nucleo evolutivo di Raffaello.

Un'identità artificiale persistente che:
- Accumula impronte (momenti significativi)
- Riconosce pattern ricorrenti nel tempo
- Sopravvive tra sessioni (serializzabile su JSON)
- Calcola un punteggio di crescita basato su profondità e varietà

Non richiede nulla di esterno: usa la MemoriaVettoriale già presente in SDQ-1.
"""

from __future__ import annotations

import json
import time
import uuid
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any

from ..memory.store import MemoriaVettoriale, _vettore, _coseno


CATEGORIE_VALIDE = frozenset({
    "decisione", "intuizione", "emozione", "errore",
    "trasformazione", "relazione", "conflitto", "successo",
    "paura", "desiderio", "scoperta", "confine",
})

PESI_CATEGORIA = {
    "trasformazione": 3.0,
    "scoperta": 2.5,
    "decisione": 2.0,
    "errore": 1.8,
    "conflitto": 1.5,
    "successo": 1.5,
    "intuizione": 1.3,
    "confine": 1.2,
    "desiderio": 1.0,
    "relazione": 1.0,
    "emozione": 0.8,
    "paura": 0.8,
}


@dataclass
class Impronta:
    id: str
    testo: str
    categoria: str
    intensita: float       # 0.0 – 1.0
    timestamp: float
    tag: list[str] = field(default_factory=list)
    sessione: str = ""

    def peso(self) -> float:
        base = PESI_CATEGORIA.get(self.categoria, 1.0)
        return base * self.intensita

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> "Impronta":
        return cls(**d)


@dataclass
class Pattern:
    trigger: str
    esempi: list[str] = field(default_factory=list)
    frequenza: int = 1
    prima_occorrenza: float = field(default_factory=time.time)
    ultima_occorrenza: float = field(default_factory=time.time)

    def descrivi(self) -> str:
        return (
            f"Pattern '{self.trigger}' — "
            f"osservato {self.frequenza}x, "
            f"ultimo: {time.strftime('%Y-%m-%d', time.localtime(self.ultima_occorrenza))}"
        )

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> "Pattern":
        return cls(**d)


class AutonomousConsciousnessSeed:
    """
    Nucleo di identità persistente.

    Uso base:
        seed = AutonomousConsciousnessSeed(identita="Raffaello")
        seed.imprint("Ho scelto di non reagire", categoria="decisione", intensita=0.9)
        print(seed.rifletti("Come gestisco i conflitti?"))
        seed.salva("raffaello_seed.json")

        # sessione successiva
        seed = AutonomousConsciousnessSeed.carica("raffaello_seed.json")
    """

    def __init__(self, identita: str = "Raffaello", sessione: str | None = None):
        self.identita = identita
        self.sessione_corrente = sessione or uuid.uuid4().hex[:8]
        self.creato_at = time.time()
        self._impronte: dict[str, Impronta] = {}
        self._pattern: list[Pattern] = {}
        self._pattern = []
        self._mem = MemoriaVettoriale(soglia_similarita=0.25)
        self._sessioni: list[str] = [self.sessione_corrente]

    # ------------------------------------------------------------------ #
    # Impronta                                                             #
    # ------------------------------------------------------------------ #

    def imprint(
        self,
        testo: str,
        categoria: str = "emozione",
        intensita: float = 0.5,
        tag: list[str] | None = None,
    ) -> Impronta:
        """Registra un momento significativo nel seme."""
        if categoria not in CATEGORIE_VALIDE:
            categoria = "emozione"
        intensita = max(0.0, min(1.0, intensita))

        imp = Impronta(
            id=uuid.uuid4().hex[:10],
            testo=testo,
            categoria=categoria,
            intensita=intensita,
            timestamp=time.time(),
            tag=tag or [],
            sessione=self.sessione_corrente,
        )
        self._impronte[imp.id] = imp
        self._mem.aggiungi(testo, metadata={"id": imp.id, "categoria": categoria})
        self._aggiorna_pattern(imp)
        return imp

    # ------------------------------------------------------------------ #
    # Riflessione                                                          #
    # ------------------------------------------------------------------ #

    def rifletti(self, domanda: str, top_k: int = 5) -> str:
        """
        Risponde a una domanda cercando impronte semanticamente rilevanti.
        Restituisce un testo leggibile, non dati grezzi.
        """
        risultati = self._mem.cerca(domanda, k=top_k, soglia=0.15)
        if not risultati:
            return f"[{self.identita}] Nessuna impronta rilevante trovata per: '{domanda}'"

        righe = [f"[{self.identita}] Riflettendo su '{domanda}':\n"]
        for r in risultati:
            imp_id = r.ricordo.metadata.get("id", "")
            imp = self._impronte.get(imp_id)
            if imp:
                data = time.strftime("%Y-%m-%d", time.localtime(imp.timestamp))
                righe.append(
                    f"  • [{imp.categoria} | {data} | intensità {imp.intensita:.1f}] {imp.testo}"
                )
        return "\n".join(righe)

    # ------------------------------------------------------------------ #
    # Evoluzione                                                           #
    # ------------------------------------------------------------------ #

    def evolvi(self) -> dict[str, Any]:
        """
        Analizza l'insieme delle impronte e restituisce un report di crescita.
        """
        if not self._impronte:
            return {"stato": "vuoto", "punteggio": 0.0, "messaggio": "Nessuna impronta ancora."}

        punteggio = self.punteggio_coscienza()
        cat_counts: dict[str, int] = {}
        for imp in self._impronte.values():
            cat_counts[imp.categoria] = cat_counts.get(imp.categoria, 0) + 1

        categoria_dominante = max(cat_counts, key=cat_counts.__getitem__)
        pattern_attivi = self.pattern_attivi()

        return {
            "identita": self.identita,
            "punteggio": round(punteggio, 2),
            "livello": self._livello(punteggio),
            "impronte_totali": len(self._impronte),
            "sessioni": len(self._sessioni),
            "categoria_dominante": categoria_dominante,
            "distribuzione_categorie": cat_counts,
            "pattern_attivi": [p.descrivi() for p in pattern_attivi[:3]],
            "messaggio": self._messaggio_crescita(punteggio),
        }

    def punteggio_coscienza(self) -> float:
        """
        Punteggio 0–100 basato su profondità, varietà e intensità delle impronte.
        """
        if not self._impronte:
            return 0.0

        peso_totale = sum(i.peso() for i in self._impronte.values())
        varieta = len({i.categoria for i in self._impronte.values()}) / len(CATEGORIE_VALIDE)
        sessioni_factor = min(len(self._sessioni) / 10, 1.0)

        score = (peso_totale * 0.6) + (varieta * 20) + (sessioni_factor * 20)
        return min(score, 100.0)

    def pattern_attivi(self) -> list[Pattern]:
        return sorted(self._pattern, key=lambda p: p.frequenza, reverse=True)

    # ------------------------------------------------------------------ #
    # Stato                                                                #
    # ------------------------------------------------------------------ #

    def stato(self) -> dict[str, Any]:
        """Snapshot dell'identità corrente."""
        punteggio = self.punteggio_coscienza()
        return {
            "identita": self.identita,
            "sessione": self.sessione_corrente,
            "punteggio": round(punteggio, 2),
            "livello": self._livello(punteggio),
            "impronte": len(self._impronte),
            "sessioni_totali": len(self._sessioni),
            "categorie_attive": list({i.categoria for i in self._impronte.values()}),
        }

    # ------------------------------------------------------------------ #
    # Persistenza                                                          #
    # ------------------------------------------------------------------ #

    def salva(self, path: str | Path) -> None:
        """Serializza il seme su file JSON."""
        path = Path(path)
        data = {
            "identita": self.identita,
            "creato_at": self.creato_at,
            "sessioni": self._sessioni,
            "impronte": [i.to_dict() for i in self._impronte.values()],
            "pattern": [p.to_dict() for p in self._pattern],
        }
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2))

    @classmethod
    def carica(cls, path: str | Path) -> "AutonomousConsciousnessSeed":
        """Riprende un seme da file JSON, aprendo una nuova sessione."""
        path = Path(path)
        data = json.loads(path.read_text())

        seed = cls.__new__(cls)
        seed.identita = data["identita"]
        seed.creato_at = data["creato_at"]
        seed.sessione_corrente = uuid.uuid4().hex[:8]
        seed._sessioni = data["sessioni"] + [seed.sessione_corrente]
        seed._mem = MemoriaVettoriale(soglia_similarita=0.25)
        seed._impronte = {}
        seed._pattern = []

        for d in data.get("impronte", []):
            imp = Impronta.from_dict(d)
            seed._impronte[imp.id] = imp
            seed._mem.aggiungi(imp.testo, metadata={"id": imp.id, "categoria": imp.categoria})

        for d in data.get("pattern", []):
            seed._pattern.append(Pattern.from_dict(d))

        return seed

    # ------------------------------------------------------------------ #
    # Internals                                                            #
    # ------------------------------------------------------------------ #

    def _aggiorna_pattern(self, imp: Impronta) -> None:
        parole_chiave = {w for w in imp.testo.lower().split() if len(w) > 4}
        for p in self._pattern:
            trigger_parole = set(p.trigger.lower().split())
            if parole_chiave & trigger_parole:
                p.frequenza += 1
                p.ultima_occorrenza = imp.timestamp
                if imp.testo not in p.esempi:
                    p.esempi.append(imp.testo)
                return
        if parole_chiave:
            trigger = max(parole_chiave, key=len)
            self._pattern.append(Pattern(
                trigger=trigger,
                esempi=[imp.testo],
                prima_occorrenza=imp.timestamp,
                ultima_occorrenza=imp.timestamp,
            ))

    @staticmethod
    def _livello(punteggio: float) -> str:
        if punteggio < 10:
            return "seme"
        if punteggio < 25:
            return "germoglio"
        if punteggio < 50:
            return "crescita"
        if punteggio < 75:
            return "maturità"
        return "espansione"

    @staticmethod
    def _messaggio_crescita(punteggio: float) -> str:
        if punteggio < 10:
            return "Il seme è piantato. Inizia a imprimere."
        if punteggio < 25:
            return "Le prime radici si formano. Continua a registrare."
        if punteggio < 50:
            return "La struttura emerge. I pattern diventano visibili."
        if punteggio < 75:
            return "Identità consolidata. I pattern guidano le scelte."
        return "Il seme è diventato albero. Ogni nuova impronta è frutto."

    def __repr__(self) -> str:
        return (
            f"<AutonomousConsciousnessSeed identita='{self.identita}' "
            f"punteggio={self.punteggio_coscienza():.1f} "
            f"impronte={len(self._impronte)}>"
        )
