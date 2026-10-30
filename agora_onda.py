"""Bounded Agorà queue adapter for the existing ONDA worker.

The authenticated owner endpoint constructs records and sets
``onda_owner_authorized=True``; callers' JSON and model output must never supply
that authority marker. Redis is the existing trusted Agorà archive, not a new
authorization service. Only two literal commands are admitted. The supplied
executor must implement idempotent ensure-active/read-state operations.

A durable dispatch fence prevents automatic re-execution after an uncertain
outcome. This provides at-most-once dispatch per retained request, not a claim
of distributed exactly-once execution. A lost worker produces an explicit
unverified outcome; a new owner request is needed to retry.
"""

from __future__ import annotations

import copy
from datetime import datetime, timezone
import json
import math
import re
import secrets
import time


PREFIX = "agora:v1:"
RETENTION = 30 * 86400
PENDING_KEY = PREFIX + "onda:pending"
HISTORY_KEY = PREFIX + "history"
TARGET = "claudio-dell-onda"
VERSION = 1
DEADLINE_SECONDS = 600
LEASE_SECONDS = 90
MAX_BATCH = 3
PROOF_MAX_AGE_SECONDS = 90
RID = re.compile(r"^[a-f0-9]{32}$")
_COMMAND = re.compile(r"/onda[ \t]+(attiva|stato)", re.IGNORECASE | re.ASCII)
_TERMINAL = frozenset({"completato", "errore", "interrotto", "scaduto"})
_AGENTS = frozenset({"NARR-003", "NARR-013"})
_SOURCE = "agora_owner_endpoint"
_RELEASE = """
if redis.call('GET', KEYS[1]) == ARGV[1] then
  return redis.call('DEL', KEYS[1])
end
return 0
"""
_SAVE_WITH_LEASE = """
if redis.call('GET', KEYS[1]) ~= ARGV[1] then return 0 end
redis.call('SET', KEYS[2], ARGV[2], 'EX', ARGV[3])
return 1
"""


class OndaArchiveError(RuntimeError):
    """Persistence or read-after-write could not be confirmed."""


class OndaLeaseLost(RuntimeError):
    """This worker no longer owns the request lease."""


class OndaBusyError(RuntimeError):
    """Another invocation is registering this request."""


def _now():
    return time.time()


def _utc(epoch=None):
    return datetime.fromtimestamp(_now() if epoch is None else epoch, timezone.utc).isoformat()


def _rid(rid):
    if not isinstance(rid, str) or not RID.fullmatch(rid):
        raise ValueError("Identificativo della richiesta non valido.")
    return rid


def _record_key(rid):
    return PREFIX + "request:" + _rid(rid)


def _lease_key(rid):
    return PREFIX + "onda:lease:" + _rid(rid)


def _text(raw):
    return raw.decode("utf-8") if isinstance(raw, bytes) else raw


def _finite(value):
    return type(value) in (int, float) and math.isfinite(value)


def parse_command(command):
    """Return the allowlisted action; never extract an action from prose."""
    if not isinstance(command, str):
        return None
    match = _COMMAND.fullmatch(command.strip())
    return match.group(1).lower() if match else None


def _reject_constant(value):
    raise ValueError("Valore JSON non finito.")


def load_record(client, rid):
    raw = client.get(_record_key(rid))
    if raw is None:
        return None
    try:
        record = json.loads(_text(raw), parse_constant=_reject_constant)
    except (ValueError, TypeError, UnicodeError) as exc:
        raise OndaArchiveError("La richiesta archiviata non è leggibile.") from exc
    if not isinstance(record, dict) or record.get("id") != rid:
        raise OndaArchiveError("Identità della richiesta archiviata non confermata.")
    return record


def _encode(rid, record):
    _rid(rid)
    if not isinstance(record, dict) or record.get("id") != rid:
        raise ValueError("Identità della richiesta non coerente.")
    return json.dumps(record, ensure_ascii=False, allow_nan=False)


