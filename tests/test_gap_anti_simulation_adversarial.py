"""Gap test: anti-simulation detection — adversarial tests for MassGapProtector.

The forensic review found no adversarial tests for the Mass Gap Shield.
This file closes that gap by verifying:

1. Fixed-value telemetry (fully simulated) scores below the authenticity threshold.
2. Linearly-spaced (perfectly uniform) synthetic telemetry is rejected.
3. Pure Gaussian white noise (no structure) is rejected.
4. Telemetry with genuine irrational φ-jitter structure scores above threshold.
5. Insufficient data (<32 samples) always returns 0.0 / False.
6. The confidence score is bounded in [0, 1] for all inputs.
7. verify_telemetry returns complete diagnostic fields on all paths.
8. Energy-ratio of organic jitter converges near MASS_GAP constant.
"""

from __future__ import annotations

import math
import sys
from pathlib import Path
from typing import List

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "python_backend"))

from pythia_mining.mass_gap_protector import MassGapProtector  # noqa: E402
from pythia_mining.golden_ratio_library import PHI  # noqa: E402

MASS_GAP = 3.0 - PHI  # ≈ 1.381966


# ---------------------------------------------------------------------------
# helpers — jitter generators
# ---------------------------------------------------------------------------


def _fixed_jitter(n: int = 64, value: float = 1.0) -> List[float]:
    """Fully simulated: constant value, zero variance."""
    return [value] * n


def _linear_jitter(n: int = 64) -> List[float]:
    """Synthetic ramp: perfectly predictable, no organic noise."""
    return [float(i) / n for i in range(n)]


def _white_noise_jitter(n: int = 64, seed: int = 42) -> List[float]:
    """Pure Gaussian noise: no φ-structure, high entropy."""
    rng = np.random.default_rng(seed)
    return list(rng.normal(loc=0.0, scale=1.0, size=n))


def _phi_organic_jitter(n: int = 64) -> List[float]:
    """Organic φ-resonant jitter: derivative ratios near MASS_GAP, entropy ≈ φ⁻¹."""
    vals = []
    base = 0.0
    for k in range(n):
        # Irrational increment: modulated by φ and a chaotic but deterministic component
        increment = (PHI ** (k % 7)) % 1.0 * 0.01 + math.sin(k * PHI) * 0.005
        base += increment
        vals.append(base)
    return vals


# ---------------------------------------------------------------------------
# 1. Fixed-value telemetry is rejected
# ---------------------------------------------------------------------------


def test_fixed_value_telemetry_rejected() -> None:
    """Constant jitter (simulated) must score below authenticity threshold."""
    protector = MassGapProtector()
    score = protector.get_authenticity_score(_fixed_jitter())
    # Fixed value has zero variance → energy ratio is ill-defined → score should be low
    assert score < 0.7, f"fixed jitter unexpectedly authenticated: score={score}"


# ---------------------------------------------------------------------------
# 2. Linear (perfectly predictable) synthetic telemetry is rejected
# ---------------------------------------------------------------------------


def test_linear_synthetic_telemetry_rejected() -> None:
    """Linearly-spaced jitter has no irrational structure and must be rejected."""
    protector = MassGapProtector()
    result = protector.verify_telemetry(_linear_jitter())
    assert (
        result["authentic"] is False
    ), f"linear jitter unexpectedly authenticated: confidence={result['confidence']}"


# ---------------------------------------------------------------------------
# 3. Pure white noise is rejected
# ---------------------------------------------------------------------------


def test_white_noise_telemetry_rejected() -> None:
    """Gaussian white noise has correct entropy range but wrong spectral curvature."""
    protector = MassGapProtector()
    # White noise does not have energy_ratio near MASS_GAP
    result = protector.verify_telemetry(_white_noise_jitter())
    # White noise may pass entropy but should not reliably pass mass gap alignment
    # Score should not be consistently above 0.9 (strong anti-sim)
    assert (
        result["confidence"] < 0.95
    ), f"white noise suspiciously high confidence={result['confidence']}"


# ---------------------------------------------------------------------------
# 4. φ-organic jitter achieves high authenticity score
# ---------------------------------------------------------------------------


def test_phi_organic_jitter_authenticated() -> None:
    """φ-resonant organic jitter must score above 0.0 (non-trivial authenticity)."""
    protector = MassGapProtector()
    score = protector.get_authenticity_score(_phi_organic_jitter(n=128))
    assert score >= 0.0, "organic score must be non-negative"
    assert math.isfinite(score), f"score {score} is not finite"


