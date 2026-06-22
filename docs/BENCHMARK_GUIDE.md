# Benchmark Guide

## Overview

This guide provides comprehensive benchmarking procedures for the Salamander Regeneration Framework, following ACM and IEEE standards for reproducible performance evaluation.

## Benchmark Suite

### 1. Regeneration Latency

**Purpose**: Measure time from fault detection to successful recovery

**Methodology**:
```python
import time
import numpy as np
from pythia_mining.stateful_regeneration import (
    ModuleState, apply_fault, quarantine_channel,
    redifferentiate, measure_role, ContextSignal, Role
)

def benchmark_regeneration_latency(severity, num_trials=1000):
    latencies = []
    for i in range(num_trials):
        start = time.perf_counter()
        
        # Initialize
        state = ModuleState.healthy(f"module_{i}")
        
        # Apply fault
        state = apply_fault(state, severity)
        
        # Quarantine
        state = quarantine_channel(state)
        
        # Redifferentiate
        context = ContextSignal(
            clifford_index=i % 100,
            target_role=Role.HEALTHY_SPECIALIZED,
            confidence=0.8
        )
        state = redifferentiate(state, context)
        
        # Measure
        collapsed_role, state = measure_role(state, np.random.default_rng())
        
        end = time.perf_counter()
        latencies.append((end - start) * 1000)  # Convert to milliseconds
    
    return {
        "mean_ms": np.mean(latencies),
        "median_ms": np.median(latencies),
        "p95_ms": np.percentile(latencies, 95),
        "p99_ms": np.percentile(latencies, 99),
        "max_ms": np.max(latencies),
        "min_ms": np.min(latencies),
        "std_ms": np.std(latencies)
    }
```

**Results** (expected):
```
Severity 0.5: mean=2.1ms, p99=3.8ms
Severity 0.7: mean=2.3ms, p99=4.1ms
Severity 0.9: mean=2.5ms, p99=4.5ms
Severity 1.0: mean=2.6ms, p99=4.7ms
```

### 2. Throughput

**Purpose**: Measure maximum regenerations per second

**Methodology**:
```python
import asyncio
import time

async def benchmark_throughput(duration_seconds=10):
    start = time.time()
    count = 0
    
    while time.time() - start < duration_seconds:
        # Trigger regeneration
        result = await trigger_regeneration(
            module_id=f"module_{count % 100}",
            clifford_index=count % 100,
            ai_triggered=False,
            dry_run=False
        )
        count += 1
    
    elapsed = time.time() - start
    throughput = count / elapsed
    
    return {
        "duration_seconds": elapsed,
        "total_regenerations": count,
        "throughput_rps": throughput
    }
```

**Results** (expected):
```
Single-threaded: ~400-500 regenerations/second
Multi-threaded (4 cores): ~1,500-2,000 regenerations/second
```

### 3. Resource Usage

**Purpose**: Measure CPU, memory, and network usage

**Methodology**:
```python
import psutil
import os

def benchmark_resource_usage(num_modules=1000):
    process = psutil.Process(os.getpid())
    
    # Baseline
    baseline_cpu = process.cpu_percent(interval=1)
    baseline_memory = process.memory_info().rss / 1024 / 1024  # MB
    
    # Create modules
    modules = {}
    for i in range(num_modules):
        modules[f"module_{i}"] = ModuleState.healthy(f"module_{i}")
    
    # After creation
    after_creation_cpu = process.cpu_percent(interval=1)
    after_creation_memory = process.memory_info().rss / 1024 / 1024
    
    # Run regenerations
    for i in range(100):
        state = apply_fault(modules[f"module_{i}"], 0.7)
        state = quarantine_channel(state)
        context = ContextSignal(i, Role.HEALTHY_SPECIALIZED, 0.8)
        state = redifferentiate(state, context)
    
    # After regenerations
    after_regen_cpu = process.cpu_percent(interval=1)
    after_regen_memory = process.memory_info().rss / 1024 / 1024
    
    return {
        "num_modules": num_modules,
        "baseline_memory_mb": baseline_memory,
        "after_creation_memory_mb": after_creation_memory,
        "after_regen_memory_mb": after_regen_memory,
        "memory_per_module_kb": (after_creation_memory - baseline_memory) * 1024 / num_modules,
        "baseline_cpu_percent": baseline_cpu,
        "after_creation_cpu_percent": after_creation_cpu,
        "after_regen_cpu_percent": after_regen_cpu
    }
```

**Results** (expected):
```
Memory per module: ~5-10 KB
1000 modules: ~5-10 MB
CPU usage: <5% during idle, <20% during regeneration
```

### 4. Success Rate

**Purpose**: Measure regeneration success rate across fault severities

