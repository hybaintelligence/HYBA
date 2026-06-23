#!/usr/bin/env python3
"""Dependency-free verifier for PULVINI certificate-ledger exports.

The auditor intentionally imports only the elevation control plane. It does not
require NumPy, GPUs, mining clients, or research-runtime modules. Given a binary
`CertificateLedger.to_bytes()` export, it verifies the hash chain, inspects
runtime-passport-like ledger payloads, and emits a regulator-readable JSON
pass/fail report.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Mapping

ROOT = Path(__file__).resolve().parents[1]
PYTHON_BACKEND = ROOT / "python_backend"
if str(PYTHON_BACKEND) not in sys.path:
    sys.path.insert(0, str(PYTHON_BACKEND))

from pythia_mining.pulvini_elevation import (
    CertificateLedger,
    ConsensusLedger,
)  # noqa: E402


def verify_ledger(path: Path) -> dict[str, Any]:
    ledger = CertificateLedger.from_bytes(path.read_bytes())
    chain_verified = ledger.verify_chain()
    passport_checks = [
        _inspect_passport_entry(entry.to_dict()) for entry in ledger.entries
    ]
    invariant_violations = [
        entry
        for entry in ledger.entries
        if entry.certificate_type == "mathematical_exception"
    ]
    autonomic_repairs = [
        entry
        for entry in ledger.entries
        if entry.certificate_type == "autonomic_repair"
    ]
    failed_passports = [
        check for check in passport_checks if check["checked"] and not check["verified"]
    ]
    passed = bool(chain_verified and not failed_passports and not invariant_violations)
    return {
        "passed": passed,
        "chain_verified": chain_verified,
        "root_hash": ledger.root_hash,
        "entry_count": len(ledger.entries),
        "passport_checks": passport_checks,
        "failed_passport_count": len(failed_passports),
        "mathematical_exception_count": len(invariant_violations),
        "autonomic_repair_count": len(autonomic_repairs),
    }


def _inspect_passport_entry(entry: Mapping[str, Any]) -> dict[str, Any]:
    payload = entry.get("payload", {})
    if not isinstance(payload, Mapping):
        return {
            "entry_index": entry.get("index"),
            "checked": False,
            "verified": False,
            "reason": "payload_not_mapping",
        }
    candidate = payload.get("passport", payload)
    if not isinstance(candidate, Mapping) or "kernel_invariants_met" not in candidate:
        return {
            "entry_index": entry.get("index"),
            "checked": False,
            "verified": True,
            "reason": "not_runtime_passport",
        }
    verified = bool(
        candidate.get("kernel_invariants_met") and candidate.get("ledger_entry_hash")
    )
    return {
        "entry_index": entry.get("index"),
        "checked": True,
        "verified": verified,
        "module_id": candidate.get("module_id"),
        "ledger_entry_hash": candidate.get("ledger_entry_hash"),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Verify one or more PULVINI CertificateLedger exports."
    )
    parser.add_argument(
        "ledger",
        nargs="+",
        type=Path,
        help="Path(s) to CertificateLedger binary exports produced by to_bytes().",
    )
    parser.add_argument("--json", action="store_true", help="Emit compact JSON only.")
    args = parser.parse_args(argv)
    reports = [verify_ledger(path) for path in args.ledger]
    if len(reports) == 1:
        report = reports[0]
    else:
        ledgers = [
            CertificateLedger.from_bytes(path.read_bytes()) for path in args.ledger
        ]
        consensus = ConsensusLedger(ledgers).report().to_dict()
        report = {
            "passed": bool(
                consensus["passed"] and all(item["passed"] for item in reports)
            ),
            "node_reports": reports,
            "consensus": consensus,
        }
    if args.json:
        print(json.dumps(report, sort_keys=True, separators=(",", ":")))
    else:
        print(json.dumps(report, sort_keys=True, indent=2))
    return 0 if report["passed"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
