import { describe, expect, it, vi } from "vitest";
import { get_trace_context, init_logging, init_metrics, logger } from "../src/core/telemetry";

describe("HYBA telemetry service", () => {
  it("initializes structured logging and metrics through the shared logger", () => {
    const info = vi.spyOn(logger, "info").mockImplementation(() => {});

    init_logging();
    init_metrics();

    expect(info).toHaveBeenCalledWith(
      { logic_floor: "Φ-resonant" },
      "Telemetry: Structured logging engine (Pino) initialized.",
    );
    expect(info).toHaveBeenCalledWith(
      "Telemetry: Metrics aggregator operational. Monitoring Φ-resonance and QEC rejection paths.",
    );

    info.mockRestore();
  });

  it("returns explicit trace IDs unchanged and generates IDs when omitted", () => {
    const explicit = get_trace_context("trace-fixed");
    const generated = get_trace_context();

    expect(explicit.trace_id).toBe("trace-fixed");
    expect(explicit.timestamp).toEqual(expect.any(String));
    expect(Number.isNaN(Date.parse(explicit.timestamp))).toBe(false);
    expect(generated.trace_id).toEqual(expect.any(String));
    expect(generated.trace_id).not.toBe("trace-fixed");
    expect(Number.isNaN(Date.parse(generated.timestamp))).toBe(false);
  });
});
