"""Test del ponte SDQ-1 e del terzo P5.

P6: questi test cadono se sdq1.py o terzo.py cambiano contratto
(nomi funzioni, chiavi del dict, mappa ESITI).
"""

from __future__ import annotations

import json
import sqlite3

import pytest

from bot import config, db, sdq1
from bot.terzo import ESITI


def test_health_dichiara_ponte_assente(monkeypatch):
    monkeypatch.setattr(config, "SDQ1_URL", "")
    h = sdq1.health()
    assert h["engine"] == "protocollo-nucleo"
    assert h["agenti"] == 0
    assert h["ponte_sdq1"] == "assente"


def test_ask_locale_senza_ponte(monkeypatch):
    monkeypatch.setattr(config, "SDQ1_URL", "")
    out = sdq1.ask("forse il campo esiste")
    assert out["agenti"] == 0
    assert out["provider"] == ["protocollo-nucleo"]
    assert "non sono qui" in out["risposta"]


def test_ponte_caduto_dichiarato(monkeypatch):
    monkeypatch.setattr(config, "SDQ1_URL", "http://127.0.0.1:1/ask")
    monkeypatch.setattr(config, "SDQ1_TIMEOUT", 1.0)
    out = sdq1.ask("forse il campo esiste")
    assert out["agenti"] == 0
    assert out.get("ponte") == "caduto"
    assert "non risponde" in out["risposta"]


def test_ponte_vivo_inoltra(monkeypatch):
    chiamate = {}

    class _Resp:
        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

        def read(self):
            return json.dumps({"risposta": "dai sei", "agenti": 6}).encode()

    def _fake_urlopen(req, timeout):
        chiamate["url"] = req.full_url
        return _Resp()

    monkeypatch.setattr(config, "SDQ1_URL", "http://motore-finto/ask")
    monkeypatch.setattr("urllib.request.urlopen", _fake_urlopen)
    out = sdq1.ask("forse il campo esiste")
    assert chiamate["url"] == "http://motore-finto/ask"
    assert out["risposta"] == "dai sei"
    assert out["agenti"] == 6
    assert out["provider"] == ["sdq1-esterno:http://motore-finto/ask"]
    assert "nota_ponte" in out


def test_mappa_esiti():
    assert ESITI["sì"] == "VISTO"
    assert ESITI["si"] == "VISTO"
    assert ESITI["no"] == "NEGATO"
    assert ESITI["non visto"] == "NON_VERIFICABILE"
    assert ESITI["non ho visto"] == "NON_VERIFICABILE"


def test_giro_testimone_legacy_su_db(tmp_path, monkeypatch):
    monkeypatch.setattr(db, "DATABASE_PATH", str(tmp_path / "legacy.db"))
    db.init_db()
    tid = db.add_testimone(1, "Fabri", "una chiamata fatta oggi")
    t = db.get_testimone(1, tid)
    assert t["esito"] is None
    assert t["witness_token"] is None
    assert len(db.list_testimoni(1, solo_aperti=True)) == 1
    assert db.set_esito_testimone(1, tid, "VISTO") is True
    assert db.get_testimone(1, tid)["esito"] == "VISTO"
    assert db.list_testimoni(1, solo_aperti=True) == []
    assert db.set_esito_testimone(2, tid, "NEGATO") is False


def test_p5_rifiuta_autore_e_accetta_account_distinto(tmp_path, monkeypatch):
    monkeypatch.setattr(db, "DATABASE_PATH", str(tmp_path / "p5.db"))
    db.init_db()
    token = "w_Q7k9Fa2Rz_test"
    tid = db.add_testimone(101, "Eva", "ha consegnato il documento", witness_token=token)

    status, row = db.record_witness_response(token, 101, "VISTO")
    assert status == "P5_SELF"
    assert row["id"] == tid
    assert db.get_testimone(101, tid)["esito"] is None

    status, row = db.record_witness_response(token, 202, "VISTO")
    assert status == "RECORDED"
    assert row["esito"] == "VISTO"
    assert row["testimone_telegram_id"] == 202
    assert row["verified_at"]

    status, row = db.record_witness_response(token, 303, "NEGATO")
    assert status == "ALREADY"
    assert row["esito"] == "VISTO"
    assert row["testimone_telegram_id"] == 202


def test_record_p5_non_si_chiude_con_esito_legacy(tmp_path, monkeypatch):
    monkeypatch.setattr(db, "DATABASE_PATH", str(tmp_path / "p5-legacy.db"))
    db.init_db()
    tid = db.add_testimone(1, "Eva", "atto", witness_token="w_token12345")
    assert db.set_esito_testimone(1, tid, "VISTO") is False
    assert db.get_testimone(1, tid)["esito"] is None


def test_esito_p5_immutabile_anche_a_livello_db(tmp_path, monkeypatch):
    monkeypatch.setattr(db, "DATABASE_PATH", str(tmp_path / "immutable.db"))
    db.init_db()
    token = "w_immutable12345"
    tid = db.add_testimone(11, "Eva", "atto", witness_token=token)
    status, _ = db.record_witness_response(token, 22, "VISTO")
    assert status == "RECORDED"

    with pytest.raises(sqlite3.IntegrityError):
        with db.connect() as conn:
            conn.execute(
                "UPDATE testimoni SET esito = 'NEGATO' WHERE id = ?",
                (tid,),
            )

    assert db.get_testimone(11, tid)["esito"] == "VISTO"


def test_token_testimone_univoco(tmp_path, monkeypatch):
    monkeypatch.setattr(db, "DATABASE_PATH", str(tmp_path / "tokens.db"))
    db.init_db()
    db.add_testimone(1, "A", "atto A", witness_token="w_unique12345")
    with pytest.raises(sqlite3.IntegrityError):
        db.add_testimone(2, "B", "atto B", witness_token="w_unique12345")
