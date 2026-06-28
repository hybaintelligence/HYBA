"""HYBA Python runtime contract tests.

HYBA defaults to Python 3.12. This test prevents accidental drift back to older
runtime classifiers, workflow pins, or formatter/mypy/ruff targets.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_current_runtime_is_python_312() -> None:
    assert sys.version_info[:2] == (3, 12)


def test_repo_contract_declares_python_312_only() -> None:
    assert _read(".python-version").strip().startswith("3.12")
    assert "FROM python:3.12." in _read("Dockerfile")

    root_pyproject = _read("python_backend/pyproject.toml")

    assert 'requires-python = ">=3.12"' in root_pyproject
    assert 'target-version = ["py312"]' in root_pyproject


def test_workflows_pin_python_312() -> None:
    workflow_paths = [
        ".github/workflows/ci.yml",
        ".github/workflows/production-readiness.yml",
        ".github/workflows/benchmark-ci.yml",
        ".github/workflows/security_scan.yml",
    ]
    for path in workflow_paths:
        text = _read(path)
        assert "3.12" in text, f"workflow must pin Python 3.12: {path}"
        assert "3.11" not in text, f"workflow must not pin Python 3.11: {path}"
        assert "3.10" not in text, f"workflow must not pin Python 3.10: {path}"
        assert "3.9" not in text, f"workflow must not pin Python 3.9: {path}"


def test_active_runtime_files_do_not_reference_legacy_python_targets() -> None:
    active_paths = [
        "python_backend/pyproject.toml",
        ".github/workflows/ci.yml",
        ".github/workflows/production-readiness.yml",
        ".github/workflows/benchmark-ci.yml",
        ".github/workflows/security_scan.yml",
        "python_backend/hyba_genesis_api/core/intelligence_fabric.py",
        "python_backend/pythia_self_healing/autonomous_damage_detector.py",
        "python_backend/pythia_self_healing/salamander_regenerator.py",
        "python_backend/pythia_self_healing/self_healing_reactor.py",
        "python_backend/pythia_agents/__init__.py",
        "python_backend/pythia_agents/pythia_agent_orchestrator.py",
    ]
    legacy_pattern = re.compile(
        r"py3(8|9|10|11)|Python 3\.(8|9|10|11)|python_version = \"3\.(8|9|10|11)\""
    )
    for path in active_paths:
        assert not legacy_pattern.search(
            _read(path)
        ), f"legacy Python target found in {path}"
