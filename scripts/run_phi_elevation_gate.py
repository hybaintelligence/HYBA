#!/usr/bin/env python3
"""Generate and verify the phi elevation packet."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def run(command: list[str]) -> None:
    result = subprocess.run(command, cwd=ROOT, check=False)
    if result.returncode:
        raise SystemExit(result.returncode)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", default="artifacts/phi_resonance_elevation")
    args = parser.parse_args()
    run([sys.executable, "scripts/generate_phi_resonance_elevation_packet.py", "--output-dir", args.output_dir])
    run([sys.executable, "-m", "pytest", "tests/test_phi_resonance_elevation_properties.py", "tests/test_phi_resonance_elevation_packet.py", "-q"])
    print("phi elevation gate passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
