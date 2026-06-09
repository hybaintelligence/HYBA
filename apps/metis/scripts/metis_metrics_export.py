#!/usr/bin/env python3
"""
metis_metrics_export.py
HYBA Metis - Metrics Export
Extracts standardized metrics from a benchmark evidence artifact
and exports them in the Metis Metrics Standard format.

Computational Intelligence as a Service (CIaaS)
"""

import sys
import os
import json
import hashlib
import argparse
from datetime import datetime, timezone


METRICS_STANDARD_VERSION = "1.0.0"
ALLOWED_CLAIMS = [
    "metis_uses_versioned_benchmark",
    "metis_records_reproducible_evidence",
    "metis_separates_observed_from_sla",
    "metis_exposes_allowed_blocked_claims",
    "metis_uses_training_readiness_gate",
    "metis_reports_observed_quantum_metrics",
    "metis_does_not_claim_quantum_advantage",
    "metis_is_substrate_independent",
    "metis_uses_pure_mathematical_computation"
]

BLOCKED_CLAIMS = [
    "metis_has_proven_quantum_advantage",
    "metis_is_certified_quantum_compliant",
    "metis_guarantees_quantum_speedup",
    "metis_never_needs_retraining",
    "metis_self_certifies_regulatory_compliance",
    "metis_guarantees_autonomous_retraining",
    "metis_five_nines_reliability",
    "metis_independently_certified"
]


def extract_quantum_path_metrics(data: dict) -> dict:
    """
    Extract quantum-path metrics from benchmark data.
    
    Reports observed latency, energy, finite-output, compression, and retained-kernel.
    Does NOT claim quantum advantage.
    """
    benchmarks = data.get("benchmarks", [])
    
    if not benchmarks:
        return {
            "note": "No benchmark data available",
            "metrics": {}
        }
    
    # Aggregate solver metrics
    solver_times = [b["solver"]["computation_time_s"] for b in benchmarks if "solver" in b]
    entropies = [b["solver"]["entropy"] for b in benchmarks if "solver" in b]
    nonces = [b["solver"].get("nonce") for b in benchmarks if "solver" in b]
    
    # Aggregate Yang-Mills mass gaps
    mass_gaps = [b["yang_mills"]["mass_gap"] for b in benchmarks if "yang_mills" in b]
    spectral_ratios = [b["yang_mills"]["spectral_gap_ratio"] for b in benchmarks if "yang_mills" in b]
    
    # Aggregate Pulvini metrics
    pulvini_results = [b["pulvini"]["pulvini_result"] for b in benchmarks if "pulvini" in b]
    pulvini_times = [b["pulvini"]["computation_time_s"] for b in benchmarks if "pulvini" in b]
    
    # Extract quantum advantage metrics
    advantage_metrics = []
    for b in benchmarks:
        if "quantum_advantage" in b:
            qa = b["quantum_advantage"]
            advantage_metrics.append({
                "latency_ms": qa.get("latency_ms"),
                "phi_energy": qa.get("phi_energy"),
                "finite_output": qa.get("finite_output", {}),
                "compression": qa.get("compression", {}),
                "retained_kernel": qa.get("retained_kernel", {})
            })
    
    return {
        "total_benchmarks": len(benchmarks),
        "quantum_path": "yang-mills-pulvini-pythagoras",
        "solver": {
            "average_computation_time_s": round(sum(solver_times) / len(solver_times), 6) if solver_times else None,
            "average_entropy": round(sum(entropies) / len(entropies), 6) if entropies else None,
            "entropy_range": {
                "min": round(min(entropies), 6) if entropies else None,
                "max": round(max(entropies), 6) if entropies else None
            },
            "nonces": [n for n in nonces if n is not None]
        },
        "yang_mills": {
            "average_mass_gap": round(sum(mass_gaps) / len(mass_gaps), 8) if mass_gaps else None,
            "average_spectral_gap_ratio": round(sum(spectral_ratios) / len(spectral_ratios), 8) if spectral_ratios else None,
            "mass_gap_range": {
                "min": round(min(mass_gaps), 8) if mass_gaps else None,
                "max": round(max(mass_gaps), 8) if mass_gaps else None
            }
        },
        "pulvini": {
            "average_computation_time_s": round(sum(pulvini_times) / len(pulvini_times), 6) if pulvini_times else None,
            "metric_compression": pulvini_results[0].get("metric_compression") if pulvini_results else None,
            "status": pulvini_results[0].get("status") if pulvini_results else None
        },
        "quantum_advantage_metrics": {
            "average_latency_ms": round(
                sum(m["latency_ms"] for m in advantage_metrics if m["latency_ms"] is not None) / len(advantage_metrics), 
                6
            ) if advantage_metrics else None,
            "average_phi_energy": round(
                sum(m["phi_energy"] for m in advantage_metrics if m["phi_energy"] is not None) / len(advantage_metrics),
                8
            ) if advantage_metrics else None,
            "finite_output_verified": all(
                m["finite_output"].get("finite", False) for m in advantage_metrics
            ) if advantage_metrics else None,
            "deterministic": all(
                m["finite_output"].get("deterministic", False) for m in advantage_metrics
            ) if advantage_metrics else None,
            "compression_method": advantage_metrics[0]["compression"].get("method") if advantage_metrics else None,
            "compression_ratio": advantage_metrics[0]["compression"].get("ratio") if advantage_metrics else None
        },
        "note": "Observed quantum-path metrics. No quantum advantage claim is made."
    }


