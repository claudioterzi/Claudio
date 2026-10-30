"""Owner-only local ONDA commands, captured advice and bounded PC operations."""
import json
import unittest
from types import SimpleNamespace
from unittest.mock import patch, Mock

import agora_runtime
import agora_web
import agora_onda
from tests.test_agora_web import WebCommands, HEADERS
from scripts import agora_onda_pc as pc


class OndaWebTests(unittest.TestCase):
    setUp = WebCommands.setUp
    start = WebCommands.start
    login = WebCommands.login
    command = WebCommands.command

    def test_owner_action_is_queued_once_without_model_or_telegram(self):
        self.login()
        with patch('agora_runtime.esegui') as model, patch('sdq1.notifiche.invia') as telegram:
            response = self.command(command='/onda attiva')
            self.assertEqual(response.status_code, 202)
            record = response.get_json()['richiesta']
            self.assertEqual(record['stato'], 'in_attesa_pc')
            self.assertTrue(record['onda_owner_authorized'])
            self.assertEqual(self.command(command='/onda attiva').get_json()['richiesta'], record)
            model.assert_not_called()
            telegram.assert_not_called()
        self.assertEqual(self.redis.llen('agora:v1:history'), 1)
        self.assertEqual(self.redis.zcard('agora:v1:onda:pending'), 1)

    def test_unsigned_or_cross_origin_request_never_queues(self):
        self.assertEqual(self.command(command='/onda attiva').status_code, 403)
        self.login()
        response = self.client.post('/api/agora', json={'comando': '/onda attiva'},
                                    headers={'X-Agora': '1', 'Origin': 'https://elsewhere.invalid'})
        self.assertEqual(response.status_code, 403)
        self.assertEqual(self.redis.zcard('agora:v1:onda:pending'), 0)

    def test_unknown_actions_and_telegram_copy_are_rejected(self):
        self.login()
        for command in ('/onda elimina', '/onda attiva;whoami', '/onda attiva altro'):
            self.assertEqual(self.command(command=command).status_code, 400)
        self.assertEqual(self.command(command='/onda attiva', telegram=True).status_code, 400)
        self.assertEqual(self.redis.zcard('agora:v1:onda:pending'), 0)

    def test_error_after_enqueue_never_overwrites_durable_receipt(self):
        self.login()
        preserved = []
        def save_then_fail(client, record):
            queued = agora_onda.enqueue(client, record)
            preserved.append(queued)
            raise agora_onda.OndaArchiveError('Injected failure after durable write')
        with patch('agora_web.enqueue_onda', side_effect=save_then_fail):
            self.assertEqual(self.command(command='/onda attiva').status_code, 503)
        self.assertEqual(agora_web._record(self.redis, '1' * 32), preserved[0])
        self.assertEqual(self.command(command='/onda attiva').status_code, 202)

    def test_retry_and_history_repair_queue_without_resetting_receipt(self):
        self.login()
        original = self.command(command='/onda stato').get_json()['richiesta']
        self.redis.zrem('agora:v1:onda:pending', original['id'])
        self.assertEqual(self.command(command='/onda stato').get_json()['richiesta'], original)
        self.assertEqual(self.redis.zcard('agora:v1:onda:pending'), 1)
        self.redis.zrem('agora:v1:onda:pending', original['id'])
        restored = self.client.post('/api/agora/richieste/' + original['id'], json={}, headers=HEADERS)
        self.assertEqual(restored.get_json()['richiesta'], original)
        self.assertEqual(self.redis.zcard('agora:v1:onda:pending'), 1)

    def test_parent_council_is_preserved_and_reference_is_idempotent(self):
        self.login()
        parent = {'id': 'a' * 32, 'comando': '/consiglio Attiva onda', 'telegram_richiesto': False,
                  'stato': 'completato', 'risultato': {'testo': 'Originale immutato'}}
        agora_web._save(self.redis, parent['id'], parent)
        response = self.command(command='/onda attiva', riferimento=parent['id'])
        self.assertEqual(response.status_code, 202)
        self.assertEqual(response.get_json()['richiesta']['riferimento'], parent['id'])
        self.assertEqual(agora_web._record(self.redis, parent['id']), parent)
        self.assertEqual(self.command(command='/onda attiva').status_code, 409)

    def test_model_recommendation_does_not_create_an_action(self):
        council = {'questione': 'Attiva onda', 'voti': [], 'sintesi_agenti': 'Attiva onda', 'decisione_finale': 'Attiva onda'}
        def fake(command):
            agora_runtime.dato('consiglio', council)
            agora_runtime.cattura('Parere del modello')
        with patch('sdq1.notifiche._esegui_singolo_comando', side_effect=fake):
            ordinary = agora_runtime.esegui('/consiglio Quale sarebbe una buona idea?')
            direct = agora_runtime.esegui('/consiglio Attiva onda')
        self.assertNotIn('azione_proposta', ordinary['dati'])
        self.assertEqual(direct['dati']['azione_proposta']['comando'], '/onda attiva')
        self.assertEqual(self.redis.zcard('agora:v1:onda:pending'), 0)


class PcAdapterTests(unittest.TestCase):
    def proof(self):
        return {'servizio_recente': True, 'processo_presente': True, 'pid': 29840,
                'agenti_operativi': ['NARR-003', 'NARR-013']}

    def test_existing_healthy_service_is_observed_without_start(self):
        with patch.object(pc, 'observe', return_value=self.proof()), patch.object(pc, 'powershell') as shell:
            result = pc.execute('attiva')
        self.assertTrue(result['ok'])
        self.assertFalse(result['proof']['avvio_richiesto'])
        shell.assert_not_called()

    def test_observation_rechecks_freshness_after_process_query(self):
        state = Mock()
        state.read_text.return_value = json.dumps({'pid': 29840, 'attivi': ['NARR-003', 'NARR-013'],
            'agenti': {'NARR-003': {'stato': 'OPERATIVO'}, 'NARR-013': {'stato': 'OPERATIVO'}}})
        state.stat.return_value = SimpleNamespace(st_mtime=100)
        with patch.object(pc, 'STATE', state), patch.object(pc.time, 'time', side_effect=[100, 120]), \
             patch.object(pc, 'powershell', return_value=SimpleNamespace(returncode=0, stdout='True')):
            result = pc.observe()
        self.assertTrue(result['processo_presente'])
        self.assertFalse(result['servizio_recente'])

    def test_stale_process_is_not_reported_active_or_force_restarted(self):
        proof = self.proof()
        proof['servizio_recente'] = False
        with patch.object(pc, 'observe', return_value=proof), patch.object(pc, 'powershell') as shell:
            self.assertFalse(pc.execute('attiva')['ok'])
        shell.assert_not_called()

    def test_unknown_action_does_not_observe_or_execute(self):
        with patch.object(pc, 'observe') as observe, patch.object(pc, 'powershell') as shell:
            self.assertFalse(pc.execute('delete')['ok'])
        observe.assert_not_called()
        shell.assert_not_called()

    def test_failed_task_start_never_becomes_success(self):
        proof = self.proof()
        proof['processo_presente'] = False
        with patch.object(pc, 'observe', return_value=proof), \
             patch.object(pc, 'powershell', return_value=SimpleNamespace(returncode=1)) as shell:
            self.assertFalse(pc.execute('attiva')['ok'])
        self.assertEqual(shell.call_count, 1)
        self.assertIn("'R3_ONDA_servizio'", shell.call_args.args[0])


if __name__ == '__main__':
    unittest.main()
