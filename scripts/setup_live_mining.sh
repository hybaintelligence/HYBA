#!/bin/bash
set -e

cd /Users/demouser/Desktop/HYBA_FULLSTACK

# Kill previous processes
pkill -9 uvicorn 2>/dev/null || true
pkill -9 "npm run" 2>/dev/null || true
sleep 2

# Create JWT token
JWT_SECRET="dev-secret-key-for-live-mining"
export JWT_SECRET

# Set production environment
export NODE_ENV=production
export HYBA_ENV=production
export HYBA_ALLOW_DEV_FIXTURES=false
export HYBA_ENABLE_LIVE_STRATUM=true
export HYBA_ENABLE_AUDIT_LOGGING=true
export HYBA_ENABLE_LIVE_SHARE_SUBMIT=true
export HYBA_ENABLE_MINING_AUTOCONNECT=false
export HYBA_POOL_BRAIINS_USERNAME=PYTHIA.001
export HYBA_POOL_BRAIINS_PASSWORD=9awtMD5KQgvRUh2yFbjVeT7b6hjipWcAsQHd6wEhgtDT9soosna
export HYBA_LIVE_SHARE_APPROVAL_ID=operator-live-approval-$(date +%s)
export HYBA_PULVINI_HASHRATE_CAP_EHS=1.0

# Disable Redis and external services  
export HYBA_REDIS_ENABLED=false
export HYBA_CACHE_BACKEND=memory
export HYBA_QUEUE_BACKEND=memory

echo "=========================================="
echo "HYBA LIVE MINING TEST SETUP"
echo "=========================================="
echo "JWT_SECRET: $JWT_SECRET"
echo "Approval ID: $HYBA_LIVE_SHARE_APPROVAL_ID"
echo "Pool: Braiins (default)"
echo "Live Share Submit: ENABLED"
echo ""

# Generate JWT token for testing
python3 << 'PEOF'
import jwt
from datetime import datetime, timedelta

secret = "dev-secret-key-for-live-mining"
payload = {
    "sub": "operator-live-test",
    "role": "mining:operate",
    "iat": int(datetime.utcnow().timestamp()),
    "exp": int((datetime.utcnow() + timedelta(hours=1)).timestamp())
}

token = jwt.encode(payload, secret, algorithm="HS256")
with open('/tmp/auth_token.txt', 'w') as f:
    f.write(token)
print(f"Auth Token: {token}")
PEOF

echo ""
echo "Starting backend in production mode..."
python -m uvicorn hyba_genesis_api.main:app \
  --app-dir python_backend \
  --host 127.0.0.1 \
  --port 3001 \
  --log-level info \
  --workers 1
