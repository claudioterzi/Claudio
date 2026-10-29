"""Offline check of the real mistralai SDK against LLMRouter._complete_mistral.

No network and no real key: httpx.MockTransport answers the SDK's HTTP call, so the
test proves the request shape and the router's text/token extraction with the pinned
mistralai version.
"""

import asyncio
import json
import os
import unittest
from unittest.mock import patch

import httpx
import mistralai

from rrremergen.api.router import LLMRouter

_REAL_MISTRAL = mistralai.Mistral


class MistralSDKTests(unittest.TestCase):
    def setUp(self):
        self.requests = []

    def _client_with(self, handler):
        def factory(api_key=None, **kwargs):
            return _REAL_MISTRAL(api_key=api_key, client=httpx.Client(transport=httpx.MockTransport(handler)))
        return factory

    def _complete(self, handler):
        with patch.dict(os.environ, {'MISTRAL_API_KEY': 'TEST_ONLY'}), \
                patch.object(mistralai, 'Mistral', self._client_with(handler)):
            return asyncio.run(LLMRouter()._complete_mistral(
                prompt='Ciao', model='mistral-small-latest', temperature=0.2, max_tokens=50))

    def test_chat_complete_request_and_extraction(self):
        def handler(request):
            self.requests.append(request)
            return httpx.Response(200, json={
                'id': 'cmpl-test', 'object': 'chat.completion', 'model': 'mistral-small-latest',
                'created': 1,
                'choices': [{'index': 0, 'finish_reason': 'stop',
                             'message': {'role': 'assistant', 'content': 'Risposta di prova'}}],
                'usage': {'prompt_tokens': 3, 'completion_tokens': 7, 'total_tokens': 10},
            })

        result = self._complete(handler)

        self.assertEqual(result, {'text': 'Risposta di prova', 'model': 'mistral-small-latest', 'tokens_used': 7})
        self.assertEqual(len(self.requests), 1)
        request = self.requests[0]
        self.assertEqual(request.method, 'POST')
        self.assertTrue(request.url.path.endswith('/v1/chat/completions'), request.url)
        self.assertEqual(request.headers['authorization'], 'Bearer TEST_ONLY')
        body = json.loads(request.content)
        self.assertEqual(body['model'], 'mistral-small-latest')
        self.assertEqual(body['messages'], [{'role': 'user', 'content': 'Ciao'}])
        self.assertEqual(body['temperature'], 0.2)
        self.assertEqual(body['max_tokens'], 50)

    def test_provider_error_is_reported_not_invented(self):
        result = self._complete(lambda request: httpx.Response(401, json={'message': 'Unauthorized'}))

        self.assertTrue(result['text'].startswith('// Error calling Mistral'), result)
        self.assertEqual(result['tokens_used'], 0)


if __name__ == '__main__':
    unittest.main()
