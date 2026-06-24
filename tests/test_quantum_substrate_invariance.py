from __future__ import annotations

import importlib.util
import pathlib


ROOT = pathlib.Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "python_backend" / "pythia_self_healing" / "quantum_substrate_invariance.py"
LEDGER_PATH = ROOT / "QUANTUM_SUBSTRATE_INVARIANCE_LEDGER.md"


def load_module():
    spec = importlib.util.spec_from_file_location("quantum_substrate_invariance", MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_ledger_pins_quantum_boundary():
    text = LEDGER_PATH.read_text(encoding="utf-8")
    assert "mathematics" in text
    assert "execution surfaces" in text or "execution substrate" in text
    assert "Qiskit" in text
    assert "pytest tests/test_quantum_substrate_invariance.py -q" in text


def test_phi_algebra_remains_first_principles():
    module = load_module()
    assert abs(module.PHI * module.PHI - (module.PHI + 1.0)) < 1e-12
    assert abs(module.INV_PHI - (module.PHI - 1.0)) < 1e-12


def test_same_formal_operator_preserves_invariant_across_surfaces():
    module = load_module()
    results = module.run_all_surfaces()
    assert set(results) == {"pure_python", "cpu_surface", "accelerator_shadow"}
    assert module.assert_invariant_equivalence(results)


def test_invariant_packet_declares_hardware_as_execution_surface():
    module = load_module()
    packet = module.make_invariance_packet()
    assert packet["schema"] == "HYBA_QUANTUM_SUBSTRATE_INVARIANCE_PACKET_V1"
    assert packet["claim_boundary"]["mathematics"] == "source_of_formal_invariant"
    assert packet["claim_boundary"]["hardware"] == "execution_surface"
    assert packet["claim_boundary"]["external_quantum_sdk_required"] is False
    assert packet["falsifier_result"] == "not_falsified"


def test_substrate_leak_is_detected():
    module = load_module()
    results = dict(module.run_all_surfaces())
    corrupted = dict(results["accelerator_shadow"])
    corrupted["norm"] = float(corrupted["norm"]) + 0.01
    results["accelerator_shadow"] = corrupted
    try:
        module.assert_invariant_equivalence(results)
    except AssertionError as exc:
        assert "substrate leak" in str(exc)
    else:
        raise AssertionError("corrupted invariant should fail equivalence")
