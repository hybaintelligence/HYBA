import { expect, test } from "@playwright/test";
import { installBackendMocks, seedAuth } from "./fixtures";

const operationalRoles = ["operator", "analyst", "miner"] as const;
const invalidSessionRoles = ["anonymous", "expired_token", "malformed_token", "backend_profile_unavailable"] as const;
const executiveRoles = ["ceo_heir_apparent", "chairman", "cto", "cfo", "legal", "chief_of_staff"] as const;

test.describe("frontend role matrix", () => {
  for (const role of [...operationalRoles, ...invalidSessionRoles]) {
    test(`${role} receives operator surface only`, async ({ page }) => {
      await seedAuth(page, role as any);
      await installBackendMocks(page, { role: role as any });
      await page.goto("/");
      await expect(page.getByRole("heading", { name: "Genesis Runtime Console" })).toBeVisible();
      await expect(page.getByRole("button", { name: "Admin" })).toHaveCount(0);
      await expect(page.getByRole("button", { name: "Executive" })).toHaveCount(0);
      await expect(page.getByRole("button", { name: "Refresh" })).toBeVisible();
    });
  }

  test("admin receives admin surface", async ({ page }) => {
    await seedAuth(page, "admin");
    await installBackendMocks(page, { role: "admin" });
    await page.goto("/");
    await expect(page.getByRole("button", { name: "Admin" })).toBeVisible();
    await expect(page.getByRole("button", { name: "Executive" })).toHaveCount(0);
  });

  for (const role of executiveRoles) {
    test(`${role} receives executive surface`, async ({ page }) => {
      await seedAuth(page, role as any);
      await installBackendMocks(page, { role: role as any });
      await page.goto("/");
      await expect(page.getByRole("button", { name: "Admin" })).toBeVisible();
      await expect(page.getByRole("button", { name: "Executive" })).toBeVisible();
      await page.getByRole("button", { name: "Executive" }).click();
      await expect(page.getByRole("heading", { name: "HYBA Group Executive Console" })).toBeVisible();
    });
  }
});
