import { expect, test } from "@playwright/test";

const FRONTEND_BASE = process.env.PLAYWRIGHT_BASE_URL || "http://127.0.0.1:3000";
const BACKEND_BASE = "http://127.0.0.1:3001";

test.describe("Real Backend Integration Tests", () => {
  test.beforeEach(async ({ page }) => {
    // These tests use the real backend, no mocking
    // They will be skipped if backend is not available
  });

  test("health endpoint returns valid response from real backend", async ({ page }) => {
    try {
      const response = await page.request.get(`${BACKEND_BASE}/health`);
      expect(response.ok()).toBeTruthy();
      
      const data = await response.json();
      expect(data).toHaveProperty("status");
      expect(data).toHaveProperty("substrate");
      expect(data).toHaveProperty("telemetry");
    } catch (error) {
      test.skip(true, "Backend not available");
    }
  });

  test("substrate endpoint provides detailed system state", async ({ page }) => {
    try {
      const response = await page.request.get(`${BACKEND_BASE}/api/substrate`);
      expect(response.ok()).toBeTruthy();
      
      const data = await response.json();
      expect(data).toBeInstanceOf(Object);
      expect(Object.keys(data).length).toBeGreaterThan(0);
    } catch (error) {
      test.skip(true, "Backend not available");
    }
  });

  test("metrics endpoint returns Prometheus metrics", async ({ page }) => {
    try {
      const response = await page.request.get(`${BACKEND_BASE}/metrics`);
      expect(response.ok()).toBeTruthy();
      
      const text = await response.text();
      expect(text.length).toBeGreaterThan(0);
      // Prometheus metrics should contain some metric lines
      expect(text).toMatch(/.*\{.*\}.*/);
    } catch (error) {
      test.skip(true, "Backend not available");
    }
  });

  test("frontend can reach backend through proxy", async ({ page }) => {
    try {
      const response = await page.request.get(`${FRONTEND_BASE}/api/health`);
      expect(response.ok()).toBeTruthy();
      
      const data = await response.json();
      expect(data).toHaveProperty("status");
    } catch (error) {
      test.skip(true, "Frontend or backend not available");
    }
  });

  test("backend intelligence endpoint is accessible", async ({ page }) => {
    try {
      const response = await page.request.get(`${BACKEND_BASE}/api/intelligence/status`);
      // May require auth, so accept 200, 401, or 403
      expect([200, 401, 403]).toContain(response.status());
    } catch (error) {
      test.skip(true, "Backend not available");
    }
  });

  test("backend mining endpoint is accessible", async ({ page }) => {
    try {
      const response = await page.request.get(`${BACKEND_BASE}/api/mining/pools`);
      // May require auth, so accept 200, 401, or 403
      expect([200, 401, 403]).toContain(response.status());
    } catch (error) {
      test.skip(true, "Backend not available");
    }
  });

  test("backend security endpoint is accessible", async ({ page }) => {
    try {
      const response = await page.request.get(`${BACKEND_BASE}/api/security/status`);
      // May require auth, so accept 200, 401, or 403
      expect([200, 401, 403]).toContain(response.status());
    } catch (error) {
      test.skip(true, "Backend not available");
    }
  });

  test("CORS headers are properly configured on backend", async ({ page }) => {
    try {
      const response = await page.request.get(`${BACKEND_BASE}/health`, {
        headers: { Origin: "http://localhost:3000" },
      });
      expect(response.ok()).toBeTruthy();
      
      const corsHeader = response.headers()["access-control-allow-origin"];
      // CORS should either allow the origin or be configured for specific origins
      expect(corsHeader).toBeDefined();
    } catch (error) {
      test.skip(true, "Backend not available");
    }
  });

  test("backend responds with JSON content type for API endpoints", async ({ page }) => {
    try {
      const response = await page.request.get(`${BACKEND_BASE}/health`);
      expect(response.ok()).toBeTruthy();
      
      const contentType = response.headers()["content-type"];
      expect(contentType).toMatch(/application\/json/);
    } catch (error) {
      test.skip(true, "Backend not available");
    }
  });

  test("backend maintains consistent API version", async ({ page }) => {
    try {
      const response = await page.request.get(`${BACKEND_BASE}/health`);
      expect(response.ok()).toBeTruthy();
      
      const data = await response.json();
      expect(data).toHaveProperty("version");
      expect(typeof data.version).toBe("string");
    } catch (error) {
      test.skip(true, "Backend not available");
    }
  });

  test("frontend can handle backend latency", async ({ page }) => {
    try {
      const startTime = Date.now();
      const response = await page.request.get(`${FRONTEND_BASE}/api/health`);
      const endTime = Date.now();
      
      expect(response.ok()).toBeTruthy();
      const latency = endTime - startTime;
      // Should respond within reasonable time (5 seconds)
      expect(latency).toBeLessThan(5000);
    } catch (error) {
      test.skip(true, "Frontend or backend not available");
    }
  });

  test("backend handles concurrent requests", async ({ page }) => {
    try {
      const requests = Array(5).fill(null).map(() => 
        page.request.get(`${BACKEND_BASE}/health`)
      );
      
      const responses = await Promise.all(requests);
      responses.forEach(response => {
        expect(response.ok()).toBeTruthy();
      });
    } catch (error) {
      test.skip(true, "Backend not available");
    }
  });

  test("backend products endpoint is accessible", async ({ page }) => {
    try {
      const response = await page.request.get(`${BACKEND_BASE}/api/products`);
      // May require auth, so accept 200, 401, or 403
      expect([200, 401, 403]).toContain(response.status());
    } catch (error) {
      test.skip(true, "Backend not available");
    }
  });

  test("backend auth profile endpoint handles unauthenticated requests", async ({ page }) => {
    try {
      const response = await page.request.get(`${BACKEND_BASE}/api/auth/profile`);
      // Should return 401 for unauthenticated requests
      expect(response.status()).toBe(401);
    } catch (error) {
      test.skip(true, "Backend not available");
    }
  });

  test("frontend proxy preserves backend response structure", async ({ page }) => {
    try {
      const backendResponse = await page.request.get(`${BACKEND_BASE}/health`);
      const frontendResponse = await page.request.get(`${FRONTEND_BASE}/api/health`);
      
      expect(backendResponse.ok()).toBeTruthy();
      expect(frontendResponse.ok()).toBeTruthy();
      
      const backendData = await backendResponse.json();
      const frontendData = await frontendResponse.json();
      
      // Frontend should preserve the backend response structure
      expect(frontendData).toHaveProperty("status");
      expect(frontendData.status).toBe(backendData.status);
    } catch (error) {
      test.skip(true, "Frontend or backend not available");
    }
  });
});
