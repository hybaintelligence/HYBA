import { describe, expect, it } from "vitest";
import { execFileSync } from "node:child_process";
import { readFileSync } from "node:fs";

interface ManifestRow {
  function: string;
  method: string;
  path: string;
  sideEffect: string;
  role: string;
  idempotent: boolean;
  tested: boolean;
}

describe("frontend API command manifest", () => {
  it("extracts a machine-readable route manifest for every apiClient helper-backed command", () => {
    execFileSync(process.execPath, ["scripts/extract_api_client_manifest.mjs"], { stdio: "pipe" });
    const manifest = JSON.parse(readFileSync("artifacts/frontend_api_command_manifest.json", "utf8")) as ManifestRow[];

    expect(manifest.length).toBeGreaterThanOrEqual(80);
    expect(new Set(manifest.map((row) => row.function)).size).toBe(manifest.length);
    expect(manifest.every((row) => ["GET", "POST", "PUT", "PATCH", "DELETE"].includes(row.method))).toBe(true);
    expect(manifest.every((row) => row.path.startsWith("/api/"))).toBe(true);
    expect(manifest.filter((row) => row.method !== "GET").every((row) => row.sideEffect !== "read" && row.idempotent === false)).toBe(true);

    expect(manifest).toEqual(
      expect.arrayContaining([
        expect.objectContaining({ function: "pauseMining", method: "POST", path: "/api/mining/pause", sideEffect: "destructive", role: "operator_or_admin", idempotent: false }),
        expect.objectContaining({ function: "deleteAdminUser", method: "DELETE", path: "/api/admin/users/${userId}", sideEffect: "destructive", role: "admin", idempotent: false }),
        expect.objectContaining({ function: "setMiningIntent", method: "POST", path: "/api/organism/executive/intent", role: "executive", idempotent: false }),
      ]),
    );
  });
});
