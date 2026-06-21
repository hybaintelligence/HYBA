#!/usr/bin/env python3
"""Forensic SU(2) spectral-spacing probe for the Riemann-domain contract.

This probe does not prove the Riemann Hypothesis or a gauge/zeta theorem. It
measures whether deterministic phi-LCG sampled SU(2) plaquette spectra resemble
the GUE Wigner-surmise nearest-neighbor spacing law more than a control sampler.
The output is intended as falsifiable evidence for a local runtime contract.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List, Literal, Sequence

ROOT = Path(__file__).resolve().parents[1]
PYTHON_BACKEND = ROOT / "python_backend"
if str(PYTHON_BACKEND) not in sys.path:
    sys.path.insert(0, str(PYTHON_BACKEND))


PHI = (1.0 + math.sqrt(5.0)) / 2.0
UINT32 = 2**32
PHI_LCG_STRIDE = 0x9E3779B9
CONTROL_LCG_MULTIPLIER = 1664525
CONTROL_LCG_INCREMENT = 1013904223
DEFAULT_SAMPLE_COUNT = 512
DEFAULT_BINS = 16

SamplerName = Literal["phi_lcg", "control_lcg"]

Matrix2 = List[List[complex]]


def matmul(left: Matrix2, right: Matrix2) -> Matrix2:
    return [
        [
            left[0][0] * right[0][0] + left[0][1] * right[1][0],
            left[0][0] * right[0][1] + left[0][1] * right[1][1],
        ],
        [
            left[1][0] * right[0][0] + left[1][1] * right[1][0],
            left[1][0] * right[0][1] + left[1][1] * right[1][1],
        ],
    ]


def dagger(matrix: Matrix2) -> Matrix2:
    return [
        [matrix[0][0].conjugate(), matrix[1][0].conjugate()],
        [matrix[0][1].conjugate(), matrix[1][1].conjugate()],
    ]


def su2_from_byte(byte: int, axis: int = 0) -> Matrix2:
    theta = float(byte) * (2.0 * math.pi / 255.0)
    c, s = math.cos(theta), math.sin(theta)
    if axis == 0:
        return [[complex(c, 0.0), complex(0.0, s)], [complex(0.0, s), complex(c, 0.0)]]
    if axis == 1:
        return [[complex(c, 0.0), complex(s, 0.0)], [complex(-s, 0.0), complex(c, 0.0)]]
    return [
        [complex(math.cos(theta), math.sin(theta)), 0j],
        [0j, complex(math.cos(theta), -math.sin(theta))],
    ]


def su2_eigenphases(matrix: Matrix2) -> List[float]:
    cos_theta = max(-1.0, min(1.0, ((matrix[0][0] + matrix[1][1]).real / 2.0)))
    theta = math.acos(cos_theta)
    return [theta % (2.0 * math.pi), (-theta) % (2.0 * math.pi)]


def canonical_bytes(payload: Dict[str, Any]) -> bytes:
    return json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")


def forensic_sha256(payload: Dict[str, Any]) -> str:
    return hashlib.sha256(canonical_bytes(payload)).hexdigest()


def nonce_stream(count: int, sampler: SamplerName = "phi_lcg", seed: int = 0xC0DEC0DE) -> List[int]:
    """Return a deterministic nonce stream for the requested sampler."""
    if count < 1:
        raise ValueError("count must be positive")
    state = int(seed) % UINT32
    values: List[int] = []
    for _ in range(int(count)):
        if sampler == "phi_lcg":
            state = (state + PHI_LCG_STRIDE) % UINT32
        elif sampler == "control_lcg":
            state = (CONTROL_LCG_MULTIPLIER * state + CONTROL_LCG_INCREMENT) % UINT32
        else:  # pragma: no cover - protected by Literal at call sites
            raise ValueError(f"unknown sampler: {sampler}")
        values.append(state)
    return values


def su2_plaquette_phases(nonce: int) -> List[float]:
    """Extract sorted eigenphases from the six SU(2) plaquettes induced by a nonce."""
    n = int(nonce) % UINT32
    parts = [(n >> (8 * k)) & 0xFF for k in range(4)]
    axes = [0, 1, 2, 0]
    links = [su2_from_byte(byte, axis=axes[index]) for index, byte in enumerate(parts)]
    phases: List[float] = []
    for left in range(4):
        for right in range(left + 1, 4):
            plaquette = matmul(
                matmul(matmul(links[left], links[right]), dagger(links[left])), dagger(links[right])
            )
            phases.extend(su2_eigenphases(plaquette))
    return sorted(phases)


def unfolded_spacings(phases: Sequence[float]) -> List[float]:
    """Compute unit-mean nearest-neighbor spacings on the phase circle."""
    if len(phases) < 3:
        return []
    ordered = sorted(float(phase) % (2.0 * math.pi) for phase in phases)
    spacings = [ordered[index + 1] - ordered[index] for index in range(len(ordered) - 1)]
    spacings.append((ordered[0] + 2.0 * math.pi) - ordered[-1])
    spacing_mean = sum(spacings) / len(spacings)
    if spacing_mean <= 0.0:
        return []
    return [spacing / spacing_mean for spacing in spacings]


def wigner_gue_pdf(x: float) -> float:
    """GUE Wigner surmise nearest-neighbor spacing density."""
    if x < 0.0:
        return 0.0
    return (32.0 / (math.pi**2)) * (x**2) * math.exp((-4.0 * x * x) / math.pi)


def wigner_gue_cdf(x: float) -> float:
    """Numerically integrate the GUE Wigner surmise CDF on [0, x]."""
    if x <= 0.0:
        return 0.0
    steps = max(32, int(math.ceil(x * 96)))
    width = x / steps
    total = 0.0
    for index in range(steps):
        left = index * width
        right = left + width
        middle = (left + right) / 2.0
        total += (
            (wigner_gue_pdf(left) + 4.0 * wigner_gue_pdf(middle) + wigner_gue_pdf(right))
            * width
            / 6.0
        )
    return min(1.0, total)


def histogram_density(
    values: Sequence[float], bins: int = DEFAULT_BINS, upper: float = 4.0
) -> Dict[str, List[float]]:
    if bins < 4:
        raise ValueError("bins must be at least 4")
    counts = [0 for _ in range(bins)]
    width = upper / bins
    for value in values:
        if 0.0 <= value < upper:
            counts[min(int(value / width), bins - 1)] += 1
    total = sum(counts)
    centers = [(index + 0.5) * width for index in range(bins)]
    densities = [(count / total / width) if total else 0.0 for count in counts]
    return {"centers": centers, "densities": densities}


def r_squared(observed: Sequence[float], expected: Sequence[float]) -> float:
    if len(observed) != len(expected) or not observed:
        return 0.0
    observed_mean = sum(observed) / len(observed)
    ss_tot = sum((value - observed_mean) ** 2 for value in observed)
    ss_res = sum((left - right) ** 2 for left, right in zip(observed, expected))
    if ss_tot <= 0.0:
        return 0.0
    return max(0.0, 1.0 - ss_res / ss_tot)


def ks_distance(values: Sequence[float]) -> float:
    ordered = sorted(values)
    if not ordered:
        return 1.0
    n = len(ordered)
    distance = 0.0
    for index, value in enumerate(ordered, start=1):
        theoretical = wigner_gue_cdf(value)
        empirical_hi = index / n
        empirical_lo = (index - 1) / n
        distance = max(distance, abs(empirical_hi - theoretical), abs(theoretical - empirical_lo))
    return distance


def collect_spacings(count: int, sampler: SamplerName, seed: int = 0xC0DEC0DE) -> List[float]:
    phases: List[float] = []
    for nonce in nonce_stream(count=count, sampler=sampler, seed=seed):
        phases.extend(su2_plaquette_phases(nonce))
    return unfolded_spacings(phases)


def run_probe(
    sample_count: int = DEFAULT_SAMPLE_COUNT,
    bins: int = DEFAULT_BINS,
    seed: int = 0xC0DEC0DE,
    r2_threshold: float = 0.95,
) -> Dict[str, Any]:
    """Run phi-LCG and control spectral probes and return signed evidence."""
    phi_spacings = collect_spacings(sample_count, "phi_lcg", seed=seed)
    control_spacings = collect_spacings(sample_count, "control_lcg", seed=seed)
    phi_hist = histogram_density(phi_spacings, bins=bins)
    control_hist = histogram_density(control_spacings, bins=bins)
    expected = [wigner_gue_pdf(center) for center in phi_hist["centers"]]

    phi_r2 = r_squared(phi_hist["densities"], expected)
    control_r2 = r_squared(control_hist["densities"], expected)
    phi_ks = ks_distance(phi_spacings)
    control_ks = ks_distance(control_spacings)

    unsigned = {
        "schema_version": "hyba.forensic_spectral_zeta_probe.v1",
        "claim_boundary": "SU(2) spectral-spacing runtime evidence only; not a proof of the Riemann Hypothesis or Yang-Mills mass gap",
        "sample_count": sample_count,
        "spacing_count": len(phi_spacings),
        "samplers": {
            "phi_lcg": {
                "stride": PHI_LCG_STRIDE,
                "r_squared_to_gue_wigner": round(phi_r2, 12),
                "ks_distance_to_gue_wigner": round(phi_ks, 12),
            },
            "control_lcg": {
                "multiplier": CONTROL_LCG_MULTIPLIER,
                "increment": CONTROL_LCG_INCREMENT,
                "r_squared_to_gue_wigner": round(control_r2, 12),
                "ks_distance_to_gue_wigner": round(control_ks, 12),
            },
        },
        "thresholds": {
            "r_squared_pass": r2_threshold,
            "requires_phi_beats_control": True,
        },
        "contract_satisfied": bool(phi_r2 >= r2_threshold and phi_r2 > control_r2),
        "histogram": {
            "centers": [round(value, 12) for value in phi_hist["centers"]],
            "phi_lcg_density": [round(value, 12) for value in phi_hist["densities"]],
            "control_lcg_density": [round(value, 12) for value in control_hist["densities"]],
            "gue_wigner_density": [round(value, 12) for value in expected],
        },
    }
    return {**unsigned, "forensic_sha256": forensic_sha256(unsigned)}


def write_probe(
    output: Path, sample_count: int = DEFAULT_SAMPLE_COUNT, bins: int = DEFAULT_BINS
) -> Dict[str, Any]:
    output.parent.mkdir(parents=True, exist_ok=True)
    packet = run_probe(sample_count=sample_count, bins=bins)
    output.write_text(json.dumps(packet, indent=2, sort_keys=True), encoding="utf-8")
    return packet


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sample-count", type=int, default=DEFAULT_SAMPLE_COUNT)
    parser.add_argument("--bins", type=int, default=DEFAULT_BINS)
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("artifacts/forensic_spectral_zeta_probe.json"),
    )
    args = parser.parse_args(list(argv) if argv is not None else None)
    packet = write_probe(args.output, sample_count=args.sample_count, bins=args.bins)
    print(json.dumps(packet, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
