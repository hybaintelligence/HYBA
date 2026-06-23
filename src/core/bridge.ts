import axios from "axios";
import { logger, get_trace_context } from "./telemetry";
import { calculate_phi_resonance } from "./constants";

/**
 * HYBA Substrate Bridge
 * High-performance, low-latency RPC link between the Express secure bridge
 * and the Python mathematical core.
 */

const PYTHON_CORE_URL = process.env.PYTHON_CORE_URL || "http://127.0.0.1:3001";

const client = axios.create({
  baseURL: PYTHON_CORE_URL,
  timeout: 5000,
  headers: {
    "Content-Type": "application/json",
    "X-System-Origin": "HYBA-TS-SUBSTRATE",
  },
});

/**
 * Injects spectral signatures into outbound requests to the Python core.
 */
client.interceptors.request.use((config) => {
  const resonance = calculate_phi_resonance(Date.now());
  config.headers["X-Substrate-Resonance"] = resonance.toFixed(10);
  return config;
});

export const bridge = {
  /**
   * Universal RPC call to the Python mathematical core.
   */
  async call(method: string, path: string, data?: unknown) {
    const ctx = get_trace_context();
    const startTime = Date.now();

    try {
      const response = await client.request({
        method,
        url: path,
        data,
        headers: {
          "X-Request-ID": ctx.trace_id,
        },
      });

      const latency = Date.now() - startTime;
      logger.debug({ ...ctx, path, latency }, "Bridge: Deterministic RPC call successful.");

      return response.data;
    } catch (error: unknown) {
      const latency = Date.now() - startTime;
      const errorMessage = (error as { message?: string }).message ?? "Unknown error";
      const errorResponse = (error as { response?: { data?: unknown } }).response?.data;
      logger.error(
        {
          ...ctx,
          path,
          latency,
          err: errorMessage,
          response: errorResponse,
        },
        "Bridge: RPC call failed. Substrate discontinuity detected.",
      );
      throw error;
    }
  },

  /**
   * Health verification via resonant ping.
   */
  async ping(): Promise<boolean> {
    try {
      const result = await this.call("GET", "/");
      return result.status === "ok";
    } catch {
      return false;
    }
  },
};
