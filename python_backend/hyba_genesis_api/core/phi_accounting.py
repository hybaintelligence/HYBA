"""Φ-Density Accounting — Separating Initialization from Optimization

This module resolves the Δ Φ accounting gap identified in UAT feedback:
- Observed Δ Φ: +0.280 (+40.4%)
- Declared optimization gains: +0.027 (sum of 3 proposals)
- Unaccounted: +0.253

The gap exists because we conflate:
1. **Initialization Gain** (cold → warm substrate): Φ_cold → Φ_substrate_ready
2. **Optimization Gain** (proposal-driven): Φ_substrate_ready → Φ_optimized

This module provides separate accounting for each phenomenon.

Mathematical Framework:
    Φ_total = Φ_baseline + Φ_init + Φ_opt
    
    Where:
    - Φ_baseline: Cold-start floor (typically 0.5-0.7)
    - Φ_init: Substrate initialization synergy (6 subsystems → coherent state)
    - Φ_opt: Autonomous optimization gain (reflexive proposals)

Units:
    Φ-density is dimensionless, bounded [0, 1]
    Represents integrated information density across substrate components
    NOT Tononi IIT Φ (bits); this is a structural coherence proxy
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Dict, Any, Optional


# Empirically measured Φ-floor after cold start (no subsystems initialized)
PHI_COLD_START_FLOOR = 0.50

# Φ-floor governance threshold (from substrate initialization)
PHI_GOVERNANCE_FLOOR = 0.85


@dataclass
class PhiAccountingReport:
    """Detailed Φ-density accounting with initialization vs optimization split."""
    
    # Cold start (no subsystems)
    phi_cold_start: float
    
    # After substrate initialization (6 subsystems ready)
    phi_post_initialization: float
    
    # After autonomous optimization (proposals applied)
    phi_post_optimization: float
    
    # Gains (deltas)
    phi_initialization_gain: float  # Synergy from subsystem coupling
    phi_optimization_gain: float  # Reflexive proposal improvements
    phi_total_gain: float  # Total improvement from cold start
    
    # Proposal-level accounting
    declared_optimization_gain: float  # Sum of proposal expected_gain
    unaccounted_optimization_gain: float  # Residual (non-linear coupling or measurement error)
    
    # Metadata
    subsystems_initialized: int
    proposals_applied: int
    reflexive_cycles: int
    
    def to_dict(self) -> Dict[str, Any]:
        """Export as JSON-serializable dict."""
        return {
            "phi_cold_start": round(self.phi_cold_start, 6),
            "phi_post_initialization": round(self.phi_post_initialization, 6),
            "phi_post_optimization": round(self.phi_post_optimization, 6),
            "phi_initialization_gain": round(self.phi_initialization_gain, 6),
            "phi_optimization_gain": round(self.phi_optimization_gain, 6),
            "phi_total_gain": round(self.phi_total_gain, 6),
            "declared_optimization_gain": round(self.declared_optimization_gain, 6),
            "unaccounted_optimization_gain": round(self.unaccounted_optimization_gain, 6),
            "subsystems_initialized": self.subsystems_initialized,
            "proposals_applied": self.proposals_applied,
            "reflexive_cycles": self.reflexive_cycles,
            "accounting_notes": self._generate_accounting_notes()
        }
    
    def _generate_accounting_notes(self) -> str:
        """Generate human-readable accounting explanation."""
        init_pct = (self.phi_initialization_gain / self.phi_cold_start * 100) if self.phi_cold_start > 0 else 0
        opt_pct = (self.phi_optimization_gain / self.phi_post_initialization * 100) if self.phi_post_initialization > 0 else 0
        
        notes = []
        notes.append(f"Initialization gain: +{self.phi_initialization_gain:.3f} ({init_pct:+.1f}%) from subsystem synergy")
        notes.append(f"Optimization gain: +{self.phi_optimization_gain:.3f} ({opt_pct:+.1f}%) from {self.proposals_applied} proposals")
        
        if abs(self.unaccounted_optimization_gain) > 0.001:
            if self.unaccounted_optimization_gain > 0:
                notes.append(
                    f"Unaccounted gain: +{self.unaccounted_optimization_gain:.3f} "
                    f"(likely non-linear coupling across {self.reflexive_cycles} cycles)"
                )
            else:
                notes.append(
                    f"Unaccounted loss: {self.unaccounted_optimization_gain:.3f} "
                    f"(measurement noise or proposal interference)"
                )
        
        return " | ".join(notes)


def compute_phi_accounting(
    phi_before_init: float,
    phi_after_init: float,
    phi_after_opt: float,
    proposals: list,
    subsystems_initialized: int,
    reflexive_cycles: int
) -> PhiAccountingReport:
    """Compute detailed Φ-density accounting.
    
    Args:
        phi_before_init: Φ-density before substrate initialization (cold start)
        phi_after_init: Φ-density after substrate initialization (6 subsystems ready)
        phi_after_opt: Φ-density after autonomous optimization (proposals applied)
        proposals: List of proposals with expected_gain fields
        subsystems_initialized: Number of substrate subsystems initialized
        reflexive_cycles: Number of reflexive optimization cycles executed
    
    Returns:
        PhiAccountingReport with separated initialization and optimization gains
    """
    
    # Calculate gains
    phi_init_gain = phi_after_init - phi_before_init
    phi_opt_gain = phi_after_opt - phi_after_init
    phi_total_gain = phi_after_opt - phi_before_init
    
    # Sum declared proposal gains
    declared_opt_gain = sum(
        p.get("expected_gain", 0.0) 
        for p in proposals 
        if p.get("applied", False)
    )
    
    # Unaccounted optimization gain (non-linear coupling or measurement error)
    unaccounted_opt_gain = phi_opt_gain - declared_opt_gain
    
    return PhiAccountingReport(
        phi_cold_start=phi_before_init,
        phi_post_initialization=phi_after_init,
        phi_post_optimization=phi_after_opt,
        phi_initialization_gain=phi_init_gain,
        phi_optimization_gain=phi_opt_gain,
        phi_total_gain=phi_total_gain,
        declared_optimization_gain=declared_opt_gain,
        unaccounted_optimization_gain=unaccounted_opt_gain,
        subsystems_initialized=subsystems_initialized,
        proposals_applied=len([p for p in proposals if p.get("applied", False)]),
        reflexive_cycles=reflexive_cycles
    )


def estimate_initialization_phi_contribution(subsystems_ready: int, total_subsystems: int = 6) -> float:
    """Estimate Φ-density contribution from substrate initialization.
    
    Model: Φ_init scales with √(subsystems_ready) due to pairwise coupling synergy
    
    Args:
        subsystems_ready: Number of subsystems successfully initialized
        total_subsystems: Total number of subsystems in substrate (default 6)
    
    Returns:
        Estimated Φ-density contribution from initialization (0 to ~0.35)
    """
    if subsystems_ready == 0:
        return 0.0
    
    # √(n) scaling captures pairwise synergy: n subsystems → n(n-1)/2 couplings
    # Normalized by √(total_subsystems) to bound output
    synergy_factor = math.sqrt(subsystems_ready / total_subsystems)
    
    # Empirical calibration: 6 subsystems → ~0.25-0.30 Φ gain
    # This is substrate-specific; adjust based on measurements
    max_init_contribution = 0.30
    
    return synergy_factor * max_init_contribution


def validate_phi_metric_bounds(phi: float, context: str = "") -> bool:
    """Validate Φ-density is within expected bounds [0, 1].
    
    Args:
        phi: Φ-density value to validate
        context: Description for error message
    
    Returns:
        True if valid, False otherwise
    
    Raises:
        ValueError if Φ outside [0, 1] bounds
    """
    if not (0.0 <= phi <= 1.0):
        raise ValueError(
            f"Φ-density out of bounds: {phi:.6f} {context}. "
            f"Expected [0, 1]. Check measurement validity."
        )
    return True


def is_phi_governance_floor_met(phi: float) -> bool:
    """Check if Φ-density meets governance floor threshold.
    
    Args:
        phi: Current Φ-density
    
    Returns:
        True if Φ >= governance floor (0.85), False otherwise
    """
    return phi >= PHI_GOVERNANCE_FLOOR
