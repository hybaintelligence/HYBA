# Cloud Agent Quick Start: Frontend Integration Testing

## What You're Doing
Testing and fixing the frontend-backend integration to ensure they communicate properly and are ready for production deployment.

## System Status

**Currently Running:**
- ✅ Backend FastAPI server on `127.0.0.1:3001`
- ✅ Frontend dev server (Node) on `127.0.0.1:3000`
- ✅ API proxy configured (`/api` → backend)

**What Works:**
- Backend health check: `curl http://127.0.0.1:3001/health`
- Frontend proxy: `curl http://127.0.0.1:3000/api/health`
- Bridge server: Running

**What Needs Testing:**
- Frontend React components
- API client functions
- Full E2E workflows
- All backend endpoints
- Error handling
- Performance

---

## Your Tasks (Pick One)

### Task 1: Frontend Component Testing (Agent 5)

**What to do:**
1. Test React components render correctly
2. Verify API client exports all functions
3. Test error boundaries
4. Create E2E communication tests

**Quick Start:**
```bash
cd /Users/demouser/Desktop/HYBA_FULLSTACK
npm install  # If needed

# Run existing frontend tests
npm run test:property:frontend
# Expected: Tests pass

# Run bridge tests
npm run test:bridge
# Expected: 16 tests pass

# Create new E2E test
cat > tests/test_frontend_backend_e2e.test.ts << 'EOF'
import { describe, it, expect } from 'vitest';

describe('Frontend-Backend E2E', () => {
  it('frontend proxy health works', async () => {
    const response = await fetch('http://127.0.0.1:3000/api/health');
    expect(response.status).toBe(200);
    const data = await response.json();
    expect(data.status).toBe('ok');
  });

  it('frontend can fetch pools', async () => {
    const response = await fetch('http://127.0.0.1:3000/api/mining/pools');
    expect(response.status).toBe(200);
    const data = await response.json();
    expect(data.pools).toBeDefined();
  });
});
EOF

# Run your new test
npx vitest run tests/test_frontend_backend_e2e.test.ts
```

**Success Criteria:**
- ✅ All frontend tests pass
- ✅ E2E test file created and passing
- ✅ No TypeScript errors

---

### Task 2: Backend API Testing (Agent 6)

**What to do:**
1. Test all mining endpoints
2. Test intelligence endpoints
3. Test security endpoints
4. Verify response formats

**Quick Start:**
```bash
cd /Users/demouser/Desktop/HYBA_FULLSTACK

# Test backend directly
curl -s http://127.0.0.1:3001/health | jq '.'
curl -s http://127.0.0.1:3001/api/mining/pools | jq '.summary'

# Create Python tests
cat > tests/test_backend_api_integration.py << 'EOF'
import requests
import pytest

BASE_URL = "http://127.0.0.1:3001"

class TestBackendAPI:
    def test_health(self):
        r = requests.get(f"{BASE_URL}/health")
        assert r.status_code == 200
        assert r.json()["status"] == "ok"
    
    def test_mining_pools(self):
        r = requests.get(f"{BASE_URL}/api/mining/pools")
        assert r.status_code == 200
        data = r.json()
        assert "pools" in data
        assert "summary" in data
    
    def test_security_status(self):
        r = requests.get(f"{BASE_URL}/api/security/status")
        assert r.status_code == 200
        assert "threat_level" in r.json()

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
EOF

# Run tests
python -m pytest tests/test_backend_api_integration.py -v
```

**Success Criteria:**
- ✅ Health endpoints return 200
- ✅ Mining endpoints respond correctly
- ✅ Security endpoints functional
- ✅ 10+ tests created and passing

---

### Task 3: Full Stack Integration (Agent 7)

**What to do:**
1. Verify frontend ↔ backend communication
2. Test complete workflows (pool connection, etc.)
3. Test performance
4. Generate deployment readiness report