def _confirmed(client, rid, encoded):
    if _text(client.get(_record_key(rid))) != encoded:
        raise OndaArchiveError("Salvataggio non confermato dalla rilettura dell'archivio.")
    return json.loads(encoded)


def save_record(client, rid, record):
    """Use the existing Agorà request key/retention and verify exact readback."""
    encoded = _encode(rid, record)
    client.set(_record_key(rid), encoded, ex=RETENTION)
    return _confirmed(client, rid, encoded)


def _save_locked(client, rid, record, token):
    encoded = _encode(rid, record)
    saved = client.eval(_SAVE_WITH_LEASE, 2, _lease_key(rid), _record_key(rid),
                        token, encoded, RETENTION)
    if saved != 1:
        raise OndaLeaseLost("La lease della richiesta non appartiene più a questo worker.")
    return _confirmed(client, rid, encoded)


def _acquire(client, rid):
    token = secrets.token_hex(24)
    return token if client.set(_lease_key(rid), token, nx=True, ex=LEASE_SECONDS) else None


def _owns(client, rid, token):
    return _text(client.get(_lease_key(rid))) == token


def _release(client, rid, token):
    # Failure leaves the bounded TTL in place; never delete another owner's lease.
    try:
        client.eval(_RELEASE, 1, _lease_key(rid), token)
    except Exception:
        pass


def _same_request(old, new):
    fields = ("id", "comando", "telegram_richiesto", "riferimento")
    if any(old.get(field) != new.get(field) for field in fields):
        raise ValueError("Identificativo già usato per un'altra richiesta.")


def _validate_new(record):
    if not isinstance(record, dict):
        raise ValueError("Richiesta non valida.")
    _rid(record.get("id"))
    action = parse_command(record.get("comando"))
    if action is None or record.get("onda_owner_authorized") is not True:
        raise ValueError("ONDA richiede un comando esplicito del proprietario autenticato.")
    if record.get("telegram_richiesto", False) is not False:
        raise ValueError("La consegna Telegram non è supportata per questa richiesta ONDA.")
    if record.get("telegram_inviato", False) is not False:
        raise ValueError("Una nuova richiesta ONDA non può risultare già inviata.")
    return action


def _validate_queued(record):
    action = _validate_new(record)
    meta = record.get("onda")
    if not isinstance(meta, dict):
        raise ValueError("Metadati ONDA mancanti.")
    if (type(meta.get("version")) is not int or meta["version"] != VERSION
            or meta.get("target") != TARGET or meta.get("source") != _SOURCE
            or meta.get("action") != action
            or type(meta.get("dispatch_started")) is not bool):
        raise ValueError("Contratto ONDA non valido.")
    queued, deadline = meta.get("queued_epoch"), meta.get("deadline_epoch")
    if (not _finite(queued) or not _finite(deadline)
            or abs((deadline - queued) - DEADLINE_SECONDS) > 0.001):
        raise ValueError("Scadenza ONDA non valida.")
    return action


def _result(record, state, text, *, code=None, proof=None):
    data = {"version": VERSION, "target": TARGET,
            "azione": parse_command(record.get("comando")), "stato": state,
            "verificato": state == "completato"}
    if code:
        data["codice"] = code
    if proof is not None:
        data["proof"] = proof
        if "verificato_alle_utc" in proof:
            data["verificato_alle_utc"] = proof["verificato_alle_utc"]
    return {"stato": state, "testo": text, "note": [],
            "dati": {"onda": data}, "messaggi": [text]}


def _ensure_history(client, rid):
    if rid not in [_text(value) for value in client.lrange(HISTORY_KEY, 0, 49)]:
        client.lpush(HISTORY_KEY, rid)
        client.ltrim(HISTORY_KEY, 0, 49)


