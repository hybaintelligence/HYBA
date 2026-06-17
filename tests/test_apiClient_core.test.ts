import { describe, it, expect, vi } from "vitest";
import fc from "fast-check";
import { assertPulviniHashrateCap, getSecurityStatus, fetchTelemetryData } from "../src/apiClient";

// Property and unit tests for API client core functionality

describe("assertPulviniHashrateCap", () => {
  it("allows undefined and numbers within [0, 1]", () => {
    expect(() => assertPulviniHashrateCap(undefined, "cap")).not.toThrow();
    expect(() => assertPulviniHashrateCap(0, "cap")).not.toThrow();
    expect(() => assertPulviniHashrateCap(1, "cap")).not.toThrow();
    expect(() => assertPulviniHashrateCap(0.5, "cap")).not.toThrow();
  });

  it("throws for numbers outside [0, 1]", () => {
    expect(() => assertPulviniHashrateCap(-0.1, "cap")).toThrow();
    expect(() => assertPulviniHashrateCap(1.1, "cap")).toThrow();
    expect(() => assertPulviniHashrateCap(Number.NaN, "cap")).toThrow();
    expect(() => assertPulviniHashrateCap(Infinity, "cap")).toThrow();
  });

  it("property: throws outside interval", async () => {
    await fc.assert(
      fc.property(
        fc.oneof(
          fc.double({ min: -1000, max: -1, noNaN: true }),
          fc.double({ min: 1.0000001, max: 1000, noNaN: true }),
        ),
        (value) => {
          try {
            assertPulviniHashrateCap(value, "cap");
            return false;
          } catch {
            return true;
          }
        },
      ),
    );
  });
});

describe("getSecurityStatus", () => {
  it("calls fetch with /security/status and returns parsed json", async () => {
    const sample = { status: "ok" };
    const mockFetch = vi.fn().mockResolvedValue({
      ok: true,
      json: () => Promise.resolve(sample),
    });
    vi.stubGlobal("fetch", mockFetch);
    vi.stubGlobal("localStorage", {
      getItem: vi.fn().mockReturnValue(null),
      setItem: vi.fn(),
      removeItem: vi.fn(),
    });
    const result = await getSecurityStatus();
    expect(mockFetch).toHaveBeenCalledTimes(1);
    expect(mockFetch).toHaveBeenCalledWith(
      "/api/security/status",
      expect.objectContaining({ method: "GET" }),
    );
    expect(result).toEqual(sample);
    vi.unstubAllGlobals();
  });
});

describe("fetchTelemetryData", () => {
  it("returns aggregated telemetry data and calls endpoints", async () => {
    const health = { status: "ok", timestamp: "now", version: "1.0.0", telemetry_source: "test" };
    const consciousness = {
      status: "unknown",
      source: "ai_endpoint_unavailable",
      consciousness_level: null,
      phi_resonance: null,
      integrated_information: null,
    };
    const pools = {
      pools: [],
      summary: { total_pools: 0, active_pools: 0, telemetry_source: "test" },
    };
    const security = { status: "safe" };

    const responseMap: Record<string, any> = {
      "/api/health": health,
      "/api/ai/consciousness": consciousness,
      "/api/mining/pools": pools,
      "/api/security/status": security,
    };

    const mockFetch = vi.fn((url: string, _init: RequestInit) => {
      const data = responseMap[url];
      if (data) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve(data),
        });
      }
      return Promise.resolve({
        ok: false,
        status: 404,
        json: () => Promise.resolve({}),
      });
    });
    vi.stubGlobal("fetch", mockFetch);
    vi.stubGlobal("localStorage", {
      getItem: vi.fn().mockReturnValue(null),
      setItem: vi.fn(),
      removeItem: vi.fn(),
    });
    const result = await fetchTelemetryData();
    expect(mockFetch.mock.calls.length).toBeGreaterThanOrEqual(4);
    expect(result.health.status).toBe("ok");
    expect(result.consciousness.status).toBe("unknown");
    expect(result.pools.summary.total_pools).toBe(0);
    expect(result.security.status).toBe("safe");
    vi.unstubAllGlobals();
  });
});
