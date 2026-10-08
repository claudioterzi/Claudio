import json
import tempfile
import unittest
import subprocess
import sys
from pathlib import Path

from scripts import r3_context_pointer_manifest as pointers


class ContextPointerManifestTests(unittest.TestCase):
    def setUp(self):
        self.manifest = pointers.load_pointer_manifest()

    def test_manifest_identity_and_root_packet(self):
        self.assertEqual(self.manifest["schema"], "R3_CONTEXT_POINTER_MANIFEST_V1")
        packet = pointers.pointer_packet(self.manifest)
        self.assertEqual(packet["content_policy"], "retrieve_source_on_demand")
        self.assertGreater(packet["count"], 0)
        self.assertTrue(all(p["load_mode"] == "root" for p in packet["pointers"]))
        self.assertTrue(all("content" not in p for p in packet["pointers"]))

    def test_task_tags_expand_context_without_inlining_source(self):
        packet = pointers.pointer_packet(self.manifest, tags=["memory"])
        ids = {item["id"] for item in packet["pointers"]}
        self.assertIn("bootstrap", ids)
        self.assertIn("project_memory", ids)
        self.assertIn("learning_watch", ids)
        self.assertTrue(all(set(item) == {"id", "path", "role", "load_mode"} for item in packet["pointers"]))

    def test_selection_is_bounded(self):
        packet = pointers.pointer_packet(
            self.manifest,
            tags=["memory", "autonomy", "architecture", "history", "research"],
            limit=6,
        )
        self.assertLessEqual(packet["count"], 6)

    def test_agent_authority_is_always_in_root_packet(self):
        packet = pointers.pointer_packet(self.manifest)
        paths = {entry["path"] for entry in packet["pointers"]}
        self.assertIn("AGENTS.md", paths)
        self.assertIn("R3_AI_BOOTSTRAP.md", paths)
        self.assertTrue(packet["authority_context_complete"])
        self.assertFalse(packet["promotion_authorized"])

    def test_missing_agents_fails_even_if_remaining_roots_exist(self):
        broken = json.loads(json.dumps(self.manifest))
        broken["entries"] = [e for e in broken["entries"] if e["path"] != "AGENTS.md"]
        with self.assertRaisesRegex(pointers.ContextPointerError, "missing mandatory root"):
            pointers.validate_pointer_manifest(broken, verify_paths=False)

    def test_mandatory_authority_demoted_to_on_demand_is_rejected(self):
        broken = json.loads(json.dumps(self.manifest))
        for entry in broken["entries"]:
            if entry["path"] == "R3_AI_BOOTSTRAP.md":
                entry["load_mode"] = "on_demand"
        with self.assertRaisesRegex(pointers.ContextPointerError, "missing mandatory root"):
            pointers.validate_pointer_manifest(broken, verify_paths=False)

    def test_limit_below_root_count_fails_instead_of_truncating(self):
        root_count = sum(e["load_mode"] == "root" for e in self.manifest["entries"])
        with self.assertRaisesRegex(pointers.ContextPointerError, "silently truncate"):
            pointers.pointer_packet(self.manifest, limit=root_count-1)

    def test_no_root_packet_is_explicitly_not_authority_complete(self):
        packet = pointers.pointer_packet(self.manifest, tags=["continuity"], include_root=False)
        self.assertFalse(packet["authority_context_complete"])
        self.assertFalse(packet["promotion_authorized"])

    def test_symlink_escape_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            sandbox = Path(tmp)
            repo = sandbox / "repo"
            repo.mkdir()
            with tempfile.TemporaryDirectory() as outside:
                outside_file = Path(outside) / "private.txt"
                outside_file.write_text("not repository evidence", encoding="utf-8")
                for entry in self.manifest["entries"]:
                    target = repo / entry["path"]
                    target.parent.mkdir(parents=True, exist_ok=True)
                    target.write_text("public placeholder", encoding="utf-8")
                (repo / self.manifest["entries"][-1]["path"]).unlink()
                (repo / self.manifest["entries"][-1]["path"]).symlink_to(outside_file)
                with self.assertRaisesRegex(pointers.ContextPointerError, "escapes repository"):
                    pointers.validate_pointer_manifest(self.manifest, root=repo)

    def test_direct_cli_exec_from_fresh_process(self):
        path = Path(pointers.__file__).resolve()
        run = subprocess.run(
            [sys.executable, str(path), "--check"], cwd=str(pointers.ROOT),
            capture_output=True, text=True, check=True,
        )
        self.assertTrue(json.loads(run.stdout)["ok"])

    def test_duplicate_id_is_rejected(self):
        broken = json.loads(json.dumps(self.manifest))
        broken["entries"][1]["id"] = broken["entries"][0]["id"]
        with self.assertRaises(pointers.ContextPointerError):
            pointers.validate_pointer_manifest(broken)

    def test_inline_body_is_rejected(self):
        broken = json.loads(json.dumps(self.manifest))
        broken["entries"][0]["content"] = "duplicated source body"
        with self.assertRaises(pointers.ContextPointerError):
            pointers.validate_pointer_manifest(broken)

    def test_missing_target_is_rejected(self):
        broken = {
            "schema": "R3_CONTEXT_POINTER_MANIFEST_V1",
            "protocol_id": "rosso-rosso-rosso/r3-infinity",
            "version": "test",
            "strategy": "pointer_first_bounded_expansion",
            "content_policy": "retrieve_source_on_demand",
            "entries": [{
                "id": "missing",
                "path": "does-not-exist.md",
                "role": "test",
                "load_mode": "root",
                "tags": ["test"],
            }],
        }
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(pointers.ContextPointerError):
                pointers.validate_pointer_manifest(broken, root=Path(tmp))

    def test_repository_escape_is_rejected_without_path_lookup(self):
        broken = json.loads(json.dumps(self.manifest))
        broken["entries"][0]["path"] = "../outside"
        with self.assertRaises(pointers.ContextPointerError):
            pointers.validate_pointer_manifest(broken, verify_paths=False)


if __name__ == "__main__":
    unittest.main()
