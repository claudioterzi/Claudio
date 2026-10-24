"""A red test must stay red in every isolated CI suite."""
import os
from pathlib import Path
import subprocess

import pytest
import yaml


ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github/workflows/ci_security.yml"


def test_ci_preserves_all_component_suites_and_runtime_checks():
    job = yaml.safe_load(WORKFLOW.read_text())["jobs"]["python_tests"]
    assert set(job["strategy"]["matrix"]["suite"]) == {"core", "rrremergen", "bot"}
    assert set(job["strategy"]["matrix"]["python"]) == {"3.11", "3.12"}
    assert not job.get("continue-on-error", False)
    checkout = next(step for step in job["steps"] if step.get("uses", "").startswith("actions/checkout@"))
    assert checkout["with"]["fetch-depth"] == "${{ matrix.suite == 'core' && '0' || '1' }}"
    assert "|| true" not in WORKFLOW.read_text()
    install = next(step for step in job["steps"] if step.get("name") == "Install the suite's declared dependencies")
    assert not install.get("continue-on-error", False)
    assert "python -m pip check" in install["run"]


@pytest.mark.parametrize("suite", ["core", "rrremergen", "bot"])
def test_ci_propagates_test_process_failure(tmp_path, suite):
    job = yaml.safe_load(WORKFLOW.read_text())["jobs"]["python_tests"]
    step = next(step for step in job["steps"] if step.get("name") == "Run all tests in this suite (blocking)")
    assert not step.get("continue-on-error", False)
    # Falsify the workflow shell with a deterministic failing test interpreter.
    interpreter = tmp_path / "python"
    interpreter.write_text("#!/bin/sh\nexit 7\n")
    interpreter.chmod(0o755)
    env = os.environ.copy()
    env.update(SUITE=suite, PATH=str(tmp_path) + os.pathsep + env["PATH"])
    result = subprocess.run(
        ["bash", "-e", "-o", "pipefail", "-c", step["run"]],
        cwd=ROOT, env=env, capture_output=True, text=True, timeout=10,
    )
    assert result.returncode == 7, result.stderr
