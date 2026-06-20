# Gap 17: Standardization - Interoperability Crosswalk

**Gap ID:** 17  
**Track:** FAIR Infrastructure  
**Status:** CLOSED  
**Closure Date:** 2026-06-20  
**Evidence Owner:** Standards Lead

---

## 1. Gap Description

Documents translation boundaries and unsupported cases when converting HYBA/PYTHIA representations to industry-standard quantum programming frameworks (OpenQASM, QIR, Qiskit, Braket).

---

## 2. Acceptance Criteria

✅ **OpenQASM translation documented:** Supported gates, circuit width limits, pulse-level incompatibilities  
✅ **QIR mapping specified:** Type system alignment, metadata preservation, error cases  
✅ **Qiskit bridge defined:** QuantumCircuit → HYBA conversion rules, provider integration  
✅ **Braket compatibility mapped:** PulseSequence translation, device constraints  
✅ **Unsupported cases catalogued:** Explicit boundary stating what cannot be translated  

---

## 3. Artifact: Interoperability Crosswalk Matrix

```markdown
# HYBA/PYTHIA ↔ Industry Standard Interoperability Crosswalk

**Version:** 1.0  
**Date:** 2026-06-20  
**Maintainer:** Standards Lead  

---

## Executive Summary

HYBA/PYTHIA is a mathematical quantum operations substrate (not a physical hardware abstraction). This document specifies:

1. **Translatable:** Gate sets, circuit semantics, density matrix operations
2. **Lossy:** Pulse scheduling, hardware-specific optimizations
3. **Untranslatable:** Substrate-specific features (PULVINI memory bounds, non-Markovian extensions)

All translations are ONE-WAY (external → HYBA) or INFORMATIONAL (HYBA → external) until external backends prove equivalence.

---

## OpenQASM 3.0 ↔ HYBA Translation

### Supported Mappings

| OpenQASM 3.0 Feature | HYBA Representation | Fidelity | Notes |
|---|---|---|---|
| `qubit q[n]` | Density matrix state vector (2^n × 2^n) | Native | Default to |ψ⟩⟨ψ\| mixed state |
| `reset q;` | Trace out, reinitialize to \|0⟩⟨0\| | Native | Partial trace → reinitialization |
| `h q;` | Hadamard unitary application | Native | Verify unitary preservation |
| `cx q0, q1;` | Two-qubit controlled gate (CNOT) | Native | Tensor product structure |
| `measure q → c;` | Born-rule projection + classical bit | Native | Deterministic simulation |
| `rx(θ) q;` | Rotation by angle θ around X | Native | Parameterizable |
| `parametrized circuit` | Template substitution | Native | Pre-compute all instances |
| `array indexing` | Classical register access | Native | Symbolic or concrete |

### Partially Supported

| OpenQASM Feature | HYBA Status | Limitation | Workaround |
|---|---|---|---|
| `pulse {...}` | Info-only | HYBA operates at gate level | Extract gate decomposition |
| `defcal` (custom calibration) | Info-only | No hardware feedback loop | Assume ideal unitary |
| `barrier` (timing hint) | Ignored | Deterministic execution | Log timing separately |
| `reset on qubit subset` | Supported | Requires tensor untracing | Explicit partial-trace operation |

### Unsupported (Hard Boundary)

| OpenQASM Feature | Reason | Alternative |
|---|---|---|
| Hardware-specific gate errors | HYBA is substrate-independent | Inject noise classically if needed |
| Timing/scheduling (pulses) | Beyond gate-model abstraction | Extract ideal gate sequence |
| Mid-circuit measurement feedback | Requires conditional branching | Decompose into classical logic |
| `extern` functions | Would break reproducibility | Inline all computation |
| Dynamic circuit dispatch | Not compatible with HYBA proof system | Use static circuit instantiation |

### Translation Direction

```
┌─────────────────────────────────────┐
│   External OpenQASM 3.0 Circuit     │
└──────────────┬──────────────────────┘
               │
               ↓ (lossless)
┌─────────────────────────────────────┐
│ HYBA Gate Sequence + Tensor Proof   │
└──────────────┬──────────────────────┘
               │
               ↓ (informational only)
┌─────────────────────────────────────┐
│  Reconstructed OpenQASM 3.0 (≈)    │
└─────────────────────────────────────┘

Note: Rightward arrow ↓ is one-way until external validation
```

**Implementation:**
```python
# hyba_sdk/interop/openqasm.py

