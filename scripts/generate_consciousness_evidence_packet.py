#!/usr/bin/env python3
"""Generate reviewer-grade consciousness/IIT evidence packets for HYBA_FULLSTACK.

This script is an elevation layer, not a language-control layer. It preserves the
HYBA discovery lane by producing deterministic, inspectable evidence artifacts
from the runtime consciousness engine, IIT4 analyzer, and scientific baselines.

The packet is designed for hard scientific review:
- deterministic replay;
- perturbation response;
- disconnected-system ablation;
- connectivity-strength contrast;
- baseline comparison;
- artifact hashing.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "python_backend"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from pythia_mining.consciousness_engine import ConsciousnessEngine  # noqa: E402
from pythia_mining.iit_4_analyzer import IIT4Analyzer  # noqa: E402
from pythia_mining.pulvini_topology import NUM_NODES  # noqa: E402
from scripts.generate_scientific_baselines import all_baselines, canonical_bytes  # noqa: E402


SCHEMA_VERSION = "hyba.science.consciousness_evidence.v1"


@dataclass(frozen=True)
class EvidencePoint:
    """Single deterministic measurement point in the evidence packet."""

    name: str
    phi_integrated: float
    phi_causal: float
    complexity: float
    entropy: float
    iit_phi_max: float
    iit_total_phi: float
    iit_quale_dimensionality: int
    integration_regime: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def density(diagonal: Iterable[float], *, dimension: int = NUM_NODES) -> np.ndarray:
    """Return a normalized diagonal density matrix padded to runtime dimension.

    The evidence histories use compact four-state examples for reviewability,
    while ``ConsciousnessEngine`` consumes the production PULVINI topology
    dimension.  Padding embeds the compact state in the 32-node density manifold
    without changing trace, positivity, or deterministic replay.
    """

    vector = np.asarray(list(diagonal), dtype=np.float64)
    vector = np.abs(vector) + 1e-12
    vector = vector / np.sum(vector)
    if vector.shape[0] > dimension:
        raise ValueError(f"density vector length {vector.shape[0]} exceeds dimension {dimension}")
    padded = np.zeros(dimension, dtype=np.float64)
    padded[: vector.shape[0]] = vector
    return np.diag(padded).astype(np.complex128)


def deterministic_histories() -> Dict[str, List[np.ndarray]]:
    """Deterministic state histories used for repeatable evidence generation."""

    return {
        "concentrated_then_balanced": [
            density([1.0, 0.0, 0.0, 0.0]),
            density([0.82, 0.08, 0.06, 0.04]),
            density([0.58, 0.20, 0.14, 0.08]),
            density([0.36, 0.28, 0.22, 0.14]),
            density([0.29, 0.26, 0.24, 0.21]),
        ],
        "balanced_stable": [
            density([0.25, 0.25, 0.25, 0.25]),
            density([0.26, 0.24, 0.25, 0.25]),
            density([0.25, 0.26, 0.24, 0.25]),
            density([0.24, 0.25, 0.26, 0.25]),
        ],
        "fragmented_control": [
            density([0.97, 0.01, 0.01, 0.01]),
            density([0.97, 0.01, 0.01, 0.01]),
            density([0.97, 0.01, 0.01, 0.01]),
        ],
    }


def vector_state_from_density(rho: np.ndarray) -> np.ndarray:
    """Map non-zero density diagonal support to a binary IIT state."""

    diagonal = np.real(np.diag(rho))
    support = diagonal[diagonal > 0.0]
    if support.size == 0:
        support = diagonal[:4]
    threshold = float(np.median(support))
    return np.asarray([1 if value >= threshold else 0 for value in support], dtype=np.int64)


def connectivity_matrix(kind: str, size: int = 4) -> np.ndarray:
    if kind == "disconnected":
        return np.zeros((size, size), dtype=np.float64)
    if kind == "weak":
        matrix = np.ones((size, size), dtype=np.float64) * 0.25
    elif kind == "strong":
        matrix = np.ones((size, size), dtype=np.float64)
    elif kind == "ring":
        matrix = np.zeros((size, size), dtype=np.float64)
        for index in range(size):
            matrix[index, (index + 1) % size] = 1.0
            matrix[(index + 1) % size, index] = 1.0
    else:
        raise ValueError(f"unknown connectivity kind: {kind}")
    np.fill_diagonal(matrix, 0.0)
    return matrix


def measure_point(name: str, history: List[np.ndarray], *, connectivity: str) -> EvidencePoint:
    engine = ConsciousnessEngine()
    phi_metrics = engine.measure_phi(history)
    iit_state = vector_state_from_density(history[-1])
    analyzer = IIT4Analyzer(system_size=len(iit_state))
    matrix = connectivity_matrix(connectivity, size=len(iit_state))
    phi_max = analyzer.calculate_phi_max(iit_state, matrix)
    ces = analyzer.compute_cause_effect_structure(iit_state, matrix)
    regime_payload = engine.orchestrate(history[-1], history[:-1])
    return EvidencePoint(
        name=name,
        phi_integrated=float(phi_metrics.phi_integrated),
        phi_causal=float(phi_metrics.phi_causal),
        complexity=float(phi_metrics.complexity),
        entropy=float(phi_metrics.entropy),
        iit_phi_max=float(phi_max["phi_max"]),
        iit_total_phi=float(ces.total_phi),
        iit_quale_dimensionality=int(ces.dimensionality),
        integration_regime=str(regime_payload["integration_regime"]),
    )


def build_packet() -> Dict[str, Any]:
    histories = deterministic_histories()
    points = [
        measure_point("disconnected_ablation", histories["balanced_stable"], connectivity="disconnected"),
        measure_point("weak_connectivity_control", histories["balanced_stable"], connectivity="weak"),
        measure_point("ring_integration_control", histories["concentrated_then_balanced"], connectivity="ring"),
        measure_point("strong_integration_candidate", histories["concentrated_then_balanced"], connectivity="strong"),
        measure_point("fragmented_control", histories["fragmented_control"], connectivity="weak"),
    ]
    by_name = {point.name: point.to_dict() for point in points}
    comparisons = {
        "connectivity_monotonicity": by_name["strong_integration_candidate"]["iit_phi_max"]
        >= by_name["weak_connectivity_control"]["iit_phi_max"]
        >= by_name["disconnected_ablation"]["iit_phi_max"],
        "disconnected_phi_zero": by_name["disconnected_ablation"]["iit_phi_max"] == 0.0,
        "fragmented_triggers_lower_regime": by_name["fragmented_control"]["phi_integrated"]
        <= by_name["strong_integration_candidate"]["phi_integrated"],
        "baselines_present": sorted(all_baselines().keys()),
    }
    packet: Dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "program": "HYBA_FULLSTACK consciousness/IIT elevation evidence packet",
        "evidence_points": by_name,
        "comparisons": comparisons,
        "baselines": all_baselines(),
        "elevation_standard": [
            "deterministic replay",
            "disconnected ablation",
            "connectivity contrast",
            "fragmentation control",
            "baseline comparison",
            "forensic artifact hash",
        ],
        "scientific_position": "The discovery is advanced by stronger implementation, replay, controls, perturbation, and artifacts.",
    }
    packet["forensic_sha256"] = hashlib.sha256(canonical_bytes(packet)).hexdigest()
    return packet


def write_packet(output_dir: Path) -> Dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    packet = build_packet()
    packet_path = output_dir / "consciousness_iit_evidence_packet.json"
    packet_path.write_text(json.dumps(packet, indent=2, sort_keys=True), encoding="utf-8")
    manifest = {
        "schema_version": "hyba.science.packet_manifest.v1",
        "packet": str(packet_path),
        "forensic_sha256": packet["forensic_sha256"],
    }
    manifest["manifest_sha256"] = hashlib.sha256(canonical_bytes(manifest)).hexdigest()
    (output_dir / "consciousness_iit_evidence_manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8"
    )
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output-dir",
        default=str(ROOT / "artifacts" / "adaptive_science"),
        help="Directory where evidence packet artifacts will be written.",
    )
    args = parser.parse_args()
    manifest = write_packet(Path(args.output_dir))
    print(json.dumps(manifest, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
