#!/usr/bin/env python3
"""Generate a DIFC / AAOIFI Sukuk lifecycle drift simulation artifact.

This emits JSON evidence only. It does not approve, issue, book, trade, file,
execute, submit, or provide a Shariah/legal/regulatory opinion.
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

from pythia_finance_audit.sukuk_lifecycle_simulation import simulate_sukuk_lifecycle_drift


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Generate a DIFC / AAOIFI Sukuk lifecycle drift simulation."
    )
    parser.add_argument(
        "--compact",
        action="store_true",
        help="Omit embedded full per-step packets and emit a compact summary artifact.",
    )
    parser.add_argument("--output", type=Path, default=None, help="Optional JSON output path.")
    args = parser.parse_args()

    bundle = simulate_sukuk_lifecycle_drift(include_packets=not args.compact)
    rendered = json.dumps(bundle, indent=2, sort_keys=True)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered + "\n", encoding="utf-8")
    print(rendered)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
