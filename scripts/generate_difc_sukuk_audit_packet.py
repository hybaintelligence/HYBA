#!/usr/bin/env python3
"""Generate a DIFC / AAOIFI Sukuk sovereign-audit evidence packet.

This script emits JSON only. It does not approve, issue, book, trade, file,
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

from pythia_finance_audit.difc_aaiofi_bridge import generate_sample_difc_sukuk_packet


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate a DIFC / AAOIFI Sukuk audit packet.")
    parser.add_argument("--drift", action="store_true", help="Emit the drifting Sukuk packet that should be rejected before staging.")
    parser.add_argument("--output", type=Path, default=None, help="Optional JSON output path.")
    args = parser.parse_args()

    packet = generate_sample_difc_sukuk_packet(drift=args.drift)
    rendered = json.dumps(packet, indent=2, sort_keys=True)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered + "\n", encoding="utf-8")
    print(rendered)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
