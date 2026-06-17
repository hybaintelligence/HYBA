#!/usr/bin/env python3
"""Rollback PYTHIA autonomous mining reflexive state with audit evidence."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
PYTHON_BACKEND = ROOT / "python_backend"
if str(PYTHON_BACKEND) not in sys.path:
    sys.path.insert(0, str(PYTHON_BACKEND))

from pythia_mining.autonomous_mining_controller import AutonomousConfig, AutonomousMiningController  # noqa: E402


class RollbackEngineStub:
    """Minimal engine surface required for state-only rollback."""


def main() -> int:
    parser = argparse.ArgumentParser(description="Rollback autonomous mining reflexive state")
    parser.add_argument("--state", required=True, type=Path, help="State JSON file to restore")
    parser.add_argument("--operator", required=True, help="Operator ID approving rollback")
    parser.add_argument("--reason", required=True, help="Auditable rollback reason")
    parser.add_argument(
        "--state-dir",
        default="artifacts/autonomous_mining",
        help="Autonomy state directory to update",
    )
    args = parser.parse_args()

    controller = AutonomousMiningController(
        RollbackEngineStub(),
        AutonomousConfig(persistence_enabled=True, persistence_dir=args.state_dir),
    )
    result = controller.rollback_to_state(args.state, args.reason, operator_id=args.operator)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
