import fs from "node:fs";
import path from "node:path";
import { describe, expect, it } from "vitest";

const root = process.cwd();
const readText = (relativePath: string) => fs.readFileSync(path.join(root, relativePath), "utf8");

describe("HYBA autonomy ubiquity contract", () => {
  const app = readText("src/App.tsx");
  const commandPost = readText("src/components/SovereignCommandPost.tsx");
  const rail = readText("src/components/HybaIntelligenceRail.tsx");
  const proofsApi = readText("python_backend/hyba_genesis_api/api/proofs.py");
  const fabricCore = readText("python_backend/hyba_genesis_api/core/autonomy_fabric.py");

  it("mounts the intelligence rail through an always-visible command-post surface", () => {
    expect(app).toContain("SovereignCommandPost");
    expect(commandPost).toContain("HybaIntelligenceRail");
    expect(rail).toContain("HYBA Intelligence Rail");
    expect(rail).toContain("Observe → Reason → Recommend → Simulate → Approve → Execute → Audit → Learn");
  });

  it("forces every client-facing autonomy panel to explain value, evidence, and approval boundaries", () => {
    for (const contractSignal of [
      "clientValue",
      "recommendation",
      "approvalRequired",
      "Evidence:",
      "Approval required",
      "Autonomous with audit",
      "Clients can interrogate HYBA",
    ]) {
      expect(rail, contractSignal).toContain(contractSignal);
    }
  });

  it("exposes backend autonomy evidence through production proof endpoints", () => {
    for (const endpoint of [
      "/autonomy-fabric",
      "/client-intelligence-brief",
      "/autonomy-fabric/simulate",
      "/autonomy-fabric/execute",
    ]) {
      expect(proofsApi, endpoint).toContain(endpoint);
    }

    for (const backendContract of [
      "build_autonomy_fabric_snapshot",
      "build_client_intelligence_brief",
      "simulate_autonomy_action",
      "request_autonomy_execution",
    ]) {
      expect(fabricCore, backendContract).toContain(backendContract);
    }
  });

  it("preserves fail-closed market posture for high-risk autonomy", () => {
    expect(fabricCore).toContain("High-impact or externally material actions must be approval-gated");
    expect(fabricCore).toContain("high_risk_actions_approval_gated");
    expect(fabricCore).toContain("approval_required");
    expect(fabricCore).toContain("will_execute_without_approval");
    expect(fabricCore).toContain("approval_required");
  });
});
