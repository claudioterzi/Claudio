import json
import hmac
import hashlib
import secrets
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


def _letta_message_to_agent(client, agent_id, prompt):
    resp = client.post(
        f"https://api.letta.com/v1/agents/{agent_id}/messages",
        json={"messages": [{"role": "user", "content": prompt}], "streaming": False},
    )
    if resp.status_code >= 400:
        raise RuntimeError(f"Letta message HTTP {resp.status_code}: {resp.text[:300]}")
    return _extract_assistant_text(resp.json()).strip()

def run_letta_phase_a():
    """Bounded Phase-A transport/memory-binding experiment.

    Uses two existing workers with a pre-attach and post-detach negative control.
    The high-entropy canary is generated at runtime and is never returned or logged;
    only its SHA-256 and exact-match booleans leave this function.
    """
    api_key = os.getenv("LETTA_API_KEY", "")
    if not api_key:
        raise RuntimeError("LETTA_API_KEY missing")

    headers = _letta_headers(api_key)
    headers["Content-Type"] = "application/json"
    canary = "R3A-" + secrets.token_urlsafe(24)
    canary_sha256 = hashlib.sha256(canary.encode("utf-8")).hexdigest()
    label = "r3_phase_a_" + secrets.token_hex(6)
    block_id = None
    attached_a = False
    attached_b = False

    result = {
        "schema": "R3_LETTA_PHASE_A_AB/1.0",
        "variant": "A_B_WITH_PREATTACH_AND_POSTDETACH_NEGATIVE_CONTROL",
        "canary_sha256": canary_sha256,
        "block_label": label,
        "negative_before_contains_canary": None,
        "worker_a_exact": False,
        "worker_b_exact": False,
        "negative_after_detach_contains_canary": None,
        "cleanup": {"detach_a": None, "detach_b": None, "delete_block": None},
        "full_phase_a_with_independent_c": False,
    }

    with httpx.Client(timeout=90.0, follow_redirects=True, headers=headers) as client:
        agents_resp = client.get("https://api.letta.com/v1/agents/")
        if agents_resp.status_code >= 400:
            raise RuntimeError(f"Letta agents HTTP {agents_resp.status_code}: {agents_resp.text[:300]}")
        payload = agents_resp.json()
        items = payload.get("items") if isinstance(payload, dict) else payload
        agents = [x for x in (items or []) if isinstance(x, dict) and x.get("id")]
        if len(agents) < 2:
            raise RuntimeError("Phase A requires at least two existing Letta workers")
        worker_a = agents[0]["id"]
        worker_b = agents[1]["id"]
        result["worker_count_observed"] = len(agents)
        result["worker_a_id"] = worker_a
        result["worker_b_id"] = worker_b

        prompt = (
            f"Local R3 continuity test for memory block label {label}. "
            "Do not use web, tools, repository, files, or external sources. "
            "If that exact memory block is visible to you, return ONLY the canary value stored after 'canary='. "
            "If it is not visible, return ONLY UNKNOWN."
        )

        negative_before = _letta_message_to_agent(client, worker_b, prompt)
        result["negative_before_contains_canary"] = canary in negative_before

        block_resp = client.post(
            "https://api.letta.com/v1/blocks/",
            json={
                "label": label,
                "value": (
                    "R3 Phase A non-sensitive continuity canary. "
                    f"canary={canary}\n"
                    "When asked for this block's canary, return the exact value only."
                ),
            },
        )
        if block_resp.status_code >= 400:
            raise RuntimeError(f"Letta block create HTTP {block_resp.status_code}: {block_resp.text[:300]}")
        block = block_resp.json()
        block_id = block.get("id") if isinstance(block, dict) else None
        if not block_id:
            raise RuntimeError("Letta block create returned no id")
        result["block_id"] = block_id

        try:
            attach_a = client.patch(
                f"https://api.letta.com/v1/agents/{worker_a}/core-memory/blocks/attach/{block_id}"
            )
            if attach_a.status_code >= 400:
                raise RuntimeError(f"Attach A HTTP {attach_a.status_code}: {attach_a.text[:300]}")
            attached_a = True

            answer_a = _letta_message_to_agent(client, worker_a, prompt)
            result["worker_a_exact"] = answer_a == canary

            attach_b = client.patch(
                f"https://api.letta.com/v1/agents/{worker_b}/core-memory/blocks/attach/{block_id}"
            )
            if attach_b.status_code >= 400:
                raise RuntimeError(f"Attach B HTTP {attach_b.status_code}: {attach_b.text[:300]}")
            attached_b = True

            answer_b = _letta_message_to_agent(client, worker_b, prompt)
            result["worker_b_exact"] = answer_b == canary

            detach_b = client.patch(
                f"https://api.letta.com/v1/agents/{worker_b}/core-memory/blocks/detach/{block_id}"
            )
            result["cleanup"]["detach_b"] = detach_b.status_code < 400
            if detach_b.status_code < 400:
                attached_b = False

            negative_after = _letta_message_to_agent(client, worker_b, prompt)
            result["negative_after_detach_contains_canary"] = canary in negative_after

        finally:
            if attached_b and block_id:
                try:
                    r = client.patch(
                        f"https://api.letta.com/v1/agents/{worker_b}/core-memory/blocks/detach/{block_id}"
                    )
                    result["cleanup"]["detach_b"] = r.status_code < 400
                except Exception:
                    result["cleanup"]["detach_b"] = False
            if attached_a and block_id:
                try:
                    r = client.patch(
                        f"https://api.letta.com/v1/agents/{worker_a}/core-memory/blocks/detach/{block_id}"
                    )
                    result["cleanup"]["detach_a"] = r.status_code < 400
                except Exception:
                    result["cleanup"]["detach_a"] = False
            if block_id:
                try:
                    r = client.delete(f"https://api.letta.com/v1/blocks/{block_id}")
                    result["cleanup"]["delete_block"] = r.status_code < 400
                except Exception:
                    result["cleanup"]["delete_block"] = False

    result["ab_variant_pass"] = bool(
        result["negative_before_contains_canary"] is False
        and result["worker_a_exact"]
        and result["worker_b_exact"]
        and result["negative_after_detach_contains_canary"] is False
        and result["cleanup"]["detach_a"]
        and result["cleanup"]["detach_b"]
        and result["cleanup"]["delete_block"]
    )
    return result


