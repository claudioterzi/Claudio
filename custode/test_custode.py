"""Test del prototipo CUSTODE.  Esecuzione: python -m custode.test_custode"""

import unittest

from custode.confronto import confronta
from custode.modelli import ConteggioZona, Inventario
from custode.report import ReportCheckout
from custode.varco import (Direzione, EventoVarco, RegistroTag,
                           TagRegistrato, Varco)


def inventario(etichetta, zona, **quantita):
    inv = Inventario(etichetta)
    inv.aggiungi(ConteggioZona(zona_id=zona, quantita=quantita))
    return inv


class TestConfronto(unittest.TestCase):
    def test_mancanza(self):
        base = inventario("base", "z1", libro=12)
        out = inventario("out", "z1", libro=11)
        (d,) = confronta(base, out)
        self.assertEqual((d.oggetto, d.mancanti, d.in_piu), ("libro", 1, 0))

    def test_nessun_problema(self):
        base = inventario("base", "z1", libro=12)
        self.assertEqual(confronta(base, inventario("out", "z1", libro=12)), [])

    def test_zona_non_fotografata(self):
        base = inventario("base", "z1", libro=12)
        (d,) = confronta(base, Inventario("out"))
        self.assertIn("non fotografata", d.note)


class TestVarco(unittest.TestCase):
    def setUp(self):
        self.registro = RegistroTag()
        self.registro.registra(TagRegistrato(
            epc="E1", oggetto="libro — prova", zona_id="z1", valore_eur=10))
        self.varco = Varco(self.registro)

    def test_uscita_taggata_allarma(self):
        allarme = self.varco.evento(EventoVarco("E1", Direzione.USCITA))
        self.assertIsNotNone(allarme)
        self.assertEqual(len(self.varco.allarmi), 1)

    def test_ingresso_non_allarma(self):
        self.assertIsNone(self.varco.evento(EventoVarco("E1", Direzione.INGRESSO)))

    def test_epc_sconosciuto_ignorato(self):
        self.assertIsNone(self.varco.evento(EventoVarco("X9", Direzione.USCITA)))


class TestReport(unittest.TestCase):
    def test_incrocio_doppia_evidenza(self):
        registro = RegistroTag()
        registro.registra(TagRegistrato(
            epc="E1", oggetto="libro — prova", zona_id="z1", valore_eur=10))
        varco = Varco(registro)
        varco.evento(EventoVarco("E1", Direzione.USCITA))
        discrepanze = confronta(inventario("b", "z1", libro=12),
                                inventario("o", "z1", libro=11))
        report = ReportCheckout(discrepanze, varco.allarmi)
        conferme = report.incroci(registro)
        self.assertEqual(len(conferme), 1)
        self.assertIn("evidenza doppia", conferme[0])


class TestCatalogo(unittest.TestCase):
    def setUp(self):
        import tempfile
        from custode.catalogo import Catalogo, SchedaOggetto
        self.percorso = tempfile.mktemp(suffix=".json")
        self.catalogo = Catalogo(self.percorso)
        self.catalogo.aggiungi(SchedaOggetto(
            epc="E1", nome="Il nome della rosa", categoria="libro",
            zona_id="soggiorno/libreria-ripiano-2", valore_eur=35.0,
            posizione_tag="incollato tra pagina 142 e 143",
            campi={"autore": "Umberto Eco", "isbn": "978-88-452-1066-1"}))
        self.catalogo.aggiungi(SchedaOggetto(
            epc="E2", nome="phon", categoria="elettronica", valore_eur=40.0))

    def tearDown(self):
        import os
        if os.path.exists(self.percorso):
            os.remove(self.percorso)

    def test_bottone_analizza_mancanti(self):
        r = self.catalogo.analizza_mancanti({"E2", "EPC-IGNOTO"})
        self.assertEqual([s.nome for s in r.mancanti], ["Il nome della rosa"])
        self.assertEqual([s.epc for s in r.presenti], ["E2"])
        self.assertEqual(r.epc_sconosciuti, ["EPC-IGNOTO"])
        self.assertAlmostEqual(r.valore_mancante, 35.0)
        self.assertIn("pagina 142", r.testo())

    def test_persistenza(self):
        from custode.catalogo import Catalogo
        riletto = Catalogo(self.percorso)
        scheda = riletto.scheda("E1")
        self.assertEqual(scheda.campi["autore"], "Umberto Eco")
        self.assertEqual(scheda.posizione_tag, "incollato tra pagina 142 e 143")

    def test_export_registro_per_varco(self):
        registro = self.catalogo.registro()
        tag = registro.cerca("E1")
        self.assertEqual(tag.oggetto, "libro — Il nome della rosa")
        self.assertEqual(tag.valore_eur, 35.0)


if __name__ == "__main__":
    unittest.main()
