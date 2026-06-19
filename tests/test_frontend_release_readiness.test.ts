import { describe, expect, it } from "vitest";
import packageJson from "../package.json";
import generatedManifest from "../artifacts/frontend_api_command_manifest.generated.json";
import coverageStatus from "../artifacts/frontend_api_command_coverage_status.json";

type ManifestEntry = {
  function: string;
  method: string;
  sideEffect: string;
  idempotent: boolean;
};

type CoverageEntry = ManifestEntry & {
  coverageStatus: "covered" | "partial" | "required" | "blocked";
  evidence: string[];
};

describe("frontend release readiness", () => {
  const manifest = generatedManifest as ManifestEntry[];
  const statuses = coverageStatus as CoverageEntry[];
  const scripts = (packageJson as { scripts: Record<string, string>; devDependencies: Record<string, string> }).scripts;
  const devDependencies = (packageJson as { devDependencies: Record<string, string> }).devDependencies;
  const statusNames = new Set(statuses.map((entry) => entry.function));

  it("keeps release scripts and dependencies available", () => {
    for (const scriptName of [
      "lint",
      "test:frontend:unit",
      "test:frontend:components",
      "test:frontend:coverage",
      "test:frontend:e2e",
      "test:frontend:gate",
      "build",
      "prod:check",
    ]) {
      expect(scripts[scriptName], scriptName).toBeTruthy();
    }

    for (const dependencyName of [
      "@axe-core/playwright",
      "@playwright/test",
      "@testing-library/react",
      "@testing-library/user-event",
      "msw",
      "jsdom",
    ]) {
      expect(devDependencies[dependencyName], dependencyName).toBeTruthy();
    }
  });

  it("keeps the generated inventory and behavioural status connected", () => {
    expect(manifest.length).toBeGreaterThanOrEqual(80);
    expect(new Set(manifest.map((entry) => entry.function)).size).toBe(manifest.length);

    for (const entry of manifest.filter((item) => item.method !== "GET" || item.sideEffect !== "read")) {
      expect(statusNames.has(entry.function), entry.function).toBe(true);
      expect(entry.idempotent, entry.function).toBe(false);
      expect(entry.sideEffect, entry.function).not.toBe("read");
    }
  });

  it("requires diverse evidence before a side-effect row can be marked covered", () => {
    for (const entry of statuses.filter((item) => item.coverageStatus === "covered" && item.sideEffect !== "read")) {
      const evidence = entry.evidence.join("\n").toLowerCase();
      expect(evidence, entry.function).toMatch(/api|client|contract/);
      expect(evidence, entry.function).toMatch(/playwright|e2e|ui/);
      expect(evidence, entry.function).toMatch(/auth|role/);
      expect(evidence, entry.function).toMatch(/failure|4xx|5xx|retry|offline/);
    }
  });
});
