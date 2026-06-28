# HYBA Backend Debugging - Quick Start Guide

**For Python & FastAPI Debugging**  
**Updated**: June 26, 2026  

---

## 30-Second Setup

```bash
# Navigate to backend
cd python_backend

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Run diagnostic tool
python debug_backend.py

# Start the server
uvicorn hyba_genesis_api.main:app --reload --log-level debug
```

If all goes well, you'll see:
```
✅ Backend is ready for debugging!
```

---

## The 3 Debug Scripts

### 1. **debug_backend.py** — Overall Health Check

**What it does**: Tests imports, modules, API, TestClient, and environment

```bash
python debug_backend.py
```

**Output**: 6 diagnostic checks with ✅/❌ results

**Use this when**:
- Starting work on the project
- After installing new dependencies
- Something feels broken but you don't know what

---

### 2. **debug_pulvini_analysis.py** — PULVINI Math Verification

**What it does**: Checks if PULVINI structure computes correctly (especially automorphism group)

```bash
python debug_pulvini_analysis.py
```

**Output**: 5-step analysis ending with a verdict

**Use this when**:
- You're working on A2 (PULVINI)
- Tests are failing
- Automorphism group computation is wrong

**Key findings from this tool**:
- ✅ If automorphism group = 120: PULVINI is correct
- ❌ If automorphism group = 1: Only identity automorphism found (broken math)

---

### 3. **debug_api_endpoints.py** — API Response Testing

**What it does**: Tests endpoints and verifies claim boundaries are present

```bash
python debug_api_endpoints.py
```

**Output**: Test results for health, quantum endpoints, routers, claim boundaries

**Use this when**:
- Testing specific API endpoints
- Verifying claim boundaries are in responses
- Checking router structure

---

## Running the Server in Debug Mode

### Start with Debug Logging

```bash
uvicorn hyba_genesis_api.main:app --reload --log-level debug --port 8000
```

**Flags explained**:
- `--reload`: Auto-restart when files change
- `--log-level debug`: Show detailed logs
- `--port 8000`: Use port 8000 (default)

### Visit Swagger UI

Once the server is running, open:
```
http://localhost:8000/docs
```

You'll see an interactive API browser where you can test endpoints directly.

---

## Common Debugging Tasks

### Task 1: Test an Endpoint

**Option A: Using Swagger UI**
1. Start server: `uvicorn hyba_genesis_api.main:app --reload`
2. Open: `http://localhost:8000/docs`
3. Click an endpoint, fill in parameters, click "Try it out"

**Option B: Using curl**
```bash
curl http://localhost:8000/api/v1/virtual-fault-tolerant-computers/status | python -m json.tool
```

**Option C: Using Python**
```python
from fastapi.testclient import TestClient
from hyba_genesis_api.main import app

client = TestClient(app)
response = client.get("/api/v1/virtual-fault-tolerant-computers/status")
print(response.json())
```

### Task 2: Run Tests

```bash
# All tests
pytest tests/ -v

# Only PULVINI tests
pytest tests/test_pulvini* -v

# With coverage
pytest tests/ --cov=python_backend --cov-report=html

# Only failing tests
pytest tests/ --lf -v

# Stop on first failure
pytest tests/ -x
```

### Task 3: Debug Test Failures

```bash
# With detailed output and print statements
pytest tests/test_pulvini_structural_certificate.py -v -s

# With pdb on failure
pytest tests/test_pulvini_structural_certificate.py -v --pdb
```

### Task 4: Check for Import Issues

```bash
# Quick check
python -c "from hyba_genesis_api.main import app; print('✅ Imports OK')"

# Detailed check
python debug_backend.py  # Shows which imports fail
```

### Task 5: Check Specific Module

```bash
# PULVINI
python debug_pulvini_analysis.py

# API Endpoints
python debug_api_endpoints.py

# Overall health
python debug_backend.py
```

---

## The A1/A2 Status

### A1: Quantum-as-a-Service ✅ READY

- **Tests**: 25/25 passing
- **Status**: Ready for elevation
- **What to verify**:
  ```bash
  pytest tests/test_fault_tolerant_quantum.py -v
  ```
- **API path**: `/api/v1/virtual-fault-tolerant-computers/status`

### A2: PULVINI 🔴 BLOCKED

