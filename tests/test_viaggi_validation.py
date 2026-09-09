import unittest
from tarocchi_web import app

class ViaggiValidationTests(unittest.TestCase):
    def test_invalid_requests_are_client_errors(self):
        c=app.test_client()
        for payload in [dict(budget=200,giorni=3,mese='abc'),dict(budget=-10,giorni=-3),dict(budget=200,giorni=3,tipo=42),dict(budget=200,giorni=3,origine=42),['invalid'],dict(budget=200,giorni=3,tipo=[{}])]:
            with self.subTest(payload=payload):
                r=c.post('/api/viaggi/pianifica',json=payload)
                self.assertEqual(r.status_code,400)
                self.assertIn('errore',r.get_json())
    def test_valid_estimates_stay_in_budget(self):
        r=app.test_client().post('/api/viaggi/pianifica',json=dict(budget=200,giorni=3,solo_nel_budget=True))
        self.assertEqual(r.status_code,200)
        self.assertTrue(r.get_json()['proposte'])
        self.assertTrue(all(p['totale']<=200 for p in r.get_json()['proposte']))
