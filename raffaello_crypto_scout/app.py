import json
import os
import time
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

TOPIC = os.getenv("NTFY_TOPIC", "raffaellocrypto")
NTFY_BASE = os.getenv("NTFY_BASE", "https://ntfy.sh").rstrip("/")
PORT = int(os.getenv("PORT", "8080"))

def send_ntfy():
    body = "✅ TEST RAFFAELLO CRYPTO\nCanale operativo collegato. Se leggi questo messaggio, il ponte Railway → ntfy → iPhone funziona."
    req = urllib.request.Request(
        f"{NTFY_BASE}/{TOPIC}",
        data=body.encode("utf-8"),
        method="POST",
        headers={
            "Title": "RaffaelloCrypto · TEST",
            "Priority": "high",
            "Tags": "white_check_mark,chart_with_upwards_trend",
            "Content-Type": "text/plain; charset=utf-8",
        },
    )
    with urllib.request.urlopen(req, timeout=10) as resp:
        payload = resp.read().decode("utf-8", errors="replace")
        return {"status": resp.status, "body": payload}

class Handler(BaseHTTPRequestHandler):
    def _json(self, status, obj):
        data = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        if self.path == "/health":
            self._json(200, {"ok": True, "service": "raffaello-crypto-scout", "topic": TOPIC})
            return
        if self.path == "/test":
            try:
                result = send_ntfy()
                self._json(200, {"ok": True, "sent": True, "ntfy": result})
            except Exception as e:
                self._json(502, {"ok": False, "sent": False, "error": repr(e)})
            return
        self._json(404, {"ok": False, "routes": ["/health", "/test"]})

    def log_message(self, fmt, *args):
        print(time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), fmt % args, flush=True)

if __name__ == "__main__":
    if os.getenv("SEND_STARTUP_TEST", "0") == "1":
        try:
            print("startup ntfy test:", send_ntfy(), flush=True)
        except Exception as e:
            print("startup ntfy test failed:", repr(e), flush=True)
    print(f"RaffaelloCrypto bridge listening on :{PORT}, topic={TOPIC}", flush=True)
    ThreadingHTTPServer(("0.0.0.0", PORT), Handler).serve_forever()

# deploy-trigger: resource-reuse-2026-09-22
