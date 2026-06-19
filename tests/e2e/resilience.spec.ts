import { expect, test } from "@playwright/test";

test("offline backend handling shows interruption, retry, and dismissible network state", async ({
  page,
}) => {
  let telemetryCalls = 0;
  await page.route("**/api/health", (route) => {
    telemetryCalls += 1;
    if (telemetryCalls === 1) return route.abort("failed");
    return route.fulfill({
      json: {
        status: "ok",
        timestamp: new Date().toISOString(),
        version: "2.0.1",
        systemMetrics: {},
      },
    });
  });
  await page.route("**/api/ai/consciousness", (route) =>
    route.fulfill({ json: { status: "nominal", source: "mock" } }),
  );
  await page.route("**/api/mining/pools", (route) =>
    route.fulfill({ json: { summary: {}, pools: [] } }),
  );
  await page.route("**/api/security/status", (route) =>
    route.fulfill({ json: { status: "nominal", defense_systems: {} } }),
  );
  await page.route("**/api/products", (route) => route.fulfill({ json: [] }));
  await page.route("**/api/auth/profile", (route) => route.fulfill({ json: { success: false } }));

  await page.goto("/");
  await expect(page.getByText("Telemetry interruption")).toBeVisible();
  await expect(page.getByText(/Connection Lost to HYBA Unified Backend/i)).toBeVisible();
  await page.getByRole("button", { name: /dismiss network status/i }).click();
  await expect(page.getByText(/Connection Lost to HYBA Unified Backend/i)).toBeHidden();
  await page.getByRole("button", { name: /retry connection/i }).click();
  await expect(page.getByText("Enterprise-Grade Mining Operations")).toBeVisible();
});
