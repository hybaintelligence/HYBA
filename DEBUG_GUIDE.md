# HYBA Quantum Platform - Python & FastAPI Debugging Guide

**Purpose**: Structured debugging workflow for HYBA backend using Python and FastAPI  
**Updated**: June 26, 2026  
**Scope**: Backend diagnostics, API verification, mathematical claims validation  

---

## Quick Start: Running the Backend in Debug Mode

### Prerequisites
```bash
cd python_backend
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

### Start FastAPI with Auto-Reload & Logging
```bash
# Full debug output
uvicorn hyba_genesis_api.main:app --reload --log-level debug --port 8000

# Or with Python directly
python -m uvicorn hyba_genesis_api.main:app --reload --log-level debug --port 8000
```

### Verify Backend is Running
```bash
curl http://localhost:8000/health
# Expected: {"status": "ok", "version": "..."}
```

---

## Part 1: Testing API Endpoints

### 1.1 Using pytest (Recommended)

**Run all tests**:
```bash
pytest tests/ -v --tb=short
```

**Run specific test file**:
```bash
pytest tests/test_fault_tolerant_quantum.py -v
```

**Run with coverage**:
```bash
pytest tests/ --cov=python_backend --cov-report=html
```

**Run only failing tests**:
```bash
pytest tests/ --lf -v
```

**Run with verbose output and print statements**:
```bash
pytest tests/ -v -s
```

### 1.2 Using FastAPI's TestClient (In Python)

Create a file `debug_test.py`:

```python
from fastapi.testclient import TestClient
from hyba_genesis_api.main import app

client = TestClient(app)

# Test health endpoint
response = client.get("/health")
print(f"Health: {response.status_code}")
print(f"Response: {response.json()}")

# Test quantum endpoint
response = client.get("/api/v1/virtual-fault-tolerant-computers/status")
print(f"Quantum Status: {response.status_code}")
print(f"Response: {response.json()}")
```

Run it:
```bash
python debug_test.py
```

### 1.3 Using curl/httpie for Manual Testing

```bash
# Get quantum computer status
curl -X GET "http://localhost:8000/api/v1/virtual-fault-tolerant-computers/status"

# With pretty printing
curl -X GET "http://localhost:8000/api/v1/virtual-fault-tolerant-computers/status" | python -m json.tool

# Using httpie (more readable)
http GET localhost:8000/api/v1/virtual-fault-tolerant-computers/status
```

---

## Part 2: Debugging Common Issues

### Issue: Module Not Found

**Symptom**: `ModuleNotFoundError: No module named 'hyba_genesis_api'`

**Fix**:
```bash
# Ensure you're in python_backend directory
cd python_backend

# Reinstall in editable mode
pip install -e .

# Or set PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
```

### Issue: Port Already in Use

**Symptom**: `Address already in use`

**Fix**:
```bash
# Kill process on port 8000
# On Windows (PowerShell):
Stop-Process -Id (Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue).OwningProcess -Force

# On macOS/Linux:
lsof -ti:8000 | xargs kill -9
```

### Issue: Database Connection Error

**Symptom**: `pymongo.errors.ServerSelectionTimeoutError`

**Fix**:
```bash
# Check if MongoDB is running
mongosh  # or mongo

# Or disable MongoDB in dev
export HYBA_ENV=development
export SKIP_DB=true
```

### Issue: Import Circular Dependency

**Symptom**: `ImportError` or weird `None` values

**Debug**:
```python
import sys
import importlib

# Check import order
module = importlib.import_module('hyba_genesis_api.api.quantum_as_a_service')
print(f"Module loaded: {module}")
print(f"Module path: {module.__file__}")
```

---

## Part 3: Debugging Specific Modules

### 3.1 PULVINI Structure Verification

The A2 issue from the elevation report: automorphism group returns 1 instead of 120.

**Debug script** (`debug_pulvini.py`):

```python
"""Debug PULVINI structural certificate."""

