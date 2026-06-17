#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || true)"
if [[ -z "${REPO_ROOT}" ]]; then
  SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
  REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
fi
cd "${REPO_ROOT}"

printf 'Layer 0: exact SHA256d verifier/firewall truth-source gate\n'
bash scripts/run_verifier_firewall_gate.sh

printf 'Layer 1: production preflight gate\n'
bash scripts/preflight_production_readiness_check.sh

printf 'Layer 2: full existing production check\n'
npm run prod:check

printf 'Layered deployment gate passed.\n'
