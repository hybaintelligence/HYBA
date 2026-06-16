#!/bin/bash

# JWT Token (created above)
TOKEN="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJvcGVyYXRvci1saXZlLXRlc3QiLCJyb2xlIjoibWluaW5nOm9wZXJhdGUiLCJpYXQiOjE3ODE2MjQzMzksImV4cCI6MTc4MTYyNzkzOX0.MxRnXcFGDR6IyvyZqQMYQaP65_nbaqL-I-pX4V0_Su8"

echo "=========================================="
echo "HYBA LIVE MINING PERFORMANCE TEST"
echo "Start: $(date)"
echo "=========================================="
echo ""

# Get initial pool config
echo "1. Fetching pool configuration..."
curl -s http://127.0.0.1:3001/api/mining/pools \
  -H "Authorization: Bearer $TOKEN" 2>/dev/null | python3 -c "
import sys, json
try:
  d = json.load(sys.stdin)
  summary = d.get('summary', {})
  print(f'  Active Pool: {summary.get(\"active_pool_name\")}')
  print(f'  Total Pools: {summary.get(\"total_pools\")}')
  print(f'  Configured: {summary.get(\"configured_pools\")}')
  print(f'  Daemon Running: {summary.get(\"daemon_running\")}')
except Exception as e:
  print(f'  Error: {e}')
" 2>/dev/null

echo ""
echo "2. Starting 10-minute monitoring period..."
echo "   [Time] [Shares] [Acceptance Rate] [Hashrate] [Status]"
echo ""

# Monitor for 10 minutes (600 seconds = 20 * 30 second intervals)
START=$(date +%s)
END=$((START + 600))

iteration=1
while [ $(date +%s) -lt $END ]; do
  ELAPSED=$(($(date +%s) - START))
  REMAINING=$((600 - ELAPSED))
  
  # Get live metrics
  curl -s http://127.0.0.1:3001/api/mining/pools \
    -H "Authorization: Bearer $TOKEN" 2>/dev/null | python3 -c "
import sys, json
from datetime import datetime
try:
  data = json.load(sys.stdin)
  summary = data.get('summary', {})
  elapsed = $ELAPSED
  mins = elapsed // 60
  secs = elapsed % 60
  
  shares = summary.get('total_shares_24h', 0)
  rate = summary.get('global_acceptance_rate', 0) * 100
  hashrate = summary.get('total_hashrate', 0)
  midas = summary.get('midas_state', 'unknown')
  
  print(f'[{mins:02d}:{secs:02d}] [{shares:>5}] [{rate:>5.1f}%] [{hashrate:.2f} EH/s] [{midas}]')
except Exception as e:
  print(f'Error: {e}')
" 2>/dev/null || echo "[??:??] [ERROR] [Connection lost]"
  
  sleep 30
  iteration=$((iteration + 1))
done

END_TIME=$(date)
echo ""
echo "=========================================="
echo "MONITORING COMPLETE"
echo "End: $END_TIME"
echo "Duration: 10 minutes"
echo "=========================================="
echo ""

# Final status
echo "3. Final Status Check..."
curl -s http://127.0.0.1:3001/api/mining/pools \
  -H "Authorization: Bearer $TOKEN" 2>/dev/null | python3 -c "
import sys, json
try:
  data = json.load(sys.stdin)
  pools = data.get('pools', [])
  summary = data.get('summary', {})
  
  print(f'  Total pools: {len(pools)}')
  print(f'  Active: {summary.get(\"active_pools\")}')
  print(f'  Total shares (24h): {summary.get(\"total_shares_24h\")}')
  print(f'  Final acceptance rate: {summary.get(\"global_acceptance_rate\")*100:.1f}%')
  print(f'  Daemon running: {summary.get(\"daemon_running\")}')
  print(f'  MIDAS state: {summary.get(\"midas_state\")}')
except Exception as e:
  print(f'  Error: {e}')
" 2>/dev/null

echo ""
echo "✓ Test Complete"
