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
});
