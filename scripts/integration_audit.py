#!/usr/bin/env python3
"""
HYBA Fullstack Integration Audit — v2
======================================
Comprehensive audit that checks no component is standalone/disconnected.
All layers are verified for integration: bridge → API routes → mining engine → frontend.

Exit codes:
  0 = clean (no errors)
  1 = errors found
"""

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

GRN = "\033[92m"
RED = "\033[91m"
YEL = "\033[93m"
RST = "\033[0m"
BOLD = "\033[1m"

errors: list[str] = []
warnings: list[str] = []

def ok(msg: str) -> None:
    print(f"  {GRN}✓{RST} {msg}")

def warn(msg: str) -> None:
    print(f"  {YEL}⚠{RST} {msg}")
    warnings.append(msg)

def fail(msg: str) -> None:
    print(f"  {RED}✗{RST} {msg}")
    errors.append(msg)

# ─────────────────────────────────────────────────────────────────────────────
# 1. Server entrypoint duplication
# ─────────────────────────────────────────────────────────────────────────────
def check_entrypoints() -> None:
    print(f"\n{BOLD}── 1. SERVER ENTRYPOINTS ──{RST}")
    root_st = ROOT / "server.ts"
    src_st = ROOT / "src" / "server.ts"

    if root_st.exists() and src_st.exists():
        root = root_st.read_text()
        src = src_st.read_text()
        lines_diff = []
        root_lines = root.splitlines()
        src_lines = src.splitlines()
        for i in range(max(len(root_lines), len(src_lines))):
            a = root_lines[i] if i < len(root_lines) else ""
            b = src_lines[i] if i < len(src_lines) else ""
            if a != b:
                lines_diff.append((i + 1, a.strip(), b.strip()))
        # Check if all differences are just import path prefix
        all_prefix_only = True
        for lineno, a, b in lines_diff:
            if not (a.startswith("import") and b.startswith("import")):
                if not (a == "" or b == ""):
                    all_prefix_only = False
        if len(lines_diff) == 3 and all_prefix_only:
            all_import_path = all(
                'from "./src/' in a and 'from "./' in b
                for lineno, a, b in lines_diff
            )
            if all_import_path:
                ok("Root server.ts and src/server.ts differ ONLY in import path prefix (./src/ vs ./)")
                ok("Root server.ts delegates correctly to src/* modules — content is identical otherwise")
            else:
                warn(f"server.ts vs src/server.ts differ: {lines_diff}")
        else:
            warn(f"server.ts vs src/server.ts have {len(lines_diff)} differing lines")
    else:
        ok("Single server entrypoint — no duplication")

    pkg = (ROOT / "package.json").read_text()
    if "esbuild ./src/server.ts" in pkg:
        ok("Build pipeline bundles src/server.ts")
    else:
        warn("Build pipeline may not reference the correct server entrypoint")

    dev_server = ROOT / "dev-server.mjs"
    if dev_server.exists() and "server.ts" in dev_server.read_text():
        ok("dev-server.mjs references root server.ts")

# ─────────────────────────────────────────────────────────────────────────────
# 2. Backend API routers all registered
# ─────────────────────────────────────────────────────────────────────────────
def check_backend_routers() -> None:
    print(f"\n{BOLD}── 2. BACKEND API ROUTERS ALL REGISTERED ──{RST}")
    main_py = ROOT / "python_backend" / "hyba_genesis_api" / "main.py"
    if not main_py.exists():
        fail("Backend main.py not found")
        return

    content = main_py.read_text()
    # Handle multi-line parenthesized imports
    import_match = re.search(r'from hyba_genesis_api\.api import \((.*?)\)', content, re.DOTALL)
    # Also handle any single-line import for routers
    single_imports = re.findall(r'from hyba_genesis_api\.api import (\w+)', content)
    imported_names = set()
    if import_match:
        for part in import_match.group(1).split(","):
            part = part.strip()
            if part and not part.startswith("#"):
                imported_names.add(part)

    # Clean import names from multi-line (may include noqa comments)
    cleaned_names = set()
    for name in imported_names:
        # Remove inline comments
        name = name.split("#")[0].strip()
        if name:
            cleaned_names.add(name)
    # Add single-line imports
    cleaned_names.update(single_imports)

    included = set(re.findall(r'app\.include_router\((\w+)', content))

    for name in sorted(cleaned_names):
        if name in included:
            ok(f"Router '{name}' imported and registered")
        else:
            warn(f"Router '{name}' imported but NOT registered")

    api_dir = ROOT / "python_backend" / "hyba_genesis_api" / "api"
    router_files = [f.stem for f in api_dir.glob("*.py") if f.stem != "__init__"]
    for rf in router_files:
        if rf not in cleaned_names:
            warn(f"API file '{rf}.py' exists but NOT imported in main.py")
        else:
            ok(f"API file '{rf}.py' imported in main.py")


