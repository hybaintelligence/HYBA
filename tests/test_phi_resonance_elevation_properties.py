from __future__ import annotations

import hashlib
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.phi_resonance_math import (  # noqa: E402
    PHI,
    canonical_bytes,
    forensic_hash,
    inverse_power_distribution,
    lucas_phi_ratios,
    phi_structured_scoreboard,
    stable_hardware_allocation,
    uniform_noise_scoreboard,
)


def test_lucas_sequence_converges_to_phi() -> None:
    ratios = lucas_phi_ratios(12)
    errors = [abs(value - PHI) for value in ratios]

    assert errors[-1] < 0.001
    assert all(errors[index + 1] <= errors[index] for index in range(2, len(errors) - 1))


def test_phi_dominates_phi_structured_distribution() -> None:
    scores = phi_structured_scoreboard()

    assert max(scores, key=scores.get) == "phi"
    assert scores["phi"] > scores["pi"]
    assert scores["phi"] > scores["e"]
    assert scores["phi"] > scores["sqrt2"]


def test_phi_does_not_dominate_uniform_noise() -> None:
    scores = uniform_noise_scoreboard()

    assert max(scores, key=scores.get) == "uniform"
    assert scores["uniform"] >= scores["phi"]


def test_phi_distribution_is_normalized_bounded_and_non_flat() -> None:
    distribution = inverse_power_distribution(PHI, size=13)

    assert abs(sum(distribution) - 1.0) < 1e-12
    assert all(0.0 <= value <= 1.0 for value in distribution)
    assert distribution[0] > distribution[-1]
    assert len(set(round(value, 12) for value in distribution)) > 3


def test_phi_hardware_allocation_is_stable_and_normalized() -> None:
    allocation = stable_hardware_allocation([1.0, 0.62, 0.38, 0.24, 0.15])

    assert abs(sum(allocation) - 1.0) < 1e-12
    assert max(allocation) < 0.75
    assert allocation[0] > allocation[-1]


def test_phi_hashing_is_replay_stable() -> None:
    payload = {
        "phi": PHI,
        "structured": phi_structured_scoreboard(),
        "noise": uniform_noise_scoreboard(),
        "allocation": stable_hardware_allocation([1.0, 0.62, 0.38, 0.24, 0.15]),
    }

    digest = forensic_hash(payload)
    assert digest == hashlib.sha256(canonical_bytes(payload)).hexdigest()
    assert digest == forensic_hash(dict(reversed(list(payload.items()))))
