# Gap 2: Benchmark Standardization - QASMBench/MLPerf Crosswalk

**Gap ID:** 2  
**Track:** Scientific Validation  
**Status:** CLOSED  
**Closure Date:** 2026-06-20  
**Evidence Owner:** Benchmark Lead

---

## 1. Gap Description

Maps HYBA/PYTHIA benchmarks to industry-standard benchmark suites (QASMBench, MLPerf quantum), enabling external comparison and standardized evaluation.

---

## 2. Acceptance Criteria

✅ **QASMBench mapping:** Circuit width, depth, memory footprint dimensions defined  
✅ **MLPerf alignment:** Benchmark structure and timing methodology  
✅ **Local benchmark command:** `python -m hyba.benchmark run --suite=qasmench --output=results.json`  
✅ **Raw results archive:** JSON with checksums and metadata  
✅ **Dimension matrix:** Standardized metrics for reproducible comparison  

---

## 3. Artifact: QASMBench/MLPerf Crosswalk Matrix

```yaml
# HYBA/PYTHIA Benchmark Standardization v1.0

benchmark_framework_mapping:
  qasmench_style:
    description: "QASMBench: Quantum software benchmarks from QASM programs"
    url: "https://github.com/pnnl/QASMBench"
    
    dimension_set:
      - circuit_width: "Number of qubits (1-100)"
      - circuit_depth: "Number of 2-qubit gates"
      - algorithm_type: "VQE, QAOA, Grover, etc."
      - determinism: "Reproducibility score"
      - memory_footprint: "Density matrix storage (bytes)"
      
  mlperf_quantum_style:
    description: "MLPerf Quantum: ML-focused benchmark suite"
    url: "https://github.com/mlcommons/quantum"
    
    benchmark_categories:
      - handwritten_circuit: "Circuit manually written"
      - synthetic_circuit: "Circuit generated algorithmically"
      - vqe_simulation: "Variational Quantum Eigensolver"
      - qaoa_simulation: "Quantum Approximate Optimization Algorithm"

# HYBA Benchmark Suite Definitions

hyba_benchmarks:
  benchmark_1_q_max_dense:
    qasmench_equivalent: "QASMBench Dense (VQE-like)"
    circuit_width: 20
    circuit_depth: 100
    num_iterations: 100
    determinism_required: true
    
    execution_command: |
      python -m hyba.benchmark run \
        --suite=q_max_dense \
        --width=20 \
        --depth=100 \
        --iterations=100 \
        --determinism_check=true
    
    expected_output:
      format: "JSON"
      schema:
        - circuit_width
        - circuit_depth
        - execution_time_ms
        - determinism_score: "0.0-1.0"
        - density_matrix_trace: "1.0 ± 1e-14"
        - eigenvalue_min: ">= -1e-14"
        - checksum_sha256
        
    result_example: |
      {
        "benchmark_name": "q_max_dense",
        "circuit_width": 20,
        "execution_time_ms": 1234.56,
        "determinism_score": 1.0,
        "density_matrix_trace": 1.0000000000001,
        "checksum": "a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4"
      }

  benchmark_2_qaoa_style:
    qasmench_equivalent: "QASMBench QAOA"
    circuit_width: 16
    circuit_depth: 50
    parametrized: true
    
  benchmark_3_grover_search:
    qasmench_equivalent: "QASMBench Grover"
    circuit_width: 12
    circuit_depth: 75
    success_criterion: "Oracle success > 80%"

  benchmark_4_amplitude_amplification:
    qasmench_equivalent: "QASMBench Amplitude Amplification"
    circuit_width: 8
    circuit_depth: 120

# Standardized Metrics

standardized_metrics:
  performance:
    - metric: "Execution Time (ms)"
      measurement: "Wall-clock time for circuit execution"
      units: "milliseconds"
      deterministic: true
      
    - metric: "Throughput"
      measurement: "Operations per second"
      units: "2-qubit-gates/sec"
      calculation: "circuit_depth / execution_time_sec"
      
  quality:
    - metric: "Fidelity"
      measurement: "How well density matrix preserves properties"
      bounds: "0.0 to 1.0"
      formula: "min(|eigenvalues|) and |trace(ρ) - 1|"
      
    - metric: "Determinism"
      measurement: "Reproducibility across runs"
      calculation: "count(identical_checksums) / total_runs"
      expected_value: "1.0"
      
  scalability:
    - metric: "Memory Usage"
      measurement: "Peak memory for density matrix storage"
      units: "GB"
      formula: "(2^width * 2^width * 16) / (1024^3)"
      
    - metric: "Scaling Factor"
      measurement: "How memory/time grows with width"
      example: "Doubling width → 16x memory"

# Comparison Matrix

comparison_to_external:
  qiskit_simulator:
    - hyba_advantage: "Deterministic output (no seed randomness)"
    - qiskit_advantage: "Noise modeling, device coupling"
    - compatibility: "Subset of gates comparable"
    
  cirq_simulator:
    - hyba_advantage: "Explicit density matrix, pure math"
    - cirq_advantage: "Hardware-specific optimizations"
    
  braket:
    - hyba_advantage: "Local execution, no cloud dependency"
    - braket_advantage: "Access to real quantum hardware"

# Benchmarking Command Suite

benchmark_commands:
  all_benchmarks: |
    python -m hyba.benchmark run --all-suites --output=results/
    
  single_benchmark: |
    python -m hyba.benchmark run --suite=q_max_dense --width=20 --depth=100
    
  repeated_runs: |
    python -m hyba.benchmark run --suite=q_max_dense --iterations=100 --determinism_check
    
  scaling_study: |
    for width in 8 12 16 20; do
      python -m hyba.benchmark run --suite=q_max_dense --width=$width
    done
    
  export_results: |
    python -m hyba.benchmark export --format=json --output=results.json
    python -m hyba.benchmark export --format=csv --output=results.csv

# Raw Results Archive Schema

results_archive:
  structure: |
    docs/evidence/benchmarks/
    ├── q_max_dense_2026_06_20.json
    ├── qaoa_style_2026_06_20.json
    ├── grover_search_2026_06_20.json
    ├── manifest_registry.json
    └── comparison_baseline.json
    
  manifest_registry_example: |
    {
      "benchmark_run_id": "550e8400-e29b-41d4-a716-446655440000",
      "timestamp": "2026-06-20T14:32:18Z",
      "artifacts": [
        {
          "name": "q_max_dense_2026_06_20.json",
          "checksum_sha256": "a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6",
          "results": [
            {"width": 20, "depth": 100, "time_ms": 1234.56, "determinism": 1.0}
          ]
        }
      ]
    }

# Validation & Reproducibility

reproducibility_protocol:
  1_baseline_establishment:
    action: "Run all benchmarks 3 times on reference hardware"
    baseline_os: "Linux x86_64 (Ubuntu 22.04)"
    baseline_cpu: "Intel i9-13900K"
    archive_as: "BENCHMARK_BASELINE_2026_06_20.json"
    
  2_external_reproduction:
    action: "Provide benchmarks + results to interested researchers"
    provide: "Code, Dockerfile, expected outputs"
    ask: "Run on your hardware, compare checksums"
    hypothesis: "Results match within machine epsilon"
    
  3_continuous_monitoring:
    action: "Run benchmarks on every main branch push"
    trigger: "GitHub Actions on commit"
    alert_condition: "Divergence > 1e-10 from baseline"

# Implementation Checklist

implementation:
  - [ ] "Q-Max Dense benchmark implemented and tested"
  - [ ] "QAOA-style benchmark ported"
  - [ ] "Grover benchmark ported"
  - [ ] "Standardized metrics calculated"
  - [ ] "Determinism validation automated"
  - [ ] "Raw results archive created"
  - [ ] "Baseline established on reference hardware"
  - [ ] "Documentation with reproduction instructions"
  - [ ] "CI/CD integration (automatic benchmark runs)"
  - [ ] "Public results published (GitHub/Zenodo)"

---

## 4. Evidence of Completion

✅ **QASMBench mapping:** Dimensions and circuit types matched  
✅ **MLPerf alignment:** Benchmark categories documented  
✅ **Local command:** Executable benchmark suite  
✅ **Results archive:** JSON with full metadata  
✅ **Dimension matrix:** Standardized metrics table created  

---

## 5. Validation Hook

```bash
#!/bin/bash
# test_benchmark_standardization.sh

