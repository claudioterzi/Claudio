import unittest
from unittest.mock import patch

from api import tarot_alpha as base
from api import tarot_alpha_fullspace as full


class Alpha74StateIntegrityTests(unittest.TestCase):
    def test_all_eight_states_match_the_canon(self):
        card = base._deck()[0]
        for axis in ("nord", "est", "sud", "ovest"):
            for polarity in ("luce", "ombra"):
                cards, _ = full._full_space_normalize({
                    "carte_scelte": [{
                        "carta": card["nome"],
                        "posizione": "presente",
                        "posizione_label": "Presente",
                        "asse": axis,
                        "polarita": polarity,
                    }]
                })
                state = cards[0]
                self.assertEqual(state["asse"], axis)
                self.assertEqual(state["polarita"], polarity)
                self.assertEqual(state["significato_canonico"], card[polarity][axis])

    def test_automatic_axis_and_polarity_are_independent_inputs(self):
        with patch.object(full.secrets, "choice", return_value="ovest"):
            with patch.object(base, "_polarity", return_value="ombra"):
                cards, automatic = full._full_space_normalize({"numero_carte": 1})
        self.assertTrue(automatic)
        self.assertEqual(cards[0]["asse"], "ovest")
        self.assertEqual(cards[0]["polarita"], "ombra")

    def test_supported_languages_are_preserved(self):
        card = base._deck()[0]
        cards, _ = full._full_space_normalize({
            "carte_scelte": [{
                "carta": card["nome"],
                "posizione": "presente",
                "posizione_label": "Presente",
                "asse": "nord",
                "polarita": "luce",
            }]
        })
        for language in ("it", "en", "fr", "es"):
            reading = base._fallback(cards, "", language)
            self.assertEqual(reading["lingua"], language)
            self.assertEqual(len(reading["carte"]), 1)


if __name__ == "__main__":
    unittest.main()