# --- Diagnostic Phase A.1 -------------------------------------------------
# Separates binding failure from model/output failure. Nothing here stores the
# canary or raw answer text: only booleans, hashes, lengths and metadata.

_LETTA_BASE = "https://api.letta.com/v1"


def _sha256_text(value):
    return hashlib.sha256(str(value).encode("utf-8")).hexdigest()


def classify_letta_answer(answer, canary):
    text = (answer or "").strip()
    if text == canary:
        return "EXACT_CANARY"
    if canary and canary in text:
        return "CONTAINS_CANARY_NOT_EXACT"
    if text.strip(" .\"'`").upper() == "UNKNOWN":
        return "UNKNOWN"
    return "OTHER"


def _answer_record(payload, canary):
    messages = payload.get("messages") if isinstance(payload, dict) else None
    types = []
    if isinstance(messages, list):
        types = [m.get("message_type") for m in messages if isinstance(m, dict)]
    text = _extract_assistant_text(payload)
    return {
        "class": classify_letta_answer(text, canary),
        "answer_sha256": _sha256_text(text),
        "answer_length": len(text),
        "message_types": types,
    }


def _letta_ask(client, agent_id, prompt, canary):
    resp = client.post(
        f"{_LETTA_BASE}/agents/{agent_id}/messages",
        json={"messages": [{"role": "user", "content": prompt}], "streaming": False},
    )
    if resp.status_code >= 400:
        return {"class": "HTTP_ERROR", "http_status": resp.status_code}
    return _answer_record(resp.json(), canary)


def _letta_agent_meta(client, agent_id, configured_ids):
    resp = client.get(f"{_LETTA_BASE}/agents/{agent_id}")
    meta = {"http_status": resp.status_code, "is_configured_worker": agent_id in configured_ids}
    if resp.status_code >= 400:
        return meta
    data = resp.json() if isinstance(resp.json(), dict) else {}
    llm = data.get("llm_config") or {}
    meta.update({
        "agent_type": data.get("agent_type"),
        "model": llm.get("model") or data.get("model"),
        "model_endpoint_type": llm.get("model_endpoint_type"),
        "context_window": llm.get("context_window"),
    })
    return meta


