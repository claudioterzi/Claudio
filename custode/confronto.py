"""OCCHIO — confronto baseline vs check-out.

La differenza tra i due inventari produce l'elenco delle discrepanze,
con foto e timestamp: l'evidenza per la richiesta AirCover/deposito.
"""

from typing import List

from custode.modelli import Inventario, Discrepanza


def confronta(baseline: Inventario, checkout: Inventario,
              solo_problemi: bool = True) -> List[Discrepanza]:
    """Confronta due inventari zona per zona, oggetto per oggetto."""
    discrepanze: List[Discrepanza] = []
    zone = set(baseline.conteggi) | set(checkout.conteggi)
    for zona_id in sorted(zone):
        base = baseline.conteggi.get(zona_id)
        dopo = checkout.conteggi.get(zona_id)
        if dopo is None:
            discrepanze.append(Discrepanza(
                zona_id, "(zona intera)", 1, 0,
                note="zona non fotografata al check-out"))
            continue
        oggetti = set(base.quantita if base else {}) | set(dopo.quantita)
        for oggetto in sorted(oggetti):
            attesi = base.quantita.get(oggetto, 0) if base else 0
            trovati = dopo.quantita.get(oggetto, 0)
            if solo_problemi and attesi == trovati:
                continue
            discrepanze.append(Discrepanza(
                zona_id, oggetto, attesi, trovati, note=dopo.note))
    return discrepanze
