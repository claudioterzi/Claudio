"""Browser/Telegram command parity and owner-only durable receipts; no live AI."""
import json
import os
import time
import unittest
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import patch

import fakeredis
import agora_runtime
import agora_web
import tarocchi_web
from sdq1.consiglio import Delibera, Voto
from tests.test_agora import init_data, TOKEN, CHAT

HEADERS = {'X-Agora': '1', 'Origin': 'http://localhost'}
RESULT = {'stato': 'completato', 'testo': 'Risposta verificata', 'note': [], 'dati': {}, 'messaggi': []}


class WebCommands(unittest.TestCase):
    def setUp(self):
        self.redis = fakeredis.FakeRedis()
        self.client = tarocchi_web.app.test_client()
        self.start(patch.dict(os.environ, {'PERFUME_ARCHIVE_SECRET': 's' * 40,
                    'PERFUME_ARCHIVE_PASSWORD': 'fixture-private-password', 'PERFUME_ARCHIVE_PASSWORD_HASH': '',
                    'TELEGRAM_BOT_TOKEN': TOKEN, 'TELEGRAM_CHAT_ID': CHAT, 'AGORA_TELEGRAM_BOT_TOKEN': 'fixture:copy-token'}))
        self.start(patch('agora_web._redis', return_value=self.redis))
        self.start(patch('perfume_studio._redis', return_value=self.redis))

    def start(self, p):
        result = p.start()
        self.addCleanup(p.stop)
        return result

    def login(self):
        return self.client.post('/api/agora/session', json={'password': 'fixture-private-password'}, headers=HEADERS)

    def command(self, rid='1' * 32, command='/agenda', **extra):
        return self.client.post('/api/agora', json={'comando': command, 'id': rid, **extra}, headers=HEADERS)

    def test_browser_session_sends_without_telegram_and_result_survives_new_client(self):
        self.assertEqual(self.login().status_code, 200)
        with patch('agora_runtime.esegui', return_value=RESULT) as execute, patch('sdq1.notifiche.invia') as send:
            response = self.command()
        self.assertEqual(response.get_json()['richiesta']['risultato']['testo'], RESULT['testo'])
        execute.assert_called_once_with('/agenda')
        send.assert_not_called()
        second = tarocchi_web.app.test_client()
        second.set_cookie(agora_web.COOKIE, self.client.get_cookie(agora_web.COOKIE).value)
        restored = second.post('/api/agora/richieste/' + '1' * 32, json={}, headers=HEADERS)
        self.assertEqual(restored.get_json()['richiesta']['risultato'], RESULT)
        self.assertEqual(second.post('/api/agora/history', json={}, headers=HEADERS).get_json()['richieste'][0]['stato'], 'completato')

    def test_no_cookie_unsigned_flags_and_cross_origin_never_execute(self):
        with patch('agora_runtime.esegui') as execute:
            for body in ({'comando': '/agenda'}, {'comando': '/agenda', 'owner': True, 'private_session': '1'}, []):
                self.assertEqual(self.client.post('/api/agora', json=body, headers=HEADERS).status_code, 403)
            self.assertEqual(self.client.post('/api/agora/session', json={'password': 'fixture-private-password'}).status_code, 403)
            self.login()
            self.assertEqual(self.client.post('/api/agora', json={'comando': '/agenda'}, headers={'X-Agora': '1', 'Origin': 'https://evil.test'}).status_code, 403)
            self.assertEqual(self.client.post('/api/agora/history', json={}).status_code, 403)
            execute.assert_not_called()
        response = self.client.post('/api/agora', json={}, headers=HEADERS)
        self.assertNotIn('Access-Control-Allow-Origin', response.headers)
        self.assertEqual(response.headers['Cache-Control'], 'no-store')

    def test_retry_same_id_returns_existing_result_without_spend_or_delivery(self):
        self.login()
        with patch('agora_runtime.esegui', return_value=RESULT) as execute, patch('sdq1.notifiche.invia', return_value=True) as send:
            self.assertEqual(self.command(telegram=True).status_code, 200)
            self.assertEqual(self.command(telegram=True).status_code, 200)
            self.assertEqual(self.command(command='/briefing', telegram=True).status_code, 409)
            self.assertEqual(self.command(telegram=False).status_code, 409)
        self.assertEqual(execute.call_count, 1)
        self.assertEqual(send.call_count, 1)

    def test_telegram_failure_preserves_website_result(self):
        self.login()
        with patch('agora_runtime.esegui', return_value=RESULT), patch('sdq1.notifiche.invia', return_value=False):
            record = self.command(telegram=True).get_json()['richiesta']
        self.assertEqual(record['stato'], 'completato')
        self.assertFalse(record['telegram_inviato'])
        self.assertEqual(record['risultato']['testo'], RESULT['testo'])

    def test_concurrent_completed_receipt_after_lock_is_not_executed_again(self):
        self.login()
        old = {'id': '1' * 32, 'comando': '/agenda', 'telegram_richiesto': False, 'stato': 'completato', 'risultato': RESULT}
        with patch('agora_web._record', side_effect=[None, old]), patch('agora_runtime.esegui') as execute:
            self.assertEqual(self.command().get_json()['richiesta'], old)
            execute.assert_not_called()
        self.assertIsNone(self.redis.get(agora_web.PREFIX + 'active'))

    def test_missing_copy_token_does_not_fall_back_to_another_bot(self):
        self.login()
        with patch.dict(os.environ, {'AGORA_TELEGRAM_BOT_TOKEN': ''}), patch('agora_runtime.esegui', return_value=RESULT), patch('sdq1.notifiche.invia') as send:
            record = self.command(telegram=True).get_json()['richiesta']
        self.assertFalse(record['telegram_inviato'])
        send.assert_not_called()

    def test_running_command_blocks_duplicate_and_records_are_private(self):
        self.login()
        self.redis.set(agora_web.PREFIX + 'active', 'another', ex=60)
        with patch('agora_runtime.esegui') as execute:
            self.assertEqual(self.command().status_code, 409)
            execute.assert_not_called()
        outsider = tarocchi_web.app.test_client()
        self.assertEqual(outsider.post('/api/agora/history', json={}, headers=HEADERS).status_code, 403)

    def test_logout_revokes_cookie_even_if_copied(self):
        self.login()
        value = self.client.get_cookie(agora_web.COOKIE).value
        self.assertEqual(self.client.delete('/api/agora/session', json={}, headers=HEADERS).status_code, 200)
        self.client.set_cookie(agora_web.COOKIE, value)
        self.assertFalse(self.client.get('/api/agora/session').get_json()['autorizzato'])

    def test_wrong_password_throttled_and_production_cookie_secure(self):
        for _ in range(5):
            self.assertEqual(self.client.post('/api/agora/session', json={'password': 'wrong'}, headers=HEADERS).status_code, 403)
        self.assertEqual(self.login().status_code, 429)
        self.redis.flushall()
        with patch.dict(os.environ, {'VERCEL': '1'}):
            response = self.login()
        cookie = response.headers['Set-Cookie']
        self.assertIn('Secure', cookie)
        self.assertIn('HttpOnly', cookie)
        self.assertIn('SameSite=Strict', cookie)
        self.assertIn('Path=/', cookie)

    def test_no_storage_or_failed_readback_does_not_claim_success(self):
        self.login()
        with patch('agora_web._redis', return_value=None), patch('agora_runtime.esegui') as execute:
            self.assertEqual(self.command().status_code, 503)
            execute.assert_not_called()
        with patch.object(self.redis, 'get', return_value=b'1'):
            self.assertRaises(Exception, agora_web._save, self.redis, 'f' * 32, {'stato': 'completato'})

    def test_signed_telegram_and_webhook_still_work_but_future_signature_denied(self):
        with patch('agora_runtime.esegui', return_value=RESULT) as execute:
            self.assertEqual(self.command(initData=init_data()).status_code, 200)
            self.assertEqual(self.command(rid='2' * 32, initData=init_data(eta_s=-3600)).status_code, 403)
            execute.assert_called_once()
        self.assertEqual(self.client.post('/api/telegram/prova').status_code, 403)

    def test_all_six_commands_capture_results_without_sending_telegram(self):
        from sdq1 import notifiche
        vote = Voto('TECNICO', 't', 'Una raccomandazione completa', 'Una motivazione completa', 0.8, 'fixture/model')
        council = Delibera('Questione', 'data', [vote], 'Sintesi', None, 'Decisione', 'Regola')
        snapshot = {'meta': {}, 'git': {'commit_short': 'fixture', 'dirty': False}, 'codice': {'file_presenti': 1, 'file': ['f']}, 'scanner': {'score_sistema': 80}}
        response = SimpleNamespace(testo='Riflessione reale della fixture.', via_api=True, errore=None, modello='fixture', provider='Gemini')
        with patch('sdq1.consiglio.ConsiglioAgenti.delibera', return_value=council), \
             patch('sdq1.snapshot.crea_snapshot', return_value=snapshot), \
             patch('sdq1.snapshot.salva_snapshot') as disk_write, \
             patch('sdq1.agenda.carica', return_value={'ok': True, 'ultima_sync': datetime.now(timezone.utc).isoformat()}), \
             patch.object(notifiche, '_consulta_ai', return_value='Risposta modello della fixture'), \
             patch('sdq1.llm.providers.GeminiProvider') as provider, \
             patch('urllib.request.urlopen') as telegram_network:
            provider.return_value.disponibile = True
            provider.return_value.completa.return_value = response
            for cmd in ('/consiglio Questione', '/snapshot', '/agenda', '/agenda skyrights', '/briefing', '/tarocchi', '/riflessione'):
                result = agora_runtime.esegui(cmd)
                self.assertEqual(result['stato'], 'completato', (cmd, result))
                self.assertTrue(result['dati'], cmd)
                self.assertTrue(result['testo'], cmd)
            disk_write.assert_not_called()
            telegram_network.assert_not_called()

    def test_contexts_do_not_mix_and_missing_model_is_not_a_reflection(self):
        def fake(cmd):
            time.sleep(0.01)
            agora_runtime.cattura('Risultato ' + cmd)
        with patch('sdq1.notifiche._esegui_singolo_comando', side_effect=fake), ThreadPoolExecutor(2) as pool:
            results = list(pool.map(agora_runtime.esegui, ['/a', '/b']))
        self.assertEqual([r['testo'] for r in results], ['Risultato a', 'Risultato b'])
        self.assertFalse(agora_runtime.sul_sito())
        with patch('sdq1.llm.providers.GeminiProvider') as provider:
            provider.return_value.disponibile = False
            result = agora_runtime.esegui('/riflessione')
        self.assertEqual(result['stato'], 'errore')
        self.assertNotIn('Il sistema è presente', result['testo'])


if __name__ == '__main__':
    unittest.main()
