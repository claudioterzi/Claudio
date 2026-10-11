"""Regia tests: dependencies, privacy, concurrency and persistence boundaries."""
import copy
from datetime import date
import json
from pathlib import Path
import subprocess
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from fabbrica import PREFIX, apply_progress, review_schedule, validate_plan
from tarocchi_web import app


class MemoryRedis:
    def __init__(self):
        self.values = {}
        self.allow_quota = True

    def ping(self):
        return True

    def get(self, key):
        return self.values.get(key)

    def set(self, key, value, ex=None, nx=False):
        if nx and key in self.values:
            return False
        self.values[key] = value
        return True

    def delete(self, key):
        self.values.pop(key, None)

    def eval(self, script, count, *args):
        if count == 3:
            return int(self.allow_quota)
        if count == 4:
            parent, index, output, cache, body, ttl, status = args
            if not self.get(parent): return 0
            self.values.setdefault(index, set()).update([output, cache])
            self.set(output, body)
            if status == 'suggested': self.set(cache, body)
            return 1
        if count == 2:
            parent, index = args
            for key in self.values.get(index, set()): self.delete(key)
            self.delete(parent); self.delete(index)
            return 1
        key, expected, body = args
        current = self.get(key)
        if not current or json.loads(current)['version'] != expected:
            return 0
        self.set(key, body)
        return 1


