#!/usr/bin/env python3
"""
Orphaned Code Scanner

Identifies standalone implementations that aren't integrated into the system.
Everything should be imported and used - no orphaned modules.
"""

import ast
import os
from pathlib import Path
from typing import Dict, List, Set, Tuple
from collections import defaultdict


class OrphanedCodeScanner:
    def __init__(self, root_dir: str):
        self.root = Path(root_dir)
        self.python_backend = self.root / "python_backend"
        self.imports: Dict[str, Set[str]] = defaultdict(set)
        self.definitions: Dict[str, Set[str]] = defaultdict(set)

    def scan(self) -> Dict[str, List[str]]:
        """Scan for orphaned code."""
        print("🔍 Scanning for orphaned code...\n")

        # Collect all Python files
        py_files = list(self.python_backend.rglob("*.py"))

        # Parse imports and definitions
        for py_file in py_files:
            if "__pycache__" in str(py_file) or "venv" in str(py_file):
                continue
            self._parse_file(py_file)

        # Find orphans
        orphans = {
            "unused_modules": self._find_unused_modules(),
            "unused_classes": self._find_unused_definitions("class"),
            "unused_functions": self._find_unused_definitions("function"),
            "standalone_scripts": self._find_standalone_scripts(),
        }

        return orphans

    def _parse_file(self, filepath: Path):
        """Parse Python file for imports and definitions."""
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                tree = ast.parse(f.read(), filename=str(filepath))

            rel_path = str(filepath.relative_to(self.python_backend))

            # Collect imports
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        self.imports[rel_path].add(alias.name)
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        self.imports[rel_path].add(node.module)
                        for alias in node.names:
                            self.imports[rel_path].add(f"{node.module}.{alias.name}")

            # Collect definitions
            for node in ast.iter_child_nodes(tree):
                if isinstance(node, ast.ClassDef):
                    self.definitions[rel_path].add(f"class:{node.name}")
                elif isinstance(node, ast.FunctionDef):
                    self.definitions[rel_path].add(f"function:{node.name}")

        except Exception as e:
            pass

    def _find_unused_modules(self) -> List[str]:
        """Find modules that are never imported."""
        all_files = set(self.definitions.keys())
        imported_modules = set()

        for imports in self.imports.values():
            for imp in imports:
                # Convert import to file path
                parts = imp.split(".")
                for i in range(len(parts)):
                    potential = "/".join(parts[: i + 1]) + ".py"
                    imported_modules.add(potential)

        # Exclude main entry points and __init__ files
        excluded = {"main.py", "__init__.py", "wsgi.py", "asgi.py"}

        unused = []
        for file in all_files:
            basename = os.path.basename(file)
            if basename not in excluded and file not in imported_modules:
                # Check if any definition from this file is imported
                is_used = False
                for imports in self.imports.values():
                    for imp in imports:
                        if file.replace(".py", "").replace("/", ".") in imp:
                            is_used = True
                            break
                    if is_used:
                        break

                if not is_used:
                    unused.append(file)

        return sorted(unused)

    def _find_unused_definitions(self, def_type: str) -> List[Tuple[str, str]]:
        """Find classes/functions that are never imported."""
        all_defs = []
        for file, defs in self.definitions.items():
            for d in defs:
                if d.startswith(f"{def_type}:"):
                    all_defs.append((file, d.split(":")[1]))

        imported_names = set()
        for imports in self.imports.values():
            for imp in imports:
                if "." in imp:
                    imported_names.add(imp.split(".")[-1])

        unused = []
        for file, name in all_defs:
            if name not in imported_names and not name.startswith("_"):
                unused.append((file, name))

        return sorted(unused)[:20]  # Limit output

    def _find_standalone_scripts(self) -> List[str]:
        """Find standalone scripts with if __name__ == '__main__' but not in scripts/."""
        standalone = []

        for py_file in self.python_backend.rglob("*.py"):
            if "__pycache__" in str(py_file) or "scripts" in str(py_file):
                continue

            try:
                with open(py_file, "r", encoding="utf-8") as f:
                    content = f.read()
                    if (
                        'if __name__ == "__main__"' in content
                        or "if __name__ == '__main__'" in content
                    ):
                        rel_path = str(py_file.relative_to(self.python_backend))
                        standalone.append(rel_path)
            except:
                pass

        return sorted(standalone)

    def report(self, orphans: Dict[str, List]):
        """Print orphaned code report."""
        print("=" * 80)
        print("ORPHANED CODE SCAN REPORT")
        print("=" * 80)

        # Unused modules
        print(f"\n🗂️  UNUSED MODULES ({len(orphans['unused_modules'])} found):")
        if orphans["unused_modules"]:
            for mod in orphans["unused_modules"]:
                print(f"   ❌ {mod}")
        else:
            print("   ✅ No unused modules found")

        # Unused classes
        print(
            f"\n🏗️  POTENTIALLY UNUSED CLASSES ({len(orphans['unused_classes'])} found, showing top 20):"
        )
        if orphans["unused_classes"]:
            for file, name in orphans["unused_classes"]:
                print(f"   ❌ {name} in {file}")
        else:
            print("   ✅ No unused classes found")

        # Unused functions
        print(
            f"\n⚙️  POTENTIALLY UNUSED FUNCTIONS ({len(orphans['unused_functions'])} found, showing top 20):"
        )
        if orphans["unused_functions"]:
            for file, name in orphans["unused_functions"]:
                print(f"   ❌ {name} in {file}")
        else:
            print("   ✅ No unused functions found")

        # Standalone scripts
        print(f"\n📜 STANDALONE SCRIPTS ({len(orphans['standalone_scripts'])} found):")
        if orphans["standalone_scripts"]:
            for script in orphans["standalone_scripts"]:
                print(f"   ⚠️  {script}")
        else:
            print("   ✅ No standalone scripts outside scripts/")

        print("\n" + "=" * 80)

        # Special check for billing_rollback.py
        if any("billing_rollback.py" in mod for mod in orphans["unused_modules"]):
            print("\n⚠️  ALERT: billing_rollback.py appears to be ORPHANED")
            print(
                "   This module defines BillingRollbackManager but is never imported."
            )
            print("   Action required: Integrate or remove.\n")


def main():
    root = Path(__file__).parent.parent
    scanner = OrphanedCodeScanner(str(root))
    orphans = scanner.scan()
    scanner.report(orphans)

    # Return exit code based on findings
    total_orphans = (
        len(orphans["unused_modules"])
        + len(orphans["unused_classes"])
        + len(orphans["standalone_scripts"])
    )

    if total_orphans > 0:
        print(f"\n❌ Found {total_orphans} potential orphaned code issues")
        return 1
    else:
        print("\n✅ No orphaned code detected - all implementations are integrated")
        return 0


if __name__ == "__main__":
    exit(main())
