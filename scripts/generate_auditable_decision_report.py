#!/usr/bin/env python3
"""Generate a PYTHIA auditable-decision report as JSON."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
PYTHON_BACKEND = REPO_ROOT / "python_backend"
if str(PYTHON_BACKEND) not in sys.path:
    sys.path.insert(0, str(PYTHON_BACKEND))

from pythia_mining.auditable_decision_bridge import generate_first_decision_audit_report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, help="Optional path for JSON output")
    parser.add_argument(
        "--adversarial",
        action="store_true",
        help="Emit the adversarial probe report instead of the safe staged report",
    )
    args = parser.parse_args()

    report = generate_first_decision_audit_report(
        adversarial=args.adversarial
    ).to_dict()
    text = json.dumps(report, indent=2, sort_keys=True)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text + "\n", encoding="utf-8")
    print(text)


if __name__ == "__main__":
    main()
