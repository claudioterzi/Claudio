"""Verifiche dello spazio interpretativo Alpha 74 e della lettura 1–7 carte."""
import unittest
from unittest.mock import patch

from api import tarot_alpha
from tarocchi.spazio_interpretativo import configuration_space


class AlphaInterpretiveSpaceTests(unittest.TestCase):
    def setUp(self):
        self.client = tarot_alpha.app.test_client()

    def test_seven_cards_matches_the_canonical_exact_number(self):
        space = configuration_space(7)
        self.assertEqual(space["stati_elementari_per_carta"], 8)
        self.assertEqual(
            space["configurazioni_stessa_lunghezza"],
            "19020913799457669120",
        )
        self.assertEqual(
            space["formula_massima_7"],
            "P(74,7) × 8^7",
        )

    def test_api_supports_every_spread_length_from_one_to_seven(self):
        with patch.object(tarot_alpha, "_ai", return_value=(None, None)):
            for count in range(1, 8):
                with self.subTest(count=count):
                    response = self.client.post("/", json={"numero_carte": count})
                    self.assertEqual(response.status_code, 200)
                    data = response.get_json()
                    self.assertEqual(data["numero_carte"], count)
                    space = data["spazio_interpretativo"]
                    self.assertEqual(space["carte_nella_stesa"], count)
                    self.assertEqual(
                        len(data["registri_epistemici"]["fatti"]["dati_stesa"]),
                        count,
                    )
                    self.assertEqual(
                        data["registri_epistemici"]["ipotesi"]["stato"],
                        "da_verificare",
                    )

    def test_api_rejects_card_counts_outside_the_protocol(self):
        for value in (0, 8, "sette"):
            with self.subTest(value=value):
                response = self.client.post("/", json={"numero_carte": value})
                self.assertEqual(response.status_code, 400)
                self.assertIn("numero_carte", response.get_json()["errore"])


if __name__ == "__main__":
    unittest.main()
