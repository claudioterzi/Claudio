"""Agorà: le delibere arrivano al bot solo da Claudio, con la firma di Telegram."""

import hashlib
import hmac
import json
import os
import time
import unittest
import urllib.parse
from unittest.mock import patch

import tarocchi_web

TOKEN = "123456:token-di-prova"
CHAT = "1034473460"


def init_data(user_id=CHAT, eta_s=0, token=TOKEN, manomesso=False):
    campi = {
        "auth_date": str(int(time.time()) - eta_s),
        "query_id": "AAHdF6IQAAAAAN0XohDhrOrc",
        "user": json.dumps({"id": int(user_id), "first_name": "Claudio"}),
    }
    controllo = "\n".join(f"{k}={v}" for k, v in sorted(campi.items()))
    chiave = hmac.new(b"WebAppData", token.encode(), hashlib.sha256).digest()
    campi["hash"] = hmac.new(chiave, controllo.encode(), hashlib.sha256).hexdigest()
    if manomesso:
        campi["user"] = json.dumps({"id": int(user_id), "first_name": "Intruso"})
    return urllib.parse.urlencode(campi)


class TestAgora(unittest.TestCase):
    def setUp(self):
        self.env = patch.dict(os.environ, {"TELEGRAM_BOT_TOKEN": TOKEN, "TELEGRAM_CHAT_ID": CHAT}, clear=False)
        self.env.start()
        self.addCleanup(self.env.stop)
        self.eseguiti = []
        p = patch("sdq1.notifiche._esegui_singolo_comando", side_effect=self.eseguiti.append)
        p.start()
        self.addCleanup(p.stop)
        self.client = tarocchi_web.app.test_client()

    def agora(self, comando, dati):
        return self.client.post("/api/agora", json={"comando": comando, "initData": dati})

    def test_delibera_firmata_da_claudio_arriva_al_consiglio(self):
        r = self.agora("/consiglio Apro la ASBL a novembre?", init_data())
        self.assertEqual(r.status_code, 200)
        self.assertEqual(self.eseguiti, ["consiglio Apro la ASBL a novembre?"])

    def test_firma_falsa_scaduta_o_di_altri_rifiutata(self):
        for dati in (init_data(manomesso=True), init_data(eta_s=2 * 86_400),
                     init_data(token="999:altro-bot"), init_data(user_id="555"), "", "hash=abc"):
            self.assertEqual(self.agora("/consiglio x", dati).status_code, 403)
        self.assertEqual(self.eseguiti, [])

    def test_solo_i_comandi_dell_agora(self):
        self.assertEqual(self.agora("/scan", init_data()).status_code, 400)
        self.assertEqual(self.agora("consiglio senza barra", init_data()).status_code, 400)
        self.assertEqual(self.eseguiti, [])

    def test_webhook_legge_web_app_data(self):
        upd = {"message": {"chat": {"id": int(CHAT)}, "web_app_data": {"data": "/consiglio Dalla tastiera", "button_text": "Agorà"}}}
        self.assertEqual(self.client.post("/api/telegram", json=upd).status_code, 200)
        self.assertEqual(self.eseguiti, ["consiglio Dalla tastiera"])

    def test_webhook_ignora_chi_non_e_claudio(self):
        upd = {"message": {"chat": {"id": 555}, "text": "/consiglio prendo il controllo"}}
        self.client.post("/api/telegram", json=upd)
        self.assertEqual(self.eseguiti, [])

    def test_webhook_con_segreto(self):
        upd = {"message": {"chat": {"id": int(CHAT)}, "text": "/briefing"}}
        with patch.dict(os.environ, {"TELEGRAM_WEBHOOK_SECRET": "segreto-webhook"}):
            self.assertEqual(self.client.post("/api/telegram", json=upd).status_code, 403)
            r = self.client.post("/api/telegram", json=upd, headers={"X-Telegram-Bot-Api-Secret-Token": "segreto-webhook"})
            self.assertEqual(r.status_code, 200)
        self.assertEqual(self.eseguiti, ["briefing"])


if __name__ == "__main__":
    unittest.main()
