"""Harness di flusso: zero rete Telegram."""

from __future__ import annotations

from bot.epistemic import END, STAY, classify, sanctuary_advance, sanctuary_path
from bot.states import SanctuaryState


def test_classify_layers():
    assert classify("Ho visto il file sul disco.").layer == "RECUPERATO"
    assert classify("Quindi il sistema è vivo.").layer == "INFERITO"
    assert classify("Forse il già è già in atto.").layer == "IPOTESI"
    assert classify("Desidero che resti aperta.").layer == "DESIDERIO"
    assert classify("Simulo un nodo online.").layer == "SIMULAZIONE"
    assert classify("Oggi piove a Bruxelles.").layer == "UNKNOWN"


def test_ipotesi_porta_p6():
    lab = classify("Immagino che costruire davvero basti.")
    assert lab.layer == "IPOTESI"
    assert lab.how_falls


def test_santuario_path_completa():
    path = sanctuary_path()
    script = ["entro", "luce", "altare", "accendo", "esco"]
    state = path[0]
    for i, word in enumerate(script):
        nxt, ok = sanctuary_advance(state, word)
        assert ok, word
        if i == len(script) - 1:
            assert nxt == END
        else:
            state = nxt
            assert state == path[i + 1]


def test_santuario_rifiuta_chiusura_anticipata():
    nxt, ok = sanctuary_advance(SanctuaryState.WAITING_ENTER, "esco")
    assert nxt == STAY and not ok
    nxt, ok = sanctuary_advance(SanctuaryState.SILENCE, "accendo")
    assert not ok


def test_registro_db(tmp_path, monkeypatch):
    monkeypatch.setenv("DATABASE_PATH", str(tmp_path / "e.db"))
    import importlib
    import bot.config as config
    import bot.db as db

    importlib.reload(config)
    importlib.reload(db)
    db.init_db()
    db.upsert_user(3, "x", "X")
    db.add_epistemic(3, "IPOTESI", "una tesi aperta", "tieni_aperto", "non so ancora")
    rows = db.list_epistemic(3)
    assert rows[0]["layer"] == "IPOTESI"
    assert rows[0]["how_falls"] == "non so ancora"
