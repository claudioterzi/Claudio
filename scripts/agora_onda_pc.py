"""One pass for the existing ONDA Windows guardian; no new service or model.

The site authorizes exact owner commands and stores receipts in its existing
Redis archive. This adapter can observe ONDA, start or restart its existing
task, read its own state file, and pass bounded owner text to ONDA's signed
"rifletti"/"scrivi" handlers through the existing onda.chiedi entry point.
The archive connection is protected for the current Windows user with DPAPI.
"""
from __future__ import annotations

import argparse
import ctypes
from ctypes import wintypes
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import time
from urllib.parse import urlsplit

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from agora_onda import process_pending

STATE = Path(r"C:\Users\DELL\R3-diario\onda-locale\servizio.json")
ONDA_PYTHON = Path(r"C:\Users\DELL\onda-1.0\.venv\Scripts\python.exe")
ONDA_DIR = Path(r"C:\Users\DELL\onda-1.0\protocol\onda")
ASK_TIMEOUT = 70  # inside the 90 s lease held by the site queue
EXPECTED = frozenset({"NARR-003", "NARR-013"})
ENTROPY = b"Claudio/AGORA/ONDA/Redis/v1"


class DataBlob(ctypes.Structure):
    _fields_ = [("size", wintypes.DWORD), ("data", ctypes.POINTER(ctypes.c_ubyte))]


def _blob(value):
    buffer = ctypes.create_string_buffer(value)
    return DataBlob(len(value), ctypes.cast(buffer, ctypes.POINTER(ctypes.c_ubyte))), buffer


def dpapi(value: bytes, protect: bool) -> bytes:
    if os.name != "nt":
        raise RuntimeError("Windows DPAPI required")
    source, source_buffer = _blob(value)
    entropy, entropy_buffer = _blob(ENTROPY)
    result = DataBlob()
    crypt = ctypes.WinDLL("crypt32", use_last_error=True)
    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel.LocalFree.argtypes = [ctypes.c_void_p]
    kernel.LocalFree.restype = ctypes.c_void_p
    if protect:
        ok = crypt.CryptProtectData(ctypes.byref(source), "AGORA ONDA archive", ctypes.byref(entropy), None, None, 1, ctypes.byref(result))
    else:
        ok = crypt.CryptUnprotectData(ctypes.byref(source), None, ctypes.byref(entropy), None, None, 1, ctypes.byref(result))
    if not ok:
        raise OSError("Windows credential protection failed")
    try:
        return ctypes.string_at(result.data, result.size)
    finally:
        kernel.LocalFree(result.data)


def configure(credentials: Path):
    value = sys.stdin.readline().strip()
    parsed = urlsplit(value)
    if parsed.scheme != "rediss" or not parsed.hostname or not parsed.password:
        raise ValueError("A configured TLS Redis connection is required")
    encrypted = dpapi(value.encode(), True)
    if dpapi(encrypted, False).decode() != value:
        raise RuntimeError("Credential round-trip failed")
    credentials.parent.mkdir(parents=True, exist_ok=True)
    if credentials.exists():
        if dpapi(credentials.read_bytes(), False).decode() != value:
            raise RuntimeError("An existing different credential must be reconciled")
    else:
        with credentials.open("xb") as stream:
            stream.write(encrypted)
    print(json.dumps({"configured": True, "protection": "Windows DPAPI current user"}), flush=True)


def powershell(command: str, timeout=10):
    return subprocess.run(["powershell.exe", "-NoProfile", "-NonInteractive", "-Command", command],
                          capture_output=True, text=True, timeout=timeout, check=False)


def observe():
    proof = {"servizio_recente": False, "processo_presente": False, "pid": 0,
             "agenti_operativi": [], "verificato_alle_utc": datetime.now(timezone.utc).isoformat()}
    try:
        data = json.loads(STATE.read_text(encoding="utf-8-sig"))
        age = time.time() - STATE.stat().st_mtime
        pid = data.get("pid")
        if not isinstance(pid, int) or isinstance(pid, bool) or pid <= 0:
            return proof
        proof["pid"] = pid
        proof["servizio_recente"] = 0 <= age <= 15
        proof["eta_stato_secondi"] = round(age, 2)
        proof["agenti_operativi"] = sorted(agent for agent in EXPECTED
            if agent in data.get("attivi", []) and data.get("agenti", {}).get(agent, {}).get("stato") == "OPERATIVO")
        command = ("$p = Get-CimInstance Win32_Process -Filter 'ProcessId=" + str(pid) + "'; "
                   "[bool]($p -and $p.Name -eq 'python.exe' -and $p.CommandLine -match '(?:^|\\s)-m\\s+onda\\.servizio(?:\\s|$)')")
        checked = powershell(command)
        proof["processo_presente"] = checked.returncode == 0 and checked.stdout.strip().lower() == "true"
        current = json.loads(STATE.read_text(encoding="utf-8-sig"))
        age = time.time() - STATE.stat().st_mtime
        proof["servizio_recente"] = current.get("pid") == pid and 0 <= age <= 15
        proof["eta_stato_secondi"] = round(age, 2)
        proof["agenti_operativi"] = sorted(agent for agent in EXPECTED
            if agent in current.get("attivi", []) and current.get("agenti", {}).get(agent, {}).get("stato") == "OPERATIVO")
        proof["verificato_alle_utc"] = datetime.now(timezone.utc).isoformat()
        return proof
    except (OSError, ValueError, TypeError, subprocess.SubprocessError):
        proof["servizio_recente"] = False
        return proof


