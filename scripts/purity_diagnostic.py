#!/usr/bin/env python3
"""
Purity Diagnostic for Bures Convergence

Determines whether the Bures certificate convergence is genuine (structured fixed point)
or trivial (maximally mixed state).
"""

import sys
import numpy as np
from pathlib import Path

ROOT = Path(__file__).resolve().parents[0]
BACKEND = ROOT / "python_backend"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from pythia_mining.pulvini_manifold import PulviniManifold
from pythia_mining.pulvini_bures import bures_certificate
from pythia_mining.pulvini_topology import ADJACENCY_MAP


def main():
    print("=" * 70)
    print("BURES CONVERGENCE PURITY DIAGNOSTIC")
    print("=" * 70)

    # Initialize manifold
    manifold = PulviniManifold(adjacency_map=ADJACENCY_MAP)

    # Get initial density matrix
    rho = manifold.rho.copy()
    n = rho.shape[0]

    print("\nInitial State Analysis:")
    print(f"  Matrix shape: {rho.shape}")
    print(f"  Dimension n: {n}")

    # Compute purity
    purity = np.real(np.trace(rho @ rho))
    print(f"  Purity tr(ρ²) = {purity:.6f}")
    print(f"    [1 = pure state, 1/n = {1 / n:.4f} = maximally mixed]")

    # Compute distance from maximally mixed state
    distance_from_mixed = np.linalg.norm(rho - np.eye(n) / n, "fro")
    print(f"  Distance from maximally mixed: {distance_from_mixed:.6e}")

    # Compute von Neumann entropy
    eigvals = np.linalg.eigvalsh(rho).real
    eigvals = eigvals[eigvals > 1e-15]
    entropy = 0.0 if eigvals.size == 0 else float(-np.sum(eigvals * np.log2(eigvals)))
    print(f"  Von Neumann entropy S(ρ) = {entropy:.6f}")
    print(f"    [0 = pure state, log2(n) = {np.log2(n):.4f} = maximally mixed]")

    # Compute Bures certificate
    cert = bures_certificate(rho, manifold.entropy_gradient)
    print("\nBures Certificate:")
    print(f"  Bures norm: {cert.bures_norm:.6f}")
    print(f"  Tangent norm: {cert.tangent_norm:.6f}")
    print(f"  Stationary: {cert.stationary}")

    # Evolve and check again
    print("\nEvolution Analysis:")
    manifold.evolve_closed_system(dt=0.05)
    rho_evolved = manifold.rho.copy()

    purity_evolved = np.real(np.trace(rho_evolved @ rho_evolved))
    distance_evolved = np.linalg.norm(rho_evolved - np.eye(n) / n, "fro")
    entropy_evolved = manifold.von_neumann_entropy()

    print(f"  Purity after evolution: {purity_evolved:.6f}")
    print(f"  Distance from mixed after evolution: {distance_evolved:.6e}")
    print(f"  Entropy after evolution: {entropy_evolved:.6f}")

    cert_evolved = bures_certificate(rho_evolved, manifold.entropy_gradient)
    print(f"  Bures norm after evolution: {cert_evolved.bures_norm:.6f}")
    print(f"  Stationary after evolution: {cert_evolved.stationary}")

    # Interpretation
    print("\n" + "=" * 70)
    print("INTERPRETATION")
    print("=" * 70)

    purity_threshold = 1.0 / n + 0.01  # Allow small margin

    if purity > purity_threshold:
        print(f"✓ Purity {purity:.6f} > {purity_threshold:.4f}")
        print("  → INTERPRETATION A: Genuine convergence to structured fixed point")
        print("  → The density matrix has converged to a non-trivial attractor")
        print("  → Bures certificate is geometrically meaningful")
    elif abs(purity - 1.0 / n) < 0.01:
        print(f"✗ Purity {purity:.6f} ≈ 1/n = {1 / n:.4f}")
        print("  → INTERPRETATION B: Trivial fixed point (maximally mixed state)")
        print("  → The density matrix has converged to ρ = I/n")
        print("  → Bures convergence is not structurally meaningful")
        print("  → Hamiltonian recalibration may be needed")
    else:
        print(f"⚠ Purity {purity:.6f} is intermediate")
        print("  → Mixed state, but not maximally mixed")
        print("  → Partial convergence - further analysis needed")

    # Check if state is pure
    if abs(purity - 1.0) < 0.01:
        print("\n✓ State is PURE (purity ≈ 1)")
        print("  → Rank-1 density matrix")
        print("  → Single eigenvalue = 1, all others = 0")
    elif abs(purity - 1.0 / n) < 0.01:
        print("\n✗ State is MAXIMALLY MIXED (purity ≈ 1/n)")
        print("  → All eigenvalues equal to 1/n")
        print("  → Maximum entropy state")
    else:
        print("\n⚠ State is MIXED (purity between 1/n and 1)")
        print("  → Rank > 1 density matrix")
        print("  → Partially coherent state")

    print("\n" + "=" * 70)
    print("DIAGNOSTIC COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    main()