- **Issue**: Automorphism group computes to 1 instead of 120
- **Tests**: 1/24 passing
- **Debugging**: Run `python debug_pulvini_analysis.py`
- **Next steps**:
  1. Run the debug script
  2. Fix root cause (asymmetric edges or math bug)
  3. Rerun tests until 24/24 pass
  4. Then elevate

---

## Troubleshooting

### "ModuleNotFoundError: No module named 'hyba_genesis_api'"

**Fix**:
```bash
cd python_backend
pip install -e .
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
```

### "Address already in use"

**Fix**:
```bash
# PowerShell (Windows):
Stop-Process -Id (Get-NetTCPConnection -LocalPort 8000).OwningProcess -Force

# Linux/Mac:
lsof -ti:8000 | xargs kill -9
```

### "Can't connect to MongoDB"

**Fix**:
```bash
export SKIP_DB=true
uvicorn hyba_genesis_api.main:app --reload
```

### Tests failing for mysterious reasons

**Fix**:
1. Run `python debug_backend.py` — see if there are import issues
2. Check Python version: `python --version` (should be 3.9+)
3. Reinstall dependencies: `pip install --force-reinstall -r requirements.txt`
4. Clear cache: `find . -type d -name __pycache__ -exec rm -rf {} +`

---

## Example: Debugging the A2 (PULVINI) Issue

### Step 1: Run diagnostics

```bash
python debug_pulvini_analysis.py
```

### Step 2: Read the output

Look for:
- **STEP 1**: Asymmetric edges? Yes/No
- **STEP 2**: Degree values correct? Yes/No
- **STEP 3**: Automorphism group = 120? Yes/No
- **STEP 5**: Tests passing? Yes/No

### Step 3: If automorphism = 1, check STEP 1

```
❌ Found X asymmetric edges (should be 0)
```

**Fix**: Edit `pythia_mining/pulvini_topology.py`, add missing reciprocal edges

### Step 4: Rerun diagnostics

```bash
python debug_pulvini_analysis.py
```

### Step 5: When all checks pass, run pytest

```bash
pytest tests/test_pulvini_structural_certificate.py -v
```

---

## File Reference

### Debug Scripts (in python_backend/)

| File | Purpose | Run with |
|------|---------|----------|
| `debug_backend.py` | Overall health check | `python debug_backend.py` |
| `debug_pulvini_analysis.py` | PULVINI math verification | `python debug_pulvini_analysis.py` |
| `debug_api_endpoints.py` | Endpoint testing | `python debug_api_endpoints.py` |

### Documentation (in root)

| File | Purpose |
|------|---------|
| `DEBUG_GUIDE.md` | Comprehensive debugging reference |
| `ELEVATION_VERIFICATION_REPORT.md` | Full elevation findings |
| `ELEVATION_SESSION_SUMMARY.md` | Executive summary of elevation work |

### Key Source Files

| Path | Purpose |
|------|---------|
| `hyba_genesis_api/main.py` | FastAPI app entry point |
| `hyba_genesis_api/api/quantum_as_a_service.py` | Quantum-as-a-Service API (A1) |
| `pythia_mining/pulvini_topology.py` | PULVINI structure definition (A2) |
| `pythia_mining/pulvini_group.py` | Automorphism computation (A2) |

---

## Next Steps

1. ✅ Run `python debug_backend.py` to verify setup
2. ✅ Run `python debug_api_endpoints.py` to test API
3. ✅ Run `python debug_pulvini_analysis.py` to check A2
4. ✅ Run `pytest tests/ -v` to verify all tests
5. 🚀 Start server: `uvicorn hyba_genesis_api.main:app --reload`

---

## Quick Command Reference

```bash
# Diagnostics
python debug_backend.py                           # Overall health
python debug_pulvini_analysis.py                  # PULVINI math
python debug_api_endpoints.py                     # API testing

# Server
uvicorn hyba_genesis_api.main:app --reload        # Start server
# Visit: http://localhost:8000/docs               # Swagger UI

# Testing
pytest tests/ -v                                  # All tests
pytest tests/test_pulvini* -v                     # PULVINI tests
pytest tests/test_fault_tolerant_quantum.py -v    # Quantum tests
pytest tests/ --cov --cov-report=html             # With coverage

# Checks
python -c "from hyba_genesis_api.main import app; print('✅')"  # Import check
mypy python_backend/                              # Type checking
black python_backend/                             # Code formatting
```

---

**Ready to debug? Start with:**
```bash
cd python_backend
python debug_backend.py
```

