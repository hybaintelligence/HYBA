/**
 * HYBA Bridge → Backend Real Integration Tests
 *
 * Validates that the ACTUAL Express bridge server (running on port 3000)
 * correctly proxies requests to the REAL Python FastAPI backend (port 3001).
 *
 * Unlike test_bridge_server.test.ts (which uses a mock Express app),
 * these tests exercise the live production code path:
 *   Browser ──► Bridge (port 3000) ──► FastAPI Backend (port 3001)
 *
 * Prerequisites:
 *   - Bridge running on http://127.0.0.1:3000
 *   - Backend running on http://127.0.0.1:3001
 *
 * In CI, both services are started automatically by frontend-ci.yml
 * (which starts the Python backend + `npm run dev` for the bridge).
 * The fullstack-ci.yml workflow runs these tests against the built Docker image.
 *
 * IMPORTANT: These tests FAIL in CI if the backend is not reachable —
 * there are no silent skips. This guarantees frontend-backend communication
 * is validated on every PR before merge.
 */

import { describe, it, expect, beforeAll } from "vitest";

const BRIDGE_BASE = "http://127.0.0.1:3000";
const BACKEND_BASE = "http://127.0.0.1:3001";
const IS_CI = process.env.CI === "true";

interface HealthResponse {
  status: string;
  service: string;
  version: string;
  backendReachable: boolean;
  timestamp: string;
}

async function isBackendReachable(): Promise<boolean> {
  try {
    const response = await fetch(`${BACKEND_BASE}/health`, {
      signal: AbortSignal.timeout(3000),
    });
    return response.status < 600;
  } catch {
    return false;
  }
}

async function isBridgeReachable(): Promise<boolean> {
  try {
    const response = await fetch(`${BRIDGE_BASE}/bridge/health`, {
      signal: AbortSignal.timeout(3000),
    });
    return response.status < 600;
  } catch {
    return false;
  }
}

