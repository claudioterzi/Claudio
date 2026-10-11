"""Execute the hosted pytest command against passing and broken local fixtures."""
from __future__ import annotations

import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

import yaml


ROOT = Path(__file__).resolve().parents[1]


class CIFailurePropagationTests(unittest.TestCase):
    def test_coverage_command_preserves_test_and_collection_failures(self):
        workflow = yaml.safe_load((ROOT / ".github/workflows/ci_security.yml").read_text())
        job = workflow["jobs"]["ci_security"]
        self.assertFalse(job.get("continue-on-error", False))
        steps = [step for step in job["steps"]
                 if "coverage run -m pytest" in step.get("run", "")]
        self.assertEqual(len(steps), 1)
        self.assertFalse(steps[0].get("continue-on-error", False))
        cases = {
            "passing": ("def test_ok(): assert True\n", True),
            "assertion_failure": ("def test_broken(): assert False\n", False),
            "collection_failure": ("import r3_intentionally_missing_dependency\n", False),
            "no_tests": (None, False),
        }
        for name, (source, expected_success) in cases.items():
            with self.subTest(case=name), tempfile.TemporaryDirectory() as tmp:
                if source is not None:
                    (Path(tmp) / "test_probe.py").write_text(source)
                env = os.environ.copy()
                env["PATH"] = str(Path(sys.executable).parent) + os.pathsep + env.get("PATH", "")
                # Each probe owns its collection, configuration and coverage data.
                for key in ("PYTEST_ADDOPTS", "PYTEST_PLUGINS", "PYTHONPATH", "COVERAGE_FILE", "COVERAGE_RCFILE"):
                    env.pop(key, None)
                env["PYTEST_DISABLE_PLUGIN_AUTOLOAD"] = "1"
                result = subprocess.run(
                    ["bash", "--noprofile", "--norc", "-eo", "pipefail", "-c", steps[0]["run"]],
                    cwd=tmp, env=env, capture_output=True, text=True, timeout=30,
                )
                self.assertEqual(result.returncode == 0, expected_success,
                                 msg=f"{name}: exit={result.returncode}\n{result.stdout[-2000:]}\n{result.stderr[-1000:]}")


if __name__ == "__main__":
    unittest.main()
