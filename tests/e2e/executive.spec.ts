import { expect, test } from "@playwright/test";
import { installBackendMocks, seedAuth } from "./fixtures";

test.describe("executive E2E hardening", () => {
  test("executive role can open executive console and run mocked autonomy-adjacent pool operation", async ({ page }) => {
    await seedAuth(page, "ceo_heir_apparent");
    await installBackendMocks(page, { role: "ceo_heir_apparent" });
    let switchCalls = 0;
    page.on("request", (request) => {
      if (request.method() === "POST" && new URL(request.url()).pathname === "/api/mining/switch") switchCalls += 1;
    });

    await page.goto("/");
    await page.getByRole("button", { name: "Executive" }).click();
    await expect(page.getByRole("heading", { name: "HYBA Group Executive Console" })).toBeVisible();
    await expect(page.getByText("Executive Access")).toBeVisible();

    await page.getByRole("button", { name: "Quantum" }).click();
    await page.getByLabel("Select Pool").selectOption("mock-beta");
    await page.getByRole("button", { name: /Switch Pool/i }).click();
    await expect(page.getByText(/Pool switched successfully|switched/i)).toBeVisible();
    expect(switchCalls).toBe(1);
  });

  test("operator role has no executive command surface", async ({ page }) => {
    await seedAuth(page, "operator");
    await installBackendMocks(page, { role: "operator" });
    await page.goto("/");
    await expect(page.getByRole("button", { name: "Executive" })).toHaveCount(0);
  });
});
