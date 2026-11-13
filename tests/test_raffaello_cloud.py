"""Cloud dialogue uses one mocked provider, real receipt code and fake Redis."""
import json
import unittest
from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import patch

from flask import Flask
import fakeredis
import agora_web
from sdq1 import cloud_raffaello as cloud
from raffaello_identita import IDENTITA


class CloudDialogue(unittest.TestCase):
    def setUp(self):
        app = Flask(__name__)
        app.register_blueprint(agora_web.agora)
        self.client = app.test_client()
        self.redis = fakeredis.FakeRedis()
        for mock in (patch.object(agora_web, '_owner', return_value=True),
                     patch.object(agora_web, '_client', return_value=self.redis)):
            mock.start()
            self.addCleanup(mock.stop)
        provider_patch = patch.object(cloud, 'GeminiProvider')
        self.provider = provider_patch.start()
        self.addCleanup(provider_patch.stop)
        self.provider.return_value.disponibile = True
        self.provider.return_value.completa.return_value = SimpleNamespace(
            testo='Una risposta di prova', errore=None, via_api=True,
            provider='gemini', modello='gemini-2.5-flash')

    def send(self, rid='1' * 32, command='/raffaello Una domanda', **extra):
        return self.client.post('/api/agora', json={'id': rid, 'comando': command, **extra})

    def test_one_call_receipt_and_replay_without_pc_or_second_charge(self):
        with patch('agora_runtime.esegui') as pc:
            response = self.send()
            self.assertEqual(response.status_code, 200)
            record = response.get_json()['richiesta']
            self.assertEqual(record['stato'], 'completato')
            self.assertFalse(record['risultato']['dati']['raffaello_cloud']['pc_richiesto'])
            pc.assert_not_called()
        self.provider.assert_called_once_with(modello='gemini-2.5-flash', api_key=None,
            timeout=20, max_token=600, temperatura=0.4)
        self.provider.return_value.completa.assert_called_once()
        prompt, question = self.provider.return_value.completa.call_args.args
        self.assertTrue(prompt.startswith(IDENTITA))
        self.assertEqual(question, 'Una domanda')
        self.assertEqual(self.send().get_json()['richiesta'], record)
        self.provider.return_value.completa.assert_called_once()
        self.assertEqual(self.send(command='/raffaello Altra domanda').status_code, 409)
        read = self.client.post('/api/agora/richieste/' + '1' * 32, json={})
        self.assertEqual(read.get_json()['richiesta']['risultato'], record['risultato'])

    def test_unsigned_owner_never_calls_provider(self):
        with patch.object(agora_web, '_owner', return_value=False):
            self.assertEqual(self.send().status_code, 403)
        self.provider.assert_not_called()

    def test_invalid_text_and_telegram_copy_never_call_provider(self):
        for command in ('/raffaello', '/raffaello ' + 'x' * 901):
            self.assertEqual(self.send(command=command).status_code, 400)
        self.assertEqual(self.send(telegram=True).status_code, 400)
        self.provider.assert_not_called()

    def test_daily_attempt_limit_and_cached_result_remain_readable(self):
        self.send()
        key = agora_web.PREFIX + 'cloud-quota:' + datetime.now(timezone.utc).date().isoformat()
        self.assertEqual(int(self.redis.get(key)), 1)
        self.assertGreater(self.redis.ttl(key), 0)
        self.redis.set(key, 20)
        self.assertEqual(self.send(rid='2' * 32).status_code, 429)
        self.assertEqual(self.send().status_code, 200)
        self.provider.return_value.completa.assert_called_once()
        self.assertIsNone(self.redis.get(agora_web.PREFIX + 'active'))

    def test_provider_error_is_recorded_without_fallback_or_secret_leak(self):
        self.provider.return_value.completa.return_value.errore = 'private upstream detail'
        response = self.send()
        self.assertEqual(response.status_code, 200)
        record = response.get_json()['richiesta']
        self.assertEqual(record['stato'], 'errore')
        self.assertNotIn('private upstream detail', json.dumps(record))
        self.assertNotIn('risultato', record)
        self.send()
        self.provider.return_value.completa.assert_called_once()

    def test_unavailable_archive_blocks_inference(self):
        with patch.object(agora_web, '_client', side_effect=agora_web.ArchiveUnavailable('Archivio non disponibile')):
            self.assertEqual(self.send().status_code, 503)
        self.provider.assert_not_called()

    def test_active_command_blocks_a_second_cloud_request(self):
        self.redis.set(agora_web.PREFIX + 'active', 'other-request', ex=240)
        self.assertEqual(self.send().status_code, 409)
        self.provider.assert_not_called()

    def test_unconfigured_provider_does_not_attempt_inference(self):
        self.provider.return_value.disponibile = False
        self.assertEqual(self.send().get_json()['richiesta']['stato'], 'errore')
        self.provider.return_value.completa.assert_not_called()

    def test_empty_or_offline_answers_are_not_success(self):
        for change in ({'via_api': False}, {'testo': '  '}):
            self.provider.return_value.completa.return_value = SimpleNamespace(
                **({'testo': 'ok', 'via_api': True, 'errore': None,
                    'provider': 'gemini', 'modello': 'test'} | change))
            with self.assertRaises(RuntimeError):
                cloud.rispondi('Domanda')


if __name__ == '__main__':
    unittest.main()
