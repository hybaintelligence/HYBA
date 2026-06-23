import { describe, expect, test, beforeEach } from "vitest";

const BACKEND_URL = process.env.HYBA_BACKEND_URL || "http://127.0.0.1:3001";
const FRONTEND_URL = process.env.HYBA_FRONTEND_URL || "http://127.0.0.1:3000";

function isServerAvailable(url: string): Promise<boolean> {
  try {
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 1500);
    return fetch(url, { signal: controller.signal })
      .then((r) => r.ok)
      .catch(() => false)
      .finally(() => clearTimeout(timeout));
  } catch {
    return Promise.resolve(false);
  }
}

let backendAvailable = false;
try {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), 1500);
  const healthCheck = await fetch(`${BACKEND_URL}/health`, { signal: controller.signal });
  clearTimeout(timeout);
  backendAvailable = healthCheck.ok;
} catch {
  backendAvailable = false;
}

const storage = new Map<string, string>();
beforeEach(() => {
  storage.clear();
});

function setToken(token: string) {
  storage.set("hyba_auth_token", token);
}
function clearToken() {
  storage.delete("hyba_auth_token");
}
function getToken() {
  return storage.get("hyba_auth_token") || null;
}

const requiresBackend = () =>
  describe("live backend E2E", () => {
    test.beforeAll(async () => {
      if (!backendAvailable) {
        console.warn("Backend not available — live E2E auth claim tests will fail");
      }
    });

    test("backend health endpoint responds", async () => {
      const res = await fetch(`${BACKEND_URL}/health`);
      expect(res.status).toBe(200);
      const data = await res.json();
      expect(data.status).toBe("ok");
    });

    test("frontend proxy forwards /api/health to backend", async () => {
      const res = await fetch(`${FRONTEND_URL}/api/health`);
      expect(res.status).toBe(200);
      const data = await res.json();
      expect(data.status).toBe("ok");
    });

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
      if (data.token) setToken(data.token);
    });

    test("profile endpoint returns current user", async () => {
      const token = getToken() || "";
      const res = await fetch(`${BACKEND_URL}/api/auth/profile`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      expect(res.status).toBe(200);
      const data = await res.json();
      expect(data.success).toBe(true);
      expect(data.user?.username).toBe("operator");
    });

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
      if (data.token) setToken(data.token);
    });

    test("after claim, profile reflects executive role", async () => {
      const token = getToken() || "";
      const res = await fetch(`${BACKEND_URL}/api/auth/profile`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      expect(res.status).toBe(200);
      const data = await res.json();
      expect(data.user?.role).toBe("ceo_heir_apparent");
    });

    test("claim-role rejects invalid secret", async () => {
      clearToken();
      const res = await fetch(`${BACKEND_URL}/api/auth/claim-role`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username: "operator", password: "operator", claim_secret: "wrong-secret" }),
      });
      expect([401, 403]).toContain(res.status);
      const data = await res.json();
      expect(data.success).toBeFalsy();
    });
  });

describe("E2E auth + executive founder claim", () => {
  requiresBackend();
});