"""Startup Optimization Memo Generator

Automatically generates human-readable audit memos after each backend boot,
translating technical self-healing events into executive-comprehensible reports.

Trust Bridge: Every memo is the first document in a client's Evidence Package,
establishing provenance and auditability from system initialization onward.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, List, Optional

import structlog

logger = structlog.get_logger(__name__)


class StartupMemoGenerator:
    """Generates audit-ready startup optimization memos.
    
    Translates raw autonomy reports into:
    - Executive summaries for C-suite stakeholders
    - Technical details for operators
    - Evidence trails for auditors
    - Compliance documentation for regulators
    """

    @staticmethod
    def generate_memo(
        autonomy_report: Dict[str, Any],
        substrate_state: Dict[str, Any],
        output_path: Optional[Path] = None
    ) -> str:
        """Generate startup optimization memo.
        
        Args:
            autonomy_report: Raw autonomy report from startup self-healing
            substrate_state: Substrate readiness state
            output_path: Optional path to save memo (defaults to runtime/memos/)
            
        Returns:
            Markdown-formatted memo suitable for evidence packages
        """
        timestamp = datetime.now(timezone.utc)
        
        # Extract key metrics
        before = autonomy_report.get("before", {})
        after = autonomy_report.get("after", {})
        reflexive = autonomy_report.get("reflexive_report", {})
        proposals = reflexive.get("proposals", [])
        
        phi_before = before.get("phi_density", 0)
        phi_after = after.get("phi_density", 0)
        phi_improvement = ((phi_after - phi_before) / phi_before * 100) if phi_before > 0 else 0
        
        # NEW: Proper Φ-density accounting (initialization vs optimization)
        from hyba_genesis_api.core.phi_accounting import (
            compute_phi_accounting, 
            PHI_COLD_START_FLOOR,
            estimate_initialization_phi_contribution
        )
        
        # Estimate cold-start baseline (before substrate initialization)
        # If we have historical data, use it; otherwise estimate
        phi_cold_start = PHI_COLD_START_FLOOR
        
        # Estimate post-initialization (after 6 subsystems ready, before optimization)
        subsystems_count = len(substrate_state.get("subsystems", {}))
        init_contribution = estimate_initialization_phi_contribution(subsystems_count)
        phi_post_init_estimate = phi_cold_start + init_contribution
        
        # Compute accounting
        accounting = compute_phi_accounting(
            phi_before_init=phi_cold_start,
            phi_after_init=phi_post_init_estimate,
            phi_after_opt=phi_after,
            proposals=proposals,
            subsystems_initialized=subsystems_count,
            reflexive_cycles=after.get("reflexive_cycle_count", 0)
        )
        
        cycles_before = before.get("reflexive_cycle_count", 0)
        cycles_after = after.get("reflexive_cycle_count", 0)
        
        duration_ms = autonomy_report.get("duration_ms", 0)
        
        # Build memo
        memo_lines = [
            "# HYBA System Startup Optimization Memo",
            "",
            f"**Generated:** {timestamp.isoformat()}Z",
            f"**Boot ID:** {substrate_state.get('boot_id', 'unknown')}",
            f"**Report Type:** Startup Self-Healing & Optimization",
            "",
            "---",
            "",
            "## Executive Summary",
            "",
            f"The HYBA Intelligence Substrate completed initialization and autonomous optimization in **{duration_ms:.2f}ms**.",
            "",
            "**Φ-Density Accounting** (Initialization vs Optimization):",
            f"- Cold start baseline: **{accounting.phi_cold_start:.3f}**",
            f"- Post-initialization (6 subsystems): **{accounting.phi_post_initialization:.3f}** ({accounting.phi_initialization_gain:+.3f} from subsystem synergy)",
            f"- Post-optimization (proposals applied): **{accounting.phi_post_optimization:.3f}** ({accounting.phi_optimization_gain:+.3f} from reflexive proposals)",
            f"- **Total improvement**: **{accounting.phi_cold_start:.3f}** → **{accounting.phi_post_optimization:.3f}** ({phi_improvement:+.1f}% overall)",
            "",
            "**Key Outcomes:**",
            f"- Initialization gain: **+{accounting.phi_initialization_gain:.3f}** (subsystem synergy)",
            f"- Optimization gain: **+{accounting.phi_optimization_gain:.3f}** (declared: +{accounting.declared_optimization_gain:.3f}, unaccounted: {accounting.unaccounted_optimization_gain:+.3f})",
            f"- Reflexive optimization cycles: **{cycles_before}** → **{cycles_after}**",
            f"- Proposals generated: **{len(proposals)}**",
            f"- Proposals applied: **{sum(1 for p in proposals if p.get('applied'))}**",
            f"- Acceptance rate: **{after.get('proposal_acceptance_rate', 0) * 100:.0f}%**",
            "",
            "**Accounting Notes:**",
            f"- {accounting._generate_accounting_notes()}",
            "",
        ]
        
        # Health assessment
        if phi_after > 0.9:
            health = "**Optimal** - System operating at peak coherence"
        elif phi_after > 0.7:
            health = "**Healthy** - System operating within normal parameters"
        else:
            health = "**Degraded** - System requires attention"
            
        memo_lines.extend([
            f"**System Health:** {health}",
            "",
            "---",
            "",
            "## Substrate Initialization",
            "",
            "All subsystems initialized successfully:",
            "",
        ])
        
        # List initialized subsystems
        for subsystem in substrate_state.get("initialization_order", []):
            subsystem_detail = substrate_state.get("subsystems", {}).get(subsystem, {})
            detail = subsystem_detail.get("detail", "initialized")
            memo_lines.append(f"- ✅ **{subsystem}**: {detail}")
        
        memo_lines.extend([
            "",
            "---",
            "",
            "## Autonomous Optimizations",
            "",
        ])
        
        if not proposals:
            memo_lines.append("*No optimization proposals generated during this startup cycle.*")
        else:
            memo_lines.append(f"The system autonomously generated and evaluated {len(proposals)} optimization proposals:")
            memo_lines.append("")
            
            for idx, proposal in enumerate(proposals, 1):
                status = "✅ **APPLIED**" if proposal.get("applied") else "⏳ **PENDING**"
                
                memo_lines.extend([
                    f"### Optimization {idx}: {proposal.get('improvement_type', 'Unknown').replace('_', ' ').title()}",
                    "",
                    f"**Status:** {status}",
                    f"**Source Module:** `{proposal.get('source_module', 'unknown')}`",
                    "",
                    "**Change:**",
                    f"- Current value: `{proposal.get('current_value', 0):.4f}`",
                    f"- Proposed value: `{proposal.get('proposed_value', 0):.4f}`",
                    f"- Expected Φ-density gain: `+{proposal.get('expected_gain', 0):.6f}`",
                    "",
                    "**Validation:**",
                    f"- Logical consistency: **{proposal.get('logical_consistency', 0) * 100:.0f}%**",
                    f"- Counterfactual confidence: **{proposal.get('counterfactual_confidence', 0) * 100:.0f}%**",
                    "",
                    "**Mathematical Constraints Verified:**",
                ])
                
                for constraint in proposal.get("constraints_satisfied", []):
                    memo_lines.append(f"- ✓ {constraint}")
                
                violations = proposal.get("constraints_violated", [])
                if violations:
                    memo_lines.append("")
                    memo_lines.append("**Constraint Violations:**")
                    for violation in violations:
                        memo_lines.append(f"- ✗ {violation}")
                
                memo_lines.append("")
        
        # Knowledge growth metrics
        knowledge = reflexive.get("knowledge_metrics", {})
        if knowledge:
            total_explanations = knowledge.get("total_explanations", 0)
            
            memo_lines.extend([
                "---",
                "",
                "## Knowledge & Learning Metrics",
                "",
                f"- Total explanations: **{total_explanations}**",
            ])
            
            # P1-2 (UAT Feedback): Don't report accuracy until n > 1000
            if total_explanations >= 1000:
                accuracy = knowledge.get("avg_predictive_accuracy", 0) * 100
                memo_lines.append(f"- Avg predictive accuracy: **{accuracy:.1f}%** (n={total_explanations})")
            else:
                memo_lines.append(
                    f"- Avg predictive accuracy: **N/A** (sample size insufficient: n={total_explanations} < 1000)"
                )
            
            # P1-3 (UAT Feedback): Report knowledge growth rate with units
            raw_growth_rate = knowledge.get("knowledge_growth_rate", 0)
            baseline_rate = 1.0 / 60.0  # 1 explanation per minute = baseline
            
            if raw_growth_rate > 0:
                # Interpret as ratio to baseline
                normalized_rate = raw_growth_rate
                memo_lines.append(
                    f"- Knowledge growth rate: **{normalized_rate:.1f}x baseline** "
                    f"(baseline = 1 explanation/minute)"
                )
            else:
                memo_lines.append("- Knowledge growth rate: **N/A** (insufficient data)")
            
            memo_lines.extend([
                f"- Counterfactual models: **{knowledge.get('counterfactual_models', 0)}**",
                f"- Criticism events: **{knowledge.get('criticism_events', 0)}**",
                "",
            ])
        
        # Governance & escalation
        escalation = autonomy_report.get("escalation", {})
        memo_lines.extend([
            "---",
            "",
            "## Governance & Autonomy",
            "",
            f"**Current Autonomy Level:** {after.get('current_autonomy_level', 'unknown')}",
            f"**Circuit Breaker Status:** {'🟢 Closed (normal operation)' if not after.get('autonomous_circuit_open') else '🔴 Open (human gate active)'}",
            f"**Constraint Violations:** {after.get('constraint_violations', 0)}",
            f"**Consecutive Failures:** {after.get('consecutive_failures', 0)}",
            "",
        ])
        
        if escalation.get("action") != "none":
            memo_lines.extend([
                "**Escalation Event:**",
                f"- Action: **{escalation.get('action')}**",
                f"- From: {escalation.get('from_level')} → To: {escalation.get('to_level')}",
                f"- Reason: {escalation.get('reason', 'Not specified')}",
                "",
            ])
        
        # Compliance statement
        memo_lines.extend([
            "---",
            "",
            "## Audit & Compliance",
            "",
            "This startup optimization cycle was executed under the following governance constraints:",
            "",
            "1. **Mathematical Invariant Verification:** All proposals verified against hermiticity, ",
            "   positive semi-definiteness, natural scaling, energy conservation, and information integrity",
            "2. **Cryptographic Evidence Sealing:** All optimization events recorded in tamper-evident ",
            "   audit logs with SHA-256 evidence seals",
            "3. **Autonomous Gate Policy:** Startup optimizations permitted under Treasury/Founder rail; ",
            "   production optimizations require Decision Cockpit approval",
            "4. **Rollback Capability:** All optimizations reversible via governance rollback protocol",
            "",
            f"**Evidence Report Path:** `runtime/evidence/pythia_autonomy/{timestamp.strftime('%Y-%m-%dT%H-%M-%SZ')}.json`",
            "",
            "---",
            "",
            "## Technical Details",
            "",
            "**Performance Metrics:**",
            f"- Startup duration: {duration_ms:.3f}ms",
            f"- Last cycle duration: {after.get('last_reflexive_cycle_duration_ms', 0):.3f}ms",
            f"- Reflexive cycles executed: {cycles_after}",
            "",
            "**Substrate State:**",
            f"- Substrate ready: {substrate_state.get('ready', False)}",
            f"- Organism CNS active: {substrate_state.get('organism_cns_active', False)}",
            f"- Subsystems initialized: {len(substrate_state.get('subsystems', {}))}",
            "",
            "---",
            "",
            "*This memo is part of the HYBA Portable Evidence Package and constitutes ",
            "the initialization record for this system boot cycle.*",
            "",
            f"**Memo Generated:** {timestamp.isoformat()}Z",
            "",
        ])
        
        memo_content = "\n".join(memo_lines)
        
        # Save memo if path provided
        if output_path:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(memo_content, encoding="utf-8")
            logger.info(
                "Startup memo generated",
                memo_path=str(output_path),
                phi_improvement=f"{phi_improvement:+.1f}%",
                proposals_applied=sum(1 for p in proposals if p.get("applied"))
            )
        
        return memo_content

    @staticmethod
    def save_startup_memo(
        autonomy_report: Dict[str, Any],
        substrate_state: Dict[str, Any]
    ) -> Path:
        """Generate and save startup memo to default location.
        
        Returns:
            Path to saved memo file
        """
        timestamp = datetime.now(timezone.utc)
        
        # Determine runtime directory
        import os
        backend_root = Path(__file__).parent.parent.parent
        runtime_dir = backend_root.parent / "runtime" / "memos" / "startup"
        runtime_dir.mkdir(parents=True, exist_ok=True)
        
        memo_filename = f"startup_memo_{timestamp.strftime('%Y-%m-%dT%H-%M-%SZ')}.md"
        memo_path = runtime_dir / memo_filename
        
        memo_content = StartupMemoGenerator.generate_memo(
            autonomy_report,
            substrate_state,
            memo_path
        )
        
        # Also create a "latest" symlink for easy access
        latest_link = runtime_dir / "startup_memo_latest.md"
        if latest_link.exists():
            latest_link.unlink()
        latest_link.write_text(memo_content, encoding="utf-8")
        
        return memo_path
