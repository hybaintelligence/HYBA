/**
 * Production JWT secret validation utilities.
 * Tests in tests/ import from "../bridge_security" which resolves to this file.
 */

export const MIN_PRODUCTION_JWT_SECRET_BYTES = 32;

export function validateProductionJwtSecret(
  secret: string | undefined | null,
): { ok: true } | { ok: false; reason: string } {
  if (secret === undefined || secret === null || secret === "") {
    return { ok: false, reason: "JWT_SECRET is required in production" };
  }
  const byteLength = Buffer.byteLength(secret, "utf8");
  if (byteLength < MIN_PRODUCTION_JWT_SECRET_BYTES) {
    return {
      ok: false,
      reason: `JWT_SECRET must be at least ${MIN_PRODUCTION_JWT_SECRET_BYTES} bytes (got ${byteLength})`,
    };
  }
  return { ok: true };
}