def enqueue(client, record):
    """Persist and queue a newly authorized command, or return its original receipt.

    Call this instead of the ordinary endpoint's first save/history/execute block.
    An existing RID is never reset, and its original deadline is never renewed.
    """
    action = _validate_new(record)
    rid = record["id"]
    token = _acquire(client, rid)
    if token is None:
        old = load_record(client, rid)
        if old is not None:
            _same_request(old, record)
            _validate_queued(old)
            return old
        raise OndaBusyError("Registrazione della richiesta già in corso.")
    try:
        old = load_record(client, rid)
        if old is not None:
            _same_request(old, record)
            _validate_queued(old)
            if old.get("stato") == "in_attesa_pc":
                _ensure_history(client, rid)
                client.zadd(PENDING_KEY, {rid: old["onda"]["queued_epoch"]})
            return old
        queued = copy.deepcopy(record)
        now = _now()
        queued["onda"] = {"version": VERSION, "target": TARGET, "source": _SOURCE,
                          "action": action, "queued_epoch": now,
                          "deadline_epoch": now + DEADLINE_SECONDS,
                          "dispatch_started": False}
        queued["stato"] = "in_attesa_pc"
        queued["risultato"] = _result(
            queued, "in_attesa_pc", "Richiesta ONDA registrata. In attesa della verifica sul PC.")
        queued = _save_locked(client, rid, queued, token)
        _ensure_history(client, rid)
        client.zadd(PENDING_KEY, {rid: now})
        if client.zscore(PENDING_KEY, rid) != now:
            raise OndaArchiveError("Inserimento nella coda ONDA non confermato.")
        return queued
    finally:
        _release(client, rid, token)


def _terminal(client, record, token, *, code=None, text, proof=None):
    terminal = copy.deepcopy(record)
    state = "completato" if proof is not None else "errore"
    terminal["stato"] = state
    terminal["completata_utc"] = _utc()
    if code:
        terminal["errore"] = text
    terminal["risultato"] = _result(terminal, state, text, code=code, proof=proof)
    terminal = _save_locked(client, record["id"], terminal, token)
    client.zrem(PENDING_KEY, record["id"])
    return terminal


def _proof(result):
    if not isinstance(result, dict) or result.get("ok") is not True:
        return None
    proof = result.get("proof")
    if not isinstance(proof, dict):
        return None
    agents = proof.get("agenti_operativi")
    if (proof.get("servizio_recente") is not True
            or proof.get("processo_presente") is not True
            or type(proof.get("pid")) is not int or proof["pid"] <= 0
            or not isinstance(agents, (list, tuple, set, frozenset))
            or not all(isinstance(agent, str) for agent in agents)
            or not _AGENTS.issubset(agents)):
        return None
    # Preserve bounded operational proof, never arbitrary executor output/secrets.
    clean = {"servizio_recente": True, "processo_presente": True,
             "pid": proof["pid"], "agenti_operativi": sorted(set(agents))}
    if "verificato_alle_utc" in proof:
        value = proof["verificato_alle_utc"]
        try:
            if not isinstance(value, str):
                return None
            verified = datetime.fromisoformat(value.replace("Z", "+00:00"))
            if verified.tzinfo is None:
                return None
            age = _now() - verified.timestamp()
            if not -15 <= age <= PROOF_MAX_AGE_SECONDS:
                return None
        except (ValueError, OverflowError):
            return None
        clean["verificato_alle_utc"] = value
    return clean


def expire_if_needed(client, record):
    """Expire an offline-PC request without racing a worker holding its lease."""
    if (not isinstance(record, dict) or record.get("stato") != "in_attesa_pc"
            or not isinstance(record.get("onda"), dict)):
        return record
    deadline = record["onda"].get("deadline_epoch")
    if not _finite(deadline) or _now() < deadline:
        return record
    rid = _rid(record.get("id"))
    token = _acquire(client, rid)
    if token is None:
        return record
    try:
        current = load_record(client, rid)
        if current is None:
            raise OndaArchiveError("La richiesta non è più presente nell'archivio.")
        if current.get("stato") != "in_attesa_pc":
            return current
        _validate_queued(current)
        if _now() < current["onda"]["deadline_epoch"]:
            return current
        return _terminal(client, current, token, code="SCADUTA",
                         text="La verifica ONDA non è stata conclusa entro 10 minuti. "
                              "Nessuna nuova esecuzione verrà avviata per questa richiesta.")
    finally:
        _release(client, rid, token)


