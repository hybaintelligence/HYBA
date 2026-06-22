# Local Governance Gate Transcript

- Timestamp UTC: `2026-06-22T08:42:26+00:00`
- Repository root: `/workspace/HYBA_FULLSTACK`
- Result: `PASS`
- Python: `/root/.pyenv/versions/3.12.13/bin/python3`

## Commands

### claim-tier evidence binding

Command:
```text
/root/.pyenv/versions/3.12.13/bin/python3 scripts/check_validation_claim_tiers.py
```

Return code: `0`

Stdout:
```text
validation-claim-tier guard passed
```

Stderr:
_No output._

### mining commercialization stage gates

Command:
```text
/root/.pyenv/versions/3.12.13/bin/python3 scripts/check_commercialization_gates.py
```

Return code: `0`

Stdout:
```text
commercialization gate passed
```

Stderr:
_No output._

### claim-tier regression tests

Command:
```text
/root/.pyenv/versions/3.12.13/bin/python3 -m pytest tests/test_validation_claim_tiers.py -q
```

Return code: `0`

Stdout:
```text
......                                                                   [100%]
=============================== warnings summary ===============================
../../root/.pyenv/versions/3.12.13/lib/python3.12/site-packages/_pytest/config/__init__.py:1434
  /root/.pyenv/versions/3.12.13/lib/python3.12/site-packages/_pytest/config/__init__.py:1434: PytestConfigWarning: Unknown config option: timeout
  
    self._warn_or_fail_if_strict(f"Unknown config option: {key}\n")

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
6 passed, 1 warning in 0.61s
```

Stderr:
_No output._

## Operating rule

A FAIL result blocks merge, external distribution, and mining commercialization-stage promotion until fixed and re-run.
A PASS result is necessary but not sufficient for production claims; the underlying evidence manifest must still support the requested tier.
