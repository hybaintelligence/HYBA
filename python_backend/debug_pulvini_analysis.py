#!/usr/bin/env python3
"""
PULVINI Structural Certificate Debug Script

Diagnoses issues with PULVINI topology and automorphism group computation.
Run this from python_backend/ directory:
    python debug_pulvini_analysis.py
"""

import sys
import traceback
from collections import defaultdict

# Colors
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    END = '\033[0m'
    BOLD = '\033[1m'

def print_section(title):
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'=' * 70}")
    print(f"  {title}")
    print(f"{'=' * 70}{Colors.END}\n")

def print_ok(msg, indent=0):
    prefix = "  " * indent
    print(f"{prefix}{Colors.GREEN}✅ {msg}{Colors.END}")

def print_error(msg, indent=0):
    prefix = "  " * indent
    print(f"{prefix}{Colors.RED}❌ {msg}{Colors.END}")

def print_warning(msg, indent=0):
    prefix = "  " * indent
    print(f"{prefix}{Colors.YELLOW}⚠️  {msg}{Colors.END}")

def print_info(msg, indent=0):
    prefix = "  " * indent
    print(f"{prefix}{Colors.BLUE}ℹ️  {msg}{Colors.END}")

def analyze_adjacency_map():
    """Step 1: Analyze adjacency map structure."""
    print_section("STEP 1: Adjacency Map Analysis")
    
    try:
        from pythia_mining.pulvini_topology import ADJACENCY_MAP
    except ImportError as e:
        print_error(f"Cannot import ADJACENCY_MAP: {e}")
        return None
    
    print(f"Total nodes in ADJACENCY_MAP: {len(ADJACENCY_MAP)}")
    
    # Verify expected node counts
    d_nodes = list(range(20))  # Dodecahedral
    i_nodes = list(range(20, 32))  # Icosahedral
    
    print(f"  D-nodes expected (0-19): {len(d_nodes)}")
    print(f"  I-nodes expected (20-31): {len(i_nodes)}")
    
    # Check if all nodes exist
    missing_nodes = [n for n in range(32) if n not in ADJACENCY_MAP]
    if missing_nodes:
        print_error(f"Missing nodes: {missing_nodes}")
    else:
        print_ok(f"All 32 nodes present in ADJACENCY_MAP")
    
    # Check symmetry
    print(f"\n{Colors.BOLD}Symmetry Check:{Colors.END}")
    asymmetric_pairs = []
    for node, neighbors in ADJACENCY_MAP.items():
        for neighbor in neighbors:
            if node not in ADJACENCY_MAP.get(neighbor, []):
                asymmetric_pairs.append((node, neighbor))
    
    if asymmetric_pairs:
        print_error(f"Found {len(asymmetric_pairs)} asymmetric edges (should be 0)")
        # Group by source node
        by_source = defaultdict(list)
        for src, dst in asymmetric_pairs:
            by_source[src].append(dst)
        
        for src in sorted(by_source.keys()):
            dsts = by_source[src]
            print(f"  Node {src} → {dsts} (but {dsts} ↛ {src})", end="")
            if len(dsts) <= 2:
                print()  # New line for short lists
            else:
                print(f" (+ {len(dsts)-2} more)\n")
    else:
        print_ok("All edges are bidirectional (symmetric)")
    
    return ADJACENCY_MAP

