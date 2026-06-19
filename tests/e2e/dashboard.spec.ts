import { expect, test } from "@playwright/test";

const telemetry = {
  latency: 35,
  health: {
    status: "ok",
    version: "2.0.1",
    telemetry_source: "playwright-mock",
    quantumCoherence: 0.91,
    phiResonance: 0.86,
    quantumSpeedupFactor: 1.2,
    actualSpeedupFactor: 1.1,
    systemMetrics: {
      activePool: "ViaBTC",
      blockHeight: 850000,
      currentHashrate: 0.5,
      powerConsumption: 10,
      networkDifficulty: 88,
      difficultyTarget: "target",
      system_health: "healthy",
      power_scale: 1,
      phi_tier: 12,
    },
  },
  pools: {
    summary: { total_pools: 2, configured_pools: 2, active_pools: 1 },
    pools: [
      {
        pool_id: "viabtc",
        name: "ViaBTC",
        url: "stratum+tcp://via",
        configured: true,
        is_active: true,
        status: "connected",
        credential_mode: "username_password",
        required_fields: ["username", "password"],
        performance: { latency_ms: 20, shares_submitted: 3 },
      },
      {
        pool_id: "braiins",
        name: "Braiins",
        url: "stratum+tcp://braiins",
        configured: true,
        is_active: false,
        status: "configured",
        credential_mode: "username_password",
        required_fields: ["username", "password"],
        performance: { latency_ms: 25, shares_submitted: 1 },
      },
    ],
  },
  security: { status: "nominal", threat_level: "low", defense_systems: {} },
  consciousness: { status: "nominal", integrated_information: 0.5 },
};

test.beforeEach(async ({ page }) => {
  await page.route("**/api/health", (route) => route.fulfill({ json: telemetry.health }));
  await page.route("**/api/ai/consciousness", (route) =>
    route.fulfill({ json: telemetry.consciousness }),
  );
  await page.route("**/api/mining/pools", (route) => route.fulfill({ json: telemetry.pools }));
  await page.route("**/api/security/status", (route) =>
    route.fulfill({ json: telemetry.security }),
  );
  await page.route("**/api/products", (route) =>
    route.fulfill({ json: [{ id: "p1", name: "HYBA Console", description: "Control plane" }] }),
  );
  await page.route("**/api/auth/profile", (route) => route.fulfill({ json: { success: false } }));
  await page.route("**/api/mining/power", (route) => route.fulfill({ json: { status: "ok" } }));
  await page.route("**/api/mining/switch", (route) => route.fulfill({ json: { status: "ok" } }));
  await page.route("**/api/mining/disconnect", (route) =>
    route.fulfill({ json: { status: "ok" } }),
  );
});

test("dashboard actions expose accessible controls and send mocked operator commands", async ({
  page,
}) => {
  await page.goto("/");
  await expect(page.getByText("Genesis Runtime Console")).toBeVisible();
  await expect(page.getByText("Enterprise-Grade Mining Operations")).toBeVisible();

  await page.getByRole("button", { name: /refresh/i }).click();
  await page.getByRole("button", { name: /live/i }).click();
  await expect(page.getByRole("button", { name: /paused/i })).toBeVisible();
  await page.getByRole("button", { name: /toggle color theme/i }).click();

  await page.getByRole("button", { name: /jobs/i }).click();
  await expect(page.getByText(/mining jobs/i)).toBeVisible();
  await page.getByRole("button", { name: /dashboard/i }).click();
  await page.getByRole("button", { name: /history/i }).click();
  await expect(page.getByText(/historical/i)).toBeVisible();
  await page.getByRole("button", { name: /dashboard/i }).click();
  await page.getByRole("button", { name: /analytics/i }).click();
  await expect(page.getByText(/analytics/i)).toBeVisible();
  await page.getByRole("button", { name: /dashboard/i }).click();

  const powerRequest = page.waitForRequest("**/api/mining/power");
  await page.getByLabel(/power scale control/i).fill("2");
  await powerRequest;
  await page.getByLabel(/phi tier control/i).selectOption("15");

  const switchRequest = page.waitForRequest("**/api/mining/switch");
  await page.getByRole("button", { name: /^switch$/i }).click();
  await switchRequest;
});
