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

  const skip = !backendAvailable;

  test("backend health endpoint responds", async () => {
    const res = await fetch(`${BACKEND_URL}/health`);
    expect(res.status).toBe(200);
    const data = await res.json();
    expect(data.status).toBe("ok");
  }, skip ? 0 : undefined);

  test("frontend proxy forwards /api/health to backend", async () => {
    expect(frontendAvailable).toBe(true);
  }, skip ? 0 : undefined);

  test("login returns token and user role", async () => {
    const res = await fetch(`${BACKEND_URL}/api/auth/login`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ username: "operator", password: "operator" }),
    });
    expect(res.status).toBe(200);
    const data = await res.json();
    expect(data.success).toBe(true);
    expect(data.token).toBeTruthy();
    expect(data.user?.role).toBe("operator");
  }, skip ? 0 : undefined);

  test("claim-role upgrades operator to executive founder admin with valid secret", async () => {
    const secret = process.env.HYBA_FOUNDER_CLAIM_SECRET || "test-founder-secret";
    const res = await fetch(`${BACKEND_URL}/api/auth/claim-role`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ username: "operator", password: "operator", claim_secret: secret }),
    });
    expect(res.status).toBe(200);
    const data = await res.json();
    expect(data.success).toBe(true);
    expect(data.user?.role).toBe("ceo_heir_apparent");
  }, skip ? 0 : undefined);

  test("claim-role rejects invalid secret", async () => {
    const res = await fetch(`${BACKEND_URL}/api/auth/claim-role`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ username: "operator", password: "operator", claim_secret: "wrong-secret" }),
    });
    expect([401, 403]).toContain(res.status);
    const data = await res.json();
    expect(data.success).toBeFalsy();
  }, skip ? 0 : undefined);
});