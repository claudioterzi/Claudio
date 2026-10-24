"""Parse generated output without inventing replacements for failed generations."""
import json


def unfence(text: str) -> str:
    text = text.strip()
    if text.startswith("```") and text.endswith("```"):
        text = text.split("\n", 1)[1].rsplit("```", 1)[0].strip()
    return text


def json_object(text: str) -> dict:
    value = json.loads(unfence(text))
    if not isinstance(value, dict) or not value:
        raise ValueError("Il modello deve restituire un oggetto JSON non vuoto")
    return value
