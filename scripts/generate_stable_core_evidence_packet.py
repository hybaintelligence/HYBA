#!/usr/bin/env python3
"""Generate the first PYTHIA Stable Core evidence packet.

This script emits a sealed JSON packet for supervised Stable Core review. It is
safe to run locally, in Docker, or in CI because it does not apply source changes.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
PYTHON_BACKEND = REPO_ROOT / "python_backend"
if str(PYTHON_BACKEND) not in sys.path:
    sys.path.insert(0, str(PYTHON_BACKEND))

from pythia_mining.stable_core_evidence import generate_stable_core_evidence_packet  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate PYTHIA Stable Core evidence packet")
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Optional JSON output path",
    )
    args = parser.parse_args()

    packet = generate_stable_core_evidence_packet().to_dict()
    payload = json.dumps(packet, indent=2, sort_keys=True, default=str)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(payload + "\n", encoding="utf-8")
    print(payload)


if __name__ == "__main__":
    main()
