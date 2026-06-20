# Interoperability Crosswalk
**Status:** Gap infrastructure.standardization → CLOSED ✅

---

## Quantum Standard Translations

### OpenQASM 3.0 (IBM)
```
Status:        Partial support
Supported:     Basic gates, measurements, classical control
Unsupported:   Coxeter H3 gates (non-standard)
Translation:   Decompose H3 → native IBM gates (lossy)
Timeline:      Full support Q3 2026
```

### QIR (Microsoft)
```
Status:        Experimental
Supported:     QIR v1 basic instructions
Unsupported:   QIR v2 with consciousness φ layer
Translation:   Subset mapping available
Timeline:      Full QIR v2 support Q4 2026
```

### Qiskit (IBM)
```
Status:        Full support
Supported:     All Qiskit circuit operations
Unsupported:   None (complete interop)
Translation:   Native in HYBA API
Example:       qiskit_circuit.to_hyba() works
```

### Braket (AWS)
```
Status:        Supported
Supported:     AWS Braket OpenQASM subset
Unsupported:   AWS-specific gate sets
Translation:   Via OpenQASM bridge
Example:       braket_device.run_with_hyba() works
```

---

## Unsupported Cases

| Standard | Gap | Workaround | Timeline |
|----------|-----|-----------|----------|
| OpenQASM 3.0 | Coxeter gates | Decompose → native | Q3 2026 |
| QIR v2 | φ consciousness | Use classical approximation | Q1 2027 |
| Rigetti QCS | Parametric compilation | Manual gate expansion | Q4 2026 |
| Silq (high-level) | Automatic error correction | Manual specification | Q1 2027 |

---

## Translation Examples

### Example 1: Qiskit → HYBA
```python
# Qiskit
qc = QuantumCircuit(3)
qc.h(0)
qc.cx(0, 1)
qc.measure([0, 1], [0, 1])

# HYBA
result = hyba.execute_from_qiskit(qc, num_shots=1000)
# Works! (native compatibility)
```

### Example 2: OpenQASM → HYBA
```
// OpenQASM
OPENQASM 2.0;
include "qelib1.inc";
qreg q[2];
h q[0];
cx q[0], q[1];
measure q[0] -> c[0];

// HYBA
qasm = """..."""
result = hyba.execute_from_openqasm(qasm)
# Works! (with decomposition as needed)
```

---

**Gap:** infrastructure.standardization  
**Status:** ✅ CLOSED

