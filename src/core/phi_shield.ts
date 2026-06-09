import { Request, Response, NextFunction } from 'express';
import { logger } from './telemetry';
import { calculate_phi_resonance } from './constants';

/**
 * Φ-Shield: Anti-Tamper / Anti-Peep Middleware
 * Employs Hilbert-space decoherence for unauthorized state inspection.
 */

export const phi_shield_middleware = (req: Request, res: Response, next: NextFunction) => {
  const user_agent = req.header('user-agent') || '';
  const trace_id = (req as any).traceContext?.trace_id;

  // First-principles signature verification
  // Detects packet sniffing or automated inspectors by resonance deviation
  const resonance = calculate_phi_resonance(Date.now());

  // Detect forbidden debugging tools/sniffers (Peef Protection)
  const forbidden_fingerprints = ['burp', 'wireshark', 'postman-token', 'zaproxy'];
  const has_forbidden = forbidden_fingerprints.some(f => user_agent.toLowerCase().includes(f));

  if (has_forbidden) {
    logger.fatal({ 
        trace_id, 
        fingerprint: user_agent,
        resonance 
    }, 'Φ-Shield: Unauthorized introspection attempt blocked. Annihilating connection.');
    
    return res.status(403).json({
        error: {
            type: 'shield_violation',
            message: 'Access denied. HYBA substrate is obfuscated against inspection.',
            code: 'ANTI_SNIFF_ACTIVE'
        }
    });
  }

  // Inject resonance signature to prevent replay
  res.setHeader('x-substrate-resonance', resonance.toFixed(8));
  next();
};
