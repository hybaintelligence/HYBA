from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_setup_and_start_is_root_anchored_and_strict() -> None:
    script = (ROOT / "scripts" / "setup_and_start.sh").read_text(encoding="utf-8")

    assert "set -Eeuo pipefail" in script
    assert 'SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"' in script
    assert 'REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"' in script
    assert 'cd "${REPO_ROOT}"' in script
    assert 'if [[ ! -f "requirements.txt" || ! -f "package.json" || ! -d "python_backend" ]]' in script


def test_setup_and_start_runs_gate_before_runtime_processes() -> None:
    script = (ROOT / "scripts" / "setup_and_start.sh").read_text(encoding="utf-8")

    gate_index = script.index("run_sovereign_gate")
    backend_index = script.index("Starting FastAPI backend")
    frontend_index = script.index("Starting frontend/bridge")

    assert gate_index < backend_index < frontend_index
    assert "python scripts/mining_autonomous_sovereign_gate.py --mode" in script
    assert "Autonomous sovereign gate returned NO-GO" in script
    assert "Autonomous sovereign gate returned GO" in script


def test_setup_and_start_installs_reproducibly() -> None:
    script = (ROOT / "scripts" / "setup_and_start.sh").read_text(encoding="utf-8")

    assert "python -m pip install --upgrade pip setuptools wheel" in script
    assert "python -m pip install -r requirements.txt" in script
    assert "npm ci" in script
    assert "npm audit fix" not in script


def test_setup_and_start_proves_backend_and_frontend_bridge_health() -> None:
    script = (ROOT / "scripts" / "setup_and_start.sh").read_text(encoding="utf-8")

    assert "http://127.0.0.1:${BACKEND_PORT}/api/health/readiness" in script
    assert "http://127.0.0.1:${PORT}/bridge/health" in script
    assert "http://127.0.0.1:${PORT}/health" in script
    assert "Frontend bridge cannot reach backend health" in script


def test_dev_server_uses_repository_root_and_backend_url_contract() -> None:
    script = (ROOT / "scripts" / "dev-server.mjs").read_text(encoding="utf-8")

    assert "const projectRoot = path.resolve(scriptDir, '..');" in script
    assert "process.env.PULVINI_BACKEND_URL" in script
    assert "process.env.BACKEND_PORT" in script
    assert "app.use('/api'" in script
    assert "app.use('/health'" in script
    assert "fs: { strict: false, allow: [projectRoot] }" in script