def analyze_degrees(adjacency_map):
    """Step 2: Analyze node degrees."""
    print_section("STEP 2: Degree Analysis")
    
    if not adjacency_map:
        print_error("No adjacency map provided")
        return
    
    # D-nodes (0-19)
    d_nodes = list(range(20))
    d_degrees = {n: len(adjacency_map.get(n, [])) for n in d_nodes}
    
    # I-nodes (20-31)
    i_nodes = list(range(20, 32))
    i_degrees = {n: len(adjacency_map.get(n, [])) for n in i_nodes}
    
    # D-nodes analysis
    print(f"{Colors.BOLD}D-Nodes (Dodecahedral, 0-19):{Colors.END}")
    d_values = list(d_degrees.values())
    d_avg = sum(d_values) / len(d_values)
    d_min = min(d_values)
    d_max = max(d_values)
    
    print(f"  Count: {len(d_nodes)}")
    print(f"  Degrees: min={d_min}, max={d_max}, avg={d_avg:.2f}")
    print(f"  Expected: all should have degree 3 (dodecahedral vertex)")
    
    if d_min == d_max == 3 and d_avg == 3:
        print_ok("D-nodes have correct dodecahedral degree (3)")
    elif d_min == d_max:
        print_warning(f"D-nodes have uniform degree {d_min} (expected 3)")
    else:
        print_warning(f"D-nodes have mixed degrees (not regular)")
        # Show distribution
        degree_dist = defaultdict(int)
        for n, deg in d_degrees.items():
            degree_dist[deg] += 1
        for deg in sorted(degree_dist.keys()):
            print(f"    Degree {deg}: {degree_dist[deg]} nodes")
    
    # I-nodes analysis
    print(f"\n{Colors.BOLD}I-Nodes (Icosahedral, 20-31):{Colors.END}")
    i_values = list(i_degrees.values())
    i_avg = sum(i_values) / len(i_values)
    i_min = min(i_values)
    i_max = max(i_values)
    
    print(f"  Count: {len(i_nodes)}")
    print(f"  Degrees: min={i_min}, max={i_max}, avg={i_avg:.2f}")
    print(f"  Expected: all should have degree 5 (icosahedral vertex)")
    
    if i_min == i_max == 5 and i_avg == 5:
        print_ok("I-nodes have correct icosahedral degree (5)")
    elif i_min == i_max:
        print_warning(f"I-nodes have uniform degree {i_min} (expected 5)")
    else:
        print_warning(f"I-nodes have mixed degrees (not regular)")
        # Show distribution
        degree_dist = defaultdict(int)
        for n, deg in i_degrees.items():
            degree_dist[deg] += 1
        for deg in sorted(degree_dist.keys()):
            print(f"    Degree {deg}: {degree_dist[deg]} nodes")
    
    # Total edges
    total_edges = sum(d_values) // 2 + sum(i_values) // 2
    print(f"\n{Colors.BOLD}Total Edges:{Colors.END}")
    print(f"  Undirected edges: {total_edges}")
    print(f"  Expected for dodecahedron: 30")
    print(f"  Expected for icosahedron: 30")

def compute_automorphisms(adjacency_map):
    """Step 3: Compute automorphism group."""
    print_section("STEP 3: Automorphism Group Computation")
    
    if not adjacency_map:
        print_error("No adjacency map provided")
        return None
    
    try:
        from pythia_mining.pulvini_group import compute_graph_automorphisms
    except ImportError as e:
        print_error(f"Cannot import automorphism function: {e}")
        return None
    
    print("Computing automorphisms (this may take a moment)...")
    
    try:
        autos = compute_graph_automorphisms(adjacency_map)
        print_ok(f"Computation completed")
        
        print(f"\n{Colors.BOLD}Results:{Colors.END}")
        print(f"  Automorphism group order: {len(autos)}")
        print(f"  Expected: 120 (5! for dodecahedron)")
        
        if len(autos) == 1:
            print_error(f"Only identity automorphism found!")
            print(f"\n{Colors.BOLD}Diagnosis:{Colors.END}")
            print_warning("This indicates one of the following:", 0)
            print_warning("1. Adjacency map is not actually dodecahedral/icosahedral", 1)
            print_warning("2. Adjacency map has asymmetric edges breaking symmetry", 1)
            print_warning("3. Automorphism computation algorithm has a bug", 1)
            
            print(f"\n{Colors.BOLD}Next Steps:{Colors.END}")
            print_info("Check results from STEP 1 (Symmetry Check) above", 0)
            print_info("If edges are asymmetric, fix ADJACENCY_MAP in pulvini_topology.py", 0)
            print_info("If edges are symmetric, the math definition may be wrong", 0)
            return autos
        
        elif len(autos) == 120:
            print_ok(f"Automorphism group order is correct (120)")
            return autos
        
        else:
            print_warning(f"Unexpected automorphism group order: {len(autos)}")
            print(f"  This is neither 1 (identity only) nor 120 (full symmetry)")
            print(f"  It may indicate partial symmetry or a hybrid structure")
            return autos
    
    except Exception as e:
        print_error(f"Automorphism computation failed: {type(e).__name__}: {e}")
        traceback.print_exc()
        return None

