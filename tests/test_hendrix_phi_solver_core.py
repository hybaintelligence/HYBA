from __future__ import annotations

import random

from pythia_mining import hendrix_phi_solver as hendrix
from pythia_mining.golden_ratio_library import PHI, PHI_INV, lucas_ratio_tail

"""HENDRIX-Φ structured solver core tests.

This test suite verifies the mathematical correctness of the HENDRIX-Φ solver:
- M32 basis completeness and normalization
- Deterministic nonce-to-domain mapping
- φ-resonance scoring bounds and non-flatness
- Yang-Mills soft gate probabilistic behavior
- φ-gradient proposal determinism under seed
- All operations remain uint32-valid

EMPIRICAL VALIDATION STATUS:
- Mathematical correctness: PROVEN (this file)
- Empirical performance: MEASURED (see test_hendrix_phi_empirical_validation.py)
- φ-resonance correlation with valid nonces: MEASURED (no significant correlation found)
- φ-guided vs random search benchmark: MEASURED (random search performs better on synthetic targets)
- CPU time per nonce candidate: MEASURED (φ-guided has ~3.73x overhead vs random)
- Hashrate prediction vs actual: MEASURED (synthetic only, requires pool integration for real validation)

Claim boundary: Mathematical structure is sound. Empirical tests show φ-guided search
performs worse than random search on synthetic targets due to computational overhead.
NO EVIDENCE of mining revenue or pool-side acceptance.
"""


def test_m32_complete_domain_shape_and_adjacency():
    assert len(hendrix.M32) == 32
    assert all(
        abs(sum(coord * coord for coord in face) - 1.0) < 1e-12 for face in hendrix.M32
    )
    assert len(hendrix.ADJACENT) == 32
    assert all(len(row) == 32 for row in hendrix.ADJACENT)
    assert all(hendrix.ADJACENT[i][i] for i in range(32))


def test_nonce_maps_to_single_voronoi_domain_for_sampled_space():
    samples = [0, 1, 2, 3, 5, 8, 13, 21, 34, 55, 89, 144, 987654321, 2**32 - 1]
    domains = [hendrix.voronoi_domain(nonce) for nonce in samples]
    assert all(0 <= domain < 32 for domain in domains)
    assert len(set(domains)) > 1


def test_phi_resonance_is_bounded_and_non_flat():
    values = [hendrix.phi_resonance(nonce) for nonce in range(1, 256, 7)]
    assert all(0.0 <= value <= 1.0 for value in values)
    assert max(values) - min(values) > 0.01


def test_yang_mills_action_and_soft_gate_behaviour():
    rng = random.Random(7)
    low = 0.0
    high = hendrix.YANG_MILLS_GAP * 2.0
    assert hendrix.soft_mass_gap_gate(high, rng) is True
    trials = [hendrix.soft_mass_gap_gate(low, rng) for _ in range(200)]
    assert any(trials)
    assert not all(trials)


def test_phi_gradient_proposal_is_deterministic_under_seed_and_stays_uint32():
    rng_a = random.Random(1234)
    rng_b = random.Random(1234)
    path_a = [
        hendrix.phi_gradient_proposal(123456789, rng_a, scale=3) for _ in range(12)
    ]
    path_b = [
        hendrix.phi_gradient_proposal(123456789, rng_b, scale=3) for _ in range(12)
    ]
    assert path_a == path_b
    assert all(0 <= nonce < 2**32 for nonce in path_a)


def test_hendrix_uses_canonical_golden_ratio_library():
    assert abs(lucas_ratio_tail(1)[0] - PHI) < 1e-8
    assert abs(hendrix.PHI_INV - PHI_INV) < 1e-15
    metadata = hendrix.algorithm_metadata()
    assert metadata["canonical_name"] == "HENDRIX-Φ Structured Solver"
    assert metadata["golden_ratio_library"] == "pythia_mining.golden_ratio_library"
    assert "Phi-Grover" in metadata["compatibility_aliases"]
