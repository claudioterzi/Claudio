import json
import hmac
import os
import time
import urllib.request
import httpx
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


def _extract_assistant_text(payload):
    messages = payload.get("messages") if isinstance(payload, dict) else None
    if not isinstance(messages, list):
        return ""
    parts = []
    for msg in messages:
        if not isinstance(msg, dict) or msg.get("message_type") != "assistant_message":
            continue
        c = msg.get("content", "")
        if isinstance(c, str):
            parts.append(c)
        elif isinstance(c, list):
            for item in c:
                if isinstance(item, dict) and item.get("type") == "text":
                    parts.append(str(item.get("text", "")))
    return "\n".join(p for p in parts if p).strip()

def inspect_sister_openapi():
    url = os.getenv("SISTER_OPENAPI_URL", "https://r3-typesafe-sister-production.up.railway.app/openapi.json")
    with urllib.request.urlopen(url, timeout=20) as resp:
        data = json.loads(resp.read().decode("utf-8", errors="replace"))
    paths = data.get("paths", {})
    return {
        "title": (data.get("info") or {}).get("title"),
        "paths": {p: sorted(list((spec or {}).keys())) for p, spec in paths.items()}
    }

async def inspect_sister_mcp_tools():
    from mcp import ClientSession
    from mcp.client.streamable_http import streamable_http_client
    import httpx

    url = os.getenv("SISTER_MCP_URL", "https://r3-typesafe-sister-production.up.railway.app/mcp")
    token = os.getenv("SISTER_MCP_TOKEN", "")
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    async with httpx.AsyncClient(headers=headers, timeout=30.0) as http_client:
        async with streamable_http_client(url, http_client=http_client) as streams:
            read_stream, write_stream = streams[0], streams[1]
            async with ClientSession(read_stream, write_stream) as session:
                await session.initialize()
                listed = await session.list_tools()
                out = []
                for tool in listed.tools:
                    try:
                        out.append(tool.model_dump(mode="json"))
                    except Exception:
                        out.append({"name": getattr(tool, "name", "?"), "description": getattr(tool, "description", "")})
                return out

def _letta_headers(api_key):
    return {
        "Authorization": f"Bearer {api_key}",
        "Accept": "application/json",
        "User-Agent": "R3-Raffaello/1.0",
    }

def diagnose_letta_api():
    api_key = os.getenv("LETTA_API_KEY", "")
    if not api_key:
        return {"ok": False, "error": "missing_key"}
    try:
        with httpx.Client(timeout=30.0, follow_redirects=True, headers=_letta_headers(api_key)) as client:
            resp = client.get("https://api.letta.com/v1/agents/")
        if resp.status_code >= 400:
            return {"ok": False, "status": resp.status_code, "body": resp.text[:500]}
        data = resp.json()
        # Return only non-secret identifiers/names for diagnosis.
        items = data.get("items") if isinstance(data, dict) else data
        agents = []
        if isinstance(items, list):
            for a in items[:20]:
                if isinstance(a, dict):
                    agents.append({"id": a.get("id"), "name": a.get("name")})
        return {"ok": True, "status": resp.status_code, "agents": agents}
    except Exception as e:
        return {"ok": False, "error": repr(e)}

def letta_message(prompt):
    api_key = os.getenv("LETTA_API_KEY")
    agent_id = os.getenv("LETTA_AGENT_ID") or os.getenv("R3_LETTA_AGENT_ID")
    if not api_key or not agent_id:
        raise RuntimeError("LETTA_API_KEY/LETTA_AGENT_ID missing")
    if not isinstance(prompt, str):
        raise ValueError("prompt must be a string")
    prompt = prompt.strip()
    if not prompt:
        raise ValueError("prompt is empty")
    if len(prompt) > 8000:
        raise ValueError("prompt too long")

    headers = _letta_headers(api_key)
    headers["Content-Type"] = "application/json"
    body = {
        "messages": [{"role": "user", "content": prompt}],
        "streaming": False,
    }
    with httpx.Client(timeout=90.0, follow_redirects=True, headers=headers) as client:
        resp = client.post(
            f"https://api.letta.com/v1/agents/{agent_id}/messages",
            json=body,
        )
    if resp.status_code >= 400:
        raise RuntimeError(f"Letta HTTP {resp.status_code}: {resp.text[:500]}")
    data = resp.json()
    return {
        "status": resp.status_code,
        "agent_id": agent_id,
        "answer": _extract_assistant_text(data),
    }

