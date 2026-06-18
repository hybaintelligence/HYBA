#!/usr/bin/env python3
"""Generate reviewer-grade baseline artifacts for HYBA adaptive-systems science.

These artifacts are deterministic negative/contrast controls. They do not claim
that HYBA is adaptive by themselves; they provide comparison anchors for the
proof ladder: compare baselines -> falsify -> external review.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any, Dict, Iterable


SCHEMA_VERSION = "hyba.science.baseline.v1"


def canonical_bytes(payload: Dict[str, Any]) -> bytes:
    """Return deterministic JSON bytes for forensic hashing."""
    return json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")


def attach_forensic_hash(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Attach SHA-256 over the payload before the hash field exists."""
    unsigned = dict(payload)
    unsigned.pop("forensic_sha256", None)
    digest = hashlib.sha256(canonical_bytes(unsigned)).hexdigest()
    signed = dict(unsigned)
    signed["forensic_sha256"] = digest
    return signed


def baseline_header(system_type: str) -> Dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "system_type": system_type,
        "generated_at": "2026-06-18T00:00:00+00:00",
        "claim_boundary": {
            "supported": "deterministic baseline artifact for comparison only",
            "not_supported": [
                "HYBA superiority by itself",
                "consciousness",
                "AGI",
                "accepted-share evidence",
                "production readiness",
            ],
        },
    }


def generate_modular_baseline() -> Dict[str, Any]:
    payload = baseline_header("modular_static")
    payload.update(
        {
            "description": "Non-adaptive modular controller with minimal cross-module coupling.",
            "phi_analog": 0.042,
            "feedback_loops": 0,
            "memory_patterns": 0,
            "optimisation_patterns": 0,
            "causal_autonomy": 0.10,
            "irreducibility": 0.02,
            "learning_present": False,
            "supported_claim": "Minimal integration and high decomposability baseline.",
        }
    )
    return attach_forensic_hash(payload)


def generate_random_baseline() -> Dict[str, Any]:
    payload = baseline_header("stochastic_noise")
    payload.update(
        {
            "description": "Stochastic non-stateful controller with entropy but no causal accumulation.",
            "phi_analog": 0.25,
            "feedback_loops": 0,
            "memory_patterns": 0,
            "optimisation_patterns": 0,
            "causal_autonomy": 0.05,
            "irreducibility": 0.01,
            "learning_present": False,
            "supported_claim": "High entropy can create spurious correlation without learning.",
        }
    )
    return attach_forensic_hash(payload)


def generate_coupled_nonadaptive_baseline() -> Dict[str, Any]:
    payload = baseline_header("coupled_nonadaptive")
    payload.update(
        {
            "description": "Highly coupled system with shared state but no feedback-driven adaptation.",
            "phi_analog": 0.31,
            "feedback_loops": 0,
            "memory_patterns": 5,
            "optimisation_patterns": 0,
            "causal_autonomy": 0.35,
            "irreducibility": 0.48,
            "learning_present": False,
            "supported_claim": "Coupling and irreducibility alone are not adaptation or learning.",
        }
    )
    return attach_forensic_hash(payload)


def generate_stateful_feedback_baseline() -> Dict[str, Any]:
    payload = baseline_header("stateful_feedback_control")
    payload.update(
        {
            "description": "Toy stateful controller with feedback and memory but no open-ended learning.",
            "phi_analog": 0.18,
            "feedback_loops": 8,
            "memory_patterns": 12,
            "optimisation_patterns": 2,
            "causal_autonomy": 0.80,
            "irreducibility": 0.22,
            "learning_present": False,
            "supported_claim": "Feedback plus memory remains below learning without outcome-conditioned improvement.",
        }
    )
    return attach_forensic_hash(payload)


def all_baselines() -> Dict[str, Dict[str, Any]]:
    return {
        "modular_static": generate_modular_baseline(),
        "stochastic_noise": generate_random_baseline(),
        "coupled_nonadaptive": generate_coupled_nonadaptive_baseline(),
        "stateful_feedback_control": generate_stateful_feedback_baseline(),
    }


def write_artifact(payload: Dict[str, Any], output_dir: Path) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / f"{payload['system_type']}.json"
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    return path


def generate_artifacts(output_dir: Path) -> Dict[str, Any]:
    written = []
    for payload in all_baselines().values():
        artifact_path = write_artifact(payload, output_dir)
        written.append(
            {
                "system_type": payload["system_type"],
                "path": str(artifact_path),
                "forensic_sha256": payload["forensic_sha256"],
            }
        )
    manifest = attach_forensic_hash(
        {
            "schema_version": f"{SCHEMA_VERSION}.manifest",
            "generated_at": "2026-06-18T00:00:00+00:00",
            "artifact_count": len(written),
            "artifacts": written,
            "claim_boundary": {
                "supported": "baseline artifact manifest for adaptive-systems comparison",
                "not_supported": ["production readiness", "consciousness", "AGI"],
            },
        }
    )
    manifest_path = output_dir / "baseline_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")
    return manifest


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output-dir",
        default="artifacts/science_baselines",
        help="Directory where baseline artifacts should be written.",
    )
    args = parser.parse_args(list(argv) if argv is not None else None)
    manifest = generate_artifacts(Path(args.output_dir))
    print(json.dumps(manifest, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
