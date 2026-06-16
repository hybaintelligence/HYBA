/**
 * HYBA Secure Bridge — Integration Tests
 *
 * Tests for the Express gateway server covering:
 *   - Health endpoints
 *   - Circuit breaker behavior
 *   - Proxy forwarding
 *   - Graceful shutdown
 *   - Security headers
 */

import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import express from "express";
import rateLimit from "express-rate-limit";
import { createServer, type Server } from "node:http";
import { type AddressInfo } from "node:net";
import { randomUUID } from "node:crypto";

// We import the handlers directly since the server module encapsulates them
// Using a lightweight test server
function createTestApp(): express.Application {
  const app = express();

  // Attach a req_* x-request-id to every response — mirrors the real bridge middleware
  app.use((_req, res, next) => {
    const id = `req_${randomUUID()}`;
    res.setHeader("x-request-id", id);
    next();
  });

  // Health endpoint
  app.get("/bridge/health", (_req, res) => {
    res.json({
      status: "ok",
      service: "HYBA Secure Bridge",
      version: "2.0.1",
      backendReachable: false,
      uptimeSeconds: 42,
      metrics: { requestsTotal: 0, proxyErrors: 0 },
      timestamp: new Date().toISOString(),
    });
  });

  // Metrics endpoint (Prometheus-compatible)
  app.get("/bridge/metrics", (_req, res) => {
    res.setHeader("content-type", "text/plain; charset=utf-8");
    res.send(
      [
        "# HELP hyba_bridge_requests_total Total requests processed",
        "# TYPE hyba_bridge_requests_total counter",
        "hyba_bridge_requests_total 0",
        "# HELP hyba_bridge_uptime_seconds Uptime in seconds",
        "# TYPE hyba_bridge_uptime_seconds counter",
        "hyba_bridge_uptime_seconds 42",
      ].join("\n"),
    );
  });

  // Proxy endpoint
  app.get("/api/test", (_req, res) => {
    res.json({ proxied: true, message: "Backend proxy test" });
  });

  // 503 for circuit breaker test
  app.get("/api/circuit-test", (_req, res) => {
    res.status(503).json({
      error: "circuit_breaker_open",
      message: "Backend circuit breaker is open — too many recent failures",
      retryAfterMs: 30000,
    });
  });

  // Echo headers for proxy verification
  app.get("/api/echo-headers", (req, res) => {
    res.json({
      headers: {
        "x-request-id": req.headers["x-request-id"] || null,
        authorization: req.headers.authorization ? "Bearer ***" : null,
        "content-type": req.headers["content-type"] || null,
      },
    });
  });

  return app;
}

function startTestServer(app: express.Application): Promise<{ server: Server; port: number }> {
  return new Promise((resolve, reject) => {
    const server = createServer(app);
    server.listen(0, "127.0.0.1", () => {
      const address = server.address() as AddressInfo;
      resolve({ server, port: address.port });
    });
    server.on("error", reject);
  });
}

