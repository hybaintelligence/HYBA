# HYBA PQMC Enterprise-Grade Benchmark Suite

## Overview

This enterprise-grade benchmark suite provides comprehensive, evidence-based validation of HYBA's Post-Quantum Mathematical Computing (PQMC) platform superiority over classical approaches across multiple dimensions using real-world datasets.

## Features

### Real-World Datasets
- **Financial**: S&P 500 historical data, portfolio optimization datasets
- **Machine Learning**: MNIST, CIFAR-10, quantum chemistry datasets
- **Scientific**: Materials properties, molecular energies
- **Cryptography**: RSA factoring challenges, elliptic curve parameters

### Evidence Tagging
- **Cryptographic Hashes**: SHA-256 and SHA3-256 for all datasets and results
- **Provenance Tracking**: Complete audit trail of code, environment, and execution
- **Git Integration**: Automatic capture of commit, branch, and author information
- **Verification**: Automated verification of result integrity

### Multi-Dimensional Metrics
- **Speed**: Execution time, throughput, latency, time efficiency
- **Accuracy**: Result correctness, precision, recall, F1 score, error rate
- **Scalability**: Scaling factors, Big O complexity, data size scaling
- **Efficiency**: Memory usage, energy consumption, cost efficiency, resource utilization
- **Robustness**: Fault tolerance, error recovery, stability, resilience
- **Statistical Validation**: P-values, confidence intervals, effect sizes, power analysis

### Reproducibility
- **Fixed Seeds**: Deterministic execution with fixed random seeds
- **Environment Specification**: Complete environment capture (Python, packages, system)
- **Docker Support**: Containerized environment for exact reproduction
- **Validation Scripts**: Automated validation of all results

## Components

### 1. Enterprise Benchmark Suite (`enterprise_benchmark_suite.py`)
Main benchmark runner with real-world datasets and comprehensive metrics.

**Usage**:
```bash
python reproducibility/benchmarks/enterprise_benchmark_suite.py --seed 42 --output validation_output/enterprise_benchmarks.json
```

**Benchmarks**:
- Portfolio Optimization (Financial)
- ML Training (Machine Learning)
- Cryptographic Operations (Cryptography)

### 2. Evidence Provenance System (`evidence_provenance.py`)
Cryptographic evidence tagging and provenance tracking.

**Usage**:
```bash
python reproducibility/benchmarks/evidence_provenance.py
```

**Features**:
- Dataset provenance (hash, size, source)
- Code provenance (git info, file hash)
- Environment provenance (Python, packages, system)
- Execution provenance (parameters, environment variables)
- Result provenance (hash, size, keys)
- Cryptographic evidence (combined hash, timestamp)

### 3. Dataset Registry (`dataset_registry.py`)
Real-world dataset integration and validation.

**Usage**:
```bash
python reproducibility/benchmarks/dataset_registry.py
```

**Datasets**:
- Financial: S&P 500, portfolio optimization
- Machine Learning: MNIST, CIFAR-10
- Scientific: Quantum chemistry, materials science
- Cryptography: RSA challenge, ECC challenge

### 4. Superiority Metrics (`superiority_metrics.py`)
Multi-dimensional superiority analysis with statistical validation.

**Usage**:
```bash
python reproducibility/benchmarks/superiority_metrics.py
```

**Metrics**:
- Speed: speedup, throughput, latency, efficiency
- Accuracy: accuracy, precision, recall, F1, error rate
- Scalability: scaling factor, Big O, scalability score
- Efficiency: memory, energy, cost, resource utilization
- Robustness: fault tolerance, error recovery, stability, resilience
- Statistical: p-value, confidence interval, effect size, power

## Output Format

### Benchmark Result JSON
```json
{
  "name": "Portfolio Optimization",
  "category": "Financial Optimization",
  "dataset": "Portfolio Returns (100 assets, 1000 scenarios)",
  "metadata": {
    "benchmark_id": "portfolio_optimization",
    "timestamp": "2024-06-20T12:00:00Z",
    "python_version": "3.12.7",
    "numpy_version": "2.0.0",
    "seed": 42,
    "dataset_hash": "abc123...",
    "dataset_size": 800000,
    "dataset_source": "synthetic_portfolio_optimization",
    "environment": "macOS-14.0-arm64",
    "git_commit": "abc123...",
    "git_branch": "main"
  },
  "evidence": {
    "result_hash": "def456...",
    "timestamp": "2024-06-20T12:00:00Z",
    "signature": "ghi789...",
    "verification_method": "SHA-256"
  },
  "hyba_time_ms": 123.45,
  "hyba_accuracy": 0.95,
  "hyba_memory_mb": 100.0,
  "hyba_energy_joules": 0.5,
  "hyba_throughput_ops": 50.0,
  "classical_time_ms": 1234.56,
  "classical_accuracy": 0.85,
  "classical_memory_mb": 500.0,
  "classical_energy_joules": 2.5,
  "classical_throughput_ops": 5.0,
  "speedup": 10.0,
  "accuracy_improvement": 0.10,
  "memory_reduction": 0.80,
  "energy_efficiency": 5.0,
  "throughput_improvement": 10.0,
  "p_value": 0.0001,
  "confidence_interval": [0.08, 0.12],
  "effect_size": 2.5,
  "statistical_significance": true,
  "ground_truth_match": true,
  "reproducibility_score": 1.0,
  "audit_trail": [...]
}
```

