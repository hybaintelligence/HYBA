#!/bin/zsh

# Set up PATH and tools
export PATH=/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin:$PATH
export PYENV_ROOT="$HOME/.pyenv"
export PATH="$PYENV_ROOT/bin:$PATH"
eval "$($PYENV_ROOT/bin/pyenv init -)"

# Print info
echo "=== Local Acceptance Gate ==="
echo "Python version: $(python --version)"

# Install dependencies
echo; echo "=== Installing dependencies ==="
python3 -m pip install -e .
python3 -m pip install pytest hypothesis

# Run pycompile check
echo; echo "=== Running pycompile check ==="
python3 -m py_compile python_backend/pythia_mining/*.py scripts/replay_claim.py

# Run test suite
echo; echo "=== Running test suite ==="
PYTHONPATH=python_backend python3 -m pytest \
  tests/test_replay_executor.py \
  tests/test_manifest_registry.py \
  tests/test_replay_claim_cli.py \
  tests/test_replay_reporting.py \
  tests/test_mining_auto_attester.py \
  tests/test_reproducibility_evidence_gate.py \
  tests/test_replay_properties.py \
  -q

# Run example replays
echo; echo "=== Running example replays ==="
echo "--- Replay nonce ---"
PYTHONPATH=python_backend python scripts/replay_claim.py replay examples/replay_nonce/manifest.json --cwd examples/replay_nonce

echo; echo "--- Replay matrix ---"
PYTHONPATH=python_backend python scripts/replay_claim.py replay examples/replay_matrix/manifest.json --cwd examples/replay_matrix

echo; echo "=== All local validation complete! ==="
