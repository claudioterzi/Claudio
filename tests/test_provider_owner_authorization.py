import os
import unittest
from unittest.mock import patch
from api import tarot_alpha as alpha, tarot_voice
from tests.test_agora import init_data, TOKEN, CHAT

def card():
    return {'carta': alpha._deck()[0]['nome'], 'posizione': 'presente', 'asse': 'nord', 'polarita': 'luce'}

class ProviderOwnerTests(unittest.TestCase):
    def test_omitting_guest_fields_or_forging_owner_never_selects_ai(self):
        candidates=[{}, {'owner':True}, {'initData':'owner=1'}, {'initData':'hash=%C3%A9'}, {'initData':init_data(user_id='999')}, {'initData':init_data(eta_s=86401)}, {'initData':init_data(manomesso=True)}]
        with patch.dict(os.environ,{'TELEGRAM_BOT_TOKEN':TOKEN,'TELEGRAM_CHAT_ID':CHAT}):
            for index, extra in enumerate(candidates):
                for follow in [False,True]:
                    with self.subTest(case=index,follow=follow),patch.object(alpha,'_ai') as ai,patch.object(alpha,'_ai_follow_up') as follow_ai:
                        body={'domanda':'Test sintetico','domanda_utente':'Test sintetico','carte_scelte':[card()],**extra}
                        if follow:body['modalita']='approfondimento'
                        result=alpha.app.test_client().post('/api/tarocchi/alpha-leggi',json=body)
                        self.assertEqual(result.status_code,200)
                        ai.assert_not_called();follow_ai.assert_not_called()

    def test_invalid_or_missing_owner_signature_never_selects_voice(self):
        with patch.dict(os.environ,{'TELEGRAM_BOT_TOKEN':TOKEN,'TELEGRAM_CHAT_ID':CHAT}):
            for index, extra in enumerate([{},{'initData':'owner=1'},{'initData':'hash=%C3%A9'},{'initData':init_data(user_id='999')},{'initData':init_data(eta_s=86401)}]):
                with self.subTest(case=index),patch.object(tarot_voice,'_provider_order') as provider:
                    result=tarot_voice.app.test_client().post('/api/tarocchi/alpha-voce',json={'testo':'Test sintetico',**extra})
                    self.assertEqual(result.status_code,403);provider.assert_not_called()

if __name__=='__main__':unittest.main()
