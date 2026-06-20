#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

python -m py_compile python_backend/pythia_mining/autonomous_mining_controller.py
python -m pytest \
  tests/test_autonomous_mining_stress.py \
  tests/test_autonomous_mining_adversarial.py \
  tests/test_autonomous_mining_properties.py
