#!/usr/bin/env python3
"""Run the standalone HYBA_FULLSTACK Millennium elevation gate.

This runner preserves production compatibility: it does not modify existing npm
scripts, production gates, or runtime APIs. It generates the local extracted
Millennium packet and executes the packet verifier.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path
from typing import Iterable

ROOT = Path(__file__).resolve().parents[1]


def run(command: list[str]) -> None:
    completed = subprocess.run(command, cwd=ROOT, check=False)
    if completed.returncode != 0:
        raise SystemExit(completed.returncode)


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output-dir",
        default="artifacts/millennium_runtime_elevation",
        help="Where the elevation packet should be written.",
    )
    args = parser.parse_args(list(argv) if argv is not None else None)

    run(
        [
            sys.executable,
            "scripts/generate_millennium_runtime_elevation_packet.py",
            "--output-dir",
            args.output_dir,
        ]
    )
    run([sys.executable, "-m", "pytest", "tests/test_millennium_runtime_elevation_packet.py", "-q"])
    print("Millennium runtime elevation gate passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
