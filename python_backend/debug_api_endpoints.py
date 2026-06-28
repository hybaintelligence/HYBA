#!/usr/bin/env python3
"""
FastAPI Endpoint Tester

Tests key HYBA API endpoints and reports results.
Run this from python_backend/ directory:
    python debug_api_endpoints.py
"""

import sys
import json
from typing import Dict, Any

# Colors
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
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

def print_response(status: int, data: Any, indent=0):
    prefix = "  " * indent
    status_color = Colors.GREEN if 200 <= status < 300 else Colors.YELLOW if status < 500 else Colors.RED
    print(f"{prefix}{status_color}Status: {status}{Colors.END}")
    try:
        json_str = json.dumps(data, indent=2)
        for line in json_str.split('\n'):
            print(f"{prefix}  {line}")
    except:
        print(f"{prefix}  {data}")

def test_endpoints():
    """Test key API endpoints."""
    print_section("API ENDPOINT TESTS")
    
    try:
        from fastapi.testclient import TestClient
        from hyba_genesis_api.main import app
    except ImportError as e:
        print_error(f"Cannot import TestClient or app: {e}")
        return False
    
    client = TestClient(app)
    results = []
    
    # 1. Health endpoint
    print(f"{Colors.BOLD}1. Health Endpoint{Colors.END}")
    try:
        response = client.get("/health")
        if response.status_code == 200:
            print_ok("Health endpoint responds")
            data = response.json()
            print_response(response.status_code, data, indent=1)
            results.append(("Health", True))
        else:
            print_warning(f"Health endpoint returned {response.status_code}")
            results.append(("Health", False))
    except Exception as e:
        print_error(f"Health endpoint failed: {e}")
        results.append(("Health", False))
    
    # 2. Quantum API - Status
    print(f"\n{Colors.BOLD}2. Quantum-as-a-Service - Status{Colors.END}")
    try:
        response = client.get("/api/v1/virtual-fault-tolerant-computers/status")
        print_ok(f"Endpoint exists (status {response.status_code})")
        
        data = response.json()
        print_response(response.status_code, data, indent=1)
        
        # Check for claim_boundary
        if "claim_boundary" in data:
            print_ok("Response includes claim_boundary", indent=1)
            results.append(("Quantum Status", True))
        else:
            print_warning("Response missing claim_boundary", indent=1)
            results.append(("Quantum Status", False))
    except Exception as e:
        print_error(f"Quantum status endpoint failed: {e}")
        results.append(("Quantum Status", False))
    
    # 3. Health check with more detail
    print(f"\n{Colors.BOLD}3. Route Summary{Colors.END}")
    print(f"Total routes defined: {len(app.routes)}")
    
    # Find routes with "quantum" or "virtual"
    quantum_routes = [r for r in app.routes if hasattr(r, 'path') and 'virtual' in r.path.lower()]
    print_ok(f"Routes with 'virtual': {len(quantum_routes)}", indent=1)
    
    for route in quantum_routes:
        methods = list(route.methods) if hasattr(route, 'methods') else ['GET', 'POST']
        print_info(f"{route.path} {methods}", indent=2)
    
    # 4. Router structure
    print(f"\n{Colors.BOLD}4. API Router Structure{Colors.END}")
    try:
        from hyba_genesis_api.api import quantum_as_a_service
        
        if hasattr(quantum_as_a_service, 'router'):
            router = quantum_as_a_service.router
            print_ok(f"Admin router exists", indent=1)
            print_info(f"Prefix: {router.prefix}", indent=2)
            print_info(f"Routes: {len(router.routes)}", indent=2)
            
            if "virtual" in router.prefix:
                print_ok("✓ Router prefix includes 'virtual'", indent=2)
            else:
                print_error("✗ Router prefix missing 'virtual'", indent=2)
        
        if hasattr(quantum_as_a_service, 'public_router'):
            public_router = quantum_as_a_service.public_router
            print_ok(f"Public router exists", indent=1)
            print_info(f"Prefix: {public_router.prefix}", indent=2)
            print_info(f"Routes: {len(public_router.routes)}", indent=2)
            
            if "virtual" in public_router.prefix:
                print_ok("✓ Public router prefix includes 'virtual'", indent=2)
            else:
                print_error("✗ Public router prefix missing 'virtual'", indent=2)
    
    except Exception as e:
        print_error(f"Could not inspect routers: {e}")
    
    # Summary
    print(f"\n{Colors.BOLD}Test Results:{Colors.END}")
    passed = sum(1 for _, result in results if result)
    total = len(results)
    print(f"Passed: {passed}/{total}")
    
    for name, result in results:
        status = f"{Colors.GREEN}✅{Colors.END}" if result else f"{Colors.RED}❌{Colors.END}"
        print(f"  {status} {name}")
    
    return passed == total