def openqasm3_to_hyba(qasm_text: str) -> HYBACircuit:
    """Convert OpenQASM 3.0 to HYBA gate sequence."""
    # 1. Parse OpenQASM 3.0 AST
    ast = parse_qasm3(qasm_text)
    
    # 2. Extract classical + quantum components
    gate_sequence = extract_gates(ast)
    classical_logic = extract_classicals(ast)
    
    # 3. Validate supported gates
    for gate in gate_sequence:
        if gate.name not in SUPPORTED_GATES:
            raise UnsupportedGateError(f"{gate.name} not in HYBA gate set")
    
    # 4. Build density matrix proof
    hyba_circuit = HYBACircuit(
        n_qubits=ast.num_qubits,
        gate_sequence=gate_sequence,
        proof_obligation="unitary_preservation"
    )
    
    return hyba_circuit

def hyba_to_openqasm3(circuit: HYBACircuit, target_format="text") -> str:
    """Convert HYBA circuit to OpenQASM 3.0 (informational)."""
    # Note: This is for clarity only. HYBA is the source of truth.
    lines = ["OPENQASM 3.0;"]
    lines += [f"qubit q[{circuit.n_qubits}];"]
    
    for gate in circuit.gate_sequence:
        qasm_text = gate.to_openqasm3()
        lines.append(qasm_text)
    
    return "\n".join(lines)
```

---

## QIR (Quantum Intermediate Representation) ↔ HYBA Translation

### Type System Alignment

| QIR Type | HYBA Type | Mapping Strategy |
|---|---|---|
| `!quantum.qubit` | Qubit index (0..n-1) | Direct map |
| `i64` (classical int) | Python int | Native |
| `i1` (classical bit) | {0, 1} | Native |
| `!quantum.result` | Measurement outcome dict | Dict[int, {0,1}] |
| `[Type x N]` (array) | List[T] | Homogeneous list |

### Metadata Preservation

```python
# QIR → HYBA preservation
qir_metadata = {
    "version": "1.0",
    "target": "generic",
    "entry_point": "main",
    "args": [("q", "QirQubit[]"), ("c", "QirClassical[]")]
}

hyba_metadata = {
    "source_format": "QIR",
    "source_version": qir_metadata["version"],
    "preserved_types": qir_metadata["args"],
    "entry_point": qir_metadata["entry_point"]
}
```

### Error Cases

| QIR Feature | HYBA Handling | Error Message |
|---|---|---|
| Unsupported intrinsics (e.g., `__quantum__*` extensions) | Reject with specificity | "Intrinsic `__quantum__foo` not in HYBA" |
| Recursive function calls | Unroll at compile time | "Recursion not supported; max depth 100" |
| Undefined reference | Validation error | "Symbol `xyz` not found in scope" |
| Type mismatch | Static check failure | "Expected i64, got !quantum.qubit" |

---

## Qiskit ↔ HYBA Bridge

### QuantumCircuit → HYBA Conversion

```python
from qiskit import QuantumCircuit, QuantumRegister
from hyba_sdk import HYBACircuit, Interop

qc = QuantumCircuit(3)  # Qiskit circuit
qc.h(0)
qc.cx(0, 1)
qc.measure_all()

# Bridge conversion
hyba_circuit = Interop.from_qiskit(qc)

# Properties preserved:
# ✅ Qubit count
# ✅ Gate sequence
# ✅ Classical bits
# ❌ Optimization metadata (Qiskit-specific passes)
# ❌ Layout information
```

### Supported Qiskit Gates

| Qiskit Gate | HYBA Support | Notes |
|---|---|---|
| `h`, `x`, `y`, `z`, `s`, `t` | ✅ Full | Single-qubit Paulis + phase |
| `rx`, `ry`, `rz` | ✅ Full | Parameterizable rotations |
| `cx` (CNOT) | ✅ Full | Controlled-NOT |
| `swap` | ✅ Full | Two-qubit swap unitary |
| `ccx` (Toffoli) | ✅ Full | Three-qubit controlled gate |
| `u1`, `u2`, `u3` | ✅ Full | General unitary parameterization |
| `rxx`, `ryy`, `rzz` | ✅ Full | Two-qubit interactions |
| `measure` | ✅ Full | Born-rule projection |
| `barrier` | ⚠ Ignored | No-op; structural only |
| `reset` | ✅ Full | Partial trace + reinitialization |

### Qiskit Provider Integration

```python
# Register HYBA as a Qiskit backend (for interoperability demo)
from qiskit_hyba import HYBABackend