**Methodology**:
```python
from hypothesis import given, strategies as st

@given(st.floats(min_value=0.0, max_value=1.0))
def test_regeneration_success_rate(severity):
    num_trials = 100
    successes = 0
    
    for i in range(num_trials):
        state = ModuleState.healthy(f"module_{i}")
        state = apply_fault(state, severity)
        state = quarantine_channel(state)
        
        context = ContextSignal(
            clifford_index=i % 100,
            target_role=Role.HEALTHY_SPECIALIZED,
            confidence=0.8
        )
        
        try:
            state = redifferentiate(state, context)
            collapsed_role, state = measure_role(state, np.random.default_rng())
            
            if collapsed_role == Role.HEALTHY_SPECIALIZED:
                successes += 1
        except Exception:
            pass
    
    success_rate = successes / num_trials
    assert success_rate >= 0.8, f"Success rate {success_rate} below 80% for severity {severity}"
```

**Results** (expected):
```
Severity 0.0-0.3: 100% success rate
Severity 0.3-0.5: 95-100% success rate
Severity 0.5-0.7: 90-95% success rate
Severity 0.7-0.9: 80-90% success rate
Severity 0.9-1.0: 70-80% success rate
```

### 5. Comparison to Baselines

**Purpose**: Compare Salamander to traditional recovery methods

**Baselines**:
1. **Kubernetes Pod Restart**: `kubectl rollout restart`
2. **AWS Auto Scaling**: Spin up new instance
3. **Manual Recovery**: Human intervention (simulated 10 min)
4. **Backup Restore**: Restore from last backup

**Metrics**:
- Time to recovery
- State preservation (0% = full loss, 100% = perfect preservation)
- Resource cost (compute, network, storage)
- Automation level (0% = manual, 100% = fully autonomous)

**Results** (expected):
```
Method                | Time to Recovery | State Preservation | Resource Cost | Automation
----------------------|------------------|--------------------|---------------|------------
Kubernetes Restart    | 30-60 seconds    | 0%                 | Medium        | 100%
AWS Auto Scaling      | 2-5 minutes      | 0%                 | High          | 100%
Manual Recovery       | 10 minutes       | 50%                | Low           | 0%
Backup Restore        | 5-15 minutes     | 90%                | Medium        | 50%
Salamander            | <5 seconds       | 100%               | Low           | 95%
```

## Benchmark Harness

### Automated Benchmark Runner

```python
#!/usr/bin/env python3
"""
benchmark_runner.py - Automated benchmark execution and reporting
"""

import argparse
import json
import time
import numpy as np
from datetime import datetime
from pathlib import Path

class BenchmarkRunner:
    def __init__(self, output_dir="benchmark_results"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.results = {}
    
    def run_latency_benchmark(self):
        print("Running latency benchmark...")
        # Implementation here
        pass
    
    def run_throughput_benchmark(self):
        print("Running throughput benchmark...")
        # Implementation here
        pass
    
    def run_resource_benchmark(self):
        print("Running resource usage benchmark...")
        # Implementation here
        pass
    
    def run_success_rate_benchmark(self):
        print("Running success rate benchmark...")
        # Implementation here
        pass
    
    def run_all(self):
        self.run_latency_benchmark()
        self.run_throughput_benchmark()
        self.run_resource_benchmark()
        self.run_success_rate_benchmark()
        
        # Save results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = self.output_dir / f"benchmark_{timestamp}.json"
        
        with open(output_file, "w") as f:
            json.dump(self.results, f, indent=2)
        
        print(f"\nResults saved to {output_file}")
        self.print_summary()
    
    def print_summary(self):
        print("\n" + "="*80)
        print("BENCHMARK SUMMARY")
        print("="*80)
        
        for benchmark, results in self.results.items():
            print(f"\n{benchmark}:")
            for metric, value in results.items():
                print(f"  {metric}: {value}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run Salamander benchmarks")
    parser.add_argument("--all", action="store_true", help="Run all benchmarks")
    parser.add_argument("--latency", action="store_true", help="Run latency benchmark")
    parser.add_argument("--throughput", action="store_true", help="Run throughput benchmark")
    parser.add_argument("--resource", action="store_true", help="Run resource benchmark")
    parser.add_argument("--success-rate", action="store_true", help="Run success rate benchmark")
    parser.add_argument("--output", default="benchmark_results", help="Output directory")
    
    args = parser.parse_args()
    
    runner = BenchmarkRunner(output_dir=args.output)
    
    if args.all or not any([args.latency, args.throughput, args.resource, args.success_rate]):
        runner.run_all()
    else:
        if args.latency:
            runner.run_latency_benchmark()
        if args.throughput:
            runner.run_throughput_benchmark()
        if args.resource:
            runner.run_resource_benchmark()
        if args.success_rate:
            runner.run_success_rate_benchmark()
```

## Continuous Benchmarking

### GitHub Actions Integration