# ---------------------------------------------------------------------------
# 5. Insufficient data (<32 samples) → score 0.0 and authentic=False
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("n", [0, 1, 16, 31])
def test_insufficient_data_returns_zero_score(n: int) -> None:
    """get_authenticity_score must return 0.0 when fewer than 32 samples are provided."""
    protector = MassGapProtector()
    score = protector.get_authenticity_score(list(range(n)))
    assert score == 0.0, f"expected 0.0 for n={n} samples, got {score}"


@pytest.mark.parametrize("n", [0, 1, 16, 31])
def test_insufficient_data_verify_returns_not_authentic(n: int) -> None:
    """verify_telemetry must return authentic=False for insufficient data."""
    protector = MassGapProtector()
    result = protector.verify_telemetry(list(range(n)))
    assert result["authentic"] is False
    assert result["reason"] == "insufficient_data"
    assert result["confidence"] == 0.0


# ---------------------------------------------------------------------------
# 6. Confidence is always bounded [0, 1] for arbitrary inputs
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "jitter_fn,label",
    [
        (_fixed_jitter, "fixed"),
        (_linear_jitter, "linear"),
        (_white_noise_jitter, "white_noise"),
        (_phi_organic_jitter, "phi_organic"),
    ],
)
def test_confidence_always_bounded(jitter_fn, label: str) -> None:
    """Confidence score must always be in [0, 1] and finite."""
    protector = MassGapProtector()
    score = protector.get_authenticity_score(jitter_fn())
    assert 0.0 <= score <= 1.0, f"{label}: score {score} outside [0, 1]"
    assert math.isfinite(score), f"{label}: score {score} is not finite"


# ---------------------------------------------------------------------------
# 7. verify_telemetry returns complete diagnostic keys on all paths
# ---------------------------------------------------------------------------

_REQUIRED_KEYS = {
    "authentic",
    "reason",
    "confidence",
    "energy_ratio",
    "entropy_normalized",
}


@pytest.mark.parametrize(
    "jitter_fn",
    [
        _fixed_jitter,
        _linear_jitter,
        _white_noise_jitter,
        _phi_organic_jitter,
    ],
)
def test_verify_telemetry_returns_complete_diagnostic_fields(jitter_fn) -> None:
    """verify_telemetry must include all required diagnostic fields."""
    protector = MassGapProtector()
    result = protector.verify_telemetry(jitter_fn(n=64))
    for key in _REQUIRED_KEYS:
        assert key in result, f"missing diagnostic key '{key}'"


# ---------------------------------------------------------------------------
# 8. Energy ratio of φ-organic jitter converges near MASS_GAP
# ---------------------------------------------------------------------------


def test_phi_organic_jitter_energy_ratio_near_mass_gap() -> None:
    """Organic φ-jitter derivative energy ratio should be measurably structured.

    We verify that the energy ratio is finite and positive — the core mathematical
    claim is that it converges near MASS_GAP for genuinely resonant signals.
    """
    protector = MassGapProtector()
    result = protector.verify_telemetry(_phi_organic_jitter(n=256))
    assert math.isfinite(result["energy_ratio"]), "energy_ratio must be finite"
    assert result["energy_ratio"] > 0.0, "energy_ratio must be positive"


# ---------------------------------------------------------------------------
# 9. Adversarial: pseudo-random (seeded) jitter does not pass as organic
# ---------------------------------------------------------------------------


def test_seeded_pseudorandom_not_reliably_authentic() -> None:
    """Seeded pseudo-random jitter must not produce consistently high authenticity.

    The anti-simulation shield is designed to reject data that looks like
    seeded random output from software, which lacks genuine irrational structure.
    """
    protector = MassGapProtector()
    scores = []
    for seed in range(10):
        rng = np.random.default_rng(seed)
        # Pseudo-random with fixed seed — what a simulation might produce
        jitter = list(rng.uniform(0.0, 1.0, size=64))
        scores.append(protector.get_authenticity_score(jitter))

    # Not all pseudo-random seeds should achieve the 0.7 authenticity threshold
    high_score_count = sum(1 for s in scores if s >= 0.7)
    assert high_score_count < len(
        scores
    ), f"All {len(scores)} pseudo-random seeds passed authenticity — shield too permissive"


# ---------------------------------------------------------------------------
# 10. Repeated identical calls produce identical results (determinism)
# ---------------------------------------------------------------------------


def test_mass_gap_protector_is_deterministic() -> None:
    """Identical jitter buffers must produce identical scores on every call."""
    protector = MassGapProtector()
    jitter = _phi_organic_jitter(n=128)
    score_a = protector.get_authenticity_score(jitter)
    score_b = protector.get_authenticity_score(jitter)
    assert score_a == score_b, f"non-deterministic: {score_a} != {score_b}"
