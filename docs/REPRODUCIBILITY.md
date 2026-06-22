# Reproducibility Package

## Overview

This document describes the reproducibility package for the Salamander Regeneration Framework, enabling independent researchers to reproduce all published results.

## Package Contents

```
reproducibility/
├── docker/
│   ├── Dockerfile
│   ├── docker-compose.yml
│   └── requirements.txt
├── scripts/
│   ├── setup.sh
│   ├── run_benchmarks.sh
│   ├── run_tests.sh
│   └── generate_figures.sh
├── data/
│   ├── synthetic/
│   │   ├── generate_synthetic_data.py
│   │   └── sample_inputs/