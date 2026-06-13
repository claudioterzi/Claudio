"""La Stesa — oggetto digitale trasmissibile e analizzabile.

Una stesa è una configurazione ordinata di nodi (carta × stato × posizione).
È serializzabile: può essere fotografata, trasmessa, salvata, analizzata.
Non è un oracolo — è una grammatica applicata (Layer 1 + Layer 2).

La DoppiaErmeneutica (Layer 3) legge la stesa e genera le due letture.
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone

from .codice_simbolico import Carta
from .r3_infinito import (
    StatoQuantico,
    OrientamentoCarta,
    TipoPosizione,
    Posizione,
    applica_assiomi,
)


@dataclass
class NodoDiStesa:
    """Un singolo nodo: carta + stato quantico + posizione + orientamento.

    Lo stato_effettivo viene calcolato applicando gli assiomi R³∞ al momento
    della costruzione del nodo — non è modificabile dopo.
    """
    carta: Carta
    stato: StatoQuantico
    posizione: Posizione
    orientamento: OrientamentoCarta = OrientamentoCarta.DIRITTA
    stato_effettivo: StatoQuantico = field(init=False)
    assiomi_attivati: list[int] = field(init=False, default_factory=list)

    def __post_init__(self) -> None:
        stato_eff, assiomi = applica_assiomi(self.carta, self.stato, self.posizione)
        self.stato_effettivo = stato_eff
        self.assiomi_attivati = assiomi

    def serializza(self) -> dict:
        return {
            "posizione_numero": self.posizione.numero,
            "posizione_tipo":   self.posizione.tipo.value,
            "carta":            self.carta.nome,
            "arcano":           self.carta.arcano.value,
            "seme":             self.carta.seme.value if self.carta.seme else None,
            "stato":            self.stato.value,
            "stato_effettivo":  self.stato_effettivo.value,
            "orientamento":     self.orientamento.value,
            "parole_chiave":    list(self.carta.parole_chiave),
            "elemento":         self.carta.elemento,
            "dominio":          self.carta.dominio,
            "assiomi_attivati": self.assiomi_attivati,
        }


@dataclass
class Stesa:
    """La Stesa: configurazione completa di carte.

    È un oggetto digitale. Una stesa fisica può essere fotografata e
    tradotta in questo oggetto (mappa oggettiva della configurazione).
    Lo stesso oggetto Stesa, letto due volte, produce sempre la stessa
    LetturaStrutturale — è la LetturaPersonale che cambia con l'osservatore.
    """
    nodi: list[NodoDiStesa] = field(default_factory=list)
    stesa_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    schema: str = "libero"  # libero / tre_carte / celtic_cross / cinque_elementi

    def aggiungi(
        self,
        carta: Carta,
        stato: StatoQuantico,
        tipo_posizione: TipoPosizione,
        numero_posizione: int,
        orientamento: OrientamentoCarta = OrientamentoCarta.DIRITTA,
        peso: float = 1.0,
    ) -> "Stesa":
        posizione = Posizione(tipo_posizione, numero_posizione, peso)
        nodo = NodoDiStesa(carta, stato, posizione, orientamento)
        self.nodi.append(nodo)
        return self

    def serializza(self) -> dict:
        return {
            "stesa_id":  self.stesa_id,
            "timestamp": self.timestamp,
            "schema":    self.schema,
            "nodi":      [n.serializza() for n in self.nodi],
        }

    # ── Filtri per stato ─────────────────────────────────────────────────────

    def carte_per_stato(self, stato: StatoQuantico) -> list[NodoDiStesa]:
        return [n for n in self.nodi if n.stato_effettivo == stato]

    def carte_collassate(self) -> list[NodoDiStesa]:
        return self.carte_per_stato(StatoQuantico.COLLASSATO)

    def carte_sovrapposte(self) -> list[NodoDiStesa]:
        return self.carte_per_stato(StatoQuantico.SOVRAPPOSTO)

    def carte_entangled(self) -> list[NodoDiStesa]:
        return self.carte_per_stato(StatoQuantico.ENTANGLED)

    def carte_rovesciate(self) -> list[NodoDiStesa]:
        return [n for n in self.nodi if n.orientamento == OrientamentoCarta.ROVESCIA]

    # ── Analisi strutturale (Assioma 7) ─────────────────────────────────────

    def rileva_tensioni(self) -> list[str]:
        """Rileva tensioni strutturali nella configurazione (Assioma 4 + 7)."""
        tensioni = []

        for n in self.carte_rovesciate():
            tensioni.append(
                f"Tensione in {n.posizione.tipo.value}: "
                f"{n.carta.nome} rovescia — significato differito o interiore"
            )

        _OPPOSTI = {
            "fuoco": "acqua", "acqua": "fuoco",
            "aria":  "terra", "terra": "aria",
        }
        per_posizione: dict[TipoPosizione, list[NodoDiStesa]] = {}
        for n in self.nodi:
            per_posizione.setdefault(n.posizione.tipo, []).append(n)

        presenti = per_posizione.get(TipoPosizione.PRESENTE, [])
        futuri   = per_posizione.get(TipoPosizione.FUTURO, [])
        for p in presenti:
            for f in futuri:
                if p.carta.elemento and _OPPOSTI.get(p.carta.elemento) == f.carta.elemento:
                    tensioni.append(
                        f"Tensione elementale: {p.carta.elemento} (Presente) ↔ "
                        f"{f.carta.elemento} (Futuro) — transizione non lineare"
                    )

        return tensioni

    def rileva_risorse(self) -> list[str]:
        """Identifica risorse e punti di forza strutturali."""
        risorse = []
        for n in self.nodi:
            if n.posizione.tipo == TipoPosizione.POTENZIALE:
                kw = ", ".join(n.carta.parole_chiave[:2])
                risorse.append(f"Risorsa latente ({n.carta.nome}): {kw}")
            elif n.posizione.tipo == TipoPosizione.CONSIGLIO:
                risorse.append(f"Indicazione strutturale ({n.carta.nome}): {n.carta.dominio}")
        return risorse

    def distribuzione_stati(self) -> dict[str, int]:
        conteggio: dict[str, int] = {}
        for n in self.nodi:
            k = n.stato_effettivo.value
            conteggio[k] = conteggio.get(k, 0) + 1
        return conteggio

    def distribuzione_elementi(self) -> dict[str, int]:
        conteggio: dict[str, int] = {}
        for n in self.nodi:
            if n.carta.elemento:
                conteggio[n.carta.elemento] = conteggio.get(n.carta.elemento, 0) + 1
        return conteggio

    def assiomi_attivati(self) -> list[int]:
        """Restituisce la lista de-duplicata degli assiomi attivati in questa stesa."""
        attivati = {7}  # Assioma 7 è sempre attivo
        for n in self.nodi:
            attivati.update(n.assiomi_attivati)
            if n.stato_effettivo == StatoQuantico.ENTANGLED:
                attivati.add(3)
            if n.orientamento == OrientamentoCarta.ROVESCIA:
                attivati.add(4)
        return sorted(attivati)
