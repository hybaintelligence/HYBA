#!/usr/bin/env python3
"""
Module Isolation Test

Tests pulvini_phi_memory and pulvini_bures_variational modules in isolation
to verify RuntimeWarnings don't reappear independently of the test suite.
"""

import sys
import numpy as np
from pathlib import Path

ROOT = Path(__file__).resolve().parents[0]
BACKEND = ROOT / "python_backend"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

# Enable all warnings to detect any issues
import warnings

warnings.filterwarnings("error")

from pythia_mining.pulvini_phi_memory import PulviniPhiMemoryCompressionEngine
from pythia_mining.pulvini_bures_variational import bures_variational_certificate
from pythia_mining.pulvini_manifold import PulviniManifold
from pythia_mining.pulvini_topology import ADJACENCY_MAP


def test_phi_memory_isolation():
    """Test pulvini_phi_memory module in isolation."""
    print("Testing pulvini_phi_memory module in isolation...")
    try:
        engine = PulviniPhiMemoryCompressionEngine(fold_depth=2)
        test_matrix = np.random.randn(32, 32) + 1j * np.random.randn(32, 32)
        result = engine.compress(test_matrix)
        reconstructed = engine.decompress(result)
        print("✓ pulvini_phi_memory: No RuntimeWarnings")
        return True
    except RuntimeWarning as e:
        print(f"✗ pulvini_phi_memory: RuntimeWarning detected - {e}")
        return False
    except Exception as e:
        print(f"✗ pulvini_phi_memory: Unexpected error - {e}")
        return False


def test_bures_variational_isolation():
    """Test pulvini_bures_variational module in isolation."""
    print("Testing pulvini_bures_variational module in isolation...")
    try:
        manifold = PulviniManifold(adjacency_map=ADJACENCY_MAP)
        cert = bures_variational_certificate(manifold.rho, manifold.entropy_gradient)
        print(
            f"✓ pulvini_bures_variational: No RuntimeWarnings (norm={cert.bures_gradient_norm:.6f})"
        )
        return True
    except RuntimeWarning as e:
        print(f"✗ pulvini_bures_variational: RuntimeWarning detected - {e}")
        return False
    except Exception as e:
        print(f"✗ pulvini_bures_variational: Unexpected error - {e}")
        return False


def main():
    print("=" * 70)
    print("MODULE ISOLATION TEST")
    print("=" * 70)

    phi_result = test_phi_memory_isolation()
    bures_result = test_bures_variational_isolation()

    print("\n" + "=" * 70)
    if phi_result and bures_result:
        print("✓ ALL MODULES CLEAN - No RuntimeWarnings in isolation")
        print("=" * 70)
        return 0
    else:
        print("✗ MODULES HAVE WARNINGS - RuntimeWarnings detected in isolation")
        print("=" * 70)
        return 1


if __name__ == "__main__":
    sys.exit(main())
