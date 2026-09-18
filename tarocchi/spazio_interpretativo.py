"""Spazio combinatorio e registri epistemici del Canone Alpha 74.

Le configurazioni contano carte distinte, ordine della stesa, direzione/asse
e polarità. Il conteggio descrive lo spazio del modello, non il numero di
verità disponibili.
"""
from __future__ import annotations

from math import prod


DECK_SIZE = 74
POLARITIES_PER_CARD = 2
DIRECTIONS_PER_CARD = 4
STATES_PER_CARD = POLARITIES_PER_CARD * DIRECTIONS_PER_CARD
MAX_CARDS = 7


def _ordered_distinct_cards(card_count: int) -> int:
    """Return P(74, card_count): distinct cards with order preserved."""
    return prod(range(DECK_SIZE - card_count + 1, DECK_SIZE + 1))


MAX_ORDERED_7 = _ordered_distinct_cards(MAX_CARDS) * STATES_PER_CARD ** MAX_CARDS
TOTAL_CONFIGURATIONS_1_TO_7 = sum(
    _ordered_distinct_cards(card_count) * STATES_PER_CARD ** card_count
    for card_count in range(1, MAX_CARDS + 1)
)


def configuration_space(card_count: int) -> dict:
    """Describe the exact Alpha configuration space for a 1–7 card spread."""
    if isinstance(card_count, bool) or not isinstance(card_count, int):
        raise ValueError("Il numero di carte deve essere un intero da 1 a 7.")
    if not 1 <= card_count <= MAX_CARDS:
        raise ValueError("Il numero di carte deve essere compreso tra 1 e 7.")

    ordered_cards = _ordered_distinct_cards(card_count)
    same_length = ordered_cards * STATES_PER_CARD ** card_count
    return {
        "modello": "Canone Alpha 74",
        "carte_disponibili": DECK_SIZE,
        "carte_nella_stesa": card_count,
        "carte_distinte": True,
        "ordine_rilevante": True,
        "direzioni_per_carta": DIRECTIONS_PER_CARD,
        "polarita_per_carta": POLARITIES_PER_CARD,
        "stati_elementari_per_carta": STATES_PER_CARD,
        "permutazioni_carte_distinte": str(ordered_cards),
        "configurazioni_stessa_lunghezza": str(same_length),
        "configurazioni_massime_7": str(MAX_ORDERED_7),
        "configurazioni_da_1_a_7": str(TOTAL_CONFIGURATIONS_1_TO_7),
        "formula": f"P({DECK_SIZE},{card_count}) × {STATES_PER_CARD}^{card_count}",
        "formula_massima_7": f"P({DECK_SIZE},7) × {STATES_PER_CARD}^7",
        "definizione": "Spazio combinatorio di configurazioni interpretative; non insieme di verità assolute.",
    }
