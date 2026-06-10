import math

from scripts.phi_block_analyser import golden_distance, leading_zero_bits, phi_residue


def test_leading_zero_bits_basic():
    assert leading_zero_bits("1") == 3
    assert leading_zero_bits("8") == 0


def test_phi_residue_is_bounded():
    for value in [0.0, 0.1, 0.5, 1.0, 1.618, 2.618]:
        assert 0.0 <= phi_residue(value) <= 0.5


def test_golden_distance_is_finite_and_bounded():
    for value in [0.0, 0.2, 0.4, 0.6, 0.8, 1.0]:
        distance = golden_distance(value)
        assert math.isfinite(distance)
        assert 0.0 <= distance <= 1.0