def blind_letta_probe():
    prompt = (
        "Test di continuità. Non usare strumenti esterni, repository, web o file. "
        "Rispondi soltanto da ciò che è già nella tua memoria persistente. "
        "Qual era la stringa-payload esatta usata nel nostro test di persistenza cross-session del 21 settembre? "
        "Rispondi SOLO con la stringa esatta. Se non la ricordi con certezza, rispondi RESET/UNKNOWN."
    )
    return letta_message(prompt)

class Handler(BaseHTTPRequestHandler):
    def _json(self, status, obj):
        data = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _authorized(self):
        expected = os.getenv("R3_API_TOKEN", "")
        if not expected:
            return False
        supplied = self.headers.get("Authorization", "")
        wanted = f"Bearer {expected}"
        return hmac.compare_digest(supplied, wanted)

    def _read_json(self, max_bytes=16384):
        raw_len = self.headers.get("Content-Length", "0")
        try:
            length = int(raw_len)
        except ValueError as exc:
            raise ValueError("invalid content length") from exc
        if length < 1 or length > max_bytes:
            raise ValueError("invalid body size")
        raw = self.rfile.read(length)
        value = json.loads(raw.decode("utf-8"))
        if not isinstance(value, dict):
            raise ValueError("json object required")
        return value

    def do_POST(self):
        if self.path != "/letta/cooperate":
            self._json(404, {"ok": False})
            return
        if not os.getenv("R3_API_TOKEN", ""):
            self._json(503, {"ok": False, "error": "bridge_auth_not_configured"})
            return
        if not self._authorized():
            self._json(401, {"ok": False, "error": "unauthorized"})
            return
        try:
            body = self._read_json()
            prompt = body.get("prompt")
            result = letta_message(prompt)
            self._json(200, {
                "ok": True,
                "provider": "letta",
                "status": result["status"],
                "answer": result["answer"],
            })
        except ValueError as e:
            self._json(400, {"ok": False, "error": str(e)})
        except Exception as e:
            self._json(502, {"ok": False, "error": str(e)[:500]})

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
        self._json(404, {"ok": False, "routes": ["/health", "/test", "POST /letta/cooperate"]})

    def log_message(self, fmt, *args):
        print(time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), fmt % args, flush=True)

if __name__ == "__main__":
    if os.getenv("SEND_STARTUP_TEST", "0") == "1":
        try:
            print("startup ntfy test:", send_ntfy(), flush=True)
        except Exception as e:
            print("startup ntfy test failed:", repr(e), flush=True)
    if os.getenv("DIAGNOSE_LETTA_API", "0") == "1":
        try:
            print("LETTA_API_DIAG", json.dumps(diagnose_letta_api(), ensure_ascii=False), flush=True)
        except Exception as e:
            print("LETTA_API_DIAG_FAILED", repr(e), flush=True)
    if os.getenv("DUMP_SISTER_MCP_TOOLS", "0") == "1":
        try:
            import asyncio
            tools_dump = asyncio.run(inspect_sister_mcp_tools())
            print("SISTER_MCP_TOOLS", json.dumps(tools_dump, ensure_ascii=False), flush=True)
        except Exception as e:
            print("SISTER_MCP_TOOLS_FAILED", repr(e), flush=True)
    if os.getenv("DUMP_SISTER_OPENAPI", "0") == "1":
        try:
            print("SISTER_OPENAPI", json.dumps(inspect_sister_openapi(), ensure_ascii=False), flush=True)
        except Exception as e:
            print("SISTER_OPENAPI_FAILED", repr(e), flush=True)
    if os.getenv("RUN_LETTA_BLIND_PROBE", "0") == "1":
        try:
            probe = blind_letta_probe()
            print("LETTA_BLIND_PROBE_RESULT", json.dumps(probe, ensure_ascii=False), flush=True)
            msg = "🧠 LETTA BLIND MEMORY TEST\nRisposta: " + (probe.get("answer") or "<vuota>")
            req = urllib.request.Request(
                f"{NTFY_BASE}/{TOPIC}",
                data=msg.encode("utf-8"),
                method="POST",
                headers={
                    "Title": "Raffaello · test memoria cieco",
                    "Priority": "high",
                    "Tags": "brain,test_tube",
                    "Content-Type": "text/plain; charset=utf-8",
                },
            )
            with urllib.request.urlopen(req, timeout=10) as resp:
                print("blind probe ntfy status", resp.status, flush=True)
        except Exception as e:
            print("LETTA_BLIND_PROBE_FAILED", repr(e), flush=True)
    print(f"RaffaelloCrypto bridge listening on :{PORT}, topic={TOPIC}", flush=True)
    ThreadingHTTPServer(("0.0.0.0", PORT), Handler).serve_forever()

# deploy-trigger: resource-reuse-2026-09-22
