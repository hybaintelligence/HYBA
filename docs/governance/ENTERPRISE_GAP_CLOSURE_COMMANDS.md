# Enterprise Gap Closure Commands

Run this exact command set before merging the close-down PR:

```bash
npm run python:env:check
PYTHONPATH=python_backend python -m pytest tests/test_enterprise_telemetry_posture.py tests/test_enterprise_resilience.py -q
PYTHONPATH=python_backend python scripts/run_enterprise_gap_closure_gate.py
python scripts/run_local_governance_gate.py
python scripts/check_validation_claim_tiers.py
python scripts/check_commercialization_gates.py
npm run build
```

The enterprise gap closure gate writes:

```text
docs/governance/enterprise_gap_closure_gate.json
```

Do not close #130 unless these commands pass or any failure is explicitly recorded as a remaining gap.
