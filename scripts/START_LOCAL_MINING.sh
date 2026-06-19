#!/bin/zsh
# HYBA Local Mining Session Startup Script
# Usage: ./START_LOCAL_MINING.sh

set -e

cd "$(dirname "$0")"

# Source zshrc to get all environment setup
source ~/.zshrc

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║           HYBA FULLSTACK LOCAL MINING SESSION                   ║"
echo "╚════════════════════════════════════════════════════════════════╝"

# Setup environment
echo ""
echo "Setting up environment..."

# Development settings (dev fixtures, no live pool I/O)
export NODE_ENV=development
export HYBA_ENV=development
export HYBA_ALLOW_DEV_FIXTURES=true
export HYBA_ENABLE_LIVE_STRATUM=false
export HYBA_ENABLE_AUDIT_LOGGING=true

# Auto-start mining with Braiins as default pool
export HYBA_ENABLE_MINING_AUTOCONNECT=true
export HYBA_POOL_BRAIINS_USERNAME=dev_worker
export HYBA_POOL_BRAIINS_PASSWORD=x

echo "✓ Environment configured"
echo "✓ Mining auto-connect enabled (Braiins default)"
echo ""

# Start backend in background
echo "Starting backend on http://127.0.0.1:3001..."
cd ../python_backend
python -m uvicorn hyba_genesis_api.main:app \
  --host 127.0.0.1 \
  --port 3001 \
  --reload \
  > /tmp/hyba_backend.log 2>&1 &
BACKEND_PID=$!
cd ../scripts
echo "✓ Backend started (PID: $BACKEND_PID)"
echo "  Mining auto-starting in background..."

sleep 3

# Start frontend in background
echo "Starting frontend on http://127.0.0.1:3000..."
npm run dev > /tmp/hyba_frontend.log 2>&1 &
FRONTEND_PID=$!
echo "✓ Frontend dev server started (PID: $FRONTEND_PID)"

sleep 2

echo ""
echo "╔════════════════════════════════════════════════════════════════╗"
echo "║                    MINING SESSION ACTIVE                        ║"
echo "╠════════════════════════════════════════════════════════════════╣"
echo "║  Frontend:         http://127.0.0.1:3000                       ║"
echo "║  Backend API:      http://127.0.0.1:3001                       ║"
echo "║  Pool profile:     Braiins default selected                    ║"
echo "║  Mode:             Development fixtures                        ║"
echo "║  Live pool I/O:    disabled                                    ║"
echo "║  Status:           Mining auto-started                         ║"
echo "║  Duration:         20 minutes (or until Ctrl+C)                ║"
echo "╠════════════════════════════════════════════════════════════════╣"
echo "║  Dev Mining Metrics (watch in browser):                        ║"
echo "║  • Simulated job flow from Braiins default                     ║"
echo "║  • Solver iterations & nonce discovery                         ║"
echo "║  • Memory compression state                                    ║"
echo "║  • Share submission acceptance (local validation only)         ║"
echo "║  • Health score & performance                                  ║"
echo "║                                                                 ║"
echo "║  API Endpoints:                                                ║"
echo "║  • /api/mining/status     (current state)                      ║"
echo "║  • /api/mining/stats      (aggregated metrics)                 ║"
echo "║  • /api/mining/pools      (pool rotation status)               ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""
echo "Mining session running. Press Ctrl+C to stop."
echo ""

# Watch logs
tail -f /tmp/hyba_backend.log /tmp/hyba_frontend.log 2>/dev/null &
LOG_PID=$!

# Wait for user interrupt or 20 minutes
sleep 1200 2>/dev/null || true

# Cleanup
echo ""
echo "Shutting down..."
kill $FRONTEND_PID 2>/dev/null || true
kill $BACKEND_PID 2>/dev/null || true
kill $LOG_PID 2>/dev/null || true

echo "Session complete."
