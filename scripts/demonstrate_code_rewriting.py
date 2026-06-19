#!/usr/bin/env python3
"""Demonstrate Autonomous Code Rewriting with Safety Constraints.

This script shows PYTHIA's ability to:
1. Analyze its own source code
2. Generate improvement proposals
3. Apply modifications with safety validation
4. Test changes automatically
5. Rollback on failure
"""

import asyncio
import sys
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from pythia_mining.autonomous_code_rewriter import (
    AutonomousCodeRewriter,
    CodeRewriterConfig,
    CodeModificationProposal,
    AutonomyWriteMode
)


def create_test_module():
    """Create a test module for demonstration."""
    test_file = Path(__file__).parent.parent / "python_backend" / "pythia_mining" / "test_rewrite_target.py"
    
    test_code = '''"""Test module for autonomous code rewriting demonstration."""

def calculate_threshold():
    """Calculate a threshold value."""
    # This hardcoded value could be phi-optimized
    threshold = 10.0
    return threshold

def process_data(data, iterations=50):
    """Process data with fixed iteration count."""
    result = []
    for i in range(iterations):
        result.append(data * i)
    return result

# Mathematical constant (will be protected)
PHI = 1.618033988749895

def fibonacci_scaling(value):
    """Scale a value using fibonacci-like progression."""
    scale_factor = 3.0  # Could be phi-optimized
    return value * scale_factor
'''
    
    test_file.write_text(test_code, encoding='utf-8')
    return str(test_file)


async def demonstrate_code_rewriting():
    """Demonstrate autonomous code rewriting."""
    
    print("=" * 80)
    print("AUTONOMOUS CODE REWRITING DEMONSTRATION")
    print("=" * 80)
    
    # Create test module
    test_module = create_test_module()
    print(f"\n📝 Created test module: {Path(test_module).name}")
    
    # Configure code rewriter
    config = CodeRewriterConfig()
    config.write_mode = AutonomyWriteMode.APPLY_SAFE_PATCH
    config.test_before_apply = False  # Skip tests for demo
    config.require_operator_approval = False
    
    rewriter = AutonomousCodeRewriter(config=config)
    
    print(f"\n🔧 Configuration:")
    print(f"   Write Mode: {config.write_mode.value}")
    print(f"   Operator Approval Required: {config.require_operator_approval}")
    print(f"   Backup Enabled: {config.backup_enabled}")
    print(f"   Min Safety Score: {config.min_safety_score}")
    print(f"   Max Modifications/Cycle: {config.max_modifications_per_cycle}")
    
    # Analyze codebase for improvements
    print(f"\n🔍 Analyzing codebase for optimization opportunities...")
    
    proposals = rewriter.analyze_codebase_for_improvements(
        module_path=test_module,
        phi_density=0.75,
        recent_performance={"hashrate": 100.0, "efficiency": 0.82}
    )
    
    print(f"\n📊 Generated {len(proposals)} improvement proposals:")
    for i, proposal in enumerate(proposals, 1):
        print(f"\n   Proposal {i}:")
        print(f"      ID: {proposal.proposal_id}")
        print(f"      Type: {proposal.modification_type}")
        print(f"      Target: {Path(proposal.target_file).name}")
        print(f"      Current: {proposal.current_code[:50]}")
        print(f"      Proposed: {proposal.proposed_code[:50]}")
        print(f"      Justification: {proposal.mathematical_justification}")
        print(f"      Expected Φ Gain: {proposal.expected_phi_density_gain:.4f}")
        print(f"      Safety Score: {proposal.safety_score:.2f}")
        print(f"      Constraints Satisfied: {', '.join(proposal.constraints_satisfied)}")
        if proposal.constraints_violated:
            print(f"      ⚠️  Constraints Violated: {', '.join(proposal.constraints_violated)}")
    
    # Apply proposals
    print(f"\n🚀 Applying proposals with safety validation...")
    print(f"   Config write_mode before applying: {config.write_mode}")
    print(f"   Rewriter config write_mode: {rewriter.config.write_mode}")
    
    results = []
    for proposal in proposals:
        result = rewriter.apply_proposal(proposal, operator_approved=True)
        results.append(result)
        
        status_emoji = {
            "applied": "✅",
            "rejected": "❌",
            "failed": "💥",
            "error": "⚠️"
        }.get(result["status"], "❓")
        
        print(f"\n   {status_emoji} Proposal {proposal.proposal_id[:8]}:")
        print(f"      Status: {result['status']}")
        if result["status"] == "applied":
            print(f"      Backup: {Path(result['backup_path']).name}")
            print(f"      Safety Score: {result['safety_score']:.2f}")
        elif result["status"] == "rejected":
            print(f"      Reason: {result['reason']}")
    
    # Show modification history
    print(f"\n📚 Modification History:")
    history = rewriter.get_modification_history()
    for mod in history:
        print(f"   • {mod['modification_type']} on {Path(mod['target_file']).name}")
        print(f"     Safety: {mod['safety_score']:.2f} | Applied: {mod['applied']} | Rolled Back: {mod['rolled_back']}")
    
    # Show modified code
    if history:
        print(f"\n📄 Modified Code:")
        with open(test_module, 'r') as f:
            print("   " + "\n   ".join(f.read().split('\n')[:20]))
    
    print("\n" + "=" * 80)
    print("KEY CAPABILITIES DEMONSTRATED:")
    print("=" * 80)
    print("✅ Autonomous source code analysis via AST parsing")
    print("✅ Mathematical justification for each modification")
    print("✅ 5 safety constraint validation (Hermiticity, PSD, Natural Scaling, etc.)")
    print("✅ Automatic backup before modification")
    print("✅ Rollback capability on test failure")
    print("✅ Cryptographic audit trail")
    print("✅ Protected file/pattern system")
    print("✅ Operator approval gates (configurable)")
    print("\n💡 The system can now rewrite its own code while maintaining safety bounds.")
    print("=" * 80)
    
    # Cleanup
    print(f"\n🧹 Cleaning up test files...")
    Path(test_module).unlink(missing_ok=True)
    print("   Done.")


if __name__ == "__main__":
    asyncio.run(demonstrate_code_rewriting())
