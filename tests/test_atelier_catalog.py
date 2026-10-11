import copy
import json
import unittest
from types import SimpleNamespace
from unittest.mock import patch

import tarocchi_web as web
from atelier_validation import CompositionInvalid, validate_proposal
from studio.parfums.formula_code import decode


class AtelierCatalogTests(unittest.TestCase):
    def setUp(self):
        self.catalog = web._carica_organo_atelier()['materie']
        self.materials = {m['n']: m for m in self.catalog if m['tipo'] != 'SOL'}
        self.proposal = dict(nome='Essai', famille='Floreale', testa=[2, 4], cuore=[21, 40],
                             fondo=[36, 7], scia=[32, 38], overdose=21,
                             concept='Luce', ragionamento='Scelta motivata', riferimento='')

    def test_all_293_ids_can_be_selected_without_substitution(self):
        self.assertEqual(len(self.catalog), 300)
        self.assertEqual(len(self.materials), 293)
        for number in self.materials:
            candidate = copy.deepcopy(self.proposal)
            flat = sum([candidate[k] for k in ('testa', 'cuore', 'fondo', 'scia')], [])
            if number not in flat:
                candidate['testa'][0] = number
            _, pyramid, trail = validate_proposal(json.dumps(candidate), self.materials, (2, 2, 2), 2)
            actual = [m['n'] for group in pyramid.values() for m in group] + [m['n'] for m in trail]
            self.assertIn(number, actual)
            self.assertEqual(actual, sum([candidate[k] for k in ('testa', 'cuore', 'fondo', 'scia')], []))

    def test_incomplete_duplicate_foreign_solvent_and_noninteger_rejected(self):
        cases = []
        for value in (999, 44, 1.5, True):
            p = copy.deepcopy(self.proposal); p['testa'][0] = value; cases.append(p)
        p = copy.deepcopy(self.proposal); p['scia'] = [21, 32]; cases.append(p)
        p = copy.deepcopy(self.proposal); p['cuore'] = []; cases.append(p)
        p = copy.deepcopy(self.proposal); p['scia'] = [1, 3]; cases.append(p)
        for p in cases:
            with self.subTest(proposal=p), self.assertRaises(CompositionInvalid):
                validate_proposal(json.dumps(p), self.materials, (2, 2, 2), 2)

    def test_model_repairs_entire_proposal_and_receives_full_catalog(self):
        broken = copy.deepcopy(self.proposal); broken['scia'] = [21, 32]
        calls = []
        responses = iter([broken, self.proposal])
        class Fake:
            disponibile = True
            def __init__(self, **kw):
                assert kw['max_retries'] == 0
            def completa(self, system, user):
                calls.append((system, user))
                return SimpleNamespace(testo=json.dumps(next(responses)))
        with patch('sdq1.llm.providers.GeminiProvider', Fake), patch('perfume_research.research_reference', return_value={'status':'not_requested', 'reference':''}):
            p, err = web._atelier_componi_ai('Luce', stile='ellena')
        self.assertIsNone(err)
        for m in self.materials.values():
            self.assertIn(f'{m["n"]}|{m["nome"]}|', calls[0][0])
        self.assertIn('ripetuto', calls[1][1])
        self.assertEqual([r[1] for r in p['ricetta']], [2, 4, 21, 40, 36, 7, 32, 38])
        self.assertEqual(p['organo']['materie_disponibili'], 293)
        self.assertEqual(len(p['organo']['supporti']), 7)
        self.assertEqual(p['verifica']['correzioni_modello'], 1)
        self.assertFalse(p['verifica']['aggiunte_automatiche'])
        self.assertEqual(sum(r[2] for r in p['ricetta']), 100)
        self.assertEqual([r['n'] for r in decode(p['formula_code'])], [r[1] for r in p['ricetta']])

    def test_permanent_failure_does_not_create_generic_formula(self):
        class Fake:
            disponibile = True
            def __init__(self, **kw): pass
            def completa(self, *args): return SimpleNamespace(testo='{}')
        with patch('sdq1.llm.providers.GeminiProvider', Fake), patch('sdq1.llm.providers.AnthropicProvider', Fake):
            p, err = web._atelier_componi_ai('Luce', stile='ellena')
        self.assertIsNone(p)
        self.assertIn('nessuna essenza', err)

    def test_api_invalid_input_is_400_and_default_is_full_catalog(self):
        with web.app.test_client() as client:
            for body in ([], 'bad', {'intenzione':[]}, {'intenzione':'Luce','ondata':'bad'}):
                self.assertEqual(client.post('/api/atelier',json=body).status_code,400)
            with patch('tarocchi_web._atelier_componi_ai',return_value=(None,'test')) as compose:
                client.post('/api/atelier',json={'intenzione':'Luce'})
                self.assertEqual(compose.call_args.args[2],2)
                client.get('/api/atelier?intenzione=Luce&ondata=0')
                self.assertEqual(compose.call_args.args[2],0)
