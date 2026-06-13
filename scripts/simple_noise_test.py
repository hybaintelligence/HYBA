#!/usr/bin/env python3
"""Simple test for noise protocol import and basic functionality."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "python_backend"
sys.path.insert(0, str(BACKEND))
sys.path.insert(0, str(ROOT))

print("Testing noise protocol import...")
try:
    from pythia_mining.noise_wrapper import NoiseWrapper, NoiseHandshakeResult
    print("✓ noise_wrapper imported successfully")
except ImportError as e:
    print(f"✗ Failed to import noise_wrapper: {e}")
    sys.exit(1)

print("\nTesting LiveStratumV2Session import...")
try:
    from pythia_mining.live_stratum_v2_session import LiveStratumV2Session
    print("✓ LiveStratumV2Session imported successfully")
except ImportError as e:
    print(f"✗ Failed to import LiveStratumV2Session: {e}")
    sys.exit(1)

print("\nTesting NoiseWrapper initialization...")
try:
    wrapper = NoiseWrapper()
    print("✓ NoiseWrapper initialized successfully")
except Exception as e:
    print(f"✗ Failed to initialize NoiseWrapper: {e}")
    sys.exit(1)

print("\nAll basic tests passed!")
print("Noise protocol support is ready for integration.")
