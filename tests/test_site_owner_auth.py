"""The owner's private browser session is recognised by tarot readings and voice."""
import os
import unittest
from unittest.mock import patch

import fakeredis
import site_owner_auth
import tarocchi_web
from tests.test_agora import TOKEN, CHAT

HEADERS = {'X-Agora': '1', 'Origin': 'http://localhost'}


class SiteOwner(unittest.TestCase):
    def setUp(self):
        self.redis = fakeredis.FakeRedis()
        self.client = tarocchi_web.app.test_client()
        for p in (patch.dict(os.environ, {'PERFUME_ARCHIVE_SECRET': 's' * 40,
                      'PERFUME_ARCHIVE_PASSWORD': 'fixture-private-password', 'PERFUME_ARCHIVE_PASSWORD_HASH': '',
                      'TELEGRAM_BOT_TOKEN': TOKEN, 'TELEGRAM_CHAT_ID': CHAT}),
                  patch('agora_web._redis', return_value=self.redis),
                  patch('perfume_studio._redis', return_value=self.redis)):
            p.start()
            self.addCleanup(p.stop)

    def recognised(self, headers=HEADERS, cookie=True):
        value = self.client.get_cookie(site_owner_auth.COOKIE)
        environ = {'HTTP_COOKIE': f'{site_owner_auth.COOKIE}={value.value}'} if cookie and value else {}
        with tarocchi_web.app.test_request_context('/api/tarocchi/alpha-leggi', method='POST',
                                                   headers=headers, environ_base=environ):
            return site_owner_auth.site_owner({})

    def test_password_session_is_recognised(self):
        self.assertEqual(self.client.post('/api/agora/session', json={'password': 'fixture-private-password'},
                                          headers=HEADERS).status_code, 200)
        self.assertTrue(self.recognised())

    def test_no_session_wrong_origin_or_missing_marker_is_not_recognised(self):
        self.assertFalse(self.recognised())
        self.client.post('/api/agora/session', json={'password': 'fixture-private-password'}, headers=HEADERS)
        self.assertFalse(self.recognised(headers={'Origin': 'http://localhost'}))
        self.assertFalse(self.recognised(headers={**HEADERS, 'Origin': 'https://evil.example'}))
        self.assertFalse(self.recognised(cookie=False))

    def test_logout_revokes_recognition(self):
        self.client.post('/api/agora/session', json={'password': 'fixture-private-password'}, headers=HEADERS)
        self.client.delete('/api/agora/session', headers=HEADERS)
        self.assertFalse(self.recognised())

    def test_forged_cookie_is_rejected(self):
        environ = {'HTTP_COOKIE': f'{site_owner_auth.COOKIE}=forged'}
        with tarocchi_web.app.test_request_context('/api/tarocchi/alpha-leggi', method='POST',
                                                   headers=HEADERS, environ_base=environ):
            self.assertFalse(site_owner_auth.site_owner({}))


if __name__ == '__main__':
    unittest.main()
