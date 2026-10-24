import unittest
from unittest.mock import patch

from flight_hunter.fonti import FonteTravelpayouts


class TravelpayoutsFinitePriceTests(unittest.TestCase):
    def setUp(self):
        self.source = FonteTravelpayouts("synthetic-token")

    def _offers(self, value):
        payload = {
            "data": [
                {
                    "destination": "PAR",
                    "value": value,
                    "depart_date": "2026-11-05",
                }
            ]
        }
        with patch.object(self.source, "_get", return_value=payload) as get_mock:
            result = self.source.offerte("BRU", "2026-11-01", "2026-11-30")
        get_mock.assert_called_once()
        return result

    def _calendar(self, value):
        payload = {
            "data": [
                {
                    "value": value,
                    "depart_date": "2026-11-05",
                }
            ]
        }
        with patch.object(self.source, "_get", return_value=payload) as get_mock:
            result = self.source.calendario("BRU", "PAR", "2026-11")
        get_mock.assert_called_once()
        return result

    def test_offers_reject_every_non_finite_price(self):
        for value in (float("nan"), float("inf"), float("-inf")):
            with self.subTest(value=value):
                self.assertEqual(self._offers(value), [])

    def test_calendar_rejects_every_non_finite_price(self):
        for value in (float("nan"), float("inf"), float("-inf")):
            with self.subTest(value=value):
                self.assertEqual(self._calendar(value), [])

    def test_offers_preserve_finite_controls(self):
        for value in (0, 49.95):
            with self.subTest(value=value):
                result = self._offers(value)
                self.assertEqual(len(result), 1)
                self.assertEqual(result[0].prezzo, float(value))
        for value in (-1, "not-a-price"):
            with self.subTest(value=value):
                self.assertEqual(self._offers(value), [])

    def test_calendar_preserves_finite_controls(self):
        for value in (0, 49.95):
            with self.subTest(value=value):
                result = self._calendar(value)
                self.assertEqual(len(result), 1)
                self.assertEqual(result[0].prezzo, float(value))
        for value in (-1, "not-a-price"):
            with self.subTest(value=value):
                self.assertEqual(self._calendar(value), [])


if __name__ == "__main__":
    unittest.main()
