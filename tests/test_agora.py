"""Agorà: le delibere arrivano al bot solo da Claudio, con la firma di Telegram."""

import hashlib
import hmac
import json
import os
import time
import unittest
import urllib.parse
import fakeredis
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
        storage = patch('agora_web._redis', return_value=fakeredis.FakeRedis())
        storage.start()
        self.addCleanup(storage.stop)
        self.eseguiti = []
        p = patch("sdq1.notifiche._esegui_singolo_comando", side_effect=self.eseguiti.append)
        p.start()
        self.addCleanup(p.stop)
        self.client = tarocchi_web.app.test_client()

    def webhook(self, upd, **kw):
        intest = {"X-Telegram-Bot-Api-Secret-Token": tarocchi_web._segreto_webhook()}
        return self.client.post("/api/telegram", json=upd, headers=intest, **kw)

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
        self.assertEqual(self.webhook(upd).status_code, 200)
        self.assertEqual(self.eseguiti, ["consiglio Dalla tastiera"])

    def test_webhook_ignora_chi_non_e_claudio(self):
        upd = {"message": {"chat": {"id": 555}, "text": "/consiglio prendo il controllo"}}
        self.webhook(upd)
        self.assertEqual(self.eseguiti, [])

    def test_webhook_con_segreto(self):
        upd = {"message": {"chat": {"id": int(CHAT)}, "text": "/briefing"}}
        with patch.dict(os.environ, {"TELEGRAM_WEBHOOK_SECRET": "segreto-webhook"}):
            self.assertEqual(self.client.post("/api/telegram", json=upd).status_code, 403)
            r = self.client.post("/api/telegram", json=upd, headers={"X-Telegram-Bot-Api-Secret-Token": "segreto-webhook"})
            self.assertEqual(r.status_code, 200)
        self.assertEqual(self.eseguiti, ["briefing"])

    def test_webhook_senza_segreto_rifiutato(self):
        upd = {"message": {"chat": {"id": int(CHAT)}, "text": "/briefing"}}
        self.assertEqual(self.client.post("/api/telegram", json=upd).status_code, 403)
        self.assertEqual(self.eseguiti, [])

    def test_attiva_senza_segreto_vercel_spiega_cosa_fare(self):
        with patch.dict(os.environ, {"VERCEL_AUTOMATION_BYPASS_SECRET": ""}):
            r = self.client.get("/api/telegram/attiva")
        self.assertIn("Protection Bypass for Automation", r.get_data(as_text=True))

    def test_attiva_collega_webhook_e_pulsante(self):
        chiamate = []

        def finta_api(metodo, dati):
            chiamate.append((metodo, dati))
            if metodo == "getMe":
                return {"ok": True, "result": {"id": 777, "username": "AssistenteRaffaelloBot"}}
            return {"ok": True, "description": "fatto", "result": {"pending_update_count": 0}}

        with patch.dict(os.environ, {"VERCEL_AUTOMATION_BYPASS_SECRET": "bypass123"}), \
                patch.object(tarocchi_web, "_telegram_api", side_effect=finta_api):
            r = self.client.get("/api/telegram/attiva")
        self.assertEqual(r.status_code, 200)
        metodi = dict(chiamate)
        ordine = [m for m, _ in chiamate]
        self.assertLess(ordine.index("deleteWebhook"), ordine.index("setWebhook"))
        self.assertFalse(metodi["deleteWebhook"]["drop_pending_updates"])
        self.assertEqual(metodi["setWebhook"]["url"],
                         "https://claudio-ebon.vercel.app/api/telegram?x-vercel-protection-bypass=bypass123")
        self.assertEqual(metodi["setWebhook"]["secret_token"], tarocchi_web._segreto_webhook())
        self.assertIn("/home?x-vercel-protection-bypass=bypass123&x-vercel-set-bypass-cookie=true",
                      metodi["setChatMenuButton"]["menu_button"]["web_app"]["url"])
        self.assertEqual(metodi["setChatMenuButton"]["chat_id"], CHAT)
        self.assertIn("@AssistenteRaffaelloBot", r.get_data(as_text=True))
        comandi = metodi["setMyCommands"]
        self.assertEqual(comandi["scope"], {"type": "chat", "chat_id": CHAT})
        nomi = [c["command"] for c in comandi["commands"]]
        self.assertIn("consiglio", nomi)
        for c in comandi["commands"]:
            self.assertRegex(c["command"], r"^[a-z0-9_]{1,32}$")
            self.assertTrue(3 <= len(c["description"]) <= 256)
        self.assertLessEqual(len(metodi["setMyShortDescription"]["short_description"]), 120)
        self.assertLessEqual(len(metodi["setMyDescription"]["description"]), 512)

    def test_attiva_non_tocca_il_bot_in_polling_su_render(self):
        chiamate = []

        def finta_api(metodo, dati):
            chiamate.append(metodo)
            return {"ok": True, "result": {"id": 8900249704, "username": "ProtocolloRossoBot"}}

        with patch.dict(os.environ, {"VERCEL_AUTOMATION_BYPASS_SECRET": "bypass123"}), \
                patch.object(tarocchi_web, "_telegram_api", side_effect=finta_api):
            r = self.client.get("/api/telegram/attiva")
        self.assertEqual(chiamate, ["getMe"])
        self.assertIn("polling su Render", r.get_data(as_text=True))


    def test_prova_completa_riporta_modelli_e_webhook(self):
        from sdq1.consiglio import Delibera, Voto

        voti = [Voto("STRATEGA", "s", "procedi", "", 0.8, modello="gemini/gemini-2.5-flash"),
                Voto("TECNICO", "t", "Nessun modello ha risposto.", "", 0.0)]
        finta = Delibera(questione="q", timestamp="t", voti=voti, sintesi_agenti="",
                         voto_presidente=None, decisione_finale="", regola_applicata="")
        info = {"ok": True, "result": {
            "url": "https://claudio-ebon.vercel.app/api/telegram?x-vercel-protection-bypass=SEGRETO",
            "pending_update_count": 0}}
        with patch("sdq1.consiglio.ConsiglioAgenti.delibera", return_value=finta), \
                patch("sdq1.consiglio.invia_delibera_telegram", return_value=True), \
                patch.object(tarocchi_web, "_telegram_api", return_value=info):
            r = self.client.post("/api/telegram/prova", json={'initData': init_data()})
        d = r.get_json()
        self.assertEqual([v["ok"] for v in d["consiglio"]], [True, False])
        self.assertTrue(d["inviata_in_chat"])
        self.assertTrue(d["webhook"]["con_passaggio_vercel"])
        self.assertNotIn("SEGRETO", r.get_data(as_text=True), "il segreto non esce mai")


if __name__ == "__main__":
    unittest.main()
