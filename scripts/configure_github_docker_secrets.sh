#!/usr/bin/env bash
set -euo pipefail

if ! command -v gh >/dev/null 2>&1; then
  echo "GitHub CLI (gh) is not installed. Install gh, run 'gh auth login', then rerun this script." >&2
  exit 127
fi

if ! gh auth status >/dev/null 2>&1; then
  echo "GitHub CLI is not authenticated. Run 'gh auth login' first." >&2
  exit 1
fi

put_secret() {
  local name="$1"
  local value="$2"
  if [[ -n "$value" ]]; then
    printf '%s' "$value" | gh secret set "$name" --body-file -
    echo "Set $name"
  fi
}

prompt_secret() {
  local name="$1"
  local prompt="$2"
  local value=""
  read -r -s -p "$prompt: " value
  echo
  put_secret "$name" "$value"
}

prompt_plain() {
  local name="$1"
  local prompt="$2"
  local value=""
  read -r -p "$prompt: " value
  put_secret "$name" "$value"
}

put_secret JWT_SECRET "$(openssl rand -base64 32)"
put_secret HYBA_INTERNAL_HEALTH_TOKEN "$(openssl rand -base64 32)"

prompt_plain DOCKERHUB_USERNAME "Docker Hub username/org"
prompt_secret DOCKERHUB_TOKEN "Docker Hub access token"
prompt_plain DOCKERHUB_REPOSITORY "Docker Hub repository (example: your-org/hyba-fullstack)"
prompt_secret HYBA_OPERATOR_CREDENTIALS "Operator credentials (username:\$argon2id\$...:mining_operator)"

read -r -p "Configure which pool for auto-connect? [viabtc/nicehash/braiins/ckpool/skip]: " pool
case "${pool,,}" in
  viabtc)
    put_secret HYBA_MINING_AUTO_POOL_ID viabtc
    prompt_plain HYBA_POOL_VIABTC_URL "ViaBTC Stratum URL"
    prompt_plain HYBA_POOL_VIABTC_USERNAME "ViaBTC username/worker"
    prompt_secret HYBA_POOL_VIABTC_PASSWORD "ViaBTC password"
    ;;
  nicehash)
    put_secret HYBA_MINING_AUTO_POOL_ID nicehash
    prompt_plain HYBA_POOL_NICEHASH_URL "NiceHash Stratum URL"
    prompt_plain HYBA_POOL_NICEHASH_WORKER "NiceHash worker"
    prompt_plain HYBA_POOL_NICEHASH_NH_POOL_ID "NiceHash pool id"
    prompt_secret HYBA_POOL_NICEHASH_PASSWORD "NiceHash password (often x)"
    ;;
  braiins)
    put_secret HYBA_MINING_AUTO_POOL_ID braiins
    prompt_plain HYBA_POOL_BRAIINS_URL "Braiins Stratum URL"
    prompt_plain HYBA_POOL_BRAIINS_USERNAME "Braiins username"
    prompt_secret HYBA_POOL_BRAIINS_PASSWORD "Braiins password"
    ;;
  ckpool)
    put_secret HYBA_MINING_AUTO_POOL_ID ckpool
    prompt_plain HYBA_POOL_CKPOOL_URL "CKPool Stratum URL"
    prompt_plain HYBA_POOL_CKPOOL_BTC_ADDRESS "CKPool BTC address"
    prompt_secret HYBA_POOL_CKPOOL_PASSWORD "CKPool password (often x)"
    ;;
  skip|"")
    echo "Skipped pool secrets. Add at least one pool before live mining deploy."
    ;;
  *)
    echo "Unknown pool '$pool'; skipped pool secrets." >&2
    ;;
esac

echo "Done. Review docs/deployment/docker-cloud.md for optional secrets and launch flags."
