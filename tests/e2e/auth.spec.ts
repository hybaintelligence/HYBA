import { expect, test } from "@playwright/test";

test.beforeEach(async ({ page }) => {
  await page.route("**/api/health", (route) => route.fulfill({ json: { status: "ok", timestamp: new Date().toISOString(), version: "2.0.1", systemMetrics: {} } }));
  await page.route("**/api/ai/consciousness", (route) => route.fulfill({ json: { status: "nominal", source: "mock" } }));
  await page.route("**/api/mining/pools", (route) => route.fulfill({ json: { summary: {}, pools: [] } }));
  await page.route("**/api/security/status", (route) => route.fulfill({ json: { status: "nominal", defense_systems: {} } }));
  await page.route("**/api/products", (route) => route.fulfill({ json: [] }));
  await page.route("**/api/auth/profile", (route) => route.fulfill({ json: { success: false } }));
  await page.route("**/api/auth/register", (route) => route.fulfill({ json: { success: true } }));
  await page.route("**/api/auth/login", (route) => route.fulfill({ json: { success: true, token: "mock-token", user: { username: "operator", role: "miner" } } }));
});

test("operator can register, log in, and log out through accessible form controls", async ({ page }) => {
  await page.goto("/");
  await page.getByRole("button", { name: /sign up/i }).click();
  await page.getByLabel(/operator handle/i).fill("operator");
  await page.getByLabel(/password/i).fill("secret123");
  await page.getByRole("button", { name: /^register$/i }).click();
  await expect(page.getByText(/registered successfully/i)).toBeVisible();

  await page.getByLabel(/operator handle/i).fill("operator");
  await page.getByLabel(/password/i).fill("secret123");
  await page.getByRole("button", { name: /log in/i }).click();
  await expect(page.getByText(/welcome back, operator/i)).toBeVisible();
  await page.getByRole("button", { name: /log out/i }).click();
  await expect(page.getByText(/session ended securely/i)).toBeVisible();
});
