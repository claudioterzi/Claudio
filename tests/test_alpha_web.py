"""Contratto del frontend Alpha e fedeltà ai significati del canone."""
import json
from pathlib import Path
import unittest
from tarocchi_web import app


class AlphaWebTests(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()
        self.carte = json.loads((Path(__file__).parents[1] / 'tarocchi_quantici_alpha.json').read_text())['carte']

    def test_catalogo_completo(self):
        response = self.client.get('/api/alpha')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json(), self.carte)
        self.assertEqual(len(response.get_json()), 74)

    def test_tutti_i_592_stati_preservano_il_canone(self):
        for carta in self.carte:
            for polarita in ('luce', 'ombra'):
                for asse in ('nord', 'est', 'sud', 'ovest'):
                    with self.subTest(carta=carta['nome'], polarita=polarita, asse=asse):
                        r = self.client.get('/api/alpha/collasso', query_string=dict(carta=carta['nome'], asse=asse, polarita=polarita))
                        self.assertEqual(r.status_code, 200)
                        self.assertEqual(r.get_json()['significato'], carta[polarita][asse])
                        self.assertEqual(r.get_json()['simbolo'], carta['simbolo'])

    def test_parametri_invalidi(self):
        for q in ({}, dict(carta='La Ferita', asse='centro', polarita='luce'), dict(carta='La Ferita', asse='sud', polarita='altra')):
            r = self.client.get('/api/alpha/collasso', query_string=q)
            self.assertEqual(r.status_code, 400)
            self.assertIn('errore', r.get_json())

    def test_carta_sconosciuta(self):
        r = self.client.get('/api/alpha/collasso', query_string=dict(carta='inesistente', asse='sud', polarita='luce'))
        self.assertEqual(r.status_code, 404)

    def test_mazzo_tradizionale_preservato(self):
        r = self.client.get('/api/mazzo')
        self.assertEqual(r.status_code, 200)
        self.assertEqual(len(r.get_json()), 78)


if __name__ == '__main__':
    unittest.main()
