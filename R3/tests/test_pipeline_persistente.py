from pathlib import Path

from r3_core import PipelinePersistente


def test_registra_ed_esegue():
    p = PipelinePersistente()
    p.registra("incr", lambda ctx: {**ctx, "n": ctx.get("n", 0) + 1})
    p.esegui("incr")
    p.esegui("incr")
    assert p.stato["n"] == 2
    assert p.stato["_storia"] == ["incr", "incr"]


def test_trigger_sconosciuto():
    p = PipelinePersistente()
    try:
        p.esegui("inesistente")
        assert False, "doveva sollevare KeyError"
    except KeyError:
        pass


def test_persistenza_su_file(tmp_path: Path):
    f = tmp_path / "stato.json"
    p1 = PipelinePersistente(percorso=f)
    p1.registra("set", lambda ctx: {**ctx, "valore": 99})
    p1.esegui("set")
    # nuova istanza ricarica dallo stesso file
    p2 = PipelinePersistente(percorso=f)
    assert p2.stato.get("valore") == 99


def test_continuo_sequenza():
    p = PipelinePersistente()
    p.registra("a", lambda ctx: {**ctx, "passi": ctx.get("passi", 0) + 1})
    p.continuo(["a", "a", "a"])
    assert p.stato["passi"] == 3
