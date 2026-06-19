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


def test_setup_and_start_runs_bootstrap_and_gate_before_runtime_processes() -> None:
    script = (ROOT / "scripts" / "setup_and_start.sh").read_text(encoding="utf-8")

    bootstrap_call_index = script.index("run_pythia_bootstrap", script.index("main()"))
    gate_call_index = script.index("run_sovereign_gate", script.index("main()"))
    backend_index = script.index("Starting FastAPI backend")
    frontend_index = script.index("Starting frontend/bridge")

    assert bootstrap_call_index < gate_call_index < backend_index < frontend_index
    assert "python scripts/pythia_autonomous_bootstrap.py" in script
    assert "pythia_autonomous_bootstrap.json" in script
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


def test_pythia_bootstrap_script_records_self_healing_and_self_optimising_evidence() -> None:
    script = (ROOT / "scripts" / "pythia_autonomous_bootstrap.py").read_text(encoding="utf-8")

    assert any(
        tag in script
        for tag in ["HYBA_PYTHIA_AUTONOMOUS_BOOTSTRAP_V1", "HYBA_PYTHIA_AUTONOMOUS_BOOTSTRAP_V2"]
    )
    assert "controller.set_autonomy_level(level)" in script
    assert "await controller.seek_improvement()" in script
    assert "stale_state_lock_recoveries" in script
    assert "degradation_events" in script
    assert "reflexive_cycle_count" in script
    assert "proposal_acceptance_rate" in script
