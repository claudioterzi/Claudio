"""Regression tests for the Alpha 74 contextual follow-up flow."""
import json
from pathlib import Path
import unittest
from unittest.mock import patch

from api import tarot_alpha


ROOT = Path(__file__).parents[1]


class AlphaFollowUpApiTests(unittest.TestCase):
    def setUp(self):
        self.client = tarot_alpha.app.test_client()
        self.card = json.loads(
            (ROOT / "tarocchi_quantici_alpha.json").read_text(encoding="utf-8")
        )["carte"][0]
        self.chosen = {
            "carta": self.card["nome"],
            "posizione": "presente",
            "posizione_label": "Presente",
            "asse": "sud",
            "polarita": "luce",
        }

    def test_follow_up_is_anchored_to_the_existing_cards(self):
        payload = {
            "modalita": "approfondimento",
            "lettura_id": "reading-test",
            "domanda_originale": "Che cosa devo osservare?",
            "domanda_utente": "Perché questa carta è importante?",
            "carte_scelte": [self.chosen],
            "lettura_precedente": {"messaggio": "Lettura precedente."},
        }
        with patch.object(tarot_alpha, "_ai_follow_up", return_value=(None, None)):
            response = self.client.post("/", json=payload)

        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data["vincolo"], "SOLO_CARTE_ESTRATTE")
        self.assertEqual(data["lettura_id"], "reading-test")
        self.assertEqual(data["carte_richiamate"], [self.card["nome"]])
        self.assertIn(self.card["nome"], data["risposta"])
        self.assertIn(self.card["luce"]["sud"], data["risposta"])

    def test_follow_up_requires_a_free_text_question(self):
        response = self.client.post("/", json={
            "modalita": "approfondimento",
            "domanda_utente": "   ",
            "carte_scelte": [self.chosen],
        })
        self.assertEqual(response.status_code, 400)
        self.assertIn("domanda", response.get_json()["errore"].lower())


class AlphaFollowUpFrontendTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.html = (ROOT / "public" / "tarocchi-manuale-alpha.html").read_text(encoding="utf-8")

    def test_free_question_and_speech_controls_are_present(self):
        self.assertIn("Chiedi a Raffaello qualsiasi cosa su questa lettura.", self.html)
        self.assertIn("modalita:'approfondimento'", self.html)
        self.assertIn("speechSynthesis", self.html)
        self.assertIn("Ascolta la lettura", self.html)

    def test_card_by_card_text_uses_a_full_width_layout(self):
        self.assertIn('<article class="why-card">', self.html)
        self.assertIn(".why-card{display:block;width:100%", self.html)


if __name__ == "__main__":
    unittest.main()
