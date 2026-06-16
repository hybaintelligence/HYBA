#!/usr/bin/env bash
# 10-minute live mining observation script
set -euo pipefail

BASE_URL="http://127.0.0.1:3001"
OBSERVATION_SECONDS=600  # 10 minutes
INTERVAL_SECONDS=15     # Poll every 15s
AUDIT_LOG="logs/audit/audit_20260616.log"
START_TIME=$(date +%s)
END_TIME=$((START_TIME + OBSERVATION_SECONDS))
SNAPSHOT_DIR="artifacts/mining_readiness/live_dryrun"
mkdir -p "$SNAPSHOT_DIR"

echo "=============================================="
echo "  LIVE MINING OBSERVATION — 10 MINUTES"
echo "  Started: $(date -u '+%Y-%m-%dT%H:%M:%SZ')"
echo "  Backend: $BASE_URL"
echo "  Poll interval: ${INTERVAL_SECONDS}s"
echo "=============================================="
echo ""

OBSERVATION_COUNT=0

while [ "$(date +%s)" -lt "$END_TIME" ]; do
  OBSERVATION_COUNT=$((OBSERVATION_COUNT + 1))
  NOW=$(date -u '+%H:%M:%S')
  
  # --- Health endpoints ---
  READY=$(curl -s "$BASE_URL/api/health/ready" 2>/dev/null | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('status','?'))" 2>/dev/null || echo "unreachable")
  HEALTH=$(curl -s "$BASE_URL/api/health" 2>/dev/null | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('status','?'))" 2>/dev/null || echo "unreachable")
  
  # --- Audit log tail (last 15s of events) ---
  RECENT_EVENTS=$(tail -100 "$AUDIT_LOG" 2>/dev/null | python3 -c "
import sys,json
events=[]
for line in sys.stdin:
    parts = line.split('|')
    if len(parts) >= 4:
        try:
            e = json.loads(parts[-1])
            events.append(e)
        except: pass
# Show counts by type
from collections import Counter
c = Counter(e.get('event_type','unknown') for e in events)
for k,v in c.most_common():
    print(f'  {k}: {v}')
" 2>/dev/null || echo "  (no recent events)")

  echo "─── [$NOW] Observation #$OBSERVATION_COUNT ───"
  echo "  Health:        ready=$READY | status=$HEALTH"
  echo "  Recent events (last ~100 lines):"
  echo "$RECENT_EVENTS"
  
  # --- Check for shares ---
  SHARES=$(tail -500 "$AUDIT_LOG" 2>/dev/null | grep -c '"share_submit\|share_accepted\|share_rejected' || true)
  ACCEPTED=$(tail -500 "$AUDIT_LOG" 2>/dev/null | grep -c '"share_accepted' || true)
  REJECTED=$(tail -500 "$AUDIT_LOG" 2>/dev/null | grep -c '"share_rejected' || true)
  echo "  Share stats:   total=$SHARES | accepted=$ACCEPTED | rejected=$REJECTED"
  
  # --- Write snapshot ---
  SNAPSHOT_FILE="${SNAPSHOT_DIR}/snapshot_$(date -u '+%Y%m%dT%H%M%S').json"
  curl -s "$BASE_URL/api/health" > "$SNAPSHOT_FILE" 2>/dev/null || true
  
  echo "  Snapshot:      $SNAPSHOT_FILE"
  echo ""
  
  sleep "$INTERVAL_SECONDS"
done

echo "=============================================="
echo "  OBSERVATION COMPLETE — $OBSERVATION_COUNT polls"
echo "  Ended: $(date -u '+%Y-%m-%dT%H:%M:%SZ')"
echo "=============================================="

# Final summary
TOTAL_AUDIT=$(wc -l < "$AUDIT_LOG" 2>/dev/null || echo 0)
echo ""
echo "  Total audit events logged: $TOTAL_AUDIT"
echo "  Snapshots captured:         $(ls "$SNAPSHOT_DIR"/*.json 2>/dev/null | wc -l)"
SNAPSHOTS=$(ls "$SNAPSHOT_DIR"/*.json 2>/dev/null)
echo ""
echo "=============================================="
echo "  FINAL SHARE SUMMARY"
echo "=============================================="
echo "  Shares submitted:  $(grep -c '"share_submit' "$AUDIT_LOG" 2>/dev/null || echo 0)"
echo "  Shares accepted:   $(grep -c '"share_accepted' "$AUDIT_LOG" 2>/dev/null || echo 0)"
echo "  Shares rejected:   $(grep -c '"share_rejected' "$AUDIT_LOG" 2>/dev/null || echo 0)"
echo "  Connections:       $(grep -c '"connection_success' "$AUDIT_LOG" 2>/dev/null || echo 0)"
echo "  Jobs received:     $(grep -c '"job_received' "$AUDIT_LOG" 2>/dev/null || echo 0)"