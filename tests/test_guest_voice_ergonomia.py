import unittest
from unittest.mock import patch
from api import tarot_voice

class GuestVoiceTests(unittest.TestCase):
    def test_guest_claims_never_select_a_voice_provider(self):
        for key, value in [('guest_invite','example'),('guest_mode',True),('guest_mode',False),('invito','')]:
            with self.subTest(key=key,value=value), patch.object(tarot_voice, '_provider_order') as provider:
                response=tarot_voice.app.test_client().post('/api/tarocchi/alpha-voce',json={key:value,'testo':'Test sintetico'})
                self.assertEqual(response.status_code,403)
                provider.assert_not_called()

    def test_owner_request_retains_configured_provider_path(self):
        import os
        from tests.test_agora import init_data, TOKEN, CHAT
        with patch.dict(os.environ,{'TELEGRAM_BOT_TOKEN':TOKEN,'TELEGRAM_CHAT_ID':CHAT}),patch.object(tarot_voice,'_provider_order',return_value=([],[],None)) as provider:
            response=tarot_voice.app.test_client().post('/api/tarocchi/alpha-voce',json={'testo':'Test sintetico','initData':init_data()})
            self.assertEqual(response.status_code,503)
            provider.assert_called_once()

    def test_omitting_guest_markers_does_not_grant_voice_spend(self):
        with patch.object(tarot_voice,'_provider_order') as provider:
            response=tarot_voice.app.test_client().post('/api/tarocchi/alpha-voce',json={'testo':'Test sintetico','owner':True})
            self.assertEqual(response.status_code,403)
            provider.assert_not_called()

if __name__=='__main__': unittest.main()
