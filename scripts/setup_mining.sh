#!/usr/bin/env bash
#
# HYBA local mining setup helper.
# Creates .env.mining.local with the pool variable names consumed by
# python_backend/pythia_mining/pool_profiles.py.
#

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_ROOT}"

echo "HYBA local mining setup"
echo "======================="
echo

if [[ ! -f "package.json" || ! -d "python_backend" ]]; then
  echo "Error: run this script from the HYBA_FULLSTACK repository root or via scripts/setup_mining.sh"
  exit 1
fi

ENV_FILE=".env.mining.local"
if [[ -f "${ENV_FILE}" ]]; then
  echo "Warning: ${ENV_FILE} already exists"
  read -r -p "Overwrite? (y/N) " reply
  if [[ ! "${reply}" =~ ^[Yy]$ ]]; then
    echo "Keeping existing file"
    exit 0
  fi
fi

JWT_SECRET_VALUE="$(python3 - <<'PY'
import secrets
print(secrets.token_urlsafe(48))
PY
)"
INTERNAL_TOKEN_VALUE="$(python3 - <<'PY'
import secrets
print(secrets.token_urlsafe(32))
PY
)"

umask 077
cat > "${ENV_FILE}" <<EOF
# HYBA local mining configuration
# Generated for scripts/setup_and_start.sh and local Docker/Compose use.
# Fill in one real pool profile before expecting pool connection.

NODE_ENV=development
HYBA_ENV=development

# Required auth values for local operator/API control.
JWT_SECRET=${JWT_SECRET_VALUE}
HYBA_INTERNAL_HEALTH_TOKEN=${INTERNAL_TOKEN_VALUE}

# Runtime safety gates. Live Stratum may connect to a configured pool, but live
# share submit remains disabled unless the operator explicitly enables it.
HYBA_ALLOW_DEV_FIXTURES=false
HYBA_ENABLE_LIVE_STRATUM=true
HYBA_ENABLE_MINING_AUTOCONNECT=false
HYBA_ENABLE_LIVE_SHARE_SUBMIT=false
HYBA_LIVE_SHARE_APPROVAL_ID=
HYBA_ENABLE_AUDIT_LOGGING=true
BACKEND_PROXY_TIMEOUT_MS=30000

# Optional declared capacity. Backend enforces its own cap.
HYBA_QUANTUM_CAPACITY_EHS=1.0

# Pick one primary pool first. Leave unused pools blank.

# ViaBTC
HYBA_POOL_VIABTC_URL=stratum+tcp://btc.viabtc.io:3333
HYBA_POOL_VIABTC_USERNAME=
HYBA_POOL_VIABTC_PASSWORD=
HYBA_POOL_VIABTC_STRATUM_VERSION=1

# Braiins
HYBA_POOL_BRAIINS_URL=stratum+tcp://stratum.braiins.com:3333
HYBA_POOL_BRAIINS_USERNAME=
HYBA_POOL_BRAIINS_PASSWORD=
HYBA_POOL_BRAIINS_STRATUM_VERSION=1

# Solo CKPool
HYBA_POOL_CKPOOL_URL=stratum+tcp://solo.ckpool.org:3333
HYBA_POOL_CKPOOL_BTC_ADDRESS=
HYBA_POOL_CKPOOL_PASSWORD=x
HYBA_POOL_CKPOOL_STRATUM_VERSION=1

# NiceHash SHA256
# The loader expects WORKER + NH_POOL_ID/NICEHASH_POOL_ID. PASSWORD defaults to x
# in the runtime profile if omitted, but setting it explicitly is clearer.
HYBA_POOL_NICEHASH_URL=stratum+ssl://sha256.auto.nicehash.com:443
HYBA_POOL_NICEHASH_WORKER=
HYBA_POOL_NICEHASH_NH_POOL_ID=
HYBA_POOL_NICEHASH_PASSWORD=x
HYBA_POOL_NICEHASH_STRATUM_VERSION=1

# Generic Stratum v2
HYBA_POOL_STRATUMV2_URL=stratum2+ssl://pool.example.com:3336
HYBA_POOL_STRATUMV2_USERNAME=
HYBA_POOL_STRATUMV2_PASSWORD=
HYBA_POOL_STRATUMV2_STRATUM_VERSION=2
EOF

echo "Created ${ENV_FILE}"
echo
echo "Next:"
echo "1. Fill in one real pool profile."
echo "2. Keep HYBA_ENABLE_LIVE_SHARE_SUBMIT=false for first bring-up."
echo "3. Start the local stack with:"
echo "   bash scripts/setup_and_start.sh"
echo "4. Once the frontend/backend health is green, use Treasury/MIDAS to connect/switch the pool."
echo
echo "For Docker/Compose production-mode bring-up, use:"
echo "   docker compose --env-file ${ENV_FILE} -f docker-compose.production.yml up --build"
