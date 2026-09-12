"""Verifiche di strato tecnico sul bot pubblicato."""

from __future__ import annotations


def test_states_match_handlers():
    from bot.states import (
        ActionState,
        EtichettaState,
        PossibilityState,
        SanctuaryState,
        VeloState,
    )

    assert SanctuaryState.WAITING_ENTER
    assert SanctuaryState.SILENCE
    assert SanctuaryState.LIGHT
    assert SanctuaryState.ALTAR
    assert SanctuaryState.CANDLE
    assert PossibilityState.WAITING_TEXT
    assert ActionState.WAITING_DESCRIPTION
    assert VeloState.WAITING_CHOICE
    assert EtichettaState.WAITING_TEXT


def test_tesi_resta_ipotesi():
    from bot import texts

    assert "IPOTESI" in texts.TESI_GRANDE
    assert "P6" in texts.TESI_GRANDE
    assert "non lo so" in texts.TESI_GRANDE.lower() or "Non lo so" in texts.TESI_GRANDE
    assert "P5" in texts.P5_P6
    assert "auto-conferma" in texts.P5_P6.lower() or "auto-conferma" in texts.P5_P6


def test_db_layer_labels(tmp_path, monkeypatch):
    db_file = tmp_path / "t.db"
    monkeypatch.setenv("DATABASE_PATH", str(db_file))
    import importlib
    import bot.config as config

    importlib.reload(config)
    import bot.db as db

    importlib.reload(db)
    db.init_db()
    db.upsert_user(7, "n", "N")
    pid = db.add_possibility(7, "una possibilità aperta")
    rows = db.list_possibilities(7)
    assert pid >= 1
    assert rows[0]["layer"] == "IPOTESI"
    assert rows[0]["status"] == "APERTA"
    aid = db.add_action(7, "ho inviato un messaggio")
    actions = db.list_actions(7)
    assert aid >= 1
    assert actions[0]["layer"] == "TECNICO"


def test_handlers_export():
    from bot.handlers import build_command_handlers, build_conversation_handlers, cmd_unknown

    cmds = build_command_handlers()
    conv = build_conversation_handlers()
    assert len(cmds) >= 8
    assert len(conv) == 5
    assert cmd_unknown is not None
