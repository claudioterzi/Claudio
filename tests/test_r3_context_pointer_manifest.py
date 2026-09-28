import json
import tempfile
import unittest
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
            limit=5,
        )
        self.assertLessEqual(packet["count"], 5)

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
