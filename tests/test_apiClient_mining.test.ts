import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import {
  clearToken,
  connectToPool,
  disconnectFromPool,
  pauseMining,
  resumeMining,
  setToken,
  startMiningProduction,
  stopMiningProduction,
  submitJob,
  submitMiningProductionShare,
  switchPool,
  updatePowerScale,
} from "../src/apiClient";

function ok(body: unknown = { status: "ok" }) {
  return new Response(JSON.stringify(body), {
    status: 200,
    headers: { "Content-Type": "application/json" },
  });
}

async function expectSingleMutation(
  call: () => Promise<unknown>,
  expected: { method: string; path: string; body?: unknown },
) {
  const fetchMock = vi.mocked(fetch);
  fetchMock.mockClear();
  fetchMock.mockResolvedValue(ok());
  await call();
  expect(fetchMock).toHaveBeenCalledTimes(1);
  const [url, init] = fetchMock.mock.calls[0] as [string, RequestInit];
  expect(url).toBe(expected.path);
  expect(init.method).toBe(expected.method);
  if (expected.body !== undefined) expect(JSON.parse(String(init.body))).toEqual(expected.body);
  const headers = init.headers as Headers;
  expect(headers.get("Authorization")).toBe("Bearer mining-token");
}

describe("apiClient mining and production-mining command contracts", () => {
  beforeEach(() => {
    vi.useFakeTimers();
    vi.stubGlobal("fetch", vi.fn());
    setToken("mining-token");
  });

  afterEach(() => {
    vi.useRealTimers();
    vi.unstubAllGlobals();
    clearToken();
  });

  it("sends one authenticated non-retried request for each core mining mutation", async () => {
    await expectSingleMutation(() => connectToPool({ pool_id: "braiins", capacity_ehs: 0.5 }), {
      method: "POST",
      path: "/api/mining/connect",
      body: { pool_id: "braiins", capacity_ehs: 0.5, switch: true },
    });
    await expectSingleMutation(() => switchPool({ pool_id: "via", capacity_ehs: 0.25 }), {
      method: "POST",
      path: "/api/mining/switch",
      body: { pool_id: "via", capacity_ehs: 0.25, switch: true },
    });
    await expectSingleMutation(() => disconnectFromPool(), {
      method: "POST",
      path: "/api/mining/disconnect",
      body: {},
    });
    await expectSingleMutation(() => pauseMining(), {
      method: "POST",
      path: "/api/mining/pause",
      body: {},
    });
    await expectSingleMutation(() => resumeMining(), {
      method: "POST",
      path: "/api/mining/resume",
      body: {},
    });
    await expectSingleMutation(() => updatePowerScale(0.5, 21), {
      method: "POST",
      path: "/api/mining/power",
      body: { scale: 0.5, phi_tier: 21 },
    });
  });

  it("enforces the 1 EH/s cap before mining connect, switch, and submit requests leave the browser", async () => {
    await expect(connectToPool({ pool_id: "x", capacity_ehs: 1.01 })).rejects.toThrow(
      "capacity_ehs",
    );
    await expect(switchPool({ pool_id: "x", capacity_ehs: Number.NaN })).rejects.toThrow(
      "capacity_ehs",
    );
    await expect(
      submitJob({ pool_id: "x", worker: "w", job_id: "job", nonce: "00", hashrate_ehs: 2 }),
    ).rejects.toThrow("hashrate_ehs");
    expect(fetch).not.toHaveBeenCalled();
  });

  it("does not retry production-mining destructive commands on 5xx", async () => {
    const fetchMock = vi
      .mocked(fetch)
      .mockResolvedValue(new Response(JSON.stringify({ error: "boom" }), { status: 500 }));

    await expect(startMiningProduction()).rejects.toMatchObject({ status: 500 });
    await expect(stopMiningProduction()).rejects.toMatchObject({ status: 500 });
    await expect(
      submitMiningProductionShare({
        pool_id: "pool",
        worker: "worker",
        job_id: "job-1",
        nonce: "abc",
      }),
    ).rejects.toMatchObject({ status: 500 });
    expect(fetchMock).toHaveBeenCalledTimes(3);
  });
});
