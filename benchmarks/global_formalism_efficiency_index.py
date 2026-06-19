#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "python_backend"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from pythia_mining.after_quantum_trifecta import run_global_formalism_efficiency_index


def main() -> int:
    reports = [report.as_dict() for report in run_global_formalism_efficiency_index()]
    out = {
        "index": "Global Formalism Efficiency Index",
        "epistemic_status": "after-quantum formalism benchmark; structured workloads only",
        "reports": reports,
    }
    print(json.dumps(out, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
