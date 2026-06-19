import React from "react";
import { render, screen, waitFor } from "@testing-library/react";
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

const telemetry = {
  latency: 42,
  health: {
    status: "ok",
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
    summary: { total_pools: 2, configured_pools: 2, active_pools: 1 },
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
  security: { status: "nominal", threat_level: "low", defense_systems: {} },
  consciousness: { status: "nominal", integrated_information: 0.5 },
};

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
  it("covers dashboard loading, refresh, polling pause/resume, theme, navigation, power, phi, and pool actions", async () => {
    const user = userEvent.setup();
    render(<App />);

    expect(screen.getByText("Genesis Runtime Console")).toBeInTheDocument();
    expect(await screen.findByText("Enterprise-Grade Mining Operations")).toBeInTheDocument();

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

  it("covers login, register, logout, offline retry, and network toast dismissal", async () => {
    const user = userEvent.setup();
    vi.spyOn(apiClient, "fetchTelemetryData")
      .mockRejectedValueOnce(new Error("backend offline"))
      .mockResolvedValue(telemetry as any);
    render(<App />);

    expect(await screen.findByText("Telemetry interruption")).toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: /retry connection/i }));
    expect(await screen.findByText("Enterprise-Grade Mining Operations")).toBeInTheDocument();

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
    await screen.findByText("Enterprise-Grade Mining Operations");
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
