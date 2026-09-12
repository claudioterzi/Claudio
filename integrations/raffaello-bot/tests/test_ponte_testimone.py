"""Test del passo successivo: ponte SDQ-1 ed esito del testimone.

P6: questi test cadono se sdq1.py o terzo.py cambiano contratto
(nomi funzioni, chiavi del dict, mappa ESITI).
"""

from __future__ import annotations

import json

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
    assert ESITI["non visto"] == "NON_VISTO"
    assert ESITI["non ho visto"] == "NON_VISTO"


def test_giro_testimone_su_db(tmp_path, monkeypatch):
    monkeypatch.setattr(db, "DATABASE_PATH", str(tmp_path / "t.db"))
    db.init_db()
    tid = db.add_testimone(1, "Fabri", "una chiamata fatta oggi")
    t = db.get_testimone(1, tid)
    assert t["esito"] is None
    assert len(db.list_testimoni(1, solo_aperti=True)) == 1
    assert db.set_esito_testimone(1, tid, "VISTO") is True
    assert db.get_testimone(1, tid)["esito"] == "VISTO"
    assert db.list_testimoni(1, solo_aperti=True) == []
    assert db.set_esito_testimone(2, tid, "NEGATO") is False
