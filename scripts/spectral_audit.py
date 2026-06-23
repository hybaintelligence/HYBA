#!/usr/bin/env python3
"""
Spectral Audit for PULVINI Density Matrix

Analyzes eigenvalue structure to determine if degenerate eigenspaces are
structural (inherent to icosahedral graph Laplacian) or numerical (accumulated error).
"""

import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[0]
BACKEND = ROOT / "python_backend"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from pythia_mining.pulvini_manifold import PulviniManifold
from pythia_mining.pulvini_phi_memory import PulviniPhiMemoryCompressionEngine
from pythia_mining.pulvini_topology import ADJACENCY_MAP


def spectral_audit(matrix, label):
    """Perform spectral analysis on a matrix."""
    # Handle 1D arrays (compressed representations)
    if matrix.ndim == 1:
        print(f"\n{label}")
        print("  (1D compressed representation - skipping eigenvalue analysis)")
        print(f"  length: {len(matrix)}")
        print(f"  norm: {np.linalg.norm(matrix):.6e}")
        return None, None

    eigvals, eigvecs = np.linalg.eigh(matrix)
    print(f"\n{label}")
    print(f"  λ_min = {eigvals.min():.6e}")
    print(f"  λ_max = {eigvals.max():.6e}")
    print(f"  condition κ = {eigvals.max() / max(abs(eigvals.min()), 1e-300):.6e}")
    print(f"  negative eigenvalues: {(eigvals < 0).sum()}")
    print(f"  near-zero (< 1e-10): {(np.abs(eigvals) < 1e-10).sum()}")
    with np.errstate(divide="ignore", invalid="ignore", over="ignore"):
        vtv_residual = np.max(np.abs(eigvecs.conj().T @ eigvecs - np.eye(len(eigvals))))
    print(f"  V†V residual: {vtv_residual:.2e}")
    print(f"  trace: {np.trace(matrix):.6e}")
    print(f"  rank estimate (σ > 1e-10): {np.sum(np.abs(eigvals) > 1e-10)}")

    # Check for degenerate eigenvalues (multiplicities)
    unique_eigvals = np.unique(np.round(eigvals, decimals=10))
    if len(unique_eigvals) < len(eigvals):
        print(
            f"  degenerate eigenspaces: {len(eigvals) - len(unique_eigvals)} eigenvalues collapsed into {len(unique_eigvals)} unique values"
        )
        multiplicities = []
        for val in unique_eigvals:
            mult = np.sum(np.abs(eigvals - val) < 1e-10)
            if mult > 1:
                multiplicities.append((val, mult))
        if multiplicities:
            print(
                f"  degeneracy details: {[(f'{v:.3e}', m) for v, m in multiplicities]}"
            )

    return eigvals, eigvecs


def main():
    print("=" * 70)
    print("SPECTRAL AUDIT FOR PULVINI DENSITY MATRIX")
    print("=" * 70)

    # Initialize manifold
    manifold = PulviniManifold(adjacency_map=ADJACENCY_MAP)

    # Get initial density matrix (before any operations)
    rho_initial = manifold.rho.copy()
    spectral_audit(rho_initial, "1. Initial Density Matrix (ρ₀)")

    # Evolve the system
    manifold.evolve_closed_system(dt=0.05)
    rho_evolved = manifold.rho.copy()
    spectral_audit(rho_evolved, "2. Evolved Density Matrix (ρ after dt=0.05)")

    # Apply phi-folding compression
    engine = PulviniPhiMemoryCompressionEngine(fold_depth=2)
    compression_result = engine.compress(rho_evolved)

    # Analyze folded representation (may be 1D)
    if hasattr(compression_result, "folded") and compression_result.folded is not None:
        spectral_audit(
            compression_result.folded,
            "3. Folded Density Matrix (compressed representation)",
        )

    # Analyze reconstructed matrix
    rho_reconstructed = engine.decompress(compression_result)
    spectral_audit(
        rho_reconstructed, "4. Reconstructed Density Matrix (after decompression)"
    )

    # Compare reconstruction error
    reconstruction_error = np.linalg.norm(rho_evolved - rho_reconstructed, ord="fro")
    relative_error = reconstruction_error / np.linalg.norm(rho_evolved, ord="fro")

    print("\n" + "=" * 70)
    print("RECONSTRUCTION ANALYSIS")
    print("=" * 70)
    print(f"  Absolute reconstruction error: {reconstruction_error:.6e}")
    print(f"  Relative reconstruction error: {relative_error:.6e}")
    print(
        f"  Reconstruction error from compression result: {compression_result.reconstruction_error or 'N/A'}"
    )
    print(
        f"  Compression ratio: {compression_result.working_set_compression_ratio:.2f}x"
    )

    # Structural interpretation
    print("\n" + "=" * 70)
    print("STRUCTURAL INTERPRETATION")
    print("=" * 70)

    eigvals_initial, _ = spectral_audit(rho_initial, "")
    condition_number = eigvals_initial.max() / max(abs(eigvals_initial.min()), 1e-300)

    if condition_number > 1e10:
        print("  Condition number is HIGH (>1e10)")
        print("  → This suggests ill-conditioned spectrum")
        print("  → For icosahedral adjacency matrices, this is EXPECTED")
        print(
            "  → High-multiplicity eigenspaces correspond to irreducible representations of I_h"
        )
    elif condition_number > 1e6:
        print("  Condition number is MODERATE (1e6-1e10)")
        print("  → Some numerical conditioning issues present")
    else:
        print("  Condition number is LOW (<1e6)")
        print("  → Well-conditioned spectrum")

    if (eigvals_initial < 0).sum() > 0:
        print("  ⚠ Negative eigenvalues detected - violates PSD constraint")
    else:
        print("  ✓ All eigenvalues non-negative - PSD constraint satisfied")

    near_zero_count = (np.abs(eigvals_initial) < 1e-10).sum()
    if near_zero_count > 0:
        print(
            f"  ⚠ {near_zero_count} near-zero eigenvalues - potential rank deficiency"
        )
        print("  → For pure states, this is EXPECTED (rank-1 density matrices)")
    else:
        print("  ✓ No near-zero eigenvalues - full rank matrix")

    print("\n" + "=" * 70)
    print("SPECTRAL AUDIT COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    main()
