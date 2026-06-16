#!/bin/bash
set -e

cd /Users/demouser/Desktop/HYBA_FULLSTACK

echo "=========================================="
echo "CONNECTING TO BRAIINS AND STARTING MINING"
echo "=========================================="

# Generate JWT token
TOKEN=$(python3 << 'PYEOF'
import jwt
from datetime import datetime, timedelta

secret = "hyba-live-mining-operator"
payload = {
    "sub": "live-operator",
    "role": "mining:operate",
    "iat": int(datetime.utcnow().timestamp()),
    "exp": int((datetime.utcnow() + timedelta(hours=2)).timestamp()),
    "permissions": ["mining:operate", "mining:read"]
}

token = jwt.encode(payload, secret, algorithm="HS256")
print(token)
PYEOF
)

echo "Token: $TOKEN"
echo ""

# Connect to Braiins pool
echo "1. Connecting to Braiins pool..."
curl -X POST http://127.0.0.1:3001/api/mining/connect \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"pool_id":"braiins","capacity_ehs":1.0,"switch":true}' \
  2>&1 | python3 -m json.tool

echo ""
echo "2. Starting mining daemon..."
curl -X POST http://127.0.0.1:3001/api/mining/start \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  2>&1 | python3 -m json.tool || echo "(Mining daemon starting...)"

echo ""
echo "3. Checking mining status..."
sleep 2
curl -X GET http://127.0.0.1:3001/api/mining/status \
  -H "Authorization: Bearer $TOKEN" \
  2>&1 | python3 -m json.tool

echo ""
echo "=========================================="
echo "MINING SESSION STARTED"
echo "Check audit logs: tail -f logs/audit/audit_20260616.log"
echo "Look for: share_submission + share_accepted from Braiins Pool"
echo "=========================================="
