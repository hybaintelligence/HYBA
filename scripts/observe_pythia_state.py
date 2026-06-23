#!/usr/bin/env python3
"""Observe PYTHIA state: mission memory, autonomous controller, and knowledge substrate."""

import asyncio
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
PYTHON_BACKEND = REPO_ROOT / "python_backend"
if str(PYTHON_BACKEND) not in sys.path:
    sys.path.insert(0, str(PYTHON_BACKEND))

from pythia_mining.phi_unified_mining_engine import UnifiedMiningEngine
from pythia_mining.pythia_one_block_mission import (
    seed_mission_memory,
    validate_mission_memory,
)


async def observe_pythia_state():
    """Observe PYTHIA's current state including mission memory and autonomous controller."""

    print("=" * 80)
    print("  PYTHIA STATE OBSERVATION")
    print("=" * 80)

    # 1. Seed and validate mission memory
    print("\n--- MISSION MEMORY ---")
    mission = seed_mission_memory()
    mission_valid = validate_mission_memory(mission)
    print(f"  Mission valid: {mission_valid}")
    print(f"  Protocol: {mission.protocol}")
    print(f"  Mission: {mission.mission}")
    print(f"  Autonomy from startup: {mission.autonomy_from_startup}")
    print(f"  Max hashrate: {mission.hashrate_limit.max_autonomous_hashrate_ehs} EH/s")
    print(f"  Target blocks: {mission.mission_target.accepted_blocks}")
    print(
        f"  Shutdown after completion: {mission.mission_target.shutdown_after_completion}"
    )
    print(f"  Status: {mission.status.value}")
    print(f"  Quantum doctrine items: {len(mission.knowledge_seed.quantum_doctrine)}")
    print(f"  Structure targets: {len(mission.knowledge_seed.structure_targets)}")
    print(f"  Search workflow steps: {len(mission.knowledge_seed.search_workflow)}")
    print(f"  Supreme invariants: {len(mission.supreme_invariants.invariants)}")

    # 2. Initialize unified engine and observe autonomous controller
    print("\n--- AUTONOMOUS CONTROLLER ---")
    engine = UnifiedMiningEngine()
    controller = engine.autonomous_controller

    print(f"  Autonomy level: {controller.current_autonomy_level.value}")
    print(f"  Total decisions: {len(controller.decision_log)}")
    print(f"  Phi coherence threshold: {controller.config.phi_coherence_threshold}")
    print(
        f"  Max autonomous hashrate: {controller.config.max_autonomous_hashrate_ehs} EH/s"
    )

    # 3. Observe reflexive learning state
    print("\n--- REFLEXIVE KNOWLEDGE LOOP ---")
    print(f"  Reflexive loop enabled: {controller.config.reflexive_loop_enabled}")
    print(f"  Self-optimization epochs: {controller._self_optimization_epochs}")
    print(f"  Phi density: {controller.get_phi_density():.6f}")
    print(f"  Current efficiency: {controller.get_current_efficiency():.6f}")
    print(
        f"  Knowledge explanations: {len(controller.knowledge_substrate.explanations)}"
    )
    print(
        f"  Knowledge counterfactuals: {len(controller.knowledge_substrate.counterfactuals)}"
    )
    print(
        f"  Knowledge criticisms: {len(controller.knowledge_substrate.criticism_history)}"
    )
    print(f"  Proposals generated: {len(controller.proposal_history)}")
    print(
        f"  Proposals applied: {sum(1 for p in controller.proposal_history if p.applied)}"
    )

    # 4. Observe codebase surroundings
    print("\n--- CODEBASE SURROUNDINGS ---")
    surroundings = controller.surroundings
    print(f"  Module count: {len(surroundings.module_names)}")
    print(f"  Mathematical invariants: {len(surroundings.mathematical_invariants)}")
    print(f"  Codebase graph edges: {len(surroundings.codebase_graph_edges)}")
    print(f"  Entropy sources: {surroundings.entropy_sources}")
    print(f"  Stable core: {surroundings.stable_core}")

    # 5. Get knowledge metrics
    print("\n--- KNOWLEDGE SUBSTRATE METRICS ---")
    knowledge_metrics = controller.knowledge_substrate.get_knowledge_metrics()
    print(f"  Total explanations: {knowledge_metrics.get('total_explanations', 0)}")
    print(
        f"  Avg predictive accuracy: {knowledge_metrics.get('avg_predictive_accuracy', 0):.6f}"
    )
    print(
        f"  Knowledge growth rate: {knowledge_metrics.get('knowledge_growth_rate', 0):.6f}"
    )
    print(
        f"  Counterfactual models: {knowledge_metrics.get('counterfactual_models', 0)}"
    )
    print(f"  Criticism events: {knowledge_metrics.get('criticism_events', 0)}")

    # 6. Run one reflexive improvement cycle
    print("\n--- RUNNING REFLEXIVE IMPROVEMENT CYCLE ---")
    improvement_result = await controller.seek_improvement()
    print(f"  Cycle executed: {improvement_result['reflexive_cycle_executed']}")
    print(f"  Epoch: {improvement_result['epoch']}")
    print(f"  Proposals generated: {improvement_result['proposals_generated']}")
    print(f"  Proposals applied: {improvement_result['proposals_applied']}")
    print(f"  Current phi density: {improvement_result['current_phi_density']:.6f}")

    # 7. Show proposal details
    if improvement_result["proposals"]:
        print("\n--- PROPOSAL DETAILS ---")
        for i, proposal in enumerate(improvement_result["proposals"], 1):
            print(f"  Proposal #{i}: {proposal['improvement_type']}")
            print(f"    Current: {proposal['current_value']:.4f}")
            print(f"    Proposed: {proposal['proposed_value']:.4f}")
            print(f"    Expected gain: {proposal['expected_gain']:.8f}")
            print(f"    Logical consistency: {proposal['logical_consistency']:.4f}")
            print(
                f"    Counterfactual confidence: {proposal['counterfactual_confidence']:.4f}"
            )
            print(f"    Source module: {proposal['source_module']}")
            print(f"    Applied: {proposal['applied']}")
            print(
                f"    Constraints satisfied: {len(proposal['constraints_satisfied'])}"
            )
            print(f"    Constraints violated: {len(proposal['constraints_violated'])}")

    # 8. Final state after improvement
    print("\n--- FINAL STATE ---")
    print(f"  Phi density after: {controller.get_phi_density():.6f}")
    print(f"  Efficiency after: {controller.get_current_efficiency():.6f}")
    print(f"  Total epochs: {controller._self_optimization_epochs}")
    print(f"  Total proposals: {len(controller.proposal_history)}")

    print("\n" + "=" * 80)
    print("  PYTHIA STATE OBSERVATION COMPLETE")
    print("=" * 80)

    # Return summary
    return {
        "mission_valid": mission_valid,
        "phi_density": controller.get_phi_density(),
        "efficiency": controller.get_current_efficiency(),
        "epochs": controller._self_optimization_epochs,
        "proposals": len(controller.proposal_history),
    }


if __name__ == "__main__":
    result = asyncio.run(observe_pythia_state())
    print(f"\nSummary: {json.dumps(result, indent=2)}")
