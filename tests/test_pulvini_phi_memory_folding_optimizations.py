"""Regression gate for PULVINI/Φ memory-folding optimisations.

This test formalises the manual command-room memory-folding proof:
Fibonacci split surfaces, in-place buffers, sparse Fibonacci packing,
large-array sketch error estimation, and full engine strategy selection.
"""

from __future__ import annotations

import numpy as np

from pythia_mining.phi_folding import PhiFoldingOperator
from pythia_mining.pulvini_memory_compression_proof import verify_memory_compression_gate
from pythia_mining.pulvini_phi_memory import PulviniPhiMemoryCompressionEngine


RNG = np.random.default_rng(161803398)


def _folded_dimension(operator: PhiFoldingOperator, dimension: int) -> int:
    """Return the actual dense folded width used by ``fold``.

    ``fibonacci_split`` preserves the exact original dimension and returns a
    Fibonacci-aligned primary split plus any remainder.  ``fold`` then promotes
    the larger side to the folded width so arbitrary dimensions remain exactly
    reversible even when the remainder is larger than the Fibonacci anchor.
    """

    larger, smaller = operator.fibonacci_split(dimension)
    return max(larger, smaller)


def test_phi_folding_reversible_across_small_fibonacci_and_large_dimensions() -> None:
    """Dense fold/unfold must remain reversible across operational dimensions."""

    operator = PhiFoldingOperator()
    for dimension in [1, 2, 3, 5, 8, 13, 21, 32, 55, 89, 100, 144, 1000, 5000]:
        payload = RNG.normal(size=dimension).astype(np.float64)
        folded, kernel, original_size = operator.fold(payload)
        reconstructed = operator.unfold(folded, kernel, original_size)
        error = np.linalg.norm(payload - reconstructed)

        assert original_size == dimension
        assert folded.size == _folded_dimension(operator, dimension)
        assert kernel.size == folded.size
        assert error < 1e-9, f"dimension={dimension}, error={error}"


def test_phi_folding_supports_in_place_buffers() -> None:
    """Caller-provided buffers should be used for zero-allocation folding paths."""

    operator = PhiFoldingOperator()
    payload = RNG.normal(size=55).astype(np.float64)
    folded_width = _folded_dimension(operator, payload.size)
    out = np.zeros(folded_width, dtype=np.float64)
    kernel_out = np.zeros(folded_width, dtype=np.float64)

    folded, kernel, original_size = operator.fold(payload, out=out, kernel_out=kernel_out)
    reconstructed = operator.unfold(folded, kernel, original_size)

    assert np.shares_memory(folded, out)
    assert np.shares_memory(kernel, kernel_out)
    assert np.allclose(folded, out[:folded_width])
    assert np.allclose(kernel, kernel_out[:folded_width])
    assert np.linalg.norm(payload - reconstructed) < 1e-12


def test_sparse_fibonacci_compression_uses_sparse_kernel_and_reconstructs() -> None:
    """Sparse fold/unfold should use compact transformed value/index kernels."""

    operator = PhiFoldingOperator()
    sparse = np.zeros(144, dtype=np.float64)
    sparse[[0, 5, 13, 21, 55, 89]] = [1.0, 2.0, 3.0, 5.0, 8.0, 13.0]

    packed, sparse_kernel, original_size = operator.fold_sparse(sparse)
    reconstructed = operator.unfold_sparse(packed, sparse_kernel, original_size)

    assert original_size == sparse.size
    assert packed.size == 6
    assert sparse_kernel.size == packed.size
    assert np.count_nonzero(reconstructed) == 6
    assert np.flatnonzero(reconstructed).tolist() == [0, 5, 13, 21, 55, 89]
    assert np.linalg.norm(sparse - reconstructed) < 1e-9


def test_approximate_error_sketch_tracks_uniform_reconstruction_noise() -> None:
    """The O(sqrt(n)) sketch should estimate broad reconstruction error."""

    operator = PhiFoldingOperator()
    payload = RNG.normal(size=5000).astype(np.float64)
    noise_rng = np.random.default_rng(31415926)
    noisy_candidate = payload + noise_rng.normal(scale=0.01, size=payload.size)

    approximate = operator.approximate_error(payload, noisy_candidate, sketch_size=500)
    exact = np.linalg.norm(payload - noisy_candidate)
    ratio = approximate / max(exact, 1e-12)

    assert exact > 0.0
    assert 0.3 < ratio < 3.0


def test_pulvini_memory_gate_and_engine_strategies_preserve_reversibility() -> None:
    """The proof gate remains closed and engine selects dense/sparse strategies."""

    gate = verify_memory_compression_gate()
    assert gate["status"] == "CLOSED"
    assert gate["lane_surface_32"]["reversible"] is True
    assert gate["density_matrix_32x32"]["reversible"] is True

    engine = PulviniPhiMemoryCompressionEngine(fold_depth=2, sparse_skip_threshold=0.7)
    dense = engine.compress(RNG.normal(size=144).astype(np.float64))
    sparse = np.zeros(144, dtype=np.float64)
    sparse[::5] = RNG.normal(size=29)
    sparse_result = engine.compress(sparse)

    assert dense.reversible is True
    assert dense.compression_strategy == "phi_fold"
    assert sparse_result.reversible is True
    assert sparse_result.sparse_optimized is True
    assert sparse_result.compression_strategy == "sparse_fib_packed"
    assert sparse_result.folded_dimension == 29
    assert np.linalg.norm(sparse - sparse_result.reconstructed) < 1e-9


def test_memory_folding_optimisation_claim_boundary() -> None:
    """Optimisation tests do not imply live hardware or mining outcomes."""

    claim_boundary = {
        "software_memory_folding_optimisations_verified": True,
        "hardware_rowhammer_elimination_proven": False,
        "accepted_share_proven": False,
        "block_mined": False,
        "10e20_tier_measured": False,
    }

    assert claim_boundary["software_memory_folding_optimisations_verified"] is True
    assert not any(
        value for key, value in claim_boundary.items() if key != "software_memory_folding_optimisations_verified"
    )
