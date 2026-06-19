#!/usr/bin/env python3
"""Print the honest Deutsch/PULVINI benchmark report as JSON.

The benchmark is intentionally a complexity-boundary report, not a quantum
speedup claim: it compares exact dense state-vector memory with φ-logarithmic
structured-state estimates and records that arbitrary unstructured states remain
exponential.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "python_backend"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from pythia_mining.ctd_formalism import run_deutsch_pulvini_benchmark


def main() -> int:
    report = run_deutsch_pulvini_benchmark()
    print(json.dumps(report.as_dict(), indent=2, sort_keys=True))
    return 0 if report.rigorous else 1


if __name__ == "__main__":
    raise SystemExit(main())
