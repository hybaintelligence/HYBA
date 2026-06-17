#!/usr/bin/env python3
"""Rollback PYTHIA autonomous mining reflexive state with audit evidence."""
from __future__ import annotations

import argparse
import hashlib
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
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate the rollback state and report what would be restored without writing it",
    )
    args = parser.parse_args()

    controller = AutonomousMiningController(
        RollbackEngineStub(),
        AutonomousConfig(persistence_enabled=True, persistence_dir=args.state_dir),
    )
    if args.dry_run:
        checksum_file = args.state.with_suffix(args.state.suffix + ".sha256")
        if checksum_file.exists():
            expected = checksum_file.read_text(encoding="utf-8").strip()
            actual = hashlib.sha256(args.state.read_bytes()).hexdigest()
            if expected != actual:
                raise ValueError("rollback state checksum mismatch")
        state = json.loads(args.state.read_text(encoding="utf-8"))
        schema_version = int(state.get("schema_version", 1))
        target_schema_version = controller.config.state_schema_version
        if schema_version > target_schema_version:
            raise ValueError(
                f"unsupported rollback state schema {schema_version}; "
                f"controller supports {target_schema_version}"
            )
        controller._load_reflexive_state_locked(args.state)
        result = {
            "dry_run": True,
            "validated": True,
            "state_file": str(args.state),
            "operator_id": args.operator,
            "reason": args.reason,
            "target_state_dir": args.state_dir,
            "schema_version": schema_version,
            "target_schema_version": target_schema_version,
            "schema_migration": (
                "v1_to_v2_in_memory"
                if schema_version == 1 and target_schema_version == 2
                else "not_required"
            ),
            "epochs": controller._self_optimization_epochs,
            "phi_density_history_len": len(controller._phi_density_history),
            "proposals_loaded": len(state.get("proposals", [])),
        }
    else:
        result = controller.rollback_to_state(args.state, args.reason, operator_id=args.operator)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
