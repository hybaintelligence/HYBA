# THREE_SUBSTRATE_ARCHITECTURE.md

## Overview

HYBA_FULLSTACK implements a three-layer substrate architecture that provides a general-purpose coherent decision substrate. Each layer addresses a fundamental capability required for autonomous, resilient, and mathematically grounded systems.

## Layer 1: Mathematical Substrate

### Purpose
Provides deterministic mathematical transforms, structured search, and local validation capabilities.

### Core Components

#### Deterministic Protocol Handling
- **Location**: `python_backend/pythia_mining/`
- **Function**: Ensures reproducible behavior across network interactions
- **Key modules**: Protocol parsers, state machines, message handlers

#### Structured Nonce-Space Coverage
- **Location**: `python_backend/pythia_mining/quantum_*.py`
- **Function**: Systematic exploration of solution spaces with bounded search
- **Key modules**: Basis selection, nonce traversal, search algorithms

#### Bounded Basis-Selection Mechanisms
- **Location**: `rust_core/src/`, `cuda_core/`, `quantum_core/`
- **Function**: Classical hash verification with guided search
- **Key modules**: SIMD implementations, CUDA kernels, quantum gates

#### Local Proof-of-Work Validation
- **Location**: `python_backend/pythia_mining/`, `tests/`
- **Function**: Independent verification before external submission
- **Key modules**: Hash validators, difficulty checkers, share validators

#### Mathematical Certificate Generation
- **Location**: `artifacts/`, `python_backend/pythia_mining/`
- **Function**: Provable evidence of mathematical operations
- **Key modules**: Certificate builders, evidence packets, scope certificates

### Test Coverage
- **51/51 Great Minds integration tests** passing
- Validates mathematical integration across modules
- Ensures deterministic behavior in production paths

### Key Invariants
- No simulated telemetry in production codepaths
- Explicit gates for all mathematical operations
- Reproducible transforms given same inputs

## Layer 2: Autonomous-Control Substrate

### Purpose
Provides self-monitoring, decision-making, and operational control capabilities.

### Core Components

#### Autonomous Healing and Recovery
- **Location**: `python_backend/pythia_mining/quantum_regeneration.py`
- **Function**: Automatic recovery from failure states
- **Key modules**: Regeneration engines, state restoration, recovery planners

#### Optimizers and Meta-Controllers
- **Location**: `python_backend/pythia_mining/`, `scripts/`
- **Function**: Adaptive parameter tuning and system optimization
- **Key modules**: Gradient optimizers, meta-controllers, parameter search

#### Circuit Breakers and Safety Interlocks
- **Location**: `src/core/`, `python_backend/hyba_genesis_api/`
- **Function**: Operational safety and failure containment
- **Key modules**: Circuit breaker implementations, safety gates, rate limiters

#### Audit Logs and State Persistence
- **Location**: `logs/`, `artifacts/`, `python_backend/consciousness_db/`
- **Function**: Complete traceability and state recovery
- **Key modules**: Audit loggers, state serializers, database schemas

#### Production Control Rooms
- **Location**: `src/components/AdminPanel.tsx`, `dashboards/`
- **Function**: Real-time monitoring and intervention
- **Key modules**: Dashboard components, alert systems, control interfaces

#### SRE Copilots
- **Location**: `scripts/`, `runbooks/`
- **Function**: Automated incident response and guidance
- **Key modules**: Runbook engines, incident responders, health checkers

### Test Coverage
- **37/37 autonomous-controller tests** passing
- Validates healing, optimization, and control logic
- Ensures safe autonomous operation

### Key Invariants
- Operator-controlled production-readiness gates
- No autonomous action without audit trail
- All control surfaces have manual override

## Layer 3: Regeneration / Resilience Substrate

### Purpose
Provides fault tolerance, recovery physics, and regenerative process capabilities.

### Core Components

#### Recovery Physics
- **Location**: `python_backend/pythia_mining/quantum_regeneration.py`
- **Function**: Mathematical modeling of recovery processes
- **Key modules**: Recovery state machines, physics models, regeneration timers

#### Fault/Recovery Systems
- **Location**: `scripts/`, `python_backend/pythia_mining/`
- **Function**: Detection, isolation, and recovery from faults
- **Key modules**: Fault detectors, recovery orchestrators, health monitors

#### Regenerative Process Analogues
- **Location**: `hyba_intelligence_tests/`, `tests/`
- **Function**: Biological-inspired recovery mechanisms
- **Key modules**: Memory compression tests, mass gap shields, consciousness engines

