#!/bin/zsh
# HYBA Live Mining Session — 20-Minute Live Share Acceptance Test
# Usage: ./START_LIVE_MINING_20MIN.sh
#
# Launches the PYTHIA/PULVINI Unified Mining Engine directly against
# configured pools (ViaBTC + Braiins) with live Stratum I/O and share submission.
#
# Prerequisites:
#   - Backend running (npm run backend:start or uvicorn)
#   - config/mining_pools_live.json with valid credentials
#   - HYBA_POOL_CONFIG_PATH pointing to live config (default: config/mining_pools_live.json)
#   - Run configure_live_mining.py first to set JWT and pool credentials

set -e

cd "$(dirname "$0")/.."

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║       HYBA LIVE MINING — 20 MIN SHARE ACCEPTANCE TEST          ║"
echo "║             ViaBTC + Braiins Dual Pool Session                 ║"
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
export HYBA_POOL_CONFIG_PATH="config/mining_pools_live.json"

echo "✓ Live Stratum I/O:        ENABLED"
echo "✓ Live share submit:       ENABLED"
echo "✓ Audit logging:           ENABLED"
echo "✓ Pool config:             $HYBA_POOL_CONFIG_PATH"
echo ""

# Print pool summary from live config
echo "📡 Pool Configuration:"
python3 -c "
import json
import sys
try:
    with open('config/mining_pools_live.json') as f:
        cfg = json.load(f)
    default_pool = cfg.get('default_pool', 'unknown')
    print(f'  Default pool: {default_pool}')
    print()
    for pid, p in cfg.get('pools', {}).items():
        if p.get('enabled'):
            enabled = '✓ ACTIVE'
            if p.get('is_default'):
                enabled += ' [DEFAULT]'
        else:
            enabled = '✗ DISABLED'
        name = p.get('name', pid)
        url = p.get('url', '?')
        user = p.get('username', '(no auth)')
        print(f'  {enabled:20s} {name:20s}')
        print(f'    → {url}')
        print(f'    → {user}')
        print()
except Exception as e:
    print(f'  Error reading config: {e}')
    sys.exit(1)
" || true
echo ""

# Check if backend health endpoint responds
BACKEND_OK=$(curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:3001/health 2>/dev/null || echo "000")
if [ "$BACKEND_OK" = "200" ]; then
    echo "✓ Backend API reachable at http://127.0.0.1:3001"
else
    echo "⚠️  Backend not reachable. Start it with: npm run backend:start"
    echo ""
fi

# Verify environment variables
echo "📋 Environment Check:"
echo "  JWT_SECRET:    ${JWT_SECRET:-(not set)}"
echo "  NODE_ENV:      $NODE_ENV"
echo "  HYBA_ENV:      $HYBA_ENV"
echo ""

# ────────────────────────────────────────────────────────────
# Launch the unified miner directly (standalone process)
# ────────────────────────────────────────────────────────────
echo "Starting unified miner (standalone) — 20-minute session..."
echo ""

MINER_LOG="/tmp/hyba_live_miner_20min.log"
SESSION_START=$(date '+%Y-%m-%d %H:%M:%S')
SESSION_DURATION_SEC=$((20 * 60))

# Kill any previous live miner session
pkill -f "run_unified_miner.py" 2>/dev/null || true
sleep 1

# Load .env.local credentials before launching
if [ -f ".env.local" ]; then
  export $(grep -v '^#' .env.local | xargs)
fi

# Run the miner in the background with env vars
python3 python_backend/run_unified_miner.py > "$MINER_LOG" 2>&1 &
MINER_PID=$!
echo "  ✓ Miner started (PID: $MINER_PID)"
echo "  ✓ Log file: $MINER_LOG"
echo ""

# Wait for first connection attempt
sleep 5

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║                  LIVE MINING SESSION ACTIVE                    ║"
echo "╠════════════════════════════════════════════════════════════════╣"
echo "║  Start time:       $(date '+%H:%M:%S')                              ║"
echo "║  Duration:         20 minutes                                  ║"
echo "║  Pools:            ViaBTC (primary) + Braiins (fallback)       ║"
echo "║  Live Stratum:     ENABLED (real pool I/O)                    ║"
echo "║  Share submit:     ENABLED (real share submission)            ║"
echo "║  Logs:             /tmp/hyba_live_miner_20min.log             ║"
echo "║                                                                ║"
echo "║  📊 Watching for accepted shares...                            ║"
echo "║     (Share acceptance shows as 'Share accepted' in logs)       ║"
echo "║     (Pool rejections show as 'Share rejected' in logs)         ║"
echo "║                                                                ║"
echo "║  Press Ctrl+C to stop early                                   ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

# Show the miner log in real-time
function show_logs() {
    if command -v gtimeout &>/dev/null; then
        gtimeout 1200 tail -f "$MINER_LOG" 2>/dev/null &
    elif command -v timeout &>/dev/null; then
        timeout 1200 tail -f "$MINER_LOG" 2>/dev/null &
    else
        # macOS fallback
        tail -f "$MINER_LOG" 2>/dev/null &
    fi
}

TAIL_PID=""
show_logs
TAIL_PID=$!

# Calculate session end time
SESSION_END=$((SECONDS + SESSION_DURATION_SEC))

# Monitor the session
while [ $SECONDS -lt $SESSION_END ]; do
    sleep 1
done

# Kill the tail process
kill $TAIL_PID 2>/dev/null || true
sleep 1

echo ""
echo "╔════════════════════════════════════════════════════════════════╗"
echo "║                   20-MINUTE SESSION COMPLETE                   ║"
echo "╠════════════════════════════════════════════════════════════════╣"
echo "║  End time:         $(date '+%H:%M:%S')                              ║"
echo "║  Mining Summary:                                               ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

# Print the final stats lines from the log
echo "📊 Session Statistics:"
echo "────────────────────────────────────────────────────────────────"
grep -E "(MINING STATISTICS|Accepted|Rejected|Accept rate|Searches|invalid|Connected|Disconnected)" "$MINER_LOG" | tail -15 2>/dev/null || echo "(no stats lines found)"
echo "────────────────────────────────────────────────────────────────"
echo ""

# Show last 30 lines for context
echo "📋 Last 30 Log Lines (full context):"
echo "────────────────────────────────────────────────────────────────"
tail -30 "$MINER_LOG" 2>/dev/null || echo "(log empty)"
echo "────────────────────────────────────────────────────────────────"
echo ""

# Cleanup
kill $MINER_PID 2>/dev/null || true
sleep 1

echo "✓ Miner process $MINER_PID terminated"
echo ""
echo "📂 Session artifacts:"
echo "  • Complete log: $MINER_LOG"
echo ""
echo "📈 Next steps:"
echo "  1. Review the log for pool connectivity and share acceptance"
echo "  2. Check for 'Share accepted' or 'Share rejected' messages"
echo "  3. Verify MINING STATISTICS show accepted/rejected counts"
echo "  4. Run health check: npm run prod:check"
echo ""
echo "✓ Session complete. Ready for inspection."
echo ""
