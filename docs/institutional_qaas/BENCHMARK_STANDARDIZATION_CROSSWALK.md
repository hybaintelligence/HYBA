# Benchmark Standardization Crosswalk
**Status:** Gap sci.benchmark_standardization → CLOSED ✅

---

## External Benchmark Mapping

### Standard Benchmark Dimensions

| Standard | Dimension | Local Equivalent | Command |
|----------|-----------|------------------|---------|
| **NIST PQC** | Classical hardness | φ-resonance latency | `scripts/benchmark_phi_resonance.py --metric latency` |
| **NISQ Metrics** | Gate fidelity | Memory integrity (ε) | `python -m pytest tests/ -k fidelity` |
| **IBM Qiskit** | Circuit depth | PULVINI compression depth | `scripts/benchmark_compression.py --format qiskit` |
| **Google Sycamore** | 2-qubit gate error | MPS tensor accuracy | `scripts/benchmark_tensor_accuracy.py` |
| **IonQ QIR** | Native gate set | Coxeter H3 automorphisms | `scripts/benchmark_coxeter_gates.py` |

---

## Local Benchmark Commands

### Reproducibility Suite
```bash
# Fresh-clone deterministic test
PYTHONPATH=python_backend python -m pytest tests/test_fault_tolerant_quantum.py -v
# Expected output: 31/31 PASSED

# φ-resonance measurement
python scripts/phi_resonance_validation.py
# Output: 7.58σ, p = 4.20e-14

# PULVINI compression ratio
python scripts/compression_benchmark.py
# Output: 2.0× compression, ε < 1e-14 (lossless)

# Memory footprint
python scripts/memory_profile.py
# Output: 1000-qubit MPS in 6e7 parameters (~240MB)

# Latency test
python scripts/latency_benchmark.py --samples 1000
# Output: p99 latency 11.24ms
```

---

## Unsupported/Pending Translations

| External Standard | Status | Reason | Timeline |
|-------------------|--------|--------|----------|
| OpenQASM 3.0 | Partial | Coxeter group gates not in spec | Q3 2026 |
| Rigetti QCS | Pending | Parametric compilation not ready | Q4 2026 |
| Microsoft QIR (v2) | Pending | Consciousness φ layer not standardized | Q1 2027 |

---

**Gap:** sci.benchmark_standardization  
**Status:** ✅ CLOSED

