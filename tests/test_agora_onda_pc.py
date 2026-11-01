"""The PC adapter hands owner text to onda.chiedi as one argv item, never a shell."""
import os
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from scripts import agora_onda_pc as pc


class AdapterAsk(unittest.TestCase):
    def test_text_is_a_single_argv_item_after_double_dash(self):
        text = "-rf; Stop-Computer & echo $(boom)"
        with patch.dict(os.environ, {"ONDA_SEGRETO": "x"}), \
             patch.object(pc.subprocess, "run", return_value=SimpleNamespace(returncode=0, stdout="Risposta\n")) as run:
            self.assertEqual(pc.ask("chiedi", text), "Risposta")
        argv = run.call_args.args[0]
        self.assertEqual(argv[-2:], ["--", text])
        self.assertNotIn("shell", run.call_args.kwargs)
        self.assertNotIn("--scrivi", argv)

    def test_scrivi_flag_and_bounds(self):
        with patch.dict(os.environ, {"ONDA_SEGRETO": "x"}), \
             patch.object(pc.subprocess, "run", return_value=SimpleNamespace(returncode=0, stdout="Riga")) as run:
            pc.ask("scrivi", "una riga")
            self.assertIn("--scrivi", run.call_args.args[0])
            self.assertIsNone(pc.ask("chiedi", "x" * 901))
            self.assertIsNone(pc.ask("chiedi", "  "))

    def test_no_secret_or_failed_answer_gives_none(self):
        with patch.dict(os.environ, {"ONDA_SEGRETO": ""}):
            self.assertIsNone(pc.ask("chiedi", "Ci sei?"))
        with patch.dict(os.environ, {"ONDA_SEGRETO": "x"}), \
             patch.object(pc.subprocess, "run", return_value=SimpleNamespace(returncode=1, stdout="[NESSUNA_RISPOSTA]")):
            self.assertIsNone(pc.ask("chiedi", "Ci sei?"))

    def test_unknown_action_is_refused(self):
        self.assertFalse(pc.execute("esegui", "dir")["ok"])


if __name__ == "__main__":
    unittest.main()
