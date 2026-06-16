# HYBA_FULLSTACK Local Command-Room Test Evidence — 2026-06-13

Owner: HYBA Group Command Room  
Repository: HYBA_FULLSTACK  
Evidence source: operator-provided local PowerShell transcript  
Status: local funding / innovation / benefit tests passed

## Summary

The command-room operator reported a successful local test run on Windows PowerShell from:

```text
C:\Users\USER\OneDrive\Desktop\HYBA_FULLSTACK
```

The repository was already up to date after:

```powershell
git pull
```

## Evidence 1 — Mining benefit assessment

Command executed manually with local Python:

```powershell
python -m pytest tests/test_mining_benefit_assessment.py
```

Reported result:

```text
collected 7 items
7 passed in 2.42s
```

The passing suite covered:

- PULVINI reducing active working space without information loss;
- PULVINI lane surface aligning with the dodecahedral working set;
- phi harmony increasing when indicators are structured;
- structured ordering finding an injected signal earlier than a linear baseline;
- capacity/performance claims requiring measured input;
- structured ordering remaining deterministic and complete;
- candidate budget reduction when a structure prior exists.

## Evidence 2 — Combined funding / innovation / benefit gate

Initial npm attempt exposed a Windows portability issue:

```text
'PYTHONPATH' is not recognized as an internal or external command,
operable program or batch file.
```

The operator then ran the equivalent Windows-safe command:

```powershell
$env:PYTHONPATH="python_backend"; python -m pytest tests/test_funding_engine_deployment_gate.py tests/test_mining_innovation_properties.py tests/test_mining_benefit_assessment.py -q
```

Reported result:

```text
29 passed in 1.62s
```

This validates, locally:

- funding-engine deployment gate tests;
- mining innovation property tests;
- mining benefit assessment tests.

## Remediation applied

The Windows portability defect has been patched in `package.json` by removing Unix-style `PYTHONPATH=... python3` prefixes from the funding/mining npm scripts and using Windows-safe local Python invocation for:

```text
npm run test:mining:innovation
npm run test:mining:benefit
npm run test:funding:gate
npm run funding:gate
npm run funding:accepted-share:gate
```

## Evidence interpretation

This evidence supports the following claim:

```text
HYBA_FULLSTACK local funding-engine tests passed for deterministic search, mining innovation invariants, and benefit-assessment comparisons on the operator's Windows command-room machine.
```

This evidence does not yet support:

```text
accepted-share evidence
sustained hashrate
revenue
profitability
payroll coverage
office-cost coverage
first-seven-MD offer release
```

Those remain gated by live accepted-share evidence, pool-side proof, and signed command-room approval.
