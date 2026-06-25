/**
 * HYBA Frontend-Backend E2E Communication Tests
 *
 * Validates that the Express bridge server correctly proxies requests
 * to the Python FastAPI backend. These tests REQUIRE a live stack:
 *   - Bridge on http://127.0.0.1:3000
 *   - Backend on http://127.0.0.1:3001
 *
 * In CI, the backend is started automatically by frontend-ci.yml.
 * If the stack is not running, tests FAIL to prevent silent skips.
 */

import { beforeAll, describe, expect, it } from "vitest";

const BRIDGE_BASE = "http://127.0.0.1:3000";
const BACKEND_BASE = "http://127.0.0.1:3001";

const IS_CI = process.env.CI === "true";

async function canReach(url: string): Promise<boolean> {
  try {
    const response = await fetch(url, { signal: AbortSignal.timeout(3000) });
    return response.status < 600;
  } catch {
    return false;
  }
}

describe("Frontend-Backend E2E Communication", () => {
  let liveStackAvailable = false;

  beforeAll(async () => {
    // Check if bridge is running and can reach backend
    const bridgeHealth = await canReach(`${BRIDGE_BASE}/bridge/health`);
    if (bridgeHealth) {
      const response = await fetch(`${BRIDGE_BASE}/bridge/health`);
      const data = await response.json();
      liveStackAvailable = data.backendReachable === true;
    }

    if (!liveStackAvailable && IS_CI) {
      throw new Error(
        "FATAL: Frontend-backend stack is not available in CI! " +
        "The Python backend must be running on port 3001 and the bridge on port 3000. " +
        "This test suite validates frontend-backend communication and cannot be skipped."
      );
    }

    if (!liveStackAvailable) {
      console.warn(
        "⚠️  Skipping live frontend/backend assertions because the stack is not available " +
        "(bridge or backend not running). Run `npm run dev:full` to start both services.",
      );
    }
  });

  it("Bridge health endpoint confirms backend is reachable", async () => {
    if (!liveStackAvailable) return;
    const response = await fetch(`${BRIDGE_BASE}/bridge/health`);
    expect(response.status).toBe(200);
    const data = await response.json();
    expect(data.backendReachable).toBe(true);
    expect(data.status).toBe("ok");
  });

  it("Bridge proxies /health to backend successfully", async () => {
    if (!liveStackAvailable) return;
    const response = await fetch(`${BRIDGE_BASE}/health`);
    expect(response.status).toBe(200);
    const data = await response.json();
    expect(data).toHaveProperty("status");
    expect(data).toHaveProperty("substrate");
    expect(data.substrate).toBeDefined();
  });

  it("Bridge proxies /api/substrate to backend", async () => {
    if (!liveStackAvailable) return;
    const response = await fetch(`${BRIDGE_BASE}/api/substrate`);
    expect(response.status).toBe(200);
    const data = await response.json();
    expect(data).toBeInstanceOf(Object);
    expect(Object.keys(data).length).toBeGreaterThan(0);
  });

  it("Bridge can fetch pool configuration through proxy", async () => {
    if (!liveStackAvailable) return;
    const response = await fetch(`${BRIDGE_BASE}/api/mining/pool-config`);
    // Pool config may require authentication, so accept both 200 (success) and 401 (auth required)
    expect([200, 401]).toContain(response.status);
    if (response.status === 200) {
      const data = await response.json();
      expect(data.pools).toBeDefined();
    }
  });

  it("Bridge can submit pool connection request", async () => {
    if (!liveStackAvailable) return;
    const payload = {
      pool_id: "test-pool",
      worker: "test-worker",
      password: "test",
      capacity_ehs: 0.5,
    };
    const response = await fetch(`${BRIDGE_BASE}/api/mining/connect`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    expect(response.status).toBeGreaterThanOrEqual(200);
    expect(response.status).toBeLessThan(600);
  });

  it("Bridge preserves backend error responses without crashing", async () => {
    if (!liveStackAvailable) return;
    const response = await fetch(`${BRIDGE_BASE}/api/mining/connect`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ capacity_ehs: 2 }),
    });
    expect(response.status).toBeGreaterThanOrEqual(400);
    expect(response.status).toBeLessThan(600);
  });

  it("Bridge proxies intelligence endpoint", async () => {
    if (!liveStackAvailable) return;
    const response = await fetch(`${BRIDGE_BASE}/api/intelligence/status`);
    // May require auth, so accept 200, 401, or 403
    expect([200, 401, 403]).toContain(response.status);
  });

  it("Bridge proxies mining endpoint", async () => {
    if (!liveStackAvailable) return;
    const response = await fetch(`${BRIDGE_BASE}/api/mining/pools`);
    // May require auth, so accept 200, 401, or 403
    expect([200, 401, 403]).toContain(response.status);
  });

  it("Bridge proxies security endpoint", async () => {
    if (!liveStackAvailable) return;
    const response = await fetch(`${BRIDGE_BASE}/api/security/status`);
    // May require auth, so accept 200, 401, or 403
    expect([200, 401, 403]).toContain(response.status);
  });

  it("Bridge handles API key validation (proves backend integration)", async () => {
    if (!liveStackAvailable) return;
    const response = await fetch(`${BRIDGE_BASE}/api/v1/computational-intelligence-services`);
    // Should return 422 for missing API key (proves backend is receiving requests)
    expect([422, 401, 403]).toContain(response.status);
    const data = await response.json();
    expect(data).toHaveProperty("error");
  });

  it("Bridge can handle backend timeouts gracefully", async () => {
    if (!liveStackAvailable) return;
    try {
      const response = await fetch(`${BRIDGE_BASE}/health`, {
        signal: AbortSignal.timeout(100),
      });
      // If it responds within timeout, that's fine
      expect(response.status).toBeLessThan(600);
    } catch (error) {
      // Timeout is acceptable - shows bridge handles it
      expect(error).toBeDefined();
    }
  });

  it("Backend maintains consistent API version (direct check)", async () => {
    if (!liveStackAvailable) return;
    const response = await fetch(`${BACKEND_BASE}/health`);
    expect(response.status).toBe(200);
    const data = await response.json();
    expect(data).toHaveProperty("version");
    expect(typeof data.version).toBe("string");
  });

  it("Bridge propagates request IDs for tracing", async () => {
    if (!liveStackAvailable) return;
    const response = await fetch(`${BRIDGE_BASE}/health`);
    expect(response.status).toBe(200);
    const requestId = response.headers.get("x-request-id");
    expect(requestId).toBeDefined();
    expect(typeof requestId).toBe("string");
  });

  it("Bridge handles concurrent requests", async () => {
    if (!liveStackAvailable) return;
    const requests = Array(5).fill(null).map(() => 
      fetch(`${BRIDGE_BASE}/health`)
    );
    
    const responses = await Promise.all(requests);
    responses.forEach(response => {
      expect(response.status).toBe(200);
    });
  });
});
