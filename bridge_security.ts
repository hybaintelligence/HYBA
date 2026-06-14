/**
 * Re-export from src/bridge_security for test resolution.
 * Tests in tests/ import from "../bridge_security" which resolves to this file.
 */
export { MIN_PRODUCTION_JWT_SECRET_BYTES, validateProductionJwtSecret } from "./src/bridge_security";
