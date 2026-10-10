"""Regression tests for the full sdq1.snapshot module; no external network.

Run: python -m unittest tests.test_snapshot_solution -v
Synthetic files and real local bare Git repositories only. NOT full R3 coverage.
"""
from __future__ import annotations

import copy
import json
import os
import subprocess
import tempfile
import unittest
import uuid
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

from sdq1 import snapshot


class FrozenDateTime(datetime):
    @classmethod
    def now(cls, tz=None):
        value = cls(2026, 10, 10, 20, 40, 0, 123456, tzinfo=timezone.utc)
        return value.astimezone(tz) if tz is not None else value.replace(tzinfo=None)


def payload(label="first"):
    return {"meta": {"data_ora": "2026-10-10 12:00:00", "versione": "1.1.0"},
            "data": {"label": label}}


class SnapshotFiles(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="r3-snapshot-unit-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.out = self.root / "snapshots"
        for p in [patch.object(snapshot, "_SNAPSHOT_DIR", self.out),
                  patch.object(snapshot, "datetime", FrozenDateTime)]:
            p.start()
            self.addCleanup(p.stop)

    def test_milliseconds_alone_can_still_collide(self):
        a = datetime(2026, 10, 10, 12, 0, 0, 123001)
        b = a.replace(microsecond=123999)
        self.assertEqual(a.isoformat(timespec="milliseconds"), b.isoformat(timespec="milliseconds"))
        self.assertNotEqual(a, b)

    def test_100_saves_with_identical_microsecond_keep_every_payload(self):
        records = [snapshot.salva_snapshot(payload(str(i))) for i in range(100)]
        self.assertEqual(len(set(records)), 100)
        self.assertEqual(len(list(self.out.glob("snapshot_*.json"))), 100)
        parsed = [json.loads(p.read_bytes()) for p in records]
        self.assertEqual({p["data"]["label"] for p in parsed}, {str(i) for i in range(100)})
        self.assertEqual(len({p["meta"]["snapshot_id"] for p in parsed}), 100)
        self.assertEqual({p["meta"]["saved_at_utc"] for p in parsed},
                         {"2026-10-10T20:40:00.123456+00:00"})

    def test_forced_full_name_collision_preserves_first_bytes(self):
        with patch.object(snapshot.uuid, "uuid4", return_value=uuid.UUID(int=1)):
            p = snapshot.salva_snapshot(payload())
            original = p.read_bytes()
            with self.assertRaises(FileExistsError):
                snapshot.salva_snapshot(payload("second"))
            self.assertEqual(p.read_bytes(), original)
            self.assertEqual(len(list(self.out.iterdir())), 1)

    def test_caller_data_unchanged_and_event_time_not_fake_precision(self):
        data = payload()
        before = copy.deepcopy(data)
        p = snapshot.salva_snapshot(data)
        self.assertEqual(data, before)
        saved = json.loads(p.read_bytes())
        self.assertEqual(saved["meta"]["data_ora"], data["meta"]["data_ora"])
        self.assertEqual(saved["meta"]["snapshot_storage_version"], 2)
        self.assertTrue(p.name.startswith("snapshot_2026-10-10_12-00-00__saved_"))
        self.assertIn("20261010T204000123456Z", p.name)

    def test_invalid_timestamp_has_no_filesystem_effect(self):
        for value in ("../../escape", "2026-02-30 12:00:00", None, 1, "bad\nname"):
            with self.subTest(value=value):
                data = payload()
                data["meta"]["data_ora"] = value
                with self.assertRaises(ValueError):
                    snapshot.salva_snapshot(data)
                self.assertFalse(self.out.exists())

    def test_invalid_json_serialization_has_no_filesystem_effect(self):
        for value in (float("nan"), float("inf"), object()):
            with self.subTest(kind=type(value).__name__):
                data = payload()
                data["bad"] = value
                with self.assertRaises((ValueError, TypeError)):
                    snapshot.salva_snapshot(data)
                self.assertFalse(self.out.exists())

    def test_readback_mismatch_is_not_acknowledged(self):
        data = payload()
        with patch.object(Path, "read_bytes", return_value=b"wrong bytes"):
            with self.assertRaisesRegex(OSError, "readback mismatch"):
                snapshot.salva_snapshot(data)
        self.assertNotIn("snapshot_id", data["meta"])
        # The newly written file can exist after failure: no rollback claim.
        self.assertEqual(len(list(self.out.glob("snapshot_*.json"))), 1)

    def test_fsync_failure_is_not_acknowledged(self):
        with patch.object(snapshot.os, "fsync", side_effect=OSError("synthetic fsync failure")):
            with self.assertRaises(OSError):
                snapshot.salva_snapshot(payload())

    def test_existing_legacy_record_is_not_modified(self):
        self.out.mkdir()
        old = self.out / "snapshot_2026-10-10_12-00-00.json"
        old.write_bytes(b"legacy original")
        snapshot.salva_snapshot(payload())
        self.assertEqual(old.read_bytes(), b"legacy original")
        self.assertEqual(len(list(self.out.glob("snapshot_*.json"))), 2)

    def test_existing_symlink_destination_does_not_write_its_target(self):
        if not hasattr(os, "symlink"):
            self.skipTest("symlink unsupported")
        self.out.mkdir()
        victim = self.root / "synthetic-victim"
        victim.write_bytes(b"do not replace")
        fixed = uuid.UUID(int=1)
        dest = self.out / f"snapshot_2026-10-10_12-00-00__saved_20261010T204000123456Z__{fixed.hex}.json"
        try:
            dest.symlink_to(victim)
        except OSError as exc:
            if os.name == "nt" and getattr(exc, "winerror", None) == 1314:
                self.skipTest("Windows fixture requires symlink privilege; no privilege escalation")
            raise
        with patch.object(snapshot.uuid, "uuid4", return_value=fixed):
            with self.assertRaises(FileExistsError):
                snapshot.salva_snapshot(payload())
        self.assertEqual(victim.read_bytes(), b"do not replace")


class LocalBareGit(unittest.TestCase):
    """The network protocol allowlist applies to every subprocess in these tests."""
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="r3-local-git-")
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.root = self.base / "work"
        self.remote = self.base / "origin.git"
        env = {"PATH": os.environ.get("PATH", ""), "HOME": str(self.base),
               "GIT_CONFIG_NOSYSTEM": "1", "GIT_CONFIG_GLOBAL": os.devnull,
               "GIT_TERMINAL_PROMPT": "0", "GIT_ALLOW_PROTOCOL": "file",
               "LC_ALL": "C.UTF-8", "LANG": "C.UTF-8"}
        clean = patch.dict(os.environ, env, clear=True)
        clean.start()
        self.addCleanup(clean.stop)
        self.root.mkdir()
        self.git(self.base, "init", "--bare", str(self.remote))
        self.git(self.root, "init", "-b", "main")
        self.git(self.root, "config", "user.name", "R3 isolated test")
        self.git(self.root, "config", "user.email", "r3-test@invalid.local")
        (self.root / "README").write_text("synthetic fixture\n")
        canonical_ignore = Path(__file__).resolve().parents[1] / ".gitignore"
        ignore_bytes = canonical_ignore.read_bytes()
        self.assertIn(b"!output/snapshots/*.json", ignore_bytes)
        (self.root / ".gitignore").write_bytes(ignore_bytes)
        self.git(self.root, "add", "README", ".gitignore")
        self.git(self.root, "commit", "-m", "fixture baseline")
        self.git(self.root, "remote", "add", "origin", str(self.remote))
        self.git(self.root, "push", "origin", "HEAD:refs/heads/main")
        self.original_remote = self.ref(self.remote)
        p = patch.object(snapshot, "_SNAPSHOT_DIR", self.root / "output/snapshots")
        p.start()
        self.addCleanup(p.stop)
        self.target = snapshot.salva_snapshot(payload())

    @staticmethod
    def git(root, *args):
        return subprocess.run(["git", *args], cwd=root, capture_output=True,
                              timeout=15, check=True).stdout

    def ref(self, root):
        return self.git(root, "rev-parse", "refs/heads/main").strip()

    def publish(self):
        return snapshot.push_snapshot(self.target, repo_dir=self.root)

    def test_accepted_push_has_exact_remote_sha_and_content(self):
        self.assertIn(b".env", self.git(self.root, "check-ignore", "--no-index", ".env"))
        self.assertIs(self.publish(), True)
        head = self.git(self.root, "rev-parse", "HEAD").strip()
        self.assertEqual(self.ref(self.remote), head)
        relative = self.target.relative_to(self.root).as_posix()
        self.assertEqual(self.git(self.remote, "show", "refs/heads/main:" + relative), self.target.read_bytes())
        message = self.git(self.remote, "log", "-1", "--format=%B", "refs/heads/main").decode()
        self.assertIn(json.loads(self.target.read_bytes())["meta"]["snapshot_id"], message)

    def test_noop_keeps_commit_and_verifies_existing_ref(self):
        self.assertTrue(self.publish())
        head = self.ref(self.remote)
        self.assertTrue(self.publish())
        self.assertEqual(self.ref(self.remote), head)

    def test_remote_rejection_is_false_and_remote_unchanged(self):
        hook = self.remote / "hooks/pre-receive"
        hook.write_text("#!/bin/sh\necho synthetic rejection >&2\nexit 1\n")
        hook.chmod(0o700)
        self.assertIs(self.publish(), False)
        self.assertEqual(self.ref(self.remote), self.original_remote)
        self.assertNotEqual(self.git(self.root, "rev-parse", "HEAD").strip(), self.original_remote)

    def test_failed_commit_hook_never_pushes(self):
        hook = self.root / ".git/hooks/pre-commit"
        hook.write_text("#!/bin/sh\nexit 1\n")
        hook.chmod(0o700)
        with patch.object(snapshot, "_snapshot_git", wraps=snapshot._snapshot_git) as calls:
            self.assertIs(self.publish(), False)
            self.assertFalse(any(c.args[1] == "push" for c in calls.call_args_list))
        self.assertEqual(self.ref(self.remote), self.original_remote)

    def test_failed_add_never_commits_or_pushes(self):
        real = snapshot._snapshot_git
        seen = []
        def fail_add(root, *args):
            seen.append(args[0])
            if args[0] == "add":
                raise subprocess.CalledProcessError(1, ["git", "add"])
            return real(root, *args)
        with patch.object(snapshot, "_snapshot_git", side_effect=fail_add):
            self.assertIs(self.publish(), False)
        self.assertNotIn("commit", seen)
        self.assertNotIn("push", seen)
        self.assertEqual(self.ref(self.remote), self.original_remote)

    def test_detached_head_is_refused_before_staging(self):
        self.git(self.root, "checkout", "--detach")
        self.assertIs(self.publish(), False)
        self.assertEqual(self.git(self.root, "diff", "--cached", "--name-only"), b"")
        self.assertEqual(self.ref(self.remote), self.original_remote)

    def test_unrelated_staged_changes_remain_untouched(self):
        f = self.root / "other.txt"
        f.write_text("unrelated\n")
        self.git(self.root, "add", "other.txt")
        before = self.git(self.root, "diff", "--cached", "--binary")
        self.assertIs(self.publish(), False)
        self.assertEqual(self.git(self.root, "diff", "--cached", "--binary"), before)
        self.assertEqual(self.ref(self.remote), self.original_remote)

    def test_push_url_different_from_fetch_url_is_the_readback_target(self):
        other = self.base / "actual-push.git"
        self.git(self.base, "init", "--bare", str(other))
        self.git(self.root, "remote", "set-url", "--push", "origin", str(other))
        self.assertTrue(self.publish())
        self.assertEqual(self.ref(self.remote), self.original_remote)
        self.assertEqual(self.ref(other), self.git(self.root, "rev-parse", "HEAD").strip())

    def test_multiple_push_urls_are_refused_before_staging(self):
        other = self.base / "second.git"
        self.git(self.root, "config", "--add", "remote.origin.pushurl", str(self.remote))
        self.git(self.root, "config", "--add", "remote.origin.pushurl", str(other))
        self.assertIs(self.publish(), False)
        self.assertEqual(self.git(self.root, "diff", "--cached", "--name-only"), b"")
        self.assertEqual(self.ref(self.remote), self.original_remote)

    def test_wrong_remote_readback_never_becomes_true(self):
        real = snapshot._snapshot_git
        def wrong_readback(root, *args):
            if args[0] == "ls-remote":
                return b"0" * 40 + b"\trefs/heads/main\n"
            return real(root, *args)
        with patch.object(snapshot, "_snapshot_git", side_effect=wrong_readback):
            self.assertIs(self.publish(), False)
        # Push did occur; false is verification failure, NOT proof of no effect.
        self.assertNotEqual(self.ref(self.remote), self.original_remote)

    def test_readback_timeout_is_unknown_without_retry(self):
        real = snapshot._snapshot_git
        seen = []
        def timeout(root, *args):
            seen.append(args[0])
            if args[0] == "ls-remote":
                raise subprocess.TimeoutExpired(["git", "ls-remote"], 30)
            return real(root, *args)
        with patch.object(snapshot, "_snapshot_git", side_effect=timeout):
            self.assertIs(self.publish(), False)
        self.assertEqual(seen.count("push"), 1)
        self.assertEqual(seen.count("ls-remote"), 1)

    def test_committed_bytes_mismatch_prevents_push(self):
        real = snapshot._snapshot_git
        seen = []
        def mismatch(root, *args):
            seen.append(args[0])
            if args[0] == "show":
                return b"wrong committed bytes"
            return real(root, *args)
        with patch.object(snapshot, "_snapshot_git", side_effect=mismatch):
            self.assertIs(self.publish(), False)
        self.assertNotIn("push", seen)
        self.assertEqual(self.ref(self.remote), self.original_remote)

    def test_legacy_filename_message_comes_from_json_not_stem(self):
        self.target = self.root / "output/snapshots/snapshot_arbitrary-name.json"
        self.target.write_text(json.dumps(payload("legacy")))
        self.assertTrue(self.publish())
        message = self.git(self.remote, "log", "-1", "--format=%B", "refs/heads/main").decode()
        self.assertIn("2026-10-10 12:00:00", message)
        self.assertIn("legacy-sha256:", message)
        self.assertNotIn("arbitrary-name", message)

    def test_outside_repository_is_refused_without_git_effect(self):
        outside = self.base / "snapshot_outside.json"
        outside.write_text(json.dumps(payload()))
        with patch.object(snapshot, "_snapshot_git") as calls:
            self.assertIs(snapshot.push_snapshot(outside, repo_dir=self.root), False)
            calls.assert_not_called()

    def test_push_failure_without_readback(self):
        real = snapshot._snapshot_git
        seen = []
        def fail_push(root, *args):
            seen.append(args[0])
            if args[0] == "push":
                raise subprocess.CalledProcessError(1, ["git", "push"])
            return real(root, *args)
        with patch.object(snapshot, "_snapshot_git", side_effect=fail_push):
            self.assertIs(self.publish(), False)
        self.assertNotIn("ls-remote", seen)
        self.assertEqual(self.ref(self.remote), self.original_remote)


if __name__ == "__main__":
    unittest.main(verbosity=2)
