import json
import os
import httpx

OLD_AGENT = "agent-34c4c128-350c-4901-b0ce-d1df15c16f40"
NEW_AGENT = "agent-e359c0b3-fbee-4a99-bf7a-d0441cf2f05e"
NEEDLES = ["R3-LETTA-260921-0739-ALFA7", "LETTA-PERSIST-001"]

def get_json(client, url):
    try:
        r = client.get(url)
        try:
            data = r.json()
        except Exception:
            data = {"_raw": r.text[:1000]}
        return r.status_code, data
    except Exception as exc:
        return 0, {"error": repr(exc)}

def stringify(value):
    try:
        return json.dumps(value, ensure_ascii=False, sort_keys=True)
    except Exception:
        return repr(value)

def block_summary(data):
    items = data if isinstance(data, list) else data.get("items", []) if isinstance(data, dict) else []
    out = []
    for b in items:
        if isinstance(b, dict):
            out.append({"id": b.get("id"), "label": b.get("label")})
    return out

def inspect_agent(client, agent_id):
    core_status, core = get_json(
        client,
        f"https://api.letta.com/v1/agents/{agent_id}/core-memory/blocks?limit=200"
    )
    arch_status, arch = get_json(
        client,
        f"https://api.letta.com/v1/agents/{agent_id}/archival-memory?limit=200"
    )
    core_text = stringify(core)
    arch_text = stringify(arch)
    return {
        "agent_id": agent_id,
        "core_status": core_status,
        "archival_status": arch_status,
        "core_blocks": block_summary(core),
        "found": {
            needle: {
                "core": needle in core_text,
                "archival": needle in arch_text,
                "any": (needle in core_text) or (needle in arch_text),
            }
            for needle in NEEDLES
        },
    }

def main():
    key = os.getenv("LETTA_API_KEY", "")
    if not key:
        print("LETTA_MEMORY_COMPARE", json.dumps({"error": "LETTA_API_KEY missing"}), flush=True)
        return
    headers = {
        "Authorization": f"Bearer {key}",
        "Accept": "application/json",
        "User-Agent": "letta-client-python/1.0",
    }
    with httpx.Client(headers=headers, timeout=45.0, follow_redirects=False) as client:
        old = inspect_agent(client, OLD_AGENT)
        new = inspect_agent(client, NEW_AGENT)
    old_ids = {x.get("id") for x in old["core_blocks"] if x.get("id")}
    new_ids = {x.get("id") for x in new["core_blocks"] if x.get("id")}
    result = {
        "test": "LETTA-PERSIST-001 blind persisted-state comparison",
        "old": old,
        "new": new,
        "shared_core_block_ids": sorted(old_ids & new_ids),
        "shared_core_block_count": len(old_ids & new_ids),
    }
    print("LETTA_MEMORY_COMPARE", json.dumps(result, ensure_ascii=False), flush=True)

if __name__ == "__main__":
    main()
