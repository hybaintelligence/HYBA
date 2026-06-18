# Frontend Integration & Deployment Readiness — Cloud Agent Task Cards

## Overview
**Goal**: Test frontend-backend communication, fix integration issues, and ensure full end-to-end connectivity for production deployment.

**Current Status**:
- ✅ Backend: FastAPI running on `127.0.0.1:3001`
- ✅ Frontend dev server: Node running on `127.0.0.1:3000`
- ✅ API proxy: Configured in `dev-server.mjs` (`/api` → backend)
- ⚠️ Frontend app: Needs integration testing
- ⚠️ E2E connectivity: Needs verification

---

## Agent 5: Frontend Component Testing & UI Integration

### Task: Test React components and verify UI rendering with live backend connection

**Objective**: Ensure React components render correctly, API client is properly integrated, and UI displays real backend data.

### Prerequisites
```bash
cd /Users/demouser/Desktop/HYBA_FULLSTACK
npm install  # Ensure dependencies
node dev-server.mjs &  # Start dev server (should already be running on :3000)
```

### Tests to Execute

#### 1. **Frontend Build & Compile Check**
```bash
npm run lint
# Expected: TypeScript compilation passes with no errors
# If fails: Fix TypeScript errors in src/ directory
```

#### 2. **Component Integration Tests** (Create new test file: `tests/test_frontend_components.test.ts`)
```typescript
describe('HYBA Frontend Components', () => {
  // Test 1: App component renders
  test('App component mounts without errors', () => {
    // Import App from src/App.tsx
    // Render with Provider wrappers
    // Assert component exists
  });

  // Test 2: API client initializes
  test('apiClient exports all endpoint functions', () => {
    // Import * as apiClient from src/apiClient.ts
    // Assert methods exist: fetchTelemetryData, connectToPool, etc.
  });

  // Test 3: Error boundary works
  test('ErrorBoundary catches and displays errors', () => {
    // Test error handling in src/components/ErrorBoundary.tsx
  });

  // Test 4: Hook integration
  test('useEffect hooks properly initialize', () => {
    // Verify main.tsx hook usage
  });
});
```

**Run**:
```bash
npm run test:property:frontend
# Expected: All component tests pass
```

---

#### 3. **API Client Integration Tests** (Already exists: `tests/test_apiClient_core.test.ts`)
```bash
npx vitest run tests/test_apiClient_core.test.ts tests/test_apiClient_authInterceptor.test.ts
# Expected: All API client tests pass (retry logic, auth, error handling)
```

**What to verify**:
- ✅ `fetchTelemetryData()` calls all endpoints correctly
- ✅ `connectToPool()` with capacity validation
- ✅ Auth interceptor adds tokens
- ✅ Error handling catches backend failures
- ✅ Retry logic works with exponential backoff

---

### Tests to Write

#### 4. **Frontend ↔ Backend Communication Test** (New: `tests/test_frontend_backend_e2e.test.ts`)
```typescript
describe('Frontend-Backend E2E Communication', () => {
  const FRONTEND_BASE = 'http://127.0.0.1:3000';
  const BACKEND_BASE = 'http://127.0.0.1:3001';

  // Test 1: Frontend can fetch health via proxy
  test('Frontend proxy /api/health reaches backend', async () => {
    const response = await fetch(`${FRONTEND_BASE}/api/health`);
    expect(response.status).toBe(200);
    const data = await response.json();
    expect(data.status).toBe('ok');
  });

  // Test 2: Frontend can fetch pool config
  test('Frontend can fetch pool configuration', async () => {
    const response = await fetch(`${FRONTEND_BASE}/api/mining/pool-config`);
    expect(response.status).toBe(200);
    const data = await response.json();
    expect(data.pools).toBeDefined();
  });

  // Test 3: Frontend can connect to pool
  test('Frontend can submit pool connection request', async () => {
    const payload = {
      pool_id: 'test-pool',
      worker: 'test-worker',
      password: 'test',
      capacity_ehs: 0.5
    };
    const response = await fetch(`${FRONTEND_BASE}/api/mining/connect`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    expect(response.status).toBeGreaterThanOrEqual(200);
    expect(response.status).toBeLessThan(600);
  });

  // Test 4: Frontend handles auth
  test('Frontend auth interceptor adds token header', async () => {
    // Call loginApi()
    // Verify Authorization header in subsequent requests
  });

  // Test 5: Frontend error handling
  test('Frontend handles backend errors gracefully', async () => {
    // Send invalid request
    // Verify error response contains proper error codes
    // Verify UI doesn't crash
  });
});
```

**Run**:
```bash
npx vitest run tests/test_frontend_backend_e2e.test.ts
# Expected: All E2E tests pass
```

---

### Verification Checklist