from pythia_mining.pulvini_topology import StructuralCertificate, ADJACENCY_MAP
from pythia_mining.pulvini_group import compute_graph_automorphisms

# 1. Check adjacency map symmetry
print("=" * 60)
print("STEP 1: Verify Adjacency Map Symmetry")
print("=" * 60)

def verify_symmetric():
    """Ensure every edge is bidirectional."""
    asymmetric = []
    for node, neighbors in ADJACENCY_MAP.items():
        for neighbor in neighbors:
            if node not in ADJACENCY_MAP.get(neighbor, []):
                asymmetric.append((node, neighbor))
    return asymmetric

asymmetric_edges = verify_symmetric()
if asymmetric_edges:
    print(f"❌ Found {len(asymmetric_edges)} asymmetric edges:")
    for src, dst in asymmetric_edges:
        print(f"   {src} → {dst} (but {dst} ↛ {src})")
else:
    print("✅ All edges are bidirectional (symmetric)")

# 2. Check node degrees
print("\n" + "=" * 60)
print("STEP 2: Verify Node Degrees")
print("=" * 60)

d_nodes = list(range(20))  # Dodecahedral (D)
i_nodes = list(range(20, 32))  # Icosahedral (I)

print(f"D-nodes (0-19): {len(d_nodes)} nodes")
print(f"I-nodes (20-31): {len(i_nodes)} nodes")
print(f"Total: {len(d_nodes) + len(i_nodes)} nodes")

for node_type, nodes in [("D", d_nodes), ("I", i_nodes)]:
    degrees = [len(ADJACENCY_MAP.get(n, [])) for n in nodes]
    if degrees:
        avg_degree = sum(degrees) / len(degrees)
        print(f"  {node_type}-nodes: avg degree = {avg_degree:.1f}, min = {min(degrees)}, max = {max(degrees)}")

# 3. Compute automorphisms
print("\n" + "=" * 60)
print("STEP 3: Compute Automorphism Group")
print("=" * 60)

autos = compute_graph_automorphisms(ADJACENCY_MAP)
print(f"Automorphism group size: {len(autos)}")
print(f"Expected: 120 (5! for dodecahedral symmetry)")
print(f"Actual: {len(autos)}")

if len(autos) == 1:
    print("\n❌ PROBLEM: Only identity automorphism found!")
    print("   This means either:")
    print("   1. Adjacency map is not actually dodecahedral")
    print("   2. Adjacency map has asymmetric edges (would break symmetry)")
    print("   3. Automorphism computation has a bug")
    print("\n   Next: Check adjacency_edges_symmetric() above")
else:
    print(f"\n✅ Found {len(autos)} automorphisms (matches expected 120)")

# 4. Load structural certificate
print("\n" + "=" * 60)
print("STEP 4: Structural Certificate")
print("=" * 60)

cert = StructuralCertificate()
print(f"D-nodes: {cert.d_node_count} (expected 20)")
print(f"I-nodes: {cert.i_node_count} (expected 12)")
print(f"Automorphism group order: {cert.automorphism_group_order} (expected 120)")

if cert.automorphism_group_order == 120:
    print("\n✅ Structural certificate is valid")
else:
    print(f"\n❌ Structural certificate INVALID: expected 120, got {cert.automorphism_group_order}")
```

**Run it**:
```bash
cd python_backend
python ../debug_pulvini.py
```

**Interpret output**:
- If asymmetric edges found → Fix `ADJACENCY_MAP` in `pulvini_topology.py`
- If only identity automorphism → Either restate the claim or debug the math
- If degrees don't match → Verify the topology matches dodecahedral/icosahedral

### 3.2 Quantum-as-a-Service Verification

Debug script (`debug_quantum.py`):

```python
"""Debug Quantum-as-a-Service API."""

from fastapi.testclient import TestClient
from hyba_genesis_api.main import app

client = TestClient(app)

# Test endpoint paths include "virtual" qualifier
endpoints = [
    "/api/v1/virtual-fault-tolerant-computers/status",
    "/api/admin/virtual-fault-tolerant-computers/provision",
]

