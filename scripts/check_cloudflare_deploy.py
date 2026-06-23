#!/usr/bin/env python3
"""Cloudflare Pages deployment preflight for HYBA.

The check is intentionally filesystem-only so it can run in CI before secrets are
available. It verifies the repo contains the Pages config, security headers,
SPA fallback, and edge API proxy functions required for a production deploy.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REQUIRED_FILES = [
    "wrangler.toml",
    "public/_headers",
    "public/_redirects",
    "functions/api/[[path]].ts",
    "functions/health/[[path]].ts",
    "functions/bridge/health.ts",
    ".env.example",
]


def fail(message: str) -> None:
    print(f"❌ {message}")
    raise SystemExit(1)


def main() -> None:
    missing = [path for path in REQUIRED_FILES if not (ROOT / path).is_file()]
    if missing:
        fail("Missing Cloudflare deployment files: " + ", ".join(missing))

    package = json.loads((ROOT / "package.json").read_text())
    scripts = package.get("scripts", {})
    for script in ["build", "prod:check", "cloudflare:check", "runtime:guard"]:
        if script not in scripts:
            fail(f"package.json is missing npm script: {script}")

    wrangler = (ROOT / "wrangler.toml").read_text()
    if "pages_build_output_dir" not in wrangler or "dist" not in wrangler:
        fail('wrangler.toml must set pages_build_output_dir = "dist"')

    deployment_doc = (ROOT / "docs/deployment/CLOUDFLARE_DEPLOYMENT.md").read_text()
    if "Build command | `npm run build`" not in deployment_doc:
        fail(
            "Cloudflare deployment docs must pin the Pages build command to `npm run build`"
        )
    if "Build command | `npm build`" in deployment_doc:
        fail("Cloudflare Pages build command must not be documented as `npm build`")

    headers = (ROOT / "public/_headers").read_text()
    for header in [
        "Strict-Transport-Security",
        "X-Content-Type-Options",
        "Referrer-Policy",
    ]:
        if header not in headers:
            fail(f"public/_headers missing security header: {header}")

    redirects = (ROOT / "public/_redirects").read_text()
    for rule in ["/api/*", "/* /index.html 200"]:
        if rule not in redirects:
            fail(f"public/_redirects missing route rule: {rule}")

    edge_proxy = (ROOT / "functions/api/[[path]].ts").read_text()
    if "HYBA_BACKEND_URL" not in edge_proxy:
        fail("Cloudflare API proxy must read HYBA_BACKEND_URL")

    print("✅ Cloudflare deployment preflight passed")


if __name__ == "__main__":
    sys.exit(main())