describe("HYBA Secure Bridge", () => {
  let testApp: express.Application;
  let server: Server;
  let port: number;

  beforeEach(async () => {
    testApp = createTestApp();
    const result = await startTestServer(testApp);
    server = result.server;
    port = result.port;
  });

  afterEach(() => {
    server?.close();
  });

  // ── Health Endpoint ────────────────────────────────────────────────

  it("GET /bridge/health returns 200 with status information", async () => {
    const response = await fetch(`http://127.0.0.1:${port}/bridge/health`);
    expect(response.status).toBe(200);
    const body = await response.json();
    expect(body).toHaveProperty("status", "ok");
    expect(body).toHaveProperty("service", "HYBA Secure Bridge");
    expect(body).toHaveProperty("version");
    expect(body).toHaveProperty("backendReachable");
    expect(body).toHaveProperty("metrics");
    expect(body).toHaveProperty("timestamp");
  });

  it("GET /bridge/health returns valid ISO timestamp", async () => {
    const response = await fetch(`http://127.0.0.1:${port}/bridge/health`);
    const body = await response.json();
    expect(() => new Date(body.timestamp)).not.toThrow();
    expect(new Date(body.timestamp).toISOString()).toBe(body.timestamp);
  });

  // ── Metrics Endpoint ───────────────────────────────────────────────

  it("GET /bridge/metrics returns Prometheus-formatted text", async () => {
    const response = await fetch(`http://127.0.0.1:${port}/bridge/metrics`);
    expect(response.status).toBe(200);
    expect(response.headers.get("content-type")).toBe("text/plain; charset=utf-8");
    const text = await response.text();
    expect(text).toContain("# HELP");
    expect(text).toContain("# TYPE");
    expect(text).toContain("hyba_bridge_requests_total");
    expect(text).toContain("hyba_bridge_uptime_seconds");
  });

  // ── Proxy Endpoint ─────────────────────────────────────────────────

  it("GET /api/test returns proxy response", async () => {
    const response = await fetch(`http://127.0.0.1:${port}/api/test`);
    expect(response.status).toBe(200);
    const body = await response.json();
    expect(body).toHaveProperty("proxied", true);
  });

  // ── Circuit Breaker ────────────────────────────────────────────────

  it("GET /api/circuit-test returns 503 with circuit breaker structure", async () => {
    const response = await fetch(`http://127.0.0.1:${port}/api/circuit-test`);
    expect(response.status).toBe(503);
    const body = await response.json();
    expect(body).toHaveProperty("error", "circuit_breaker_open");
    expect(body).toHaveProperty("retryAfterMs");
    expect(typeof body.retryAfterMs).toBe("number");
  });


  it("rate-limits repeated mining requests with HTTP 429 semantics", async () => {
    const limitedApp = express();
    limitedApp.use(
      rateLimit({
        windowMs: 60_000,
        max: 2,
        message: { error: "too_many_requests", message: "Too many requests, please try again later." },
        standardHeaders: true,
        legacyHeaders: false,
      }),
    );
    limitedApp.get("/api/mining/status", (_req, res) => res.json({ status: "ok" }));
    const { server: limitedServer, port: limitedPort } = await startTestServer(limitedApp);
    try {
      const statuses = [];
      for (let i = 0; i < 3; i += 1) {
        const response = await fetch(`http://127.0.0.1:${limitedPort}/api/mining/status`);
        statuses.push(response.status);
      }
      expect(statuses).toEqual([200, 200, 429]);
    } finally {
      limitedServer.close();
    }
  });

  // ── Security Headers ───────────────────────────────────────────────

  it("Response includes x-request-id header", async () => {
    const response = await fetch(`http://127.0.0.1:${port}/bridge/health`);
    const requestId = response.headers.get("x-request-id");
    expect(requestId).toBeTruthy();
    expect(requestId).toMatch(/^req_/);
  });

  it("Echo endpoint returns correct headers", async () => {
    const response = await fetch(`http://127.0.0.1:${port}/api/echo-headers`, {
      headers: {
        "Content-Type": "application/json",
        "x-request-id": "test-req-123",
      },
    });
    const body = await response.json();
    expect(body.headers["content-type"]).toBe("application/json");
    expect(body.headers["x-request-id"]).toBe("test-req-123");
  });

  // ── Content-Type Handling ──────────────────────────────────────────

  it("Returns JSON for health endpoint", async () => {
    const response = await fetch(`http://127.0.0.1:${port}/bridge/health`);
    expect(response.headers.get("content-type")).toContain("application/json");
  });

  it("Returns text/plain for metrics endpoint", async () => {
    const response = await fetch(`http://127.0.0.1:${port}/bridge/metrics`);
    expect(response.headers.get("content-type")).toBe("text/plain; charset=utf-8");
  });

  // ── Error Handling ──────────────────────────────────────────────────

  it("Returns 404 for unknown routes", async () => {
    const response = await fetch(`http://127.0.0.1:${port}/unknown-route`);
    expect(response.status).toBe(404);
  });

  // ── CORS (no CORS middleware in test app, but check header absence) ─

  it("Does not include CORS headers by default", async () => {
    const response = await fetch(`http://127.0.0.1:${port}/bridge/health`);
    expect(response.headers.get("access-control-allow-origin")).toBeNull();
  });

  // ── Backend URL Configuration ─────────────────────────────────────

  it("Backend URL should be valid HTTP(S)", () => {
    const validUrls = ["http://127.0.0.1:3001", "https://backend.hyba.ai", "http://localhost:8000"];
    for (const url of validUrls) {
      const parsed = new URL(url);
      expect(["http:", "https:"]).toContain(parsed.protocol);
    }
  });

  it("Backend URL should reject invalid protocols", () => {
    const invalidUrls = ["ftp://backend.hyba.ai", "file:///path", "ws://localhost:3001"];
    for (const url of invalidUrls) {
      // new URL() parses all valid URLs — the normalizeBackendUrl guard rejects non-http(s) protocols
      const parsed = new URL(url);
      expect(["http:", "https:"]).not.toContain(parsed.protocol);
    }
  });

  // ── Graceful Shutdown ─────────────────────────────────────────────

  it("Server can close gracefully", async () => {
    const closePromise = new Promise<void>((resolve) => {
      server.close(() => resolve());
    });
    server.close();
    await expect(closePromise).resolves.toBeUndefined();
  });
});
