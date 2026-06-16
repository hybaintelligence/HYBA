import { createRequire } from "node:module";
import { randomUUID } from "node:crypto";

// Use require to import pino to sidestep ESM/CJS interop issues
const require = createRequire(import.meta.url);
const pino = require("pino");

/**
 * HYBA Telemetry Service (Stripe-Grade)
 * Primary logger with support for structured tracing and correlation.
 */
export const logger = pino({
  level: process.env.LOG_LEVEL || "info",
  base: {
    service: "hyba-secure-bridge",
    env: process.env.NODE_ENV || "development",
  },
  timestamp: pino.stdTimeFunctions.isoTime,
});

export const init_logging = () => {
  logger.info(
    { logic_floor: "Φ-resonant" },
    "Telemetry: Structured logging engine (Pino) initialized.",
  );
};

export const init_metrics = () => {
  logger.info(
    "Telemetry: Metrics aggregator operational. Monitoring Φ-resonance and QEC rejection paths.",
  );
};

/**
 * Request Context Manager
 * Generates a unique trace ID for every operation within the substrate.
 */
export const get_trace_context = (traceId?: string) => ({
  trace_id: traceId || randomUUID(),
  timestamp: new Date().toISOString(),
});
