#!/usr/bin/env bash
set -euo pipefail

BASE_URL="${1:-${HYBA_STAGING_URL:-}}"
API_KEY="${HYBA_API_KEY:-}"
if [[ -z "$BASE_URL" ]]; then
  echo "usage: HYBA_STAGING_URL=https://example.com $0 [base_url]" >&2
  exit 2
fi
BASE_URL="${BASE_URL%/}"
AUTH_ARGS=()
if [[ -n "$API_KEY" ]]; then
  AUTH_ARGS=(-H "X-API-Key: $API_KEY")
fi

check() {
  local path="$1"
  local url="$BASE_URL$path"
  local code
  code=$(curl -sS -o /tmp/hyba_smoke_response.json -w '%{http_code}' "${AUTH_ARGS[@]}" "$url")
  if [[ "$code" != "200" ]]; then
    echo "FAIL $path HTTP $code" >&2
    cat /tmp/hyba_smoke_response.json >&2 || true
    exit 1
  fi
  python3 -m json.tool /tmp/hyba_smoke_response.json >/dev/null
  echo "PASS $path HTTP $code"
}

check /api/health
check /api/v1/fault-tolerant-computers
check /api/qiaas
check /api/quantum-finance/capability-map
