"""Misure: registra, guarda il trend, dice la verità. Zero rete Telegram."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone


def _punti(valori, giorno0=datetime(2026, 8, 1, tzinfo=timezone.utc), passo=7):
    return [(v, giorno0 + timedelta(days=i * passo)) for i, v in enumerate(valori)]


def test_parse_valori():
    from bot.misure import _parse_valore

    assert _parse_valore("78,5", "peso") == 78.5
    assert _parse_valore("78.5kg", "peso") == 78.5
    assert _parse_valore("92 cm", "vita") == 92.0
    assert _parse_valore("8k", "passi") == 8000.0
    assert _parse_valore("abc", "peso") is None


def test_ancora_peso_bmi():
    from bot.misure import ancora_peso

    lo, target, hi = ancora_peso(178)
    assert round(lo, 1) == 58.6
    assert round(target, 1) == 69.7
    assert round(hi, 1) == 78.9


def test_verdetto_verso_meta_dimagrire():
    from bot.misure import verdetto

    v = verdetto("peso", _punti([80.0, 79.0]), "dimagrire")
    assert v["stato"] == "VERSO_META"
    assert v["kcal_giorno"] < 0  # deficit: bilancio positivo per la meta


def test_verdetto_contro_meta_sgrida():
    from bot.misure import verdetto

    v = verdetto("peso", _punti([79.0, 80.0]), "dimagrire")
    assert v["stato"] == "CONTRO_META"
    assert v["kcal_giorno"] > 0  # surplus


def test_verdetto_statico():
    from bot.misure import verdetto

    v = verdetto("peso", _punti([80.0, 80.05]), "dimagrire")
    assert v["stato"] == "STATICO"


def test_verdetto_muscolo_soglia_bassa_e_deriva_mantenere():
    from bot.misure import verdetto

    v = verdetto("peso", _punti([80.0, 80.8]), "muscolo")  # +0.11 kg/sett
    assert v["stato"] == "VERSO_META"
    v2 = verdetto("peso", _punti([80.0, 81.0]), "mantenere")
    assert v2["stato"] == "DERIVA"


def test_verdetto_poche_misure_e_senza_meta():
    from bot.misure import verdetto

    assert verdetto("peso", _punti([80.0]), "dimagrire")["stato"] == "POCHE_MISURE"
    v = verdetto("vita", _punti([90.0, 92.0]), None)
    assert v["stato"] == "SENZA_META"
    assert v["direzione"] == "su"
    assert "kcal_giorno" not in v  # bilancio solo per il peso


def test_misure_db_roundtrip(tmp_path, monkeypatch):
    monkeypatch.setenv("DATABASE_PATH", str(tmp_path / "m.db"))
    import importlib

    import bot.config as config
    import bot.db as db

    importlib.reload(config)
    importlib.reload(db)
    db.init_db()

    import bot.misure as misure

    importlib.reload(misure)
    mid = misure.salva(3, "peso", 80.0, "kg", None)
    assert mid >= 1
    misure.salva(3, "peso", 79.2, "kg", "dopo corsa")
    misure.salva(3, "vita", 91.0, "cm", None)
    rows = misure.lista(3, "peso")
    assert len(rows) == 2
    assert rows[0]["valore"] == 79.2
    assert rows[0]["nota"] == "dopo corsa"
    assert rows[1]["nota"] is None
    assert misure.tipi_usati(3) == ["vita", "peso"]  # più recente prima
