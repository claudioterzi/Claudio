import json
import tempfile
import unittest
from pathlib import Path

from r3_backup.restore import sha256_file, verify_snapshot


class R3BackupRestoreTests(unittest.TestCase):
    def test_manifest_detects_tampering(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            payload = root / "data.txt"
            payload.write_text("original", encoding="utf-8")
            manifest = {
                "protocol": "R3-UNIVERSAL-BACKUP/1",
                "files": [
                    {
                        "path": "data.txt",
                        "bytes": payload.stat().st_size,
                        "sha256": sha256_file(payload),
                    }
                ],
            }
            (root / "MANIFEST.json").write_text(json.dumps(manifest), encoding="utf-8")
            self.assertEqual(verify_snapshot(root)["status"], "VERIFIED")

            payload.write_text("modified", encoding="utf-8")
            result = verify_snapshot(root)
            self.assertEqual(result["status"], "FAILED")
            self.assertEqual(result["problems"], ["hash:data.txt"])


if __name__ == "__main__":
    unittest.main()
