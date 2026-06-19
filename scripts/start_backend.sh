#!/usr/bin/env bash
set -a
source /Users/demouser/Desktop/HYBA_FULLSTACK/.env.local
set +a

export PYENV_ROOT="$HOME/.pyenv"
export PATH="$PYENV_ROOT/bin:$PATH"
eval "$(pyenv init -)"

export PYTHONPATH=/Users/demouser/Desktop/HYBA_FULLSTACK/python_backend

cd /Users/demouser/Desktop/HYBA_FULLSTACK

exec python3 -m uvicorn hyba_genesis_api.main:app \
  --app-dir python_backend \
  --host 127.0.0.1 \
  --port 3001 \
  --log-level info
