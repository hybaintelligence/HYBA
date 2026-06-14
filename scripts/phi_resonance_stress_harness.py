#!/usr/bin/env python3
"""Dependency-free φ-resonance stress harness for PULVINI elevation.

Sweeps φ exponents, injects deterministic geometric discontinuities, measures
stability decay, and emits a compact resonance envelope that can be committed to
audit evidence without raw workload data.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "python_backend"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from pythia_mining.pulvini_elevation import (  # noqa: E402
    PHI,
    CertificateLedger,
    PhiInvariantKernelScheduler,
    PhiScalingContract,
    PhiStabilityDiagnostic,
    PhiTopologyLedgerCompressor,
    QuantumRuntimePassport,
)


def _window_for_exponent(exponent: int, *, discontinuity: bool) -> list[float]:
    start = max(0, exponent - 3)
    values = [PHI**n for n in range(start, start + 5)]
    if discontinuity:
        values[2] *= 3.0
    return values


def run_harness(exponents: list[int], *, inject_every: int = 3) -> dict[str, Any]:
    contract = PhiScalingContract()
    diagnostic = PhiStabilityDiagnostic(tolerance=0.05)
    scheduler = PhiInvariantKernelScheduler()
    ledger = CertificateLedger()
    envelope: list[dict[str, Any]] = []

    for index, exponent in enumerate(exponents):
        inject = inject_every > 0 and index % inject_every == inject_every - 1
        tier = contract.tier(exponent)
        report = diagnostic.evaluate(
            _window_for_exponent(exponent, discontinuity=inject)
        )
        certificate_type = (
            "phi_scaling_invariant" if report.stable else "phi_scaling_violation"
        )
        entry = ledger.append(
            certificate_type,
            {"tier": tier, "stability": report.to_dict()},
            timestamp_ns=exponent,
        )
        passport = QuantumRuntimePassport(
            module_id="phi_resonance_stress_harness",
            phi_value_fixed=0,
            bures_score_fixed=0,
            kernel_invariants_met=report.stable,
            ledger_entry_hash=entry.entry_hash,
            phi_exponent=exponent,
            phi_scale_factor_fixed=int(
                min(1_000_000_000, round(tier["phi_exponent"] / 120 * 1_000_000_000))
            ),
        )
        decision = scheduler.route(passport, report)
        envelope.append(
            {
                "phi_exponent": exponent,
                "tier_label": tier["label"],
                "discontinuity_injected": inject,
                "stable": report.stable,
                "stability_error": report.phi_ratio_error,
                "scheduler_route": decision.route,
                "ledger_entry_hash": entry.entry_hash,
            }
        )

    proof = PhiTopologyLedgerCompressor().compress(ledger)
    return {
        "version": "PULVINI_PHI_RESONANCE_STRESS_V1",
        "exponents": exponents,
        "inject_every": inject_every,
        "resonance_envelope": envelope,
        "ledger_root_hash": ledger.root_hash,
        "phi_topology_compression": proof.to_dict(),
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run PULVINI φ-resonance stress harness"
    )
    parser.add_argument("--exponents", default="7,10,12,15,18,20,31,76")
    parser.add_argument("--inject-every", type=int, default=3)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    exponents = [
        int(item.strip()) for item in args.exponents.split(",") if item.strip()
    ]
    result = run_harness(exponents, inject_every=args.inject_every)
    payload = json.dumps(result, sort_keys=True, indent=2)
    if args.output:
        args.output.write_text(payload + "\n", encoding="utf-8")
    else:
        print(payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