def healthy(proof):
    return (proof.get("servizio_recente") is True and proof.get("processo_presente") is True
            and EXPECTED.issubset(proof.get("agenti_operativi", [])))


def _wait_healthy(seconds=30):
    proof = observe()
    deadline = time.monotonic() + seconds
    while not healthy(proof) and time.monotonic() < deadline:
        time.sleep(1)
        proof = observe()
    return proof


def restart():
    """Stop only the verified onda.servizio PID, then start the existing task."""
    proof = observe()
    if proof["processo_presente"] and proof["pid"] > 0:
        powershell(f"Stop-Process -Id {int(proof['pid'])} -Force -ErrorAction Stop", timeout=10)
        time.sleep(2)
    launch = powershell("Start-ScheduledTask -TaskName 'R3_ONDA_servizio' -ErrorAction Stop", timeout=10)
    proof = _wait_healthy(45) if launch.returncode == 0 else observe()
    return {"ok": healthy(proof), "proof": proof, "riavviato": launch.returncode == 0 and healthy(proof)}


def report(proof):
    try:
        data = json.loads(STATE.read_text(encoding="utf-8-sig"))
    except (OSError, ValueError):
        return None
    result = {"compiti": {k: v for k, v in (data.get("compiti") or {}).items() if isinstance(v, int)},
              "raffaello": str(data.get("raffaello", ""))[:60], "avviato": str(data.get("avviato", ""))[:60],
              "aggiornato": str(data.get("aggiornato", ""))[:60]}
    try:
        result["attivo_da_ore"] = round((datetime.now() - datetime.fromisoformat(result["avviato"])).total_seconds() / 3600, 1)
    except ValueError:
        pass
    return result


def ask(action, text):
    """Hand bounded text to ONDA as data; argv list, never a shell string."""
    if not isinstance(text, str) or not text.strip() or len(text) > 900:
        return None
    argv = [str(ONDA_PYTHON), "-m", "onda.chiedi"] + (["--scrivi"] if action == "scrivi" else []) + ["--", text]
    env = dict(os.environ, PYTHONIOENCODING="utf-8", ONDA_STATO=str(STATE.parent),
               ONDA_REDIS_URL=os.environ.get("ONDA_REDIS_URL", "redis://127.0.0.1:6379"))
    if not env.get("ONDA_SEGRETO"):
        return None
    try:
        done = subprocess.run(argv, cwd=str(ONDA_DIR), env=env, capture_output=True, text=True,
                              encoding="utf-8", timeout=ASK_TIMEOUT, check=False)
    except subprocess.TimeoutExpired:
        return None
    answer = done.stdout.strip()
    return answer if done.returncode == 0 and answer else None


def execute(action, text=None):
    if action not in {"attiva", "stato", "riavvia", "rapporto", "chiedi", "scrivi"}:
        return {"ok": False, "proof": {}, "error": "Azione non prevista."}
    if action == "riavvia":
        return restart()
    proof = observe()
    if action in {"chiedi", "scrivi"}:
        if not healthy(proof):
            return {"ok": False, "proof": proof}
        answer = ask(action, text)
        return {"ok": True, "proof": observe(), "risposta": answer}
    if action == "rapporto":
        return {"ok": healthy(proof), "proof": proof, "rapporto": report(proof)}
    started = False
    if action == "attiva" and not proof["processo_presente"]:
        launch = powershell("Start-ScheduledTask -TaskName 'R3_ONDA_servizio' -ErrorAction Stop", timeout=10)
        started = launch.returncode == 0
        if started:
            deadline = time.monotonic() + 30
            while time.monotonic() < deadline:
                proof = observe()
                if healthy(proof):
                    break
                time.sleep(1)
    proof["avvio_richiesto"] = started
    if healthy(proof):
        return {"ok": True, "proof": proof}
    return {"ok": False, "proof": proof, "error": "ONDA non confermata operativa: il controllo di recupero esistente resta responsabile del servizio."}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--credentials", type=Path, required=True)
    parser.add_argument("--configure-stdin", action="store_true")
    parser.add_argument("--once", action="store_true")
    args = parser.parse_args()
    try:
        if args.configure_stdin:
            print("READY_FOR_CONFIG", flush=True)
            configure(args.credentials)
            return 0
        import redis
        url = dpapi(args.credentials.read_bytes(), False).decode()
        if urlsplit(url).scheme != "rediss":
            raise ValueError("TLS Redis connection required")
        client = redis.Redis.from_url(url, decode_responses=True, socket_connect_timeout=4,
                                     socket_timeout=5, ssl_cert_reqs="required")
        records = process_pending(client, execute, socket.gethostname() + ":" + str(os.getpid()))
        print(json.dumps({"checked_at_utc": datetime.now(timezone.utc).isoformat(),
                          "receipts": [{"id": r.get("id"), "stato": r.get("stato")} for r in records]}), flush=True)
        return 0
    except Exception as exc:
        # Exceptions from network clients may contain connection credentials.
        print(json.dumps({"ok": False, "error_type": type(exc).__name__}), flush=True)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
