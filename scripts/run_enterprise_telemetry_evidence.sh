#!/usr/bin/env bash
# Collect first-customer evidence for the Phase 3.5 EnterpriseTelemetryBridge.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
OUT_DIR="$ROOT/artifacts/first_customer_evidence/enterprise_telemetry"
mkdir -p "$OUT_DIR"

cd "$ROOT"
python3 -m py_compile reproducibility/benchmarks/*.py \
  | tee "$OUT_DIR/py_compile.log"

cd "$ROOT/reproducibility/benchmarks"
python3 - <<'PY' | tee "$OUT_DIR/smoke.log"
import test_mckinsey_additions as t

for name in dir(t):
    if name.startswith("test_"):
        getattr(t, name)()
        print(name, "ok")
PY
