from rituals.triggers import REGISTRO, esegui_rito
from rituals.mapping import risolvi, mappa_completa


def test_registro_contiene_i_quattro_riti():
    assert set(REGISTRO) == {"Rosso", "Raffaello", "Updater", "Applica"}


def test_riti_restituiscono_stato():
    assert esegui_rito("Rosso", {"energia": 0.7})["rito"] == "Rosso"
    assert esegui_rito("Applica")["applicato"] is True
    assert esegui_rito("Updater")["aggiornamento_richiesto"] is True


def test_rito_sconosciuto():
    try:
        esegui_rito("Blu")
        assert False
    except KeyError:
        pass


def test_mapping_comandi():
    assert risolvi("pytest -q") == "Updater"
    assert risolvi("git push") == "Applica"
    assert risolvi("comando inesistente") is None
    # tutti i comandi mappati puntano a riti reali
    for rito in mappa_completa().values():
        assert rito in REGISTRO
