import { expect, test } from "@playwright/test";
import { installBackendMocks, seedAuth } from "./fixtures";

test.describe("admin E2E hardening", () => {
  test("admin can create, edit, and delete only disposable users through mocked endpoints", async ({
    page,
  }) => {
    await seedAuth(page, "admin");
    await installBackendMocks(page, { role: "admin" });

    const mutations: string[] = [];
    page.on("request", (request) => {
      if (["POST", "PUT", "DELETE"].includes(request.method()))
        mutations.push(`${request.method()} ${new URL(request.url()).pathname}`);
    });
    page.on("dialog", (dialog) => dialog.accept());

    await page.goto("/");
    await expect(page.getByRole("heading", { name: "Genesis Runtime Console" })).toBeVisible();
    await page.getByRole("button", { name: "Admin" }).click();
    await expect(page.getByRole("heading", { name: "User Management" })).toBeVisible();
    await expect(page.getByText("agent4-disposable")).toBeVisible();

    await page.getByRole("button", { name: /Create User/i }).click();
    await page.getByLabel("Username").fill("agent4-created");
    await page.getByLabel(/Email/).fill("agent4-created@example.test");
    await page.getByLabel("Password").fill("CorrectHorse42!");
    await page.getByLabel("Role").selectOption("operator");
    await page.getByRole("button", { name: /^Create User$/ }).click();
    await expect(page.getByText("User created successfully")).toBeVisible();

    await page.getByTitle("Edit user").last().click();
    await page.getByLabel("Role").selectOption("analyst");
    await page.getByRole("button", { name: /^Update User$/ }).click();
    await expect(page.getByText("User updated successfully")).toBeVisible();

    await page.getByTitle("Delete user").last().click();
    await expect(page.getByText("User deleted successfully")).toBeVisible();

    expect(mutations).toContain("POST /api/admin/users");
    expect(mutations).toContain("PUT /api/admin/users/11");
    expect(mutations).toContain("DELETE /api/admin/users/11");
    expect(mutations.every((entry) => entry.includes("/api/admin/users"))).toBe(true);
  });

  test("non-admin cannot access admin panel", async ({ page }) => {
    await seedAuth(page, "operator");
    await installBackendMocks(page, { role: "operator" });
    await page.goto("/");
    await expect(page.getByRole("button", { name: "Admin" })).toHaveCount(0);
  });
});
