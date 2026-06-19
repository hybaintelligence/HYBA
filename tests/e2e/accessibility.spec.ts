import AxeBuilder from "@axe-core/playwright";
import { expect, test } from "@playwright/test";
import { installBackendMocks, seedAuth, type MockRole } from "./fixtures";

const ACCESSIBILITY_ROLES: MockRole[] = [
  "anonymous",
  "operator",
  "admin",
  "ceo_heir_apparent",
  "chairman",
  "cto",
  "cfo",
  "legal",
  "chief_of_staff",
];

test.describe("accessibility production hardening", () => {
  for (const role of ACCESSIBILITY_ROLES) {
    test(`${role} surface has landmarks, named controls, and no high-impact axe findings`, async ({
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

      const results = await new AxeBuilder({ page }).analyze();
      const highImpactFindings = results.violations.filter((violation) =>
        ["serious", "critical"].includes(violation.impact || ""),
      );
      expect(highImpactFindings).toEqual([]);
    });
  }
});
