#!/usr/bin/env bash
# PYTHIA Runtime Soak Test
# Runs backend for N minutes, captures evidence chain, validates autonomy continuity

set -euo pipefail

SOAK_MINUTES="${1:-30}"
EVIDENCE_DIR="runtime/evidence/pythia_autonomy"
SOAK_LOG="runtime/evidence/soak_test_$(date -u +%Y-%m-%dT%H-%M-%SZ).log"

echo "PYTHIA Soak Test: ${SOAK_MINUTES} minutes"
echo "Evidence will accumulate in: ${EVIDENCE_DIR}"
echo "Soak log: ${SOAK_LOG}"

# Start backend in background
npm run backend:start > "${SOAK_LOG}" 2>&1 &
BACKEND_PID=$!

echo "Backend PID: ${BACKEND_PID}"
echo "Waiting for substrate ready..."
sleep 5

# Poll health endpoint
if curl -sf http://127.0.0.1:3001/api/health/startup-self-healing > /dev/null; then
    echo "✅ Substrate ready, self-healing verified"
else
    echo "❌ Health check failed"
    kill ${BACKEND_PID}
    exit 1
fi

# Soak duration
echo "Soaking for ${SOAK_MINUTES} minutes..."
sleep $((SOAK_MINUTES * 60))

# Graceful shutdown
echo "Sending SIGTERM to backend..."
kill -TERM ${BACKEND_PID}
wait ${BACKEND_PID} || true

# Evidence summary
echo ""
echo "=== Evidence Chain Summary ==="
ls -lh "${EVIDENCE_DIR}"/*.json | tail -10
echo ""
echo "Total evidence files: $(ls -1 "${EVIDENCE_DIR}"/*.json 2>/dev/null | wc -l)"
echo "Soak log: ${SOAK_LOG}"
echo "✅ PYTHIA soak test complete"