### Provenance Record JSON
```json
{
  "record_id": "prov-portfolio_optimization-1718899200",
  "timestamp": "2024-06-20T12:00:00Z",
  "benchmark_id": "portfolio_optimization",
  "dataset_provenance": {
    "source": "synthetic_portfolio_optimization",
    "hash_sha256": "abc123...",
    "hash_sha3_256": "def456...",
    "size_bytes": 800000,
    "shape": [1000, 100],
    "dtype": "float64",
    "capture_timestamp": "2024-06-20T12:00:00Z",
    "capture_method": "automatic",
    "data_classification": "public"
  },
  "code_provenance": {
    "file_path": "/path/to/benchmark.py",
    "file_hash_sha256": "ghi789...",
    "file_hash_sha3_256": "jkl012...",
    "file_size_bytes": 15000,
    "file_lines": 500,
    "git": {
      "commit": "abc123...",
      "branch": "main",
      "commit_timestamp": "2024-06-20 10:00:00",
      "author": "John Doe",
      "message": "Add enterprise benchmarks"
    },
    "capture_timestamp": "2024-06-20T12:00:00Z"
  },
  "environment_provenance": {
    "python": {
      "version": "3.12.7",
      "executable": "/usr/bin/python3",
      "implementation": "CPython"
    },
    "numpy_version": "2.0.0",
    "packages": {
      "numpy": "2.0.0",
      "scipy": "1.13.0",
      "pandas": "2.2.0"
    },
    "system": {
      "platform": "macOS-14.0-arm64",
      "system": "Darwin",
      "release": "23.0.0",
      "machine": "arm64",
      "processor": "arm",
      "cpu_count": 8
    },
    "memory": {
      "total_gb": 16.0,
      "available_gb": 8.0,
      "percent_used": 50.0
    },
    "capture_timestamp": "2024-06-20T12:00:00Z"
  },
  "execution_provenance": {
    "parameters": {
      "seed": 42,
      "iterations": 100
    },
    "environment_variables": {
      "HYBA_REDIS_URL": "redis://localhost:6379",
      "PYTHONPATH": "/path/to/python_backend"
    },
    "working_directory": "/path/to/HYBA_FULLSTACK",
    "user": "demouser",
    "pid": 12345,
    "start_timestamp": "2024-06-20T12:00:00Z"
  },
  "result_provenance": {
    "result_hash_sha256": "mno345...",
    "result_hash_sha3_256": "pqr678...",
    "result_size_bytes": 5000,
    "result_keys": ["accuracy", "time", "memory"],
    "capture_timestamp": "2024-06-20T12:00:00Z",
    "result_count": 3
  },
  "cryptographic_evidence": {
    "combined_hash_sha256": "stu901...",
    "combined_hash_sha3_256": "vwx234...",
    "timestamp": "2024-06-20T12:00:00Z",
    "evidence_version": "1.0",
    "hash_algorithm": "SHA-256 and SHA3-256"
  },
  "verification_status": "verified",
  "audit_trail": [...]
}
```

## Running Benchmarks

### Quick Start
```bash
# Run all enterprise benchmarks
python reproducibility/benchmarks/enterprise_benchmark_suite.py --seed 42

# Run with custom output
python reproducibility/benchmarks/enterprise_benchmark_suite.py --seed 42 --output custom_output.json

# Verify previous results
python reproducibility/benchmarks/enterprise_benchmark_suite.py --verify previous_results.json
```

### Docker Environment
```bash
# Build reproducibility environment
docker build -t hyba-pqmc-benchmarks:latest -f reproducibility/Dockerfile .

# Run benchmarks in Docker
docker run --rm hyba-pqmc-benchmarks:latest python reproducibility/benchmarks/enterprise_benchmark_suite.py
```

### Individual Components
```bash
# Test evidence provenance system
python reproducibility/benchmarks/evidence_provenance.py

# Test dataset registry
python reproducibility/benchmarks/dataset_registry.py

# Test superiority metrics
python reproducibility/benchmarks/superiority_metrics.py
```

## Validation

### Automated Validation
```bash
# Validate all benchmarks
python reproducibility/validate_all.py

# Validate specific benchmark
python reproducibility/benchmarks/enterprise_benchmark_suite.py --verify validation_output/enterprise_benchmarks.json
```

### Manual Verification
1. Check result hashes match expected values
2. Verify audit trail completeness
3. Confirm reproducibility score is 1.0
4. Validate statistical significance (p < 0.05)
5. Verify ground truth match

## Superiority Ranks

- **Exceptional** (0.8+): Outstanding superiority across all dimensions
- **Superior** (0.6-0.8): Strong superiority in most dimensions
- **Significant** (0.4-0.6): Clear superiority in key dimensions
- **Moderate** (0.2-0.4): Measurable superiority in some dimensions
- **Marginal** (0.0-0.2): Slight superiority
- **Inferior** (<0.0): No superiority or inferior performance

## Statistical Significance

All benchmarks include:
- **P-value**: Probability of observing results by chance (target: < 0.05)
- **Confidence Interval**: 95% confidence interval for the difference
- **Effect Size**: Cohen's d (small: 0.2, medium: 0.5, large: 0.8)
- **Power**: Statistical power (target: > 0.8)

## Contact

For questions about the enterprise benchmark suite:
- Email: benchmarks@hyba-analytics.com
- Documentation: https://docs.hyba-analytics.com/benchmarks
- Issues: https://github.com/hyba-analytics/HYBA_FULLSTACK/issues

## License

Benchmark suite: MIT license
Datasets: Per dataset license (see dataset metadata)
