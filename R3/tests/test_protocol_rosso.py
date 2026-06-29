from r3_core import ProtocolloRosso, FASI
from r3_core.protocol_rosso import RIVELAZIONE, DIREZIONE, MUTAZIONE, FUSIONE


def test_quattro_fasi_in_ordine():
    p = ProtocolloRosso()
    p.esegui({"osservazione": "x", "energia": 0.7})
    assert p.fasi_eseguite() == [RIVELAZIONE, DIREZIONE, MUTAZIONE, FUSIONE]
    assert FASI == (RIVELAZIONE, DIREZIONE, MUTAZIONE, FUSIONE)


def test_direzione_dipende_da_energia():
    assert ProtocolloRosso().esegui({"energia": 0.9})["direzione"] == "avanti"
    assert ProtocolloRosso().esegui({"energia": 0.1})["direzione"] == "raccolta"


def test_fusione_produce_sintesi():
    finale = ProtocolloRosso().esegui({"energia": 0.6})
    assert finale["fuso"] is True
    assert "sintesi" in finale and "mut=" in finale["sintesi"]
