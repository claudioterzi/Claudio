"""Miglioramenti v1.1: P6, escape, conteggi. Zero rete Telegram."""

from __future__ import annotations


def test_escape_md():
    from bot.md import clip, escape_md

    assert "_" in escape_md("a_b")
    assert escape_md("a_b") == "a\\_b"
    assert escape_md("*x*") == "\\*x\\*"
    assert clip("abcd", 3) == "ab…"
    assert clip("ab", 3) == "ab"


def test_p6_on_possibility(tmp_path, monkeypatch):
    monkeypatch.setenv("DATABASE_PATH", str(tmp_path / "p6.db"))
    import importlib
    import bot.config as config
    import bot.db as db

    importlib.reload(config)
    importlib.reload(db)
    db.init_db()
    db.upsert_user(9, "n", "N")
    pid = db.add_possibility(9, "il già è già")
    assert db.set_possibility_how_falls(9, pid, "cade se un terzo misura il contrario")
    rows = db.list_possibilities(9)
    assert rows[0]["how_falls"] == "cade se un terzo misura il contrario"


def test_user_counts_and_veil(tmp_path, monkeypatch):
    monkeypatch.setenv("DATABASE_PATH", str(tmp_path / "c.db"))
    import importlib
    import bot.config as config
    import bot.db as db

    importlib.reload(config)
    importlib.reload(db)
    db.init_db()
    db.upsert_user(1, "a", "A")
    db.add_possibility(1, "aperta")
    db.add_action(1, "ho scritto un test")
    db.add_veil(1, 2, "letto")
    c = db.user_counts(1)
    assert c["possibilities"] == 1
    assert c["actions"] == 1
    assert c["sanctuary_completed"] == 0


def test_help_elenco_completo():
    from bot import texts
    from bot.states import PossibilityState

    assert "/registro" in texts.HELP
    assert "/ping" in texts.HELP
    assert "/stato" in texts.HELP
    assert "P6" in texts.P6_PROMPT
    assert PossibilityState.WAITING_P6


def test_handlers_include_stato():
    from bot.handlers import build_command_handlers, build_conversation_handlers

    cmds = build_command_handlers()
    flat = set()
    for h in cmds:
        flat.update(getattr(h, "commands", set()) or set())
    assert "stato" in flat
    assert "registro" in flat
    conv = build_conversation_handlers()
    assert len(conv) == 5