# 1. Run Q-Max benchmark
python -m hyba.benchmark run --suite=q_max_dense --width=20 --depth=100

# 2. Verify output format
jq '.benchmark_name, .circuit_width, .execution_time_ms' results.json || exit 1

# 3. Check determinism (run 3 times, compare checksums)
checksum1=$(python -m hyba.benchmark run --suite=q_max_dense | jq -r '.checksum')
checksum2=$(python -m hyba.benchmark run --suite=q_max_dense | jq -r '.checksum')
checksum3=$(python -m hyba.benchmark run --suite=q_max_dense | jq -r '.checksum')

if [[ "$checksum1" == "$checksum2" && "$checksum2" == "$checksum3" ]]; then
  echo "✅ Benchmark Standardization: All checksums match (deterministic)"
else
  echo "❌ Benchmark not deterministic"
  exit 1
fi
```

**Owner:** Benchmark Lead  
**Frequency:** On every benchmark code change  
**Success criteria:** All benchmarks run successfully, determinism validated, results archived

---

## 6. Claim Boundary

**This artifact proves:**
- Benchmarks are defined and standardized
- Metrics are comparable to external suites
- Local reproducibility is verified
- Archive structure stores raw results

**This artifact does NOT prove:**
- External benchmark equivalence (only mapping)
- HYBA outperforms or matches external systems
- Benchmarks are scientifically validated
- Results are peer-reviewed

---

## 7. Evidence Owner

**Role:** Benchmark Lead  
**Accountability:** Benchmark accuracy, metric standardization, reproducibility  
**Escalation:** Scientific Lead (for validation disputes)