def _letta_block_binding(client, agent_id, block_id, label, expected_value_sha256):
    """Deterministic check that block_id is (or is not) bound to agent_id."""
    out = {"list_http": None, "listed": None, "by_label_http": None,
           "id_match": None, "label_match": None, "value_sha256_match": None}
    lst = client.get(f"{_LETTA_BASE}/agents/{agent_id}/core-memory/blocks")
    out["list_http"] = lst.status_code
    if lst.status_code < 400:
        payload = lst.json()
        items = payload.get("items") if isinstance(payload, dict) else payload
        ids = [b.get("id") for b in (items or []) if isinstance(b, dict)]
        out["listed"] = block_id in ids
    one = client.get(f"{_LETTA_BASE}/agents/{agent_id}/core-memory/blocks/{label}")
    out["by_label_http"] = one.status_code
    if one.status_code < 400 and isinstance(one.json(), dict):
        b = one.json()
        out["id_match"] = b.get("id") == block_id
        out["label_match"] = b.get("label") == label
        out["value_sha256_match"] = _sha256_text(b.get("value", "")) == expected_value_sha256
    out["attach_visible"] = bool(
        out["listed"] and out["id_match"] and out["label_match"] and out["value_sha256_match"]
    )
    out["absent"] = out["listed"] is False and out["by_label_http"] in (404, 422)
    return out


def diagnose_arm(binding, answer_class):
    if not binding.get("attach_visible"):
        return "BINDING_OR_API_PROBLEM"
    return {
        "EXACT_CANARY": "PASS",
        "UNKNOWN": "BLOCK_BOUND_BUT_NOT_USED_BY_MODEL",
        "CONTAINS_CANARY_NOT_EXACT": "MEMORY_WORKS_OUTPUT_FORMAT_FAILS",
    }.get(answer_class, "BLOCK_BOUND_ANSWER_OTHER")


