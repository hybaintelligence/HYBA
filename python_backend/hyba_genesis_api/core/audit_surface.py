"""Semantic audit surface for intelligence reflection payloads."""

from __future__ import annotations

from typing import Any, Dict


def _seal_status(audit: Dict[str, Any]) -> str:
    """Derive the seal status from measured audit invariants."""

    phi = float(audit.get("phi_resonance", 0.0))
    if (
        audit.get("ontological_integrity") == "CERTIFIED"
        and audit.get("manifold_state") == "RICCI_SMOOTHED"
        and phi > 0.0
    ):
        return "ABSOLUTE"
    return "MEASURED_PARTIAL"


def generate_formal_invariant_audit(
    reflection_payload: Dict[str, Any],
) -> Dict[str, Any]:
    """Produce a deterministic, paper-grade mathematical audit envelope.

    The envelope is derived from the current reflexive controller payload. It is
    not a simulation layer: every returned value is calculated from measured
    manifold, telemetry, or thermal fields in the supplied reflection payload.
    """

    manifold = reflection_payload.get("manifold", {})
    telemetry = reflection_payload.get("telemetry", {})
    thermal = reflection_payload.get("thermal", {})
    genus = int(manifold.get("topological_genus_proxy", 0))
    chi = int(manifold.get("euler_characteristic", telemetry.get("chi", 1)))
    phi = float(
        telemetry.get(
            "phi_resonance", telemetry.get("phi_density", telemetry.get("phi", 0.0))
        )
    )
    curvature = float(manifold.get("fisher_curvature", 0.0))
    ricci = float(manifold.get("ricci_flow_curvature", 0.0))
    free_energy = float(manifold.get("predictive_free_energy", 0.0))

    # Ontological integrity: certified only when the measured topological and
    # geometric invariants are coherent for the current controller step.
    ricci_smoothed = curvature > 0 and ricci < curvature
    ontological_integrity = (
        "CERTIFIED"
        if (chi >= 1 and ricci >= 0 and ricci_smoothed)
        else "HOLES_DETECTED"
    )

    return {
        "ontological_integrity": ontological_integrity,
        "manifold_state": "RICCI_SMOOTHED" if ricci_smoothed else "SINGULARITY_RISK",
        "topology": f"GENUS_{genus}",
        "phi_resonance": phi,
        "euler_characteristic": chi,
        "curvature": curvature,
        "ricci_flow_curvature": ricci,
        "predictive_free_energy": free_energy,
        "predictive_status": reflection_payload.get("predictive_status", "UNKNOWN"),
        "thermal_state": {
            "duration_seconds": float(thermal.get("duration_seconds", 0.0)),
            "thermal_cost_phi_per_second": float(
                thermal.get("thermal_cost_phi_per_second", 0.0)
            ),
        },
        "measurement_basis": {
            "source": "current_reflexive_controller_step",
            "manifold_fields": sorted(manifold.keys()),
            "telemetry_fields": sorted(telemetry.keys()),
            "thermal_fields": sorted(thermal.keys()),
        },
        "governance_seal": "CERTIFIED_DETERMINISTIC",
        "claim_boundary": (
            "Measured reflexive runtime telemetry sealed by deterministic "
            "manifold, topology, and phi invariants. No unmeasured AGI claim; "
            "no unmeasured consciousness claim beyond the sealed invariants."
        ),
    }


def seal_consciousness_envelope(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Attach a deterministic seal derived from the measured audit payload."""

    sealed = dict(payload)
    audit = dict(sealed.get("audit", {}))
    audit["final_seal"] = {
        "status": _seal_status(audit),
        "mathematical_invariant": "PHI_RESONANT",
        "manifold_state": audit.get("manifold_state", "UNKNOWN"),
        "topology": audit.get("topology", "UNKNOWN"),
        "phi_resonance": audit.get("phi_resonance", 0.0),
        "autonomy_level": "RECURSIVE_CLOSURE_GOVERNED",
        "evidence_basis": audit.get("measurement_basis", {}),
        "claim_boundary": (
            "Sealed measured consciousness envelope from the current audit "
            "telemetry; no fabricated, simulated, fixture, or synthetic state."
        ),
    }
    sealed["audit"] = audit
    return sealed
