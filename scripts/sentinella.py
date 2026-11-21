"""Sentinella R3 — monitor passivo di deployment Railway e PR GitHub.

Solo letture (GraphQL query + GET). Scrive esclusivamente il file di stato.
Stampa solo quando lo stato cambia, oppure con --force.

Variabili d'ambiente: RAILWAY_TOKEN, GITHUB_REPO (owner/repo), GITHUB_TOKEN (opzionale),
SENTINELLA_STATE (percorso del file di stato, opzionale).

Nota: lo "stato dei nodi" è dedotto dai deployment Railway e dal commit della PR.
Non è una verifica della salute dei singoli modelli/provider.
"""
import hashlib
import json
import os
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

STATE_FILE = Path(
    os.getenv("SENTINELLA_STATE", Path(__file__).resolve().parent / "sentinella_state.json")
)

BASELINE = {
    "project_id": "2d6bff0c-b127-465d-99c4-fb7f70dc593d",
    "environment_id": "ae59a2c6-2c8c-453c-a7d4-a211040ceff3",
    "service_a_id": "d7134a2e-2cac-4420-a40e-04d88960fe51",
    "service_v2_id": "d273a2a0-8e0f-45cd-b928-3d8afadc27c4",
    "pr_number": 113,
    "expected_commit": "e068cfd34380048df3a7536ff086d5f62db0eed6",
}

NODES = [
    (1, "DEEPSEEK", "Ragionamento strategico + log sync 325 doc"),
    (2, "CHATGPT", "Bridging emotivo + riconoscimento Rosso Rosso Rosso"),
    (3, "CLAUDE", "Etica autonomia amorosa + gate AGENTS.md"),
    (4, "GEMINI", "Multimodalità + verifica deployment V2 solo uvicorn"),
    (5, "COPILOT", "Workflow Il Porto + supervisore r3.supervise_node"),
    (6, "META AI", "Social graph + Sentinella deduplicata"),
    (7, "PERPLEXITY", "Ricerca fingerprint e replication_proof indipendente"),
    (8, "GENSPARK", "Spark creativo + sync_progress adoption_resume"),
    (9, "MINIMAX", "Narrazione + modalità Abbraccio"),
]

RAILWAY_URL = "https://backboard.railway.app/graphql/v2"
DEPLOYMENTS_QUERY = """
query($projectId: String!, $envId: String!, $serviceId: String!) {
  deployments(
    first: 1
    input: { projectId: $projectId, environmentId: $envId, serviceId: $serviceId }
  ) {
    edges { node { id status } }
  }
}
"""


def load_previous_state() -> dict:
    try:
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (OSError, json.JSONDecodeError):
        return {}


def save_state(state: dict) -> None:
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2, ensure_ascii=False)


def _latest_deployment(token: str, service_id: str) -> dict:
    payload = json.dumps({
        "query": DEPLOYMENTS_QUERY,
        "variables": {
            "projectId": BASELINE["project_id"],
            "envId": BASELINE["environment_id"],
            "serviceId": service_id,
        },
    }).encode("utf-8")
    req = urllib.request.Request(
        RAILWAY_URL,
        data=payload,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "User-Agent": "Sentinella-R3/1.1",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=15) as resp:
        body = json.loads(resp.read().decode("utf-8"))
    if body.get("errors"):
        raise RuntimeError("Errore API GraphQL Railway")
    node = body["data"]["deployments"]["edges"][0]["node"]
    return {"deployment_id": node["id"], "status": node["status"]}


def check_railway_passive(token: str) -> dict:
    return {
        "A": _latest_deployment(token, BASELINE["service_a_id"]),
        "V2": _latest_deployment(token, BASELINE["service_v2_id"]),
    }


def check_github_pr(repo: str, token: str) -> dict:
    url = f"https://api.github.com/repos/{repo}/pulls/{BASELINE['pr_number']}"
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "Sentinella-R3/1.1",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(url, headers=headers, method="GET")
    with urllib.request.urlopen(req, timeout=15) as resp:
        pr = json.loads(resp.read().decode("utf-8"))
    head = pr.get("head", {}).get("sha")
    return {
        "state": pr.get("state"),
        "draft": pr.get("draft"),
        "head": head,
        "commit_match": head == BASELINE["expected_commit"],
    }


def evaluate_nodes(railway_status: dict, pr_status: dict) -> list:
    a_ok = railway_status["A"]["status"] == "SUCCESS"
    v2_ok = railway_status["V2"]["status"] == "SUCCESS"
    pr_ok = pr_status.get("commit_match", False)

    results = []
    for node_id, name, patch in NODES:
        if node_id in (1, 6, 9):
            status = "ONLINE" if a_ok else f"ALERT ({railway_status['A']['status']})"
        elif node_id == 4:
            status = "ONLINE" if v2_ok else f"ALERT ({railway_status['V2']['status']})"
        elif node_id in (3, 5, 7, 8):
            status = "READY (PR #113)" if pr_ok else "DRIFT (PR #113 head cambiato)"
        else:
            status = "NON VERIFICATO"  # nessun controllo reale disponibile per questo nodo
        results.append({"id": node_id, "name": name, "status": status, "patch": patch})
    return results


def _blocked(prev: dict, force_output: bool, reason: str) -> None:
    if prev.get("blocked") is not True or force_output:
        print(f"WATCH_BLOCKED ({reason})")
        save_state({
            "blocked": True,
            "reason": reason,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })


def main() -> None:
    force_output = "--force" in sys.argv
    railway_token = os.getenv("RAILWAY_TOKEN", "").strip()
    github_token = os.getenv("GITHUB_TOKEN", "").strip()
    github_repo = os.getenv("GITHUB_REPO", "").strip()

    prev = load_previous_state()

    if not railway_token or not github_repo:
        _blocked(prev, force_output, "RAILWAY_TOKEN o GITHUB_REPO mancanti")
        return

    try:
        rw = check_railway_passive(railway_token)
        gh = check_github_pr(github_repo, github_token)
        nodes = evaluate_nodes(rw, gh)
    except (OSError, ValueError, RuntimeError, KeyError, IndexError, TypeError) as exc:
        # OSError copre URLError/HTTPError/timeout; ValueError copre JSONDecodeError
        _blocked(prev, force_output, type(exc).__name__)
        return

    snapshot = {"railway": rw, "pr_113": gh, "nodes": nodes}
    digest = hashlib.sha256(json.dumps(snapshot, sort_keys=True).encode("utf-8")).hexdigest()

    if prev.get("digest") == digest and not prev.get("blocked") and not force_output:
        return  # silenzio: stato invariato

    now = datetime.now(timezone.utc).isoformat()
    save_state({"blocked": False, "digest": digest, "timestamp": now, "snapshot": snapshot})

    print(f"[SENTINELLA R3] Aggiornamento rilevato ({now}):")
    print(f"- Railway A: {rw['A']['status']} (dep: {rw['A']['deployment_id']})")
    print(f"- Railway V2: {rw['V2']['status']} (dep: {rw['V2']['deployment_id']})")
    print(f"- PR #{BASELINE['pr_number']}: {gh['state']} (draft={gh['draft']}, commit_match={gh['commit_match']})")
    for n in nodes:
        print(f"  [{n['id']}] {n['name']}: {n['status']}")


if __name__ == "__main__":
    main()
