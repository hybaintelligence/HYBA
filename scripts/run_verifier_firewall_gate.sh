#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || true)"
if [[ -z "${REPO_ROOT}" ]]; then
  SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
  REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
fi
cd "${REPO_ROOT}"

export PYTHONPATH="python_backend${PYTHONPATH:+:${PYTHONPATH}}"
python3 -m pytest \
  tests/test_mining_validation_pow_vectors.py \
  tests/test_mining_verification_firewall.py \
  tests/test_stratum_submission_firewall_integration.py \
  -q
