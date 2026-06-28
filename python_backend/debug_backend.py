#!/usr/bin/env python3
"""
HYBA Backend Debug Script

Quick diagnostic tool for FastAPI backend issues.
Run this from python_backend/ directory:
    python debug_backend.py
"""

import sys
import traceback
from pathlib import Path

# Colors for terminal output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    END = '\033[0m'
    BOLD = '\033[1m'

def print_section(title):
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'=' * 60}")
    print(f"{title}")
    print(f"{'=' * 60}{Colors.END}\n")

def print_ok(msg):
    print(f"{Colors.GREEN}✅ {msg}{Colors.END}")

def print_error(msg):
    print(f"{Colors.RED}❌ {msg}{Colors.END}")

def print_warning(msg):
    print(f"{Colors.YELLOW}⚠️  {msg}{Colors.END}")

def check_imports():
    """Test critical imports."""
    print_section("1. Testing Critical Imports")
    
    imports_to_test = [
        ("fastapi", "FastAPI"),
        ("pydantic", "Pydantic"),
        ("sqlalchemy", "SQLAlchemy"),
        ("motor", "Motor (async MongoDB)"),
        ("redis", "Redis"),
        ("hyba_genesis_api", "HYBA Genesis API"),
        ("pythia_mining", "PYTHIA Mining"),
        ("pythia_shared", "PYTHIA Shared"),
    ]
    
    passed = 0
    failed = 0
    
    for module, name in imports_to_test:
        try:
            __import__(module)
            print_ok(f"{name} ({module})")
            passed += 1
        except ImportError as e:
            print_error(f"{name} ({module}): {str(e)}")
            failed += 1
        except Exception as e:
            print_error(f"{name} ({module}): {type(e).__name__}: {str(e)}")
            failed += 1
    
    print(f"\nResult: {passed} passed, {failed} failed")
    return failed == 0

def check_api_main():
    """Test API main module can be imported."""
    print_section("2. Testing API Main Module")
    
    try:
        from hyba_genesis_api import main
        print_ok("Main module imports successfully")
        
        # Check app exists
        app = main.app
        print_ok(f"FastAPI app instantiated: {type(app)}")
        
        # Check key attributes
        if hasattr(app, 'router'):
            print_ok(f"App router exists with {len(app.router.routes)} routes")
        
        return True
    except Exception as e:
        print_error(f"Failed to import main: {type(e).__name__}: {str(e)}")
        traceback.print_exc()
        return False

def check_pulvini():
    """Test PULVINI module."""
    print_section("3. Testing PULVINI Module")
    
    try:
        from pythia_mining.pulvini_structural_certificate import StructuralCertificate
        from pythia_mining.pulvini_topology import ADJACENCY_MAP
        print_ok(f"PULVINI topology imports successfully")
        
        # Check adjacency map
        print_ok(f"ADJACENCY_MAP has {len(ADJACENCY_MAP)} nodes")
        
        # Verify symmetry
        asymmetric = []
        for node, neighbors in ADJACENCY_MAP.items():
            for neighbor in neighbors:
                if node not in ADJACENCY_MAP.get(neighbor, []):
                    asymmetric.append((node, neighbor))
        
        if asymmetric:
            print_warning(f"Found {len(asymmetric)} asymmetric edges (should be 0)")
            for src, dst in asymmetric[:5]:  # Show first 5
                print(f"  {src} → {dst} (but {dst} ↛ {src})")
            if len(asymmetric) > 5:
                print(f"  ... and {len(asymmetric) - 5} more")
        else:
            print_ok("All adjacency edges are symmetric")
        
        # Check degrees
        d_degrees = [len(ADJACENCY_MAP.get(n, [])) for n in range(20)]
        i_degrees = [len(ADJACENCY_MAP.get(n, [])) for n in range(20, 32)]
        
        print_ok(f"D-nodes (0-19): avg degree = {sum(d_degrees)/len(d_degrees):.1f}")
        print_ok(f"I-nodes (20-31): avg degree = {sum(i_degrees)/len(i_degrees):.1f}")
        
        # Check automorphisms
        try:
            from pythia_mining.pulvini_group import compute_graph_automorphisms
            autos = compute_graph_automorphisms(ADJACENCY_MAP)
            
            if len(autos) == 1:
                print_warning(f"Automorphism group order: 1 (expected 120)")
                print("  This suggests the adjacency map may not be dodecahedral")
            elif len(autos) == 120:
                print_ok(f"Automorphism group order: 120 (correct!)")
            else:
                print_warning(f"Automorphism group order: {len(autos)} (expected 120)")
        except Exception as e:
            print_error(f"Could not compute automorphisms: {type(e).__name__}: {str(e)}")
        
        return True
    except Exception as e:
        print_error(f"PULVINI error: {type(e).__name__}: {str(e)}")
        traceback.print_exc()
        return False

