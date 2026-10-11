"""Falsifiers for the universal backup recoverability contract."""
from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from sdq1 import backup


class FakeMemory:
    def esporta(self):
        return [{"testo": "memoria-verificata", "metadata": {"source": "test"}}]


class BrokenMemory:
    def esporta(self):
        raise RuntimeError("synthetic export failure")


class FakeVSS:
    def esporta(self):
        return [{"run_id": "r1", "agente": "test", "testo": "vss"}]


class FakeRouter:
    def provider_attivi(self):
        return {"stub": True}

    def stato_circuit_breaker(self):
        return {"stub": "closed"}


class FakeConfig:
    sistema = "test"
    modello = "stub"
    router = {"regole": [{"profilo": "default"}]}


class BackupRecoverabilityTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        root = Path(self.tmp.name)
        self.backups = root / "backups"
        self.sar = root / "sar"
        self.sar.mkdir(parents=True)
        (self.sar / "state.json").write_text(
            json.dumps({"value": 1}), encoding="utf-8"
        )
        self.patches = [
            patch.object(backup, "_BACKUP_DIR", self.backups),
            patch.object(backup, "_SAR_DIR", self.sar),
            patch("sdq1.notifiche.notifica_completato"),
        ]
        for item in self.patches:
            item.start()

    def tearDown(self):
        for item in reversed(self.patches):
            item.stop()
        self.tmp.cleanup()

    def _full_backup(self) -> Path:
        return backup.crea_backup(
            memoria=FakeMemory(),
            vss=FakeVSS(),
            router=FakeRouter(),
            config=FakeConfig(),
            etichetta="test",
        )

    def test_complete_backup_is_self_verifying(self):
        path = self._full_backup()
        result = backup.verifica_backup(path)
        data = json.loads(path.read_text(encoding="utf-8"))

        self.assertTrue(result["verified"])
        self.assertFalse(result["legacy_unverified"])
        self.assertTrue(result["complete"])
        self.assertTrue(data["meta"]["complete"])
        self.assertEqual(
            data["component_status"],
            {
                "sar": "ok",
                "memoria": "ok",
                "vss": "ok",
                "router": "ok",
                "config": "ok",
            },
        )

    def test_snapshot_counts_are_not_restored_memory_counts(self):
        result = backup.ripristina_backup(self._full_backup())
        self.assertEqual(result["restore_scope"], "SAR_ONLY")
        self.assertFalse(result["restore_complete"])
        self.assertEqual(result["memoria_entries"], 0)
        self.assertEqual(result["vss_entries"], 0)
        self.assertEqual(result["snapshot_memoria_entries"], 1)
        self.assertEqual(result["snapshot_vss_entries"], 1)

    def test_complete_restore_request_is_refused_before_writes(self):
        path = self._full_backup()
        (self.sar / "state.json").write_text('{"value": 2}', encoding="utf-8")
        before = (self.sar / "state.json").read_bytes()
        with self.assertRaises(backup.BackupIntegrityError):
            backup.ripristina_backup(path, require_complete=True)
        self.assertEqual((self.sar / "state.json").read_bytes(), before)

    def test_removing_integrity_cannot_downgrade_new_backup_to_legacy(self):
        path = self._full_backup()
        data = json.loads(path.read_text(encoding="utf-8"))
        del data["integrity"]
        path.write_text(json.dumps(data), encoding="utf-8")
        before = (self.sar / "state.json").read_bytes()
        with self.assertRaises(backup.BackupIntegrityError):
            backup.ripristina_backup(path)
        self.assertEqual((self.sar / "state.json").read_bytes(), before)

    def test_restore_checks_the_same_snapshot_it_writes(self):
        path = self._full_backup()
        valid = path.read_text(encoding="utf-8")
        tampered = json.loads(valid)
        tampered["sar"]["state.json"]["value"] = 999
        before = (self.sar / "state.json").read_bytes()
        # A second read must not validate different bytes from those restored.
        with patch.object(Path, "read_text", side_effect=[json.dumps(tampered), valid]):
            with self.assertRaises(backup.BackupIntegrityError):
                backup.ripristina_backup(path)
        self.assertEqual((self.sar / "state.json").read_bytes(), before)

    def test_partial_backup_is_preserved_but_never_claimed_complete(self):
        path = backup.crea_backup(
            memoria=BrokenMemory(),
            vss=FakeVSS(),
            router=FakeRouter(),
            config=FakeConfig(),
            etichetta="partial",
        )
        data = json.loads(path.read_text(encoding="utf-8"))

        self.assertTrue(backup.verifica_backup(path)["verified"])
        self.assertFalse(data["meta"]["complete"])
        self.assertEqual(data["component_status"]["memoria"], "error")
        self.assertTrue(any(x.startswith("memoria:") for x in data["errors"]))

    def test_tampered_new_backup_is_refused_before_restore(self):
        path = self._full_backup()
        data = json.loads(path.read_text(encoding="utf-8"))
        data["sar"]["state.json"]["value"] = 999
        path.write_text(json.dumps(data), encoding="utf-8")

        before = (self.sar / "state.json").read_text(encoding="utf-8")
        with self.assertRaises(backup.BackupIntegrityError):
            backup.ripristina_backup(path)
        after = (self.sar / "state.json").read_text(encoding="utf-8")
        self.assertEqual(before, after)

    def test_backup_names_do_not_collide_in_same_second(self):
        first = self._full_backup()
        second = self._full_backup()
        self.assertNotEqual(first.name, second.name)
        self.assertTrue(first.exists())
        self.assertTrue(second.exists())


if __name__ == "__main__":
    unittest.main()
