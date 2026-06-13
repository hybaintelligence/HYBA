import json

from pythia_mining.pulvini_elevation import (
    CertificateLedger,
    ElevationBridge,
    KernelSupervisor,
    MathematicalException,
    PhiHealthSupervisor,
    ProductionResponse,
    QuantumRuntimeManifestBuilder,
    StaticMathProvider,
    TelemetryContract,
)


class FakeOperator:
    VERSION = "FAKE_OPERATOR_V1"
    dim = 1

    def snapshot(self):
        return {"version": self.VERSION, "topology_gate_closed": True}

    def verify_topology(self):
        return {"gate_closed": True, "operator_version": self.VERSION}


class FakeVerifier:
    VERSION = "FAKE_VERIFIER_V1"

    def __init__(self, operator=None):
        self.operator = operator

    def verify_topology(self):
        return True

    def verify_passport(self, passport):
        return bool(passport.status == "verified" and not passport.quantum_speedup_claimed)

    def generate_passport(self, **_kwargs):
        return FakePassport()


class FakePassport:
    structural_hash = "a" * 64
    passport_hash = "b" * 64
    topology_verified = True
    coverage_verified = True
    grover_scope_verified = True
    quantum_speedup_claimed = False
    timestamp_ns = 99
    status = "verified"

    def to_dict(self):
        return {
            "structural_hash": self.structural_hash,
            "passport_hash": self.passport_hash,
            "topology_verified": self.topology_verified,
            "coverage_verified": self.coverage_verified,
            "grover_scope_verified": self.grover_scope_verified,
            "quantum_speedup_claimed": self.quantum_speedup_claimed,
            "timestamp_ns": self.timestamp_ns,
            "status": self.status,
        }


def _builder():
    operator = FakeOperator()
    return operator, FakeVerifier(operator), QuantumRuntimeManifestBuilder(operator, FakeVerifier(operator))


def test_runtime_manifest_contains_regulatory_elevation_artifacts_without_numpy():
    _operator, _verifier, builder = _builder()
    ledger = CertificateLedger()
    passport = FakePassport()
    ledger.append("substate_passport", passport.to_dict(), timestamp_ns=456)

    manifest = builder.build(ledger, {"trace": 1.0, "purity": 1.0, "min_eigenvalue": 0.0})

    assert manifest["version"] == "PULVINI_RUNTIME_MANIFEST_V1"
    assert manifest["capability_manifest"]["capability_flags"]["supports_certificate_ledger"] is True
    assert manifest["certificate_ledger_root_hash"] == ledger.root_hash
    assert manifest["kernel_invariants"]["closed"] is True
    assert manifest["compliance"]["quantum_speedup_claimed"] is False
    assert manifest["runtime_manifest_hash"]
    json.dumps(manifest, sort_keys=True)


def test_certificate_ledger_is_append_only_hash_chained_and_binary_round_trips():
    ledger = CertificateLedger()
    first = ledger.append("structural", {"gate_closed": True}, timestamp_ns=1)
    second = ledger.append("coverage", {"complete": True}, timestamp_ns=2)

    assert first.previous_hash == "0" * 64
    assert second.previous_hash == first.entry_hash
    assert ledger.verify_chain()

    restored = CertificateLedger.from_bytes(ledger.to_bytes())
    assert restored.root_hash == ledger.root_hash
    assert restored.verify_chain()

    tampered = bytearray(ledger.to_bytes())
    tampered[-2] = tampered[-2] ^ 1
    try:
        CertificateLedger.from_bytes(bytes(tampered))
    except (ValueError, json.JSONDecodeError, UnicodeDecodeError):
        pass
    else:
        raise AssertionError("tampered ledger unexpectedly verified")


def test_phi_health_supervisor_emits_passport_digest_and_repair_suggestions_without_numpy():
    supervisor = PhiHealthSupervisor()
    passport = supervisor.evaluate([
        {"phi": 0.62, "bures": 0.1, "purity": 0.9, "manifold_drift": 0.01, "solver_latency_ms": 10.0},
        {"phi": 0.91, "bures": 0.2, "purity": 0.8, "manifold_drift": 0.08, "solver_latency_ms": 20.0},
    ])

    assert passport.status.value in {"warn", "critical"}
    assert passport.telemetry_digest
    assert passport.suggestions
    assert passport.to_dict()["schema_version"] == "PULVINI_ELEVATION_V1"


def test_elevation_bridge_promotes_only_verified_passports_and_ledgers_without_numpy():
    operator = FakeOperator()
    verifier = FakeVerifier(operator)
    bridge = ElevationBridge(operator, verifier)
    passport = FakePassport()
    ledger = CertificateLedger()
    ledger.append("passport", passport.to_dict(), timestamp_ns=100)

    snapshot = bridge.readonly_snapshot()
    promotion = bridge.promotion_manifest(passport, ledger)

    assert snapshot["topology_verified"] is True
    assert promotion["read_only_research_access"] is True
    assert promotion["passport_hash"] == passport.passport_hash
    assert promotion["certificate_suite"] == {
        "grover": True,
        "topology": True,
        "automorphism": True,
        "coverage": True,
    }


