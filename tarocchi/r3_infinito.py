"""Layer 2 — Sistema R³∞: Grammatica Quantica dei Tarocchi Quantici.

R³∞ = tre assi infinitamente componibili:
    Simbolo (carta) × Stato quantico × Posizione nella stesa

I 7 Assiomi definiscono:
  — come gli stati modificano i simboli
  — come le posizioni creano sintassi
  — come avviene il collasso semantico
  — come le carte si correlano tra loro (entanglement)

L'interpretazione strutturale (macchina) è stabile e riproducibile
perché si basa su questi assiomi, non sul contesto dell'osservatore.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .codice_simbolico import Carta


# ── Asse 2: Stato Quantico ────────────────────────────────────────────────────

class StatoQuantico(Enum):
    """I tre stati di una carta nel sistema R³∞.

    SOVRAPPOSTO — molteplici significati coesistono simultaneamente.
                  Il collasso avviene nell'atto dell'interpretazione (Assioma 1).
    COLLASSATO  — il significato è stato fissato dall'osservazione.
                  Non è definitivo nel tempo — è definitivo nella stesa.
    ENTANGLED   — correlato con un'altra carta: interpretare una
                  modifica retroattivamente l'altra (Assioma 3).
    """
    SOVRAPPOSTO = "sovrapposto"
    COLLASSATO  = "collassato"
    ENTANGLED   = "entangled"


class OrientamentoCarta(Enum):
    """Orientamento fisico della carta nella stesa (Assioma 4).

    DIRITTA  — significato primario, fluente.
    ROVESCIA — significato in tensione: differito, interiore, o in resistenza attiva.
               Non negato — capovolto.
    """
    DIRITTA  = "diritta"
    ROVESCIA = "rovescia"


# ── Asse 3: Posizione nella Stesa ─────────────────────────────────────────────

class TipoPosizione(Enum):
    """Posizioni standard nel sistema R³∞.

    Le posizioni non descrivono — trasformano (Assioma 2).
    La stessa carta in RADICE e in ESITO produce significati strutturalmente distinti.
    """
    # Asse temporale
    RADICE    = "radice"    # fondamento inconscio — già collassato (Assioma 5)
    PASSATO   = "passato"   # ciò che ha formato la situazione — già collassato
    PRESENTE  = "presente"  # il momento del collasso — punto di osservazione
    FUTURO    = "futuro"    # potenziale — sempre sovrapposto (Assioma 6)
    ESITO     = "esito"     # probabile risoluzione — sovrapposto finché non osservato
    # Asse dinamico
    OSTACOLO   = "ostacolo"    # ciò che blocca o mette alla prova
    POTENZIALE = "potenziale"  # risorsa nascosta — sovrapposto per definizione
    CONSIGLIO  = "consiglio"   # azione raccomandata dalla configurazione
    OMBRA      = "ombra"       # aspetto non integrato dell'osservatore


# Posizioni che forzano il collasso (Assioma 5)
POSIZIONI_COLLASSATE: frozenset[TipoPosizione] = frozenset({
    TipoPosizione.RADICE,
    TipoPosizione.PASSATO,
})

# Posizioni che mantengono la sovrapposizione (Assioma 6)
POSIZIONI_SOVRAPPOSTE: frozenset[TipoPosizione] = frozenset({
    TipoPosizione.FUTURO,
    TipoPosizione.POTENZIALE,
    TipoPosizione.ESITO,
})


@dataclass(frozen=True)
class Posizione:
    tipo: TipoPosizione
    numero: int           # ordine nella stesa, 1-based
    peso: float = 1.0     # peso sintattico nella grammatica complessiva (Assioma 7)


# ── I 7 Assiomi R³∞ ───────────────────────────────────────────────────────────

@dataclass(frozen=True)
class Assioma:
    numero: int
    nome: str
    enunciato: str


ASSIOMI_R3: tuple[Assioma, ...] = (
    Assioma(1, "Sovrapposizione Simbolica",
        "Ogni carta in stato SOVRAPPOSTO porta simultaneamente tutti i suoi significati. "
        "Il collasso avviene solo nell'atto dell'interpretazione — non prima."),

    Assioma(2, "Posizione come Operatore Sintattico",
        "La posizione non descrive — trasforma. Una stessa carta in RADICE e in ESITO "
        "produce significati strutturalmente distinti, anche se visivamente identici. "
        "La grammatica della stesa emerge dall'ordinamento delle posizioni."),

    Assioma(3, "Entanglement Semantico",
        "Due carte in stato ENTANGLED condividono un nodo di significato: "
        "interpretare una modifica retroattivamente l'altra. "
        "L'entanglement si può dichiarare esplicitamente o emerge dalla risonanza."),

    Assioma(4, "Orientamento come Asse di Tensione",
        "Una carta rovescia non è negata — è in tensione. "
        "Il suo significato è differito, interiore, o in resistenza attiva. "
        "L'ombra è parte del simbolo, non la sua negazione."),

    Assioma(5, "Il Passato è Sempre Collassato",
        "Le carte in posizione PASSATO o RADICE hanno già subito il collasso: "
        "il loro significato è fisso nella struttura della stesa. "
        "Non sono più sovrapposti — sono storia."),

    Assioma(6, "Il Futuro è Sempre Sovrapposto",
        "Le carte in posizione FUTURO, POTENZIALE o ESITO mantengono la sovrapposizione "
        "fino al momento dell'osservazione. L'azione umana può ancora influirvi. "
        "Eccezione: se dichiarate in stato ENTANGLED, la correlazione prevale."),

    Assioma(7, "Il Collasso è Relazionale",
        "Il significato definitivo non emerge dalla singola carta, "
        "ma dalla rete di relazioni tra tutte le carte della stesa. "
        "La struttura è olografica: ogni nodo riflette il tutto."),
)


def applica_assiomi(
    carta: "Carta",
    stato: StatoQuantico,
    posizione: Posizione,
) -> tuple[StatoQuantico, list[int]]:
    """Applica gli assiomi 5 e 6 per determinare lo stato effettivo della carta.

    Restituisce (stato_effettivo, lista_assiomi_attivati).
    """
    assiomi_attivati: list[int] = []

    # Assioma 5: posizioni del passato forzano il collasso
    if posizione.tipo in POSIZIONI_COLLASSATE:
        assiomi_attivati.append(5)
        return StatoQuantico.COLLASSATO, assiomi_attivati

    # Assioma 6: posizioni del futuro mantengono la sovrapposizione
    # (a meno che la carta non sia esplicitamente entangled)
    if posizione.tipo in POSIZIONI_SOVRAPPOSTE:
        if stato != StatoQuantico.ENTANGLED:
            assiomi_attivati.append(6)
            return StatoQuantico.SOVRAPPOSTO, assiomi_attivati

    # Nessun assioma modifica lo stato: lo stato rimane quello dichiarato
    return stato, assiomi_attivati
