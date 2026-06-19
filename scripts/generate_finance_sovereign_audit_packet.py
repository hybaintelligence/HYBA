#!/usr/bin/env python3
"""Generate the PYTHIA finance sovereign audit demonstration packet.

This script emits a sealed JSON packet. It does not approve, execute, route,
book, trade, or submit any external action.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "python_backend"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from pythia_mining.finance_sovereign_audit import generate_finance_sovereign_packet


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Generate a PYTHIA finance sovereign audit packet."
    )
    parser.add_argument(
        "--challenge",
        action="store_true",
        help="Emit the challenge packet that should be rejected before staging.",
    )
    parser.add_argument("--output", type=Path, default=None, help="Optional JSON output path.")
    args = parser.parse_args()

    packet = generate_finance_sovereign_packet(adversarial=args.challenge).to_dict()
    rendered = json.dumps(packet, indent=2, sort_keys=True)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered + "\n", encoding="utf-8")
    print(rendered)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
