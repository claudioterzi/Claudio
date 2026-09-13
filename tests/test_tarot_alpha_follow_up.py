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

    def test_follow_up_keeps_the_requested_language(self):
        with patch.object(tarot_alpha, "_ai_follow_up", return_value=(None, None)):
            response = self.client.post("/", json={
                "modalita": "approfondimento",
                "lingua": "en",
                "domanda_utente": "Explain this card.",
                "carte_scelte": [self.chosen],
            })
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data["lingua"], "en")
        self.assertTrue(data["risposta"].startswith("I am rereading your question"))

    def test_fallback_is_deterministic_and_exposes_shared_evidence(self):
        cards, _ = tarot_alpha._normalize_items({
            "carte_scelte": [
                {"carta": tarot_alpha._deck()[0]["nome"], "posizione": "passato", "asse": "ovest", "polarita": "luce"},
                {"carta": tarot_alpha._deck()[1]["nome"], "posizione": "presente", "asse": "sud", "polarita": "ombra"},
                {"carta": tarot_alpha._deck()[2]["nome"], "posizione": "futuro", "asse": "est", "polarita": "luce"},
            ]
        })
        first = tarot_alpha._fallback(cards, "Che cosa devo osservare?", "it")
        second = tarot_alpha._fallback(cards, "Che cosa devo osservare?", "it")
        self.assertEqual(first, second)
        self.assertEqual(first["traccia"]["formula"], "CARTA + ASSE + POLARITA = SIGNIFICATO")
        self.assertEqual(first["traccia"]["carte_ancorate"], [card["carta"] for card in cards])
        self.assertEqual(first["verifica"]["stato"], "superata")
        self.assertGreaterEqual(first["verifica"]["relazioni"], 2)
        self.assertIn("Nel filo temporale", first["messaggio"])

    def test_ai_output_validator_rejects_a_card_outside_the_spread(self):
        cards, _ = tarot_alpha._normalize_items({"carte_scelte": [self.chosen]})
        valid = {
            "messaggio": "Messaggio contestuale.",
            "nodo": "Nodo.",
            "direzione": "Direzione.",
            "domanda_finale": "Domanda?",
            "carte": [{"posizione": "Present", "carta": self.card["nome"], "lettura": "Lettura ancorata."}],
        }
        self.assertIsNotNone(tarot_alpha._validate_main_reading(valid, cards, "it"))
        forged = dict(valid)
        forged["carte"] = [{"posizione": "Present", "carta": "Carta inventata", "lettura": "Lettura."}]
        self.assertIsNone(tarot_alpha._validate_main_reading(forged, cards, "it"))

    def test_follow_up_validator_rejects_unlisted_references(self):
        cards, _ = tarot_alpha._normalize_items({"carte_scelte": [self.chosen]})
        self.assertIsNotNone(tarot_alpha._validate_follow_up({
            "risposta": "Risposta.", "carte_richiamate": [self.card["nome"]]
        }, cards, "it"))
        self.assertIsNone(tarot_alpha._validate_follow_up({
            "risposta": "Risposta.", "carte_richiamate": ["Carta inventata"]
        }, cards, "it"))


class AlphaFollowUpFrontendTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.html = (ROOT / "public" / "tarocchi-manuale-alpha.html").read_text(encoding="utf-8")

    def test_free_question_and_speech_controls_are_present(self):
        self.assertIn("Chiedi a Raffaello qualsiasi cosa su questa lettura.", self.html)
        self.assertIn('id="follow-language"', self.html)
        self.assertIn("lingua:selectedLanguage()", self.html)
        self.assertIn("modalita:'approfondimento'", self.html)
        self.assertIn("speechSynthesis", self.html)
        self.assertIn("Ascolta la lettura", self.html)

    def test_card_by_card_text_uses_a_full_width_layout(self):
        self.assertIn('<article class="why-card">', self.html)
        self.assertIn(".why-card{display:block;width:100%", self.html)


if __name__ == "__main__":
    unittest.main()
