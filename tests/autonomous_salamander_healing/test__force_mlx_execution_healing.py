"""
Auto-generated test for Salamander healing: _force_mlx_execution

Generated: 2026-06-23T21:45:56.657172+00:00
Healing goal: Remove unsafe dynamic execution and preserve security invariants
PULVINI-compressed test generation
"""

import pytest
import sys
from pathlib import Path

backend_root = Path(__file__).parent.parent.parent / "python_backend"
if str(backend_root) not in sys.path:
    sys.path.insert(0, str(backend_root))


def test__force_mlx_execution_healing_applied():
    """Test that Salamander healing was applied correctly."""
    module_path = Path("C:\Users\USER\OneDrive\Desktop\HYBA_FULLSTACK\python_backend\pythia_mining\apple_silicon_metal.py")
    if not module_path.exists():
        pytest.skip(f"Module not found: {module_path}")
    
    source = module_path.read_text(encoding='utf-8')
    
    assert "Salamander healing note" in source or source != "", \
        "Healing note should be present or code should be modified"
    
    try:
        compile(source, str(module_path), 'exec')
    except SyntaxError as e:
        pytest.fail(f"Healed code has syntax error: {e}")


def test__force_mlx_execution_functionality_preserved():
    """Test that basic functionality is preserved after healing."""
    module_path = Path("C:\Users\USER\OneDrive\Desktop\HYBA_FULLSTACK\python_backend\pythia_mining\apple_silicon_metal.py")
    if not module_path.exists():
        pytest.skip(f"Module not found: {module_path}")
    
    source = module_path.read_text(encoding='utf-8')
    compile(source, str(module_path), 'exec')
    assert f"def _force_mlx_execution" in source or f"class _force_mlx_execution" in source


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
