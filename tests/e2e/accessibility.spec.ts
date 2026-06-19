import { expect, test } from "@playwright/test";
import { installBackendMocks, seedAuth } from "./fixtures";

test.describe("accessibility smoke", () => {
  for (const role of ["anonymous", "admin", "ceo_heir_apparent"] as const) {
    test(`${role} surface exposes named landmarks and controls without image-only buttons`, async ({
      page,
    }) => {
      await seedAuth(page, role);
      await installBackendMocks(page, { role });
      await page.goto("/");

      await expect(page.getByRole("banner")).toBeVisible();
      await expect(page.getByRole("main")).toBeVisible();
      await expect(page.getByRole("heading", { name: "Genesis Runtime Console" })).toBeVisible();
      await expect(page.getByRole("button", { name: "Toggle color theme" })).toBeVisible();

      const unnamedButtons = await page.locator("button").evaluateAll((buttons) =>
        buttons
          .map((button, index) => ({
            index,
            text: button.textContent?.trim() || "",
            label: button.getAttribute("aria-label") || button.getAttribute("title") || "",
          }))
          .filter((button) => !button.text && !button.label),
      );
      expect(unnamedButtons).toEqual([]);
    });
  }
});
