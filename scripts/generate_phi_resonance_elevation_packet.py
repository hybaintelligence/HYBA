#!/usr/bin/env python3
"""Generate a replay-stable phi resonance elevation packet."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, Iterable

from scripts.phi_resonance_math import (
    PHI,
    forensic_hash,
    inverse_power_distribution,
    lucas_phi_ratios,
    phi_structured_scoreboard,
    stable_hardware_allocation,
    uniform_noise_scoreboard,
)

SCHEMA_VERSION = "hyba.fullstack.phi_resonance_elevation.v1"


def signed(payload: Dict[str, Any]) -> Dict[str, Any]:
    result = dict(payload)
    result["forensic_sha256"] = forensic_hash(result)
    return result


def build_packet() -> Dict[str, Any]:
    ratios = lucas_phi_ratios(12)
    errors = [abs(value - PHI) for value in ratios]
    structured = phi_structured_scoreboard()
    noise = uniform_noise_scoreboard()
    allocation = stable_hardware_allocation([1.0, 0.62, 0.38, 0.24, 0.15])
    phi_distribution = inverse_power_distribution(PHI, size=13)
    checks = {
        "lucas_converges_to_phi": errors[-1] < 0.001,
        "phi_best_structured_scaler": max(structured, key=structured.get) == "phi",
        "phi_specific_not_noise_magic": max(noise, key=noise.get) == "uniform",
        "distribution_normalized": abs(sum(phi_distribution) - 1.0) < 1e-12,
        "hardware_allocation_stable": abs(sum(allocation) - 1.0) < 1e-12
        and max(allocation) < 0.75,
    }
    return signed(
        {
            "schema_version": SCHEMA_VERSION,
            "phi": PHI,
            "doctrine": {
                "role": "first_class_operational_invariant",
                "not_decorative": True,
                "surfaces": [
                    "scaling",
                    "stability",
                    "search",
                    "memory",
                    "hardware",
                    "resonance",
                ],
            },
            "evidence": {
                "lucas_ratios": ratios,
                "lucas_errors": errors,
                "phi_distribution": phi_distribution,
                "structured_scoreboard": structured,
                "uniform_noise_scoreboard": noise,
                "hardware_allocation": allocation,
            },
            "elevation_checks": checks,
            "all_elevation_checks_pass": all(checks.values()),
            "production_boundary": {
                "funding_runtime_separate": True,
                "changes_production_routes": False,
                "changes_funding_gate": False,
                "changes_docker_entrypoint": False,
            },
        }
    )


def write_packet(output_dir: Path) -> Dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    packet = build_packet()
    packet_path = output_dir / "phi_resonance_elevation_packet.json"
    packet_path.write_text(
        json.dumps(packet, indent=2, sort_keys=True), encoding="utf-8"
    )
    manifest = signed(
        {
            "schema_version": f"{SCHEMA_VERSION}.manifest",
            "packet": str(packet_path),
            "packet_sha256": packet["forensic_sha256"],
            "all_elevation_checks_pass": packet["all_elevation_checks_pass"],
        }
    )
    manifest_path = output_dir / "phi_resonance_elevation_manifest.json"
    manifest_path.write_text(
        json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8"
    )
    return manifest


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", default="artifacts/phi_resonance_elevation")
    args = parser.parse_args(list(argv) if argv is not None else None)
    print(json.dumps(write_packet(Path(args.output_dir)), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
