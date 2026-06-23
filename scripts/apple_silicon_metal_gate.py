#!/usr/bin/env python3
"""Generate an Apple Silicon MLX/Metal acceleration evidence packet."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from pythia_mining.apple_silicon_metal import probe_mlx_metal


ARTIFACT_DIR = Path("artifacts/apple_silicon_metal")
PACKET_PATH = ARTIFACT_DIR / "apple_silicon_metal_packet.json"
MANIFEST_PATH = ARTIFACT_DIR / "apple_silicon_metal_manifest.json"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--matrix-size", type=int, default=64)
    parser.add_argument(
        "--require-mlx",
        action="store_true",
        help="Exit non-zero when MLX/Metal is unavailable. Use on a Mac M3 evidence session.",
    )
    args = parser.parse_args()

    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    packet = probe_mlx_metal(matrix_size=args.matrix_size, require_mlx=args.require_mlx)
    PACKET_PATH.write_text(
        json.dumps(packet, indent=2, sort_keys=True), encoding="utf-8"
    )

    manifest = {
        "schema_version": "2026-06-15.apple-silicon-metal.manifest.v1",
        "packet_path": str(PACKET_PATH),
        "packet_sha256": packet["forensic_sha256"],
        "status": packet["status"],
        "apple_silicon_detected": packet["apple_silicon_detected"],
        "mlx_available": packet["mlx_available"],
        "metal_path_verified": packet["metal_path_verified"],
        "cpu_fallback_verified": packet["cpu_fallback_verified"],
        "production_boundary": {
            "changes_production_runtime": False,
            "changes_funding_gate": False,
            "changes_pool_semantics": False,
            "optional_local_acceleration_gate": True,
        },
    }
    MANIFEST_PATH.write_text(
        json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8"
    )
    print(json.dumps(manifest, indent=2, sort_keys=True))

    if args.require_mlx and packet["status"] != "verified":
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
