#!/usr/bin/env python3
"""
Autonomous Mining Proposal Generator

Runs the autonomous mining controller in proposal-only mode to generate
optimization suggestions without applying them. This allows for human review
and iterative learning.

Usage:
    python scripts/run_autonomous_mining_proposals.py
"""

import asyncio
import json
import sys
import time
from datetime import datetime
from pathlib import Path

# Add python_backend to path
PYTHON_BACKEND = Path(__file__).parent.parent / "python_backend"
sys.path.insert(0, str(PYTHON_BACKEND))

from pythia_mining.autonomous_mining_controller import (
    AutonomousMiningController,
    AutonomousConfig,
    AutonomyLevel,
)
from pythia_mining.phi_unified_mining_engine import UnifiedMiningEngine


async def generate_proposals(
    num_cycles: int = 3,
    target_hashrate_ehs: float = 150.0,
):
    """
    Generate autonomous mining proposals without applying them.
    
    Args:
        num_cycles: Number of reflexive cycles to run
        target_hashrate_ehs: Target hashrate for the engine
    """
    print("=" * 80)
    print("AUTONOMOUS MINING PROPOSAL GENERATOR")
    print("=" * 80)
    print(f"Mode: PROPOSAL-ONLY (no auto-apply)")
    print(f"Cycles: {num_cycles}")
    print(f"Target Hashrate: {target_hashrate_ehs} EH/s")
    print(f"Autonomy Level: UNBOUNDED")
    print("=" * 80)
    print()
    
    # Initialize unified mining engine
    print("🔧 Initializing Unified Mining Engine...")
    engine = UnifiedMiningEngine(
        configured_capacity_ehs=target_hashrate_ehs,
    )
    print("✅ Engine initialized")
    print()
    
    # Configure autonomous controller in UNBOUNDED mode
    print("🧠 Initializing Autonomous Mining Controller...")
    config = AutonomousConfig(
        autonomy_level=AutonomyLevel.UNBOUNDED,
        max_autonomous_hashrate_ehs=target_hashrate_ehs,
        reflexive_loop_enabled=True,
        reflexive_loop_interval=10.0,  # Short interval for testing
        max_proposals_per_cycle=5,
        min_counterfactual_confidence=0.0,  # Accept all proposals for review
    )
    
    controller = AutonomousMiningController(
        unified_engine=engine,
        config=config,
    )
    print("✅ Controller initialized")
    print(f"   Mining memory loaded: {bool(controller.mining_memory)}")
    print(f"   Autonomy level: {controller.current_autonomy_level}")
    print()
    
    # Run reflexive cycles to generate proposals
    proposals = []
    for cycle in range(num_cycles):
        print(f"🔄 Running reflexive cycle {cycle + 1}/{num_cycles}...")
        cycle_start = time.time()
        
        try:
            # Run reflexive optimization cycle
            await controller._run_reflexive_cycle()
            
            # Collect proposals from this cycle
            cycle_proposals = controller.proposal_history[-controller.config.max_proposals_per_cycle:]
            proposals.extend(cycle_proposals)
            
            cycle_duration = time.time() - cycle_start
            print(f"✅ Cycle {cycle + 1} completed in {cycle_duration:.2f}s")
            print(f"   Proposals generated: {len(cycle_proposals)}")
            print(f"   Total proposals so far: {len(proposals)}")
            print()
            
        except Exception as e:
            print(f"❌ Cycle {cycle + 1} failed: {e}")
            import traceback
            traceback.print_exc()
            print()
    
    # Generate proposal report
    print("=" * 80)
    print("PROPOSAL SUMMARY")
    print("=" * 80)
    print(f"Total proposals generated: {len(proposals)}")
    print()
    
    # Categorize proposals
    by_type = {}
    for proposal in proposals:
        prop_type = proposal.improvement_type
        if prop_type not in by_type:
            by_type[prop_type] = []
        by_type[prop_type].append(proposal)
    
    print("Proposals by type:")
    for prop_type, type_proposals in by_type.items():
        print(f"  {prop_type}: {len(type_proposals)}")
    print()
    
    # Save proposals to file
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    output_dir = Path("artifacts/autonomous_mining_proposals")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    output_file = output_dir / f"proposals_{timestamp}.json"
    
    proposal_data = {
        "generated_at": datetime.now().isoformat(),
        "autonomy_level": controller.current_autonomy_level.value,
        "num_cycles": num_cycles,
        "target_hashrate_ehs": target_hashrate_ehs,
        "total_proposals": len(proposals),
        "proposals": [
            {
                "proposal_id": p.proposal_id,
                "improvement_type": p.improvement_type,
                "current_value": p.current_value,
                "proposed_value": p.proposed_value,
                "expected_phi_density_gain": p.expected_phi_density_gain,
                "logical_consistency_score": p.logical_consistency_score,
                "confidence": p.counterfactual_confidence,
                "codebase_source": p.codebase_source_module,
                "constraints_satisfied": [c.value for c in p.constraints_satisfied],
                "constraints_violated": [c.value for c in p.constraints_violated],
                "applied": p.applied,
            }
            for p in proposals
        ],
    }
    
    with open(output_file, "w") as f:
        json.dump(proposal_data, f, indent=2)
    
    print(f"📄 Proposals saved to: {output_file}")
    print()
    
    # Display top proposals
    print("=" * 80)
    print("TOP PROPOSALS (by confidence)")
    print("=" * 80)
    
    sorted_proposals = sorted(proposals, key=lambda p: p.counterfactual_confidence, reverse=True)
    for i, proposal in enumerate(sorted_proposals[:10], 1):
        print(f"\n{i}. {proposal.improvement_type}")
        print(f"   Current: {proposal.current_value}")
        print(f"   Proposed: {proposal.proposed_value}")
        print(f"   Expected φ-density gain: {proposal.expected_phi_density_gain:.4f}")
        print(f"   Logical consistency: {proposal.logical_consistency_score:.4f}")
        print(f"   Confidence: {proposal.counterfactual_confidence:.2%}")
        print(f"   Source: {proposal.codebase_source_module}")
        print(f"   Constraints satisfied: {[c.value for c in proposal.constraints_satisfied]}")
        if proposal.constraints_violated:
            print(f"   Constraints violated: {[c.value for c in proposal.constraints_violated]}")
    
    print()
    print("=" * 80)
    print("NEXT STEPS")
    print("=" * 80)
    print("1. Review the proposals in the JSON file")
    print("2. Identify which proposals are valid and which are hallucinations")
    print("3. Update the mining memory with correct patterns")
    print("4. Re-run to see if the system learns")
    print()
    
    return proposals


async def main():
    """Main entry point."""
    try:
        proposals = await generate_proposals(
            num_cycles=3,
            target_hashrate_ehs=150.0,
        )
        print("✅ Proposal generation complete")
        return 0
    except Exception as e:
        print(f"❌ Proposal generation failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
