"""Keep the smoke runner on the same declared dependencies as production/CI."""

from pathlib import Path

import yaml


def test_smoke_runner_installs_declared_runtime_and_test_dependencies():
    root = Path(__file__).resolve().parents[1]
    workflow = yaml.safe_load((root / ".github/workflows/test_runner.yml").read_text())
    job = workflow["jobs"]["test"]
    install = next(step for step in job["steps"] if step.get("name") == "Installa dipendenze")
    commands = install["run"]
    assert "python -m pip install -r requirements.txt -r requirements-test.txt" in commands
    assert "python -m pip check" in commands
    assert not install.get("continue-on-error", False)
    requirements = (root / "requirements.txt").read_text()
    assert any(line.startswith("httpx") for line in requirements.splitlines())