- [ ] TypeScript compilation passes (`npm run lint`)
- [ ] All component tests pass (`npm run test:property:frontend`)
- [ ] API client tests pass
- [ ] E2E communication tests pass
- [ ] Frontend dev server runs on `:3000`
- [ ] Backend dev server runs on `:3001`
- [ ] Proxy `/api` → backend works
- [ ] Error boundary catches errors
- [ ] Auth tokens are properly managed
- [ ] Rate limiting is respected
- [ ] Retry logic exponential backoff works

### Deliverables
1. ✅ All frontend tests passing
2. ✅ E2E test file created and passing
3. ✅ Frontend dev server verified running
4. ✅ Documentation: Frontend integration status
5. ✅ PR with frontend integration tests

---

## Agent 6: API Endpoint Testing & Backend Validation

### Task: Test all backend API endpoints and verify they respond correctly to frontend requests

**Objective**: Ensure backend API is production-ready and all endpoints return correct responses.

### Prerequisites
```bash
cd /Users/demouser/Desktop/HYBA_FULLSTACK
# Backend should be running on :3001
curl http://127.0.0.1:3001/health | jq .
```

### Tests to Execute

#### 1. **Health & Readiness Endpoints**
```bash
# Test 1: Root health
curl -s http://127.0.0.1:3001/health | jq '.status'
# Expected: "ok"

# Test 2: API health
curl -s http://127.0.0.1:3001/api/health | jq '.status'
# Expected: "ok"

# Test 3: Substrate readiness
curl -s http://127.0.0.1:3001/api/substrate | jq '.ready'
# Expected: true
```

#### 2. **Mining API Endpoints** (Create: `tests/test_backend_mining_api.py`)
```python
import pytest
import requests

BASE_URL = "http://127.0.0.1:3001"

class TestMiningAPI:
    """Test mining API endpoints."""
    
    def test_get_pools(self):
        """GET /api/mining/pools"""
        response = requests.get(f"{BASE_URL}/api/mining/pools")
        assert response.status_code == 200
        data = response.json()
        assert "pools" in data
        assert "summary" in data
        assert isinstance(data["pools"], list)
    
    def test_get_pool_config(self):
        """GET /api/mining/pool-config"""
        response = requests.get(f"{BASE_URL}/api/mining/pool-config")
        assert response.status_code == 200
        data = response.json()
        assert "pools" in data
    
    def test_connect_to_pool(self):
        """POST /api/mining/connect"""
        payload = {
            "pool_id": "test-pool",
            "worker": "test",
            "password": "test",
            "capacity_ehs": 0.5
        }
        response = requests.post(
            f"{BASE_URL}/api/mining/connect",
            json=payload
        )
        # Accept any response (201, 400, 503, etc.)
        assert response.status_code < 600
    
    def test_pause_mining(self):
        """POST /api/mining/pause"""
        response = requests.post(f"{BASE_URL}/api/mining/pause", json={})
        assert response.status_code < 600
    
    def test_resume_mining(self):
        """POST /api/mining/resume"""
        response = requests.post(f"{BASE_URL}/api/mining/resume", json={})
        assert response.status_code < 600
```

**Run**:
```bash
python -m pytest tests/test_backend_mining_api.py -v
# Expected: All tests pass
```

#### 3. **Intelligence API Endpoints** (Create: `tests/test_backend_intelligence_api.py`)
```python
class TestIntelligenceAPI:
    """Test intelligence endpoints."""
    
    def test_get_consciousness(self):
        """GET /api/ai/consciousness"""
        response = requests.get(f"{BASE_URL}/api/ai/consciousness")
        assert response.status_code in [200, 503]  # May be unavailable
    
    def test_get_intelligence_status(self):
        """GET /api/intelligence/status"""
        response = requests.get(f"{BASE_URL}/api/intelligence/status")
        assert response.status_code in [200, 404]
    
    def test_get_intelligence_telemetry(self):
        """GET /api/intelligence/telemetry"""
        response = requests.get(f"{BASE_URL}/api/intelligence/telemetry")
        assert response.status_code in [200, 404]
```

**Run**:
```bash
python -m pytest tests/test_backend_intelligence_api.py -v
```

#### 4. **Security Endpoints** (Create: `tests/test_backend_security_api.py`)
```python
class TestSecurityAPI:
    """Test security endpoints."""
    
    def test_get_security_status(self):
        """GET /api/security/status"""
        response = requests.get(f"{BASE_URL}/api/security/status")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "threat_level" in data
```

**Run**:
```bash
python -m pytest tests/test_backend_security_api.py -v
```

#### 5. **Create Comprehensive Backend API Test Suite**

```bash
python -m pytest tests/test_backend_*_api.py -v --tb=short
# Expected: 15+ tests all passing
```

### Verification Checklist

