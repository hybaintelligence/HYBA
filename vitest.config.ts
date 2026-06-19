import react from "@vitejs/plugin-react";
import { defineConfig } from "vitest/config";

export default defineConfig({
  plugins: [react({ babel: { configFile: false } })],
  test: {
    env: {
      NODE_ENV: "test",
    },
    include: ["tests/**/*.test.ts", "tests/**/*.test.tsx"],
    exclude: ["node_modules", "dist"],
    globals: true,
    environment: "node",
    testTimeout: 30000,
    hookTimeout: 30000,
    coverage: {
      provider: "v8",
      reporter: ["text", "json", "html"],
      thresholds: {
        // Baseline mirrors docs/FRONTEND_TEST_COVERAGE_PLAN.md so CI can ratchet upward
        // instead of falsely asserting production-grade 70%+ coverage before Agents 2-4 land.
        statements: 25,
        branches: 40,
        functions: 17,
        lines: 27,
      },
      exclude: [
        "dist/**",
        "node_modules/**",
        "tests/**",
        "vite.config*.ts",
        "vitest*.config.ts",
        "playwright.config.ts",
      ],
    },
    server: {
      deps: {
        inline: ["pino"],
      },
    },
  },
});
