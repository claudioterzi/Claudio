from r3_core import ScacchieraQuantica


def test_dimensione_n8():
    s = ScacchieraQuantica(n=8, seed=7)
    assert len(s) == 64
    assert s.n == 8


def test_determinismo_per_seed():
    a = ScacchieraQuantica(n=8, seed=42).valuta()
    b = ScacchieraQuantica(n=8, seed=42).valuta()
    assert a == b


def test_valuta_in_range():
    s = ScacchieraQuantica(n=8, seed=1)
    assert 0.0 <= s.valuta() <= 1.0


def test_collasso_sopra_soglia():
    s = ScacchieraQuantica(n=8, seed=3)
    # soglia 0 → collassa sempre sul dominante; soglia >1 → mai
    assert s.collassa(0.0) is not None
    assert s.collassa(1.01) is None
