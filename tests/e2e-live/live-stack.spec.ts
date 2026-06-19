import { expect, test } from "@playwright/test";

test.describe("live stack smoke", () => {
  test("configured live frontend responds without silent skips", async ({ page, baseURL }) => {
    expect(
      process.env.LIVE_E2E_SANDBOX,
      "LIVE_E2E_SANDBOX=true is required so live checks are explicit and sandbox-only",
    ).toBe("true");
    expect(baseURL, "PLAYWRIGHT_BASE_URL must point at the live or sandbox frontend").toBeTruthy();
    const response = await page.goto("/", { waitUntil: "domcontentloaded" });
    expect(response?.ok(), `Expected ${baseURL} to return a successful document response`).toBe(true);
    await expect(page.getByRole("heading", { name: "Genesis Runtime Console" })).toBeVisible();
  });
});
