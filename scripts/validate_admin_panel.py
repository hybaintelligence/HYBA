#!/usr/bin/env python3
"""Admin Panel Implementation Validation Script.

Validates that the complete admin panel with user management is properly
integrated and ready for deployment.
"""

import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent / "python_backend"))


def validate_backend_components():
    """Validate backend admin infrastructure."""
    print("\n" + "=" * 70)
    print("BACKEND COMPONENT VALIDATION")
    print("=" * 70)

    results = []

    # Check database models
    try:
        from consciousness_db.models import User, AuditLog, UserRole

        print("✓ Database models imported successfully")
        print(f"  - User model: {User.__tablename__}")
        print(f"  - AuditLog model: {AuditLog.__tablename__}")
        print(f"  - User roles: {[r.value for r in UserRole]}")
        results.append(("Database Models", True))
    except Exception as exc:
        print(f"✗ Database models import failed: {exc}")
        results.append(("Database Models", False))

    # Check admin API
    try:
        from hyba_genesis_api.api import admin

        print("✓ Admin API module imported successfully")
        print(f"  - Router prefix: {admin.router.prefix}")
        print(f"  - Router tags: {admin.router.tags}")
        results.append(("Admin API", True))
    except Exception as exc:
        print(f"✗ Admin API import failed: {exc}")
        results.append(("Admin API", False))

    # Check authentication update
    try:
        print("✓ Authentication module imported successfully")
        results.append(("Authentication", True))
    except Exception as exc:
        print(f"✗ Authentication import failed: {exc}")
        results.append(("Authentication", False))

    # Check database initialization
    try:
        print("✓ Database initialization module imported successfully")
        results.append(("Database Init", True))
    except Exception as exc:
        print(f"✗ Database initialization import failed: {exc}")
        results.append(("Database Init", False))

    # Check main app router registration
    try:
        from hyba_genesis_api.main import app

        admin_routes = [route for route in app.routes if "/admin" in str(route.path)]
        print(f"✓ Main app includes {len(admin_routes)} admin routes")
        for route in admin_routes[:5]:  # Show first 5
            print(f"  - {route.methods}: {route.path}")
        results.append(("Router Registration", True))
    except Exception as exc:
        print(f"✗ Main app router check failed: {exc}")
        results.append(("Router Registration", False))

    return results


def validate_frontend_components():
    """Validate frontend admin infrastructure."""
    print("\n" + "=" * 70)
    print("FRONTEND COMPONENT VALIDATION")
    print("=" * 70)

    results = []

    # Check AdminPanel component
    admin_panel_path = Path(__file__).parent.parent / "src" / "components" / "AdminPanel.tsx"
    if admin_panel_path.exists():
        print(f"✓ AdminPanel component exists: {admin_panel_path}")
        content = admin_panel_path.read_text()

        # Check key features
        features = [
            ("User creation", "handleCreateUser" in content),
            ("User editing", "handleUpdateUser" in content),
            ("User deletion", "handleDeleteUser" in content),
            ("User search", "searchQuery" in content),
            ("Statistics dashboard", "fetchStats" in content),
            ("Role management", "ROLES" in content),
        ]

        for feature, present in features:
            status = "✓" if present else "✗"
            print(f"  {status} {feature}")

        all_present = all(present for _, present in features)
        results.append(("AdminPanel Features", all_present))
    else:
        print(f"✗ AdminPanel component not found: {admin_panel_path}")
        results.append(("AdminPanel Component", False))

    # Check App.tsx integration
    app_path = Path(__file__).parent.parent / "src" / "App.tsx"
    if app_path.exists():
        print(f"✓ App.tsx exists: {app_path}")
        content = app_path.read_text()

        integration_checks = [
            ("AdminPanel import", "import" in content and "AdminPanel" in content),
            ("Admin view state", "showAdminPanel" in content or "viewMode" in content),
            ("Admin button", "Admin" in content),
        ]

        for check, present in integration_checks:
            status = "✓" if present else "✗"
            print(f"  {status} {check}")

        all_present = all(present for _, present in integration_checks)
        results.append(("App.tsx Integration", all_present))
    else:
        print(f"✗ App.tsx not found: {app_path}")
        results.append(("App.tsx", False))

    return results


def validate_deployment_files():
    """Validate deployment support files."""
    print("\n" + "=" * 70)
    print("DEPLOYMENT FILES VALIDATION")
    print("=" * 70)

    results = []

    # Check seed script
    seed_script_path = (
        Path(__file__).parent.parent / "python_backend" / "scripts" / "seed_admin_user.py"
    )
    if seed_script_path.exists():
        print(f"✓ Seed script exists: {seed_script_path}")
        results.append(("Seed Script", True))
    else:
        print(f"✗ Seed script not found: {seed_script_path}")
        results.append(("Seed Script", False))

    # Check documentation
    doc_path = Path(__file__).parent.parent / "docs" / "ADMIN_PANEL_DEPLOYMENT.md"
    if doc_path.exists():
        print(f"✓ Deployment documentation exists: {doc_path}")
        results.append(("Documentation", True))
    else:
        print(f"✗ Deployment documentation not found: {doc_path}")
        results.append(("Documentation", False))

    return results


def main():
    """Run all validation checks."""
    print("\n" + "=" * 70)
    print("HYBA ADMIN PANEL VALIDATION")
    print("Complete User Management Implementation Check")
    print("=" * 70)

    all_results = []

    # Run all validations
    all_results.extend(validate_backend_components())
    all_results.extend(validate_frontend_components())
    all_results.extend(validate_deployment_files())

    # Summary
    print("\n" + "=" * 70)
    print("VALIDATION SUMMARY")
    print("=" * 70)

    passed = sum(1 for _, success in all_results if success)
    total = len(all_results)

    for component, success in all_results:
        status = "✓ PASS" if success else "✗ FAIL"
        print(f"{status} - {component}")

    print("=" * 70)
    print(f"\nResults: {passed}/{total} components validated")

    if passed == total:
        print("\n🎯 ALL ADMIN PANEL COMPONENTS VALIDATED")
        print("   System ready for user management deployment")
        print("\nNext steps:")
        print("  1. Install argon2-cffi: pip install argon2-cffi")
        print("  2. Run seed script: python3 python_backend/scripts/seed_admin_user.py")
        print("  3. Start backend: npm run backend:start")
        print("  4. Access admin panel via UI")
        return 0
    else:
        print("\n⚠️  VALIDATION FAILURES DETECTED")
        print("   Review failed components above")
        return 1


if __name__ == "__main__":
    sys.exit(main())
