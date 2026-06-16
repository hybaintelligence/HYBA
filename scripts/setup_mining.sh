#!/bin/bash
#
# HYBA local mining setup helper
# Creates a focused Docker/Compose env template for local production-mode bring-up.
#

set -euo pipefail

echo "HYBA local mining setup"
echo "======================="
echo

if [[ ! -f "docker-compose.production.yml" ]]; then
  echo "Error: run this script from the HYBA_FULLSTACK repository root"
  exit 1
fi

ENV_FILE=".env.mining.local"
if [[ -f "$ENV_FILE" ]]; then
  echo "Warning: $ENV_FILE already exists"
  read -r -p "Overwrite? (y/N) " reply
  if [[ ! "$reply" =~ ^[Yy]$ ]]; then
    echo "Keeping existing file"
    exit 0
  fi
fi

JWT_SECRET_VALUE="$(openssl rand -hex 32)"

cat > "$ENV_FILE" <<EOF
# HYBA local Docker mining configuration
# Generated for docker-compose.production.yml
# Fill in real operator and pool values before use.

NODE_ENV=production
HYBA_ENV=production

# Required auth values
JWT_SECRET=$JWT_SECRET_VALUE
# Format: username:\$argon2id\$...:role
# Example role: mining_operator
HYBA_OPERATOR_CREDENTIALS=operator:replace-with-argon2id-password-hash:mining_operator

# Runtime safety gates
HYBA_ALLOW_DEV_FIXTURES=false
HYBA_ENABLE_LIVE_STRATUM=true
HYBA_ENABLE_MINING_AUTOCONNECT=false
HYBA_ENABLE_LIVE_SHARE_SUBMIT=false
HYBA_LIVE_SHARE_APPROVAL_ID=
HYBA_ENABLE_AUDIT_LOGGING=true
HYBA_INTERNAL_HEALTH_TOKEN=
BACKEND_PROXY_TIMEOUT_MS=30000

# Optional declared capacity
HYBA_QUANTUM_CAPACITY_EHS=

# Pick one primary pool first. Leave unused pools blank.

# NiceHash SHA256
HYBA_POOL_NICEHASH_URL=stratum+ssl://sha256.eu.nicehash.com:33334
HYBA_POOL_NICEHASH_USERNAME=replace-with-real-worker
HYBA_POOL_NICEHASH_PASSWORD=replace-with-real-pool-password
HYBA_POOL_NICEHASH_STRATUM_VERSION=1

# ViaBTC
HYBA_POOL_VIABTC_URL=
HYBA_POOL_VIABTC_USERNAME=
HYBA_POOL_VIABTC_PASSWORD=
HYBA_POOL_VIABTC_STRATUM_VERSION=1

# Braiins
HYBA_POOL_BRAIINS_URL=
HYBA_POOL_BRAIINS_USERNAME=
HYBA_POOL_BRAIINS_PASSWORD=
HYBA_POOL_BRAIINS_STRATUM_VERSION=2

# CKPool
HYBA_POOL_CKPOOL_URL=
HYBA_POOL_CKPOOL_USERNAME=
HYBA_POOL_CKPOOL_BTC_ADDRESS=
HYBA_POOL_CKPOOL_PASSWORD=
HYBA_POOL_CKPOOL_STRATUM_VERSION=1

# Generic Stratum v2
HYBA_POOL_STRATUMV2_URL=
HYBA_POOL_STRATUMV2_USERNAME=
HYBA_POOL_STRATUMV2_PASSWORD=
HYBA_POOL_STRATUMV2_STRATUM_VERSION=2
EOF

echo "Created $ENV_FILE"
echo
echo "Next:"
echo "1. Fill in HYBA_OPERATOR_CREDENTIALS with a real Argon2id hash."
echo "2. Fill in one real pool profile."
echo "3. Start with HYBA_ENABLE_LIVE_SHARE_SUBMIT=false."
echo "4. Bring the stack up with:"
echo "   docker compose --env-file $ENV_FILE -f docker-compose.production.yml up --build"
echo
echo "Argon2id hash generation example:"
echo "python - <<'PY'"
echo "from argon2 import PasswordHasher"
echo "print(PasswordHasher().hash('replace-with-strong-password'))"
echo "PY"
