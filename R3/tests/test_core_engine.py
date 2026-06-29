from r3_core import RaffaelloCore, carica_preset


def test_passo_incrementa_iterazione():
    core = RaffaelloCore(carica_preset("equilibrio"))
    core.passo()
    assert core.stato.iterazione == 1
    assert 0.0 <= core.stato.energia <= 1.0


def test_loop_rispetta_max_iterazioni():
    core = RaffaelloCore(carica_preset("prudente"))  # max_iterazioni=32
    core.loop(1000)
    assert core.stato.iterazione <= core.config.max_iterazioni


def test_kill_switch_ferma_il_loop():
    core = RaffaelloCore()
    core.kill("test")
    core.loop(50)
    assert core.stato.fermato
    assert core.stato.iterazione == 0  # fermato prima del primo passo
    assert "test" in core.stato.motivo_stop


def test_riassunto_contiene_qstp():
    core = RaffaelloCore()
    core.passo()
    r = core.riassunto()
    assert "APQ+" in r["qstp"]
    assert r["scacchiera"] == "8x8"
