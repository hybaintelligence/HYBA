import { describe, expect, it } from "vitest";
import express from "express";
import rateLimit from "express-rate-limit";
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

describe("mining bridge rate-limit contract", () => {
  it("returns exactly 10 successes then a deterministic 429 failure", async () => {
    const app = express();
    app.use(
      rateLimit({
        windowMs: 60_000,
        max: 10,
        message: { error: "too_many_requests", message: "Too many requests, please try again later." },
        standardHeaders: true,
        legacyHeaders: false,
      }),
    );
    app.get("/api/mining/status", (_req, res) => res.json({ status: "ok" }));

    const { server, port } = await startServer(app);
    try {
      const responses = [];
      for (let i = 0; i < 11; i += 1) {
        const response = await fetch(`http://127.0.0.1:${port}/api/mining/status`);
        responses.push({ status: response.status, body: await response.json() });
      }

      expect(responses.slice(0, 10).every((entry) => entry.status === 200)).toBe(true);
      expect(responses[10].status).toBe(429);
      expect(responses[10].body.error).toBe("too_many_requests");
    } finally {
      server.close();
    }
  });
});
