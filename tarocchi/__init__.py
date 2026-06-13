"""Tarocchi Quantici — Sistema R³∞ con Principio della Doppia Ermeneutica.

Tre layer sovrapposti che formano un linguaggio, non un oracolo:

  Layer 1 — Codice Simbolico
      Il vocabolario: 74 carte con nome, elemento, dominio, parole chiave.
      Condiviso dall'osservatore-macchina e dall'osservatore-umano.

  Layer 2 — Grammatica Quantica (R³∞)
      Le regole di composizione: stati quantici × posizioni × 7 assiomi.
      Come gli stati modificano le carte. Come le posizioni creano sintassi.
      Come il collasso avviene.

  Layer 3 — Doppia Ermeneutica
      Chi sono gli osservatori e come le loro diverse nature
      generano diversi tipi di significato dallo stesso testo.

      — LetturaStrutturale: osservatore-macchina, stabile, riproducibile.
      — LetturaPersonale:   osservatore-umano, unica, contestuale.
      — La verità emerge dalla relazione tra osservatore e simbolo.

Uso rapido:

    from tarocchi import (
        cerca_carta, Stesa, StatoQuantico, TipoPosizione,
        ContestoPersonale, DoppiaErmeneutica,
    )

    matto = cerca_carta("Il Matto")
    torre = cerca_carta("La Torre")

    stesa = (
        Stesa(schema="tre_carte")
        .aggiungi(matto, StatoQuantico.COLLASSATO,  TipoPosizione.PASSATO,   1)
        .aggiungi(torre, StatoQuantico.SOVRAPPOSTO, TipoPosizione.PRESENTE,  2)
        .aggiungi(cerca_carta("Le Stelle"), StatoQuantico.SOVRAPPOSTO, TipoPosizione.FUTURO, 3)
    )

    proto = DoppiaErmeneutica()
    strutturale = proto.leggi_struttura(stesa)
    personale = proto.leggi_personale(
        strutturale,
        ContestoPersonale(
            domanda="Cosa sta cambiando nella mia vita?",
            aspetto_focus="crescita",
            disponibilita_collasso=True,
        ),
    )
"""

from .codice_simbolico import (
    Carta,
    TipoArcano,
    Seme,
    MAZZO,
    ARCANI_MAGGIORI,
    cerca_carta,
    carta_per_indice,
)
from .r3_infinito import (
    StatoQuantico,
    OrientamentoCarta,
    TipoPosizione,
    Posizione,
    Assioma,
    ASSIOMI_R3,
    applica_assiomi,
)
from .stesa import NodoDiStesa, Stesa
from .ermeneutica import (
    LetturaStrutturale,
    ContestoPersonale,
    LetturaPersonale,
    DoppiaErmeneutica,
)

__all__ = [
    # Layer 1
    "Carta", "TipoArcano", "Seme",
    "MAZZO", "ARCANI_MAGGIORI",
    "cerca_carta", "carta_per_indice",
    # Layer 2
    "StatoQuantico", "OrientamentoCarta",
    "TipoPosizione", "Posizione",
    "Assioma", "ASSIOMI_R3", "applica_assiomi",
    # Stesa
    "NodoDiStesa", "Stesa",
    # Layer 3
    "LetturaStrutturale", "ContestoPersonale",
    "LetturaPersonale", "DoppiaErmeneutica",
]
