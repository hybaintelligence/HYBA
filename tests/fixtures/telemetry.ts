export const telemetryHealthFixture = {
  status: "ok",
  timestamp: "2026-06-19T00:00:00.000Z",
  version: "test",
  telemetry_source: "msw-fixture",
  systemMetrics: {
    currentHashrate: 0.42,
    powerConsumption: 1200,
    activePool: "sandbox",
  },
};

export const telemetrySecurityFixture = {
  status: "safe",
  timestamp: "2026-06-19T00:00:00.000Z",
  threat_level: "low",
  source: "msw-fixture",
};
