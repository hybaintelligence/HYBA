# HYBA PQMC Reproducibility Package

This package enables complete reproducibility of all HYBA Post-Quantum Mathematical Computing (PQMC) results, benchmarks, and validation experiments.

## Purpose

To enable independent verification by external research labs, peer reviewers, and customers, this package provides:
- Exact environment specification (Docker containers)
- Deterministic execution with fixed random seeds
- Validation scripts for all published results
- Benchmark suite against classical algorithms
- Statistical significance testing framework

## Quick Start

```bash
# Build the reproducibility environment
docker build -t hyba-pqmc-reproducibility:latest .

# Run the full validation suite
docker run --rm hyba-pqmc-reproducibility:latest python validate_all.py

# Run specific benchmark
docker run --rm hyba-pqmc-reproducibility:latest python benchmarks/quantum_benchmark.py --seed 42
```

## Environment Specification

- Python 3.12.7
- NumPy 2.0.0+
- SciPy 1.13.0+
- PyTest 8.4.0+
- Jupyter 1.0.0+
- All dependencies pinned in `requirements.lock`

## Deterministic Execution

All experiments use fixed random seeds:
```python
import numpy as np
np.random.seed(42)  # Default seed
```

Override with `--seed` flag:
```bash
python benchmarks/quantum_benchmark.py --seed 12345
```

## Validation Scripts

### Core Fault Tolerance Validation
```bash
python validate_fault_tolerance.py
```
Validates:
- Logical error rate suppression formula
- Monotonic decrease with code distance
- Monotonic increase with physical error rate
- Saturation at model threshold (0.0109)

### Benchmark Suite
```bash
python benchmarks/run_all_benchmarks.py
```
Benchmarks against:
- Classical Grover's algorithm
- Classical surface code simulation
- Classical optimization heuristics
- Monte Carlo methods

### Statistical Significance Testing
```bash
python statistical_validation.py --alpha 0.05 --iterations 1000
```
Performs:
- Two-sample t-tests
- Effect size calculation (Cohen's d)
- Confidence interval estimation
- Power analysis

## Published Results Validation

Each published result includes:
1. **Experiment configuration** (`config/`)
2. **Expected outputs** (`expected/`)
3. **Validation script** (`validate/`)
4. **Jupyter notebook** (`notebooks/`)

Example structure:
```
results/paper-nature-2024/
├── config/experiment_config.yaml
├── expected/metrics.json
├── validate/nature_2024_validation.py
└── notebooks/nature_2024_analysis.ipynb
```

## Continuous Validation

CI/CD pipeline runs validation on every commit:
```yaml
# .github/workflows/reproducibility.yml
- name: Run reproducibility validation
  run: docker run --rm hyba-pqmc-reproducibility:latest python validate_all.py
```

## External Verification Guide

For external labs wishing to verify results:

1. **Environment Setup**
   ```bash
   docker pull ghcr.io/hyba-analytics/pqmc-reproducibility:latest
   ```

2. **Run Validation**
   ```bash
   docker run --rm ghcr.io/hyba-analytics/pqmc-reproducibility:latest python validate_all.py
   ```

3. **Report Issues**
   - Create issue with full output
   - Include Docker version and host OS
   - Attach validation logs

## Contact

For reproducibility questions: reproducibility@hyba-analytics.com

## License

Core algorithms: Commercial license (contact for academic use)
Validation scripts: MIT license
