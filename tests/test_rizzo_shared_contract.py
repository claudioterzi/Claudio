"""Rizzo adapter contract, mocked provider only; no live inference evidence."""
import os
import unittest
from unittest.mock import patch

import httpx
from typesafe_sister.client import backend_info, system_one, rank, SystemOneCapabilityUnavailable
from typesafe_sister.policy import universal_questions
from typesafe_sister.universal import assess_project_state

ENV = {'R3_SYSTEMONE_PROVIDER': 'clm', 'R3_SYSTEMONE_BASE_URL': 'http://127.0.0.1:8017', 'R3_SYSTEMONE_MODEL': 'rizzo-latest'}

class RizzoSharedContract(unittest.TestCase):
    def test_rizzo_configuration_reuses_existing_transport(self):
        with patch.dict(os.environ, ENV, clear=True):
            self.assertEqual(backend_info(), {'configured': True, 'provider': 'clm', 'model': 'rizzo-latest', 'base_url': 'http://127.0.0.1:8017'})

    def test_typed_questions_use_systemone_without_key_or_redirects(self):
        questions = universal_questions()
        url = ENV['R3_SYSTEMONE_BASE_URL'] + '/v1/systemone'
        response = httpx.Response(200, json={'model': 'rizzo-latest', 'answers': {}}, request=httpx.Request('POST', url))
        with patch.dict(os.environ, ENV, clear=True), patch('httpx.Client') as client:
            client.return_value.__enter__.return_value.post.return_value = response
            result = system_one({'service':'node-a','health':200}, questions)
        sent = client.return_value.__enter__.return_value.post.call_args
        self.assertEqual(sent.args[0], url)
        self.assertEqual(sent.kwargs['headers'], {})
        self.assertEqual(sent.kwargs['json']['model'], 'rizzo-latest')
        self.assertEqual(sent.kwargs['json']['questions'], questions)
        self.assertFalse(client.call_args.kwargs['follow_redirects'])
        self.assertEqual(result['_r3_provider'], 'clm')

    def test_incomplete_answers_do_not_pass_universal_review(self):
        url = ENV['R3_SYSTEMONE_BASE_URL'] + '/v1/systemone'
        response = httpx.Response(200, json={'model':'rizzo-latest','answers':{}}, request=httpx.Request('POST',url))
        with patch.dict(os.environ, ENV, clear=True), patch('httpx.Client') as client:
            client.return_value.__enter__.return_value.post.return_value = response
            result = assess_project_state('R3', {'health':200,'documents_verified':False})
        self.assertEqual(result['status'],'unavailable')
        self.assertNotIn('verified',result)
        self.assertNotIn('authorized',result)

    def test_provider_failure_does_not_become_approval(self):
        with patch.dict(os.environ, ENV, clear=True), patch('httpx.Client') as client:
            client.return_value.__enter__.return_value.post.side_effect = httpx.ConnectError('fixture down')
            result = assess_project_state('R3',{'proposal':'deploy'})
        self.assertEqual(result['status'],'unavailable')
        self.assertNotIn('authorized',result)
