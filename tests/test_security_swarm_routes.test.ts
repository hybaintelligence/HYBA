import { afterEach, describe, expect, it } from "vitest";
import express from "express";
import { createServer, type Server } from "node:http";
import { type AddressInfo } from "node:net";
import { SecuritySwarmAgent } from "../src/core/security_swarm";
import { registerSecuritySwarmRoutes } from "../src/server";

async function startSecurityRoutesServer(): Promise<{ server: Server; baseUrl: string }> {
  const app = express();
  app.use(express.json());
  registerSecuritySwarmRoutes(app, new SecuritySwarmAgent());

  return new Promise((resolve, reject) => {
    const server = createServer(app);
    server.listen(0, "127.0.0.1", () => {
      const address = server.address() as AddressInfo;
      resolve({ server, baseUrl: `http://127.0.0.1:${address.port}` });
    });
    server.on("error", reject);
  });
}

describe("HYBA security swarm HTTP routes", () => {
  let server: Server | null = null;

  afterEach(() => {
    server?.close();
    server = null;
  });

  it("integration: GET /api/security/status returns safe telemetry without raw syndrome bits", async () => {
    const started = await startSecurityRoutesServer();
    server = started.server;

    const response = await fetch(`${started.baseUrl}/api/security/status`);
    const body = await response.json();

    expect(response.status).toBe(200);
    expect(body.defense_systems.stabilizer_monitor).toHaveProperty("syndrome_weight");
    expect(body.defense_systems.stabilizer_monitor).toHaveProperty("confidence");
    expect(body.defense_systems.stabilizer_monitor).not.toHaveProperty("syndrome");
    expect(body.defense_systems.preallocated_ancilla_trap_pool.logical_agents).toBe(1);
  });

  it("end-to-end: POST /api/security/swarm/respond activates the integrity response", async () => {
    const started = await startSecurityRoutesServer();
    server = started.server;

    const response = await fetch(`${started.baseUrl}/api/security/swarm/respond?observer_pressure=1`, { method: "POST" });
    const body = await response.json();

    expect(response.status).toBe(202);
    expect(body.status).toBe("integrity_response_active");
    expect(body.activated_ancillas + body.activated_traps).toBeGreaterThan(0);
    expect(body.syndrome_rotation_index).toBeGreaterThanOrEqual(0);
    expect(body.syndrome_rotation_index).toBeLessThan(24);
  });
});
