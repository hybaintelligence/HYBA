#!/usr/bin/env bash
set -euo pipefail

: "${HYBA_API_BASE_URL:=http://localhost:8000}"
: "${HYBA_BEARER_TOKEN:?HYBA_BEARER_TOKEN must be provided via environment or secret manager}"

curl --fail --silent --show-error \
  -H "Authorization: Bearer ${HYBA_BEARER_TOKEN}" \
  "${HYBA_API_BASE_URL%/}/api/mining/status"