print("=" * 60)
print("Testing Quantum-as-a-Service Endpoints")
print("=" * 60)

for endpoint in endpoints:
    try:
        response = client.get(endpoint)
        print(f"\n✅ {endpoint}")
        print(f"   Status: {response.status_code}")
        data = response.json()
        if "claim_boundary" in data:
            print(f"   Claim Boundary: {data['claim_boundary']}")
    except Exception as e:
        print(f"\n❌ {endpoint}")
        print(f"   Error: {e}")

# Verify all responses include claim_boundary
print("\n" + "=" * 60)
print("Checking Claim Boundaries")
print("=" * 60)

response = client.get("/api/v1/virtual-fault-tolerant-computers/status")
data = response.json()
assert "claim_boundary" in data, "Missing claim_boundary field"
print("✅ All responses include claim_boundary")
```

**Run it**:
```bash
cd python_backend
python ../debug_quantum.py
```

---

## Part 4: Using Python Debugger (pdb)

### Setting a Breakpoint

In any Python file, add:

```python
import pdb

# Set breakpoint at this line
pdb.set_trace()

# Or in Python 3.7+:
breakpoint()
```

### Example: Debug PULVINI

```python
# In pulvini_topology.py
def compute_automorphisms():
    breakpoint()  # Execution will pause here
    # ... rest of function
```

**Then in the terminal**:
```bash
pytest tests/test_pulvini_structural_certificate.py -v -s
# When breakpoint is hit, you get an interactive prompt (Pdb)
# Commands:
# - n (next line)
# - s (step into function)
# - c (continue)
# - p variable_name (print variable)
# - l (list source code)
# - q (quit)
```

### Using VSCode Debugger

Create `.vscode/launch.json`:

```json
{
    "version": "0.2.0",
    "configurations": [
        {
            "name": "Python: FastAPI Debug",
            "type": "python",
            "request": "launch",
            "module": "uvicorn",
            "args": [
                "hyba_genesis_api.main:app",
                "--reload",
                "--log-level",
                "debug"
            ],
            "cwd": "${workspaceFolder}/python_backend",
            "jinja": true,
            "justMyCode": true
        },
        {
            "name": "Python: Pytest",
            "type": "python",
            "request": "launch",
            "module": "pytest",
            "args": [
                "tests/",
                "-v",
                "-s"
            ],
            "cwd": "${workspaceFolder}/python_backend",
            "justMyCode": true
        }
    ]
}
```

Then press `F5` in VSCode to start debugging.

---

## Part 5: Logging & Monitoring

### 5.1 Structured Logging

The backend should use structured logging. Example:

```python
import logging
from pythonjsonlogger import jsonlogger

logger = logging.getLogger(__name__)
handler = logging.StreamHandler()
formatter = jsonlogger.JsonFormatter()
handler.setFormatter(formatter)
logger.addHandler(handler)

# Usage
logger.info("Quantum computation started", extra={"computation_id": "qc_123"})
logger.error("PULVINI validation failed", extra={"reason": "automorphism != 120"})
```

### 5.2 Viewing Logs During Development

```bash
# Start backend with debug logging
uvicorn hyba_genesis_api.main:app --reload --log-level debug 2>&1 | tee debug.log

# In another terminal, watch logs in real-time
tail -f debug.log
```

### 5.3 Common Log Patterns

```python
# Log entry point
logger.info("API request", extra={
    "method": request.method,
    "path": request.url.path,
    "client": request.client.host
})

# Log computation progress
logger.debug("Computing automorphisms", extra={
    "graph_size": len(adjacency_map),
    "algorithm": "nauty"
})

