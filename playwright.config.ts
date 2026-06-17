import { defineConfig } from '@playwright/test';

export default defineConfig({
  // Directory containing end-to-end UI tests
  testDir: 'tests/e2e',
  // Maximum time one test can run for. Adjust as necessary for slower environments.
  timeout: 60000,
  use: {
    // Base URL for your running front-end application. Override with PLAYWRIGHT_BASE_URL env var.
    baseURL: process.env.PLAYWRIGHT_BASE_URL || 'http://localhost:3000',
    headless: true,
  },
});
