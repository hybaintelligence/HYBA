#!/usr/bin/env python3
"""Generate a QuantumRuntimeManifest for CI/CD build artifacts.

Default mode is dependency-free and uses façade-shaped build stubs so locked-down
CI can always produce a compliance manifest. Pass `--production-runtime` to bind
against the real PULVINI façade when the numerical backend dependencies are
available.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
PYTHON_BACKEND = ROOT / "python_backend"
if str(PYTHON_BACKEND) not in sys.path:
    sys.path.insert(0, str(PYTHON_BACKEND))

from pythia_mining.pulvini_elevation import (
    CertificateLedger,
    QuantumRuntimeManifestBuilder,
)  # noqa: E402


class BuildOperator:
    VERSION = "BUILD_OPERATOR_STUB_V1"
    dim = 1

    def verify_topology(self) -> dict[str, Any]:
        return {"gate_closed": True, "operator_version": self.VERSION}

    def snapshot(self) -> dict[str, Any]:
        return {"version": self.VERSION, "topology_gate_closed": True}


class BuildVerifier:
    VERSION = "BUILD_VERIFIER_STUB_V1"

    def __init__(self, operator: BuildOperator) -> None:
        self.operator = operator

    def verify_topology(self) -> bool:
        return True


def build_manifest(*, production_runtime: bool) -> dict[str, Any]:
    ledger = CertificateLedger()
    ledger.append("ci_manifest_generation", {"production_runtime": production_runtime})
    if production_runtime:
        builder = QuantumRuntimeManifestBuilder()
        return builder.build(ledger=ledger)
    operator = BuildOperator()
    builder = QuantumRuntimeManifestBuilder(operator, BuildVerifier(operator))
    return builder.build(
        ledger=ledger, rho={"trace": 1.0, "purity": 1.0, "min_eigenvalue": 0.0}
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Generate PULVINI manifest.json for CI/CD."
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("manifest.json"),
        help="Output manifest path.",
    )
    parser.add_argument(
        "--production-runtime",
        action="store_true",
        help="Use the real PULVINI façade instead of dependency-free build stubs.",
    )
    args = parser.parse_args(argv)
    manifest = build_manifest(production_runtime=args.production_runtime)
    args.output.write_text(
        json.dumps(manifest, sort_keys=True, indent=2), encoding="utf-8"
    )
    print(args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
