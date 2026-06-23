import { describe, expect, test } from "vitest";
import { claimRoleApi, loginApi, setToken, clearToken } from "../src/apiClient";

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
      const res = await loginApi({ username: "operator", password: "operator" });
      expect(res.success).toBe(true);
      expect(res.token).toBeTruthy();
      expect(res.user?.role).toBe("operator");
      if (res.token) setToken(res.token);
    });

    test("profile endpoint returns current user", async () => {
      const res = await fetch(`${BACKEND_URL}/api/auth/profile`, {
        headers: { Authorization: `Bearer ${localStorage.getItem("hyba_auth_token") || ""}` },
      });
      expect(res.status).toBe(200);
      const data = await res.json();
      expect(data.success).toBe(true);
      expect(data.user?.username).toBe("operator");
    });

    test("claim-role upgrades operator to executive founder admin with valid secret", async () => {
      const secret = process.env.HYBA_FOUNDER_CLAIM_SECRET || "test-founder-secret";
      const res = await claimRoleApi(
        { username: "operator", password: "operator" },
        secret,
      );
      expect(res.success).toBe(true);
      expect(res.user?.role).toBe("ceo_heir_apparent");
      if (res.token) setToken(res.token);
    });

    test("after claim, profile reflects executive role", async () => {
      const token = localStorage.getItem("hyba_auth_token") || "";
      const res = await fetch(`${BACKEND_URL}/api/auth/profile`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      expect(res.status).toBe(200);
      const data = await res.json();
      expect(data.user?.role).toBe("ceo_heir_apparent");
    });

    test("claim-role rejects invalid secret", async () => {
      clearToken();
      const res = await claimRoleApi(
        { username: "operator", password: "operator" },
        "wrong-secret",
      );
      expect(res.success).toBe(false);
    });
  });

describe("E2E auth + executive founder claim", () => {
  requiresBackend();
});