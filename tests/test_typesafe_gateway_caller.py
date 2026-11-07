import contextlib
import copy
import io
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import httpx

from typesafe_sister import smoke


TOKEN = "synthetic-gateway-test-token-not-a-real-secret"
REAL_CLIENT = httpx.Client


def packet():
    return {"state": {"catalog": [{"id": "github_review", "available": True}]},
            "model": "jev-latest", "questions": {
                "next_skill": {"type": "choice", "criteria": {
                    "github_review": "Inspect bounded candidate", "NO_MATCH": "No fit"}},
                "missing": {"type": "noul", "criteria": None}}}


def answer(request):
    return {"provider": "typesafe", "state_sha256": smoke._digest(request["state"]),
            "questions_sha256": smoke._digest(request["questions"]),
            "result": {"model": "jev-1.13.0", "_r3_provider": "typesafe", "answers": {
                "next_skill": {"choice": "github_review", "confidence": 0.8},
                "missing": {"noul": 0.1}}}}


class GatewayCallerTests(unittest.TestCase):
    def run_transport(self, handler, payload=None):
        transport = httpx.MockTransport(handler)
        def client(**kwargs):
            self.assertFalse(kwargs['follow_redirects'])
            return REAL_CLIENT(transport=transport, **kwargs)
        with patch.dict(os.environ, {"R3_API_TOKEN": TOKEN, "R3_TYPESAFE_URL": smoke.CANONICAL_GATEWAY_URL}):
            with patch.object(smoke.httpx, 'Client', side_effect=client):
                return smoke.judge_request(payload or packet())

    def test_validated_gateway_preserves_hashes_actual_model_and_advisory_boundary(self):
        calls = []
        def handler(request):
            calls.append(request)
            self.assertEqual(request.url.path, '/jev/judge')
            self.assertEqual(request.headers['Authorization'], 'Bearer ' + TOKEN)
            body = json.loads(request.content)
            self.assertNotIn('criteria', body['questions']['missing'])
            return httpx.Response(200, json=answer(body))
        result = self.run_transport(handler)
        self.assertEqual(len(calls), 1)
        self.assertEqual(result['response']['result']['model'], 'jev-1.13.0')
        self.assertFalse(result['automatic_actions'])
        self.assertFalse(result['web_search_by_jev'])
        self.assertNotIn(TOKEN, json.dumps(result))

    def test_absent_token_blocks_before_http_and_saves_receipt(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / 'receipt.json'
            with patch.dict(os.environ, {'R3_API_TOKEN': ''}):
                with patch.object(smoke.httpx, 'Client') as client:
                    with contextlib.redirect_stdout(io.StringIO()):
                        code = smoke.main(['--output', str(target)])
            self.assertEqual(code, 2)
            client.assert_not_called()
            receipt = json.loads(target.read_text())
            self.assertEqual(receipt['status'], 'BLOCKED_MISSING_TOKEN')
            self.assertFalse(receipt['inference_executed'])

    def test_preflight_presence_never_means_authenticated(self):
        with patch.dict(os.environ, {'R3_API_TOKEN': TOKEN}):
            with patch.object(smoke.httpx, 'Client') as client:
                result = smoke.access_status()
        client.assert_not_called()
        self.assertEqual(result['status'], 'CREDENTIAL_PRESENT_NOT_AUTHENTICATED')
        self.assertFalse(result['inference_executed'])

    def test_existing_receipt_refused_before_network_and_never_overwritten(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / 'receipt.json'
            target.write_text('original evidence')
            with patch.dict(os.environ, {'R3_API_TOKEN': TOKEN}):
                with patch.object(smoke.httpx, 'Client') as client:
                    with contextlib.redirect_stdout(io.StringIO()):
                        code = smoke.main(['--output', str(target)])
            self.assertEqual(code, 3)
            client.assert_not_called()
            self.assertEqual(target.read_text(), 'original evidence')

    def test_redirect_and_unauthorized_responses_make_only_one_request(self):
        for code in (302, 401):
            with self.subTest(code=code):
                calls = []
                def handler(request):
                    calls.append(request)
                    return httpx.Response(code, headers={'Location': 'https://other.example/steal'})
                with self.assertRaises(httpx.HTTPStatusError):
                    self.run_transport(handler)
                self.assertEqual(len(calls), 1)

    def test_mismatched_hash_missing_answer_unknown_choice_and_other_model_rejected(self):
        normalized = smoke.normalize_request(packet())
        mutations = [
            lambda r: r.update(state_sha256='0' * 64),
            lambda r: r['result']['answers'].pop('missing'),
            lambda r: r['result']['answers']['next_skill'].update(choice='unlisted_skill'),
            lambda r: r['result'].update(model='clm-latest'),
            lambda r: r['result'].update(_r3_provider='clm'),
            lambda r: r.update(provider='clm'),
        ]
        for mutate in mutations:
            result = answer(normalized)
            mutate(result)
            with self.subTest(result=result):
                with self.assertRaises(ValueError):
                    self.run_transport(lambda _: httpx.Response(200, json=result))

    def test_invalid_probabilities_and_nonfinite_metadata_rejected(self):
        normalized = smoke.normalize_request(packet())
        for value in (True, '0.9', -0.1, 1.1, float('nan'), float('inf'), 10 ** 1000):
            result = answer(normalized)
            result['result']['answers']['missing']['noul'] = value
            with self.subTest(value_type=type(value).__name__):
                with self.assertRaises((ValueError, OverflowError)):
                    smoke.validate_response(result, normalized)
        result = answer(normalized)
        result['result']['usage'] = {'unexpected': float('nan')}
        raw = json.dumps(result).encode()
        with self.assertRaises(ValueError):
            self.run_transport(lambda _: httpx.Response(200, content=raw))

    def test_secret_reflection_never_saved_as_success(self):
        normalized = smoke.normalize_request(packet())
        result = answer(normalized)
        result['debug'] = TOKEN
        with self.assertRaises(ValueError):
            self.run_transport(lambda _: httpx.Response(200, json=result))

    def test_oversized_response_rejected(self):
        with self.assertRaises(ValueError):
            self.run_transport(lambda _: httpx.Response(200, content=b'x' * (smoke.MAX_RESPONSE_BYTES + 1)))

    def test_unicode_escaped_secret_reflection_rejected_in_keys_and_values(self):
        normalized = smoke.normalize_request(packet())
        for reflected in ({'debug': [TOKEN]}, {TOKEN: 'debug'}):
            result = answer(normalized)
            result.update(reflected)
            raw = json.dumps(result).replace(TOKEN, ''.join('\\u%04x' % ord(c) for c in TOKEN)).encode()
            self.assertNotIn(TOKEN.encode(), raw)
            with self.subTest(in_key=TOKEN in reflected):
                with self.assertRaises(ValueError):
                    self.run_transport(lambda _: httpx.Response(200, content=raw))

    def test_malformed_or_nonfinite_request_rejected_before_http(self):
        invalid = [copy.deepcopy(packet()) for _ in range(4)]
        invalid[0]['state']['number'] = float('nan')
        invalid[1]['questions']['next_skill']['type'] = ['choice']
        invalid[2]['model'] = 'clm-latest'
        invalid[3]['questions'] = {}
        with patch.dict(os.environ, {'R3_API_TOKEN': TOKEN}):
            with patch.object(smoke.httpx, 'Client') as client:
                for payload in invalid:
                    with self.assertRaises(ValueError):
                        smoke.judge_request(payload)
        client.assert_not_called()

    def test_unsafe_gateway_urls_rejected_without_http(self):
        for url in ('http://example.com', 'https://user:pass@example.com',
                    'https://example.com?q=credential', 'https://example.com#secret'):
            with patch.dict(os.environ, {'R3_API_TOKEN': TOKEN, 'R3_TYPESAFE_URL': url}):
                with self.assertRaises(ValueError):
                    smoke.access_status()

    def test_error_receipt_hides_exception_text(self):
        with patch.dict(os.environ, {'R3_API_TOKEN': TOKEN}):
            with patch.object(smoke, 'judge_request', side_effect=ValueError(TOKEN)):
                out = io.StringIO()
                with contextlib.redirect_stdout(out):
                    code = smoke.main([])
        self.assertEqual(code, 3)
        self.assertNotIn(TOKEN, out.getvalue())
        self.assertFalse(json.loads(out.getvalue())['inference_success'])


if __name__ == '__main__':
    unittest.main()