#### Degraded-Mode Operation
- **Location**: `src/core/`, `python_backend/hyba_genesis_api/`
- **Function**: Continued operation under partial failure
- **Key modules**: Degradation handlers, fallback modes, graceful degradation

#### Autonomous Rollback
- **Location**: `python_backend/migrations/`, `scripts/`
- **Function**: Safe state reversion on failure
- **Key modules**: Rollback engines, state versioning, transaction managers

#### Memory-Integrity Checks
- **Location**: `hyba_intelligence_tests/`, `tests/`
- **Function**: Validation of memory and state consistency
- **Key modules**: Memory validators, integrity checkers, consistency verifiers

### Test Coverage
- **16/16 quantum-regeneration property tests** passing
- Validates recovery physics and resilience mechanisms
- Ensures system can survive and recover from failures

### Key Invariants
- All recovery paths are auditable
- No silent state corruption
- Recovery is deterministic and reproducible

## Cross-Layer Integration

### Mathematical → Autonomous Control
- Mathematical validation gates autonomous decisions
- Certificates provide evidence for control actions
- Deterministic math ensures predictable control behavior

### Autonomous Control → Regeneration
- Control systems trigger regeneration when needed
- Optimizers tune recovery parameters
- Circuit breakers prevent cascading failures

### Regeneration → Mathematical
- Recovery restores mathematical state
- Regeneration preserves mathematical invariants
- Resilience ensures continued mathematical operation

## Implementation Map

### Frontend (TypeScript/React)
- **Location**: `src/`
- **Layers**: Autonomous control (UI), Mathematical (visualization)
- **Key files**: `AdminPanel.tsx`, `bridge.ts`, `emergent_intelligence.ts`

### Backend (Python/FastAPI)
- **Location**: `python_backend/hyba_genesis_api/`, `python_backend/pythia_mining/`
- **Layers**: All three layers
- **Key files**: `main.py`, `quantum_regeneration.py`, mining modules

### Accelerated Compute (Rust/CUDA)
- **Location**: `rust_core/`, `cuda_core/`, `quantum_core/`
- **Layers**: Mathematical substrate
- **Key files**: `iit_4_gate.rs`, `phi_resonance.cu`, `phi_resonance_gate.py`

### Testing
- **Location**: `tests/`, `tests_enhanced/`, `hyba_intelligence_tests/`
- **Layers**: All three layers
- **Key files**: Integration tests, property tests, regeneration tests

### Operations
- **Location**: `scripts/`, `runbooks/`, `logs/`
- **Layers**: Autonomous control, Regeneration
- **Key files**: Gate scripts, runbooks, audit logs

## Data Flow

```
External Input
    ↓
Mathematical Substrate (validation, search, certificates)
    ↓
Autonomous-Control Substrate (decisions, optimization, control)
    ↓
Regeneration Substrate (recovery, resilience, fault tolerance)
    ↓
External Output (with proof)
```

## Deployment Architecture

### Development
- Frontend: Vite dev server on port 3000
- Backend: FastAPI on port 3001
- Local testing with full substrate coverage

### Production
- Containerized deployment with Docker
- Separate scaling per substrate layer
- Audit logging to persistent storage
- Circuit breakers at all external boundaries

## Evidence and Validation

### Current Evidence Stack
- **51/51** Great Minds integration tests (mathematical integration)
- **16/16** quantum-regeneration property tests (resilience)
- **37/37** autonomous-controller tests (control)

### Production Readiness
- All three substrates have passing test suites
- Audit trails for all autonomous actions
- Mathematical certificates for all critical operations
- Recovery procedures validated

## Future Extensions

### Mathematical Substrate
- Additional mathematical transforms
- New certificate types
- Extended search algorithms

### Autonomous-Control Substrate
- Multi-agent coordination
- Advanced optimization strategies
- Enhanced control room interfaces

### Regeneration Substrate
- Predictive failure detection
- Advanced recovery physics
- Self-healing at scale

## References

- [HYBA_SUBSTRATE_POSITIONING.md](./HYBA_SUBSTRATE_POSITIONING.md) - Strategic positioning
- [USE_CASE_FAMILIES.md](./USE_CASE_FAMILIES.md) - Use-case catalog
- [AGENTS.md](../AGENTS.md) - Repository working rules
- [TECHNICAL_SPECIFICATION.md](./TECHNICAL_SPECIFICATION.md) - Detailed technical specs
