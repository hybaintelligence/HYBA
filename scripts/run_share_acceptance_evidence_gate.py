#!/usr/bin/env python3
"""Run the share-acceptance evidence gate.

Default mode is loopback: it verifies the production share-submission spine without
contacting a public pool. Live pool acceptance must be collected by the production
runtime and funding accepted-share gate; this script never fabricates it.
"""

from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict

ROOT = Path(__file__).resolve().parents[1]
ARTIFACT_DIR = ROOT / "artifacts" / "share_acceptance_e2e"


def _run(command: list[str]) -> Dict[str, Any]:
    result = subprocess.run(command, cwd=ROOT, text=True, capture_output=True)
    return {
        "command": command,
        "returncode": result.returncode,
        "stdout_tail": result.stdout[-4000:],
        "stderr_tail": result.stderr[-4000:],
        "passed": result.returncode == 0,
    }


def build_packet() -> Dict[str, Any]:
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    tests = _run(
        [
            sys.executable,
            "-m",
            "pytest",
            "tests/test_hendrix_phi_solver_core.py",
            "tests/test_stratum_share_acceptance_e2e.py",
            "-q",
        ]
    )
    packet: Dict[str, Any] = {
        "schema": "hyba.share_acceptance_e2e.v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "mode": "loopback_transport_evidence",
        "live_pool_claim": "not_asserted_by_this_gate",
        "what_is_verified": [
            "HENDRIX_phi_solver_core_invariants",
            "local_share_validation_before_submission",
            "explicit_live_share_submit_gate",
            "pool_ack_required_before_acceptance_counter",
            "malformed_pool_response_retry",
            "pool_rejection_preserved_as_rejection",
        ],
        "test_result": tests,
        "status": "PASS" if tests["passed"] else "FAIL",
    }
    packet_path = ARTIFACT_DIR / "share_acceptance_e2e_packet.json"
    packet_path.write_text(json.dumps(packet, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return packet


def main() -> int:
    packet = build_packet()
    print(json.dumps(packet, indent=2, sort_keys=True))
    return 0 if packet["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
