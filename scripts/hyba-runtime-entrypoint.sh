#!/usr/bin/env sh
set -eu

BACKEND_HOST="${HYBA_BACKEND_HOST:-127.0.0.1}"
BACKEND_PORT="${HYBA_BACKEND_PORT:-3001}"
NODE_ENTRYPOINT="${HYBA_NODE_ENTRYPOINT:-dist/server.cjs}"

shutdown() {
  echo "[hyba-entrypoint] shutdown requested"
  if [ -n "${BACKEND_PID:-}" ] && kill -0 "$BACKEND_PID" 2>/dev/null; then
    kill -TERM "$BACKEND_PID" 2>/dev/null || true
  fi
  if [ -n "${NODE_PID:-}" ] && kill -0 "$NODE_PID" 2>/dev/null; then
    kill -TERM "$NODE_PID" 2>/dev/null || true
  fi
}

trap shutdown INT TERM HUP

echo "[hyba-entrypoint] starting FastAPI backend on ${BACKEND_HOST}:${BACKEND_PORT}"
uvicorn hyba_genesis_api.main:app \
  --host "$BACKEND_HOST" \
  --port "$BACKEND_PORT" \
  --log-level "${LOG_LEVEL:-warning}" &
BACKEND_PID=$!

echo "[hyba-entrypoint] starting Node bridge ${NODE_ENTRYPOINT}"
node "$NODE_ENTRYPOINT" &
NODE_PID=$!

while :; do
  if ! kill -0 "$BACKEND_PID" 2>/dev/null; then
    STATUS=0
    wait "$BACKEND_PID" || STATUS=$?
    echo "[hyba-entrypoint] FastAPI backend exited with ${STATUS}; stopping bridge"
    kill -TERM "$NODE_PID" 2>/dev/null || true
    wait "$NODE_PID" 2>/dev/null || true
    exit "$STATUS"
  fi

  if ! kill -0 "$NODE_PID" 2>/dev/null; then
    STATUS=0
    wait "$NODE_PID" || STATUS=$?
    echo "[hyba-entrypoint] Node bridge exited with ${STATUS}; stopping backend"
    kill -TERM "$BACKEND_PID" 2>/dev/null || true
    wait "$BACKEND_PID" 2>/dev/null || true
    exit "$STATUS"
  fi

  sleep 1
done
