"""Fail fast when the local Python test environment is incomplete.

The command-room suite depends on the canonical backend requirements lock. Without
this preflight, ``unittest discover`` reports dozens of noisy import errors. This
script turns that into one actionable dependency message while preserving the
underlying evidence-first gate semantics.
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path
from typing import Dict, List

REQUIRED_IMPORTS: Dict[str, str] = {
    "fastapi": "fastapi",
    "numpy": "numpy",
    "pytest": "pytest",
    "pytest_asyncio": "pytest-asyncio",
    "hypothesis": "hypothesis",
    "argon2": "argon2-cffi",
    "httpx": "httpx",
    "pydantic": "pydantic",
    "email_validator": "email-validator",
    "sqlalchemy": "SQLAlchemy",
    "alembic": "alembic",
}


def missing_imports() -> List[str]:
    return [
        package
        for module, package in REQUIRED_IMPORTS.items()
        if importlib.util.find_spec(module) is None
    ]


def main() -> int:
    missing = missing_imports()
    payload = {
        "status": "ready" if not missing else "missing_dependencies",
        "python_executable": sys.executable,
        "python_version": sys.version.split()[0],
        "required_imports": REQUIRED_IMPORTS,
        "missing_packages": missing,
        "install_command": (
            "python -m pip install -r python_backend/requirements.txt "
            "-r python_backend/requirements.test.txt"
        ),
        "requirements_lock": str(Path("python_backend/requirements.txt")),
        "test_requirements_lock": str(Path("python_backend/requirements.test.txt")),
    }
    print(json.dumps(payload, indent=2, sort_keys=True))
    if missing:
        print(
            "\nPython test environment is incomplete. Activate the intended venv and run:\n"
            "  python -m pip install --upgrade pip\n"
            "  python -m pip install -r python_backend/requirements.txt -r python_backend/requirements.test.txt\n",
            file=sys.stderr,
        )
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