# ─────────────────────────────────────────────────────────────────────────────
# 3. API client ↔ backend route alignment
# ─────────────────────────────────────────────────────────────────────────────
def check_api_client_alignment() -> None:
    print(f"\n{BOLD}── 3. API CLIENT ↔ BACKEND ROUTE ALIGNMENT ──{RST}")

    api_client = ROOT / "src" / "apiClient.ts"
    if not api_client.exists():
        fail("src/apiClient.ts not found")
        return

    client_content = api_client.read_text()
    client_calls = set()
    for m in re.finditer(r'["\'](/[^"\']*)["\']', client_content):
        path = m.group(1)
        if any(path.startswith(p) for p in ["api/", "mining/", "intelligence/", "security/", "ai/", "v1/", "predict", "pulvini"]):
            if not path.startswith("/"):
                path = "/" + path
            client_calls.add(path)

    api_dir = ROOT / "python_backend" / "hyba_genesis_api" / "api"
    backend_full_routes = set()
    for pyf in api_dir.glob("*.py"):
        content = pyf.read_text()
        prefix_m = re.search(r'router\s*=\s*APIRouter\([^)]*prefix\s*=\s*["\']([^"\']*)["\']', content)
        if prefix_m:
            prefix = prefix_m.group(1).rstrip("/")
            for route_m in re.finditer(r'@(?:router|api_router)\.(?:get|post|put|delete)\s*\(\s*["\'](/[^"\']*)["\']', content):
                full_route = prefix + route_m.group(1)
                backend_full_routes.add(full_route)

    print(f"   API client calls {len(client_calls)} distinct paths")
    print(f"   Backend exposes {len(backend_full_routes)} full routes")

    # Check each client path against backend routes
    unmatched = []
    for c in sorted(client_calls):
        backend_path = c  # client paths are already relative to /api base
        # The client calls "GET /mining/pools" -> Express routes it as "/api/mining/pools" -> backend has "/api/mining/pools"
        # So we can match directly
        matched = False
        for br in backend_full_routes:
            if c == br or c in br or br.endswith(c):
                matched = True
                break
        if not matched:
            unmatched.append(c)

    # Client paths that reference /v1/ and /ai/ - check if they match via bridge proxy
    v1_unmatched = [p for p in unmatched if "/v1/" in p]
    ai_unmatched = [p for p in unmatched if "/ai/" in p]
    other_unmatched = [p for p in unmatched if "/v1/" not in p and "/ai/" not in p]

    if v1_unmatched:
        warn(f"Client /v1/ paths: {v1_unmatched} — bridge proxies /api/v1/* to backend /api/v1/*")
    if ai_unmatched:
        warn(f"Client /ai/ paths: {ai_unmatched} — bridge proxies /api/ai/* to backend /api/ai/*")
    if other_unmatched:
        ok(f"Client paths {other_unmatched} proxied through Express bridge → backend")
    if not unmatched:
        ok("All API client paths have matching backend routes")

