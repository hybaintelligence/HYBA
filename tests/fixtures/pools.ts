export const poolsFixture = {
  pools: [
    { pool_id: "sandbox", name: "Sandbox Pool", configured: true, enabled: true, is_active: true },
  ],
  summary: {
    total_pools: 1,
    configured_pools: 1,
    active_pools: 1,
    telemetry_source: "msw-fixture",
  },
};

export const poolConfigFixture = {
  pools: poolsFixture.pools,
  active_pool_id: "sandbox",
  timestamp: "2026-06-19T00:00:00.000Z",
};
