#!/usr/bin/env python3
"""Create a local runtime trace packet."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from scripts.phi_resonance_math import forensic_hash

ROOT = Path(__file__).resolve().parents[1]
SCHEMA_VERSION = "hyba.fullstack.runtime_trace.v1"


def read_json(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {"error": "invalid_json", "path": str(path)}


def signed(payload: dict[str, Any]) -> dict[str, Any]:
    result = dict(payload)
    result["forensic_sha256"] = forensic_hash(result)
    return result


def build_packet(root: Path = ROOT) -> dict[str, Any]:
    state = read_json(root / "python_backend" / "pythia_state.json")
    total = int((state or {}).get("total_shares") or 0) if state and "error" not in state else 0
    accepted = int((state or {}).get("accepted_shares") or 0) if state and "error" not in state else 0
    return signed(
        {
            "schema_version": SCHEMA_VERSION,
            "inputs": {
                "pythia_state_present": state is not None,
                "pythia_state_valid": bool(state and "error" not in state),
            },
            "shares": {
                "total": total,
                "accepted": accepted,
                "accepted_present": accepted > 0,
            },
            "runtime": {
                "system_health": (state or {}).get("system_health") if state and "error" not in state else "unavailable",
                "telemetry_source": (state or {}).get("telemetry_source") if state and "error" not in state else "unavailable",
            },
            "claim_level": "share_present" if accepted > 0 else "runtime_trace_no_share_present",
            "boundaries": {
                "changes_production_routes": False,
                "changes_funding_gate": False,
                "changes_docker_entrypoint": False,
            },
        }
    )


def write_packet(output_dir: Path, root: Path = ROOT) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    packet = build_packet(root)
    packet_path = output_dir / "runtime_trace_packet.json"
    packet_path.write_text(json.dumps(packet, indent=2, sort_keys=True), encoding="utf-8")
    manifest = signed(
        {
            "schema_version": f"{SCHEMA_VERSION}.manifest",
            "packet": str(packet_path),
            "packet_sha256": packet["forensic_sha256"],
            "claim_level": packet["claim_level"],
        }
    )
    (output_dir / "runtime_trace_manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8"
    )
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", default="artifacts/runtime_trace")
    args = parser.parse_args()
    print(json.dumps(write_packet(Path(args.output_dir)), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
