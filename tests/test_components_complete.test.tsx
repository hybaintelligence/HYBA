import React from "react";
import { render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";
import App from "../src/App";
import * as apiClient from "../src/apiClient";

const authState = vi.hoisted(() => ({ isAdmin: false, isExecutive: false }));

vi.mock("../src/components/AuthProvider", () => ({
  useAuth: () => ({
    user: null,
    backendUser: null,
    loading: false,
    isAdmin: authState.isAdmin,
    isExecutive: authState.isExecutive,
    hasRole: (role: string) => role === "admin" && authState.isAdmin,
  }),
}));

vi.mock("../src/components/SovereignGenesisPanel", () => ({
  SovereignGenesisPanel: () => <div>Sovereign genesis panel</div>,
}));
vi.mock("../src/components/SovereignCommandPost", () => ({
  SovereignCommandPost: () => <div>Sovereign command post</div>,
}));
vi.mock("../src/components/AIAssistant", () => ({ default: () => <div>AI assistant</div> }));
vi.mock("../src/components/AdminPanel", () => ({
  default: () => <section>Admin panel content</section>,
}));
vi.mock("../src/components/HybaAdminDashboard", () => ({
  default: () => <section>Executive dashboard content</section>,
}));
vi.mock("../src/components/MiningJobsSection", () => ({
  default: () => <section>Mining jobs content</section>,
}));
vi.mock("../src/components/HistoricalDataSection", () => ({
  default: () => <section>Historical data content</section>,
}));
vi.mock("../src/components/AnalyticsSection", () => ({
  default: () => <section>Analytics content</section>,
}));
vi.mock("../src/components/Sparkline", () => ({
  Sparkline: () => <div aria-label="Latency history" />,
}));

const proofEvidence = {
  schema_version: "hyba.extraordinary_evidence.v1",
  claim_boundary: "bounded",
  claims: [
    {
      claim_id: "quantum_math_substrate",
      title: "Quantum as mathematical substrate",
      operationalization: "Runtime exposes substrate-independent proof surfaces.",
      required_evidence: ["sealed_endpoint"],
      invariants: ["claims_present"],
      adversarial_tests: ["unknown_claim_fail_closed"],
      api_surfaces: ["/api/v1/intelligence/extraordinary-claims/evidence"],
      proof_status: "bounded",
    },
    {
      claim_id: "emergence_intelligence",
      title: "Emergence intelligence",
      operationalization: "Runtime exposes adversarially testable intelligence invariants.",
      required_evidence: ["adversarial_contract"],
      invariants: ["phi_scaling_monotone"],
      adversarial_tests: ["placeholder_language_rejected"],
      api_surfaces: ["/api/v1/intelligence/extraordinary-claims/evidence"],
      proof_status: "bounded",
    },
  ],
  millennium_problems: [
    "yang_mills_mass_gap",
    "riemann_hypothesis",
    "p_vs_np",
    "navier_stokes",
    "hodge_conjecture",
    "poincare_conjecture",
    "birch_swinnerton_dyer",
  ],
  phi: 1.61803398875,
  phi_scaling_samples: [1.61803398875],
  invariant_results: { claims_present: true, phi_scaling_monotone: true },
  adversarial_contract: { seal_all_evidence_packets: true },
  all_invariants_passed: true,
  evidence_seal: "0123456789abcdef",
};

const unavailableProofEvidence = {
  schema_version: "hyba.extraordinary_evidence.unavailable",
  status: "unavailable",
  source: "extraordinary_evidence_endpoint_unavailable",
  claim_boundary: "Extraordinary-claims evidence endpoint unavailable; invariants are not visible.",
  claims: [],
  millennium_problems: [],
  phi: Number.NaN,
  phi_scaling_samples: [],
  invariant_results: {},
  adversarial_contract: {},
  all_invariants_passed: false,
  evidence_seal: "",
};

const telemetry = {
  status: "success",
  latency: 42,
  health: {
    status: "ok",
    timestamp: "2026-06-23T00:00:00.000Z",
    version: "2.0.1",
    telemetry_source: "mock",
    quantumCoherence: 0.91,
    phiResonance: 0.87,
    quantumSpeedupFactor: 1.2,
    actualSpeedupFactor: 1.1,
    systemMetrics: {
      activePool: "ViaBTC",
      blockHeight: 850000,
      currentHashrate: 0.4,
      powerConsumption: 12,
      networkDifficulty: 88,
      difficultyTarget: "target",
      system_health: "healthy",
      power_scale: 1,
      phi_tier: 12,
    },
  },
  pools: {
    summary: { total_pools: 2, configured_pools: 2, active_pools: 1, telemetry_source: "mock" },
    pools: [
      {
        pool_id: "viabtc",
        name: "ViaBTC",
        url: "stratum+tcp://via",
        configured: true,
        is_active: true,
        status: "connected",
        credential_mode: "username_password",
        required_fields: ["username", "password"],
        performance: { latency_ms: 20, shares_submitted: 3 },
      },
      {
        pool_id: "braiins",
        name: "Braiins",
        url: "stratum+tcp://braiins",
        configured: true,
        is_active: false,
        status: "configured",
        credential_mode: "username_password",
        required_fields: ["username", "password"],
        performance: { latency_ms: 25, shares_submitted: 1 },
      },
      {
        pool_id: "ckpool",
        name: "CKPool",
        url: "stratum+tcp://ck",
        configured: false,
        is_active: false,
        status: "not_configured",
        credential_mode: "btc_address",
        required_fields: ["btc_address"],
        performance: { latency_ms: 0, shares_submitted: 0 },
      },
    ],
  },
  security: {
    status: "nominal",
    timestamp: "2026-06-23T00:00:00.000Z",
    threat_level: "low",
    defense_systems: {},
  },
  consciousness: { status: "nominal", source: "mock", integrated_information: 0.5 },
  extraordinaryEvidence: proofEvidence,
};

function withProofEvidence(evidence: typeof proofEvidence | typeof unavailableProofEvidence) {
  return {
    ...telemetry,
    extraordinaryEvidence: evidence,
  };
}

function getProofSealPanel() {
  const heading = screen.getByText("Proof seal telemetry");
  const panel = heading.closest(".overflow-hidden");
  if (!panel) {
    throw new Error("Proof seal telemetry panel container was not rendered");
  }
  return within(panel as HTMLElement);
}

function mockStorage() {
  const values = new Map<string, string>();
  Object.defineProperty(window, "localStorage", {
    configurable: true,
    value: {
      getItem: vi.fn((key: string) => values.get(key) ?? null),
      setItem: vi.fn((key: string, value: string) => values.set(key, value)),
      removeItem: vi.fn((key: string) => values.delete(key)),
      clear: vi.fn(() => values.clear()),
    },
  });
}

beforeEach(() => {
  authState.isAdmin = false;
  authState.isExecutive = false;
  mockStorage();
  Object.defineProperty(window, "matchMedia", {
    configurable: true,
    value: vi.fn(() => ({
      matches: false,
      addEventListener: vi.fn(),
      removeEventListener: vi.fn(),
    })),
  });
  vi.stubGlobal(
    "fetch",
    vi.fn(() => Promise.resolve(new Response(JSON.stringify({ status: "ok" })) as any)),
  );
  vi.spyOn(apiClient, "fetchTelemetryData").mockResolvedValue(telemetry as any);
  vi.spyOn(apiClient, "fetchProductsApi").mockResolvedValue(
    new Response(
      JSON.stringify([{ id: "p1", name: "HYBA Console", description: "Control plane" }]),
    ) as any,
  );
  vi
    .spyOn(apiClient, "fetchProfileApi")
    .mockResolvedValue(new Response(JSON.stringify({ success: false }))) as any;
  vi.spyOn(apiClient, "loginApi").mockResolvedValue({
    success: true,
    token: "token",
    user: { username: "operator", role: "miner" },
  } as any);
  vi.spyOn(apiClient, "registerApi").mockResolvedValue({ success: true } as any);
  vi.spyOn(apiClient, "updatePowerScale").mockResolvedValue({ status: "ok" } as any);
  vi.spyOn(apiClient, "switchPool").mockResolvedValue({ status: "ok" } as any);
  vi.spyOn(apiClient, "disconnectFromPool").mockResolvedValue({ status: "ok" } as any);
  vi.spyOn(apiClient, "configurePool").mockResolvedValue({ status: "ok" } as any);
});

describe("complete App component action coverage", () => {
  it("covers dashboard loading, proof telemetry, refresh, polling pause/resume, theme, navigation, power, phi, and pool actions", async () => {
    const user = userEvent.setup();
    render(<App />);

    expect(screen.getByText("Quantum Intelligence Runtime Console")).toBeInTheDocument();
    expect(await screen.findByText("Sovereign Quantum Intelligence Execution")).toBeInTheDocument();

    const proofPanel = getProofSealPanel();
    expect(proofPanel.getByText("Evidence seal")).toBeInTheDocument();
    expect(proofPanel.getByText("0123456789ab…")).toBeInTheDocument();
    expect(proofPanel.getByText("Invariant status")).toBeInTheDocument();
    expect(proofPanel.getByText("PASS")).toBeInTheDocument();
    expect(proofPanel.getByText("Invariant checks")).toBeInTheDocument();
    expect(proofPanel.getByText("2 / 2")).toBeInTheDocument();
    expect(proofPanel.getByText("Claim contracts")).toBeInTheDocument();
    expect(proofPanel.getByText("2")).toBeInTheDocument();
    expect(proofPanel.getByText("Millennium ops")).toBeInTheDocument();
    expect(proofPanel.getByText("7")).toBeInTheDocument();
    expect(proofPanel.getByText("Seal policy")).toBeInTheDocument();
    expect(proofPanel.getByText("ENFORCED")).toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: /refresh/i }));
    expect(apiClient.fetchTelemetryData).toHaveBeenCalledTimes(2);

    await user.click(screen.getByRole("button", { name: /live/i }));
    expect(screen.getByRole("button", { name: /paused/i })).toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: /paused/i }));
    expect(screen.getByRole("button", { name: /live/i })).toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: /toggle color theme/i }));
    expect(document.documentElement.classList.contains("dark")).toBe(true);

    await user.click(screen.getByRole("button", { name: /jobs/i }));
    expect(screen.getByText("Mining jobs content")).toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: /dashboard/i }));
    await user.click(screen.getByRole("button", { name: /history/i }));
    expect(screen.getByText("Historical data content")).toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: /dashboard/i }));
    await user.click(screen.getByRole("button", { name: /analytics/i }));
    expect(screen.getByText("Analytics content")).toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: /dashboard/i }));

    await user.clear(screen.getByLabelText(/power scale control/i));
    await user.type(screen.getByLabelText(/power scale control/i), "2");
    await waitFor(() => expect(apiClient.updatePowerScale).toHaveBeenCalled());
    await user.selectOptions(screen.getByLabelText(/phi tier control/i), "15");
    expect(apiClient.updatePowerScale).toHaveBeenLastCalledWith(expect.any(Number), 15);

    await user.click(screen.getAllByRole("button", { name: /switch/i })[0]);
    await waitFor(() =>
      expect(apiClient.switchPool).toHaveBeenCalledWith({
        pool_id: "braiins",
        capacity_ehs: expect.any(Number),
        switch: true,
      }),
    );
    await user.click(screen.getAllByRole("button", { name: /disconnect/i })[0]);
    expect(apiClient.disconnectFromPool).toHaveBeenCalled();

    await user.click(screen.getAllByRole("button", { name: /setup/i })[0]);
    expect(screen.getByText(/Pool Config: CKPool/i)).toBeInTheDocument();
    await user.type(screen.getByLabelText(/btc address/i), "bc1qhybatest");
    await user.click(screen.getByRole("button", { name: /save pool config/i }));
    await waitFor(() =>
      expect(apiClient.configurePool).toHaveBeenCalledWith(
        expect.objectContaining({ pool_id: "ckpool", btc_address: "bc1qhybatest" }),
      ),
    );
  });

  it("degrades proof telemetry fail-closed when the evidence endpoint is unavailable", async () => {
    vi.mocked(apiClient.fetchTelemetryData).mockResolvedValueOnce(
      withProofEvidence(unavailableProofEvidence) as any,
    );

    render(<App />);

    expect(await screen.findByText("Proof seal telemetry")).toBeInTheDocument();
    const proofPanel = getProofSealPanel();
    expect(proofPanel.getByText("FAIL-CLOSED")).toBeInTheDocument();
    expect(proofPanel.getByText("0 / 0")).toBeInTheDocument();
    expect(proofPanel.getByText("UNAVAILABLE")).toBeInTheDocument();
    expect(proofPanel.getAllByText("—").length).toBeGreaterThan(0);
  });

  it("renders every valid evidence seal as a shortened proof metric with non-zero invariant coverage", async () => {
    const evidenceCases = [
      {
        seal: "abcdef1234567890",
        invariants: { claims_present: true },
        expectedSeal: "abcdef123456…",
        expectedInvariantCount: "1 / 1",
      },
      {
        seal: "fedcba9876543210",
        invariants: { claims_present: true, phi_scaling_monotone: true, hostile_prompt_rejected: false },
        expectedSeal: "fedcba987654…",
        expectedInvariantCount: "2 / 3",
      },
    ];

    for (const evidenceCase of evidenceCases) {
      vi.mocked(apiClient.fetchTelemetryData).mockResolvedValueOnce(
        withProofEvidence({
          ...proofEvidence,
          evidence_seal: evidenceCase.seal,
          invariant_results: evidenceCase.invariants,
          all_invariants_passed: Object.values(evidenceCase.invariants).every(Boolean),
        }) as any,
      );

      const { unmount } = render(<App />);

      expect(await screen.findByText("Proof seal telemetry")).toBeInTheDocument();
      const proofPanel = getProofSealPanel();
      expect(proofPanel.getByText(evidenceCase.expectedSeal)).toBeInTheDocument();
      expect(proofPanel.getByText(evidenceCase.expectedInvariantCount)).toBeInTheDocument();
      expect(evidenceCase.expectedInvariantCount.startsWith("0 /")).toBe(false);
      unmount();
    }
  });

  it("covers login, register, logout, offline retry, and network toast dismissal", async () => {
    const user = userEvent.setup();
    vi.spyOn(apiClient, "fetchTelemetryData")
      .mockRejectedValueOnce(new Error("backend offline"))
      .mockResolvedValue(telemetry as any);
    render(<App />);

    expect(await screen.findByText("Telemetry interruption")).toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: /retry connection/i }));
    expect(await screen.findByText("Sovereign Quantum Intelligence Execution")).toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: /dismiss network status/i }));
    expect(screen.queryByText(/connection restored/i)).not.toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: /sign up/i }));
    await user.type(screen.getByLabelText(/operator handle/i), "new-operator");
    await user.type(screen.getByLabelText(/password/i), "secret123");
    await user.click(screen.getByRole("button", { name: /^register$/i }));
    expect(await screen.findByText(/registered successfully/i)).toBeInTheDocument();

    await user.clear(screen.getByLabelText(/operator handle/i));
    await user.type(screen.getByLabelText(/operator handle/i), "operator");
    await user.type(screen.getByLabelText(/password/i), "secret123");
    await user.click(screen.getByRole("button", { name: /log in/i }));
    expect(await screen.findByText(/welcome back, operator/i)).toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: /log out/i }));
    expect(screen.getByText(/session ended securely/i)).toBeInTheDocument();
  });

  it("gates admin and executive navigation by role", async () => {
    const { rerender } = render(<App />);
    await screen.findByText("Sovereign Quantum Intelligence Execution");
    expect(screen.queryByRole("button", { name: /admin/i })).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /executive/i })).not.toBeInTheDocument();

    authState.isAdmin = true;
    rerender(<App />);
    await screen.findByRole("button", { name: /admin/i });
    expect(screen.queryByRole("button", { name: /executive/i })).not.toBeInTheDocument();

    authState.isExecutive = true;
    rerender(<App />);
    await userEvent.click(screen.getByRole("button", { name: /executive/i }));
    expect(screen.getByText("Executive dashboard content")).toBeInTheDocument();
  });
});
