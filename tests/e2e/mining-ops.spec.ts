import { expect, test } from "@playwright/test";
import { installBackendMocks, installRecoverableBackendMocks, seedAuth } from "./fixtures";

test.describe("mining operations E2E hardening", () => {
  test("power cap control and pool switch are mocked and not duplicated", async ({ page }) => {
    await seedAuth(page, "operator");
    await installBackendMocks(page, { role: "operator" });

    let switchCalls = 0;
    let powerCalls = 0;
    page.on("request", (request) => {
      const path = new URL(request.url()).pathname;
      if (request.method() === "POST" && path === "/api/mining/switch") switchCalls += 1;
      if (request.method() === "POST" && path === "/api/mining/power") powerCalls += 1;
    });

    await page.goto("/");
    await expect(page.getByText("Mock Pool Alpha").first()).toBeVisible();

    const power = page.getByLabel("Power scale control");
    await power.fill("10");
    await expect(page.getByText("EH/s cap")).toBeVisible();
    expect(powerCalls).toBeGreaterThan(0);

    const betaCard = page
      .locator("div", { hasText: "Mock Pool Beta" })
      .filter({ has: page.getByRole("button", { name: "Switch" }) })
      .first();
    await betaCard.getByRole("button", { name: "Switch" }).dblclick();
    await expect(page.getByText("Switched to Mock Pool Beta")).toBeVisible();
    expect(switchCalls).toBe(1);
  });

  test("backend offline shows interruption state and retry control", async ({ page }) => {
    await installBackendMocks(page, { role: "anonymous", offline: true });
    await page.goto("/");
    await expect(page.getByText("Telemetry interruption")).toBeVisible();
    await expect(page.getByRole("button", { name: /Retry connection/i })).toBeVisible();
    await expect(page.getByText("Connection Lost to HYBA Unified Backend")).toBeVisible();
  });

  test("retry restores connection after mocked backend recovery", async ({ page }) => {
    const backend = await installRecoverableBackendMocks(page, "operator");
    await page.goto("/");
    await expect(page.getByText("Telemetry interruption")).toBeVisible();

    backend.recover();
    await page.getByRole("button", { name: /Retry connection/i }).click();

    await expect(page.getByText("Telemetry interruption")).toHaveCount(0);
    await expect(page.getByText("Mock Pool Alpha").first()).toBeVisible();
  });

  test("operator can log in and toggle dark mode", async ({ page }) => {
    await installBackendMocks(page, { role: "operator" });
    await page.goto("/");

    await page.getByLabel("Operator Handle").fill("operator");
    await page.getByLabel("Password").fill("CorrectHorse42!");
    await page.getByRole("button", { name: "Log in" }).click();
    await expect(page.getByText("Welcome back, fixture-operator.")).toBeVisible();

    await page.getByRole("button", { name: "Toggle color theme" }).click();
    await expect(page.locator("html")).toHaveClass(/dark/);
  });

  test("pool config validates required fields, saves once, and disconnects active pool once", async ({
    page,
  }) => {
    await seedAuth(page, "operator");
    await installBackendMocks(page, { role: "operator" });
    let configCalls = 0;
    let switchCalls = 0;
    let disconnectCalls = 0;
    page.on("request", (request) => {
      const path = new URL(request.url()).pathname;
      if (request.method() === "POST" && path === "/api/mining/pool-config") configCalls += 1;
      if (request.method() === "POST" && path === "/api/mining/switch") switchCalls += 1;
      if (request.method() === "POST" && path === "/api/mining/disconnect") disconnectCalls += 1;
    });

    await page.goto("/");
    const betaCard = page
      .locator("div", { hasText: "Mock Pool Beta" })
      .filter({ has: page.getByRole("button", { name: "Configure" }) })
      .first();
    await betaCard.getByRole("button", { name: "Configure" }).click();
    await page.getByRole("button", { name: /SAVE POOL CONFIG/i }).click();
    expect(configCalls).toBe(0);

    await page.getByLabel("BTC Address").fill("bc1qagent4sandbox000000000000000000000000000");
    await page.getByRole("button", { name: /SAVE POOL CONFIG/i }).click();
    await expect(page.getByText("CONFIGURED")).toBeVisible();
    expect(configCalls).toBe(1);
    expect(switchCalls).toBe(1);

    await page.getByRole("button", { name: "Close pool configuration" }).click();
    const alphaCard = page
      .locator("div", { hasText: "Mock Pool Alpha" })
      .filter({ has: page.getByRole("button", { name: "Disconnect" }) })
      .first();
    await alphaCard.getByRole("button", { name: "Disconnect" }).dblclick();
    await expect(page.getByText("Disconnected from pool")).toBeVisible();
    expect(disconnectCalls).toBe(1);
  });
});
