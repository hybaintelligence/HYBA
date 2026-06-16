<<<<<<< Updated upstream
"""Deep invariants for PULVINI memory compression and fabric snapshots."""
=======
"""Tests for Pulvini memory compression and fabric snapshots.

These tests exercise the core invariants of the PULVINI memory engine.  They
check that the phi‐folding compressor produces reversible results for small
payloads and that the memory fabric snapshot exposes the expected audit
information.  The goal is not to maximise branch coverage but to assert
meaningful state and boundary properties about the compression layer.
"""
>>>>>>> Stashed changes

from __future__ import annotations

import numpy as np
<<<<<<< Updated upstream

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
=======
import pytest

from python_backend.pythia_mining.pulvini_memory_fabric import (
    PulviniMemoryFabric,
)
from python_backend.pythia_mining.pulvini_phi_memory import (
    PulviniPhiMemoryCompressionEngine,
)


def test_compress_reversible_on_small_matrix() -> None:
    """Ensure compression of a small matrix is reversible within tolerance.

    The phi folding engine should return a reversible result when fed a
    moderately sized dense matrix.  Reconstruction error should be within
    a small multiple of the engine tolerance and all reconstructed values
    should be within that tolerance of the original.
    """
    rng = np.random.default_rng(seed=12345)
    matrix = rng.random((10, 10))
    engine = PulviniPhiMemoryCompressionEngine()
    result = engine.compress(matrix)
    # The result should indicate reversibility for well formed inputs
    assert result.reversible, "Compression should be reversible for dense matrices"
    # Reconstruction error must be finite and small
    assert np.isfinite(result.reconstruction_error)
    assert result.reconstruction_error <= engine.tolerance * 10
    # The reconstructed matrix should approximate the original
    recon = result.reconstructed
    assert recon.shape == matrix.shape
    assert np.allclose(recon, matrix, atol=engine.tolerance * 10)


def test_memory_fabric_snapshot_invariants() -> None:
    """Check that the memory fabric snapshot contains kernel and compression metadata.

    After recording paths and deltas, a snapshot should expose a kernel
    certificate and a compression dictionary.  The compression dictionary
    should include keys describing the compression ratios, error metrics
    and other state descriptors.  We also assert that the working set
    compression ratio is at least 1.0, reflecting that folding should
    never inflate the working set size.
    """
    fabric = PulviniMemoryFabric(num_nodes=5)
    # Record some activity into the kernel
    fabric.record_path([0, 1, 2], reward=0.5)
    fabric.record_delta(np.eye(5))
    snapshot = fabric.compressed_kernel_snapshot().to_dict()
    # Ensure top level keys exist
    assert "kernel" in snapshot
    assert "compression" in snapshot
    compression = snapshot["compression"]
    # Expected audit keys in the compression result
    expected_keys = {
>>>>>>> Stashed changes
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
<<<<<<< Updated upstream
        "sizes",
        "compression_strategy",
        "sparse_optimized",
    }
    assert expected_compression_keys.issubset(snapshot["compression"])
    assert snapshot["compression"]["working_set_compression_ratio"] >= 1.0
=======
        "compression_strategy",
        "sparse_optimized",
    }
    missing = expected_keys - set(compression.keys())
    assert not missing, f"Missing compression keys: {missing}"
    # Working set compression should not inflate the matrix
    assert compression["working_set_compression_ratio"] >= 1.0
>>>>>>> Stashed changes
