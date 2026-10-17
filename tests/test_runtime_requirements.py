"""Prevent Vercel's shared Python environment from pruning earlier functions."""

import json
import os
import subprocess
from pathlib import Path

import pytest
import yaml
from packaging.requirements import Requirement
from packaging.utils import canonicalize_name

ROOT = Path(__file__).resolve().parents[1]
CANONICAL = ROOT / "requirements.txt"


def nearest_requirements(entrypoint):
    """Find the requirements manifest selected for these Python entrypoints."""
    directory = entrypoint.parent
    while directory.is_relative_to(ROOT):
        # A new dependency format needs its own builder regression review.
        alternate_manifests = (
            "pyproject.toml", "Pipfile", "Pipfile.lock", "requirements.frozen.txt",
            "requirements-frozen.txt", "requirements.in", "requirements/prod.txt",
            "uv.lock", "pylock.toml", "uv.toml",
        )
        for filename in alternate_manifests:
            assert not (directory / filename).exists(), directory / filename
        manifest = directory / "requirements.txt"
        if manifest.exists():
            return manifest
        if directory == ROOT:
            break
        directory = directory.parent
    raise AssertionError(f"No runtime manifest for {entrypoint}")


def direct_requirements(text):
    requirements = {}
    for line in text.splitlines():
        entry = line.split("#", 1)[0].strip()
        if not entry:
            continue
        # The production builder discovery path cannot resolve -r/-c includes.
        assert not entry.startswith("-"), f"Unsupported builder directive: {entry}"
        requirement = Requirement(entry)
        name = canonicalize_name(requirement.name)
        assert name not in requirements, f"Duplicate runtime dependency: {name}"
        requirements[name] = requirement
    return requirements


def test_all_python_builds_select_the_same_runtime_dependencies():
    builds = json.loads((ROOT / "vercel.json").read_text())["builds"]
    python_builds = [build for build in builds if build["use"].startswith("@vercel/python")]
    assert python_builds, "No Python functions were checked"
    for build in python_builds:
        source = ROOT / build["src"]
        assert source.is_file(), source
        manifest = nearest_requirements(source)
        assert manifest.read_bytes() == CANONICAL.read_bytes(), (
            f"{build['src']} selects {manifest.relative_to(ROOT)} with divergent "
            "dependencies; shared uv sync can delete earlier function files"
        )


def test_canonical_runtime_has_only_unique_direct_requirements():
    requirements = direct_requirements(CANONICAL.read_text())
    # Protect both application families, rather than solving pruning by dropping one.
    assert {"flask", "pillow", "pyyaml", "redis", "google-genai"} <= requirements.keys()
    assert {"fastapi", "mistralai", "google-generativeai", "sqlalchemy", "pymongo"} <= requirements.keys()


@pytest.mark.parametrize("directive", ["-r other.txt", "--requirement other.txt", "-c constraints.txt"])
def test_dependency_parser_rejects_unresolved_file_directives(directive):
    with pytest.raises(AssertionError, match="Unsupported builder directive"):
        direct_requirements(directive)


def test_dependency_parser_rejects_duplicate_package_names():
    with pytest.raises(AssertionError, match="Duplicate runtime dependency"):
        direct_requirements("SQLAlchemy==2.0.0\nsqlalchemy>=2\n")


@pytest.mark.parametrize("filename", [
    "pyproject.toml", "Pipfile", "Pipfile.lock", "requirements.frozen.txt",
    "requirements-frozen.txt", "requirements.in", "requirements/prod.txt",
    "uv.lock", "pylock.toml", "uv.toml",
])
def test_manifest_discovery_rejects_alternative_nearer_formats(tmp_path, monkeypatch, filename):
    monkeypatch.setattr(f"{__name__}.ROOT", tmp_path)
    (tmp_path / "requirements.txt").write_text("flask>=3\n")
    source = tmp_path / "api" / "handler.py"
    source.parent.mkdir()
    source.write_text("app = None\n")
    alternate = source.parent / filename
    alternate.parent.mkdir(parents=True, exist_ok=True)
    alternate.write_text("# A separately reviewed dependency format\n")
    with pytest.raises(AssertionError):
        nearest_requirements(source)


def test_packaging_workflow_is_blocking_and_propagates_failure(tmp_path):
    workflow = yaml.safe_load((ROOT / ".github/workflows/ci_security.yml").read_text())
    job = workflow["jobs"]["vercel_python_packaging"]
    assert not job.get("continue-on-error", False)
    assert job["timeout-minutes"] <= 20
    step = next(s for s in job["steps"] if s.get("name", "").endswith("(blocking)"))
    assert not step.get("continue-on-error", False)
    node = tmp_path / "node"
    node.write_text("#!/bin/sh\nexit 7\n")
    node.chmod(0o755)
    env = os.environ.copy()
    env.update(PATH=str(tmp_path) + os.pathsep + env["PATH"],
               RUNNER_TEMP=str(tmp_path), GITHUB_WORKSPACE=str(ROOT))
    result = subprocess.run(
        ["bash", "-e", "-o", "pipefail", "-c", step["run"]],
        cwd=ROOT, env=env, capture_output=True, text=True, timeout=10, check=False,
    )
    assert result.returncode == 7, result.stderr
