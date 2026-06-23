#!/usr/bin/env python3
"""Render a DIFC / AAOIFI Sukuk packet or lifecycle bundle as Markdown.

This is a read-only presentation helper for human review. It does not perform
external actions.
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

from pythia_finance_audit.criticism_ledger import render_criticism_ledger


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Render a DIFC / AAOIFI Sukuk criticism ledger."
    )
    parser.add_argument(
        "input", type=Path, help="Generated packet JSON or lifecycle simulation JSON."
    )
    parser.add_argument(
        "--output", type=Path, default=None, help="Optional Markdown output path."
    )
    args = parser.parse_args()

    data = json.loads(args.input.read_text(encoding="utf-8"))
    rendered = render_criticism_ledger(data)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
