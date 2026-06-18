import react from "@vitejs/plugin-react";
import { defineConfig } from "vitest/config";

export default defineConfig({
  plugins: [react({ babel: { configFile: false } })],
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
