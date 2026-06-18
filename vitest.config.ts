import { defineConfig } from "vitest/config";

export default defineConfig({
  test: {
    include: ["tests/**/*.test.ts", "tests/**/*.test.tsx"],
    exclude: ["node_modules", "dist"],
    globals: true,
    environment: "node",
    testTimeout: 30000,
    hookTimeout: 30000,
    server: {
      deps: {
        inline: ["pino"],
      },
    },
  },
});