import type { Page, Route } from "@playwright/test";

export type MockRole =
  | "anonymous"
  | "operator"
  | "analyst"
  | "miner"
  | "admin"
  | "ceo_heir_apparent"
  | "chairman"
  | "cto"
  | "cfo"
  | "legal"
  | "chief_of_staff"
  | "expired_token"
  | "malformed_token"
  | "backend_profile_unavailable";

type MockOptions = {
  role?: MockRole;
  offline?: boolean;
};

const now = "2026-06-19T09:00:00.000Z";
const EXECUTIVE_ROLES: MockRole[] = [
  "ceo_heir_apparent",
  "chairman",
  "cto",
  "cfo",
  "legal",
  "chief_of_staff",
];

export const disposableUsers = [
  {
    id: 10,
    username: "agent4-admin",
    email: "agent4-admin@example.test",
    role: "admin",
    is_active: true,
    created_at: now,
    updated_at: now,
    last_login: null,
    created_by: "fixture",
  },
  {
    id: 11,
    username: "agent4-disposable",
    email: "agent4-disposable@example.test",
    role: "operator",
    is_active: true,
    created_at: now,
    updated_at: now,
    last_login: null,
    created_by: "fixture",
  },
];

const telemetry = {
  health: {
    status: "healthy",
    timestamp: now,
    version: "2.0.1-test",
    telemetry_source: "playwright-mock",
    quantumCoherence: 0.91,
    phiResonance: 0.88,
    quantumSpeedupFactor: 1.2,
    actualSpeedupFactor: 1.0,
    systemMetrics: {
      blockHeight: 850000,
      currentHashrate: 0.42,
      powerConsumption: 1200,
      activePool: "Mock Pool Alpha",
      difficultyTarget: "0000000000000000000ffff",
      networkDifficulty: 83_000_000_000_000,
      power_scale: 1,
      phi_tier: 12,
      system_health: "nominal",
    },
  },
  consciousness: { status: "nominal", source: "playwright-mock", integrated_information: 0.64 },
  pools: {
    pools: [
      {
        pool_id: "mock-alpha",
        name: "Mock Pool Alpha",
        url: "stratum+tcp://alpha.example.test:3333",
        credential_mode: "username_password",
        required_fields: ["username", "password"],
        configured: true,
        enabled: true,
        status: "connected",
        is_active: true,
        performance: { latency_ms: 12, shares_submitted: 3, shares_accepted: 3 },
      },
      {
        pool_id: "mock-beta",
        name: "Mock Pool Beta",
        url: "stratum+tcp://beta.example.test:3333",
        credential_mode: "btc_address",
        required_fields: ["btc_address"],
        configured: true,
        enabled: true,
        status: "available",
        is_active: false,
        performance: { latency_ms: 18, shares_submitted: 0, shares_accepted: 0 },
      },
    ],
    summary: {
      total_pools: 2,
      configured_pools: 2,
      active_pools: 1,
      telemetry_source: "playwright-mock",
    },
  },
  security: {
    status: "nominal",
    threat_level: "low",
    defense_systems: {
      stabilizer_monitor: {
        operating_mode: "observe",
        confidence: 0.99,
        check_frequency: 0.5,
        syndrome_weight: 1,
        sanitized: true,
      },
      preallocated_ancilla_trap_pool: {
        active_ancillas: 2,
        max_ancilla_pool: 8,
        active_traps: 1,
        retired_traps: 0,
      },
    },
  },
};

const userRoleFor = (role: MockRole) => {
  if (["expired_token", "malformed_token", "backend_profile_unavailable", "anonymous"].includes(role)) {
    return "operator";
  }
  return role;
};

const profileByRole = (role: MockRole) => ({
  success: true,
  user: {
    id: `fixture-${role}`,
    username: role === "anonymous" ? "guest" : `fixture-${role}`,
    role: userRoleFor(role),
    createdAt: now,
  },
});

async function json(route: Route, body: unknown, status = 200) {
  await route.fulfill({ status, contentType: "application/json", body: JSON.stringify(body) });
}

