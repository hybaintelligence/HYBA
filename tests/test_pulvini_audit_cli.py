import json
import subprocess
import sys

from pythia_mining.pulvini_elevation import (
    CertificateLedger,
    StaticMathProvider,
    TelemetryContract,
)


def test_pulvini_audit_cli_verifies_dependency_free_ledger(tmp_path):
    ledger = CertificateLedger()
    report = StaticMathProvider().invariant_report(
        {"trace": 1.0, "purity": 1.0}, stage="cli_test"
    )
    invariant_entry = ledger.append(
        "kernel_invariant", {"report": report.to_dict()}, timestamp_ns=1
    )
    passport = TelemetryContract().runtime_passport(
        "static_kernel",
        {"phi": 0.5, "bures": 0.0, "purity": 1.0},
        report,
        invariant_entry,
    )
    ledger.append("runtime_passport", {"passport": passport.to_dict()}, timestamp_ns=2)
    ledger_path = tmp_path / "ledger.bin"
    ledger_path.write_bytes(ledger.to_bytes())

    completed = subprocess.run(
        [sys.executable, "scripts/pulvini_audit.py", str(ledger_path), "--json"],
        check=True,
        capture_output=True,
        text=True,
    )
    payload = json.loads(completed.stdout)

    assert payload["passed"] is True
    assert payload["chain_verified"] is True
    assert payload["failed_passport_count"] == 0
    assert payload["mathematical_exception_count"] == 0


def test_pulvini_audit_cli_emits_consensus_for_multiple_ledgers(tmp_path):
    paths = []
    for index in range(2):
        ledger = CertificateLedger()
        ledger.append(
            "node_health", {"node": index, "healthy": True}, timestamp_ns=index + 1
        )
        path = tmp_path / f"ledger-{index}.bin"
        path.write_bytes(ledger.to_bytes())
        paths.append(path)

    completed = subprocess.run(
        [
            sys.executable,
            "scripts/pulvini_audit.py",
            str(paths[0]),
            str(paths[1]),
            "--json",
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    payload = json.loads(completed.stdout)

    assert payload["passed"] is True
    assert payload["consensus"]["node_count"] == 2
    assert payload["consensus"]["verified_node_count"] == 2


def test_generate_pulvini_manifest_ci_script_writes_dependency_free_manifest(tmp_path):
    output = tmp_path / "manifest.json"
    completed = subprocess.run(
        [
            sys.executable,
            "scripts/generate_pulvini_manifest.py",
            "--output",
            str(output),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    manifest = json.loads(output.read_text())

    assert str(output) in completed.stdout
    assert manifest["version"] == "PULVINI_RUNTIME_MANIFEST_V1"
    assert manifest["module_versions"]["operator"] == "BUILD_OPERATOR_STUB_V1"
    assert manifest["certificate_ledger_root_hash"] != "0" * 64