def test_imports():
    """Test critical imports."""
    print_section("IMPORT CHECKS")
    
    modules = [
        "hyba_genesis_api.main",
        "hyba_genesis_api.api.quantum_as_a_service",
        "pythia_mining.pulvini_topology",
        "pythia_mining.pulvini_group",
    ]
    
    passed = 0
    for module in modules:
        try:
            __import__(module)
            print_ok(f"{module}")
            passed += 1
        except Exception as e:
            print_error(f"{module}: {type(e).__name__}: {str(e)[:60]}")
    
    print(f"\nResult: {passed}/{len(modules)} passed")
    return passed == len(modules)

def test_claim_boundaries():
    """Test that API responses include claim boundaries."""
    print_section("CLAIM BOUNDARY VERIFICATION")
    
    try:
        from fastapi.testclient import TestClient
        from hyba_genesis_api.main import app
    except ImportError as e:
        print_error(f"Cannot import: {e}")
        return False
    
    client = TestClient(app)
    
    endpoints_to_test = [
        "/api/v1/virtual-fault-tolerant-computers/status",
    ]
    
    passed = 0
    for endpoint in endpoints_to_test:
        print(f"\nEndpoint: {endpoint}")
        try:
            response = client.get(endpoint)
            
            if response.status_code >= 400:
                print_warning(f"  Status {response.status_code} (expected 2xx)", indent=1)
                continue
            
            data = response.json()
            
            if "claim_boundary" in data:
                print_ok(f"✓ Includes claim_boundary", indent=1)
                print_info(f"Value: {data['claim_boundary'][:60]}...", indent=2)
                passed += 1
            else:
                print_error(f"✗ Missing claim_boundary", indent=1)
        
        except Exception as e:
            print_error(f"Error: {e}", indent=1)
    
    print(f"\nResult: {passed}/{len(endpoints_to_test)} endpoints have claim_boundary")
    return passed == len(endpoints_to_test)

def main():
    print(f"\n{Colors.BOLD}{Colors.BLUE}")
    print("╔════════════════════════════════════════════════════════════════════╗")
    print("║              HYBA FastAPI ENDPOINT TEST SUITE                      ║")
    print("╚════════════════════════════════════════════════════════════════════╝")
    print(f"{Colors.END}")
    print(f"Python: {sys.version.split()[0]}")
    print(f"Working directory: {sys.path[0]}\n")
    
    results = []
    
    results.append(("Imports", test_imports()))
    results.append(("Endpoints", test_endpoints()))
    results.append(("Claim Boundaries", test_claim_boundaries()))
    
    # Final Report
    print_section("FINAL REPORT")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    print(f"{Colors.BOLD}Summary:{Colors.END}")
    for name, result in results:
        status = f"{Colors.GREEN}✅ PASS{Colors.END}" if result else f"{Colors.RED}❌ FAIL{Colors.END}"
        print(f"  {status} - {name}")
    
    print(f"\n{Colors.BOLD}Result: {passed}/{total} test suites passed{Colors.END}\n")
    
    if passed == total:
        print(f"{Colors.GREEN}✅ All API tests passed! Backend is ready for use.{Colors.END}\n")
        print("Next steps:")
        print("  1. Start the server: uvicorn hyba_genesis_api.main:app --reload")
        print("  2. Visit: http://localhost:8000/docs (Swagger UI)")
        print("  3. Run tests: pytest tests/ -v")
        return 0
    else:
        print(f"{Colors.RED}❌ Some tests failed. Review errors above.{Colors.END}\n")
        return 1

if __name__ == "__main__":
    sys.exit(main())
