/**
 * HYBA Secure Bridge configuration guardrails.
 *
 * Kept side-effect free so production validation can be exercised with unit and
 * property tests without starting the Express bridge or spawning the backend.
 */

export const MIN_PRODUCTION_JWT_SECRET_BYTES = 32;

type JwtSecretValidation = {
  ok: boolean;
  reason?: string;
};

export function validateProductionJwtSecret(
  secret: string | undefined | null,
): JwtSecretValidation {
  if (!secret) {
    return { ok: false, reason: "JWT_SECRET is required in production" };
  }

  const byteLength = Buffer.byteLength(secret, "utf8");
  if (byteLength < MIN_PRODUCTION_JWT_SECRET_BYTES) {
    return {
      ok: false,
      reason: `JWT_SECRET must be at least ${MIN_PRODUCTION_JWT_SECRET_BYTES} bytes in production`,
    };
  }

  return { ok: true };
}