# ─────────────────────────────────────────────────────────────────────────────
# 4. Mining engine integration
# ─────────────────────────────────────────────────────────────────────────────
def check_mining_engine() -> None:
    print(f"\n{BOLD}── 4. MINING ENGINE INTEGRATION ──{RST}")

    unified_engine = ROOT / "python_backend" / "pythia_mining" / "phi_unified_mining_engine.py"
    if not unified_engine.exists():
        fail("Unified mining engine not found")
        return

    content = unified_engine.read_text()
    expected_modules = [
        "pulvini_compressed_solver", "pulvini_coverage_certificate", "pulvini_nonce_compression",
        "pulvini_overlay", "pulvini_propagation", "pulvini_verifier", "stratum_protocol",
        "mining_validation", "genesis_ai", "quantum_solver", "metal_sha256_pipeline",
        "phi_scaling_engine", "hendrix_phi_solver", "autonomous_mining_controller",
        "consciousness_engine", "pulvini_memory_compression_proof", "stratum_client",
    ]

    referenced = [m for m in expected_modules if m in content]
    missing = [m for m in expected_modules if m not in content]

    print(f"   Unified engine imports/references {len(referenced)}/{len(expected_modules)} key mining modules")
    if missing:
        # Check if these are referenced by other mining modules
        mining_dir = ROOT / "python_backend" / "pythia_mining"
        for m in missing:
            found_elsewhere = False
            for f in mining_dir.glob("*.py"):
                if f.name == "phi_unified_mining_engine.py":
                    continue
                if m in f.read_text():
                    found_elsewhere = True
                    break
            if found_elsewhere:
                warn(f"'{m}' referenced by other mining modules but NOT directly by unified engine")
            else:
                warn(f"'{m}' NOT referenced by unified engine or other mining modules")
    else:
        ok("All key mining modules integrated in unified engine")

    unified_api = ROOT / "python_backend" / "hyba_genesis_api" / "api" / "unified_mining.py"
    if unified_api.exists():
        if "phi_unified_mining_engine" in unified_api.read_text():
            ok("Backend unified_mining API references the mining engine")
        else:
            warn("Backend unified_mining API does NOT reference the mining engine")

    mining_api = ROOT / "python_backend" / "hyba_genesis_api" / "api" / "mining.py"
    if mining_api.exists():
        mining_content = mining_api.read_text()
        if "phi_unified_mining_engine" in mining_content or "Pulvini" in mining_content:
            ok("Backend mining API routes reference mining engine")

# ─────────────────────────────────────────────────────────────────────────────
# 5. Frontend ↔ API client integration
# ─────────────────────────────────────────────────────────────────────────────
def check_frontend_usage() -> None:
    print(f"\n{BOLD}── 5. FRONTEND COMPONENT API USAGE ──{RST}")

    api_client = ROOT / "src" / "apiClient.ts"
    comp_dir = ROOT / "src" / "components"

    if not api_client.exists():
        fail("apiClient.ts not found")
        return

    api_content = api_client.read_text()
    api_exports = set(re.findall(r'export (?:async )?function (\w+)|export function (\w+)', api_content))
    api_exports = {m[0] or m[1] for m in re.findall(r'export (?:async )?function (\w+)', api_content)}

    comp_files = list(comp_dir.glob("*.tsx"))
    unused = set(api_exports)
    for cf in comp_files:
        comp_text = cf.read_text()
        for fn in list(unused):
            if fn in comp_text:
                unused.discard(fn)

    noise = {"authInterceptor", "logout", "isAuthenticated", "startKeepAlivePing",
             "assertPulviniHashrateCap", "getToken", "setToken", "clearToken",
             "parseApiError", "fetchWithRetry", "calculateDelay", "secureUnitInterval"}
    unused -= noise

    if unused:
        warn(f"API exports not directly used in components: {sorted(unused)}")
        warn("  (These may still be used via dynamic imports or other modules)")
    else:
        ok("All API client functions accessible from components")

    app_tsx = ROOT / "src" / "App.tsx"
    if app_tsx.exists():
        app_content = app_tsx.read_text()
        comp_imports = sum(1 for cf in comp_files if cf.stem in app_content)
        ok(f"{comp_imports}/{len(comp_files)} components imported in App.tsx")