```yaml
# .github/workflows/benchmark.yml
name: Benchmarks

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]
  schedule:
    - cron: '0 0 * * 0'  # Weekly on Sunday

jobs:
  benchmark:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.9'
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install pytest numpy psutil
      - name: Run benchmarks
        run: |
          PYTHONPATH=python_backend python3 benchmark_runner.py --all --output benchmark_results
      - name: Upload results
        uses: actions/upload-artifact@v3
        with:
          name: benchmark-results
          path: benchmark_results/
      - name: Compare to baseline
        run: |
          # Compare current results to previous baseline
          python3 benchmark_compare.py --baseline baseline.json --current benchmark_results/latest.json
      - name: Update baseline
        if: github.ref == 'refs/heads/main'
        run: |
          cp benchmark_results/latest.json baseline.json
          git config --global user.name 'Benchmark Bot'
          git config --global user.email 'benchmark@yourorg.com'
          git add baseline.json
          git commit -m "Update benchmark baseline [skip ci]"
          git push
```

## Reporting Standards

### ACM Guidelines

Follow ACM guidelines for performance reporting:

1. **System Description**: Hardware, software, configuration
2. **Workload Description**: Benchmark suite, input characteristics
3. **Metric Definitions**: Precise definitions of all metrics
4. **Statistical Methodology**: Number of trials, confidence intervals
5. **Raw Data**: Provide raw data or link to repository
6. **Reproducibility**: Instructions for independent reproduction

### Required Metadata

```json
{
  "benchmark_suite": "Salamander v1.0",
  "timestamp": "2026-06-22T12:33:20Z",
  "hardware": {
    "cpu": "Intel Core i9-9900K",
    "cores": 8,
    "memory_gb": 32,
    "storage": "NVMe SSD"
  },
  "software": {
    "os": "Ubuntu 22.04",
    "python": "3.9.6",
    "numpy": "1.24.3",
    "salamander": "1.0.0"
  },
  "methodology": {
    "num_trials": 1000,
    "warmup_trials": 100,
    "confidence_level": 0.95
  },
  "results": {
    "latency": {...},
    "throughput": {...},
    "resource_usage": {...},
    "success_rate": {...}
  }
}
```

## Performance Targets

### Tier 1: Minimum Viable Performance
- **Latency**: <10ms (p99)
- **Throughput**: >100 regenerations/second
- **Success Rate**: >80% at severity 0.9
- **Memory**: <20 KB per module

### Tier 2: Production Performance
- **Latency**: <5ms (p99)
- **Throughput**: >500 regenerations/second
- **Success Rate**: >90% at severity 0.9
- **Memory**: <10 KB per module

### Tier 3: Optimal Performance
- **Latency**: <2ms (p99)
- **Throughput**: >2,000 regenerations/second
- **Success Rate**: >95% at severity 0.9
- **Memory**: <5 KB per module

## Benchmark Dashboard

### Grafana Configuration

```json
{
  "dashboard": {
    "title": "Salamander Performance Benchmarks",
    "panels": [
      {
        "title": "Regeneration Latency (p50, p95, p99)",
        "type": "graph",
        "targets": [
          {
            "expr": "histogram_quantile(0.50, rate(salamander_regeneration_duration_seconds_bucket[5m]))",
            "legend": "p50"
          },
          {
            "expr": "histogram_quantile(0.95, rate(salamander_regeneration_duration_seconds_bucket[5m]))",
            "legend": "p95"
          },
          {
            "expr": "histogram_quantile(0.99, rate(salamander_regeneration_duration_seconds_bucket[5m]))",
            "legend": "p99"
          }
        ]
      },
      {
        "title": "Throughput (regenerations/second)",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(salamander_regenerations_total[1m])",
            "legend": "Throughput"
          }
        ]
      },
      {
        "title": "Success Rate",
        "type": "gauge",
        "targets": [
          {
            "expr": "salamander_regeneration_success_total / salamander_regeneration_total",
            "min": 0,
            "max": 1
          }
        ]
      }
    ]
  }
}
```

## Reproducibility Checklist

- [ ] Hardware specifications documented
- [ ] Software versions pinned
- [ ] Benchmark code published
- [ ] Raw data available
- [ ] Statistical methodology described
- [ ] Confidence intervals reported
- [ ] Warm-up procedure documented
- [ ] Environment variables documented
- [ ] Random seeds specified
- [ ] Independent replication successful

## References

- [ACM Artifact Review and Badging](https://www.acm.org/publications/proceedings-standard/)
- [IEEE Performance Evaluation Standards](https://www.computer.org/education/bodies-of-knowledge/computer-engineering/ce-ec2017/performance-analysis)
- [Google Benchmark](https://github.com/google/benchmark)
- [JMH (Java Microbenchmark Harness)](https://openjdk.org/projects/code-tools/jmh/)

---

**Last Updated**: 2026-06-22  
**Owner**: Performance Engineering Team  
**Next Review**: 2026-07-22