#!/bin/zsh
# HYBA Live Mining Session — 10-Minute Live Share Acceptance Test
# Usage: ./START_LIVE_MINING_10MIN.sh
#
# Launches the PYTHIA/PULVINI Unified Mining Engine directly against
# ViaBTC/CKPool/NiceHash with live Stratum I/O and share submission enabled.
#
# Prerequisites:
#   - Backend running (./START_LOCAL_MINING.sh or uvicorn)
#   - config/mining_pools_live.json with valid credentials
#   - HYBA_POOL_CONFIG_PATH pointing to live config (default: config/mining_pools_live.json)

set -e

cd "$(dirname "$0")"

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║        HYBA LIVE MINING — 10 MIN SHARE ACCEPTANCE TEST         ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

# Source zshrc to get any env setup
source ~/.zshrc 2>/dev/null || true

# ────────────────────────────────────────────────────────────
# CRITICAL: Enable live Stratum I/O and share submission
# ────────────────────────────────────────────────────────────
export NODE_ENV=development
export HYBA_ENV=development
export HYBA_ALLOW_DEV_FIXTURES=false
export HYBA_ENABLE_LIVE_STRATUM=true
export HYBA_ENABLE_LIVE_SHARE_SUBMIT=true
export HYBA_ENABLE_AUDIT_LOGGING=true
export HYBA_POOL_CONFIG_PATH="$(pwd)/config/mining_pools_live.json"

echo "✓ Live Stratum I/O:        ENABLED"
echo "✓ Live share submit:       ENABLED"
echo "✓ Pool config:             $HYBA_POOL_CONFIG_PATH"
echo ""

# Print pool summary from live config
echo "Pool configuration:"
python3 -c "
import json
with open('config/mining_pools_live.json') as f:
    cfg = json.load(f)
for pid, p in cfg.get('pools', {}).items():
    enabled = 'ACTIVE' if p.get('enabled') else 'DISABLED'
    name = p.get('name', pid)
    print(f'  • {name:20s} {enabled:10s} -> {p.get(\"url\",\"?\")}')
"
echo ""

# Check if backend health endpoint responds
BACKEND_OK=$(curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:3001/health 2>/dev/null || echo "000")
if [ "$BACKEND_OK" = "200" ]; then
    echo "✓ Backend API reachable at http://127.0.0.1:3001"
else
    echo "⚠ Backend not reachable. Start it first with ./START_LOCAL_MINING.sh in another terminal."
    echo "  (The miner runs as a standalone Python process and reports stats to the console.)"
fi
echo ""

# ────────────────────────────────────────────────────────────
# Launch the unified miner directly (standalone process)
# ────────────────────────────────────────────────────────────
echo "Starting unified miner (standalone) — 10-minute session..."
echo "  Log file: /tmp/hyba_live_miner_10min.log"
echo ""

MINER_LOG="/tmp/hyba_live_miner_10min.log"

# Kill any previous live miner session
pkill -f "run_unified_miner.py" 2>/dev/null || true
sleep 1

# Run the miner in the background
python3 python_backend/run_unified_miner.py > "$MINER_LOG" 2>&1 &
MINER_PID=$!
echo "✓ Miner started (PID: $MINER_PID)"
echo ""

# Wait for first connection attempt
sleep 5

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║                    LIVE MINING SESSION ACTIVE                    ║"
echo "╠════════════════════════════════════════════════════════════════╣"
echo "║  Duration:         10 minutes                                   ║"
echo "║  Live Stratum:     ENABLED (real pool I/O)                      ║"
echo "║  Share submit:     ENABLED (real share submission)               ║"
echo "║  Logs:             /tmp/hyba_live_miner_10min.log               ║"
echo "║                                                                  ║"
echo "║  Watching for accepted shares...                                 ║"
echo "║  (Share acceptance shows as 'Share accepted' in logs)            ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""
echo "Monitoring live miner output — Press Ctrl+C to stop early."
echo ""

# Show the miner log in real-time (for 10 minutes or until Ctrl+C)
TAIL_PID=""
if command -v gtimeout &>/dev/null; then
    gtimeout 600 tail -f "$MINER_LOG" &
    TAIL_PID=$!
elif command -v timeout &>/dev/null; then
    timeout 600 tail -f "$MINER_LOG" &
    TAIL_PID=$!
else
    # macOS fallback: run tail in background, sleep 10 minutes
    tail -f "$MINER_LOG" &
    TAIL_PID=$!
    SESSION_END=$((SECONDS + 600))
    while [ $SECONDS -lt $SESSION_END ]; do
        sleep 1
    done
    kill $TAIL_PID 2>/dev/null || true
fi

# Wait for the timeout or user interrupt
wait $TAIL_PID 2>/dev/null || true

echo ""
echo "╔════════════════════════════════════════════════════════════════╗"
echo "║                   10-MINUTE SESSION COMPLETE                    ║"
echo "╠════════════════════════════════════════════════════════════════╣"
echo "║  Final stats from miner log:                                   ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

# Print the final stats lines from the log
grep -E "(MINING STATISTICS|Accepted:|Rejected:|Accept rate|Searches:|Locally invalid)" "$MINER_LOG" | tail -10 2>/dev/null || echo "(no stats lines found)"
echo ""

# Also show the last 20 lines for full context
echo "Last 20 log lines:"
echo "----------------------------------------"
tail -20 "$MINER_LOG" 2>/dev/null || echo "(log empty)"
echo "----------------------------------------"
echo ""

# Cleanup
kill $MINER_PID 2>/dev/null || true
echo "Miner process $MINER_PID terminated."
echo ""
echo "Session log saved to: $MINER_LOG"
echo "Ready for inspection."