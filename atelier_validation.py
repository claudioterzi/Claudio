"""Catalog-bound composition contracts. Concept: Claudio Terzi."""
import json
import re


class CompositionInvalid(ValueError):
    pass


def validate_proposal(text, materials, counts, scia_count):
    """Reject incomplete/foreign selections; never add or silently drop a material."""
    raw = text.strip()
    if raw.startswith("```"):
        raw = re.sub(r"^```(?:json)?\s*|\s*```$", "", raw, flags=re.I)
    try:
        proposal = json.loads(raw)
    except (ValueError, TypeError):
        raise CompositionInvalid("La risposta deve essere un oggetto JSON completo.") from None
    if not isinstance(proposal, dict):
        raise CompositionInvalid("La risposta deve essere un oggetto JSON.")
    used, groups, errors = set(), {}, []
    for key, count in zip(("testa", "cuore", "fondo", "scia"), (*counts, scia_count)):
        values = proposal.get(key)
        if not isinstance(values, list) or len(values) != count:
            errors.append(f"{key}: servono esattamente {count} numeri")
            continue
        groups[key] = []
        for value in values:
            # Reject booleans and fractions instead of silently turning them into IDs.
            if isinstance(value, str) and re.fullmatch(r"[0-9]+", value):
                value = int(value)
            if type(value) is not int or value not in materials:
                errors.append(f"{key}: numero {value!r} non disponibile nel catalogo selezionato")
                continue
            if value in used:
                errors.append(f"{key}: numero {value} ripetuto; ogni materia deve apparire una volta")
                continue
            material = materials[value]
            if key == "scia" and str(material.get("ruolo_scia") or "-").strip() == "-":
                errors.append(f"scia: numero {value} privo di ruolo di scia")
                continue
            used.add(value)
            groups[key].append({"n": value, "nome": material["nome"],
                                "forza": material["forza"], "liv": material["livello"],
                                "fam": material["famiglia"]})
    if errors:
        raise CompositionInvalid("; ".join(errors[:12]))
    return proposal, {key: groups[key] for key in ("testa", "cuore", "fondo")}, groups["scia"]
