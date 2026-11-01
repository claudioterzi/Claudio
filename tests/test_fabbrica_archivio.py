"""Every completed script is kept without expiry and shown only to the owner."""
import json
import os
import unittest
from types import SimpleNamespace
from unittest.mock import patch

import fakeredis
import tarocchi_web
from tests.test_agora import TOKEN, CHAT
from tests import test_fabbrica

AGORA = {'X-Agora': '1', 'Origin': 'http://localhost'}


class Archivio(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        test_fabbrica.TestFabbrica.setUpClass()
        cls.example = test_fabbrica.TestFabbrica.examples[1]

    def setUp(self):
        self.db = fakeredis.FakeRedis()
        for p in (patch.dict(os.environ, {'PERFUME_ARCHIVE_SECRET': 's' * 40,
                      'PERFUME_ARCHIVE_PASSWORD': 'fixture-private-password', 'PERFUME_ARCHIVE_PASSWORD_HASH': '',
                      'TELEGRAM_BOT_TOKEN': TOKEN, 'TELEGRAM_CHAT_ID': CHAT}),
                  patch('fabbrica.client', return_value=self.db),
                  patch('agora_web._redis', return_value=self.db),
                  patch('perfume_studio._redis', return_value=self.db),
                  patch('fabbrica.assess_brief', return_value={'status': 'not_configured'}),
                  patch('fabbrica.providers', return_value=[SimpleNamespace(disponibile=True, completa=self.reply)])):
            p.start()
            self.addCleanup(p.stop)
        self.http = tarocchi_web.app.test_client()
        self.http.get('/api/fabbrica/status')

    def reply(self, system, prompt):
        return SimpleNamespace(via_api=True, testo=json.dumps(self.example), provider='test',
                               modello='test-only', metadata={})

    def generate(self, dream='Vorrei cantare una canzone in un piccolo locale.'):
        return self.http.post('/api/fabbrica/plans', headers={'X-Fabbrica': '1'},
                              json=dict(dream=dream, city='Bruxelles', budget='', timing='', delegation='', intensity=2))

    def login(self):
        return self.http.post('/api/agora/session', json={'password': 'fixture-private-password'}, headers=AGORA)

    def test_completed_scripts_are_archived_without_expiry(self):
        first = self.generate().get_json()
        second = self.generate('Vorrei imparare a dipingere ad acquerello.').get_json()
        self.assertEqual(self.db.ttl('terzi:fabbrica:v1:plan:' + first['id']), -1)
        self.login()
        listing = self.http.get('/api/fabbrica/archivio', headers=AGORA).get_json()
        self.assertEqual([i['id'] for i in listing['items']], [second['id'], first['id']])
        self.assertTrue(listing['items'][0]['dream'].startswith('Vorrei imparare'))
        item = self.http.get('/api/fabbrica/archivio/' + first['id'], headers=AGORA)
        self.assertEqual(item.status_code, 200)
        self.assertNotIn('owner', item.get_json())

    def test_archive_is_private(self):
        pid = self.generate().get_json()['id']
        self.assertEqual(self.http.get('/api/fabbrica/archivio', headers=AGORA).status_code, 403)
        self.assertEqual(self.http.get('/api/fabbrica/archivio/' + pid, headers=AGORA).status_code, 403)
        self.login()
        self.assertEqual(self.http.get('/api/fabbrica/archivio', headers={'Origin': 'http://localhost'}).status_code, 403)

    def test_deleted_script_leaves_the_archive(self):
        pid = self.generate().get_json()['id']
        self.http.delete('/api/fabbrica/plans/' + pid, headers={'X-Fabbrica': '1'})
        self.login()
        self.assertEqual(self.http.get('/api/fabbrica/archivio', headers=AGORA).get_json()['items'], [])

    def test_archive_page_is_served(self):
        page = self.http.get('/archivio-copioni')
        self.assertEqual(page.status_code, 200)
        self.assertIn(b'Archivio dei copioni', page.data)
        page.close()


if __name__ == '__main__':
    unittest.main()
