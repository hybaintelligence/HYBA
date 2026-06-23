import fs from "node:fs";
import path from "node:path";
import { describe, expect, it } from "vitest";

const root = process.cwd();
const readText = (relativePath: string) => fs.readFileSync(path.join(root, relativePath), "utf8");

describe("client-grade frontend production readiness", () => {
  const app = readText("src/App.tsx");
  const apiClient = readText("src/apiClient.ts");
  const readinessCheck = readText("scripts/check_frontend_readiness.mjs");
  const packageJson = JSON.parse(readText("package.json")) as { scripts: Record<string, string> };

  it("keeps the complete board-level operating surface mounted in the application shell", () => {
    for (const surface of [
      "ExecutiveSummary",
      "SovereignCommandPost",
      "SovereignGenesisPanel",
      "AdminPanel",
      "HybaAdminDashboard",
      "MiningJobsSection",
      "HistoricalDataSection",
      "AnalyticsSection",
      "CustomerPortal",
      "CIaaSServiceManager",
      "QaaSComputerManager",
      "PoolSecretsConfig",
      "NetworkToast",
      "AIAssistant",
    ]) {
      expect(app, surface).toContain(surface);
    }

    for (const view of ["dashboard", "admin", "executive", "jobs", "history", "analytics", "portal", "ciaas", "qaas"]) {
      expect(app, view).toContain(`"${view}"`);
    }
  });

  it("preserves resilient, honest degraded states instead of fabricating executive telemetry", () => {
    for (const signal of [
      "ErrorState",
      "EmptyState",
      "Skeleton",
      "NetworkToast",
      "Retry connection",
      "Telemetry interruption",
      "No pool telemetry available from backend.",
      "No catalog records available from backend.",
      "REAL TELEMETRY ONLY — NO FABRICATED DATA",
    ]) {
      expect(app, signal).toContain(signal);
    }
  });

  it("tracks the high-risk backend command families the frontend must survive", () => {
    for (const command of [
      "deleteAdminUser",
      "disburseFunding",
      "reviewFundingRequest",
      "startMiningProduction",
      "stopMiningProduction",
      "submitMiningProductionShare",
      "securityShield",
      "quarantineLane",
      "migrateToHabitat",
      "scaleIntelligence",
      "boostConsciousness",
      "intelligenceOrchestrate",
      "applyEvolution",
      "setMiningIntent",
    ]) {
      expect(apiClient, command).toContain(command);
    }
  });

  it("keeps production readiness enforceable through one command, not tribal memory", () => {
    expect(packageJson.scripts["test:frontend:gate"]).toContain("test:frontend:all");
    expect(packageJson.scripts["test:frontend:gate"]).toContain("build");
    expect(packageJson.scripts["prod:check"]).toBeTruthy();

    for (const requiredArtifact of [
      "tests/e2e/accessibility.spec.ts",
      "tests/e2e/role-matrix.spec.ts",
      "tests/e2e/command-safety.spec.ts",
      "tests/e2e-live/live-stack.spec.ts",
      "tests/test_frontend_release_readiness.test.ts",
      "tests/test_frontend_production_hardening.test.ts",
      "docs/frontend/PRODUCTION_HARDENING_EVIDENCE.md",
    ]) {
      expect(readinessCheck, requiredArtifact).toContain(requiredArtifact);
    }
  });
});
