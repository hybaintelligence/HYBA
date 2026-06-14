import { describe, expect, it } from "vitest";
import fc from "fast-check";
import { MIN_PRODUCTION_JWT_SECRET_BYTES, validateProductionJwtSecret } from "../bridge_security";

describe("production JWT secret validation", () => {
  it("rejects missing production JWT secrets", () => {
    expect(validateProductionJwtSecret(undefined).ok).toBe(false);
    expect(validateProductionJwtSecret("").ok).toBe(false);
  });

  it("rejects secrets below the production byte floor", () => {
    const weakSecret = "x".repeat(MIN_PRODUCTION_JWT_SECRET_BYTES - 1);
    const result = validateProductionJwtSecret(weakSecret);
    expect(result.ok).toBe(false);
    expect(result.reason).toContain(`${MIN_PRODUCTION_JWT_SECRET_BYTES}`);
  });

  it("accepts secrets that meet the production byte floor", () => {
    const strongSecret = "x".repeat(MIN_PRODUCTION_JWT_SECRET_BYTES);
    expect(validateProductionJwtSecret(strongSecret)).toEqual({ ok: true });
  });

  it("property: accepts exactly the secrets whose UTF-8 byte length reaches the production floor", () => {
    fc.assert(
      fc.property(fc.string({ minLength: 0, maxLength: 128 }), (secret) => {
        const expected = Buffer.byteLength(secret, "utf8") >= MIN_PRODUCTION_JWT_SECRET_BYTES;
        expect(validateProductionJwtSecret(secret).ok).toBe(expected);
      })
    );
  });
});
