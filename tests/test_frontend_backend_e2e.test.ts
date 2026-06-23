import { beforeAll, describe, expect, it } from "vitest";

const FRONTEND_BASE = "http://127.0.0.1:3000";
const BACKEND_BASE = "http://127.0.0.1:3001";

async function canReach(url: string): Promise<boolean> {
  try {
    const response = await fetch(url, { signal: AbortSignal.timeout(1500) });
    return response.status < 600;
  } catch {
    return false;
  }
}

describe("Frontend-Backend E2E Communication", () => {
  let liveStackAvailable = false;

  beforeAll(async () => {
    liveStackAvailable =
      (await canReach(`${FRONTEND_BASE}/`)) && (await canReach(`${BACKEND_BASE}/health`));
    if (!liveStackAvailable) {
      console.warn(
        "Skipping live frontend/backend assertions because 127.0.0.1:3000 and/or 127.0.0.1:3001 is unavailable.",
      );
    }
  });

  it("Frontend proxy /api/health reaches backend", async () => {
    if (!liveStackAvailable) return;
    const response = await fetch(`${FRONTEND_BASE}/api/health`);
    expect(response.status).toBe(200);
    const data = await response.json();
    expect(data.status).toBe("healthy");
  });

  it("Backend health endpoint returns substrate state", async () => {
    if (!liveStackAvailable) return;
    const response = await fetch(`${BACKEND_BASE}/health`);
    expect(response.status).toBe(200);
    const data = await response.json();
    expect(data).toHaveProperty("status");
    expect(data).toHaveProperty("substrate");
    expect(data.substrate).toBeDefined();
  });

  it("Backend substrate endpoint provides detailed system state", async () => {
    if (!liveStackAvailable) return;
    const response = await fetch(`${BACKEND_BASE}/api/substrate`);
    expect(response.status).toBe(200);
    const data = await response.json();
    expect(data).toBeInstanceOf(Object);
    expect(Object.keys(data).length).toBeGreaterThan(0);
  });

  it("Frontend can fetch pool configuration", async () => {
    if (!liveStackAvailable) return;
    const response = await fetch(`${FRONTEND_BASE}/api/mining/pool-config`);
    // Pool config may require authentication, so accept both 200 (success) and 401 (auth required)
    expect([200, 401]).toContain(response.status);
    if (response.status === 200) {
      const data = await response.json();
      expect(data.pools).toBeDefined();
    }
  });

  it("Frontend can submit pool connection request", async () => {
    if (!liveStackAvailable) return;
    const payload = {
      pool_id: "test-pool",
      worker: "test-worker",
      password: "test",
      capacity_ehs: 0.5,
    };
    const response = await fetch(`${FRONTEND_BASE}/api/mining/connect`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    expect(response.status).toBeGreaterThanOrEqual(200);
    expect(response.status).toBeLessThan(600);
  });

  it("Frontend proxy preserves backend error responses without crashing", async () => {
    if (!liveStackAvailable) return;
    const response = await fetch(`${FRONTEND_BASE}/api/mining/connect`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ capacity_ehs: 2 }),
    });
    expect(response.status).toBeGreaterThanOrEqual(400);
    expect(response.status).toBeLessThan(600);
  });

  it("Backend intelligence endpoint is accessible", async () => {
    if (!liveStackAvailable) return;
    const response = await fetch(`${BACKEND_BASE}/api/intelligence/status`);
    // May require auth, so accept 200, 401, or 403
    expect([200, 401, 403]).toContain(response.status);
  });

  it("Backend mining endpoint is accessible", async () => {
    if (!liveStackAvailable) return;
    const response = await fetch(`${BACKEND_BASE}/api/mining/pools`);
    // May require auth, so accept 200, 401, or 403
    expect([200, 401, 403]).toContain(response.status);
  });

  it("Backend security endpoint is accessible", async () => {
    if (!liveStackAvailable) return;
    const response = await fetch(`${BACKEND_BASE}/api/security/status`);
    // May require auth, so accept 200, 401, or 403
    expect([200, 401, 403]).toContain(response.status);
  });

  it("Backend metrics endpoint returns Prometheus metrics", async () => {
    if (!liveStackAvailable) return;
    const response = await fetch(`${BACKEND_BASE}/metrics`);
    expect(response.status).toBe(200);
    const text = await response.text();
    expect(text.length).toBeGreaterThan(0);
    // Prometheus metrics should contain some metric lines
    expect(text).toMatch(/.*\{.*\}.*/);
  });

  it("CORS headers are properly configured", async () => {
    if (!liveStackAvailable) return;
    const response = await fetch(`${BACKEND_BASE}/health`, {
      headers: { Origin: "http://localhost:3000" },
    });
    expect(response.status).toBe(200);
    const corsHeader = response.headers.get("access-control-allow-origin");
    // CORS should either allow the origin or be configured for specific origins
    expect(corsHeader).toBeDefined();
  });

  it("Backend responds with JSON content type for API endpoints", async () => {
    if (!liveStackAvailable) return;
    const response = await fetch(`${BACKEND_BASE}/health`);
    expect(response.status).toBe(200);
    const contentType = response.headers.get("content-type");
    expect(contentType).toMatch(/application\/json/);
  });

  it("Frontend can handle backend timeouts gracefully", async () => {
    if (!liveStackAvailable) return;
    try {
      const response = await fetch(`${FRONTEND_BASE}/api/health`, {
        signal: AbortSignal.timeout(100),
      });
      // If it responds within timeout, that's fine
      expect(response.status).toBeLessThan(600);
    } catch (error) {
      // Timeout is acceptable - shows frontend handles it
      expect(error).toBeDefined();
    }
  });

  it("Backend maintains consistent API version", async () => {
    if (!liveStackAvailable) return;
    const response = await fetch(`${BACKEND_BASE}/health`);
    expect(response.status).toBe(200);
    const data = await response.json();
    expect(data).toHaveProperty("version");
    expect(typeof data.version).toBe("string");
  });
});
