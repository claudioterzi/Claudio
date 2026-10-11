"""Alpha 74 full-space adapter: independent axis + polarity for automatic draws."""
import secrets
from api import tarot_alpha as base

_original_normalize = base._normalize_items
_AXES = ("nord", "est", "sud", "ovest")


def _full_space_normalize(body):
    items = body.get("carte_scelte") if isinstance(body, dict) else None
    if isinstance(items, list) and items:
        return _original_normalize(body)

    raw_count = body.get("numero_carte", 3) if isinstance(body, dict) else 3
    if raw_count is None or raw_count == "":
        raw_count = 3
    try:
        count = int(raw_count)
    except (TypeError, ValueError) as exc:
        raise ValueError("numero_carte deve essere un intero da 1 a 7.") from exc
    if not 1 <= count <= 7:
        raise ValueError("numero_carte deve essere compreso tra 1 e 7.")

    chosen = secrets.SystemRandom().sample(base._deck(), count)
    generated = []
    for i, card in enumerate(chosen):
        pos, label, _default_axis = base.POSITIONS[i]
        generated.append({
            "carta": card["nome"],
            "posizione": pos,
            "posizione_label": label,
            "asse": secrets.choice(_AXES),
            "polarita": base._polarity(),
        })
    patched = dict(body or {})
    patched["carte_scelte"] = generated
    cards, _manual_flag = _original_normalize(patched)
    return cards, True


base._normalize_items = _full_space_normalize
app = base.app
