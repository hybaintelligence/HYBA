#!/usr/bin/env python3
"""
Quick 100-block Φ^15 empirical evidence collection.
Usage: python scripts/collect_100_blocks.py
"""

import sys
from pathlib import Path

# Add repo root to path
REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from phi_resonance_empirical_evidence import run_pipeline

if __name__ == "__main__":
    print("=" * 70)
    print("  HYBA Φ^15 Empirical Evidence - 100 Block Sample")
    print("=" * 70)
    print()
    print("Collecting 100 recent Bitcoin blocks...")
    print("This will take ~10 seconds (0.1s delay per block)")
    print()

    exit_code = run_pipeline(
        api="https://blockstream.info/api",
        block_count=100,
        start_height=None,  # Use chain tip
        delay=0.1,  # 100ms between requests
        output_dir="artifacts/phi_resonance_100blocks",
        run_monte_carlo=True,  # Compute random baseline
    )

    sys.exit(exit_code)