def test_telemetry_contract_fixed_point_determinism_without_hypothesis_or_numpy():
    contract = TelemetryContract()
    samples = [0.0, 0.1, 0.5, 0.999999, 1.0]
    for phi in samples:
        encoded = contract.encode({"phi": phi, "bures": 1.0 - phi, "purity": phi, "manifold_drift": 0.0, "solver_latency_ms": 0.0})
        assert set(encoded) == set(contract.metrics)
        assert all(0 <= value <= contract.fixed_point_scale for value in encoded.values())
        assert contract.digest([{"phi": phi, "bures": 1.0 - phi, "purity": phi}]) == contract.digest([
            {"phi": phi, "bures": 1.0 - phi, "purity": phi}
        ])


def test_manifest_writer_and_production_response_envelope_without_numpy(tmp_path):
    operator, _verifier, builder = _builder()
    ledger = CertificateLedger()

    response = builder.production_response("FakeOperator.verify_topology", operator.verify_topology(), ledger)
    manifest_path = builder.write_manifest_json(tmp_path / "manifest.json", ledger=ledger)
    manifest = json.loads(manifest_path.read_text())

    assert isinstance(response, ProductionResponse)
    assert response.ledger_entry_hash == ledger.entries[response.ledger_index].entry_hash
    assert response.module_version_hash
    assert manifest["manifest_json_name"] == "manifest.json"
    assert "ManifoldOperator.ensure_density_state" in manifest["capability_manifest"]["endpoint_invariants"]
    assert manifest["capability_manifest"]["capability_flags"]["supports_production_response_envelope"] is True


def test_kernel_supervisor_logs_mathematical_exception_with_static_math_provider():
    ledger = CertificateLedger()
    supervisor = KernelSupervisor(ledger=ledger, math_provider=StaticMathProvider())
    invalid = {"trace": 2.0, "trace_one": False, "positive_semidefinite": True, "hermitian": True}

    try:
        supervisor.validate_density(invalid, stage="unit_test")
    except MathematicalException as exc:
        assert exc.report.closed is False
    else:
        raise AssertionError("expected mathematical exception")

    assert ledger.entries[-1].certificate_type == "mathematical_exception"
    assert ledger.verify_chain()


def test_kernel_supervisor_enforces_seeded_determinism_and_runtime_passport_without_numpy():
    ledger = CertificateLedger()
    supervisor = KernelSupervisor(ledger=ledger, math_provider=StaticMathProvider())
    density = {"trace": 1.0, "purity": 1.0, "min_eigenvalue": 0.0}

    def identity_kernel(rho, seed=0):
        return rho | {"seed": seed}

    output, report = supervisor.execute_density_contract(identity_kernel, density, seed=7)
    entry = ledger.entries[-1]
    passport = TelemetryContract().runtime_passport(
        "identity_kernel",
        {"phi": 0.618, "bures": 0.0, "purity": output["purity"]},
        report,
        entry,
    )

    assert report.closed is True
    assert TelemetryContract().verify_runtime_passport(passport, ledger) is True

    counter = {"value": 0}

    def nondeterministic_kernel(rho, seed=0):
        counter["value"] += 1
        return rho | {"counter": counter["value"], "seed": seed}

    try:
        supervisor.execute_density_contract(nondeterministic_kernel, density, seed=7)
    except MathematicalException as exc:
        assert exc.report.closed is True
    else:
        raise AssertionError("expected deterministic contract violation")


def test_elevation_bridge_returns_anonymized_read_only_research_telemetry_without_numpy():
    bridge = ElevationBridge(FakeOperator(), FakeVerifier())
    telemetry = bridge.anonymized_research_telemetry([
        {"worker_id": "secret", "phi": 0.61, "bures": 0.05, "purity": 0.9, "solver_latency_ms": 12.0},
    ])

    assert len(telemetry) == 1
    assert "worker_id" not in telemetry[0]
    assert telemetry[0]["sample_hash"]
    assert set(telemetry[0]["fixed_point"]) == set(TelemetryContract().metrics)


def test_fixed_point_metric_spec_is_explicit_and_latency_scaled():
    contract = TelemetryContract()
    specs = contract.metric_specs()
    encoded = contract.encode({"phi": 0.5, "bures": 0.25, "purity": 1.0, "manifold_drift": 0.0, "solver_latency_ms": 5000.0})

    assert specs["phi"]["bit_depth"] == 64
    assert specs["phi"]["scale"] == contract.fixed_point_scale
    assert specs["solver_latency_ms"]["maximum"] == 10000.0
    assert encoded["solver_latency_ms"] == contract.fixed_point_scale // 2


def test_phi_health_supervisor_ledgers_autonomic_repair_plan():
    ledger = CertificateLedger()
    supervisor = PhiHealthSupervisor()
    passport, plan = supervisor.evaluate_and_repair([
        {"phi": 0.2, "bures": 0.9, "purity": 0.5, "manifold_drift": 0.25, "solver_latency_ms": 50.0},
    ], ledger)

    assert passport.status.value == "critical"
    assert plan.action == "isolate_module_and_rebuild_density_state"
    assert ledger.entries[-1].certificate_type == "autonomic_repair"
    assert ledger.entries[-1].entry_hash == plan.ledger_entry_hash
    assert ledger.verify_chain()
