#!/usr/bin/env bash
set -euo pipefail

printf '🕵️ Running HYBA forensic runtime sanity check...\n'

export NODE_ENV="${NODE_ENV:-production}"
export HYBA_ENV="${HYBA_ENV:-production}"
export HYBA_ENABLE_LIVE_STRATUM="${HYBA_ENABLE_LIVE_STRATUM:-true}"
export HYBA_ENABLE_AUDIT_LOGGING="${HYBA_ENABLE_AUDIT_LOGGING:-true}"
export HYBA_ENABLE_LIVE_SHARE_SUBMIT="${HYBA_ENABLE_LIVE_SHARE_SUBMIT:-false}"

printf '🧭 Running production-readiness doctor in command-room mode...\n'
PYTHONPATH=python_backend python scripts/mining_production_readiness_doctor.py --mode command-room --skip-build

printf '🔬 Running review-environment pipeline audits...\n'
PYTHONPATH=python_backend python scripts/review_environment_pipeline_audit.py

printf '🧱 Verifying local proof-of-work validation and Stratum share guardrails...\n'
PYTHONPATH=python_backend python -m pytest tests/test_metal_sha256_pipeline.py tests/test_stratum_share_acceptance_e2e.py -q

printf '🛡️ Running exact SHA256d verifier/firewall deployment gate...\n'
bash scripts/run_verifier_firewall_gate.sh

if [[ "${HYBA_ENABLE_LIVE_SHARE_SUBMIT}" != "true" ]]; then
  printf '🛡️ Guardrail active: HYBA_ENABLE_LIVE_SHARE_SUBMIT is not true. Shares can be locally validated but will not be submitted live.\n'
fi

printf '🏁 Check complete. Forensic pipeline matches charter metrics.\n'