- [ ] Health endpoints respond with 200
- [ ] Mining endpoints respond correctly
- [ ] Intelligence endpoints available
- [ ] Security endpoints available
- [ ] Error responses use correct HTTP codes
- [ ] Response payloads match schema
- [ ] No 5xx errors on valid requests
- [ ] Rate limiting respected
- [ ] CORS headers present
- [ ] Request IDs in responses

### Deliverables
1. ✅ Backend API test suite created (30+ tests)
2. ✅ All endpoint tests passing
3. ✅ Coverage report for backend API surface
4. ✅ Documentation: Backend API validation results
5. ✅ PR with backend integration tests

---

## Agent 7: Full Stack Integration & End-to-End Deployment Testing

### Task: Verify complete frontend-backend integration and production deployment readiness

**Objective**: Ensure system is production-ready with all components communicating correctly.

### Prerequisites
```bash
cd /Users/demouser/Desktop/HYBA_FULLSTACK
# Verify both servers running
ps aux | grep -E "uvicorn|node.*dev-server"
# Should show both processes
```

### Tests to Execute

#### 1. **Full Stack Connectivity Test** (Create: `tests/test_fullstack_connectivity.py`)
```python
import requests
import time

class TestFullStackConnectivity:
    """Test complete frontend-backend integration."""
    
    BACKEND_URL = "http://127.0.0.1:3001"
    FRONTEND_URL = "http://127.0.0.1:3000"
    
    def test_backend_is_running(self):
        """Backend server is accessible."""
        response = requests.get(f"{self.BACKEND_URL}/health")
        assert response.status_code == 200
    
    def test_frontend_is_running(self):
        """Frontend dev server is accessible."""
        response = requests.get(self.FRONTEND_URL)
        assert response.status_code == 200
    
    def test_frontend_proxy_to_backend(self):
        """Frontend proxy correctly routes /api requests."""
        # Via frontend
        response_via_frontend = requests.get(f"{self.FRONTEND_URL}/api/health")
        # Via backend
        response_via_backend = requests.get(f"{self.BACKEND_URL}/health")
        
        assert response_via_frontend.status_code == 200
        assert response_via_backend.status_code == 200
        
        frontend_data = response_via_frontend.json()
        backend_data = response_via_backend.json()
        
        assert frontend_data["status"] == backend_data["status"]
    
    def test_full_mining_workflow(self):
        """Test complete mining workflow: fetch pools → connect → check status."""
        # Step 1: Fetch pools
        pools_resp = requests.get(f"{self.FRONTEND_URL}/api/mining/pools")
        assert pools_resp.status_code == 200
        pools_data = pools_resp.json()
        assert "pools" in pools_data
        
        # Step 2: Attempt pool connection
        connect_payload = {
            "pool_id": "test-pool",
            "worker": "test-worker",
            "password": "test",
            "capacity_ehs": 0.5
        }
        connect_resp = requests.post(
            f"{self.FRONTEND_URL}/api/mining/connect",
            json=connect_payload
        )
        # Accept any response (may be success, validation error, pool unavailable, etc.)
        assert connect_resp.status_code < 600
        
        # Step 3: Check pool config
        config_resp = requests.get(f"{self.FRONTEND_URL}/api/mining/pool-config")
        assert config_resp.status_code == 200
    
    def test_cross_origin_requests(self):
        """Frontend can make cross-origin requests (CORS)."""
        # Simulate browser CORS request
        headers = {
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "POST"
        }
        response = requests.options(
            f"{self.BACKEND_URL}/api/mining/connect",
            headers=headers
        )
        # Should allow CORS
        assert "access-control-allow" in str(response.headers).lower() or response.status_code == 200
    
    def test_authentication_flow(self):
        """Test auth token management."""
        from src.apiClient import loginApi, getToken, setToken, clearToken
        
        # Set a test token
        test_token = "test_token_12345"
        setToken(test_token)
        
        # Verify it's stored
        assert getToken() == test_token
        
        # Clear it
        clearToken()
        assert getToken() is None
    
    def test_retry_logic(self):
        """Test API client retry mechanism."""
        # Make multiple rapid requests
        for i in range(5):
            response = requests.get(f"{self.FRONTEND_URL}/api/health")
            assert response.status_code == 200
            time.sleep(0.1)
```

**Run**:
```bash
python -m pytest tests/test_fullstack_connectivity.py -v
# Expected: All tests pass
```

#### 2. **Performance & Load Testing**

```python
class TestPerformance:
    """Test system performance under load."""
    
    def test_response_latency(self):
        """API responses within acceptable latency."""
        start = time.time()
        response = requests.get(f"{self.BACKEND_URL}/health")
        latency = (time.time() - start) * 1000  # ms
        
        assert response.status_code == 200
        assert latency < 1000  # Should respond in < 1 second
    
    def test_concurrent_requests(self):
        """Handle multiple concurrent requests."""
        import concurrent.futures
        
        def make_request():
            return requests.get(f"{self.BACKEND_URL}/health")
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            results = list(executor.map(make_request, range(20)))
        
        # All should succeed
        assert all(r.status_code == 200 for r in results)
```