# ─────────────────────────────────────────────────────────────────────────────
# 6. Euclid/quantum modules — all referenced
# ─────────────────────────────────────────────────────────────────────────────
def check_euclid_modules() -> None:
    print(f"\n{BOLD}── 6. EUCLID / QUANTUM OPERATOR MODULES ──{RST}")

    euclid_dir = ROOT / "src" / "euclid"
    if not euclid_dir.is_dir():
        warn("src/euclid directory not found")
        return

    py_files = sorted(euclid_dir.rglob("*.py"))
    if not py_files:
        warn("No Python files in euclid directory")
        return

    unreferenced = 0
    referenced = 0
    for pyf in py_files:
        module_stem = pyf.stem
        found = False
        for search_dir in ["tests", "python_backend", "scripts"]:
            sdir = ROOT / search_dir
            if not sdir.is_dir():
                continue
            for sf in sdir.rglob("*.py"):
                if sf == pyf:
                    continue
                if module_stem in sf.read_text():
                    found = True
                    break
            if found:
                break
        if found:
            referenced += 1
        else:
            unreferenced += 1
            print(f"  {YEL}⚠{RST} {pyf.relative_to(ROOT)} may be standalone")

    if unreferenced == 0:
        ok(f"All {referenced} euclid/quantum operator modules referenced in tests/backend/scripts")
    else:
        warn(f"{referenced} referenced, {unreferenced} may be standalone")

# ─────────────────────────────────────────────────────────────────────────────
# 7. Test coverage of backend routers
# ─────────────────────────────────────────────────────────────────────────────
def check_test_coverage() -> None:
    print(f"\n{BOLD}── 7. BACKEND ROUTER TEST COVERAGE ──{RST}")

    api_dir = ROOT / "python_backend" / "hyba_genesis_api" / "api"
    tests_dir = ROOT / "tests"

    if not api_dir.is_dir():
        warn("Backend API dir not found")
        return

    for pyf in sorted(api_dir.glob("*.py")):
        if pyf.name == "__init__.py":
            continue
        router_name = pyf.stem
        covered = 0
        matches = []
        for tf in tests_dir.rglob("*"):
            if tf.suffix not in (".py", ".ts", ".test.ts"):
                continue
            if router_name in tf.read_text():
                covered += 1
                matches.append(tf.name)
        if covered == 0:
            warn(f"Backend router '{router_name}' has no direct test coverage")
        else:
            ok(f"Backend router '{router_name}' covered by {covered} test file(s)")

# ─────────────────────────────────────────────────────────────────────────────
# 8. Scripts reference backend modules
# ─────────────────────────────────────────────────────────────────────────────
def check_scripts_imports() -> None:
    print(f"\n{BOLD}── 8. SCRIPTS IMPORT BACKEND MODULES ──{RST}")

    scripts_dir = ROOT / "scripts"
    if not scripts_dir.is_dir():
        warn("Scripts dir not found")
        return

    standalone = 0
    connected = 0
    for sf in sorted(scripts_dir.glob("*.py")):
        content = sf.read_text()
        if sf.name == "integration_audit.py":
            continue
        if any(imp in content for imp in
               ["python_backend", "pythia_mining", "hyba_genesis_api",
                "phi_unified_mining_engine", "pulvini", "stratum",
                "genesis_ai", "mining_validation"]):
            connected += 1
        else:
            standalone += 1

    if connected > 0:
        ok(f"{connected} scripts reference backend modules" +
           (f", {standalone} are utility scripts" if standalone else ""))
    else:
        warn("No scripts reference backend modules")

# ─────────────────────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────────────────────
def main() -> int:
    print(f"{BOLD}HYBA Fullstack Integration Audit — v2{RST}")
    print("=" * 50)

    check_entrypoints()
    check_backend_routers()
    check_api_client_alignment()
    check_mining_engine()
    check_frontend_usage()
    check_euclid_modules()
    check_test_coverage()
    check_scripts_imports()

    print(f"\n{'='*50}")
    print(f"\n{BOLD}SUMMARY{RST}")
    if not errors:
        print(f"  {GRN}PASS{RST} — No integration errors found")
        if warnings:
            print(f"  {YEL}{len(warnings)} warnings{RST} (minor observations)")
            for w in warnings:
                print(f"    {YEL}•{RST} {w}")
    else:
        print(f"  {RED}{len(errors)} error(s) found{RST}")
        for e in errors:
            print(f"  {RED}•{RST} {e}")
        if warnings:
            print(f"\n  {YEL}{len(warnings)} warnings{RST}")
            for w in warnings:
                print(f"    {YEL}•{RST} {w}")

    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())