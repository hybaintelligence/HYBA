"""Zero-touch attestation helpers for mining and benchmark success artifacts.

This module is a generator-side companion to the claim-tier evidence gate and
replay executor. It does not mine, submit shares, contact pools, or certify
external truth. Instead, successful local mining/benchmark code can call it to
emit a manifest-ready claim entry containing the deterministic attestation,
expected replay output digest, and basic falsification route metadata required
by downstream gates and replay probes.
"""

from __future__ import annotations

import sys
from dataclasses import asdict, dataclass
from typing import Any, Mapping, Sequence

from .replay_executor import (
    ReplayCommandResult,
    canonical_replay_output_digest,
    hash_replay_artifacts,
)
from .scientific_rigor_kernel import build_reproducibility_attestation

DEFAULT_MINING_BOUNDARIES = (
    "Local deterministic replay only; not pool-side accepted-share evidence.",
    "No guaranteed mining revenue, pool hashrate, or external validation claim.",
    "No phenomenal consciousness or subjective-experience claim.",
)


@dataclass(frozen=True)
class AutoAttestedMiningManifest:
    """Manifest fragment emitted by mining/benchmark generators."""

    schema: str
    claim: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def emit_attested_mining_success_manifest(
    *,
    claim_id: str,
    claim: str,
    replay_command: str,
    replay_stdout: str,
    inputs: Mapping[str, Any],
    seeds: Mapping[str, int],
    dependency_pins: Mapping[str, str] | None = None,
    produced_artifacts: Sequence[str] = (),
    artifact_root: str | None = None,
    tier: str = "PROTOTYPE_VALIDATED",
    boundaries: Sequence[str] = DEFAULT_MINING_BOUNDARIES,
    falsification_seed_overrides: Mapping[str, int] | None = None,
) -> AutoAttestedMiningManifest:
    """Build a gate-ready manifest fragment for a successful local run.

    The caller supplies the replay command and observed deterministic stdout from
    the successful run. The helper snapshots Python and seed metadata, builds the
    static reproducibility attestation, folds the expected command output into an
    ``expected_output_digest``, and records a basic falsification route for seed
    mutation probes.
    """

    pins = {"python": f"{sys.version_info.major}.{sys.version_info.minor}.*"}
    pins.update(dict(dependency_pins or {}))
    command_result = ReplayCommandResult(
        command=replay_command,
        returncode=0,
        stdout=replay_stdout,
        stderr="",
    )
    artifact_digests = hash_replay_artifacts(produced_artifacts, cwd=artifact_root)
    output_digest = canonical_replay_output_digest([command_result], artifact_digests)
    boundary = " ".join(boundaries)
    attestation = build_reproducibility_attestation(
        claim_id=claim_id,
        inputs=inputs,
        commands=[replay_command],
        seeds=seeds,
        dependency_pins=pins,
        produced_artifacts=produced_artifacts,
        boundary=boundary,
    ).to_dict()
    attestation["inputs"] = dict(inputs)
    attestation["expected_output_digest"] = output_digest
    manifest_claim = {
        "id": claim_id,
        "claim": claim,
        "tier": tier,
        "status": "implemented_and_executable",
        "boundary": boundary,
        "boundaries": list(boundaries),
        "commands": [replay_command],
        "reproducibility_attestation": attestation,
        "falsification_routes": [
            {
                "name": "seed_mutation_negative_control",
                "type": "seed_override",
                "seed_overrides": dict(falsification_seed_overrides or {}),
                "expected": "mutated replay must diverge from expected_output_digest",
            }
        ],
    }
    return AutoAttestedMiningManifest(
        schema="HYBA_AUTO_ATTESTED_MINING_MANIFEST_V1",
        claim=manifest_claim,
    )


__all__ = [
    "AutoAttestedMiningManifest",
    "DEFAULT_MINING_BOUNDARIES",
    "emit_attested_mining_success_manifest",
]
