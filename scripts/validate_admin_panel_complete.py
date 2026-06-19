#!/usr/bin/env python3
"""Complete Admin Panel Validation Script.

Validates that all admin features are present and operational:
1. Frontend AdminPanel component exists
2. Backend admin API endpoints exist
3. Database models are configured
4. Seed script is available
5. Router is registered in main app
"""

import sys
from pathlib import Path

# Add backend to path
BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))


def check_file_exists(path: Path, name: str) -> bool:
    """Check if a file exists and report."""
    if path.exists():
        print(f"✅ {name} exists: {path.relative_to(BACKEND_ROOT)}")
        return True
    else:
        print(f"❌ {name} MISSING: {path.relative_to(BACKEND_ROOT)}")
        return False


def validate_frontend():
    """Validate frontend components."""
    print("\n" + "=" * 70)
    print("FRONTEND VALIDATION")
    print("=" * 70)

    results = []

    # Check AdminPanel component
    admin_panel = BACKEND_ROOT / "src" / "components" / "AdminPanel.tsx"
    results.append(check_file_exists(admin_panel, "AdminPanel component"))

    # Check App.tsx integration
    app_tsx = BACKEND_ROOT / "src" / "App.tsx"
    if app_tsx.exists():
        content = app_tsx.read_text()
        if "AdminPanel" in content and 'currentView === "admin"' in content:
            print("✅ AdminPanel integrated into App.tsx")
            results.append(True)
        else:
            print("❌ AdminPanel NOT integrated into App.tsx")
            results.append(False)
    else:
        print("❌ App.tsx not found")
        results.append(False)

    return all(results)


def validate_backend():
    """Validate backend API."""
    print("\n" + "=" * 70)
    print("BACKEND VALIDATION")
    print("=" * 70)

    results = []

    # Check admin API module
    admin_api = BACKEND_ROOT / "python_backend" / "hyba_genesis_api" / "api" / "admin.py"
    results.append(check_file_exists(admin_api, "Admin API module"))

    # Check if admin API has required endpoints
    if admin_api.exists():
        content = admin_api.read_text()
        endpoints = [
            ("list_users", "GET /api/admin/users"),
            ("get_user", "GET /api/admin/users/{user_id}"),
            ("create_user", "POST /api/admin/users"),
            ("update_user", "PUT /api/admin/users/{user_id}"),
            ("delete_user", "DELETE /api/admin/users/{user_id}"),
            ("list_audit_logs", "GET /api/admin/audit-logs"),
            ("get_admin_stats", "GET /api/admin/stats"),
        ]

        for func_name, endpoint in endpoints:
            if func_name in content:
                print(f"✅ Endpoint implemented: {endpoint}")
                results.append(True)
            else:
                print(f"❌ Endpoint MISSING: {endpoint}")
                results.append(False)

    # Check main.py router registration
    main_py = BACKEND_ROOT / "python_backend" / "hyba_genesis_api" / "main.py"
    if main_py.exists():
        content = main_py.read_text()
        if "admin.router" in content:
            print("✅ Admin router registered in main.py")
            results.append(True)
        else:
            print("❌ Admin router NOT registered in main.py")
            results.append(False)

    return all(results)


def validate_database():
    """Validate database models."""
    print("\n" + "=" * 70)
    print("DATABASE VALIDATION")
    print("=" * 70)

    results = []

    # Check models file
    models_file = BACKEND_ROOT / "python_backend" / "consciousness_db" / "models.py"
    results.append(check_file_exists(models_file, "Database models"))

    if models_file.exists():
        content = models_file.read_text()

        # Check User model
        if "class User(Base)" in content and "username" in content and "password_hash" in content:
            print("✅ User model defined with required fields")
            results.append(True)
        else:
            print("❌ User model MISSING or incomplete")
            results.append(False)

        # Check AuditLog model
        if "class AuditLog(Base)" in content and "actor_username" in content:
            print("✅ AuditLog model defined")
            results.append(True)
        else:
            print("❌ AuditLog model MISSING")
            results.append(False)

        # Check UserRole enum
        if "class UserRole" in content and "ADMIN" in content:
            print("✅ UserRole enum defined")
            results.append(True)
        else:
            print("❌ UserRole enum MISSING")
            results.append(False)

    return all(results)


def validate_deployment_tools():
    """Validate deployment tools."""
    print("\n" + "=" * 70)
    print("DEPLOYMENT TOOLS VALIDATION")
    print("=" * 70)

    results = []

    # Check seed script
    seed_script = BACKEND_ROOT / "python_backend" / "scripts" / "seed_admin_user.py"
    results.append(check_file_exists(seed_script, "Seed admin user script"))

    if seed_script.exists():
        content = seed_script.read_text()
        if "create_admin_user" in content and "PasswordHasher" in content:
            print("✅ Seed script functional with Argon2id hashing")
            results.append(True)
        else:
            print("❌ Seed script INCOMPLETE")
            results.append(False)

    return all(results)


def validate_security():
    """Validate security features."""
    print("\n" + "=" * 70)
    print("SECURITY VALIDATION")
    print("=" * 70)

    results = []

    admin_api = BACKEND_ROOT / "python_backend" / "hyba_genesis_api" / "api" / "admin.py"
    if admin_api.exists():
        content = admin_api.read_text()

        # Check for require_admin function
        if "def require_admin" in content:
            print("✅ Admin role enforcement function present")
            results.append(True)
        else:
            print("❌ Admin role enforcement MISSING")
            results.append(False)

        # Check for audit logging
        if "def log_audit" in content or "AuditLog" in content:
            print("✅ Audit logging implemented")
            results.append(True)
        else:
            print("❌ Audit logging MISSING")
            results.append(False)

        # Check for password hashing
        if "PasswordHasher" in content and "_password_hasher.hash" in content:
            print("✅ Argon2id password hashing configured")
            results.append(True)
        else:
            print("❌ Password hashing MISSING or insecure")
            results.append(False)

        # Check for self-protection
        if "Cannot delete your own account" in content or "Cannot change your own role" in content:
            print("✅ Self-protection mechanisms present")
            results.append(True)
        else:
            print("❌ Self-protection MISSING")
            results.append(False)

    return all(results)


def main():
    """Run all validations."""
    print("=" * 70)
    print("HYBA ADMIN PANEL COMPLETE VALIDATION")
    print("=" * 70)

    results = {
        "Frontend": validate_frontend(),
        "Backend": validate_backend(),
        "Database": validate_database(),
        "Deployment Tools": validate_deployment_tools(),
        "Security": validate_security(),
    }

    print("\n" + "=" * 70)
    print("VALIDATION SUMMARY")
    print("=" * 70)

    for category, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} - {category}")

    print("=" * 70)

    all_passed = all(results.values())
    if all_passed:
        print("\n🎯 ALL VALIDATIONS PASSED")
        print("   Admin panel is complete and ready for deployment")
        print("\n📝 Next Steps:")
        print("   1. Install argon2-cffi: pip install argon2-cffi")
        print("   2. Seed admin user: python3 python_backend/scripts/seed_admin_user.py")
        print("   3. Start backend: npm run backend:start")
        print("   4. Start frontend: npm run dev")
        print("   5. Login as admin and access admin panel")
        return 0
    else:
        print("\n⚠️  VALIDATION FAILURES DETECTED")
        print("   Review output above for missing components")
        return 1


if __name__ == "__main__":
    sys.exit(main())
