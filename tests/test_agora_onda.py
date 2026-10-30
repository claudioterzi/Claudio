"""Behavioral checks for bounded ONDA dispatch and authoritative receipts."""

import copy
from datetime import datetime, timezone
import json
import unittest
from unittest.mock import Mock, patch

import fakeredis

import agora_onda as onda


class TamperedReadback:
    """Archive proxy that returns altered persisted state after a chosen read."""

    def __init__(self, client, request_key, skip_reads=0):
        self.client = client
        self.request_key = request_key
        self.skip_reads = skip_reads

    def __getattr__(self, name):
        return getattr(self.client, name)

    def get(self, key):
        raw = self.client.get(key)
        if key == self.request_key and raw is not None:
            if self.skip_reads:
                self.skip_reads -= 1
            else:
                value = json.loads(raw)
                value["tampered"] = True
                return json.dumps(value).encode()
        return raw


class AgoraOndaTests(unittest.TestCase):
    def setUp(self):
        self.client = fakeredis.FakeRedis()
        self.now = 2_000_000_000.0
        self.clock = patch.object(onda, "_now", side_effect=lambda: self.now)
        self.clock.start()
        self.addCleanup(self.clock.stop)
        self.rid = "e911f074a7bbadf6917b33712b8697ba"

    def record(self, rid=None, command="/onda attiva"):
        return {"id": rid or self.rid, "comando": command,
                "data": datetime.fromtimestamp(self.now, timezone.utc).isoformat(),
                "iniziata_epoch": self.now, "stato": "in_corso",
                "riferimento": "0123456789abcdef0123456789abcdef",
                "onda_owner_authorized": True,
                "telegram_richiesto": False, "telegram_inviato": False}

    def response(self, **changes):
        proof = {"servizio_recente": True, "processo_presente": True, "pid": 29840,
                 "agenti_operativi": ["NARR-003", "NARR-013"],
                 "verificato_alle_utc": datetime.fromtimestamp(self.now, timezone.utc).isoformat()}
        proof.update(changes)
        return {"ok": True, "proof": proof}

    def pending(self, record=None):
        return onda.enqueue(self.client, record or self.record())

    def test_parser_requires_entire_explicit_command(self):
        self.assertEqual(onda.parse_command(" /ONDA\tATTIVA "), "attiva")
        self.assertEqual(onda.parse_command("/onda stato"), "stato")
        for value in (None, {}, "/consiglio Attiva onda", "Attiva onda", "/onda attiva ora",
                      "/onda attiva\n/cancella", "/onda ferma", "consiglio: /onda attiva"):
            with self.subTest(value=value):
                self.assertIsNone(onda.parse_command(value))

    def test_enqueue_preserves_record_and_uses_single_existing_history(self):
        original = self.record()
        before = copy.deepcopy(original)
        saved = self.pending(original)
        self.assertEqual(original, before)
        for key in ("id", "comando", "data", "riferimento", "telegram_richiesto", "telegram_inviato"):
            self.assertEqual(saved[key], original[key])
        self.assertEqual(saved["stato"], "in_attesa_pc")
        self.assertEqual(saved["onda"]["deadline_epoch"], self.now + 600)
        self.assertEqual(onda.load_record(self.client, self.rid), saved)
        self.assertEqual(self.client.lrange(onda.HISTORY_KEY, 0, -1), [self.rid.encode()])
        self.assertGreater(self.client.ttl(onda.PREFIX + "request:" + self.rid), onda.RETENTION - 5)

    def test_duplicate_does_not_renew_deadline_or_repeat_dispatch(self):
        saved = self.pending()
        self.now += 20
        duplicate = self.pending()
        self.assertEqual(duplicate["data"], saved["data"])
        self.assertEqual(duplicate["onda"]["deadline_epoch"], saved["onda"]["deadline_epoch"])
        self.assertEqual(self.client.llen(onda.HISTORY_KEY), 1)
        execute = Mock(return_value=self.response())
        result = onda.process_pending(self.client, execute, "test-worker")
        self.assertEqual(result[0]["stato"], "completato")
        self.assertEqual(result[0]["risultato"]["dati"]["onda"]["verificato_alle_utc"],
                         self.response()["proof"]["verificato_alle_utc"])
        self.assertEqual(onda.process_pending(self.client, execute, "restart"), [])
        self.assertEqual(self.pending()["stato"], "completato")
        self.assertEqual(self.client.zcard(onda.PENDING_KEY), 0)
        execute.assert_called_once_with("attiva")

    def test_same_id_different_command_or_reference_is_rejected(self):
        self.pending()
        for key, value in (("comando", "/onda stato"), ("riferimento", "different")):
            new = self.record()
            new[key] = value
            with self.subTest(key=key), self.assertRaises(ValueError):
                self.pending(new)

    def test_owner_marker_and_no_telegram_are_required(self):
        for field, value in (("onda_owner_authorized", False), ("onda_owner_authorized", "true"),
                             ("telegram_richiesto", True), ("telegram_inviato", True)):
            record = self.record()
            record[field] = value
            with self.subTest(field=field, value=value), self.assertRaises(ValueError):
                self.pending(record)
        self.assertEqual(self.client.zcard(onda.PENDING_KEY), 0)

    def test_model_recommendation_cannot_queue_an_action(self):
        record = self.record(command="/consiglio Attiva onda")
        record["risultato"] = {"dati": {"consiglio": {"decisione_finale": "/onda attiva"}}}
        record["azione"] = "attiva"
        with self.assertRaises(ValueError):
            self.pending(record)

    def test_changed_command_or_arbitrary_action_is_rejected_by_worker(self):
        for field in ("command", "action", "target", "authority"):
            with self.subTest(field=field):
                self.client.flushall()
                record = self.pending()
                if field == "command":
                    record["comando"] = "/consiglio Attiva onda"
                    record["azione"] = "attiva"
                elif field == "authority":
                    record["onda_owner_authorized"] = False
                else:
                    record["onda"][field] = "arbitrary"
                onda.save_record(self.client, self.rid, record)
                execute = Mock()
                result = onda.process_pending(self.client, execute, "worker")
                self.assertEqual(result[0]["stato"], "errore")
                execute.assert_not_called()

    def test_live_lease_prevents_execution_and_is_not_removed(self):
        self.pending()
        key = onda.PREFIX + "onda:lease:" + self.rid
        self.client.set(key, "other-worker", ex=90)
        execute = Mock()
        self.assertEqual(onda.process_pending(self.client, execute, "worker"), [])
        self.assertEqual(self.client.get(key), b"other-worker")
        self.assertEqual(self.pending()["stato"], "in_attesa_pc")
        execute.assert_not_called()

    def test_expired_request_is_never_executed(self):
        self.pending()
        self.now += 601
        execute = Mock()
        result = onda.process_pending(self.client, execute, "worker")
        self.assertEqual(result[0]["risultato"]["dati"]["onda"]["codice"], "SCADUTA")
        self.assertEqual(self.client.zcard(onda.PENDING_KEY), 0)
        execute.assert_not_called()

    def test_history_expiry_is_durable_and_respects_active_worker(self):
        record = self.pending()
        self.now += 601
        key = onda.PREFIX + "onda:lease:" + self.rid
        self.client.set(key, "worker", ex=90)
        self.assertEqual(onda.expire_if_needed(self.client, record)["stato"], "in_attesa_pc")
        self.client.delete(key)
        expired = onda.expire_if_needed(self.client, record)
        self.assertEqual(expired["stato"], "errore")
        self.assertEqual(onda.load_record(self.client, self.rid), expired)
        self.assertEqual(self.client.zcard(onda.PENDING_KEY), 0)
        self.assertEqual(onda.expire_if_needed(self.client, record), expired)

    def test_result_arriving_after_deadline_is_not_promoted(self):
        self.pending()

        def late_result(action):
            self.now += 601
            return self.response()

        result = onda.process_pending(self.client, late_result, "worker")
        self.assertEqual(result[0]["stato"], "errore")
        self.assertEqual(result[0]["risultato"]["dati"]["onda"]["codice"], "SCADUTA")
        self.assertTrue(result[0]["onda"]["dispatch_started"])

    def test_weak_or_stale_proof_cannot_become_completed(self):
        bad = [dict(servizio_recente=False), dict(processo_presente=False), dict(pid=True),
               dict(pid=0), dict(agenti_operativi=["NARR-003"]),
               dict(verificato_alle_utc=datetime.fromtimestamp(self.now - 91, timezone.utc).isoformat()),
               dict(verificato_alle_utc="2033-05-18T03:33:20")]
        for changes in bad:
            with self.subTest(changes=changes):
                self.client.flushall()
                self.pending()
                result = onda.process_pending(self.client, Mock(return_value=self.response(**changes)), "worker")
                self.assertEqual(result[0]["stato"], "errore")
                self.assertFalse(result[0]["risultato"]["dati"]["onda"]["verificato"])

    def test_executor_error_is_not_exposed_or_retried(self):
        self.pending()
        execute = Mock(side_effect=RuntimeError("secret-token-value"))
        result = onda.process_pending(self.client, execute, "worker")
        self.assertEqual(result[0]["stato"], "errore")
        self.assertNotIn("secret-token-value", json.dumps(result))
        onda.process_pending(self.client, execute, "restart")
        execute.assert_called_once()

    def test_readback_mismatch_rejects_save_and_prevents_dispatch(self):
        record = self.record()
        key = onda.PREFIX + "request:" + self.rid
        with self.assertRaises(onda.OndaArchiveError):
            onda.save_record(TamperedReadback(self.client, key), self.rid, record)
        self.client.flushall()
        self.pending()
        execute = Mock()
        with self.assertRaises(onda.OndaArchiveError):
            onda.process_pending(TamperedReadback(self.client, key, skip_reads=1), execute, "worker")
        execute.assert_not_called()
        self.assertEqual(self.client.zcard(onda.PENDING_KEY), 1)

    def test_crash_after_dispatch_fence_does_not_repeat_action(self):
        self.pending()
        execute = Mock(side_effect=SystemExit("simulated worker death"))
        with self.assertRaises(SystemExit):
            onda.process_pending(self.client, execute, "worker")
        self.assertTrue(onda.load_record(self.client, self.rid)["onda"]["dispatch_started"])
        retry = Mock()
        recovered = onda.process_pending(self.client, retry, "restart")
        self.assertEqual(recovered[0]["risultato"]["dati"]["onda"]["codice"], "ESECUZIONE_INTERROTTA")
        retry.assert_not_called()

    def test_worker_losing_lease_cannot_overwrite_new_owner_or_release_it(self):
        self.pending()
        key = onda.PREFIX + "onda:lease:" + self.rid

        def lose_lease(action):
            self.client.set(key, "new-worker", ex=90)
            return self.response()

        self.assertEqual(onda.process_pending(self.client, lose_lease, "old-worker"), [])
        self.assertEqual(self.client.get(key), b"new-worker")
        record = onda.load_record(self.client, self.rid)
        self.assertEqual(record["stato"], "in_attesa_pc")
        self.assertTrue(record["onda"]["dispatch_started"])

    def test_terminal_or_missing_records_are_cleaned_without_execution(self):
        record = self.pending()
        record["stato"] = "completato"
        onda.save_record(self.client, self.rid, record)
        missing = "a" * 32
        self.client.zadd(onda.PENDING_KEY, {missing: self.now})
        execute = Mock()
        self.assertEqual(onda.process_pending(self.client, execute, "restart"), [])
        self.assertEqual(self.client.zcard(onda.PENDING_KEY), 0)
        execute.assert_not_called()

    def test_batch_is_bounded_to_three_requests(self):
        for number in range(5):
            self.pending(self.record(rid=f"{number:032x}", command="/onda stato"))
        execute = Mock(return_value=self.response())
        result = onda.process_pending(self.client, execute, "worker")
        self.assertEqual(len(result), 3)
        self.assertEqual(execute.call_count, 3)
        self.assertEqual(self.client.zcard(onda.PENDING_KEY), 2)
        self.assertEqual({call.args for call in execute.call_args_list}, {("stato",)})


if __name__ == "__main__":
    unittest.main()
