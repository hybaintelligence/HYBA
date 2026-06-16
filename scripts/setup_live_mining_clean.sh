#!/bin/bash
set -e

cd /Users/demouser/Desktop/HYBA_FULLSTACK

echo "=========================================="
echo "HYBA LIVE MINING SETUP"
echo "=========================================="

# Kill any existing processes on port 3001
echo "[*] Clearing port 3001..."
lsof -i :3001 | grep -v COMMAND | awk '{print $2}' | xargs kill -9 2>/dev/null || true
sleep 2

# Source production credentials into this shell
echo "[*] Loading production credentials..."
# Use static credentials file (with no shell substitutions)
while IFS='=' read -r key value; do
  # Skip comments and empty lines
  [[ "$key" =~ ^#.*$ ]] && continue
  [ -z "$key" ] && continue
  
  # Export the variable
  export "$key=$value"
done < config/production_credentials_static.env

# Verify env vars are loaded
if [ -z "$NODE_ENV" ]; then
    echo "ERROR: NODE_ENV not loaded"
    exit 1
fi
echo "[✓] Environment loaded: NODE_ENV=$NODE_ENV, JWT_SECRET loaded"

# Start backend with production env
echo ""
echo "[*] Starting backend API on port 3001..."
python -m uvicorn hyba_genesis_api.main:app \
  --app-dir python_backend \
  --host 127.0.0.1 \
  --port 3001 \
  --log-level info \
  --workers 1

