"""Semantic assessment contracts and failure boundaries; no live AI calls."""
import importlib.util
import json
import os
import unittest
from unittest.mock import patch

import httpx

from fabbrica_typesafe import KINDS, MISSING, assess_brief
from typesafe_sister.client import system_one


def answer():
    return {'model': 'jev-test', 'answers': {
        'occasion': {'type': 'choice', 'choice': 'dinner', 'confidence': .96,
                     'probabilities': {key: float(key == 'dinner') for key in KINDS}},
        **{key: {'type': 'noul', 'noul': value} for key, value in {
            'travel': .01, 'music': .99, 'missing_people': .01,
            'missing_date': .99, 'missing_budget': .99, 'missing_place': .01}.items()}}}


class TestTypeSafeAssessment(unittest.TestCase):
    def setUp(self):
        self.brief = {'dream': 'Cena per quattro amici con musica a Bruxelles.',
                      'city': 'Bruxelles', 'budget': 'Da definire', 'timing': '',
                      'delegation': '', 'intensity': 2}

    def test_dinner_hints_are_advisory_and_send_only_current_brief(self):
        with patch('fabbrica_typesafe.system_one', return_value=answer()) as inference:
            result = assess_brief(self.brief, 'Niente viaggio.')
        self.assertEqual(result['status'], 'evaluated')
        self.assertEqual(result['label'], 'Cena')
        self.assertLess(result['signals']['travel'], .1)
        self.assertEqual(result['questions'], [MISSING['date'][1], MISSING['budget'][1]])
        self.assertEqual(inference.call_args.args[0], {'brief': self.brief, 'revision': 'Niente viaggio.'})
        self.assertNotIn('brief', result)
        self.assertNotIn('api_key', result)

    def test_malformed_or_incomplete_probabilities_are_not_presented_as_evaluation(self):
        broken = []
        for value in [float('nan'), float('inf'), -1, 2, True, '0.9']:
            data = answer(); data['answers']['travel']['noul'] = value; broken.append(data)
        data = answer(); del data['answers']['missing_date']; broken.append(data)
        data = answer(); data['answers']['occasion']['choice'] = 'book_now'; broken.append(data)
        data = answer(); data['answers']['occasion']['probabilities'] = {'dinner': 1}; broken.append(data)
        for data in broken:
            with self.subTest(data=data), patch('fabbrica_typesafe.system_one', return_value=data):
                self.assertEqual(assess_brief(self.brief), {'status': 'unavailable'})

    def test_upstream_exception_does_not_disclose_private_text_or_keys(self):
        with patch('fabbrica_typesafe.system_one', side_effect=RuntimeError('PRIVATE_KEY_AND_TEXT')):
            with self.assertLogs('terzi.fabbrica', level='WARNING') as logs:
                result = assess_brief(self.brief)
        self.assertEqual(result, {'status': 'unavailable'})
        self.assertNotIn('PRIVATE_KEY_AND_TEXT', '\n'.join(logs.output))

    def test_unconfigured_never_attempts_network(self):
        with patch.dict(os.environ, {'TYPESAFE_API_KEY': ''}), patch('httpx.Client') as client:
            self.assertEqual(assess_brief(self.brief), {'status': 'not_configured'})
            client.assert_not_called()

    def test_shared_transport_uses_official_schema_and_server_side_key(self):
        with patch('httpx.Client') as client:
            response = httpx.Response(200, json=answer(), request=httpx.Request('POST', 'https://api.typesafe.ai/v1/systemone'))
            client.return_value.__enter__.return_value.post.return_value = response
            result = system_one({'brief': self.brief}, {'x': {'type': 'noul', 'instructions': 'Music?'}},
                                api_key='TEST_ONLY', model='jev-test', base_url='https://api.typesafe.ai')
        sent = client.return_value.__enter__.return_value.post.call_args
        self.assertEqual(sent.args[0], 'https://api.typesafe.ai/v1/systemone')
        self.assertEqual(sent.kwargs['headers']['Authorization'], 'Bearer TEST_ONLY')
        self.assertNotIn('TEST_ONLY', json.dumps(sent.kwargs['json']))
        self.assertFalse(client.call_args.kwargs['follow_redirects'])
        self.assertEqual(result['model'], 'jev-test')

    @unittest.skipUnless(importlib.util.find_spec('fastapi'), 'Optional sister-service dependency')
    def test_sister_service_refuses_missing_and_known_default_tokens(self):
        from fastapi import HTTPException
        from typesafe_sister.app import _check_token
        for token in ['', 'changeme']:
            with patch('typesafe_sister.app.R3_API_TOKEN', token):
                with self.assertRaises(HTTPException) as failure:
                    _check_token('Bearer changeme')
                self.assertEqual(failure.exception.status_code, 503)

    @unittest.skipUnless(importlib.util.find_spec('fastapi'), 'Optional sister-service dependency')
    def test_rrr_policy_is_automatic_on_every_sister_judgment(self):
        from fastapi import HTTPException
        from typesafe_sister.app import (
            JudgeRequest,
            QuestionSpec,
            RRR_FIXED_QUESTIONS,
            RRR_POLICY_VERSION,
            _apply_rrr_policy,
            _wire_questions,
            judge,
        )

        user_questions = _wire_questions({
            'probe': QuestionSpec(type='noul', instructions='Is the proposed action supported?')
        })
        augmented = _apply_rrr_policy(user_questions)
        self.assertIn(RRR_POLICY_VERSION, augmented['probe']['instructions'])
        self.assertTrue(set(RRR_FIXED_QUESTIONS).issubset(augmented))

        with self.assertRaises(HTTPException) as reserved:
            _apply_rrr_policy({'rrr_gate': {'type': 'noul'}})
        self.assertEqual(reserved.exception.status_code, 422)

        request = JudgeRequest(
            state={'claim': 'Three confirmations all came from the same source.'},
            questions={'probe': QuestionSpec(type='noul', instructions='Is the claim independently confirmed?')},
        )
        with patch('typesafe_sister.app.R3_API_TOKEN', 'TEST_TOKEN'), \
             patch('typesafe_sister.app._system_one',
                   return_value={'model': 'jev-test', 'answers': {}}) as inference:
            response = judge(request, 'Bearer TEST_TOKEN')

        sent_questions = inference.call_args.args[1]
        self.assertIn('rrr_p5_independence', sent_questions)
        self.assertIn('rrr_p6_traceability', sent_questions)
        self.assertIn('rrr_falsifiable', sent_questions)
        self.assertIn('rrr_gate', sent_questions)
        self.assertTrue(response['rrr']['active'])
        self.assertEqual(response['rrr']['policy_version'], RRR_POLICY_VERSION)