backend = HYBABackend()
job = backend.run(qc, shots=1000)
result = job.result()
# Counts: {'000': 247, '001': 5, '010': 12, ... }
```

### Unsupported Qiskit Features

- **Transpiler optimization passes:** Qiskit's optimizations are hardware-specific
- **Calibration data:** No hardware-specific calibration in HYBA
- **Layout/Mapping:** HYBA is abstract; no physical layout
- **Dynamic circuits (mid-circuit measurements):** Not supported in current version

---

## Braket ↔ HYBA Mapping

### PulseSequence → HYBA Gate Decomposition

| Braket Pulse Feature | HYBA Handling |
|---|---|
| Drive pulse (microwave) | Extract parameterized gate |
| Capture instruction (measurement) | Convert to measurement gate |
| Barrier/timing | Ignored (deterministic execution) |
| Frame modifications | Assume identity; log warning |

### Device Constraints Mapping

```python
# Braket device properties
braket_device = {
    "native_gates": ["x", "y", "z", "h", "cnot"],
    "max_qubit_count": 11,
    "connectivity": "star"  # All-to-all via resonator
}

# HYBA abstract properties
hyba_abstract = {
    "supported_gates": [
        "x", "y", "z", "h", "s", "t",
        "rx", "ry", "rz",
        "cx", "swap", "ccx"
    ],
    "max_qubits": "unlimited (software-bounded)",
    "connectivity": "all-to-all (via tensor product)"
}
```

---

## NumPy ↔ HYBA State Representation

### Dense Matrix Conversion

```python
import numpy as np
from hyba_sdk import DensityMatrix

# NumPy array → HYBA density matrix
rho_np = np.array([
    [0.9, 0.0],
    [0.0, 0.1]
])

# Validate density matrix properties
def validate_density_matrix(rho):
    """Check Hermitian, trace=1, positive semidefinite."""
    assert np.allclose(rho, rho.conj().T), "Not Hermitian"
    assert np.isclose(np.trace(rho), 1.0), "Trace ≠ 1"
    eigenvalues = np.linalg.eigvalsh(rho)
    assert np.all(eigenvalues >= -1e-14), "Not positive semidefinite"

rho_hyba = DensityMatrix(rho_np)
```

### State Vector Preservation

```python
# |ψ⟩ → ρ = |ψ⟩⟨ψ|
psi = np.array([1/np.sqrt(2), 1/np.sqrt(2)])  # |+⟩
rho = np.outer(psi, psi.conj())  # Convert to density matrix

# Verify |ψ⟩⟨ψ| properties
assert np.isclose(np.trace(rho @ rho), 1.0), "Pure state property"
```

---

## HYBA-Internal Representation

### Tensor Network Structure

```python
# HYBA uses implicit tensor network (not explicitly serialized)
class HYBAQuantumState:
    def __init__(self, n_qubits: int):
        self.n_qubits = n_qubits
        self.tensor_layers: List[UnaryOrBinaryGate] = []
        
    def add_gate(self, gate: Gate, *targets):
        # Lazy tensor contraction; computed only on measurement
        self.tensor_layers.append((gate, targets))
        
    def measure(self) -> dict:
        # Execute Born rule: p(outcome) = |⟨outcome|ψ⟩|²
        full_density_matrix = self.materialize()
        return sample_from_born_rule(full_density_matrix)

    def materialize(self) -> np.ndarray:
        # Compute ρ = I; for each gate: ρ ← gate ⊗ I
        rho = np.eye(2 ** self.n_qubits)
        for gate, targets in self.tensor_layers:
            rho = apply_gate(rho, gate, targets)
        return rho
```

---

## Claim Boundary

### This Crosswalk Proves:

✅ Supported translation pathways are documented  
✅ Unsupported cases are explicitly stated  
✅ Error handling procedures defined  
✅ One-way translation direction (external → HYBA) is clear  

### This Crosswalk Does NOT Prove:

❌ Implementation is complete or tested  
❌ Translators maintain 100% semantic fidelity  
❌ External frameworks recognize HYBA as equivalent  
❌ Performance characteristics are comparable  

---

## Implementation Checklist

- [ ] `openqasm3_to_hyba()` implemented and tested
- [ ] `qir_to_hyba()` validator created
- [ ] Qiskit bridge registered as backend
- [ ] Braket pulse translator written
- [ ] NumPy state converter bidirectional
- [ ] Error messages enumerate unsupported cases
- [ ] Documentation examples in each language
- [ ] Automated crosswalk validation in CI/CD
- [ ] Version pinning for external library versions

---

## Validation Hook

```bash
# test_interoperability_crosswalk.py
pytest tests/interop/ -v \
  --tb=short \
  --markers="openqasm,qir,qiskit,braket,numpy" \
  --cov=hyba_sdk.interop
```

**Owner:** Standards Lead  
**Frequency:** On each external library version upgrade  
**Success criteria:** All supported pathways validate; unsupported cases rejected with clear errors
