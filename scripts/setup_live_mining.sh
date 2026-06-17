#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || true)"
if [[ -z "${REPO_ROOT}" ]]; then
  SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
  REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
fi
cd "${REPO_ROOT}"

: "${HYBA_JWT_SECRET:?HYBA_JWT_SECRET must be provided via environment or secret manager}"
: "${BRAIINS_POOL_URL:?BRAIINS_POOL_URL must be provided via environment or secret manager}"
: "${BRAIINS_WORKER_NAME:?BRAIINS_WORKER_NAME must be provided via environment or secret manager}"
: "${BRAIINS_POOL_PASSWORD:?BRAIINS_POOL_PASSWORD must be provided via environment or secret manager}"

export HYBA_JWT_SECRET
export BRAIINS_POOL_URL
export BRAIINS_WORKER_NAME
export BRAIINS_POOL_PASSWORD

printf '%s\n' "Live mining environment validated."
printf '%s\n' "Secrets were read from the process environment and were not printed."
printf '%s\n' "Repository root: ${REPO_ROOT}"
