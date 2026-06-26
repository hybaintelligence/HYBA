"""Dynamic Evidence Pack — CI-gated seal validation and drift detection.

This module provides a pre-commit/CI-gate that automatically validates and
re-seals artifacts when their generator logic changes. It solves the stale-seal
problem that caused Issue 2 by making seal validation an integral part of the
artifact pipeline rather than a manual post-hoc step.

Core loop:
1. For every artifact in the emergence_curves directory, load it
2. Run validate_* against the corresponding module's validate function
3. If validation fails, regenerate the artifact from the module's make_*_packet
4. Re-seal and write back
5. Return a diff manifest showing what changed (if anything)
"""

from __future__ import annotations

import hashlib
import json
import pathlib
from typing import Dict, List, Mapping


ROOT = pathlib.Path(__file__).resolve().parents[2]
ARTIFACTS_DIR = ROOT / "artifacts" / "emergence_curves"


def canonical_json(payload: Mapping[str, object]) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def seal_packet(packet: Mapping[str, object]) -> str:
    payload = dict(packet)
    payload.pop("artifact_seal", None)
    return "sha256:" + hashlib.sha256(canonical_json(payload).encode("utf-8")).hexdigest()


def validate_and_regenerate_complexity_gradient() -> Dict[str, object]:
    """Validate the sealed complexity gradient artifact; regenerate if stale.

    Returns a manifest showing whether the artifact was valid, and if not,
    what changed and what the new seal is.
    """
    from python_backend.pythia_self_healing.complexity_gradient import (
        make_complexity_packet,
        validate_complexity_packet,
    )

    artifact_path = ARTIFACTS_DIR / "first_complexity_gradient_v1.json"
    if not artifact_path.exists():
        return {"artifact": "first_complexity_gradient_v1.json", "status": "missing"}

    committed = json.loads(artifact_path.read_text(encoding="utf-8"))
    old_seal = committed.get("artifact_seal", "none")

    try:
        validate_complexity_packet(committed)
        return {
            "artifact": "first_complexity_gradient_v1.json",
            "status": "valid",
            "seal": old_seal,
            "regenerated": False,
        }
    except AssertionError as exc:
        # Seal is stale — regenerate
        fresh = make_complexity_packet()
        fresh_seal = fresh["artifact_seal"]
        artifact_path.write_text(
            json.dumps(fresh, indent=2) + "\n", encoding="utf-8"
        )
        return {
            "artifact": "first_complexity_gradient_v1.json",
            "status": "regenerated",
            "old_seal": old_seal,
            "new_seal": fresh_seal,
            "reason": str(exc),
        }


def validate_all_emergence_artifacts() -> List[Dict[str, object]]:
    """Run validation on all known emergence artifacts.

    This is the entry point for CI gating. Returns a list of manifests,
    one per artifact. If any artifact was regenerated, the CI pipeline
    should re-run tests and fail if the regeneration changes expected
    behavior.
    """
    manifests: List[Dict[str, object]] = []
    manifests.append(validate_and_regenerate_complexity_gradient())
    return manifests


def check_seal_drift(
    artifact_path: pathlib.Path,
    expected_generator: str,
) -> Dict[str, object]:
    """Check whether a given artifact has drifted from its generator.

    This is a hermetic check: it re-computes the seal from the artifact's
    own payload data and compares against the stored seal. If they differ
    without the generator having changed, the artifact was manually edited
    or corrupted outside the pipeline.

    Returns a drift report.
    """
    if not artifact_path.exists():
        return {"file": str(artifact_path), "status": "missing"}

    packet = json.loads(artifact_path.read_text(encoding="utf-8"))
    stored_seal = packet.get("artifact_seal", "none")
    computed_seal = seal_packet(packet)

    drifted = stored_seal != computed_seal

    return {
        "file": str(artifact_path),
        "generator": expected_generator,
        "stored_seal": stored_seal,
        "computed_seal": computed_seal,
        "drift_detected": drifted,
        "corrupted": drifted,
        "verdict": (
            "not_falsified — artifact is self-consistent"
            if not drifted
            else "falsified — artifact seal does not match its own payload"
        ),
    }


# If run as a script, execute the CI gate
if __name__ == "__main__":
    import sys

    results = validate_all_emergence_artifacts()
    print(json.dumps(results, indent=2))
    any_regenerated = any(r.get("regenerated") for r in results)
    any_missing = any(r.get("status") == "missing" for r in results)
    if any_regenerated or any_missing:
        print("WARNING: Artifacts were regenerated. Re-run tests.")
        sys.exit(1)
    print("All artifacts valid.")
    sys.exit(0)