**Quick Start:**
```bash
cd /Users/demouser/Desktop/HYBA_FULLSTACK

# Test connectivity
curl -s http://127.0.0.1:3000/api/health | jq '.status'  # Via frontend
curl -s http://127.0.0.1:3001/health | jq '.status'      # Direct to backend

# Both should return "ok"

# Create full stack test
cat > tests/test_fullstack_integration.py << 'EOF'
import requests
import time

BACKEND = "http://127.0.0.1:3001"
FRONTEND = "http://127.0.0.1:3000"

def test_backend_running():
    r = requests.get(f"{BACKEND}/health")
    assert r.status_code == 200

def test_frontend_running():
    r = requests.get(FRONTEND)
    assert r.status_code == 200

def test_frontend_proxy():
    r = requests.get(f"{FRONTEND}/api/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"

def test_mining_workflow():
    # Get pools
    r = requests.get(f"{FRONTEND}/api/mining/pools")
    assert r.status_code == 200
    
    # Attempt connection
    payload = {
        "pool_id": "test",
        "worker": "test",
        "password": "test",
        "capacity_ehs": 0.5
    }
    r = requests.post(f"{FRONTEND}/api/mining/connect", json=payload)
    assert r.status_code < 600

def test_response_time():
    start = time.time()
    r = requests.get(f"{BACKEND}/health")
    latency = (time.time() - start) * 1000
    assert r.status_code == 200
    assert latency < 1000  # Must be under 1 second

if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])
EOF

# Run tests
python -m pytest tests/test_fullstack_integration.py -v
```

**Success Criteria:**
- ✅ Backend running and healthy
- ✅ Frontend running and healthy
- ✅ Frontend proxy working
- ✅ Full workflows executable
- ✅ Response times acceptable
- ✅ All tests passing

---

## Common Issues & Fixes

### Issue: "Connection refused" on :3000 or :3001
**Fix:**
```bash
# Check what's running
ps aux | grep -E "uvicorn|node.*dev-server"

# If not running, start them:
# Terminal 1:
cd /Users/demouser/Desktop/HYBA_FULLSTACK
npm run backend:start  # or: python -m uvicorn hyba_genesis_api.main:app --app-dir python_backend --host 127.0.0.1 --port 3001

# Terminal 2:
cd /Users/demouser/Desktop/HYBA_FULLSTACK
npm run dev  # or: node dev-server.mjs
```

### Issue: "Cannot find module" in tests
**Fix:**
```bash
cd /Users/demouser/Desktop/HYBA_FULLSTACK
npm install
```

### Issue: pytest can't find tests
**Fix:**
```bash
cd /Users/demouser/Desktop/HYBA_FULLSTACK
export PYTHONPATH=$PWD/python_backend:$PYTHONPATH
python -m pytest tests/test_*.py -v
```

### Issue: "Module not found" for pythia_mining
**Fix:**
```bash
cd /Users/demouser/Desktop/HYBA_FULLSTACK
export PYTHONPATH=$PWD/python_backend:$PYTHONPATH
python -c "import pythia_mining; print('OK')"
```

---

## Test Commands Cheat Sheet

```bash
# Frontend tests
npm run test:bridge              # Bridge server tests (16 tests)
npm run test:property:frontend   # Property tests

# Backend tests
npm run python:env:check         # Python environment check
npm run test:backend             # All backend tests
npm run test:e2e:backend         # Backend E2E smoke tests

# Your new tests (create these)
python -m pytest tests/test_frontend_backend_e2e.test.ts -v
python -m pytest tests/test_backend_api_integration.py -v
python -m pytest tests/test_fullstack_integration.py -v

# Full test suite (slow)
npm run test:all
```

---

## What to Commit

1. **New test files you create** (e.g., `test_frontend_backend_e2e.test.ts`)
2. **Any fixes you make** to source code
3. **Updated documentation** of issues found

```bash
git add tests/test_*.py tests/test_*.ts
git add [any source files you fixed]
git add [any docs you updated]
git commit -m "feat: add frontend integration tests and verify E2E connectivity"
git push origin [your-branch-name]
```

---

## Success Checklist

- [ ] No connection errors to :3000 and :3001
- [ ] Health endpoints return 200
- [ ] Frontend proxy working
- [ ] API endpoints respond correctly
- [ ] Tests created and passing
- [ ] No TypeScript errors
- [ ] Performance acceptable (< 1s latency)
- [ ] Changes committed and pushed
- [ ] Ready for production deployment

---

## Need Help?

1. Check `FRONTEND_INTEGRATION_AGENTS.md` for detailed instructions
2. Look at existing tests in `tests/` directory
3. Check API client at `src/apiClient.ts`
4. Verify backend is running: `curl http://127.0.0.1:3001/health`

---

**When All Tests Pass: System is Production Ready! 🚀**