def generate_allowed_claims() -> dict:
    """Generate the list of allowed and blocked claims."""
    return {
        "allowed_claims": [
            {
                "id": claim,
                "label": claim.replace("_", " ").replace("metis", "Metis").title(),
                "evidence_required": True,
                "evidence_status": "supported"
            }
            for claim in ALLOWED_CLAIMS
        ],
        "blocked_claims": [
            {
                "id": claim,
                "label": claim.replace("_", " ").replace("metis", "Metis").title(),
                "reason": "Requires additional evidence, contractual support, or external certification",
                "evidence_status": "insufficient"
            }
            for claim in BLOCKED_CLAIMS
        ],
        "note": "Allowed claims are supported by the evidence architecture. "
                "Blocked claims require additional evidence or contractual support."
    }


def main():
    parser = argparse.ArgumentParser(description="Metis Metrics Export")
    parser.add_argument("input", type=str, help="Path to benchmark JSON file")
    parser.add_argument("--output", type=str, required=True,
                        help="Output file path for metrics standard report")
    
    args = parser.parse_args()
    
    print("[METIS] Metrics Export")
    print(f"[METIS] Reading: {args.input}")
    
    with open(args.input, 'r') as f:
        data = json.load(f)
    
    # Extract quantum-path metrics
    print("[METIS] Extracting quantum-path metrics...")
    quantum_metrics = extract_quantum_path_metrics(data)
    
    # Generate allowed/blocked claims
    print("[METIS] Generating allowed/blocked claims...")
    claims = generate_allowed_claims()
    
    # Gather environment info
    print("[METIS] Gathering environment metadata...")
    
    # Build output
    output = {
        "metis_metrics_standard_version": METRICS_STANDARD_VERSION,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "source_file": args.input,
        "source_fingerprint": hashlib.sha256(
            json.dumps(data, sort_keys=True, default=str).encode()
        ).hexdigest(),
        "quantum_path_metrics": quantum_metrics,
        "claims_governance": claims,
        "substrate": data.get("substrate", "unknown"),
        "hardware_independent": data.get("hardware_independent", False),
        "evidence_gates": {
            "five_nines_reliability": {
                "observed": False,
                "wilson_bound_satisfied": False,
                "requires_exact_fingerprint": True,
                "note": "Five-nines reliability requires exact report fingerprint, "
                        "command, environment, thresholds, and approved claim language"
            },
            "quantum_advantage": {
                "observed": False,
                "requires_controlled_environment": True,
                "note": "Quantum advantage requires repeated environment-controlled "
                        "evidence and approved thresholds"
            },
            "regulatory_compliance": {
                "observed": False,
                "requires_deployment_context": True,
                "note": "Regulatory compliance requires customer deployment context, "
                        "controller/processor analysis, and use-case classification"
            },
            "sla_commitment": {
                "observed": False,
                "requires_signed_agreement": True,
                "note": "SLA commitments require signed agreement expressly incorporating "
                        "the exact report fingerprint, command, environment, thresholds, "
                        "and approved claim language"
            }
        },
        "note": "This report separates observed benchmark evidence from SLA commitments. "
                "No unsubstantiated claims are made."
    }
    
    # Generate fingerprint
    content = json.dumps(output, sort_keys=True, default=str)
    fingerprint = hashlib.sha256(content.encode()).hexdigest()
    output["fingerprint"] = fingerprint
    
    # Write output
    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    with open(args.output, 'w') as f:
        json.dump(output, f, indent=2)
    
    print(f"[METIS] Metrics standard report written to: {args.output}")
    print(f"[METIS] Report fingerprint (SHA-256): {fingerprint}")
    print(f"[METIS] Allowed claims: {len(ALLOWED_CLAIMS)}")
    print(f"[METIS] Blocked claims: {len(BLOCKED_CLAIMS)}")
    
    return output


if __name__ == "__main__":
    main()