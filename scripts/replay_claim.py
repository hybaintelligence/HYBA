#!/usr/bin/env python3
"""Compatibility wrapper for the pythia-replay console entry point."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "python_backend"))

from pythia_mining.replay_claim_cli import main  # noqa: E402

if __name__ == "__main__":
    raise SystemExit(main())
