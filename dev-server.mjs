/**
 * HYBA Dev Server Bootstrap
 *
 * Transpiles server.ts on-the-fly with esbuild and runs it,
 * bypassing tsx which has known ESM loader issues with
 * Windows + OneDrive paths (ERR_INVALID_URL_SCHEME).
 *
 * Usage: node dev-server.mjs
 */

import { createRequire } from "node:module";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));

// Use esbuild (already a devDependency) to transpile the server
const require = createRequire(import.meta.url);
const esbuild = require("esbuild");

async function main() {
  const serverPath = path.join(__dirname, "server.ts");

  // Transpile server.ts to a temporary file
  const result = await esbuild.build({
    entryPoints: [serverPath],
    bundle: true,
    platform: "node",
    format: "esm",
    packages: "external",
    sourcemap: "inline",
    outfile: path.join(__dirname, "node_modules", ".hyba-dev-server.mjs"),
    tsconfig: path.join(__dirname, "tsconfig.json"),
  });

  if (result.errors.length > 0) {
    console.error("esbuild transpilation failed:", result.errors);
    process.exit(1);
  }

  // Dynamically import the transpiled server
  const serverUrl = new URL(
    "file:///" +
      path
        .join(__dirname, "node_modules", ".hyba-dev-server.mjs")
        .replace(/\\/g, "/"),
  );

  await import(serverUrl.href);
}

main().catch((err) => {
  console.error("Dev server bootstrap failed:", err);
  process.exit(1);
});