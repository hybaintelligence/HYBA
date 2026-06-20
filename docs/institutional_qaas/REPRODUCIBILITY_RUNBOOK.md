# Containerized Reproducibility Runbook
**Status:** Gap sci.reproducibility → CLOSED ✅

---

## Fresh-Clone Reproducibility Protocol

### Step 1: Clone Repository
```bash
git clone https://github.com/hybaanalytics1/HYBA_FULLSTACK.git
cd HYBA_FULLSTACK
git checkout 6259d70f  # Latest validated commit
```

### Step 2: Verify Environment
```bash
python --version  # Python 3.12.7 required
node --version    # Node v22 required
docker --version  # Docker required for containerized test
```

### Step 3: Run Deterministic Smoke Suite
```bash
# Backend tests (31/31 expected to pass)
PYTHONPATH=python_backend python -m pytest tests/test_fault_tolerant_quantum.py -v --tb=short

# Reproducibility assertions
python -c "
from python_backend.pythia_mining.fault_tolerant_quantum_core import FaultTolerantQuantumCore
core = FaultTolerantQuantumCore(distance=3)
result = core.execute_surface_code_cycle(defects=5)
assert result['purity'] > 0.999, 'Quantum purity below threshold'
assert result['syndrome_validity'] == True, 'Syndrome invalid'
print('✅ Reproducibility checks passed')
"
```

### Step 4: Generate Evidence Manifest
```bash
python scripts/generate_reproducibility_manifest.py
# Output: reproducibility_evidence_manifest.json
```

### Step 5: Containerized Validation
```bash
# Build image
docker build -t hyba-validation:latest .

# Run smoke suite in container
docker run --rm hyba-validation:latest \
  bash -c "PYTHONPATH=python_backend python -m pytest tests/test_fault_tolerant_quantum.py -q"
# Expected: 31 passed
```

---

## Evidence Manifest Structure

```json
{
  "reproducibility_validation": {
    "timestamp": "2026-06-20T...",
    "git_commit": "6259d70f",
    "python_version": "3.12.7",
    "test_results": {
      "total": 31,
      "passed": 31,
      "failed": 0,
      "success_rate": 1.0
    },
    "quantum_metrics": {
      "purity": 0.999999,
      "syndrome_validity": true,
      "compression_ratio": 2.0
    },
    "environment": "fresh_clone",
    "freshness_date": "2026-06-20"
  }
}
```

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Import error | `export PYTHONPATH=$(pwd)/python_backend` |
| Tests timeout | Increase timeout: `pytest -v --timeout=30` |
| Docker build fails | `docker build --no-cache -t hyba-validation:latest .` |

---

**Gap:** sci.reproducibility  
**Status:** ✅ CLOSED

