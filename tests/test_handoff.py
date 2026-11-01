"""La regola di rifiuto deve cadere sui difetti che dichiara di prendere.

Ogni test è stato provato rimettendo il difetto (togliendo il controllo
corrispondente in handoff.py): con il controllo spento, il test cade
(CLAUDE.md §7-bis).

    python tests/test_handoff.py     # oppure: pytest tests/test_handoff.py
"""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

import handoff  # noqa: E402

BUONO = """STATO: 6/6 hash del pacchetto corrispondono al manifest.
SCOPERTA: il ledger ricostruito non coincide con l'hash originale.
LIMITE: l'originale delle 12:27 non è disponibile.
PROSSIMA MOSSA: verificare il pacchetto da una macchina diversa.
EVIDENZA: output/RAFFAELLO_L10_MAX_RECONSTRUCTED/MANIFEST.json, zip 51a52dff97f3
"""


def test_handoff_conforme_passa():
    assert handoff.analizza(BUONO)[1] == []


def test_markdown_in_grassetto_e_riconosciuto():
    md = BUONO.replace("STATO:", "**STATO:**").replace("EVIDENZA:", "*   **EVIDENZA:**")
    assert handoff.conforme(md)


def test_campo_mancante_rifiutato():
    senza = "\n".join(r for r in BUONO.splitlines() if not r.startswith("LIMITE"))
    assert any("LIMITE" in e for e in handoff.analizza(senza)[1])


def test_discorsivo_rifiutato():
    errori = handoff.analizza("Ottimo lavoro, direi che siamo a buon punto.")[1]
    assert len([e for e in errori if e.startswith("manca")]) == 5


def test_preambolo_rifiutato():
    assert any("prima del primo campo" in e
               for e in handoff.analizza("Ecco il mio handoff.\n" + BUONO)[1])


def test_campo_ripetuto_rifiutato():
    assert any("ripetuto" in e for e in handoff.analizza(BUONO + "STATO: altro\n")[1])


def test_campo_vuoto_rifiutato():
    vuoto = BUONO.replace("LIMITE: l'originale delle 12:27 non è disponibile.", "LIMITE:")
    assert any("vuoto" in e for e in handoff.analizza(vuoto)[1])


def test_stato_mescolato_con_mossa_rifiutato():
    misto = BUONO.replace("manifest.", "manifest; la prossima cosa da fare è il test.")
    assert any("STATO" in e for e in handoff.analizza(misto)[1])


def test_evidenza_autoreferenziale_rifiutata():
    """Il caso reale del 31/10: EVIDENZA = «il documento che segue»."""
    auto = BUONO.replace(
        "output/RAFFAELLO_L10_MAX_RECONSTRUCTED/MANIFEST.json, zip 51a52dff97f3",
        'Il documento "SEME R³∞ v1.1 / CONTRATTO" che segue.')
    assert any("EVIDENZA" in e for e in handoff.analizza(auto)[1])


def test_parola_tutta_lettere_non_e_un_hash():
    finto = BUONO.replace(
        "output/RAFFAELLO_L10_MAX_RECONSTRUCTED/MANIFEST.json, zip 51a52dff97f3",
        "verificato: defaced")
    assert any("EVIDENZA" in e for e in handoff.analizza(finto)[1])


def _con_allegato(carico, hash_citato=None):
    import hashlib
    h = hash_citato or hashlib.sha256(carico.strip().encode("utf-8")).hexdigest()
    return BUONO.replace("zip 51a52dff97f3", f"seme sha256:{h}") + "ALLEGATO:\n" + carico


SEME = "*   **STATO:** cosa è verificato adesso.\n*   **EVIDENZA:** file / hash.\n"


def test_allegato_con_nomi_dei_campi_non_e_letto_come_handoff():
    """v1.1 non poteva trasportare sé stesso: i campi del seme si contavano due volte."""
    assert handoff.analizza(_con_allegato(SEME))[1] == []


def test_allegato_con_hash_sbagliato_rifiutato():
    assert any("sha256" in e for e in handoff.analizza(_con_allegato(SEME, "0" * 63 + "1"))[1])


def test_allegato_alterato_dopo_la_firma_rifiutato():
    """Provenienza: si ricalcola l'hash del carico, non si legge il campo che lo dichiara."""
    testo = _con_allegato(SEME).replace("cosa è verificato adesso", "tutto è verificato")
    assert any("sha256" in e for e in handoff.analizza(testo)[1])


if __name__ == "__main__":
    test = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for t in test:
        t()
    print(f"OK — {len(test)} test")
