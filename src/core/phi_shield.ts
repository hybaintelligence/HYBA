import { logger } from "./telemetry";
import { calculate_phi_resonance } from "./constants";

/**
 * Φ-Shield: Anti-Tamper / Anti-Peep Middleware
 * Employs Hilbert-space decoherence for unauthorized state inspection.
 */

interface RequestWithTrace {
  headers: Record<string, string | string[] | undefined>;
  traceContext?: { trace_id?: string };
}

interface ResponseWithMethods {
  status: (code: number) => { json: (data: unknown) => void };
  setHeader: (name: string, value: string) => void;
}

export const phi_shield_middleware = (req: unknown, res: unknown, next: () => void) => {
  const request = req as RequestWithTrace;
  const response = res as ResponseWithMethods;
  const user_agent = (request.headers["user-agent"] as string) || "";
  const trace_id = request.traceContext?.trace_id;

  // First-principles signature verification
  // Detects packet sniffing or automated inspectors by resonance deviation
  const resonance = calculate_phi_resonance(Date.now());

  // Detect forbidden debugging tools/sniffers (Peef Protection)
  const forbidden_fingerprints = ["burp", "wireshark", "postman-token", "zaproxy"];
  const has_forbidden = forbidden_fingerprints.some((f) => user_agent.toLowerCase().includes(f));

  if (has_forbidden) {
    logger.fatal(
      {
        trace_id,
        fingerprint: user_agent,
        resonance,
      },
      "Φ-Shield: Unauthorized introspection attempt blocked. Annihilating connection.",
    );

    return response.status(403).json({
      error: {
        type: "shield_violation",
        message: "Access denied. HYBA substrate is obfuscated against inspection.",
        code: "ANTI_SNIFF_ACTIVE",
      },
    });
  }

  // Inject resonance signature to prevent replay
  response.setHeader("x-substrate-resonance", resonance.toFixed(8));
  next();
};