def process_pending(client, execute, worker_id):
    """Process at most three RIDs; return only newly confirmed terminal records.

    ``execute(action)`` returns ``{ok: bool, proof: {...}}``. It receives no
    arbitrary prompt, shell command, target or model recommendation. Exceptions
    and incomplete proof are failures. Storage errors propagate, preserving the
    pending item and dispatch fence for inspection/reconciliation.
    """
    if not isinstance(worker_id, str) or not worker_id.strip() or len(worker_id) > 160:
        raise ValueError("Identità worker non valida.")
    completed = []
    for raw_rid in client.zrange(PENDING_KEY, 0, MAX_BATCH - 1):
        rid = _text(raw_rid)
        if not isinstance(rid, str) or not RID.fullmatch(rid):
            client.zrem(PENDING_KEY, raw_rid)
            continue
        token = _acquire(client, rid)
        if token is None:
            continue
        try:
            record = load_record(client, rid)
            if record is None or record.get("stato") in _TERMINAL:
                client.zrem(PENDING_KEY, rid)
                continue
            try:
                action = _validate_queued(record)
                if record.get("stato") != "in_attesa_pc":
                    raise ValueError("Stato della richiesta non eseguibile.")
            except ValueError:
                completed.append(_terminal(client, record, token, code="RICHIESTA_NON_AUTORIZZATA",
                    text="La richiesta non rispetta il contratto ONDA autorizzato. Nessuna azione eseguita."))
                continue
            if _now() >= record["onda"]["deadline_epoch"]:
                completed.append(_terminal(client, record, token, code="SCADUTA",
                    text="Richiesta ONDA scaduta prima della verifica. Nessuna nuova azione eseguita."))
                continue
            if record["onda"]["dispatch_started"]:
                completed.append(_terminal(client, record, token, code="ESECUZIONE_INTERROTTA",
                    text="Una precedente esecuzione è iniziata senza una ricevuta conclusiva. "
                         "Esito non verificato; la richiesta non viene eseguita una seconda volta."))
                continue
            record["onda"].update(dispatch_started=True, dispatch_started_epoch=_now(), worker_id=worker_id)
            record["risultato"] = _result(record, "in_attesa_pc", "Il PC sta verificando il servizio ONDA.")
            record = _save_locked(client, rid, record, token)
            if not _owns(client, rid, token):
                continue
            try:
                result = execute(action)
            except Exception:
                result = {"ok": False}
            if _now() >= record["onda"]["deadline_epoch"]:
                completed.append(_terminal(client, record, token, code="SCADUTA",
                    text="L'esecuzione ONDA è iniziata, ma la verifica ha superato la scadenza. "
                         "Esito non convalidato; nessuna riesecuzione automatica."))
                continue
            proof = _proof(result)
            if proof is None:
                terminal = _terminal(client, record, token, code="ESITO_NON_VERIFICATO",
                    text="Il PC non ha confermato un servizio ONDA recente, con processo e agenti operativi. "
                         "Esito non verificato; nessuna riesecuzione automatica.")
            else:
                terminal = _terminal(client, record, token, proof=proof,
                    text=f"ONDA operativa verificata sul PC: processo {proof['pid']}, "
                         "agenti NARR-003 e NARR-013 operativi.")
            completed.append(terminal)
        except OndaLeaseLost:
            # A newer lease owner alone may commit; the dispatch fence survives.
            continue
        finally:
            _release(client, rid, token)
    return completed
