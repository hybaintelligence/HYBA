import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import {
  applyEvolution,
  boostConsciousness,
  clearToken,
  intelligenceOrchestrate,
  migrateToHabitat,
  quarantineLane,
  scaleIntelligence,
  securityShield,
  setMiningIntent,
  setToken,
  unifiedShareResult,
} from "../src/apiClient";

const success = () =>
  new Response(JSON.stringify({ status: "ok", accepted: true }), {
    status: 200,
    headers: { "Content-Type": "application/json" },
  });

describe("apiClient autonomous/destructive safety contracts", () => {
  beforeEach(() => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockImplementation(() =>
        Promise.resolve(
          new Response(JSON.stringify({ status: "ok", accepted: true }), {
            status: 200,
            headers: { "Content-Type": "application/json" },
          }),
        ),
      ),
    );
    const autonomyStorage = new Map<string, string>();
    vi.stubGlobal("localStorage", {
      getItem: (key: string) => autonomyStorage.get(key) ?? null,
      setItem: (key: string, value: string) => { autonomyStorage.set(key, value); },
      removeItem: (key: string) => { autonomyStorage.delete(key); },
      clear: () => { autonomyStorage.clear(); },
      key: vi.fn(),
      length: 0,
    });
    setToken("executive-token");
  });

  afterEach(() => {
    vi.unstubAllGlobals();
    clearToken();
  });

  it("routes autonomous commands to mocked /api paths with explicit payloads and auth", async () => {
    await scaleIntelligence(0.75, "controller");
    await boostConsciousness(0.25, 2);
    await intelligenceOrchestrate({
      goal: "sandbox-plan",
      constraints: { safety: "no-live-destructive-calls" },
    });
    await securityShield({ activation: true, reason: "contract test" });
    await unifiedShareResult({ task_id: "contract", result: { status: "ok" }, confidence: 0.9 });
    await quarantineLane(3);
    await applyEvolution("conj-1");
    await setMiningIntent({ intent: "STASIS" });
    await migrateToHabitat("testnet-pool");

    const observed = vi.mocked(fetch).mock.calls.map(([url, init]) => ({
      url,
      method: (init as RequestInit).method,
      headers: (init as RequestInit).headers as Headers,
      body: (init as RequestInit).body ? JSON.parse(String((init as RequestInit).body)) : undefined,
    }));

    expect(observed.map((call) => [call.method, call.url])).toEqual([
      ["POST", "/api/v1/intelligence/scale"],
      ["POST", "/api/v1/intelligence/consciousness/boost"],
      ["POST", "/api/v1/intelligence/orchestrate"],
      ["POST", "/api/security/shield"],
      ["POST", "/api/v1/unified/share-result"],
      ["POST", "/api/organism/immune/quarantine/3"],
      ["POST", "/api/organism/cognition/evolve/conj-1"],
      ["POST", "/api/organism/executive/intent"],
      ["PUT", "/api/organism/executive/habitats/migrate/testnet-pool"],
    ]);
    for (const call of observed)
      expect(call.headers.get("Authorization")).toBe("Bearer executive-token");
    expect(observed[0].body).toEqual({ scale: 0.75, target: "controller" });
    expect(observed[7].body).toEqual({ intent: "STASIS" });
  });

  it("validates finite autonomous scaling payloads before sending requests", async () => {
    await expect(scaleIntelligence(Number.NaN)).rejects.toThrow("scale");
    await expect(boostConsciousness(Number.POSITIVE_INFINITY)).rejects.toThrow("boost");
    await expect(boostConsciousness(0.1, Number.NaN)).rejects.toThrow("taskBudget");
    expect(fetch).not.toHaveBeenCalled();
  });

  it("does not retry destructive/autonomous commands on 5xx", async () => {
    vi.mocked(fetch).mockResolvedValue(
      new Response(JSON.stringify({ error: "server_error" }), { status: 500 }),
    );
    await expect(securityShield({ activation: true })).rejects.toMatchObject({ status: 500 });
    await expect(setMiningIntent({ intent: "ACTIVATE" })).rejects.toMatchObject({ status: 500 });
    await expect(migrateToHabitat("sandbox")).rejects.toMatchObject({ status: 500 });
    expect(fetch).toHaveBeenCalledTimes(3);
  });
});
