import { test, expect } from "@playwright/test";

// Simple end-to-end smoke test for the HYBA front-end UI.
// This test verifies that the main page loads and displays a recognizable heading.
// Adjust selectors and assertions as the UI evolves.

test.describe("HYBA UI End-to-End", () => {
  test("Home page loads and displays the console header", async ({ page }) => {
    // Navigate to the base URL defined in playwright.config.ts
    await page.goto("/");

    // Assert that a key piece of text appears on the page. The "Genesis Runtime Console" header
    // is part of the main dashboard and indicates that the React app rendered successfully.
    await expect(page.locator("text=Genesis Runtime Console")).toBeVisible();
  });
});
