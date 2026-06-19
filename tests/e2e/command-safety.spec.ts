import { expect, test } from "@playwright/test";
import { installBackendMocks, seedAuth } from "./fixtures";

const operationalRoles = ["operator", "analyst", "miner"] as const;

const GUARDED_PATH_PATTERNS = [
  /^\/api\/v1\/mining-production\/(start|stop|submit-share)$/,
  /^\/api\/admin\/funding\//,
  /^\/api\/v1\/intelligence\/(scale|consciousness\/boost|orchestrate)$/,
  /^\/api\/security\/shield$/,
  /^\/api\/organism\/immune\/quarantine\//,
  /^\/api\/organism\/cognition\/evolve\//,
  /^\/api\/organism\/executive\/intent$/,
  /^\/api\/organism\/executive\/habitats\/migrate\//,
];

function isGuardedPath(pathname: string) {
  return GUARDED_PATH_PATTERNS.some((pattern) => pattern.test(pathname));
}

test.describe("frontend command safety", () => {
  for (const role of operationalRoles) {
    test(`${role} dashboard actions do not dispatch guarded control calls`, async ({ page }) => {
      await seedAuth(page, role as any);
      await installBackendMocks(page, { role: role as any });
      const guardedCalls: string[] = [];
      page.on("request", (request) => {
        const pathname = new URL(request.url()).pathname;
        if (isGuardedPath(pathname)) guardedCalls.push(`${request.method()} ${pathname}`);
      });

      await page.goto("/");
      await expect(page.getByRole("heading", { name: "Genesis Runtime Console" })).toBeVisible();
      await page.getByRole("button", { name: "Refresh" }).click();
      await page.getByRole("button", { name: /Live|Paused/ }).click();
      await page.getByRole("button", { name: "Jobs" }).click();
      await page.getByRole("button", { name: "Dashboard" }).click();
      await page.getByRole("button", { name: "Analytics" }).click();
      await page.getByRole("button", { name: "Dashboard" }).click();

      expect(guardedCalls).toEqual([]);
    });
  }

  test("admin user-management mutation stays scoped to disposable user endpoint", async ({ page }) => {
    await seedAuth(page, "admin");
    await installBackendMocks(page, { role: "admin" });
    page.on("dialog", (dialog) => dialog.accept());
    const mutations: string[] = [];
    page.on("request", (request) => {
      if (["POST", "PUT", "DELETE"].includes(request.method())) {
        mutations.push(`${request.method()} ${new URL(request.url()).pathname}`);
      }
    });

    await page.goto("/");
    await page.getByRole("button", { name: "Admin" }).click();
    await expect(page.getByRole("heading", { name: "User Management" })).toBeVisible();
    await page.getByTitle("Delete user").last().click();
    await expect(page.getByText("User deleted successfully")).toBeVisible();

    expect(mutations).toEqual(["DELETE /api/admin/users/11"]);
    expect(mutations.some((entry) => isGuardedPath(entry.split(" ")[1]))).toBe(false);
  });

  test("executive console passive navigation stays read-only", async ({ page }) => {
    await seedAuth(page, "ceo_heir_apparent");
    await installBackendMocks(page, { role: "ceo_heir_apparent" });
    const guardedCalls: string[] = [];
    page.on("request", (request) => {
      const pathname = new URL(request.url()).pathname;
      if (isGuardedPath(pathname)) guardedCalls.push(`${request.method()} ${pathname}`);
    });

    await page.goto("/");
    await page.getByRole("button", { name: "Executive" }).click();
    await expect(page.getByRole("heading", { name: "HYBA Group Executive Console" })).toBeVisible();
    await page.getByRole("button", { name: "Quantum" }).click();
    await page.getByRole("button", { name: "Dashboard" }).click();

    expect(guardedCalls).toEqual([]);
  });
});