def check_structural_certificate(adjacency_map, autos):
    """Step 4: Check structural certificate."""
    print_section("STEP 4: Structural Certificate Verification")
    
    if not adjacency_map:
        print_error("No adjacency map provided")
        return
    
    try:
        from pythia_mining.pulvini_structural_certificate import StructuralCertificate
    except ImportError as e:
        print_error(f"Cannot import StructuralCertificate: {e}")
        return
    
    try:
        cert = StructuralCertificate()
        
        print(f"Structural Certificate Contents:")
        print(f"  D-nodes: {cert.d_node_count} (expected 20)")
        print(f"  I-nodes: {cert.i_node_count} (expected 12)")
        print(f"  Automorphism group order: {cert.automorphism_group_order} (expected 120)")
        
        if cert.automorphism_group_order == 120:
            print_ok("Structural certificate appears valid")
        else:
            print_error(f"Automorphism group order mismatch: expected 120, got {cert.automorphism_group_order}")
        
        # Cross-check with computed automorphisms
        if autos and len(autos) != cert.automorphism_group_order:
            print_warning(f"Mismatch: computed {len(autos)}, cert says {cert.automorphism_group_order}")
    
    except Exception as e:
        print_error(f"Error loading structural certificate: {type(e).__name__}: {e}")
        traceback.print_exc()

def run_tests():
    """Step 5: Run pytest on PULVINI tests."""
    print_section("STEP 5: Running PULVINI Tests")
    
    import subprocess
    
    print("Running: pytest tests/test_pulvini_structural_certificate.py -v\n")
    
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pytest", 
             "tests/test_pulvini_structural_certificate.py", 
             "-v", "--tb=short"],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)
        
        if result.returncode == 0:
            print_ok("All PULVINI tests passed!")
        else:
            print_error("Some PULVINI tests failed")
            return False
        
        return True
    
    except Exception as e:
        print_error(f"Could not run tests: {type(e).__name__}: {e}")
        return False

def generate_report():
    """Generate diagnostic report."""
    print_section("DIAGNOSTIC REPORT")
    
    print(f"{Colors.BOLD}Analysis Summary:{Colors.END}\n")
    
    # Run all diagnostics
    adjacency_map = analyze_adjacency_map()
    
    if adjacency_map:
        analyze_degrees(adjacency_map)
        autos = compute_automorphisms(adjacency_map)
        check_structural_certificate(adjacency_map, autos)
    
    # Run tests
    print()
    tests_passed = run_tests()
    
    # Final verdict
    print_section("FINAL VERDICT")
    
    if adjacency_map and tests_passed:
        print_ok("PULVINI module is working correctly!")
        print("\nYou can proceed with:")
        print("  1. Using PULVINI in production APIs")
        print("  2. Referencing it in external documentation")
        print("  3. Running the full test suite")
    else:
        print_error("PULVINI module has issues that need fixing")
        print("\nRecommended next steps:")
        print("  1. Review STEP 1 (Symmetry) - fix asymmetric edges if present")
        print("  2. Review STEP 2 (Degrees) - verify D and I node degrees")
        print("  3. Review STEP 3 (Automorphisms) - understand why only identity found")
        print("  4. Rerun this script after making changes")
    
    print()

def main():
    print(f"\n{Colors.BOLD}{Colors.BLUE}")
    print("╔════════════════════════════════════════════════════════════════════╗")
    print("║           PULVINI STRUCTURAL CERTIFICATE DIAGNOSTIC TOOL            ║")
    print("╚════════════════════════════════════════════════════════════════════╝")
    print(f"{Colors.END}")
    print(f"Working directory: {sys.path[0]}")
    print(f"Python: {sys.version.split()[0]}\n")
    
    generate_report()
    
    print(f"{Colors.BOLD}End of Report{Colors.END}\n")

if __name__ == "__main__":
    main()
