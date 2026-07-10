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


if __name__ == "__main__":
    unittest.main()
