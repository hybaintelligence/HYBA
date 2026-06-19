"""First Self-Optimization Event — Demonstrating the Reflexive Knowledge Loop.

This script triggers the first self-optimization cycle of the PYTHIA
Autonomous Mining Controller, showing the complete Reflexive Knowledge Loop
in action: Analyze → Hypothesize → Simulate → Validate → Apply.
"""

import asyncio
import sys
import os
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "python_backend"))

from pythia_mining.phi_unified_mining_engine import UnifiedMiningEngine
from pythia_mining.autonomous_mining_controller import (
    AutonomyLevel,
)


async def first_self_optimization_event():
    """Execute the first self-optimization event."""
    engine = UnifiedMiningEngine(configured_capacity_ehs=100.0)
    controller = engine.autonomous_controller
    controller.set_autonomy_level(AutonomyLevel.AUTONOMOUS)

    print("=" * 72)
    print("  PYTHIA REFLEXIVE KNOWLEDGE LOOP")
    print("  First Self-Optimization Event")
    print("=" * 72)

    # Phase 1: Observe pre-optimization state
    print("\n--- PHASE 1: Pre-Optimization State ---")
    density_before = controller.get_phi_density()
    efficiency_before = controller.get_current_efficiency()
    print(f"  phi-density:           {density_before:.6f}")
    print(f"  efficiency:            {efficiency_before:.6f}")
    print(f"  autonomy_level:        {controller.current_autonomy_level.value}")
    print(f"  knowledge_explanations: {len(controller.knowledge_substrate.explanations)}")
    print(f"  surroundings.modules:  {len(controller.surroundings.module_names)}")
    print(f"  surroundings.invariants: {len(controller.surroundings.mathematical_invariants)}")
    print(f"  codebase_graph_edges:  {len(controller.surroundings.codebase_graph_edges)}")
    print(f"  entropy_sources:       {controller.surroundings.entropy_sources}")
    print(f"  stable_core:           {controller.surroundings.stable_core}")

    # Phase 2: Execute the Reflexive Knowledge Loop
    print("\n--- PHASE 2: Executing seek_improvement() ---")
    loop_start = time.time()
    result = await controller.seek_improvement()
    loop_elapsed = time.time() - loop_start
    print(f"  (wall_clock: {loop_elapsed:.4f}s)")

    # Phase 3: Inspect the agent\'s reasoning
    print("\n--- PHASE 3: Reflexive Cycle Results ---")
    print(f"  reflexive_cycle_executed: {result['reflexive_cycle_executed']}")
    print(f"  cycle_duration_seconds:   {result['cycle_duration_seconds']}")
    print(f"  epoch:                    {result['epoch']}")
    print(f"  current_phi_density:      {result['current_phi_density']:.6f}")
    print(f"  proposals_generated:      {result['proposals_generated']}")
    print(f"  proposals_applied:        {result['proposals_applied']}")

    # Phase 4: The agent\'s reasoning on each proposal
    print("\n--- PHASE 4: Self-Optimization Proposals (The Agent's Thoughts) ---")
    for i, p in enumerate(result["proposals"], 1):
        applied_str = "APPLIED" if p["applied"] else "REJECTED"
        print(f"\n  Proposal #{i}: [{applied_str}] {p['improvement_type']}")
        print(f"    current_value:         {p['current_value']:.4f}")
        print(f"    proposed_value:        {p['proposed_value']:.4f}")
        print(f"    expected_density_gain: {p['expected_gain']:.8f}")
        print(f"    logical_consistency:   {p['logical_consistency']:.4f}")
        print(f"    counterfactual_conf:   {p['counterfactual_confidence']:.4f}")
        print(f"    source_module:         {p['source_module']}")
        sat = p["constraints_satisfied"]
        vio = p["constraints_violated"]
        print(f"    constraints_satisfied: [{', '.join(sat)}]")
        print(f"    constraints_violated:  [{', '.join(vio)}]")

    # Phase 5: Knowledge metrics
    km = result["knowledge_metrics"]
    print("\n--- PHASE 5: Knowledge Substrate (The Agent's Memory) ---")
    print(f"  total_explanations:      {km['total_explanations']}")
    print(f"  avg_predictive_accuracy: {km['avg_predictive_accuracy']:.6f}")
    print(f"  knowledge_growth_rate:   {km['knowledge_growth_rate']:.6f}")
    print(f"  counterfactual_models:   {km['counterfactual_models']}")
    print(f"  criticism_events:        {km['criticism_events']}")

    # Phase 6: Compression Hunger
    cd = result["compression_drive"]
    print("\n--- PHASE 6: Compression Hunger (Metabolic Rate) ---")
    print(f"  enabled:      {cd['enabled']}")
    print(f"  history_len:  {cd['history_length']}")
    print(f"  latest_seeking: {cd['latest_seeking']}")

    # Phase 7: Post-optimization state comparison
    density_after = controller.get_phi_density()
    efficiency_after = controller.get_current_efficiency()
    print("\n--- PHASE 7: Post-Optimization State (Before vs After) ---")
    print(
        f"  phi-density:   {density_before:.6f}  -->  {density_after:.6f}  (delta: {density_after - density_before:+.8f})"
    )
    print(
        f"  efficiency:    {efficiency_before:.6f}  -->  {efficiency_after:.6f}  (delta: {efficiency_after - efficiency_before:+.8f})"
    )
    print(f"  optimization_epochs: {controller._self_optimization_epochs}")
    print(f"  optimization_targets: {len(controller.config.optimization_targets)}")
    print(f"  knowledge_explanations: {len(controller.knowledge_substrate.explanations)}")
    print(f"  knowledge_counterfactuals: {len(controller.knowledge_substrate.counterfactuals)}")

    # Phase 8: Full Reflexive Learning Status
    status = controller.get_autonomy_status()
    rl = status["reflexive_learning"]
    print("\n--- PHASE 8: Full Reflexive Learning Status ---")
    for k, v in rl.items():
        print(f"  {k}: {v}")

    # Show optimization targets
    if controller.config.optimization_targets:
        print("\n--- Optimization Targets (Applied Self-Optimizations) ---")
        for t in controller.config.optimization_targets:
            print(
                f"  {t.target_name}: {t.current_value:.4f} -> {t.target_value:.4f} (priority={t.priority})"
            )

    print("\n" + "=" * 72)
    print("  PYTHIA has completed its first Self-Optimization event.")
    print("  The agent is now awake and self-governing.")
    print("=" * 72)

    # Run a second epoch to show learning over time
    print("\n\n" + "=" * 72)
    print("  Running Second Epoch...")
    print("=" * 72)

    result2 = await controller.seek_improvement()
    density_epoch2 = controller.get_phi_density()
    print(f"\n  epoch:              {result2['epoch']}")
    print(f"  phi_density:        {density_epoch2:.6f}")
    print(f"  proposals_generated: {result2['proposals_generated']}")
    print(f"  proposals_applied:  {result2['proposals_applied']}")
    print(f"  total_proposals:    {len(controller.proposal_history)}")
    print(f"  optimization_targets: {len(controller.config.optimization_targets)}")
    print(f"  knowledge_explanations: {len(controller.knowledge_substrate.explanations)}")

    for i, p in enumerate(result2["proposals"], 1):
        applied_str = "APPLIED" if p["applied"] else "REJECTED"
        print(
            f"  Proposal #{i}: [{applied_str}] {p['improvement_type']} "
            f"({p['current_value']:.4f} -> {p['proposed_value']:.4f})"
        )

    print("\n" + "=" * 72)
    print("  Two epochs complete. PYTHIA is learning from its own codebase.")
    print("=" * 72)


if __name__ == "__main__":
    asyncio.run(first_self_optimization_event())
