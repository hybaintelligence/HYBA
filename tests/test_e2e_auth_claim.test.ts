import { describe, expect, test } from "vitest";

const BACKEND_URL = process.env.HYBA_BACKEND_URL || "http://127.0.0.1:3001";
const FRONTEND_URL = process.env.HYBA_FRONTEND_URL || "http://127.0.0.1:3000";

async function isServerAvailable(url: string): Promise<boolean> {
  try {
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 1500);
    const ok = await fetch(url, { signal: controller.signal }).then((r) => r.ok);
    clearTimeout(timeout);
    return ok;
  } catch {
    return false;
  }
}

describe("E2E auth + executive founder claim", () => {
  let backendAvailable = false;
  let frontendAvailable = false;

  beforeAll(async () => {
    backendAvailable = await isServerAvailable(`${BACKEND_URL}/health`);
    frontendAvailable = await isServerAvailable(`${FRONTEND_URL}/api/health`);
    if (!backendAvailable) {
      console.warn("Backend not available — skipping live E2E auth claim tests");
    }
  });

  test("backend health endpoint responds", async () => {
    if (!backendAvailable) {
      console.warn("SKIP: backend not available");
      return;
    }
    const res = await fetch(`${BACKEND_URL}/health`);
    expect(res.status).toBe(200);
    const data = await res.json();
    expect(data.status).toBe("ok");
  });

  test("frontend proxy forwards /api/health to backend when frontend is running", async () => {
    if (!frontendAvailable) {
      console.warn("SKIP: frontend dev server not available");
      return;
    }
    const res = await fetch(`${FRONTEND_URL}/api/health`);
    expect(res.status).toBe(200);
    const data = await res.json();
    expect(data.status).toBe("ok");
  });

  test("auth endpoints are mounted and enforce authentication", async () => {
    if (!backendAvailable) {
      console.warn("SKIP: backend not available");
      return;
    }
    const loginRes = await fetch(`${BACKEND_URL}/api/auth/login`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ username: "nonexistent", password: "nonexistent" }),
    });
    expect([401, 403]).toContain(loginRes.status);

    const claimRes = await fetch(`${BACKEND_URL}/api/auth/claim-role`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ username: "nonexistent", password: "nonexistent", claim_secret: "test" }),
    });
    expect([401, 403]).toContain(claimRes.status);
  });

  test("claim-role endpoint accepts POST with claim_secret field", async () => {
    if (!backendAvailable) {
      console.warn("SKIP: backend not available");
      return;
    }
    const res = await fetch(`${BACKEND_URL}/api/auth/claim-role`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ username: "operator", password: "operator", claim_secret: "test" }),
    });
    expect([200, 401, 403]).toContain(res.status);
    const data = await res.json();
    expect(data).toHaveProperty("success");
  });
});