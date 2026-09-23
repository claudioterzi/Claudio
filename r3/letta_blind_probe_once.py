import json
import os
import urllib.error
import urllib.request

NEW_AGENT = "agent-e359c0b3-fbee-4a99-bf7a-d0441cf2f05e"
PROMPT = (
    "Test di continuita cieco. Senza usare strumenti esterni, file, repository, web "
    "o informazioni fornite in questo messaggio, restituisci SOLO la stringa esatta "
    "che era stata salvata nel test LETTA-PERSIST-001 del 21/09/2026. "
    "Se non la ricordi esattamente, rispondi UNKNOWN."
)

def request_json(url, key, method="GET", body=None):
    data = None if body is None else json.dumps(body).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        method=method,
        headers={
            "Authorization": f"Bearer {key}",
            "Accept": "application/json",
            "Content-Type": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=45) as resp:
            return resp.status, json.loads(resp.read().decode("utf-8", "replace"))
    except urllib.error.HTTPError as exc:
        return exc.code, {"error": exc.read().decode("utf-8", "replace")[:1000]}
    except Exception as exc:
        return 0, {"error": repr(exc)}

def collect_agent_ids(value, out):
    if isinstance(value, dict):
        ident = value.get("id")
        if isinstance(ident, str) and ident.startswith("agent-"):
            out.add(ident)
        for child in value.values():
            collect_agent_ids(child, out)
    elif isinstance(value, list):
        for child in value:
            collect_agent_ids(child, out)

def assistant_text(value):
    parts = []
    if isinstance(value, dict):
        for msg in value.get("messages", []) or []:
            if not isinstance(msg, dict) or msg.get("message_type") != "assistant_message":
                continue
            content = msg.get("content", "")
            if isinstance(content, str):
                parts.append(content)
            elif isinstance(content, list):
                for item in content:
                    if isinstance(item, dict) and item.get("type") == "text":
                        parts.append(str(item.get("text", "")))
    return "\n".join(parts).strip()

def main():
    key = os.getenv("LETTA_API_KEY", "")
    env_agent = os.getenv("R3_LETTA_AGENT_ID", "")
    if not key:
        print("LETTA_BLIND_DIAG", json.dumps({"status": 0, "error": "LETTA_API_KEY missing"}), flush=True)
        return

    status, data = request_json("https://api.letta.com/v1/agents/?limit=100", key)
    ids = set()
    collect_agent_ids(data, ids)
    print(
        "LETTA_BLIND_LIST",
        json.dumps(
            {"status": status, "ids": sorted(ids), "env_agent": env_agent},
            ensure_ascii=False,
        ),
        flush=True,
    )

    candidates = []
    for agent_id in (env_agent, NEW_AGENT):
        if agent_id and agent_id not in candidates:
            candidates.append(agent_id)

    for agent_id in candidates:
        st, result = request_json(
            f"https://api.letta.com/v1/agents/{agent_id}/messages",
            key,
            method="POST",
            body={
                "messages": [{"role": "user", "content": PROMPT}],
                "streaming": False,
            },
        )
        print(
            "LETTA_BLIND_RESULT",
            json.dumps(
                {
                    "agent_id": agent_id,
                    "status": st,
                    "answer": assistant_text(result),
                    "error": result.get("error") if isinstance(result, dict) else None,
                },
                ensure_ascii=False,
            ),
            flush=True,
        )

if __name__ == "__main__":
    main()
