# CI Limitations and Local Evidence

## CI Status Interpretation

GitHub/Cloudflare CI checks may fail due to account/subscription execution limitations. These failures are infrastructure/account limitations unless a retained log shows a confirmed code/test/build failure.

## For First Customer Review

Use these resources for first-customer readiness review:
- Tag: `first-customer-evidence-v1`
- Evidence artifacts: `artifacts/first_customer_evidence/final/`
- Replay local validation commands (see below)
- Readiness script: `scripts/check_first_customer_readiness.py`

## Replay Local Validation Commands

### Pycompile check
```bash
python3 -m py_compile python_backend/pythia_mining/*.py scripts/replay_claim.py
```

### Test suite
```bash
PYTHONPATH=python_backend python3 -m pytest tests/test_replay_executor.py tests/test_manifest_registry.py tests/test_replay_claim_cli.py tests/test_replay_reporting.py tests/test_mining_auto_attester.py tests/test_reproducibility_evidence_gate.py tests/test_replay_properties.py -q
```

### Example replays
```bash
PYTHONPATH=python_backend python scripts/replay_claim.py replay examples/replay_nonce/manifest.json --cwd examples/replay_nonce
```
```bash
PYTHONPATH=python_backend python scripts/replay_claim.py replay examples/replay_matrix/manifest.json --cwd examples/replay_matrix
```

## Replay Scope

The replay stack is intentionally local-only and claim-bounded. It does not assert:
- Pool-side accepted-share evidence
- Hashrate
- Revenue
- Regulatory validation
- Consciousness claims
