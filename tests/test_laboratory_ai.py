import hashlib
import hmac
import json
import os
import time
import unittest
import uuid
from unittest.mock import patch

from api import laboratory_ai as bridge


def payload():
    return {"model":bridge.TEXT_MODEL,"store":False,"max_output_tokens":100,
            "instructions":"Fictional culinary test", "input":[{"role":"user","content":[{"type":"input_text","text":"Zuppa di carote"}]}],
            "text":{"format":{"type":"json_schema","name":"test","strict":True,"schema":{"type":"object","properties":{},"additionalProperties":False}}}}


class BridgeTests(unittest.TestCase):
    def setUp(self):
        self.env = patch.dict(os.environ, {"LE_LABO_BRIDGE_SECRET":"unit-test-only-"*4,"OPENAI_API_KEY":"fake-provider-key"})
        self.env.start()
        self.addCleanup(self.env.stop)
        self.client = bridge.app.test_client()

    def send(self, data=None, operation="responses", *, age=0, tamper=False):
        path = bridge.BASE + operation
        body = json.dumps(data if data is not None else payload()).encode()
        stamp, nonce = str(int(time.time())-age), str(uuid.uuid4())
        msg = f"POST\n{path}\n{stamp}\n{nonce}\n{hashlib.sha256(body).hexdigest()}"
        signature = hmac.new(os.environ["LE_LABO_BRIDGE_SECRET"].encode(),msg.encode(),hashlib.sha256).hexdigest()
        return self.client.post(path,data=body+(b" " if tamper else b""),content_type="application/json",
                                headers={"X-Labo-Time":stamp,"X-Labo-Nonce":nonce,"X-Labo-Signature":signature})

    @patch.object(bridge,"reserve")
    @patch.object(bridge.httpx,"post")
    def test_unauthorized_never_contacts_provider(self, upstream, reserve):
        self.assertEqual(self.client.post(bridge.BASE+"responses",json=payload()).status_code,401)
        self.assertEqual(self.send(age=121).status_code,401)
        self.assertEqual(self.send(tamper=True).status_code,401)
        upstream.assert_not_called(); reserve.assert_not_called()

    @patch.object(bridge,"reserve",return_value=1)
    @patch.object(bridge.httpx,"post")
    def test_valid_response_and_key_in_place(self, upstream, reserve):
        upstream.return_value = bridge.httpx.Response(200,json={"status":"completed","output":[]})
        result = self.send()
        self.assertEqual(result.status_code,200)
        self.assertEqual(result.json["status"],"completed")
        self.assertEqual(upstream.call_args.args[0],"https://api.openai.com/v1/responses")
        self.assertEqual(upstream.call_args.kwargs["headers"]["Authorization"],"Bearer fake-provider-key")
        self.assertNotIn("fake-provider-key",result.text)
        self.assertEqual(result.headers["Cache-Control"],"private, no-store")

    @patch.object(bridge,"reserve",return_value=1)
    @patch.object(bridge.httpx,"post")
    def test_upstream_error_is_sanitized(self, upstream, reserve):
        upstream.return_value = bridge.httpx.Response(401,json={"error":{"message":"bad key fake-provider-key"}})
        result = self.send()
        self.assertEqual(result.status_code,502)
        self.assertEqual(result.json["error"]["code"],"provider_credentials")
        self.assertNotIn("fake-provider-key",result.text)

    @patch.object(bridge,"reserve")
    @patch.object(bridge.httpx,"post")
    def test_replay_rate_limit_and_outage_fail_closed(self, upstream, reserve):
        for value, expected in [(-1,409),(0,429)]:
            reserve.return_value=value
            self.assertEqual(self.send().status_code,expected)
        reserve.side_effect=RuntimeError("unavailable")
        self.assertEqual(self.send().status_code,503)
        upstream.assert_not_called()

    @patch.object(bridge,"reserve")
    def test_reject_arbitrary_models_tools_and_urls(self, reserve):
        for change in [{"model":"expensive-other-model"},{"max_output_tokens":999999},{"store":True},{"tools":[{"type":"web_search"}]},
                       {"input":[{"role":"user","content":[{"type":"input_image","image_url":"https://elsewhere.example/image"}]}]}]:
            self.assertEqual(self.send({**payload(),**change}).status_code,400)
        reserve.assert_not_called()

    @patch.object(bridge,"reserve",return_value=1)
    @patch.object(bridge.httpx,"post")
    def test_images_are_bounded(self, upstream, reserve):
        data={"model":bridge.IMAGE_MODEL,"prompt":"Fictional soup","n":1,"size":"1536x1024","output_format":"jpeg"}
        upstream.return_value=bridge.httpx.Response(200,json={"data":[{"b64_json":"eA=="}]})
        self.assertEqual(self.send(data,"images").status_code,200)
        self.assertEqual(upstream.call_args.kwargs["json"]["quality"],"medium")
        self.assertEqual(self.send({**data,"n":2},"images").status_code,400)

    @patch.object(bridge,"reserve",return_value=1)
    @patch.object(bridge.httpx,"get")
    def test_health_returns_only_access_status(self, upstream, reserve):
        upstream.return_value=bridge.httpx.Response(200,json={"id":bridge.TEXT_MODEL})
        result=self.send({},"health")
        self.assertEqual(result.json,{"configured":True,"modelsAccessible":{"recipes":True,"images":True},"rateLimiter":True})

    def test_pdf_and_inline_image_are_supported(self):
        for item in [{"type":"input_file","filename":"page.pdf","file_data":"data:application/pdf;base64,eA=="},
                     {"type":"input_image","image_url":"data:image/jpeg;base64,eA==","detail":"high"}]:
            data=payload();data["input"][0]["content"].append(item)
            self.assertTrue(bridge.validate(data,"responses"))

    def test_oversized_request_rejected(self):
        result=self.client.post(bridge.BASE+"responses",data=b"x"*4_000_001)
        self.assertEqual(result.status_code,413)


if __name__=="__main__":
    unittest.main()
