"""A fresh sync process must create its log directory before opening the log."""
import os
from pathlib import Path
import subprocess
import sys


def test_fresh_sync_import_creates_nested_data_directory(tmp_path):
    root = Path(__file__).resolve().parents[1]
    data = tmp_path / "new" / "sync"
    env = {**os.environ, "R3_DATA_DIR": str(data), "PYTHONPATH": str(root)}
    result = subprocess.run(
        [sys.executable, "-c", "import r3.sync"], cwd=tmp_path, env=env,
        capture_output=True, text=True, timeout=15,
    )
    assert result.returncode == 0, result.stderr
    assert (data / "sync.log").is_file()