def check_quantum_api():
    """Test Quantum-as-a-Service API."""
    print_section("4. Testing Quantum-as-a-Service API")
    
    try:
        from hyba_genesis_api.api import quantum_as_a_service
        print_ok("Quantum API module imports successfully")
        
        # Check router exists
        if hasattr(quantum_as_a_service, 'router'):
            router = quantum_as_a_service.router
            print_ok(f"API router created with prefix: {router.prefix}")
            
            # Verify prefix includes "virtual"
            if "virtual" in router.prefix:
                print_ok(f"✓ Router path is properly qualified: {router.prefix}")
            else:
                print_warning(f"✗ Router path missing 'virtual': {router.prefix}")
        
        if hasattr(quantum_as_a_service, 'public_router'):
            public_router = quantum_as_a_service.public_router
            print_ok(f"Public router created with prefix: {public_router.prefix}")
            
            if "virtual" in public_router.prefix:
                print_ok(f"✓ Public router path is properly qualified: {public_router.prefix}")
            else:
                print_warning(f"✗ Public router path missing 'virtual': {public_router.prefix}")
        
        return True
    except Exception as e:
        print_error(f"Quantum API error: {type(e).__name__}: {str(e)}")
        traceback.print_exc()
        return False

def check_test_client():
    """Test FastAPI TestClient."""
    print_section("5. Testing FastAPI Test Client")
    
    try:
        from fastapi.testclient import TestClient
        from hyba_genesis_api.main import app
        
        client = TestClient(app)
        print_ok("TestClient created")
        
        # Test health endpoint
        try:
            response = client.get("/health")
            if response.status_code == 200:
                print_ok(f"Health endpoint: {response.status_code} OK")
                data = response.json()
                if "status" in data:
                    print_ok(f"  Status: {data.get('status')}")
            else:
                print_warning(f"Health endpoint: {response.status_code} (expected 200)")
        except Exception as e:
            print_warning(f"Health endpoint error: {type(e).__name__}")
        
        # Test quantum endpoint
        try:
            response = client.get("/api/v1/virtual-fault-tolerant-computers/status")
            if response.status_code in [200, 401, 403]:  # Any response code is OK
                print_ok(f"Quantum endpoint exists: {response.status_code}")
                if "claim_boundary" in response.json():
                    print_ok(f"  Claim boundary present in response")
                else:
                    print_warning(f"  Claim boundary NOT in response")
            else:
                print_warning(f"Quantum endpoint: {response.status_code}")
        except Exception as e:
            print_warning(f"Quantum endpoint error: {type(e).__name__}")
        
        return True
    except Exception as e:
        print_error(f"Test client error: {type(e).__name__}: {str(e)}")
        traceback.print_exc()
        return False

def check_environment():
    """Check environment variables and configuration."""
    print_section("6. Checking Environment & Configuration")
    
    import os
    
    env_vars = [
        "HYBA_ENV",
        "MONGO_URL",
        "DB_NAME",
        "JWT_SECRET",
        "REDIS_URL",
    ]
    
    for var in env_vars:
        value = os.getenv(var)
        if value:
            # Mask sensitive values
            if "SECRET" in var or "PASSWORD" in var or "KEY" in var:
                masked = value[:10] + "*" * (len(value) - 10) if len(value) > 10 else "*" * len(value)
                print_ok(f"{var} = {masked}")
            else:
                print_ok(f"{var} = {value}")
        else:
            print_warning(f"{var} not set (optional in dev)")

def main():
    """Run all diagnostic checks."""
    print(f"\n{Colors.BOLD}{Colors.BLUE}")
    print("HYBA Backend Diagnostic Tool")
    print(f"{Colors.END}")
    print(f"Working directory: {Path.cwd()}")
    print(f"Python: {sys.version}")
    
    results = []
    
    results.append(("Imports", check_imports()))
    results.append(("API Main", check_api_main()))
    results.append(("PULVINI", check_pulvini()))
    results.append(("Quantum API", check_quantum_api()))
    results.append(("Test Client", check_test_client()))
    check_environment()
    
    # Summary
    print_section("Summary")
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = f"{Colors.GREEN}✅ PASS{Colors.END}" if result else f"{Colors.RED}❌ FAIL{Colors.END}"
        print(f"{name}: {status}")
    
    print(f"\n{Colors.BOLD}Total: {passed}/{total} checks passed{Colors.END}\n")
    
    if passed == total:
        print(f"{Colors.GREEN}Backend is ready for debugging!{Colors.END}")
        print("\nNext steps:")
        print("  1. Start the backend: uvicorn hyba_genesis_api.main:app --reload --log-level debug")
        print("  2. Run tests: pytest tests/ -v")
        print("  3. For PULVINI issues: python debug_pulvini.py")
        return 0
    else:
        print(f"{Colors.RED}Some checks failed. Fix the issues above before proceeding.{Colors.END}\n")
        return 1

if __name__ == "__main__":
    sys.exit(main())