# Log errors with context
logger.error("Automorphism computation failed", extra={
    "error": str(e),
    "adjacency_map_nodes": len(adjacency_map),
    "traceback": traceback.format_exc()
})
```

---

## Part 6: Validating Mathematical Claims

### Pattern: Before Exposing Via API

1. **Write the test first** (test-driven debugging)
   ```python
   # tests/test_claim.py
   def test_automorphism_group_order():
       cert = StructuralCertificate()
       assert cert.automorphism_group_order == 120, "Dodecahedral automorphisms should be 120"
   ```

2. **Run the test** (it will fail)
   ```bash
   pytest tests/test_claim.py -v
   # FAILED: expected 120, got 1
   ```

3. **Debug until it passes**
   ```python
   # Add debug prints
   print(f"ADJACENCY_MAP has {len(ADJACENCY_MAP)} nodes")
   print(f"Symmetry check: {verify_symmetric()}")
   print(f"Automorphisms: {compute_graph_automorphisms(ADJACENCY_MAP)}")
   ```

4. **Update API response only after test passes**
   ```python
   @app.get("/api/structural-certificate")
   async def get_structural_certificate():
       cert = StructuralCertificate()  # Now test is passing
       return {
           "automorphism_group_order": cert.automorphism_group_order,
           "claim_boundary": "mathematical model, not empirical measurement"
       }
   ```

---

## Part 7: Debugging Checklist

Before considering code "done":

- [ ] All tests pass: `pytest tests/ -v`
- [ ] No import errors: `python -c "import hyba_genesis_api"`
- [ ] API starts without errors: `uvicorn hyba_genesis_api.main:app`
- [ ] Health endpoint responds: `curl http://localhost:8000/health`
- [ ] Mathematical claims are tested: `pytest tests/test_*claim* -v`
- [ ] Claim boundaries are documented: `response.json()` includes `claim_boundary`
- [ ] No circular imports: Check `import` statements
- [ ] Logging is informative: Can trace execution via logs
- [ ] No hardcoded values without explanation: All numbers have comments/tests

---

## Part 8: Quick Reference Commands

```bash
# Start backend in debug mode
uvicorn hyba_genesis_api.main:app --reload --log-level debug

# Run all tests
pytest tests/ -v

# Run tests with coverage
pytest tests/ --cov=python_backend --cov-report=html

# Run only PULVINI tests
pytest tests/test_pulvini* -v

# Run only quantum tests
pytest tests/test_fault_tolerant_quantum.py -v

# Run a specific test
pytest tests/test_pulvini_structural_certificate.py::test_automorphism_group -v

# Check imports
python -c "import hyba_genesis_api; print('✅ Imports OK')"

# Type check
mypy python_backend/ --ignore-missing-imports

# Format code
black python_backend/

# Check style
flake8 python_backend/

# Run a debug script
python debug_pulvini.py

# View logs
tail -f logs/debug.log
```

---

## Part 9: Known Issues & Workarounds

### Issue: A2 PULVINI Automorphism Group Returns 1

**Status**: 🔴 BLOCKED  
**Root Cause**: Undetermined (asymmetric adjacency or computation bug)  
**Workaround**: Run `debug_pulvini.py` to identify root cause  
**Resolution**: Fix either adjacency map or automorphism computation  

### Issue: Port 8000 Already in Use

**Status**: ⚠️ COMMON  
**Workaround**: Kill existing process or use different port
```bash
uvicorn hyba_genesis_api.main:app --port 8001
```

### Issue: MongoDB Connection Timeout

**Status**: ⚠️ COMMON  
**Workaround**: Set `SKIP_DB=true` for development
```bash
export SKIP_DB=true
uvicorn hyba_genesis_api.main:app --reload
```

---

## Part 10: Next Steps

Based on the elevation report, debugging priorities are:

1. **A1 (Complete)**: Tests pass, API verified, ready for elevation
2. **A2 (Blocked)**: Needs math fixes
   - [ ] Run `debug_pulvini.py` to identify root cause
   - [ ] Fix asymmetric edges or automorphism computation
   - [ ] Run `pytest tests/test_pulvini_structural_certificate.py -v` until 24/24 pass
   - [ ] Then elevate

---

**For questions or issues, refer back to section headings above or the full elevation report in `ELEVATION_VERIFICATION_REPORT.md`.**