class TestFabbrica(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        root = Path(__file__).resolve().parents[1]
        script = "global.window={};require('./public/fabbrica-examples.js');process.stdout.write(JSON.stringify(window.FABBRICA_LEVELS));"
        cls.examples = json.loads(subprocess.check_output(['node', '-e', script], cwd=root))

    def setUp(self):
        self.patch_assessment = patch('fabbrica.assess_brief', return_value={'status': 'not_configured'})
        self.assessment = self.patch_assessment.start()
        self.addCleanup(self.patch_assessment.stop)
        self.db = MemoryRedis()
        self.patch_db = patch('fabbrica.client', return_value=self.db)
        self.patch_db.start()
        self.addCleanup(self.patch_db.stop)
        self.provider = SimpleNamespace(disponibile=True, completa=self.reply)
        self.calls = 0
        self.patch_providers = patch('fabbrica.providers', return_value=[self.provider])
        self.patch_providers.start()
        self.addCleanup(self.patch_providers.stop)
        self.http = app.test_client()
        self.http.get('/api/fabbrica/status')
        self.brief = dict(dream='Vorrei cantare una canzone in un piccolo locale.', city='Città di prova',
                          budget='Da definire', timing='', delegation='', intensity=2)
        self.headers = {'X-Fabbrica':'1'}

    def reply(self, system, prompt):
        self.calls += 1
        return SimpleNamespace(via_api=True, testo=json.dumps(self.examples[1]), provider='test', modello='test-only', metadata={'input_tokens':10,'output_tokens':100})

    def generate(self, **extra):
        return self.http.post('/api/fabbrica/plans', json={**self.brief, **extra}, headers=self.headers)

    def test_all_five_levels_are_valid_and_reset_model_status(self):
        counts = []
        for example in self.examples:
            plan = validate_plan(json.dumps(example))
            counts.append(sum(len(s['actions']) for s in plan['scenes']))
            self.assertTrue(all(a['status']=='proposed' for s in plan['scenes'] for a in s['actions']))
        self.assertEqual(counts, [3,6,6,6,10])

    def test_forward_cycle_and_duplicate_dependencies_rejected(self):
        for dependency in [['A2'], ['A1'], ['A1','A1']]:
            example = copy.deepcopy(self.examples[0])
            example['scenes'][0]['actions'][0]['depends_on'] = dependency
            with self.assertRaises(ValueError): validate_plan(json.dumps(example))

    def test_explicit_deadlines_are_reviewed_without_rewriting_history(self):
        for when, expected in [
            ('Entro il 25 agosto 2026', 'Da ripianificare:'),
            ('2026-08-25', 'Da ripianificare:'),
            ('25/08/2026', 'Da ripianificare:'),
            ('25.08.2026', 'Da ripianificare:'),
            ('31 settembre 2026', 'Data proposta non valida'),
            ('2026-02-29', 'Data proposta non valida'),
            ('20 settembre 2026', None),
            ('Entro il 25 settembre 2026', None),
            ('Dopo A1', None),
            ('Appena possibile', None),
            ('25 agosto', None),
        ]:
            with self.subTest(when=when):
                plan = {'scenes': [{'actions': [{'when': when, 'status': 'proposed'}]}]}
                reviewed = review_schedule(plan, date(2026, 9, 20))
                result = reviewed['scenes'][0]['actions'][0]['when']
                if expected:
                    self.assertTrue(result.startswith(expected), result)
                    self.assertEqual(review_schedule(reviewed, date(2026, 9, 20)), reviewed)
                else:
                    self.assertEqual(result, when)
                self.assertEqual(plan['scenes'][0]['actions'][0]['when'], when)
                plan['scenes'][0]['actions'][0]['status'] = 'reported_done'
                self.assertEqual(review_schedule(plan, date(2026, 9, 20)), plan)

    def test_reopened_legacy_deadline_is_flagged_and_keeps_stored_evidence(self):
        record = self.generate().json
        key = PREFIX + 'plan:' + record['id']
        stored = json.loads(self.db.get(key))
        stored['plan']['scenes'][0]['actions'][0]['when'] = 'Entro il 25 agosto 2000'
        original = json.dumps(stored)
        self.db.set(key, original)
        reopened = self.http.get('/api/fabbrica/plans/' + record['id'])
        self.assertEqual(reopened.status_code, 200)
        self.assertTrue(reopened.json['plan']['scenes'][0]['actions'][0]['when'].startswith('Da ripianificare:'))
        self.assertEqual(self.db.get(key), original)

    def test_out_of_order_completion_rejected_and_revoke_cascades(self):
        plan = validate_plan(json.dumps(self.examples[0]))
        with self.assertRaises(ValueError): apply_progress(plan,'A3',True)
        for aid in ['A1','A2','A3']: apply_progress(plan,aid,True)
        apply_progress(plan,'A1',False)
        self.assertTrue(all(a['status']=='proposed' for s in plan['scenes'] for a in s['actions']))

    def test_generation_saved_and_reload_identical(self):
        response = self.generate()
        self.assertEqual(response.status_code,200,response.json)
        record = response.json
        reopened = self.http.get('/api/fabbrica/plans/'+record['id'])
        self.assertEqual(record,reopened.json)
        self.assertEqual(record['brief']['intensity'],2)
        self.assertNotIn('owner',record)
        self.assertNotIn('attempts',record)
        saved = json.loads(self.db.get(PREFIX+'plan:'+record['id']))
        self.assertEqual(len(saved['attempts']),1)
        self.assertEqual(saved['usage']['input_tokens'],10)

    def test_identical_generation_deduplicates_without_provider_call(self):
        first = self.generate().json
        second = self.generate().json
        self.assertEqual(first['id'],second['id'])
        self.assertEqual(self.calls,1)

    def test_other_browser_cannot_read_update_or_delete(self):
        pid = self.generate().json['id']
        stranger = app.test_client(); stranger.get('/api/fabbrica/status')
        for method in ['get','patch','delete']:
            response = getattr(stranger,method)('/api/fabbrica/plans/'+pid, headers=self.headers, json={} if method=='patch' else None)
            self.assertEqual(response.status_code,404)

    def test_cross_origin_and_missing_header_rejected(self):
        self.assertEqual(self.http.post('/api/fabbrica/plans',json=self.brief).status_code,403)
        self.assertEqual(self.http.post('/api/fabbrica/plans',json=self.brief,headers={**self.headers,'Origin':'https://stranger.example'}).status_code,403)
        self.assertEqual(self.calls,0)

    def test_no_public_cors_and_no_cache(self):
        response = self.http.get('/api/fabbrica/status')
        self.assertNotIn('Access-Control-Allow-Origin',response.headers)
        self.assertEqual(response.headers['Cache-Control'],'no-store')
        self.assertIn('HttpOnly',response.headers['Set-Cookie'])
        self.assertIn('SameSite=Strict',response.headers['Set-Cookie'])

    def test_progress_conflict_and_event_source(self):
        record = self.generate().json; url='/api/fabbrica/plans/'+record['id']
        response=self.http.patch(url,json={'version':1,'action_id':'A1','complete':True},headers=self.headers)
        self.assertEqual(response.status_code,200,response.json)
        self.assertEqual(response.json['events'][0]['source'],'user_report')
        self.assertEqual(response.json['version'],2)
        stale=self.http.patch(url,json={'version':1,'action_id':'A2','complete':True},headers=self.headers)
        self.assertEqual(stale.status_code,409)

    def test_revisions_leave_old_plan_intact(self):
        first=self.generate().json
        second=self.generate(parent_id=first['id'],revision='Preferisco un concerto privato.').json
        self.assertNotEqual(first['id'],second['id'])
        self.assertEqual(second['parent_id'],first['id'])
        self.assertEqual(first,self.http.get('/api/fabbrica/plans/'+first['id']).json)

    def test_delete_then_same_brief_can_generate(self):
        first=self.generate().json
        self.assertEqual(self.http.delete('/api/fabbrica/plans/'+first['id'],headers=self.headers).status_code,200)
        second=self.generate()
        self.assertEqual(second.status_code,200,second.json)
        self.assertNotEqual(first['id'],second.json['id'])

    def test_invalid_intensity_does_not_call_provider(self):
        for value in [0,6,True,'5',None]:
            self.assertEqual(self.generate(intensity=value).status_code,400)
        self.assertEqual(self.calls,0)

    def test_quota_and_storage_failure_prevent_paid_calls(self):
        self.db.allow_quota=False
        self.assertEqual(self.generate().status_code,429)
        self.assertEqual(self.calls,0)
        self.assessment.assert_not_called()
        with patch('fabbrica.client',side_effect=RuntimeError('test')):
            self.assertEqual(self.generate().status_code,503)
        self.assertEqual(self.calls,0)

    def test_typesafe_guidance_reaches_generator_and_survives_reload_and_dedup(self):
        advice = {'status': 'evaluated', 'provider': 'typesafe', 'label': 'Cena',
                  'signals': {'travel': .01}, 'questions': ['Quale data?']}
        self.assessment.return_value = advice
        prompts = []
        def reply(system, prompt):
            prompts.append(json.loads(prompt))
            return self.reply(system, prompt)
        self.provider.completa = reply
        record = self.generate().json
        self.assertEqual(record['assessment'], advice)
        self.assertEqual(prompts[0]['semantic_guidance'], advice)
        self.assertEqual(self.http.get('/api/fabbrica/plans/' + record['id']).json, record)
        self.assertEqual(self.generate().json, record)
        self.assessment.assert_called_once_with(record['brief'], '')

    def test_typesafe_failure_keeps_planning_available_without_false_evaluation(self):
        self.assessment.return_value = {'status': 'unavailable'}
        response = self.generate()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json['assessment'], {'status': 'unavailable'})

    def test_dialogue_revision_above_old_700_limit_is_accepted_and_bounded(self):
        first = self.generate().json
        revision = 'Preferenze della cena da rispettare. ' * 80
        revised = self.generate(parent_id=first['id'], revision=revision)
        self.assertEqual(revised.status_code, 200, revised.json)
        self.assertEqual(revised.json['revision'], revision.strip())
        self.assessment.assert_called_with(revised.json['brief'], revision.strip())
        calls = self.calls
        self.assertEqual(self.generate(parent_id=first['id'], revision='x' * 8001).status_code, 400)
        self.assertEqual(self.calls, calls)

    def test_invalid_ai_output_is_saved_but_never_presented_as_plan(self):
        self.provider.completa=lambda *_: SimpleNamespace(via_api=True,testo='not a plan',provider='test',modello='test-only',metadata={})
        response=self.generate()
        self.assertEqual(response.status_code,503)
        saved=json.loads(self.db.get(PREFIX+'plan:'+response.json['id']))
        self.assertEqual(saved['attempts'][0]['output'],'not a plan')
        self.assertEqual(saved['status'],'failed')

    def test_generated_status_cannot_claim_external_execution(self):
        malicious=copy.deepcopy(self.examples[0])
        malicious['scenes'][0]['actions'][0].update(status='verified',reported_at='yesterday')
        plan=validate_plan(json.dumps(malicious))
        self.assertEqual(plan['scenes'][0]['actions'][0]['status'],'proposed')
        self.assertIsNone(plan['scenes'][0]['actions'][0]['reported_at'])

    def test_dialogue_choices_survive_two_revisions_and_reach_typesafe(self):
        first = self.generate().json
        question = first['plan']['questions'][0]
        choice = dict(question=question, answer='Massimo 250 euro complessivi.', type='VINCOLO')
        second = self.generate(parent_id=first['id'], dialogue={'answers': [choice]}, revision='Solo musica di sottofondo.').json
        third = self.generate(parent_id=second['id'], revision='Preferisco venerdì sera.').json
        self.assertEqual(third['root_id'], first['id'])
        self.assertEqual(third['dialogue']['answers'][0]['answer'], choice['answer'])
        self.assertEqual(third['dialogue']['answers'][0]['source'], 'user_choice')
        self.assertEqual(third['dialogue']['revisions'], ['Solo musica di sottofondo.', 'Preferisco venerdì sera.'])
        self.assertIn(choice['answer'], self.assessment.call_args.args[1])
        self.assertEqual(self.http.get('/api/fabbrica/plans/' + third['id']).json, third)
        self.assertEqual(self.http.get('/api/fabbrica/plans/' + first['id']).json, first)

    def test_dialogue_rejects_foreign_question_and_invalid_kind_before_paid_calls(self):
        first = self.generate().json
        for answer in [dict(question='Una domanda estranea', answer='test', type='VINCOLO'),
                       dict(question=first['plan']['questions'][0], answer='test', type=[]),
                       dict(question=first['plan']['questions'][0], answer='x'*901, type='PREFERENZA')]:
            self.assertEqual(self.generate(parent_id=first['id'], dialogue={'answers':[answer]}).status_code, 400)
        self.assertEqual(self.calls, 1)

    def test_empty_questions_are_allowed_when_details_are_complete(self):
        example = copy.deepcopy(self.examples[0]); example['questions'] = []
        self.assertEqual(validate_plan(json.dumps(example))['questions'], [])

    def help_request(self, record, **extra):
        body = dict(version=record['version'], question=record['plan']['questions'][0], answer='', instruction='')
        return self.http.post('/api/fabbrica/plans/' + record['id'] + '/question-help', json={**body, **extra}, headers=self.headers)

    def test_ai_help_is_a_cached_proposal_and_never_applies_choices(self):
        first = self.generate().json
        prompts = []
        proposal = dict(explanation='Questa scelta orienta la cena.', suggestions=[dict(label='Semplice', answer='Preferisco una cena tranquilla.')])
        def reply(system, prompt):
            prompts.append(json.loads(prompt))
            self.assertIn('DATA_ONLY', system)
            return SimpleNamespace(via_api=True, testo=json.dumps(proposal), provider='test', modello='test-only', metadata={})
        self.provider.completa = reply
        first_help = self.help_request(first, instruction='Dammi una soluzione semplice.')
        self.assertEqual(first_help.status_code, 200, first_help.json)
        self.assertEqual(first_help.json['status'], 'suggested')
        self.assertEqual(first_help.json['suggestions'], proposal['suggestions'])
        self.assertNotIn('attempts', first_help.json)
        self.assertEqual(self.help_request(first, instruction='Dammi una soluzione semplice.').json, first_help.json)
        self.assertEqual(len(prompts), 1)
        self.assertEqual(prompts[0]['brief'], first['brief'])
        self.assertNotIn('owner', prompts[0])
        self.assertEqual(self.http.get('/api/fabbrica/plans/' + first['id']).json, first)
        self.assertTrue(any(k.startswith(PREFIX+'help:') for k in self.db.values))
        self.assertEqual(self.http.delete('/api/fabbrica/plans/' + first['id'], headers=self.headers).status_code, 200)
        self.assertFalse(any(k.startswith(PREFIX+'help:') or k.startswith(PREFIX+'help-cache:') for k in self.db.values))

    def test_help_rejects_other_session_stale_version_and_foreign_questions(self):
        first = self.generate().json
        stranger = app.test_client(); stranger.get('/api/fabbrica/status')
        url = '/api/fabbrica/plans/' + first['id'] + '/question-help'
        self.assertEqual(stranger.post(url, json={}, headers=self.headers).status_code, 404)
        self.assertEqual(self.http.post(url, json={}, headers={'Origin':'https://other.example', **self.headers}).status_code, 403)
        self.assertEqual(self.help_request(first, version=0).status_code, 409)
        self.assertEqual(self.help_request(first, version=True).status_code, 409)
        self.assertEqual(self.help_request(first, question='Domanda di un altro piano').status_code, 400)
        self.assertEqual(self.calls, 1)

    def test_help_quota_and_invalid_provider_output_leave_plan_unchanged(self):
        first = self.generate().json
        self.db.allow_quota = False
        self.assertEqual(self.help_request(first).status_code, 429)
        self.assertEqual(self.calls, 1)
        self.db.allow_quota = True
        # The normal planner fixture is deliberately not a valid help response.
        self.assertEqual(self.help_request(first).status_code, 503)
        self.assertEqual(self.http.get('/api/fabbrica/plans/' + first['id']).json, first)
        stored = [json.loads(v) for k, v in self.db.values.items() if k.startswith(PREFIX+'help:')]
        self.assertEqual(len(stored), 1)
        self.assertEqual(len(stored[0]['attempts']), 1)

    def test_failure_logs_diagnosis_without_private_text_or_exception_body(self):
        with patch('fabbrica.client', side_effect=RuntimeError('SECRET_CONNECTION_STRING')):
            with self.assertLogs('terzi.fabbrica', level='WARNING') as logs:
                response = self.generate(dream='Una richiesta privata che deve restare riservata.')
        self.assertEqual(response.status_code, 503)
        text = '\n'.join(logs.output)
        self.assertIn('RuntimeError', text)
        self.assertIn('generation_or_storage_failed', text)
        self.assertNotIn('SECRET_CONNECTION_STRING', text)
        self.assertNotIn('richiesta privata', text)

    def test_telegram_debug_get_never_sends_messages(self):
        with patch.dict('os.environ', {'TELEGRAM_BOT_TOKEN': 'PRIVATE_TOKEN', 'TELEGRAM_CHAT_ID': 'PRIVATE_CHAT'}):
            with patch('urllib.request.urlopen') as network:
                response = self.http.get('/api/telegram/debug')
        network.assert_not_called()
        self.assertEqual(response.json['mode'], 'configuration_only')
        self.assertFalse(response.json['connection_tested'])
        self.assertNotIn('PRIVATE_', response.get_data(as_text=True))


if __name__=='__main__': unittest.main()