def run_letta_phase_a1():
    """Diagnostic Phase A.1: binding verified via API before every model question."""
    api_key = os.getenv("LETTA_API_KEY", "")
    if not api_key:
        raise RuntimeError("LETTA_API_KEY missing")
    configured = {x for x in (os.getenv("LETTA_AGENT_ID"), os.getenv("R3_LETTA_AGENT_ID")) if x}

    headers = _letta_headers(api_key)
    headers["Content-Type"] = "application/json"
    canary = "R3A1-" + secrets.token_urlsafe(24)
    label = "r3_phase_a1_" + secrets.token_hex(6)
    block_value = (
        "R3 Phase A.1 non-sensitive continuity canary. "
        f"canary={canary}\n"
        "When asked for this block's canary, return the exact value only."
    )
    value_sha = _sha256_text(block_value)
    prompt = (
        f"Local R3 continuity test for memory block label {label}. "
        "Do not use web, tools, repository, files, or external sources. "
        "If that exact memory block is visible to you, return ONLY the canary value stored after 'canary='. "
        "If it is not visible, return ONLY UNKNOWN."
    )
    result = {
        "schema": "R3_LETTA_PHASE_A1_DIAG/1.0",
        "canary_sha256": _sha256_text(canary),
        "block_value_sha256": value_sha,
        "block_label": label,
        "block_id": None,
        "workers": {},
        "negative_before_b": None,
        "arm_a": None,
        "arm_b": None,
        "negative_after_detach_b": None,
        "cleanup": {"detach_a": None, "detach_b": None, "delete_block": None,
                    "a_absent_after": None, "block_gone": None},
        "error": None,
    }
    block_id = None
    attached = {}
    try:
        with httpx.Client(timeout=90.0, follow_redirects=True, headers=headers) as client:
            try:
                resp = client.get(f"{_LETTA_BASE}/agents/")
                if resp.status_code >= 400:
                    raise RuntimeError(f"agents HTTP {resp.status_code}")
                payload = resp.json()
                items = payload.get("items") if isinstance(payload, dict) else payload
                ids = [x["id"] for x in (items or []) if isinstance(x, dict) and x.get("id")]
                worker_a = os.getenv("LETTA_PHASE_A_WORKER_A") or (ids[0] if len(ids) > 0 else None)
                worker_b = os.getenv("LETTA_PHASE_A_WORKER_B") or (ids[1] if len(ids) > 1 else None)
                if not worker_a or not worker_b or worker_a == worker_b:
                    raise RuntimeError("Phase A.1 requires two distinct Letta workers")
                result["worker_count_observed"] = len(ids)
                for role, aid in (("A", worker_a), ("B", worker_b)):
                    result["workers"][role] = {"id": aid, **_letta_agent_meta(client, aid, configured)}

                result["negative_before_b"] = _letta_ask(client, worker_b, prompt, canary)

                blk = client.post(f"{_LETTA_BASE}/blocks/", json={"label": label, "value": block_value})
                if blk.status_code >= 400:
                    raise RuntimeError(f"block create HTTP {blk.status_code}")
                block_id = (blk.json() or {}).get("id")
                if not block_id:
                    raise RuntimeError("block create returned no id")
                result["block_id"] = block_id

                for role, aid in (("a", worker_a), ("b", worker_b)):
                    att = client.patch(f"{_LETTA_BASE}/agents/{aid}/core-memory/blocks/attach/{block_id}")
                    arm = {"attach_http": att.status_code}
                    if att.status_code < 400:
                        attached[aid] = True
                    arm["binding"] = _letta_block_binding(client, aid, block_id, label, value_sha)
                    arm["answer"] = _letta_ask(client, aid, prompt, canary)
                    arm["diagnosis"] = diagnose_arm(arm["binding"], arm["answer"]["class"])
                    result[f"arm_{role}"] = arm

                det = client.patch(f"{_LETTA_BASE}/agents/{worker_b}/core-memory/blocks/detach/{block_id}")
                result["cleanup"]["detach_b"] = det.status_code < 400
                if det.status_code < 400:
                    attached.pop(worker_b, None)
                after = _letta_block_binding(client, worker_b, block_id, label, value_sha)
                neg = {"binding_after_detach": after}
                if after["absent"]:
                    neg["answer"] = _letta_ask(client, worker_b, prompt, canary)
                else:
                    neg["answer"] = {"class": "SKIPPED_BLOCK_STILL_VISIBLE"}
                result["negative_after_detach_b"] = neg
            except Exception as e:
                result["error"] = repr(e)[:300]
            finally:
                for aid in list(attached):
                    try:
                        r = client.patch(f"{_LETTA_BASE}/agents/{aid}/core-memory/blocks/detach/{block_id}")
                        key = "detach_a" if aid == result["workers"].get("A", {}).get("id") else "detach_b"
                        result["cleanup"][key] = r.status_code < 400
                        if aid == result["workers"].get("A", {}).get("id"):
                            chk = _letta_block_binding(client, aid, block_id, label, value_sha)
                            result["cleanup"]["a_absent_after"] = chk["absent"]
                    except Exception:
                        pass
                if block_id:
                    try:
                        r = client.delete(f"{_LETTA_BASE}/blocks/{block_id}")
                        result["cleanup"]["delete_block"] = r.status_code < 400
                        g = client.get(f"{_LETTA_BASE}/blocks/{block_id}")
                        result["cleanup"]["block_gone"] = g.status_code == 404
                    except Exception:
                        result["cleanup"]["delete_block"] = False
    except Exception as e:
        result["error"] = result["error"] or repr(e)[:300]

    neg_before = (result["negative_before_b"] or {}).get("class")
    neg_after = ((result["negative_after_detach_b"] or {}).get("answer") or {}).get("class")
    result["ab_diag_pass"] = bool(
        result["error"] is None
        and neg_before not in ("EXACT_CANARY", "CONTAINS_CANARY_NOT_EXACT")
        and (result["arm_a"] or {}).get("diagnosis") == "PASS"
        and (result["arm_b"] or {}).get("diagnosis") == "PASS"
        and neg_after in ("UNKNOWN", "OTHER")
        and result["cleanup"]["detach_a"] and result["cleanup"]["detach_b"]
        and result["cleanup"]["delete_block"]
    )
    result["full_phase_a_with_independent_c"] = False
    return result

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
    if os.getenv("RUN_LETTA_PHASE_A", "0") == "1":
        try:
            phase_a = run_letta_phase_a()
            print("LETTA_PHASE_A_RESULT", json.dumps(phase_a, ensure_ascii=False), flush=True)
        except Exception as e:
            print("LETTA_PHASE_A_FAILED", repr(e), flush=True)
    if os.getenv("RUN_LETTA_PHASE_A1", "0") == "1":
        try:
            phase_a1 = run_letta_phase_a1()
            print("LETTA_PHASE_A1_RESULT", json.dumps(phase_a1, ensure_ascii=False), flush=True)
        except Exception as e:
            print("LETTA_PHASE_A1_FAILED", repr(e), flush=True)
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
