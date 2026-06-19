import { expect, test } from "@playwright/test";
import { EXECUTIVE_ROLES, installBackendMocks, OPERATIONAL_ROLES, seedAuth, type MockRole } from "./fixtures";

const invalidSessionRoles: MockRole[] = ["anonymous", "expired_token", "malformed_token", "backend_profile_unavailable"];

async function openShell(page: Parameters<Parameters<typeof test>[1]>[0]["page"], role: MockRole) {
  await seedAuth(page, role);
  await installBackendMocks(page, { role });
  await page.goto("/");
  await expect(page.getByRole("heading", { name: "Genesis Runtime Console" })).toBeVisible();
}

test.describe("frontend role matrix production gate", () => {
  for (const role of [...OPERATIONAL_ROLES, ...invalidSessionRoles]) {
    test(`${role} cannot see admin or executive command navigation`, async ({ page }) => {
      await openShell(page, role);
      await expect(page.getByRole("button", { name: "Admin" })).toHaveCount(0);
      await expect(page.getByRole("button", { name: "Executive" })).toHaveCount(0);
      await expect(page.getByRole("button", { name: "Refresh" })).toBeVisible();
    });
  }

  test("admin can see admin navigation but not executive-only navigation", async ({ page }) => {
    await openShell(page, "admin");
    await expect(page.getByRole("button", { name: "Admin" })).toBeVisible();
    await expect(page.getByRole("button", { name: "Executive" })).toHaveCount(0);
  });

  for (const role of EXECUTIVE_ROLES) {
    test(`${role} can see executive and governance navigation`, async ({ page }) => {
      await openShell(page, role);
      await expect(page.getByRole("button", { name: "Admin" })).toBeVisible();
      await expect(page.getByRole("button", { name: "Executive" })).toBeVisible();
      await page.getByRole("button", { name: "Executive" }).click();
      await expect(page.getByRole("heading", { name: "HYBA Group Executive Console" })).toBeVisible();
    });
  }
});
