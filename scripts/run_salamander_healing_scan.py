#!/usr/bin/env python3
"""
Run Salamander autonomous damage detection and healing proposal generation.

Scans the codebase for damage, drift, and optimization opportunities using the
autonomous damage detector, then generates sovereign-sealed healing proposals.
"""

import json
import sys
from pathlib import Path
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[1]
PYTHON_BACKEND = ROOT / "python_backend"
if str(PYTHON_BACKEND) not in sys.path:
    sys.path.insert(0, str(PYTHON_BACKEND))

from pythia_self_healing.autonomous_damage_detector import AutonomousDamageDetector
from pythia_self_healing.self_healing_reactor import SelfHealingReactor
from pythia_self_healing.salamander_regenerator import SalamanderRegenerator


def run_healing_scan():
    """Execute autonomous damage detection and healing proposal generation."""
    print("=" * 80)
    print("SALAMANDER AUTONOMOUS HEALING SCAN")
    print("=" * 80)
    print()
    
    detector = AutonomousDamageDetector()
    regenerator = SalamanderRegenerator()
    reactor = SelfHealingReactor(regenerator)
    
    # Scan key directories
    scan_paths = [
        PYTHON_BACKEND / "hyba_genesis_api",
        PYTHON_BACKEND / "pythia_mining",
        PYTHON_BACKEND / "pythia_self_healing",
    ]
    
    print("🔍 Scanning codebase for damage and optimization opportunities...")
    print()
    
    damage_reports = detector.scan_paths(scan_paths)
    
    print(f"📊 Found {len(damage_reports)} damage reports")
    print()
    
    if not damage_reports:
        print("✅ No damage detected - system is healthy")
        return {"status": "healthy", "reports": []}
    
    # Generate healing proposals for each damage report
    print("🦎 Generating sovereign-sealed healing proposals...")
    print()
    
    proposals = []
    for report in damage_reports:
        module_path = report.get("module_path")
        target_name = report.get("target_name")
        
        if not module_path or not target_name:
            print(f"⚠️  Skipping report with missing path/target")
            continue
        
        print(f"  Processing: {target_name} in {module_path}")
        
        try:
            proposal = reactor.heal_damage(report, module_path, target_name)
            proposals.append(proposal)
            
            status = proposal.get("status", "UNKNOWN")
            action = proposal.get("action", "NO_ACTION")
            
            print(f"    Status: {status}")
            print(f"    Action: {action}")
            print()
        except Exception as e:
            print(f"    ❌ Error generating proposal: {e}")
            print()
    
    # Summary
    print("=" * 80)
    print("HEALING SCAN SUMMARY")
    print("=" * 80)
    print()
    
    staged = sum(1 for p in proposals if "STAGED" in p.get("status", ""))
    rejected = sum(1 for p in proposals if "REJECTED" in p.get("status", ""))
    no_healing = sum(1 for p in proposals if "NO_HEALING" in p.get("status", ""))
    
    print(f"Total reports: {len(damage_reports)}")
    print(f"Proposals staged: {staged}")
    print(f"Proposals rejected: {rejected}")
    print(f"No healing needed: {no_healing}")
    print()
    
    # Save report
    artifact_dir = ROOT / "artifacts" / "salamander_healing"
    artifact_dir.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    report_path = artifact_dir / f"healing_scan_{timestamp}.json"
    
    report = {
        "schema": "SALAMANDER_HEALING_SCAN_V1",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "scan_summary": {
            "total_reports": len(damage_reports),
            "proposals_staged": staged,
            "proposals_rejected": rejected,
            "no_healing_needed": no_healing,
        },
        "damage_reports": damage_reports,
        "healing_proposals": proposals,
    }
    
    with open(report_path, "w") as f:
        json.dump(report, f, indent=2, default=str)
    
    print(f"📄 Report saved to: {report_path}")
    print()
    
    if staged > 0:
        print("⚠️  SOVEREIGN HUMAN REVIEW REQUIRED")
        print(f"   {staged} healing proposals require human approval")
        print("   Review proposals in the artifact file above")
        print("   Apply changes only after thorough review")
    else:
        print("✅ All issues are either rejected or do not require healing")
    
    return report


def main():
    try:
        report = run_healing_scan()
        return 0
    except Exception as e:
        print(f"❌ Healing scan failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