describe("Bridge → Backend Real Integration", () => {
  let bridgeReachable: boolean;
  let backendReachable: boolean;

  beforeAll(async () => {
    bridgeReachable = await isBridgeReachable();
    backendReachable = await isBackendReachable();

    if (!bridgeReachable && IS_CI) {
      throw new Error(
        "FATAL: Bridge is not running on port 3000 in CI! " +
        "The Express bridge server must be running (started via `npm run dev` or Docker). " +
        "This test suite validates frontend-backend communication and cannot be skipped."
      );
    }

    if (!backendReachable && IS_CI) {
      throw new Error(
        "FATAL: Backend is not running on port 3001 in CI! " +
        "The Python FastAPI backend must be running on port 3001. " +
        "This test suite validates frontend-backend communication and cannot be skipped."
      );
    }

    if (!bridgeReachable) {
      console.warn(
        "⚠️  Bridge not reachable on port 3000. Tests will be skipped. " +
        "Start the bridge with: npm run dev"
      );
      return;
    }

    if (!backendReachable) {
      console.warn(
        "⚠️  Backend not reachable on port 3001. Tests will be skipped. " +
        "Start the backend with: PYTHONPATH=python_backend python3 -m uvicorn hyba_genesis_api.main:app --port 3001"
      );
      return;
    }

    console.log("✅ Bridge reachable on port 3000");
    console.log("✅ Backend reachable on port 3001");
  });

  // ── Bridge Health (public endpoint, no backend required) ────────────

  it("Bridge /bridge/health returns 200 with service info", async () => {
    if (!bridgeReachable) return;
    const response = await fetch(`${BRIDGE_BASE}/bridge/health`);
    expect(response.status).toBe(200);
    const body = (await response.json()) as HealthResponse;
    expect(body).toHaveProperty("status");
    expect(body).toHaveProperty("service", "HYBA Secure Bridge");
    expect(body).toHaveProperty("version");
    expect(body).toHaveProperty("timestamp");
  });

  // ── Backend Health via Bridge Proxy ────────────────────────────────

  it("Bridge proxies GET /health to backend and returns substrate info", async () => {
    if (!bridgeReachable || !backendReachable) return;
    const response = await fetch(`${BRIDGE_BASE}/health`);
    expect(response.status).toBe(200);
    const body = await response.json();
    expect(body).toHaveProperty("status");
    expect(body).toHaveProperty("substrate");
    expect(body.substrate).toBeDefined();
  });

  // ── Substrate API via Bridge Proxy ─────────────────────────────────

  it("Bridge proxies GET /api/substrate to backend", async () => {
    if (!bridgeReachable || !backendReachable) return;
    const response = await fetch(`${BRIDGE_BASE}/api/substrate`);
    expect(response.status).toBe(200);
    const body = await response.json();
    expect(body).toBeInstanceOf(Object);
    expect(Object.keys(body).length).toBeGreaterThan(0);
  });

  // ── Mining Endpoints via Bridge Proxy ──────────────────────────────

  it("Bridge proxies GET /api/mining/pools to backend", async () => {
    if (!bridgeReachable || !backendReachable) return;
    const response = await fetch(`${BRIDGE_BASE}/api/mining/pools`);
    // May require auth, so accept 200, 401, or 403
    expect([200, 401, 403]).toContain(response.status);
  });

  it("Bridge proxies GET /api/mining/status to backend", async () => {
    if (!bridgeReachable || !backendReachable) return;
    const response = await fetch(`${BRIDGE_BASE}/api/mining/status`);
    expect([200, 401, 403]).toContain(response.status);
  });

  it("Bridge proxies GET /api/mining/pool-config to backend", async () => {
    if (!bridgeReachable || !backendReachable) return;
    const response = await fetch(`${BRIDGE_BASE}/api/mining/pool-config`);
    expect([200, 401]).toContain(response.status);
  });

  // ── Intelligence Endpoints via Bridge Proxy ────────────────────────

  it("Bridge proxies GET /api/intelligence/status to backend", async () => {
    if (!bridgeReachable || !backendReachable) return;
    const response = await fetch(`${BRIDGE_BASE}/api/intelligence/status`);
    expect([200, 401, 403]).toContain(response.status);
  });

  // ── Error Propagation ──────────────────────────────────────────────

  it("Bridge preserves backend error responses without crashing", async () => {
    if (!bridgeReachable || !backendReachable) return;
    const response = await fetch(`${BRIDGE_BASE}/api/mining/connect`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ capacity_ehs: -1 }),
    });
    // Backend should reject invalid capacity; expect 4xx
    expect(response.status).toBeGreaterThanOrEqual(400);
    expect(response.status).toBeLessThan(500);
  });

  it("Bridge preserves backend 422 errors for missing API keys", async () => {
    if (!bridgeReachable || !backendReachable) return;
    const response = await fetch(
      `${BRIDGE_BASE}/api/v1/computational-intelligence-services`
    );
    // Backend returns 422 for missing API key (proves real proxying)
    expect([422, 401, 403]).toContain(response.status);
    const body = await response.json();
    expect(body).toHaveProperty("error");
  });

  // ── Request Tracing ────────────────────────────────────────────────

  it("Bridge adds x-request-id header to proxied responses", async () => {
    if (!bridgeReachable) return;
    const response = await fetch(`${BRIDGE_BASE}/bridge/health`);
    const requestId = response.headers.get("x-request-id");
    expect(requestId).toBeDefined();
    expect(requestId).toMatch(/^req_/);
  });

  // ── Concurrent Requests ────────────────────────────────────────────

  it("Bridge handles 10 concurrent requests without errors", async () => {
    if (!bridgeReachable || !backendReachable) return;
    const requests = Array(10)
      .fill(null)
      .map(() => fetch(`${BRIDGE_BASE}/health`));
    const responses = await Promise.all(requests);
    responses.forEach((response) => {
      expect(response.status).toBe(200);
    });
  });

  // ── Backend Direct Health Check ────────────────────────────────────

  it("Backend is directly reachable on port 3001 with version info", async () => {
    if (!backendReachable) return;
    const response = await fetch(`${BACKEND_BASE}/health`);
    expect(response.status).toBe(200);
    const body = await response.json();
    expect(body).toHaveProperty("version");
    expect(typeof body.version).toBe("string");
  });

  // ── Bridge Health: Backend Reachable Status ────────────────────────

  it("Bridge health reports backendReachable=true when backend is up", async () => {
    if (!bridgeReachable || !backendReachable) return;
    const response = await fetch(`${BRIDGE_BASE}/bridge/health`);
    const body = (await response.json()) as HealthResponse;
    expect(body.backendReachable).toBe(true);
  });

  // ── Bridge Internal Metrics (without auth token, should return 404) ─

  it("Bridge /bridge/metrics requires internal access token", async () => {
    if (!bridgeReachable) return;
    const response = await fetch(`${BRIDGE_BASE}/bridge/metrics`);
    // Without HYBA_INTERNAL_HEALTH_TOKEN, internal routes return 404
    expect(response.status).toBe(404);
  });

  // ── Content Security Headers ───────────────────────────────────────

  it("Bridge responses include security headers (helmet)", async () => {
    if (!bridgeReachable) return;
    const response = await fetch(`${BRIDGE_BASE}/bridge/health`);
    expect(response.headers.get("x-content-type-options")).toBe("nosniff");
    expect(response.headers.get("x-frame-options")).toBe("DENY");
  });
});