"""Deep invariants for PULVINI memory compression and fabric snapshots."""

from __future__ import annotations

import numpy as np

from pythia_mining.pulvini_memory_fabric import PulviniMemoryFabric
from pythia_mining.pulvini_phi_memory import PulviniPhiMemoryCompressionEngine


def test_phi_memory_compression_reverses_small_dense_matrix() -> None:
    matrix = np.array(
        [
            [0.0, 1.0, 2.0, 3.0],
            [4.0, 5.0, 6.0, 7.0],
            [8.0, 9.0, 10.0, 11.0],
            [12.0, 13.0, 14.0, 15.0],
        ],
        dtype=np.float64,
    )
    engine = PulviniPhiMemoryCompressionEngine(fold_depth=2, tolerance=1e-12)

    result = engine.compress(matrix)
    reconstructed = engine.decompress(result)

    assert result.reversible is True
    assert result.reconstruction_error <= engine.tolerance
    assert result.original_shape == matrix.shape
    assert np.allclose(reconstructed, matrix, atol=1e-12, rtol=0.0)
    assert result.working_set_compression_ratio >= 1.0


def test_memory_fabric_snapshot_exposes_expected_audit_keys() -> None:
    fabric = PulviniMemoryFabric(num_nodes=4, window=8, fold_depth=2, tolerance=1e-12)
    fabric.record_path([0, 1, 2, 3], reward=1.0)
    fabric.record_delta(
        np.array(
            [
                [0.0, 0.5, 0.0, 0.0],
                [0.0, 0.0, 0.25, 0.0],
                [0.0, 0.0, 0.0, 0.125],
                [0.0, 0.0, 0.0, 0.0],
            ],
            dtype=np.float64,
        )
    )

    snapshot = fabric.compressed_kernel_snapshot().to_dict()

    assert set(snapshot) == {"kernel", "compression"}
    assert {"model", "markovian", "kernel_norm", "memory_events", "blocker"}.issubset(
        snapshot["kernel"]
    )
    expected_compression_keys = {
        "original_shape",
        "original_bytes",
        "folded_working_set_bytes",
        "retained_kernel_bytes",
        "working_set_compression_ratio",
        "retained_state_compression_ratio",
        "reconstruction_error",
        "reversible",
        "fold_depth",
        "folded_dimension",
        "input_sparsity",
        "folded_sparsity",
        "kernel_sparsity",
        "input_tail_ratio",
        "folded_tail_ratio",
        "kernel_tail_ratio",
        "heavy_tail_preserved",
        "trace_distance",
        "hermiticity_error",
        "entropy",
        "sizes",
        "compression_strategy",
        "sparse_optimized",
    }
    assert expected_compression_keys.issubset(snapshot["compression"])
    assert snapshot["compression"]["working_set_compression_ratio"] >= 1.0
