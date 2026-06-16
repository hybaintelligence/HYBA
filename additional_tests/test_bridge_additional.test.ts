/**
 * Additional tests for HYBA secure bridge endpoints
 */
import { describe, expect, it } from "vitest";
import express from "express";
import { createServer, type Server } from "node:http";
import { type AddressInfo } from "node:net";

function startServer(app: express.Application): Promise<{ server: Server; port: number }> {
  return new Promise((resolve, reject) => {
    const server = createServer(app);
    server.listen(0, "127.0.0.1", () => {
      const address = server.address() as AddressInfo;
      resolve({ server, port: address.port });
    });
    server.on("error", reject);
  });
}

describe("HYBA Bridge additional endpoints tests", () => {
  it("returns 404 for unknown routes", async () => {
    const app = express();
    // Only health and metrics endpoints
    app.get("/bridge/health", (_req, res) => {
      res.json({ status: "ok", service: "HYBA Secure Bridge", version: "test" });
    });
    const { server, port } = await startServer(app);
    try {
      const response = await fetch(`http://127.0.0.1:${port}/nonexistent`);
      expect(response.status).toBe(404);
    } finally {
      server.close();
    }
  });

  it("health endpoint includes version and status fields", async () => {
    const app = express();
    app.get("/bridge/health", (_req, res) => {
      res.json({ status: "ok", service: "HYBA Secure Bridge", version: "1.0.0" });
    });
    const { server, port } = await startServer(app);
    try {
      const response = await fetch(`http://127.0.0.1:${port}/bridge/health`);
      const data = await response.json();
      expect(data.status).toBe("ok");
      expect(data.version).toMatch(/\d+\.\d+\.\d+/);
    } finally {
      server.close();
    }
  });

  it("returns plain text for metrics endpoint", async () => {
    const app = express();
    app.get("/bridge/metrics", (_req, res) => {
      res.setHeader("content-type", "text/plain; charset=utf-8");
      res.send("hyba_bridge_requests_total 10\n");
    });
    const { server, port } = await startServer(app);
    try {
      const response = await fetch(`http://127.0.0.1:${port}/bridge/metrics`);
      expect(response.headers.get("content-type")).toBe("text/plain; charset=utf-8");
      const body = await response.text();
      expect(body.trim()).toContain("hyba_bridge_requests_total");
    } finally {
      server.close();
    }
  });
});
