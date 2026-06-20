#!/usr/bin/env python3
"""Run local-first security checks for HYBA_FULLSTACK.

This script does not require GitHub Actions, hosted CI, or paid tooling. It runs
available local security scanners and records gaps when optional tools are not
installed, so the operator gets an auditable local transcript rather than a
silent pass.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "runtime" / "evidence" / "security_scans"


def _run(label: str, command: list[str]) -> dict[str, object]:
    executable = command[0]
    if shutil.which(executable) is None:
        return {
            "label": label,
            "command": command,
            "status": "skipped",
            "reason": f"{executable} is not installed on this local machine",
        }
    completed = subprocess.run(command, cwd=ROOT, text=True, capture_output=True)
    return {
        "label": label,
        "command": command,
        "status": "passed" if completed.returncode == 0 else "failed",
        "returncode": completed.returncode,
        "stdout": completed.stdout[-8000:],
        "stderr": completed.stderr[-8000:],
    }


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H-%M-%SZ")
    transcript_path = OUT_DIR / f"{stamp}.json"

    checks = [
        _run("secret hygiene", [sys.executable, "scripts/check_secret_hygiene.py"]),
        _run("forensic closure", [sys.executable, "scripts/check_forensic_gap_closure.py"]),
        _run("npm audit", ["npm", "audit", "--omit=dev"]),
        _run("pip-audit", ["pip-audit", "-r", "requirements.txt"]),
    ]
    report = {
        "schema": "HYBA_LOCAL_SECURITY_SCAN_V1",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "requires_ci": False,
        "checks": checks,
    }
    transcript_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")

    failed = [check for check in checks if check["status"] == "failed"]
    skipped = [check for check in checks if check["status"] == "skipped"]

    print(f"security transcript: {transcript_path.relative_to(ROOT)}")
    if skipped:
        print("optional scanners skipped:")
        for check in skipped:
            print(f"- {check['label']}: {check.get('reason')}")
    if failed:
        print("local security scan failed:", file=sys.stderr)
        for check in failed:
            print(f"- {check['label']}", file=sys.stderr)
        return 1
    print("local security scan passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
