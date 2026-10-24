import unittest
from datetime import datetime, timedelta, timezone
from uuid import uuid4

from sdq1.onda_protocol import (
    COMMAND_CHANNEL, EMERGENCY_CHANNEL, HeartbeatMonitor, ProtocolError,
    new_envelope, redis_lock_command, validate_channel_authority, validate_envelope,
)


NOW = datetime(2026, 7, 17, 12, 21, tzinfo=timezone.utc)


def envelope(**overrides):
    value = new_envelope(
        sender="RAFFA-001", recipient="MEMO-002", kind="COMANDO", epoch=42,
        payload={"action": "summarize"}, correlation_id=str(uuid4()), now=NOW,
    )
    value.update(overrides)
    return value


class OndaProtocolTests(unittest.TestCase):
    def test_valid_command_envelope_normalizes_timestamp(self):
        result = validate_envelope(envelope(), 42, now=NOW)
        self.assertEqual(result["protocollo"], "ONDA/1.0")
        self.assertTrue(result["timestamp"].endswith("Z"))

    def test_stale_and_future_epochs_are_rejected(self):
        for epoch in (41, 43):
            with self.subTest(epoch=epoch), self.assertRaises(ProtocolError):
                validate_envelope(envelope(epoca=epoch), 42, now=NOW)

    def test_expired_message_is_rejected(self):
        old = NOW - timedelta(seconds=16)
        with self.assertRaises(ProtocolError):
            validate_envelope(envelope(timestamp=old.isoformat(), scadenza_secondi=15), 42, now=NOW)

    def test_naive_timestamp_is_rejected(self):
        with self.assertRaises(ProtocolError):
            validate_envelope(envelope(timestamp="2026-07-17T12:21:00"), 42, now=NOW)

    def test_invalid_message_id_and_correlation_are_rejected(self):
        for changes in ({"id_messaggio": "not-a-uuid"}, {"id_correlazione": "bad-id"}):
            with self.subTest(changes=changes), self.assertRaises(ProtocolError):
                validate_envelope(envelope(**changes), 42, now=NOW)

    def test_non_v4_message_id_is_rejected(self):
        # A valid UUID v1 is intentionally outside the protocol contract.
        with self.assertRaises(ProtocolError):
            validate_envelope(envelope(id_messaggio="00000000-0000-1000-8000-000000000000"), 42, now=NOW)

    def test_invalid_priority_expiry_and_epoch_types_are_rejected(self):
        cases = (
            {"priorita": True}, {"priorita": 4}, {"scadenza_secondi": False},
            {"scadenza_secondi": 0}, {"epoca": True},
        )
        for changes in cases:
            with self.subTest(changes=changes), self.assertRaises(ProtocolError):
                validate_envelope(envelope(**changes), 42, now=NOW)

    def test_only_orchestrator_can_send_commands(self):
        with self.assertRaises(ProtocolError):
            validate_envelope(envelope(mittente="MEMO-002"), 42, now=NOW)

    def test_only_sentinel_can_send_emergency(self):
        msg = envelope(tipo="EMERGENZA", mittente="RAFFA-001")
        with self.assertRaises(ProtocolError):
            validate_envelope(msg, 42, now=NOW)

    def test_response_requires_correlation_id(self):
        msg = envelope(tipo="RISPOSTA", id_correlazione=None)
        with self.assertRaises(ProtocolError):
            validate_envelope(msg, 42, now=NOW)

    def test_heartbeat_must_be_broadcast(self):
        msg = envelope(tipo="HEARTBEAT", destinatario="MEMO-002")
        with self.assertRaises(ProtocolError):
            validate_envelope(msg, 42, now=NOW)

    def test_payload_size_limit_is_enforced_in_utf8_bytes(self):
        msg = envelope(payload={"text": "é" * 300})
        with self.assertRaises(ProtocolError):
            validate_envelope(msg, 42, now=NOW, max_payload_bytes=512)

    def test_non_json_payload_is_rejected(self):
        msg = envelope(payload={"not_json": object()})
        with self.assertRaises(ProtocolError):
            validate_envelope(msg, 42, now=NOW)

    def test_privileged_channel_authority(self):
        validate_channel_authority(COMMAND_CHANNEL, "RAFFA-001")
        validate_channel_authority(EMERGENCY_CHANNEL, "SENTIN-004")
        with self.assertRaises(ProtocolError):
            validate_channel_authority(COMMAND_CHANNEL, "MEMO-002")
        with self.assertRaises(ProtocolError):
            validate_channel_authority(EMERGENCY_CHANNEL, "RAFFA-001")

    def test_heartbeat_offline_after_three_missed_intervals(self):
        monitor = HeartbeatMonitor()
        self.assertTrue(monitor.is_offline(NOW))
        monitor.record(NOW)
        self.assertFalse(monitor.is_offline(NOW + timedelta(seconds=29)))
        self.assertTrue(monitor.is_offline(NOW + timedelta(seconds=30)))

    def test_heartbeat_rejects_naive_clock(self):
        monitor = HeartbeatMonitor()
        with self.assertRaises(ProtocolError):
            monitor.record(datetime(2026, 7, 17, 12, 21))

    def test_redis_lock_command_has_ttl_and_owner(self):
        command = redis_lock_command("memory index", "MEMO-002")
        self.assertEqual(command, ("SET", "sdq1:lock:memory_index", "MEMO-002", 30))

    def test_future_timestamp_beyond_tolerance_is_rejected(self):
        future = NOW + timedelta(seconds=6)
        with self.assertRaises(ProtocolError):
            validate_envelope(envelope(timestamp=future.isoformat()), 42, now=NOW)


if __name__ == "__main__":
    unittest.main()