export async function installBackendMocks(page: Page, options: MockOptions = {}) {
  const role = options.role ?? "operator";
  await page.route("**/api/**", async (route) => {
    const request = route.request();
    const url = new URL(request.url());
    const path = url.pathname.replace(/^\/api/, "");

    if (options.offline) {
      await route.abort("failed");
      return;
    }

    if (path === "/health") return json(route, telemetry.health);
    if (path === "/consciousness/telemetry") return json(route, telemetry.consciousness);
    if (path === "/mining/pools") return json(route, telemetry.pools);
    if (path === "/security/status") return json(route, telemetry.security);
    if (path === "/products") return json(route, []);
    if (path === "/auth/profile") {
      if (role === "anonymous") return json(route, { success: false }, 401);
      if (role === "expired_token") return json(route, { success: false, error: "token expired" }, 401);
      if (role === "malformed_token") return json(route, { success: false, error: "malformed token" }, 401);
      if (role === "backend_profile_unavailable")
        return json(route, { success: false, error: "profile unavailable" }, 503);
      return json(route, profileByRole(role));
    }
    if (path === "/auth/login")
      return json(route, { success: true, token: "mock-token", user: profileByRole(role).user });
    if (path === "/auth/register")
      return json(route, { success: true, token: "mock-token", user: profileByRole(role).user });
    if (path === "/mining/power")
      return json(route, {
        status: "ok",
        effective_hashrate_ehs: 0.42,
        phi_tier: 12,
        hashrate_cap_ehs: 1,
      });
    if (path === "/mining/switch")
      return json(route, { status: "switched", current_pool: "mock-beta" });
    if (path === "/mining/disconnect")
      return json(route, { status: "disconnected", previous_pool: "mock-alpha" });
    if (path === "/mining/pool-config")
      return json(route, { status: "configured", pool: telemetry.pools.pools[0] });

    if (path === "/admin/stats")
      return json(route, {
        total_users: 2,
        active_users: 2,
        admin_users: role === "admin" ? 1 : 0,
        executive_users: EXECUTIVE_ROLES.includes(role) ? 1 : 0,
      });
    if (path === "/admin/audit-logs") return json(route, { logs: [], total: 0 });
    if (path === "/admin/funding/overview")
      return json(route, { total_funds: 0, pending_requests: 0, approved_allocations: 0 });
    if (/^\/admin\/funding\/allocations\/[^/]+\/disburse$/.test(path) && request.method() === "POST")
      return json(route, { status: "disbursed", allocation_id: path.split("/").at(-2) });
    if (/^\/admin\/funding\/requests\/[^/]+\/review$/.test(path) && request.method() === "PUT")
      return json(route, { status: "reviewed", request_id: path.split("/").at(-2) });
    if (path === "/admin/users" && request.method() === "GET")
      return json(route, { users: disposableUsers, total: disposableUsers.length });
    if (path === "/admin/users" && request.method() === "POST")
      return json(route, { ...disposableUsers[1], id: 99, username: "agent4-created" }, 201);
    if (path === "/admin/users/11" && request.method() === "PUT")
      return json(route, { ...disposableUsers[1], role: "analyst" });
    if (path === "/admin/users/11" && request.method() === "DELETE")
      return json(route, { status: "deleted" });

    if (path === "/intelligence/status")
      return json(route, { status: "ready", active: true, scale: 1 });
    if (path === "/intelligence/telemetry")
      return json(route, { timestamp: now, phi_resonance: 0.88, consciousness_level: 0.64 });
    if (path === "/intelligence/start") return json(route, { status: "started" });
    if (path === "/intelligence/stop") return json(route, { status: "stopped" });
    if (path === "/intelligence/reset") return json(route, { status: "reset" });
    if (path === "/v1/intelligence/scale" && request.method() === "POST")
      return json(route, { status: "scaled", scale: 2 });
    if (path === "/v1/intelligence/consciousness/boost" && request.method() === "POST")
      return json(route, { status: "boosted" });
    if (path === "/v1/intelligence/orchestrate" && request.method() === "POST")
      return json(route, { status: "orchestrated" });
    if (path === "/security/shield" && request.method() === "POST")
      return json(route, { status: "shield_activated" });
    if (/^\/organism\/immune\/quarantine\/[^/]+$/.test(path) && request.method() === "POST")
      return json(route, { status: "quarantined", lane_id: path.split("/").at(-1) });
    if (/^\/organism\/cognition\/evolve\/[^/]+$/.test(path) && request.method() === "POST")
      return json(route, { status: "evolution_applied", conjecture_id: path.split("/").at(-1) });
    if (path === "/organism/executive/status")
      return json(route, { status: "ready", intent: "stasis" });
    if (path === "/organism/executive/telemetry")
      return json(route, { status: "ready", lanes: [] });
    if (path === "/organism/executive/habitats")
      return json(route, { habitats: telemetry.pools.pools, default_pool: "mock-alpha" });
    if (path === "/organism/executive/intent")
      return json(route, { status: "accepted", intent: "stasis" });
    if (/^\/organism\/executive\/habitats\/migrate\/[^/]+$/.test(path) && request.method() === "PUT")
      return json(route, { status: "migration_scheduled", pool: path.split("/").at(-1) });

    return json(route, { detail: `Unhandled mock route: ${request.method()} ${path}` }, 404);
  });
}

export async function seedAuth(page: Page, role: MockRole) {
  if (role !== "anonymous") {
    const token =
      role === "expired_token" ? "expired-token" : role === "malformed_token" ? "malformed-token" : "mock-token";
    await page.addInitScript((authToken) => window.localStorage.setItem("hyba_auth_token", authToken), token);
  }
}

export async function installRecoverableBackendMocks(page: Page, role: MockRole = "operator") {
  const state = { offline: true };
  await installBackendMocks(page, {
    role,
    get offline() {
      return state.offline;
    },
  });
  return {
    recover() {
      state.offline = false;
    },
    fail() {
      state.offline = true;
    },
  };
}
