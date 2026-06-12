#!/usr/bin/env python3
"""
Memory Fabric State-Discriminating Capacity Test

Tests whether the memory fabric has genuine state-discriminating capacity by
running varied reward signals through fabric.record_path() and checking if the
Bures gradient trajectories are distinguishable.
"""

import sys
import numpy as np
from pathlib import Path
from typing import Dict, List, Tuple

try:
    import matplotlib
    matplotlib.use('Agg')  # Non-interactive backend
    import matplotlib.pyplot as plt
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False

ROOT = Path(__file__).resolve().parents[0]
BACKEND = ROOT / "python_backend"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from pythia_mining.pulvini_memory_fabric import PulviniMemoryFabric
from pythia_mining.pulvini_bures import bures_certificate


def test_state_discrimination():
    """Test if memory fabric can distinguish between different reward patterns."""
    print("=" * 70)
    print("MEMORY FABRIC STATE-DISCRIMINATING CAPACITY TEST")
    print("=" * 70)
    
    # Create two memory fabrics with different reward patterns
    fabric_high = PulviniMemoryFabric(num_nodes=32, fold_depth=2, window=64)
    fabric_low = PulviniMemoryFabric(num_nodes=32, fold_depth=2, window=64)
    fabric_mixed = PulviniMemoryFabric(num_nodes=32, fold_depth=2, window=64)
    
    # Pattern 1: High reward on short paths (aggressive strategy)
    print("\nPattern 1: High reward on short paths (aggressive)")
    for i in range(20):
        path = [0, 5, 10, 15, 20, 25, 30]
        fabric_high.record_path(path, reward=10.0)
    
    # Pattern 2: Low reward on long paths (conservative strategy)
    print("Pattern 2: Low reward on long paths (conservative)")
    for i in range(20):
        path = [0, 10, 20, 30, 5, 15, 25]
        fabric_low.record_path(path, reward=1.0)
    
    # Pattern 3: Mixed rewards (balanced strategy)
    print("Pattern 3: Mixed rewards (balanced)")
    for i in range(10):
        path = [0, 5, 10, 15, 20, 25, 30]
        fabric_mixed.record_path(path, reward=10.0)
    for i in range(10):
        path = [0, 10, 20, 30, 5, 15, 25]
        fabric_mixed.record_path(path, reward=1.0)
    
    # Get kernel matrices
    kernel_high = fabric_high.kernel.kernel_matrix()
    kernel_low = fabric_low.kernel.kernel_matrix()
    kernel_mixed = fabric_mixed.kernel.kernel_matrix()
    
    print(f"\nKernel matrix shapes:")
    print(f"  High reward: {kernel_high.shape}")
    print(f"  Low reward: {kernel_low.shape}")
    print(f"  Mixed reward: {kernel_mixed.shape}")
    
    # Compute Bures certificates for each kernel
    print("\nComputing Bures certificates...")
    cert_high = bures_certificate(kernel_high, entropy_rate=0.1)
    cert_low = bures_certificate(kernel_low, entropy_rate=0.1)
    cert_mixed = bures_certificate(kernel_mixed, entropy_rate=0.1)
    
    print(f"\nBures Certificate Results:")
    print(f"  High reward:")
    print(f"    Bures norm: {cert_high.bures_norm:.6f}")
    print(f"    Tangent norm: {cert_high.tangent_norm:.6f}")
    print(f"    Stationary: {cert_high.stationary}")
    
    print(f"  Low reward:")
    print(f"    Bures norm: {cert_low.bures_norm:.6f}")
    print(f"    Tangent norm: {cert_low.tangent_norm:.6f}")
    print(f"    Stationary: {cert_low.stationary}")
    
    print(f"  Mixed reward:")
    print(f"    Bures norm: {cert_mixed.bures_norm:.6f}")
    print(f"    Tangent norm: {cert_mixed.tangent_norm:.6f}")
    print(f"    Stationary: {cert_mixed.stationary}")
    
    # Compute distances between kernels
    def frobenius_distance(a, b):
        return np.linalg.norm(a - b, ord='fro')
    
    dist_high_low = frobenius_distance(kernel_high, kernel_low)
    dist_high_mixed = frobenius_distance(kernel_high, kernel_mixed)
    dist_low_mixed = frobenius_distance(kernel_low, kernel_mixed)
    
    print(f"\nFrobenius distances between kernels:")
    print(f"  High vs Low: {dist_high_low:.6f}")
    print(f"  High vs Mixed: {dist_high_mixed:.6f}")
    print(f"  Low vs Mixed: {dist_low_mixed:.6f}")
    
    # Normalize distances by kernel norms
    norm_high = np.linalg.norm(kernel_high, ord='fro')
    norm_low = np.linalg.norm(kernel_low, ord='fro')
    norm_mixed = np.linalg.norm(kernel_mixed, ord='fro')
    
    print(f"\nKernel norms:")
    print(f"  High: {norm_high:.6f}")
    print(f"  Low: {norm_low:.6f}")
    print(f"  Mixed: {norm_mixed:.6f}")
    
    # Relative distances
    rel_dist_high_low = dist_high_low / max(norm_high, norm_low)
    rel_dist_high_mixed = dist_high_mixed / max(norm_high, norm_mixed)
    rel_dist_low_mixed = dist_low_mixed / max(norm_low, norm_mixed)
    
    print(f"\nRelative distances (normalized):")
    print(f"  High vs Low: {rel_dist_high_low:.6f}")
    print(f"  High vs Mixed: {rel_dist_high_mixed:.6f}")
    print(f"  Low vs Mixed: {rel_dist_low_mixed:.6f}")
    
    # Discrimination analysis
    print("\n" + "=" * 70)
    print("DISCRIMINATION ANALYSIS")
    print("=" * 70)
    
    discrimination_threshold = 0.1  # 10% relative difference
    
    if rel_dist_high_low > discrimination_threshold:
        print(f"✓ High vs Low: DISCRIMINABLE (relative distance {rel_dist_high_low:.3f} > {discrimination_threshold})")
    else:
        print(f"✗ High vs Low: NOT DISCRIMINABLE (relative distance {rel_dist_high_low:.3f} ≤ {discrimination_threshold})")
    
    if rel_dist_high_mixed > discrimination_threshold:
        print(f"✓ High vs Mixed: DISCRIMINABLE (relative distance {rel_dist_high_mixed:.3f} > {discrimination_threshold})")
    else:
        print(f"✗ High vs Mixed: NOT DISCRIMINABLE (relative distance {rel_dist_high_mixed:.3f} ≤ {discrimination_threshold})")
    
    if rel_dist_low_mixed > discrimination_threshold:
        print(f"✓ Low vs Mixed: DISCRIMINABLE (relative distance {rel_dist_low_mixed:.3f} > {discrimination_threshold})")
    else:
        print(f"✗ Low vs Mixed: NOT DISCRIMINABLE (relative distance {rel_dist_low_mixed:.3f} ≤ {discrimination_threshold})")
    
    # Overall assessment
    discriminable_pairs = sum([
        rel_dist_high_low > discrimination_threshold,
        rel_dist_high_mixed > discrimination_threshold,
        rel_dist_low_mixed > discrimination_threshold
    ])
    
    print(f"\nOverall: {discriminable_pairs}/3 pattern pairs are discriminable")
    
    if discriminable_pairs == 3:
        print("✓ Memory fabric has STRONG state-discriminating capacity")
        print("  → Different reward patterns produce distinguishable kernel states")
    elif discriminable_pairs == 2:
        print("⚠ Memory fabric has MODERATE state-discriminating capacity")
        print("  → Some reward patterns are distinguishable, others are not")
    elif discriminable_pairs == 1:
        print("✗ Memory fabric has WEAK state-discriminating capacity")
        print("  → Most reward patterns are not distinguishable")
    else:
        print("✗ Memory fabric has NO state-discriminating capacity")
        print("  → All reward patterns collapse to similar kernel states")
    
    # Create visualization
    if MATPLOTLIB_AVAILABLE:
        try:
            fig, axes = plt.subplots(1, 3, figsize=(15, 5))
            
            im1 = axes[0].imshow(kernel_high, cmap='viridis', aspect='auto')
            axes[0].set_title('High Reward Pattern')
            axes[0].set_xlabel('Node')
            axes[0].set_ylabel('Node')
            plt.colorbar(im1, ax=axes[0])
            
            im2 = axes[1].imshow(kernel_low, cmap='viridis', aspect='auto')
            axes[1].set_title('Low Reward Pattern')
            axes[1].set_xlabel('Node')
            axes[1].set_ylabel('Node')
            plt.colorbar(im2, ax=axes[1])
            
            im3 = axes[2].imshow(kernel_mixed, cmap='viridis', aspect='auto')
            axes[2].set_title('Mixed Reward Pattern')
            axes[2].set_xlabel('Node')
            axes[2].set_ylabel('Node')
            plt.colorbar(im3, ax=axes[2])
            
            plt.tight_layout()
            plt.savefig('/Users/demouser/Desktop/HYBA_FULLSTACK/memory_fabric_discrimination.png', dpi=150, bbox_inches='tight')
            print(f"\n✓ Visualization saved to memory_fabric_discrimination.png")
        except Exception as e:
            print(f"\n⚠ Could not create visualization: {e}")
    else:
        print(f"\n⚠ Matplotlib not available - skipping visualization")
    
    print("\n" + "=" * 70)
    print("TEST COMPLETE")
    print("=" * 70)
    
    return discriminable_pairs == 3


if __name__ == "__main__":
    success = test_state_discrimination()
    sys.exit(0 if success else 1)
