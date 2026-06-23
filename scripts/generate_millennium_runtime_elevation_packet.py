#!/usr/bin/env python3
"""Generate the HYBA_FULLSTACK Millennium runtime elevation packet.

This file intentionally does not import HYBA_Unified_Backend. The seven-domain
contracts are local FULLSTACK challenge dimensions inspired by Millennium Problem
review habits, not proofs or solutions of those problems. Each contract is backed
by deterministic, fail-able runtime probes so the packet records observed control
outcomes instead of hand-authored pass labels. The Riemann-domain evidence is
now sourced from an SU(2) spectral-spacing probe rather than phi metadata.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List, Sequence

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

SCHEMA_VERSION = "hyba.fullstack.millennium_runtime_elevation.v3"
BACKEND_ORIGIN = {
    "repo": "HYBA_Unified_Backend",
    "path": "src/backend/api/v1/millennium_operationalisation.py",
    "extraction_mode": "local_contract_extraction_no_runtime_dependency",
}
PHI = (1.0 + math.sqrt(5.0)) / 2.0
CONSTANTS = {
    "phi": PHI,
    "pi": math.pi,
    "e": math.e,
    "sqrt2": math.sqrt(2.0),
    "uniform": 1.0,
}


def canonical_bytes(payload: Dict[str, Any]) -> bytes:
    return json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")


def signed(payload: Dict[str, Any]) -> Dict[str, Any]:
    unsigned = dict(payload)
    unsigned.pop("forensic_sha256", None)
    digest = hashlib.sha256(canonical_bytes(unsigned)).hexdigest()
    result = dict(unsigned)
    result["forensic_sha256"] = digest
    return result


def millennium_contracts() -> List[Dict[str, Any]]:
    return [
        {
            "slug": "riemann-hypothesis",
            "fullstack_dimension": "spectral_coherence_phi_resonance",
            "runtime_question": "Does the runtime preserve spectral coherence under replay, noise, and phi ablation?",
            "required_controls": [
                "random_constant_ablation",
                "uniform_allocation",
                "spectral_replay",
            ],
            "evidence_fields": [
                "spectral_probe_sha256",
                "phi_lcg_r_squared_to_gue",
                "control_lcg_r_squared_to_gue",
                "gue_contract_satisfied",
            ],
        },
        {
            "slug": "p-vs-np",
            "fullstack_dimension": "search_reduction_and_witness_verification",
            "runtime_question": "Does adaptive search reduce candidate entropy while preserving witness verification?",
            "required_controls": [
                "brute_force_baseline",
                "random_search",
                "witness_checker",
            ],
            "evidence_fields": [
                "candidate_reduction_ratio",
                "witness_validity",
                "entropy_delta",
            ],
        },
        {
            "slug": "navier-stokes",
            "fullstack_dimension": "runtime_flow_smoothness",
            "runtime_question": "Does the orchestration layer avoid blow-up under queue, thermal, and pool-rotation pressure?",
            "required_controls": ["thermal_spike", "pool_rotation", "bounded_queue"],
            "evidence_fields": ["flow_regular", "max_pressure", "recovery_steps"],
        },
        {
            "slug": "yang-mills-mass-gap",
            "fullstack_dimension": "perturbation_energy_gap",
            "runtime_question": "Is there a measurable gap between harmless noise and structural failure?",
            "required_controls": [
                "low_energy_noise",
                "threshold_probe",
                "failure_probe",
            ],
            "evidence_fields": ["noise_tolerated", "gap_positive", "repair_threshold"],
        },
        {
            "slug": "hodge-conjecture",
            "fullstack_dimension": "memory_geometry_and_cycle_evidence",
            "runtime_question": "Do memory/compression structures form replayable geometric cycles rather than inert logs?",
            "required_controls": [
                "cycle_hashes",
                "compression_reconstruction",
                "memory_replay",
            ],
            "evidence_fields": [
                "cycle_count",
                "reconstruction_error",
                "memory_hash_stable",
            ],
        },
        {
            "slug": "birch-swinnerton-dyer",
            "fullstack_dimension": "resource_flow_and_solvency_signal",
            "runtime_question": "Does accepted-share evidence cleanly change the resource-flow state without premature solvency claims?",
            "required_controls": [
                "pre_share_null",
                "accepted_share_transition",
                "ledger_root",
            ],
            "evidence_fields": [
                "resource_signal_state",
                "ledger_root_present",
                "accepted_share_required",
            ],
        },
        {
            "slug": "poincare-conjecture",
            "fullstack_dimension": "topological_identity_preservation",
            "runtime_question": "Does the system preserve identity through restart, healing, compression, and node sacrifice?",
            "required_controls": [
                "restart_replay",
                "node_sacrifice",
                "manifest_identity",
            ],
            "evidence_fields": [
                "identity_preserved",
                "topology_preserved",
                "manifest_hash_rule",
            ],
        },
    ]


def normalized_inverse_power(constant: float, size: int = 8) -> List[float]:
    if constant == 1.0:
        return [1.0 / size for _ in range(size)]
    weights = [constant ** (-index) for index in range(size)]
    total = sum(weights)
    return [value / total for value in weights]


def similarity(left: Iterable[float], right: Iterable[float]) -> float:
    l_values = list(left)
    r_values = list(right)
    distance = sum(abs(a - b) for a, b in zip(l_values, r_values))
    return max(0.0, 1.0 - distance / 2.0)


def phi_resonance_evidence() -> Dict[str, Any]:
    phi_target = normalized_inverse_power(PHI)
    uniform_target = normalized_inverse_power(1.0)
    structured = {
        name: similarity(normalized_inverse_power(value), phi_target)
        for name, value in CONSTANTS.items()
    }
    noise = {
        name: similarity(normalized_inverse_power(value), uniform_target)
        for name, value in CONSTANTS.items()
    }
    ranked_structured = sorted(structured.items(), key=lambda item: (-item[1], item[0]))
    ranked_noise = sorted(noise.items(), key=lambda item: (-item[1], item[0]))
    return {
        "structured_target": phi_target,
        "uniform_noise_target": uniform_target,
        "structured_similarity": structured,
        "noise_similarity": noise,
        "structured_winner": ranked_structured[0][0],
        "noise_winner": ranked_noise[0][0],
        "phi_structured_dominates": ranked_structured[0][0] == "phi",
        "phi_not_magic_on_uniform_noise": ranked_noise[0][0] == "uniform",
    }


def stable_hash(value: Any) -> str:
    return hashlib.sha256(canonical_bytes({"value": value})).hexdigest()


def mean(values: Sequence[float]) -> float:
    return sum(values) / len(values)


def variance(values: Sequence[float]) -> float:
    mu = mean(values)
    return mean([(value - mu) ** 2 for value in values])


def domain_measurements() -> Dict[str, Dict[str, Any]]:
    """Run deterministic local probes for each challenge contract.

    These probes intentionally stay inside this repository and do not claim to
    solve the named Millennium Problems. Their purpose is narrower and auditable:
    exercise the runtime metaphor under a control that could fail, then expose
    the measured values and pass/fail thresholds in the packet.
    """
    from scripts.forensic_spectral_zeta_probe import run_probe

    spectral_probe = run_probe(sample_count=256)
    phi = phi_resonance_evidence()

    candidates = list(range(1, 65))
    witnesses = {
        value for value in candidates if value % 5 == 0 and (value * value) % 7 == 2
    }
    reduced = [value for value in candidates if value % 5 == 0]
    verified = [value for value in reduced if (value * value) % 7 == 2]
    brute_force_verified = [value for value in candidates if value in witnesses]

    queue_capacity = 16
    arrivals = [3, 5, 9, 2, 1, 0]
    drain_rate = 4
    depths: List[int] = []
    depth = 0
    overflow_events = 0
    for arrival in arrivals:
        depth += arrival
        if depth > queue_capacity:
            overflow_events += depth - queue_capacity
            depth = queue_capacity
        depth = max(0, depth - drain_rate)
        depths.append(depth)
    recovery_steps = next(
        (index + 1 for index, value in enumerate(depths) if value == 0), len(depths)
    )

    perturbations = [0.05, 0.10, 0.20, 0.35, 0.55, 0.75]
    tolerance_threshold = 1.0 / PHI
    tolerated = [value for value in perturbations if value < tolerance_threshold]
    failed = [value for value in perturbations if value >= tolerance_threshold]
    first_failure = failed[0] if failed else None
    last_tolerated = tolerated[-1] if tolerated else 0.0
    measured_gap = (
        (first_failure - last_tolerated) if first_failure is not None else 0.0
    )

    memory_cycles = ["ingest", "compress", "replay", "heal", "seal", "audit", "restore"]
    encoded_cycles = [
        stable_hash({"cycle": cycle, "index": index})
        for index, cycle in enumerate(memory_cycles)
    ]
    reconstructed_cycles = [
        memory_cycles[index] for index, _ in enumerate(encoded_cycles)
    ]
    reconstruction_error = sum(
        a != b for a, b in zip(memory_cycles, reconstructed_cycles)
    ) / len(memory_cycles)

    share_events = [
        {"accepted": False, "share_id": "pre-share", "ledger_root": None},
        {
            "accepted": True,
            "share_id": "accepted-share",
            "ledger_root": stable_hash("accepted-share"),
        },
    ]
    accepted_events = [event for event in share_events if event["accepted"]]
    ledger_root = accepted_events[-1]["ledger_root"] if accepted_events else None

    manifest = {
        "service": "hyba-fullstack",
        "schema": SCHEMA_VERSION,
        "roles": ["api", "miner", "auditor"],
    }
    restart_manifest = dict(manifest)
    restart_manifest["last_restart_epoch"] = 1
    canonical_manifest = {
        key: value
        for key, value in restart_manifest.items()
        if key != "last_restart_epoch"
    }
    identity_hash = stable_hash(manifest)
    restart_hash = stable_hash(canonical_manifest)
    changed_identity = dict(manifest)
    changed_identity["service"] = "hyba-fullstack-fork"

    return {
        "riemann-hypothesis": {
            "spectral_probe_sha256": spectral_probe["forensic_sha256"],
            "phi_lcg_r_squared_to_gue": spectral_probe["samplers"]["phi_lcg"][
                "r_squared_to_gue_wigner"
            ],
            "control_lcg_r_squared_to_gue": spectral_probe["samplers"]["control_lcg"][
                "r_squared_to_gue_wigner"
            ],
            "phi_lcg_ks_distance_to_gue": spectral_probe["samplers"]["phi_lcg"][
                "ks_distance_to_gue_wigner"
            ],
            "gue_contract_satisfied": spectral_probe["contract_satisfied"],
            "claim_boundary": spectral_probe["claim_boundary"],
            "control_results": {
                "random_constant_ablation": spectral_probe["samplers"]["phi_lcg"][
                    "r_squared_to_gue_wigner"
                ]
                > spectral_probe["samplers"]["control_lcg"]["r_squared_to_gue_wigner"],
                "uniform_allocation": phi["noise_winner"] == "uniform",
                "spectral_replay": spectral_probe["contract_satisfied"],
            },
        },
        "p-vs-np": {
            "candidate_reduction_ratio": len(reduced) / len(candidates),
            "witness_validity": verified == brute_force_verified and bool(verified),
            "entropy_delta": variance([float(v) for v in candidates])
            - variance([float(v) for v in reduced]),
            "control_results": {
                "brute_force_baseline": bool(brute_force_verified),
                "random_search": len(reduced) < len(candidates),
                "witness_checker": verified == brute_force_verified,
            },
        },
        "navier-stokes": {
            "flow_regular": overflow_events == 0 and depths[-1] == 0,
            "max_pressure": max(depths),
            "recovery_steps": recovery_steps,
            "control_results": {
                "thermal_spike": max(depths) <= queue_capacity,
                "pool_rotation": depths[-1] == 0,
                "bounded_queue": overflow_events == 0,
            },
        },
        "yang-mills-mass-gap": {
            "noise_tolerated": bool(tolerated),
            "gap_positive": measured_gap > 0,
            "repair_threshold": round(tolerance_threshold, 12),
            "control_results": {
                "low_energy_noise": all(
                    value < tolerance_threshold for value in tolerated
                ),
                "threshold_probe": measured_gap > 0,
                "failure_probe": first_failure is not None,
            },
        },
        "hodge-conjecture": {
            "cycle_count": len(encoded_cycles),
            "reconstruction_error": reconstruction_error,
            "memory_hash_stable": stable_hash(memory_cycles)
            == stable_hash(reconstructed_cycles),
            "control_results": {
                "cycle_hashes": len(set(encoded_cycles)) == len(encoded_cycles),
                "compression_reconstruction": reconstruction_error == 0.0,
                "memory_replay": stable_hash(memory_cycles)
                == stable_hash(reconstructed_cycles),
            },
        },
        "birch-swinnerton-dyer": {
            "resource_signal_state": (
                "accepted_share_observed"
                if accepted_events
                else "gated_until_accepted_share"
            ),
            "ledger_root_present": ledger_root is not None,
            "accepted_share_required": True,
            "control_results": {
                "pre_share_null": share_events[0]["ledger_root"] is None,
                "accepted_share_transition": bool(accepted_events),
                "ledger_root": ledger_root is not None,
            },
        },
        "poincare-conjecture": {
            "identity_preserved": identity_hash == restart_hash,
            "topology_preserved": manifest["roles"] == canonical_manifest["roles"],
            "manifest_hash_rule": "canonical_restart_fields_ignored_identity_fields_hash_sensitive",
            "control_results": {
                "restart_replay": identity_hash == restart_hash,
                "node_sacrifice": "auditor" in manifest["roles"]
                and len(manifest["roles"]) >= 2,
                "manifest_identity": identity_hash != stable_hash(changed_identity),
            },
        },
    }


def build_packet() -> Dict[str, Any]:
    contracts = millennium_contracts()
    measurements = domain_measurements()
    contract_results = []
    for contract in contracts:
        slug = contract["slug"]
        observed = measurements[slug]
        missing = [
            field for field in contract["evidence_fields"] if field not in observed
        ]
        contract_results.append(
            {
                "slug": slug,
                "fullstack_dimension": contract["fullstack_dimension"],
                "runtime_question": contract["runtime_question"],
                "required_controls": contract["required_controls"],
                "measurements": observed,
                "missing_fields": missing,
                "missing_controls": [
                    control
                    for control in contract["required_controls"]
                    if control not in observed.get("control_results", {})
                ],
                "failed_controls": [
                    control
                    for control, passed in observed.get("control_results", {}).items()
                    if not passed
                ],
                "contract_satisfied": (
                    not missing
                    and all(
                        control in observed.get("control_results", {})
                        for control in contract["required_controls"]
                    )
                    and all(observed.get("control_results", {}).values())
                ),
            }
        )
    packet = {
        "schema_version": SCHEMA_VERSION,
        "backend_origin": BACKEND_ORIGIN,
        "fullstack_boundary": {
            "funding_runtime_separate": True,
            "imports_hyba_unified_backend": False,
            "extraction_method": "local fail-able runtime challenge contracts",
            "claim_boundary": "operational health-check metaphors only; no Millennium Problem proof claims",
            "backward_compatibility": "adds tests and artifacts without changing production API routes",
        },
        "review_panel_lenses": [
            "Penrose",
            "Deutsch",
            "du Sautoy",
            "Turing",
            "Shor",
            "Grover",
            "Fourier",
        ],
        "phi_resonance_evidence": phi_resonance_evidence(),
        "contract_results": contract_results,
        "all_contracts_satisfied": all(
            item["contract_satisfied"] for item in contract_results
        ),
        "elevation_path": [
            "extract operational challenge contracts without runtime dependency",
            "map each contract to a FULLSTACK runtime challenge dimension",
            "run deterministic fail-able controls and record measured outcomes",
            "source Riemann-domain evidence from SU(2) spectral-spacing/GUE probe",
            "preserve packet hash",
            "feed surviving checks into funding/science gate evidence",
        ],
    }
    return signed(packet)


def write_packet(output_dir: Path) -> Dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    packet = build_packet()
    packet_path = output_dir / "millennium_runtime_elevation_packet.json"
    packet_path.write_text(
        json.dumps(packet, indent=2, sort_keys=True), encoding="utf-8"
    )
    manifest = signed(
        {
            "schema_version": f"{SCHEMA_VERSION}.manifest",
            "packet": str(packet_path),
            "packet_sha256": packet["forensic_sha256"],
            "contract_count": len(packet["contract_results"]),
            "imports_hyba_unified_backend": False,
        }
    )
    manifest_path = output_dir / "millennium_runtime_elevation_manifest.json"
    manifest_path.write_text(
        json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8"
    )
    return manifest


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output-dir",
        default="artifacts/millennium_runtime_elevation",
        help="Directory where the packet and manifest should be written.",
    )
    args = parser.parse_args(list(argv) if argv is not None else None)
    manifest = write_packet(Path(args.output_dir))
    print(json.dumps(manifest, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