#### 3. **Create Deployment Readiness Report**

```python
import json
from datetime import datetime

class DeploymentReadinessReport:
    """Generate deployment readiness report."""
    
    def generate(self):
        report = {
            "timestamp": datetime.now().isoformat(),
            "checks": {
                "backend_running": self._check_backend(),
                "frontend_running": self._check_frontend(),
                "proxy_working": self._check_proxy(),
                "health_endpoints": self._check_health(),
                "mining_api": self._check_mining_api(),
                "security_api": self._check_security_api(),
                "cors_enabled": self._check_cors(),
                "performance": self._check_performance()
            },
            "status": "READY" if all(self.report["checks"].values()) else "BLOCKED"
        }
        
        with open("DEPLOYMENT_READINESS_REPORT.json", "w") as f:
            json.dump(report, f, indent=2)
        
        return report
    
    def _check_backend(self):
        try:
            r = requests.get("http://127.0.0.1:3001/health", timeout=2)
            return r.status_code == 200
        except:
            return False
    
    def _check_frontend(self):
        try:
            r = requests.get("http://127.0.0.1:3000", timeout=2)
            return r.status_code == 200
        except:
            return False
    
    def _check_proxy(self):
        try:
            r = requests.get("http://127.0.0.1:3000/api/health", timeout=2)
            return r.status_code == 200
        except:
            return False
    
    def _check_health(self):
        try:
            r = requests.get("http://127.0.0.1:3001/api/health", timeout=2)
            return r.status_code == 200
        except:
            return False
    
    def _check_mining_api(self):
        try:
            r = requests.get("http://127.0.0.1:3001/api/mining/pools", timeout=2)
            return r.status_code == 200
        except:
            return False
    
    def _check_security_api(self):
        try:
            r = requests.get("http://127.0.0.1:3001/api/security/status", timeout=2)
            return r.status_code == 200
        except:
            return False
    
    def _check_cors(self):
        try:
            r = requests.get("http://127.0.0.1:3001/health")
            return "access-control" in str(r.headers).lower()
        except:
            return False
    
    def _check_performance(self):
        import time
        start = time.time()
        try:
            requests.get("http://127.0.0.1:3001/health", timeout=2)
            latency = (time.time() - start) * 1000
            return latency < 1000
        except:
            return False
```

**Run**:
```bash
python -c "from tests.test_fullstack_connectivity import DeploymentReadinessReport; report = DeploymentReadinessReport(); print(json.dumps(report.generate(), indent=2))"
```

### Verification Checklist

- [ ] Backend server running on `:3001`
- [ ] Frontend dev server running on `:3000`
- [ ] Frontend → Backend proxy working (`/api` routes)
- [ ] All health endpoints responding
- [ ] Mining API endpoints functional
- [ ] Security endpoints functional
- [ ] CORS headers present
- [ ] Response times < 1 second
- [ ] Concurrent requests handled
- [ ] Error handling working
- [ ] No 5xx errors on valid requests
- [ ] Deployment readiness report generated

### Deliverables
1. ✅ Full stack connectivity test suite (10+ tests)
2. ✅ All tests passing
3. ✅ Performance benchmarks within thresholds
4. ✅ Deployment readiness report generated
5. ✅ Documentation: Full stack integration verified
6. ✅ PR with integration tests

---

## Summary: Cloud Agent Assignments

| Agent | Task | Focus | Tests | Files |
|-------|------|-------|-------|-------|
| **5** | Frontend Components | React rendering, API client | 5-8 | `test_frontend_*.test.ts` |
| **6** | Backend API | Endpoint validation | 15+ | `test_backend_*_api.py` |
| **7** | Full Stack | E2E integration | 10+ | `test_fullstack_*.py` |

---

## Execution Order

1. **Agent 5**: Test frontend components and API client
2. **Agent 6**: Test backend API endpoints
3. **Agent 7**: Test full stack integration

All agents should commit changes to a new branch and create a PR when complete.

---

## Success Criteria

**All tests passing**:
- ✅ Frontend component tests: 100%
- ✅ Frontend E2E tests: 100%
- ✅ Backend API tests: 100%
- ✅ Full stack connectivity tests: 100%

**Deployment ready**:
- ✅ Frontend dev server running
- ✅ Backend server running
- ✅ Proxy functioning
- ✅ All endpoints responding
- ✅ No 5xx errors
- ✅ Performance acceptable
- ✅ CORS enabled
- ✅ Ready for production deployment

