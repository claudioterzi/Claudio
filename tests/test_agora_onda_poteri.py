"""New ONDA powers stay bounded: text is data, outputs have a fixed shape."""
import unittest
from unittest.mock import Mock

import agora_onda as onda
from tests import test_agora_onda as base


class OndaPoteri(unittest.TestCase):
    setUp = base.AgoraOndaTests.setUp
    record = base.AgoraOndaTests.record
    response = base.AgoraOndaTests.response

    def run_command(self, command, result):
        onda.enqueue(self.client, self.record(command=command))
        execute = Mock(return_value=result)
        done = onda.process_pending(self.client, execute, "worker")
        self.assertEqual(len(done), 1)
        return done[0], execute

    def test_parser_admits_text_only_for_chiedi_and_scrivi(self):
        self.assertEqual(onda.parse_command("/onda chiedi Come sta la Grande Opera?"), "chiedi")
        self.assertEqual(onda.command_text("/onda scrivi una riga per la Morte V"), "una riga per la Morte V")
        self.assertEqual(onda.parse_command("/onda riavvia"), "riavvia")
        self.assertEqual(onda.parse_command("/onda rapporto"), "rapporto")
        for value in ("/onda chiedi", "/onda chiedi   ", "/onda rapporto completo", "/onda riavvia ora",
                      "/onda chiedi " + "x" * 901, "/onda esegui dir", "/onda ferma"):
            with self.subTest(value=value):
                self.assertIsNone(onda.parse_command(value))

    def test_question_reaches_executor_as_data_and_answer_is_the_receipt(self):
        done, execute = self.run_command("/onda chiedi Come sta la Grande Opera?",
                                         {**self.response(), "risposta": "  Cresce, piano.  "})
        execute.assert_called_once_with("chiedi", "Come sta la Grande Opera?")
        self.assertEqual(done["stato"], "completato")
        self.assertEqual(done["risultato"]["testo"], "Cresce, piano.")
        self.assertEqual(done["risultato"]["dati"]["onda"]["proof"]["risposta"], "Cresce, piano.")

    def test_missing_answer_is_not_completed(self):
        done, _ = self.run_command("/onda chiedi Ci sei?", {**self.response(), "risposta": None})
        self.assertEqual(done["stato"], "errore")
        self.assertEqual(done["risultato"]["dati"]["onda"]["codice"], "NESSUNA_RISPOSTA")

    def test_report_keeps_only_known_fields(self):
        report = {"compiti": {"COMPLETATO": 31, "ERRORE": 0, "SEGRETO": 5, "IN_CORSO": -1},
                  "raffaello": "OPERATIVO", "avviato": "2026-10-25T22:48:18", "attivo_da_ore": 163.4,
                  "token": "non deve uscire"}
        done, execute = self.run_command("/onda rapporto", {**self.response(), "rapporto": report})
        execute.assert_called_once_with("rapporto")
        kept = done["risultato"]["dati"]["onda"]["proof"]["rapporto"]
        self.assertEqual(kept["compiti"], {"COMPLETATO": 31, "ERRORE": 0})
        self.assertNotIn("token", kept)
        self.assertIn("completato 31", done["risultato"]["testo"])

    def test_restart_requires_healthy_proof(self):
        done, _ = self.run_command("/onda riavvia", {**self.response(), "riavviato": True})
        self.assertEqual(done["stato"], "completato")
        self.assertIn("riavviata", done["risultato"]["testo"])
        self.client.flushall()
        weak = self.response(processo_presente=False)
        done, _ = self.run_command("/onda riavvia", {**weak, "riavviato": True})
        self.assertEqual(done["stato"], "errore")


if __name__ == "__main__":
    unittest.main()
